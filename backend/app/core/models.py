from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"
    INFO     = "info"

class ScanStatus(str, Enum):
    QUEUED    = "queued"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"

class ScanRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None

    @field_validator("repo_url")
    @classmethod
    def validate_url(cls, v):
        v = v.strip()
        if not any(h in v for h in ["github.com", "gitlab.com", "bitbucket.org"]):
            raise ValueError("Only GitHub/GitLab/Bitbucket supported.")
        if not v.startswith("https"):
            v = "https://" + v
        return v.removesuffix(".git")

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, v):
        if v is None:
            return v
        if not re.match(r"^[a-zA-Z0-9._/-]+$", v.strip()):
            raise ValueError("Invalid branch name.")
        return v.strip()

class Finding(BaseModel):
    id: str; scanner: str; severity: Severity
    title: str; description: str; file: str
    line: Optional[int] = None; vuln_type: str = ""
    cve: Optional[str] = None; cvss: Optional[float] = None
    suggestion: str = ""; suggestion_source: str = "unavailable"
    model: Optional[str] = None; error_reason: Optional[str] = None
    code_snippet: Optional[str] = None
    references: List[str] = []

class ScanCounts(BaseModel):
    critical: int = 0; high: int = 0
    medium: int = 0; low: int = 0; total: int = 0

class ScanResult(BaseModel):
    scan_id: str; repo_url: str; repo_name: str; branch: Optional[str] = None
    status: ScanStatus; findings: List[Finding] = []
    counts: ScanCounts = ScanCounts(); score: Optional[int] = None
    duration_seconds: Optional[float] = None; scanners_used: List[str] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class HistoryScan(BaseModel):
    scan_id: str; repo_url: str; repo_name: str; branch: Optional[str] = None
    status: ScanStatus; score: Optional[int] = None
    counts: ScanCounts = ScanCounts()
    duration_seconds: Optional[float] = None
    completed_at: Optional[datetime] = None

class HealthResponse(BaseModel):
    status: str; version: str; environment: str
    ai_enabled: bool; db_connected: bool
