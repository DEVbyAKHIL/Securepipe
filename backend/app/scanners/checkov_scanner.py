import asyncio, json, uuid
from typing import List
from app.core.models import Finding, Severity
from app.core.logging import logger

SEV_MAP = {"HIGH": Severity.HIGH, "MEDIUM": Severity.MEDIUM, "LOW": Severity.LOW}

async def run_checkov(repo_path: str) -> List[Finding]:
    cmd = ["checkov","-d",repo_path,"--output","json","--quiet",
           "--skip-check","CKV_DOCKER_3"]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=90)
        raw = out.decode("utf-8", errors="replace").strip()
        if not raw: return []
        data = json.loads(raw)
        checks = data if isinstance(data, list) else [data]
        findings = []
        for block in checks:
            for item in block.get("results",{}).get("failed_checks",[]):
                findings.append(Finding(
                    id="ck_"+uuid.uuid4().hex[:8], scanner="IaC Checkov",
                    severity=SEV_MAP.get(item.get("severity","LOW"), Severity.LOW),
                    title=item.get("check_id","") + " " + item.get("check_type",""),
                    description=item.get("check_id","IaC misconfiguration"),
                    file=item.get("repo_file_path","").replace(repo_path,"").lstrip("/"),
                    line=item.get("file_line_range",[None])[0],
                    vuln_type="iac_misconfiguration",
                    fix_suggestion="Review Checkov docs for remediation.",
                ))
        logger.info("checkov_done", n=len(findings)); return findings
    except Exception as e:
        logger.error("checkov_fail", err=str(e)); return []
