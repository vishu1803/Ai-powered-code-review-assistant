from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, List, Any
from functools import lru_cache
import secrets
import os

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Code Review Assistant"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-powered code review assistant for modern development teams"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production-minimum-32-characters"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200
    ALGORITHM: str = "HS256"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "https://localhost:8000",
    ]
    
    BASE_URL: str = "http://localhost:8000"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database - Direct URLs (matching your .env structure)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/ai_code_review"
    DATABASE_URL_SYNC: str = "postgresql://postgres:password@localhost:5432/ai_code_review"
    
    # Required for backward compatibility (set defaults)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres" 
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "ai_code_review"
    POSTGRES_PORT: str = "5432"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # AI Configuration
    OPENAI_API_KEY: Optional[str] = None
    DEFAULT_AI_MODEL: str = "gpt-4"
    MAX_TOKENS: int = 4000
    TEMPERATURE: float = 0.1
    
    # GitHub Integration
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    
    # GitLab Integration
    GITLAB_CLIENT_ID: Optional[str] = None
    GITLAB_CLIENT_SECRET: Optional[str] = None
    GITLAB_WEBHOOK_SECRET: Optional[str] = None
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # CORS (from your .env)
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]
    
    # Testing
    TESTING: bool = False
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
