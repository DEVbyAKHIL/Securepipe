from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.logging import logger

class ScanError(Exception):
    def __init__(self, message, detail, status_code=500):
        self.message = message; self.detail = detail
        self.status_code = status_code; super().__init__(message)

class RepoAccessError(ScanError):
    def __init__(self, url):
        super().__init__("Cannot access repository",
            f"{url} is not accessible. Make sure it is public.", 422)

class RepoTooLargeError(ScanError):
    def __init__(self, size, limit):
        super().__init__("Repository too large",
            f"{size:.1f}MB exceeds {limit}MB limit.", 413)

class ScanTimeoutError(ScanError):
    def __init__(self):
        super().__init__("Scan timed out", "Try a smaller repository.", 504)

async def scan_error_handler(request: Request, exc: ScanError):
    return JSONResponse(status_code=exc.status_code,
        content={"error": exc.message, "detail": exc.detail})

async def generic_error_handler(request: Request, exc: Exception):
    logger.error("unhandled", error=str(exc))
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
