import asyncio, json, uuid
from typing import List
from app.core.models import Finding, Severity
from app.core.logging import logger

SEV_MAP = {"ERROR":Severity.HIGH,"WARNING":Severity.MEDIUM,"INFO":Severity.LOW}

async def run_semgrep(repo_path: str) -> List[Finding]:
    cmd = ["semgrep","--config","p/security-audit","--config","p/secrets",
           "--json","--quiet","--max-target-bytes","1000000", repo_path]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
        raw = out.decode("utf-8", errors="replace").strip()
        if not raw: return []
        data = json.loads(raw)
        findings = []
        for item in data.get("results", []):
            meta = item.get("extra", {})
            findings.append(Finding(
                id="sg_"+uuid.uuid4().hex[:8], scanner="SAST Semgrep",
                severity=SEV_MAP.get(meta.get("severity","WARNING"), Severity.MEDIUM),
                title=item.get("check_id","").split(".")[-1].replace("-"," ").title(),
                description=meta.get("message","Security issue detected."),
                file=item.get("path","").replace(repo_path,"").lstrip("/"),
                line=item.get("start",{}).get("line"),
                vuln_type="sast_finding",
                fix_suggestion=meta.get("fix","Review and remediate per OWASP Top 10."),
                code_snippet=meta.get("lines","").strip()[:150],
                references=meta.get("references",[]),
            ))
        logger.info("semgrep_done", n=len(findings)); return findings
    except Exception as e:
        logger.error("semgrep_fail", err=str(e)); return []
