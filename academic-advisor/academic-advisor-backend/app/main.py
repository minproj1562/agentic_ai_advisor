# app/main.py
"""
FastAPI Main Application
COMPLETE FILE - Updated for chatbot with syllabus support
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
from app.models.pending_marks import PendingStudentMarks

from app.config import settings
from app.api.v1.api import api_router

# ══════════════════════════════════════════════════════════
# IMPORT ALL DOCUMENT MODELS
# ══════════════════════════════════════════════════════════

# Student/Core models
from app.models.student_profile import StudentProfile
from app.models.student_performance import StudentPerformance
from app.models.student_projects import StudentProject, StudentInterestProfile as ProjectInterestProfile
from app.models.elective import Elective
from app.models.resource import StudyResource
from app.models.weakness import WeaknessAnalysisResult
from app.models.weakness import StudentInterestProfile as WeaknessInterestProfile  # ✅ ADD THIS
from app.models.messages import Message, Conversation
from app.models.faculty import Faculty
from app.models.meeting_request import MeetingRequest
from app.models.analytics import Analytics
from app.models.readiness import SubjectRequirementMap, ReadinessResult
from app.models.recommendation import (
    RecommendationRecord,
    RecommendationFeedback,
    TrainingDataPoint,
)

# Chatbot models
from app.models.chatbot import ChatSession, ChatMessage, ChatFeedback, ChatbotAnalyticsDoc
from app.models.career import CareerPath

# Syllabus models - IMPORTANT for chatbot to work
from app.models.syllabus import (
    Department,
    Subject,
    SubjectUnit,
    Topic,
    Abbreviation,
    ProgramElective,
    OpenElective,
    LiberalLearningCourse,
    MDMCourse,
    CreditStructure,
)

# ══════════════════════════════════════════════════════════
# LOGGING CONFIGURATION
# ══════════════════════════════════════════════════════════

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════
# DOCUMENT MODELS FOR BEANIE (COMPLETE LIST)
# ══════════════════════════════════════════════════════════

document_models = [
    # Student/Core models
    StudentProfile,
    StudentPerformance,
    StudentProject,
    ProjectInterestProfile,       # collection: student_interest_profiles (from student_projects.py)
    WeaknessInterestProfile,      # ✅ collection: student_interests (from weakness.py) — THE FIX
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
    SubjectRequirementMap,
    ReadinessResult,
    PendingStudentMarks,  # <-- ADD THIS LINE

    
    # Chatbot models
    ChatSession,
    ChatMessage,
    ChatFeedback,
    ChatbotAnalyticsDoc,
    CareerPath,
    
    # Syllabus models (REQUIRED for chatbot)
    Department,
    Subject,
    SubjectUnit,
    Topic,
    Abbreviation,
    ProgramElective,
    OpenElective,
    LiberalLearningCourse,
    MDMCourse,
    CreditStructure,
]


# ══════════════════════════════════════════════════════════
# FIREBASE INITIALIZATION
# ══════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════
# APPLICATION LIFESPAN
# ══════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting up Academic Advisor API...")

    # ─────────────────────────────────────────────────────
    # 1. Initialize MongoDB + Beanie
    # ─────────────────────────────────────────────────────
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.MONGODB_DATABASE]
        
        await init_beanie(
            database=db,
            document_models=document_models
        )
        logger.info(f"✅ MongoDB connected — {len(document_models)} document models registered")
        
        # Set database reference for repositories
        from app.database.connection import set_database, ensure_indexes
        set_database(client, db)
        
        # Create indexes for optimal query performance
        await ensure_indexes()
        
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise

    # ─────────────────────────────────────────────────────
    # 2. Seed Readiness Data
    # ─────────────────────────────────────────────────────
    try:
        from app.services.readiness_service import get_readiness_service
        svc = get_readiness_service()
        await svc._ensure_seeded()
        logger.info("✅ Readiness requirement maps ready")
    except Exception as e:
        logger.warning(f"⚠️ Readiness seed check: {e}")

    # ─────────────────────────────────────────────────────
    # 3. Seed Career Data (if empty)
    # ─────────────────────────────────────────────────────
    try:
        count = await CareerPath.find().count()
        if count == 0:
            from scripts.seed_career_data import seed_careers
            await seed_careers()
            logger.info("✅ Career data seeded")
        else:
            logger.info(f"✅ Career data ready ({count} paths)")
    except Exception as e:
        logger.warning(f"⚠️ Career seed: {e}")

    # ─────────────────────────────────────────────────────
    # 4. Check Syllabus Data
    # ─────────────────────────────────────────────────────
    try:
        subject_count = await Subject.find().count()
        topic_count = await Topic.find().count()
        dept_count = await Department.find().count()
        
        if subject_count == 0:
            logger.warning("⚠️ No syllabus data found!")
            logger.warning("   Run: python -m scripts.seed_all_chatbot_data")
        else:
            logger.info(f"✅ Syllabus data ready:")
            logger.info(f"   - {dept_count} departments")
            logger.info(f"   - {subject_count} subjects")
            logger.info(f"   - {topic_count} topics")
    except Exception as e:
        logger.warning(f"⚠️ Syllabus check: {e}")

    # ─────────────────────────────────────────────────────
    # 5. Load ML Models (optional)
    # ─────────────────────────────────────────────────────
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

    # ─────────────────────────────────────────────────────
    # 6. Start Background Tasks
    # ─────────────────────────────────────────────────────
    try:
        from app.tasks.meeting_reminders import start_reminder_task
        start_reminder_task()
        logger.info("🔔 Meeting reminder task started")
    except Exception as e:
        logger.warning(f"⚠️ Meeting reminder task failed to start: {e}")

    # ─────────────────────────────────────────────────────
    # STARTUP COMPLETE
    # ─────────────────────────────────────────────────────
    logger.info("=" * 50)
    logger.info("🎉 Academic Advisor API is ready!")
    logger.info(f"   Environment: {settings.ENVIRONMENT}")
    logger.info(f"   API Docs: http://localhost:8000/docs")
    logger.info("=" * 50)

    yield

    # ─────────────────────────────────────────────────────
    # SHUTDOWN
    # ─────────────────────────────────────────────────────
    logger.info("👋 Shutting down Academic Advisor API...")
    client.close()


# ══════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ══════════════════════════════════════════════════════════

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─────────────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )


# ─────────────────────────────────────────────────────
# EXCEPTION HANDLERS
# ─────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ─────────────────────────────────────────────────────
# HEALTH & ROOT ENDPOINTS
# ─────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status."""
    status = {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Check database
    try:
        subject_count = await Subject.find().count()
        career_count = await CareerPath.find().count()
        status["database"] = {
            "connected": True,
            "subjects": subject_count,
            "careers": career_count,
        }
    except Exception as e:
        status["database"] = {"connected": False, "error": str(e)}
    
    return status


@app.get("/")
async def read_root():
    return {
        "message": "Academic Advisor Backend is running",
        "status": "ok",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


# ─────────────────────────────────────────────────────
# API ROUTER
# ─────────────────────────────────────────────────────

app.include_router(api_router, prefix=settings.API_V1_STR)


# ─────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)