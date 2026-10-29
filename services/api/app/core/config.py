import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "AI QA Agent API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str = "dev_secret_key_change_in_production_min_32_chars_long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    ENCRYPTION_KEY: str = "dGhpcy1pcy1hLTMyLWJ5dGUtc2VjcmV0LWtleS0xMjM0NTY="

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./qa_agent.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # S3 / Cloudflare R2 Object Storage
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "qa-artifacts"
    S3_REGION: str = "auto"
    S3_PUBLIC_URL_PREFIX: Optional[str] = None

    # Cloudflare R2 Convenient Aliases
    R2_ACCOUNT_ID: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_BUCKET_NAME: Optional[str] = None

    @property
    def r2_endpoint_url(self) -> Optional[str]:
        if self.S3_ENDPOINT_URL:
            return self.S3_ENDPOINT_URL
        if self.R2_ACCOUNT_ID:
            return f"https://{self.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        return None

    @property
    def r2_access_key(self) -> Optional[str]:
        return self.S3_ACCESS_KEY_ID or self.R2_ACCESS_KEY_ID

    @property
    def r2_secret_key(self) -> Optional[str]:
        return self.S3_SECRET_ACCESS_KEY or self.R2_SECRET_ACCESS_KEY

    @property
    def r2_bucket(self) -> str:
        return self.R2_BUCKET_NAME or self.S3_BUCKET_NAME or "qa-artifacts"

    # AI Configuration
    AI_PROVIDER: str = "mock"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

settings = Settings()
