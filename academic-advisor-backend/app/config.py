# app/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path
import secrets
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Academic Advisor API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # API
    API_V1_STR: str = "/api/v1"
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "https://yourfrontend.com",
        "https://academic-advisor.com"
    ]
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "https://yourfrontend.com",
        "https://academic-advisor.com"
    ]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = os.getenv(
        "FIREBASE_CREDENTIALS_PATH", 
        "serviceAccountKey.json"
    )
    FIREBASE_STORAGE_BUCKET: str = "academic-advisor-6ed1a.appspot.com"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost/academic_advisor"
    )
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/academic_advisor")
    MONGODB_DATABASE: str = "academic_advisor"
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TTL: int = 3600
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".doc", ".docx"]
    
    # ML Models
    ML_MODELS_PATH: str = "./ml_models"
    SKILL_MODEL_PATH: str = "app/ml/models/skill_extractor.pkl"
    NER_MODEL_PATH: str = "app/ml/models/ner_model"
    SIMILARITY_THRESHOLD: float = 0.75
    
    # External Services
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_SCHOLAR_API_KEY: Optional[str] = os.getenv("GOOGLE_SCHOLAR_API_KEY")
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    
    # Monitoring
    ENABLE_METRICS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()