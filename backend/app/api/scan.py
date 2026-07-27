from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.core.models import ScanRequest, ScanResult, HistoryScan, ScanStatus, HealthResponse
from app.core.config import settings
from app.core.auth import require_api_key
from app.services.scan_service import run_full_scan
from app.db.supabase import get_scan_history

router = APIRouter()

@router.post("/scan", response_model=ScanResult)
async def trigger_scan(req: ScanRequest, _=Depends(require_api_key)):
    result = await run_full_scan(req)
    if result.status == ScanStatus.FAILED:
        raise HTTPException(status_code=500, detail=result.error_message)
    return result

@router.get("/scans", response_model=List[HistoryScan])
async def get_history(limit: int = 20, _=Depends(require_api_key)):
    return await get_scan_history(limit=min(limit, 100))

@router.get("/health", response_model=HealthResponse)
async def health():
    from app.db.supabase import get_client
    return HealthResponse(
        status="ok", version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        ai_enabled=settings.AI_ENABLED,
        db_connected=get_client() is not None,
    )
@router.get("/history", response_model=List[HistoryScan])
async def get_history_alias(limit: int = 20, _=Depends(require_api_key)):
    """Alias for /scans – kept for backward compatibility with dashboard UI."""
    return await get_scan_history(limit=min(limit, 100))
