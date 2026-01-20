from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/unilink"
    
    # JWT
    SECRET_KEY: str = "change-this-to-a-strong-random-key-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Server
    BACKEND_URL: str = "http://localhost:8000"
    ENVIRONMENT: str = "development"
    
    # Security
    ALLOWED_HOSTS: list = ["localhost", "127.0.0.1"]
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    # Rate Limiting (requests per minute)
    RATE_LIMIT_AUTH: int = 10
    RATE_LIMIT_API: int = 60
    
    class Config:
        env_file = ".env"


settings = Settings()
