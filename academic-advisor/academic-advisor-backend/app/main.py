# academic-advisor-backend/app/main.py
"""
FastAPI Main Application - FIXED
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import firebase_admin
from firebase_admin import credentials
from datetime import datetime
import os

from app.config import settings
from app.api.v1.api import api_router

# Import document models - ADD StudentProfile
from app.models.student_profile import StudentProfile  # ← ADD THIS LINE
from app.models.student_performance import StudentPerformance
from app.models.elective import Elective
from app.models.resource import StudyResource
from app.models.weakness import WeaknessAnalysisResult
from app.models.messages import Message, Conversation
from app.models.faculty import Faculty
from app.models.meeting_request import MeetingRequest

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Document models for Beanie - ADD StudentProfile
document_models = [
    StudentProfile,          # ← ADD THIS LINE
    StudentPerformance,
    Elective,
    StudyResource,
    WeaknessAnalysisResult,
    Message,
    Conversation,
    Faculty,
    MeetingRequest
]

# Initialize Firebase Admin (only once)
def init_firebase():
    """Initialize Firebase Admin SDK only if not already initialized"""
    if not firebase_admin._apps:
        try:
            cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", settings.FIREBASE_CREDENTIALS_PATH)
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(
                cred, 
                {'storageBucket': settings.FIREBASE_STORAGE_BUCKET}
            )
            logger.info("✅ Firebase Admin SDK initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase: {str(e)}")
            raise

# Initialize Firebase at module load
init_firebase()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting up Academic Advisor API...")
    
    # Initialize MongoDB
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        await init_beanie(
            database=client[settings.MONGODB_DATABASE],
            document_models=document_models
        )
        logger.info("✅ MongoDB connected successfully")
        logger.info(f"📊 Initialized {len(document_models)} document models")  # ← OPTIONAL: Add this for debugging
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise
    
    # Initialize ML models (optional - don't fail if not available)
    try:
        from app.ml.elective_recommender import ElectiveRecommender
        from app.ml.weakness_predictor import WeaknessAnalyzer
        app.state.elective_recommender = ElectiveRecommender()
        app.state.weakness_analyzer = WeaknessAnalyzer()
        logger.info("✅ ML models loaded successfully")
    except Exception as e:
        logger.warning(f"⚠️ ML models not loaded: {e}")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down Academic Advisor API...")
    client.close()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }


# Root endpoint
@app.get("/")
async def read_root():
    return {
        "message": "Academic Advisor Backend is running", 
        "status": "ok", 
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "time": datetime.utcnow().isoformat()
    }


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )