import os, shutil, uuid, asyncio
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.exceptions import RepoAccessError, RepoTooLargeError, ScanTimeoutError
from app.core.logging import logger

def size_mb(path):
    total = 0
    for dp, dns, fns in os.walk(path):
        dns[:] = [d for d in dns if d != ".git"]
        for fn in fns:
            try: total += os.path.getsize(os.path.join(dp, fn))
            except: pass
    return total / 1_048_576

@asynccontextmanager
async def cloned_repo(repo_url: str, branch: str = "main"):
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    dest = os.path.join(settings.TEMP_DIR, "repo_" + uuid.uuid4().hex[:10])
    try:
        cmd = ["git","clone","--depth","1","--branch",branch,"--single-branch",repo_url,dest]
        proc = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            _, err = await asyncio.wait_for(proc.communicate(),
                timeout=settings.SCAN_TIMEOUT_SECONDS)
            if proc.returncode != 0:
                raise RepoAccessError(repo_url)
        except asyncio.TimeoutError:
            raise ScanTimeoutError()
        mb = size_mb(dest)
        if mb > settings.MAX_REPO_SIZE_MB:
            raise RepoTooLargeError(mb, settings.MAX_REPO_SIZE_MB)
        logger.info("repo_ready", mb=round(mb, 2))
        yield dest
    finally:
        if os.path.exists(dest):
            shutil.rmtree(dest, ignore_errors=True)
