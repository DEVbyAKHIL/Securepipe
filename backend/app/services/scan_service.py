import asyncio, time, uuid
from datetime import datetime, timezone
from typing import List
from app.core.models import ScanResult, ScanRequest, ScanCounts, ScanStatus, Finding, Severity
from app.core.logging import logger
from app.scanners.repo_manager import cloned_repo
from app.scanners.bandit_scanner import run_bandit
from app.scanners.safety_scanner import run_safety
from app.scanners.trufflehog_scanner import run_trufflehog
from app.scanners.checkov_scanner import run_checkov
from app.scanners.npm_scanner import run_npm_audit
from app.scanners.semgrep_scanner import run_semgrep
from app.scanners.trivy_scanner import run_trivy
from app.services.ai_suggestions import enrich_all_findings
from app.db.supabase import save_scan_result

def score(c): return max(0, min(100, 100 - c.critical*20 - c.high*10 - c.medium*5 - c.low*2))

def counts(findings):
    c = ScanCounts(
        critical=sum(1 for f in findings if f.severity==Severity.CRITICAL),
        high    =sum(1 for f in findings if f.severity==Severity.HIGH),
        medium  =sum(1 for f in findings if f.severity==Severity.MEDIUM),
        low     =sum(1 for f in findings if f.severity==Severity.LOW),
    )
    c.total = c.critical + c.high + c.medium + c.low
    return c

async def safe(name, coro):
    try:
        r = await coro; logger.info("ok", s=name, n=len(r)); return name, r
    except Exception as e:
        logger.error("scanner_fail", s=name, err=repr(e)); return name, []

async def run_full_scan(req: ScanRequest) -> ScanResult:
    sid = "scan_" + uuid.uuid4().hex[:16]
    t0  = time.monotonic()
    started = datetime.now(timezone.utc)
    logger.info("scan_start", id=sid, repo=req.repo_url)
    try:
        async with cloned_repo(req.repo_url, req.branch) as path:
            results = await asyncio.gather(
                safe("bandit",   run_bandit(path)),
                safe("safety",   run_safety(path)),
                safe("trufflehog", run_trufflehog(path)),
                safe("checkov",  run_checkov(path)),
                safe("npm",      run_npm_audit(path)),
                safe("semgrep",  run_semgrep(path)),
                safe("trivy",    run_trivy(path)),
            )
        all_f = []
        for _, fl in results: all_f.extend(fl)
        order = {Severity.CRITICAL:0,Severity.HIGH:1,Severity.MEDIUM:2,Severity.LOW:3}
        all_f.sort(key=lambda f: order.get(f.severity, 4))
        all_f  = await enrich_all_findings(all_f)
        c      = counts(all_f)
        s      = score(c)
        dur    = round(time.monotonic() - t0, 2)
        result = ScanResult(
            scan_id=sid, repo_url=req.repo_url,
            repo_name=req.repo_url.rstrip("/").split("/")[-1],
            branch=req.branch, status=ScanStatus.COMPLETED,
            findings=all_f, counts=c, score=s, duration_seconds=dur,
            scanners_used=["Bandit","Safety","TruffleHog","Checkov","npm audit","Semgrep","Trivy"],
            started_at=started, completed_at=datetime.now(timezone.utc),
        )
        logger.info("scan_done", id=sid, total=c.total, score=s)
        asyncio.create_task(save_scan_result(result))
        return result
    except Exception as e:
        logger.error("scan_fail", id=sid, err=repr(e))
        return ScanResult(
            scan_id=sid, repo_url=req.repo_url,
            repo_name=req.repo_url.split("/")[-1],
            branch=req.branch, status=ScanStatus.FAILED,
            error_message=str(e),
            duration_seconds=round(time.monotonic()-t0,2),
            started_at=started, completed_at=datetime.now(timezone.utc),
        )
