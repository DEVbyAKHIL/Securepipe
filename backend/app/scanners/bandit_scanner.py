import asyncio, json, sys, uuid
from typing import List
from app.core.models import Finding, Severity
from app.core.logging import logger

FIXES = {
    "B105": "Use os.getenv for passwords. Never hardcode credentials.",
    "B201": "Set DEBUG=False in production via environment variable.",
    "B301": "Replace pickle with json.",
    "B303": "Use hashlib.sha256 or bcrypt. MD5/SHA1 are broken.",
    "B311": "Use secrets.token_urlsafe for cryptographic randomness.",
    "B501": "Remove verify=False. SSL verification must be enabled.",
    "B602": "Pass subprocess commands as a list, not a shell string.",
    "B608": "Use parameterized queries.",
}
DEFAULT = "Review OWASP Top 10. Validate all inputs. Use least privilege."

async def run_bandit(repo_path: str) -> List[Finding]:
    # Use python -m bandit so the pip-installed package is always found,
    # regardless of whether the 'bandit' shim is on PATH (Windows issue).
    cmd = [sys.executable, "-m", "bandit",
           "-r", repo_path, "-f", "json", "-ll", "--quiet",
           "-x", ".git,tests,venv,.venv,node_modules"]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, err = await asyncio.wait_for(proc.communicate(), timeout=60)
        raw = out.decode("utf-8", errors="replace").strip()
        if not raw:
            # Bandit exits 0 with no output when no issues found — that's fine.
            # But if exit code != 0 and no output, log stderr for debugging.
            if proc.returncode not in (0, 1):
                stderr_text = err.decode("utf-8", errors="replace").strip()
                logger.warning("bandit_no_output", rc=proc.returncode, stderr=stderr_text[:500])
            return []
        data = json.loads(raw)
        findings = []
        for item in data.get("results", []):
            tid = item.get("test_id","B000")
            s   = item.get("issue_severity","LOW").upper()
            c   = item.get("issue_confidence","LOW").upper()
            if s=="HIGH" and c=="HIGH": sev = Severity.CRITICAL
            elif s=="HIGH":             sev = Severity.HIGH
            elif s=="MEDIUM":           sev = Severity.MEDIUM
            else:                       sev = Severity.LOW
            findings.append(Finding(
                id="b_"+uuid.uuid4().hex[:8], scanner="SAST Bandit", severity=sev,
                title=item.get("test_name","Issue").replace("_"," ").title(),
                description=item.get("issue_text","Security issue."),
                file=item.get("filename","").replace(repo_path,"").lstrip("/").lstrip("\\"),
                line=item.get("line_number"), vuln_type=tid,
                suggestion=FIXES.get(tid, DEFAULT),
                code_snippet=item.get("code","").strip(),
                references=[f"https://bandit.readthedocs.io/en/latest/plugins/{tid.lower()}.html"],
            ))
        logger.info("bandit_done", n=len(findings))
        return findings
    except Exception as e:
        logger.error("bandit_fail", err=repr(e)); return []
