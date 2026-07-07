"""
Drop-in replacement for backend/app/db/supabase.py

WHY THIS CHANGES:
`supabase-py`'s client is synchronous under the hood (it's a thin wrapper over
`httpx`'s sync client via postgrest-py). Both save_scan_result and
get_scan_history are `async def` but call `.execute()` directly, which is a
blocking network call sitting inside an async function — it blocks the whole
FastAPI event loop for the duration of that request, stalling every other
concurrent request (including scans in progress) until Supabase responds.
Wrapping the blocking call in `asyncio.to_thread(...)` moves it off the event
loop onto a worker thread, same pattern already used elsewhere in this
codebase for Gemini calls in ai_suggestions.py.
"""

import asyncio
from app.core.config import settings
from app.core.models import ScanResult, HistoryScan
from app.core.logging import logger
from typing import List

_client = None


def get_client():
    global _client
    if _client is None and settings.SUPABASE_URL and settings.SUPABASE_KEY:
        try:
            from supabase import create_client
            _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        except Exception as e:
            logger.error("supabase_init_fail", err=str(e))
    return _client


async def save_scan_result(result: ScanResult):
    client = get_client()
    if not client:
        return
    try:
        data = {
            "scan_id": result.scan_id, "repo_url": result.repo_url,
            "repo_name": result.repo_name, "branch": result.branch,
            "status": result.status.value, "score": result.score,
            "counts": result.counts.model_dump(),
            "findings_count": result.counts.total,
            "duration_seconds": result.duration_seconds,
            "started_at": result.started_at.isoformat() if result.started_at else None,
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
        }
        await asyncio.to_thread(
            lambda: client.table("scan_results").insert(data).execute()
        )
        logger.info("supabase_saved", id=result.scan_id)
    except Exception as e:
        logger.error("supabase_save_fail", err=str(e))


async def get_scan_history(limit: int = 20) -> List[HistoryScan]:
    client = get_client()
    if not client:
        return []
    try:
        resp = await asyncio.to_thread(
            lambda: client.table("scan_results")
                .select("*").order("completed_at", desc=True)
                .limit(limit).execute()
        )
        from app.core.models import ScanCounts, ScanStatus
        results = []
        for row in resp.data:
            results.append(HistoryScan(
                scan_id=row["scan_id"], repo_url=row["repo_url"],
                repo_name=row.get("repo_name", ""), branch=row.get("branch", "main"),
                status=ScanStatus(row.get("status", "completed")),
                score=row.get("score"), counts=ScanCounts(**row.get("counts", {})),
                duration_seconds=row.get("duration_seconds"),
                completed_at=row.get("completed_at"),
            ))
        return results
    except Exception as e:
        logger.error("supabase_fetch_fail", err=str(e))
        return []
