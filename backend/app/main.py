from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.exceptions import ScanError, scan_error_handler, generic_error_handler
from app.api.scan import router as scan_router
from app.api.queue import router as queue_router
from app.api.webhook import router as webhook_router

limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("startup", version=settings.VERSION)
    yield

app = FastAPI(
    title="SecurePipe API",
    version=settings.VERSION,
    docs_url="/docs",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — wildcard for ngrok compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ngrok interstitial bypass + CORS safety net
@app.middleware("http")
async def add_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        return JSONResponse(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "ngrok-skip-browser-warning": "true",
            }
        )
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

app.add_exception_handler(ScanError, scan_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

app.include_router(scan_router,    prefix="/api/v1", tags=["Scan"])
app.include_router(queue_router,   prefix="/api/v1", tags=["Queue"])
app.include_router(webhook_router, prefix="/api/v1", tags=["Webhook"])

@app.get("/")
async def root():
    return {"name": "SecurePipe", "version": settings.VERSION, "docs": "/docs"}
