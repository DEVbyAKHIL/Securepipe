from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from app.core.models import ScanRequest, ScanResult, ScanStatus
from app.core.auth import require_api_key
from app.core.exceptions import ScanError
from app.core.logging import logger
from app.services.scan_service import run_full_scan
import uuid
from datetime import datetime, timezone

router = APIRouter()
jobs: dict = {}

async def run_job(job_id: str, req: ScanRequest):
    jobs[job_id]["status"] = ScanStatus.RUNNING
    try:
        result = await run_full_scan(req)
        jobs[job_id]["status"]       = result.status
        jobs[job_id]["result"]       = result
        jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        if result.status == ScanStatus.FAILED:
            jobs[job_id]["error"] = result.error_message
            logger.error("job_failed", job_id=job_id, error=result.error_message)
    except ScanError as e:
        jobs[job_id]["status"] = ScanStatus.FAILED
        jobs[job_id]["error"]  = e.detail if hasattr(e, "detail") else str(e)
        logger.error("job_scan_error", job_id=job_id, error=jobs[job_id]["error"])
    except Exception as e:
        jobs[job_id]["status"] = ScanStatus.FAILED
        jobs[job_id]["error"]  = str(e)
        logger.error("job_exception", job_id=job_id, error=str(e))

@router.post("/scan/async")
async def trigger_async_scan(req: ScanRequest, bg: BackgroundTasks, _=Depends(require_api_key)):
    job_id = "job_" + uuid.uuid4().hex[:12]
    jobs[job_id] = {
        "job_id": job_id, "repo_url": req.repo_url, "branch": req.branch,
        "status": ScanStatus.QUEUED, "result": None, "error": None,
        "queued_at": datetime.now(timezone.utc).isoformat(),
    }
    bg.add_task(run_job, job_id, req)
    return {"job_id": job_id, "status": "queued",
            "poll": f"/api/v1/scan/status/{job_id}"}

@router.get("/scan/status/{job_id}")
async def get_scan_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] == ScanStatus.COMPLETED and job["result"]:
        return job["result"]
    return {
        "job_id": job_id, "status": job["status"],
        "repo_url": job["repo_url"], "queued_at": job["queued_at"],
        "completed_at": job.get("completed_at"),
        "error_message": job.get("error"),
    }

@router.get("/scan/jobs")
async def list_jobs(_=Depends(require_api_key)):
    return [{"job_id":k,"status":v["status"],"repo_url":v["repo_url"],
             "queued_at":v["queued_at"]} for k,v in jobs.items()]
