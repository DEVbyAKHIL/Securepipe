import os, shutil, uuid, asyncio, subprocess
from contextlib import asynccontextmanager
from typing import Optional
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

def _git_clone(cmd: list, env: dict, timeout: int) -> int:
    """Run git clone synchronously (called via asyncio.to_thread to avoid
    asyncio.create_subprocess_exec which requires ProactorEventLoop on Windows)."""
    result = subprocess.run(
        cmd, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=timeout,
    )
    return result.returncode

@asynccontextmanager
async def cloned_repo(repo_url: str, branch: Optional[str] = None):
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    dest = os.path.join(settings.TEMP_DIR, "repo_" + uuid.uuid4().hex[:10])
    try:
        cmd = ["git", "clone", "--depth", "1", "--single-branch"]
        if branch:
            cmd.extend(["--branch", branch])
        cmd.extend([repo_url, dest])
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GCM_INTERACTIVE"] = "false"
        env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new"
        try:
            returncode = await asyncio.wait_for(
                asyncio.to_thread(_git_clone, cmd, env, settings.SCAN_TIMEOUT_SECONDS),
                timeout=settings.SCAN_TIMEOUT_SECONDS + 5,
            )
        except asyncio.TimeoutError:
            raise ScanTimeoutError()
        if returncode != 0:
            raise RepoAccessError(repo_url)
        mb = size_mb(dest)
        if mb > settings.MAX_REPO_SIZE_MB:
            raise RepoTooLargeError(mb, settings.MAX_REPO_SIZE_MB)
        logger.info("repo_ready", mb=round(mb, 2))
        yield dest
    finally:
        if os.path.exists(dest):
            shutil.rmtree(dest, ignore_errors=True)
