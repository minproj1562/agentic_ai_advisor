# academic-advisor-backend/app/main.py

from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Form, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager
import logging
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import firebase_admin
from firebase_admin import credentials, storage
from PyPDF2 import PdfReader
import io
from datetime import datetime
from typing import Optional, List
from app.config import settings
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==================== IMPORT ONLY DOCUMENT MODELS ====================
# DO NOT import BaseModel classes (like SemesterRecord, SubjectScore) here

from app.models.student_profile import StudentProfile

# Import other Document models with error handling
document_models = [StudentProfile]

try:
    from app.models.student_performance import StudentPerformance
    document_models.append(StudentPerformance)
except ImportError as e:
    logger.warning(f"Could not import StudentPerformance: {e}")

try:
    from app.models.student_project import StudentProject
    document_models.append(StudentProject)
except ImportError as e:
    logger.warning(f"Could not import StudentProject: {e}")

try:
    from app.models.student_interest_profile import StudentInterestProfile
    document_models.append(StudentInterestProfile)
except ImportError as e:
    logger.warning(f"Could not import StudentInterestProfile: {e}")

try:
    from app.models.study_resource import StudyResource
    document_models.append(StudyResource)
except ImportError as e:
    logger.warning(f"Could not import StudyResource: {e}")

try:
    from app.models.research_area import ResearchArea
    document_models.append(ResearchArea)
except ImportError as e:
    logger.warning(f"Could not import ResearchArea: {e}")

try:
    from app.models.publication import Publication
    document_models.append(Publication)
except ImportError as e:
    logger.warning(f"Could not import Publication: {e}")

try:
    from app.models.elective import Elective
    document_models.append(Elective)
except ImportError as e:
    logger.warning(f"Could not import Elective: {e}")

try:
    from app.models.instructor_info import InstructorInfo
    document_models.append(InstructorInfo)
except ImportError as e:
    logger.warning(f"Could not import InstructorInfo: {e}")

try:
    from app.models.message import Message
    document_models.append(Message)
except ImportError as e:
    logger.warning(f"Could not import Message: {e}")

try:
    from app.models.conversation import Conversation
    document_models.append(Conversation)
except ImportError as e:
    logger.warning(f"Could not import Conversation: {e}")

try:
    from app.models.weakness_analysis import WeaknessAnalysisResult
    document_models.append(WeaknessAnalysisResult)
except ImportError as e:
    logger.warning(f"Could not import WeaknessAnalysisResult: {e}")

try:
    from app.models.analytics import Analytics
    document_models.append(Analytics)
except ImportError as e:
    logger.warning(f"Could not import Analytics: {e}")

try:
    from app.models.mentorship import (
        MentorshipSlot,
        MentorshipSession,
        FacultyMentorshipSettings,
        MentorshipStatistics
    )
    document_models.extend([
        MentorshipSlot,
        MentorshipSession,
        FacultyMentorshipSettings,
        MentorshipStatistics
    ])
except ImportError as e:
    logger.warning(f"Could not import Mentorship models: {e}")

# Filter out None values
document_models = [m for m in document_models if m is not None]

logger.info(f"Document models to initialize: {[m.__name__ for m in document_models]}")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize Firebase Admin
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(
            cred, 
            {'storageBucket': settings.FIREBASE_STORAGE_BUCKET}
        )
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {str(e)}")
        raise

MAX_FILE_SIZE = settings.MAX_FILE_SIZE


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Enhanced user validation integrating Firebase"""
    from app.core.security import verify_firebase_token
    try:
        decoded = await verify_firebase_token(token)
        return decoded['uid']
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enhanced application lifespan manager"""
    # Startup
    logger.info("Starting up Academic Advisor API...")
    
    # Initialize MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    # Initialize Beanie with ONLY Document models
    await init_beanie(
        database=client[settings.MONGODB_DATABASE],
        document_models=document_models
    )
    logger.info(f"MongoDB connected successfully. Initialized {len(document_models)} document models.")
    
    # Initialize ML models
    try:
        from app.ml.elective_recommender import ElectiveRecommender
        from app.ml.weakness_predictor import WeaknessAnalyzer
        app.state.elective_recommender = ElectiveRecommender()
        app.state.weakness_analyzer = WeaknessAnalyzer()
        logger.info("ML models loaded successfully")
    except Exception as e:
        logger.warning(f"ML models failed to load: {e}")
        app.state.elective_recommender = None
        app.state.weakness_analyzer = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down Academic Advisor API...")
    client.close()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173", 
        "http://localhost:3000",
        "http://localhost:5174",
        "https://localhost:5173",
        "https://127.0.0.1:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)


# Add OPTIONS handler for preflight requests
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return {"message": "OK"}


# Enhanced exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) if settings.DEBUG else "Internal server error"}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "document_models": len(document_models),
        "timestamp": datetime.utcnow().isoformat()
    }


# Root endpoint
@app.get("/")
async def read_root():
    return {
        "message": "Academic Advisor Backend is running", 
        "status": "ok", 
        "version": settings.APP_VERSION,
        "time": datetime.utcnow().isoformat()
    }


# Enhanced CV Upload Endpoint
@app.post("/parse-cv")
async def parse_cv(
    cv: UploadFile = File(...),
    uid: str = Form(...),
    authorization: Optional[str] = Header(None),
    current_user: str = Depends(get_current_user)
):
    """Enhanced CV upload with validation and Firebase storage"""
    if not cv.content_type == "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    cv_size = await cv.seek(0, io.SEEK_END)
    await cv.seek(0)
    if cv_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File size must be less than {MAX_FILE_SIZE//1024//1024}MB")

    if uid != current_user:
        raise HTTPException(status_code=403, detail="Unauthorized: UID mismatch")

    try:
        pdf_content = await cv.read()
        pdf = PdfReader(io.BytesIO(pdf_content))
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""

        from app.services.cv_parser import parse_cv_text
        expertise = parse_cv_text(text)

        bucket = storage.bucket()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        blob_name = f"cvs/{uid}/{timestamp}_{cv.filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(pdf_content, content_type="application/pdf")

        url = blob.generate_signed_url(
            expiration=datetime(2025, 12, 31),
            method="GET"
        )

        logger.info(f"CV uploaded for uid {uid}: {url}")
        return {
            "message": "CV uploaded and parsed successfully",
            "uid": uid,
            "cv_url": url,
            "expertise": expertise,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"CV processing failed for uid {uid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CV processing failed: {str(e)}")


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )