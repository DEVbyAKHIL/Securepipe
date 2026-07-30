import asyncio, json, os, sys, uuid
from typing import List
from app.core.models import Finding, Severity
from app.core.logging import logger

def sev(cvss):
    if cvss >= 9.0: return Severity.CRITICAL
    if cvss >= 7.0: return Severity.HIGH
    if cvss >= 4.0: return Severity.MEDIUM
    return Severity.LOW

async def run_safety(repo_path: str) -> List[Finding]:
    req = os.path.join(repo_path, "requirements.txt")
    if not os.path.isfile(req): return []

    # Try Safety v3.x first (uses `scan` subcommand), fall back to v2 (`check`).
    findings = await _try_safety_v3(req, repo_path)
    if findings is not None:
        return findings
    return await _try_safety_v2(req, repo_path)


async def _try_safety_v3(req: str, repo_path: str) -> "List[Finding] | None":
    """Safety >= 3.x uses `safety scan` with different output."""
    cmd = [sys.executable, "-m", "safety", "check", "-r", req, "--output", "json"]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, err = await asyncio.wait_for(proc.communicate(), timeout=60)
        raw = out.decode("utf-8", errors="replace").strip()
        stderr_text = err.decode("utf-8", errors="replace").strip()

        if not raw:
            if proc.returncode != 0:
                logger.warning("safety_v3_no_output", rc=proc.returncode, stderr=stderr_text[:500])
            # Could mean no vulns or wrong subcommand — fall back to v2
            return None

        data = json.loads(raw)
        return _parse_safety_output(data, repo_path)
    except json.JSONDecodeError:
        logger.warning("safety_v3_bad_json", hint="falling back to v2")
        return None
    except Exception as e:
        logger.warning("safety_v3_error", err=repr(e))
        return None


async def _try_safety_v2(req: str, repo_path: str) -> List[Finding]:
    """Safety v2 style: `safety check -r req --json`."""
    cmd = [sys.executable, "-m", "safety", "check", "-r", req, "--json"]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, err = await asyncio.wait_for(proc.communicate(), timeout=60)
        raw = out.decode("utf-8", errors="replace").strip()
        stderr_text = err.decode("utf-8", errors="replace").strip()

        if not raw:
            if proc.returncode != 0:
                logger.warning("safety_v2_no_output", rc=proc.returncode, stderr=stderr_text[:500])
            return []

        data = json.loads(raw)
        result = _parse_safety_output(data, repo_path)
        if result is not None:
            return result
        return []
    except Exception as e:
        logger.error("safety_fail", err=repr(e)); return []


def _parse_safety_output(data, repo_path: str) -> "List[Finding] | None":
    """Parse Safety output — handles both v2 list format and v3 dict format."""
    findings = []

    # v3 format: {"report": {"vulnerabilities": [...]}}
    if isinstance(data, dict):
        vulns = (data.get("vulnerabilities", [])
                 or data.get("report", {}).get("vulnerabilities", []))
        if not vulns and "scanned_packages" in data:
            # Safety v3 with no vulns found — valid empty result
            logger.info("safety_clean")
            return []
        for v in vulns:
            if isinstance(v, dict):
                pkg  = v.get("package_name") or v.get("name", "?")
                desc = v.get("advisory") or v.get("more_info_path") or "Vulnerability"
                vid  = v.get("vulnerability_id") or v.get("id", "")
                cvss = float(v.get("cvss_v3") or v.get("severity_source", {}).get("cvss_score", 5.0) or 5.0)
                findings.append(_make_finding(pkg, desc, vid, cvss))
        logger.info("safety_done", n=len(findings))
        return findings

    # v2 format: list of lists [[pkg, installed_ver, affected_ver, desc, id, ...], ...]
    if isinstance(data, list):
        for v in data:
            if isinstance(v, list) and len(v) >= 5:
                pkg = v[0]
                desc = v[3] if len(v) > 3 else "Vulnerability"
                vid  = v[4] if len(v) > 4 else ""
                cvss = float(v[5]) if len(v) > 5 and v[5] else 5.0
                findings.append(_make_finding(pkg, desc, vid, cvss))
            elif isinstance(v, dict):
                pkg  = v.get("package_name", "?")
                desc = v.get("advisory", "Vulnerability")
                vid  = v.get("vulnerability_id", "")
                cvss = float(v.get("cvss_v3") or 5.0)
                findings.append(_make_finding(pkg, desc, vid, cvss))
        logger.info("safety_done", n=len(findings))
        return findings

    return None


def _make_finding(pkg, desc, vid, cvss):
    return Finding(
        id="s_"+uuid.uuid4().hex[:8], scanner="Dependencies Safety",
        severity=sev(cvss), title=f"Vulnerable {pkg}",
        description=desc, file="requirements.txt",
        vuln_type="outdated_dependency",
        cve=vid if isinstance(vid, str) and vid.startswith("CVE-") else None,
        cvss=round(cvss, 1), suggestion=f"pip install --upgrade {pkg}",
        code_snippet=pkg,
    )
