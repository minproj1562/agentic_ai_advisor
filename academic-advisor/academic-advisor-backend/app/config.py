# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # App Config
    APP_NAME: str = "Academic Advisor Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # API Config
    API_V1_STR: str = "/api/v1"
    
    # Database Config
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "academic_advisor"
    DATABASE_NAME: str = "academic_advisor"
    
    # PostgreSQL (for SQLAlchemy models)
    DATABASE_URL: str = "postgresql://user:password@localhost/academic_advisor"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Firebase Config
    FIREBASE_CREDENTIALS_PATH: str = "serviceAccountKey.json"
    FIREBASE_STORAGE_BUCKET: str = "smart-academic-advisor-system.firebasestorage.app"
    
    # Cloudinary Config
    CLOUDINARY_CLOUD_NAME: str = "diuifufwx"
    CLOUDINARY_API_KEY: str = "362711254198388"
    CLOUDINARY_API_SECRET: str = "gpVG8e09wuv-epLdnvyBNJN-Tek"
    CLOUDINARY_UPLOAD_PRESET: str = "student_projects"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # External Services
    OPENAI_API_KEY: Optional[str] = None
    SENTRY_DSN: Optional[str] = None
    
    # ============== Email/Notification Settings ==============
    ENABLE_EMAIL_ALERTS: bool = True
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # ============== YouTube API (Optional - FREE tier available) ==============
    # Get free API key from: https://console.cloud.google.com/apis/credentials
    # Enable "YouTube Data API v3" - gives 10,000 units/day FREE
    YOUTUBE_API_KEY: Optional[str] = None
    
    # CORS - Added port 5173 for Vite
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB


@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Create settings instance for direct import
settings = get_settings()