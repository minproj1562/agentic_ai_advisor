#academic-advisor-backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # App
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Academic Advisor API"
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = "serviceAccountKey.json"
    
    # Databases
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "academic_advisor"
    DATABASE_NAME: str = "academic_advisor"
    
    # PostgreSQL (if needed)
    DATABASE_URL: Optional[str] = "postgresql://user:password@localhost/academic_advisor"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # External Services (Optional)
    SENTRY_DSN: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_UPLOAD_PRESET: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Create settings instance
settings = Settings()