import json
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import List, Optional, Any


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/unilink"
    
    # JWT
    SECRET_KEY: str = "change-this-to-a-strong-random-key-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email - SendGrid
    SENDGRID_API_KEY: str = ""
    EMAIL_FROM: str = ""
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Server
    BACKEND_URL: str = "http://localhost:8000"
    ENVIRONMENT: str = "development"
    
    # Security
    ALLOWED_HOSTS: List[str] | str = Field(default_factory=lambda: ["localhost", "127.0.0.1"])
    ALLOWED_ORIGINS: List[str] | str = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"])
    
    # Rate Limiting (requests per minute)
    RATE_LIMIT_AUTH: int = 10
    RATE_LIMIT_API: int = 60
    
    # Sentry Error Tracking
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% of transactions
    
    # App Metadata
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"

    @field_validator("ALLOWED_HOSTS", "ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _parse_list_env(cls, value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if stripped == "":
                return []
            if stripped.startswith("["):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    pass
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return [str(value).strip()]


settings = Settings()
