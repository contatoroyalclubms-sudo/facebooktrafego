from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/metaads"
    
    REDIS_URL: str = "redis://localhost:6379"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    FACEBOOK_ACCESS_TOKEN: Optional[str] = None
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    FACEBOOK_AD_ACCOUNT_ID: Optional[str] = None
    
    OPENAI_API_KEY: Optional[str] = None
    
    JWT_SECRET_KEY: str = "your-secret-key-here-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    SLACK_WEBHOOK_URL: Optional[str] = None
    
    SENTRY_DSN: Optional[str] = None
    
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Meta Ads Enterprise"
    VERSION: str = "2.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
