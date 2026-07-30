import asyncio, json, shutil, uuid
from typing import List
from app.core.models import Finding, Severity
from app.core.logging import logger

SEV_MAP = {"CRITICAL":Severity.CRITICAL,"HIGH":Severity.HIGH,
           "MEDIUM":Severity.MEDIUM,"LOW":Severity.LOW}

async def run_trivy(repo_path: str) -> List[Finding]:
    if not shutil.which("trivy"):
        logger.info("trivy_not_installed", hint="install trivy for container/OS vuln scanning")
        return []

    cmd = ["trivy","fs","--format","json","--quiet", repo_path]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, err = await asyncio.wait_for(proc.communicate(), timeout=120)
        raw = out.decode("utf-8", errors="replace").strip()
        stderr_text = err.decode("utf-8", errors="replace").strip()

        if not raw:
            if proc.returncode != 0:
                logger.warning("trivy_no_output", rc=proc.returncode, stderr=stderr_text[:500])
            return []

        data = json.loads(raw)
        findings = []
        for result in data.get("Results", []):
            for v in result.get("Vulnerabilities", []):
                findings.append(Finding(
                    id="tv_"+uuid.uuid4().hex[:8], scanner="Trivy",
                    severity=SEV_MAP.get(v.get("Severity","LOW"), Severity.LOW),
                    title=v.get("VulnerabilityID","") + " in " + v.get("PkgName",""),
                    description=v.get("Description","OS/Container vulnerability"),
                    file=result.get("Target",""),
                    vuln_type="container_vulnerability",
                    cve=v.get("VulnerabilityID"),
                    cvss=v.get("CVSS",{}).get("nvd",{}).get("V3Score"),
                    suggestion=f"Update to {v.get('FixedVersion','latest')}",
                    references=v.get("References",[]),
                ))
        logger.info("trivy_done", n=len(findings)); return findings
    except (FileNotFoundError, OSError):
        logger.info("trivy_not_installed"); return []
    except Exception as e:
        logger.error("trivy_fail", err=repr(e)); return []
