import asyncio, json, os, uuid
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
    cmd = ["safety","check","-r",req,"--json"]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
        raw = out.decode("utf-8", errors="replace").strip()
        if not raw: return []
        data = json.loads(raw)
        vulns = data if isinstance(data, list) else data.get("vulnerabilities", [])
        findings = []
        for v in vulns:
            if isinstance(v, list) and len(v) >= 5:
                pkg,_,desc,vid = v[0],v[2],v[3],v[4]
                cvss = float(v[5]) if len(v)>5 and v[5] else 5.0
            elif isinstance(v, dict):
                pkg  = v.get("package_name","?")
                desc = v.get("advisory","Vuln.")
                vid  = v.get("vulnerability_id","")
                cvss = float(v.get("cvss_v3") or 5.0)
            else: continue
            findings.append(Finding(
                id="s_"+uuid.uuid4().hex[:8], scanner="Dependencies Safety",
                severity=sev(cvss), title=f"Vulnerable {pkg}",
                description=desc, file="requirements.txt",
                vuln_type="outdated_dependency",
                cve=vid if vid.startswith("CVE-") else None,
                cvss=round(cvss,1), fix_suggestion=f"pip install --upgrade {pkg}",
                code_snippet=pkg,
            ))
        logger.info("safety_done", n=len(findings)); return findings
    except Exception as e:
        logger.error("safety_fail", err=str(e)); return []
