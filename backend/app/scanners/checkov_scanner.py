import asyncio, json, sys, uuid
from typing import List
from app.core.models import Finding, Severity
from app.core.logging import logger

SEV_MAP = {"HIGH": Severity.HIGH, "MEDIUM": Severity.MEDIUM, "LOW": Severity.LOW}

async def run_checkov(repo_path: str) -> List[Finding]:
    # Use python -m checkov.main so the pip-installed package is always found.
    cmd = [sys.executable, "-m", "checkov.main",
           "-d", repo_path, "--output", "json", "--quiet",
           "--skip-check", "CKV_DOCKER_3",
           "--compact"]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, err = await asyncio.wait_for(proc.communicate(), timeout=60)
        raw = out.decode("utf-8", errors="replace").strip()
        stderr_text = err.decode("utf-8", errors="replace").strip()

        if not raw:
            if proc.returncode != 0:
                logger.warning("checkov_no_output", rc=proc.returncode, stderr=stderr_text[:500])
            return []

        # Checkov sometimes prints non-JSON lines before the JSON output.
        # Find the start of JSON (first '[' or '{').
        json_start = -1
        for i, ch in enumerate(raw):
            if ch in ('[', '{'):
                json_start = i
                break
        if json_start > 0:
            raw = raw[json_start:]

        data = json.loads(raw)
        checks = data if isinstance(data, list) else [data]
        findings = []
        for block in checks:
            if not isinstance(block, dict):
                continue
            failed = block.get("results",{}).get("failed_checks",[])
            for item in failed:
                findings.append(Finding(
                    id="ck_"+uuid.uuid4().hex[:8], scanner="IaC Checkov",
                    severity=SEV_MAP.get(item.get("severity","LOW"), Severity.LOW),
                    title=item.get("check_id","") + " " + item.get("check_type",""),
                    description=item.get("check_id","IaC misconfiguration"),
                    file=item.get("repo_file_path","").replace(repo_path,"").lstrip("/").lstrip("\\"),
                    line=item.get("file_line_range",[None])[0],
                    vuln_type="iac_misconfiguration",
                    suggestion="Review Checkov docs for remediation.",
                ))
        logger.info("checkov_done", n=len(findings)); return findings
    except Exception as e:
        logger.error("checkov_fail", err=repr(e)); return []
