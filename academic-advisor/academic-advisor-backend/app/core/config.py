# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache
import os
from dotenv import load_dotenv

# Load .env file first
load_dotenv()

class Settings(BaseSettings):
    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",  # Changed from "ignore" to "allow" to permit extra fields
        validate_default=True
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
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "academic_advisor")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "academic_advisor")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/academic_advisor")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Firebase Config - explicitly get from environment
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")
    FIREBASE_STORAGE_BUCKET: str = os.getenv("FIREBASE_STORAGE_BUCKET", "smart-academic-advisor-system.firebasestorage.app")
    
    # Cloudinary Config
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "diuifufwx")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "362711254198388")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "gpVG8e09wuv-epLdnvyBNJN-Tek")
    CLOUDINARY_UPLOAD_PRESET: str = os.getenv("CLOUDINARY_UPLOAD_PRESET", "student_projects")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # External Services
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

# Use lru_cache for singleton pattern
@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Don't instantiate at module level to avoid circular imports
# Use get_settings() function instead
settings = get_settings()