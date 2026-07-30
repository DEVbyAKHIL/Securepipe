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
    from app.core.logging import logger
    logger.info("trigger_scan_result", status=result.status, err=result.error_message)
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
        status="Backend connected", version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        ai_enabled=settings.AI_ENABLED,
        db_connected=get_client() is not None,
    )
@router.get("/history", response_model=List[HistoryScan])
async def get_history_alias(limit: int = 20, _=Depends(require_api_key)):
    """Alias for /scans – kept for backward compatibility with dashboard UI."""
    return await get_scan_history(limit=min(limit, 100))

@router.get("/ai/health")
async def ai_health(_=Depends(require_api_key)):
    from app.core.config import settings
    model_name = settings.GEMINI_MODEL if hasattr(settings, "GEMINI_MODEL") else "gemini-2.5-flash"
    # To determine last_status we can just check if configured. We haven't stored global state for it but we can just say "not_tested"
    # But wait, the user asked for: "last_status": "success | fallback | unavailable | not_tested"
    from app.services.ai_suggestions import get_last_status
    return {
        "configured": settings.AI_ENABLED and bool(settings.GEMINI_API_KEY),
        "sdk": "google-genai",
        "model": model_name,
        "last_status": get_last_status() if settings.AI_ENABLED else "unavailable"
    }

@router.post("/ai/test")
async def ai_test(_=Depends(require_api_key)):
    from app.services.ai_suggestions import enrich_all_findings
    from app.core.models import Finding, Severity
    import uuid
    finding = Finding(
        id="sec_" + uuid.uuid4().hex[:8],
        scanner="Secrets TruffleHog",
        severity=Severity.HIGH,
        title="Hardcoded Generic Secret",
        file="app.js",
        line=43,
        description="Hardcoded Generic Secret found.",
        code_snippet="secret: 'keyboard cat'"
    )
    result = await enrich_all_findings([finding])
    return result[0]
