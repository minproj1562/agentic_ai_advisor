# academic-advisor-backend/app/main.py
"""
FastAPI Main Application
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

# Import ALL document models (no duplicates)
from app.models.student_profile import StudentProfile
from app.models.student_performance import StudentPerformance
from app.models.student_projects import StudentProject, StudentInterestProfile as ProjectInterestProfile
from app.models.elective import Elective
from app.models.resource import StudyResource
from app.models.weakness import WeaknessAnalysisResult
from app.models.messages import Message, Conversation
from app.models.faculty import Faculty
from app.models.meeting_request import MeetingRequest
from app.models.analytics import Analytics
from app.models.recommendation import (
    RecommendationRecord,
    RecommendationFeedback,
    TrainingDataPoint,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Document models for Beanie (each model listed ONCE)
document_models = [
    StudentProfile,
    StudentPerformance,
    StudentProject,
    ProjectInterestProfile,
    Elective,
    StudyResource,
    WeaknessAnalysisResult,
    Message,
    Conversation,
    Faculty,
    MeetingRequest,
    Analytics,
    RecommendationRecord,
    RecommendationFeedback,
    TrainingDataPoint,
]


def init_firebase():
    """Initialize Firebase Admin SDK only if not already initialized"""
    if not firebase_admin._apps:
        try:
            cred_path = os.getenv(
                "GOOGLE_APPLICATION_CREDENTIALS",
                settings.FIREBASE_CREDENTIALS_PATH
            )
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(
                cred,
                {'storageBucket': settings.FIREBASE_STORAGE_BUCKET}
            )
            logger.info("✅ Firebase Admin SDK initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase: {str(e)}")
            raise


init_firebase()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting up Academic Advisor API...")

    # Initialize MongoDB + Beanie
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        await init_beanie(
            database=client[settings.MONGODB_DATABASE],
            document_models=document_models
        )
        logger.info(f"✅ MongoDB connected — {len(document_models)} document models")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise

    # Load ML models (optional)
    # Auto-train if no saved model exists
    try:
        from app.ml.models.recommendation_engine import recommendation_engine
        logger.info(
            f"✅ Recommendation engine loaded (trained={recommendation_engine.is_trained})"
        )
        
        if not recommendation_engine.is_trained:
            logger.info("🔄 No pre-trained model found. Training with synthetic data...")
            try:
                from app.ml.utils.training import train_recommendation_model
                metrics = await train_recommendation_model(n_synthetic=150, include_feedback=True)
                logger.info(f"✅ Auto-training complete! Accuracy: {metrics['accuracy']:.4f}")
            except Exception as train_err:
                logger.warning(f"⚠️ Auto-training failed (non-critical): {train_err}")
    except Exception as e:
        logger.warning(f"⚠️ Recommendation engine not loaded: {e}")

    yield

    logger.info("👋 Shutting down Academic Advisor API...")
    client.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/")
async def read_root():
    return {
        "message": "Academic Advisor Backend is running",
        "status": "ok",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)