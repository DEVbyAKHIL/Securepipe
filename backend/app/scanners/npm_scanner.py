import asyncio, json, os, shutil, uuid
from typing import List
from app.core.models import Finding, Severity
from app.core.logging import logger

def sev(severity: str) -> Severity:
    m = {"critical":Severity.CRITICAL,"high":Severity.HIGH,
         "moderate":Severity.MEDIUM,"low":Severity.LOW}
    return m.get(severity.lower(), Severity.LOW)

async def run_npm_audit(repo_path: str) -> List[Finding]:
    pkg  = os.path.join(repo_path, "package.json")
    lock = os.path.join(repo_path, "package-lock.json")
    if not os.path.isfile(pkg): return []
    if not os.path.isfile(lock):
        logger.info("npm_no_lock", hint="package-lock.json missing, skipping npm audit")
        return []
    if not shutil.which("npm"):
        logger.info("npm_not_installed", hint="install Node.js/npm for JS dependency scanning")
        return []

    cmd = ["npm","audit","--json"]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            cwd=repo_path)
        out, err = await asyncio.wait_for(proc.communicate(), timeout=60)
        raw = out.decode("utf-8", errors="replace").strip()
        stderr_text = err.decode("utf-8", errors="replace").strip()

        if not raw:
            if proc.returncode != 0:
                logger.warning("npm_no_output", rc=proc.returncode, stderr=stderr_text[:500])
            return []

        data = json.loads(raw)
        findings = []
        for pkg_name, info in data.get("vulnerabilities", {}).items():
            s   = info.get("severity","low")
            via = info.get("via",[])
            desc = via[0].get("title","Vulnerability") if via and isinstance(via[0],dict) else "Vulnerability"
            findings.append(Finding(
                id="npm_"+uuid.uuid4().hex[:8], scanner="Dependencies npm audit",
                severity=sev(s), title=f"Vulnerable package {pkg_name}",
                description=desc, file="package.json",
                vuln_type="npm_vulnerability",
                suggestion=f"npm audit fix  or  npm install {pkg_name}@latest",
            ))
        logger.info("npm_done", n=len(findings)); return findings
    except (FileNotFoundError, OSError):
        logger.info("npm_not_installed"); return []
    except Exception as e:
        logger.error("npm_fail", err=repr(e)); return []
