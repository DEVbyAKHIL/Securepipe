from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Header
from app.core.models import ScanRequest, ScanStatus
from app.core.config import settings
from app.core.logging import logger
from app.api.queue import jobs, run_job
import hashlib, hmac, uuid
from datetime import datetime, timezone

router = APIRouter()

def verify_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    if not secret or not sig_header: return True
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig_header)

@router.post("/webhook/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str = Header(default=""),
):
    payload = await request.body()
    if not verify_signature(payload, x_hub_signature_256, settings.WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")
    if x_github_event not in ["push","pull_request"]:
        return {"status": "ignored", "event": x_github_event}
    data     = await request.json()
    repo_url = data.get("repository",{}).get("clone_url","")
    branch   = data.get("ref","refs/heads/main").replace("refs/heads/","")
    if not repo_url:
        raise HTTPException(status_code=400, detail="No repo URL in payload.")
    repo_url = repo_url.replace(".git","")
    job_id   = "job_" + uuid.uuid4().hex[:12]
    req      = ScanRequest(repo_url=repo_url, branch=branch)
    jobs[job_id] = {
        "job_id": job_id, "repo_url": repo_url, "branch": branch,
        "status": ScanStatus.QUEUED, "result": None, "error": None,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "triggered_by": "github_webhook",
    }
    background_tasks.add_task(run_job, job_id, req)
    logger.info("webhook_queued", job=job_id, repo=repo_url, branch=branch)
    return {"status":"queued","job_id":job_id,"repo":repo_url,"branch":branch}
