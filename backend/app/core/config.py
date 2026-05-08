from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "SecurePipe"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    SECRET_KEY: str = Field(default="change-me")
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:5173"])
    SUPABASE_URL: str = Field(default="")
    SUPABASE_KEY: str = Field(default="")
    GEMINI_API_KEY: str = Field(default="")
    OPENAI_API_KEY: str = Field(default="")
    AI_ENABLED: bool = Field(default=False)
    MAX_REPO_SIZE_MB: int = Field(default=100)
    SCAN_TIMEOUT_SECONDS: int = Field(default=120)
    TEMP_DIR: str = Field(default="/tmp/securepipe")
    API_KEY: str = Field(default="")
    WEBHOOK_SECRET: str = Field(default="")

    def model_post_init(self, context):
        if self.GEMINI_API_KEY or self.OPENAI_API_KEY:
            object.__setattr__(self, "AI_ENABLED", True)

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
