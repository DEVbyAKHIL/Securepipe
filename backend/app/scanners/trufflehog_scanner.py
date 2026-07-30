import asyncio, re, os, uuid, json
from typing import List
from app.core.models import Finding, Severity
from app.core.logging import logger

SKIP_DIR = {".git", "node_modules", "__pycache__", ".venv", "venv"}
SKIP_EXT = {".png", ".jpg", ".gif", ".ico", ".pdf", ".zip", ".woff"}
FIX = "Rotate credential immediately. Remove from git history. Store in Vault."
PATTERNS = [
    ("AWS Key",      r"AKIA[0-9A-Z]{16}",            Severity.CRITICAL, 9.8),
    ("GitHub Token", r"ghp_[a-zA-Z0-9]{36}",          Severity.CRITICAL, 9.8),
    ("Stripe Key",   r"sk_live[0-9a-zA-Z]{24}",       Severity.CRITICAL, 9.8),
    ("Google Key",   r"AIza[0-9A-Za-z\-]{35}",       Severity.HIGH,     7.5),
    ("Private Key",  r"-----BEGIN .{0,10}PRIVATE KEY", Severity.CRITICAL, 9.8),
    ("Password",     r"(?i)password\s*=\s*.{4,}",   Severity.HIGH,     7.5),
    ("Generic Secret", r"(?i)(?:secret|token|api_key)\s*[=:]\s*['\"][^\s'\"]{8,}", Severity.HIGH, 7.5),
    ("Slack Token",  r"xox[baprs]-[0-9a-zA-Z\-]{10,}", Severity.HIGH, 7.5),
]


def regex_scan(repo_path: str) -> List[Finding]:
    """Regex-based secret scanning fallback when trufflehog binary is unavailable."""
    found, seen = [], set()
    for dp, dns, fns in os.walk(repo_path):
        dns[:] = [d for d in dns if d not in SKIP_DIR]
        for fn in fns:
            if os.path.splitext(fn)[1].lower() in SKIP_EXT:
                continue
            fp  = os.path.join(dp, fn)
            rel = fp.replace(repo_path, "").lstrip("/").lstrip("\\")
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        for name, pattern, sev, cvss in PATTERNS:
                            if re.search(pattern, line):
                                key = rel + name
                                if key in seen:
                                    continue
                                seen.add(key)
                                found.append(Finding(
                                    id="sec_" + uuid.uuid4().hex[:8],
                                    scanner="Secrets TruffleHog",
                                    severity=sev,
                                    title=f"{name} Detected",
                                    description=f"Hardcoded {name} found.",
                                    file=rel,
                                    line=i,
                                    vuln_type="secret_in_code",
                                    cvss=cvss,
                                    suggestion=FIX,
                                    code_snippet=line.strip()[:100],
                                ))
                                break
            except Exception:
                continue
    return found


async def run_trufflehog(repo_path: str) -> List[Finding]:
    # First try the trufflehog binary; if not installed, fall back to regex.
    try:
        cmd = ["trufflehog", "filesystem", repo_path, "--json", "--no-update"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=90)
        raw_lines = out.decode("utf-8", errors="replace").splitlines()
        findings = []
        for line in raw_lines:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                fp = (item
                      .get("SourceMetadata", {})
                      .get("Data", {})
                      .get("Filesystem", {})
                      .get("file", "?"))
                findings.append(Finding(
                    id="th_" + uuid.uuid4().hex[:8],
                    scanner="Secrets TruffleHog",
                    severity=Severity.CRITICAL,
                    vuln_type="secret_in_code",
                    title=f"Verified {item.get('DetectorName', 'Secret')}",
                    description="Live credential verified by TruffleHog.",
                    file=fp.replace(repo_path, "").lstrip("/").lstrip("\\"),
                    cvss=9.8,
                    suggestion=FIX,
                ))
            except Exception:
                continue
        logger.info("trufflehog_done", n=len(findings))
        return findings
    except (FileNotFoundError, OSError):
        # trufflehog binary not installed — fall back to regex scanning.
        # This is the expected case on Windows without the Go binary.
        logger.info("trufflehog_not_installed", fallback="regex")
        r = regex_scan(repo_path)
        logger.info("regex_fallback_done", n=len(r))
        return r
    except Exception as e:
        # Some other error (timeout, etc.) — still try regex fallback.
        logger.error("trufflehog_fail", err=repr(e))
        r = regex_scan(repo_path)
        logger.info("regex_fallback_done", n=len(r))
        return r
