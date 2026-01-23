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
import os
from datetime import datetime
from typing import Optional
from app.config import settings
from app.api.v1.api import api_router

# ============== UPDATED IMPORTS - Include ALL Document Models ==============
from app.models import (
    # Student models
    StudentPerformance,
    StudentProfile,           # ← ADDED
    StudentProject,           # ← ADDED
    StudentInterestProfile,   # ← ADDED
    
    # Academic models
    Elective,
    StudyResource,
    
    # Research & Publications
    ResearchArea,             # ← ADDED
    Publication,              # ← ADDED
    
    # Analysis models
    WeaknessAnalysisResult,
    Analytics,                # ← ADDED
    
    # Messaging models
    Message,
    Conversation,
    
    # Mentorship models
    MentorshipSlot,           # ← ADDED
    MentorshipSession,        # ← ADDED
    FacultyMentorshipSettings,# ← ADDED
    MentorshipStatistics,     # ← ADDED
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============== UPDATED: Complete Document Models List for Beanie ==============
document_models = [
    # Student models
    StudentPerformance,
    StudentProfile,
    StudentProject,
    StudentInterestProfile,
    
    # Academic models
    Elective,
    StudyResource,
    
    # Research & Publications
    ResearchArea,
    Publication,
    
    # Analysis models
    WeaknessAnalysisResult,
    Analytics,
    
    # Messaging models
    Message,
    Conversation,
    
    # Mentorship models
    MentorshipSlot,
    MentorshipSession,
    FacultyMentorshipSettings,
    MentorshipStatistics,
]

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize Firebase Admin (only once)
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

MAX_FILE_SIZE = settings.MAX_FILE_SIZE  # 10MB from config


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
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        
        # ============== ADDED: Test connection before init ==============
        await client.admin.command('ping')
        logger.info("MongoDB connection successful")
        
        await init_beanie(
            database=client[settings.MONGODB_DATABASE],
            document_models=document_models
        )
        logger.info(f"Beanie initialized with {len(document_models)} document models:")
        for model in document_models:
            logger.info(f"  - {model.__name__}")
            
    except Exception as e:
        logger.error(f"MongoDB/Beanie initialization failed: {e}")
        raise
    
    # Initialize ML models
    try:
        from app.ml.elective_recommender import ElectiveRecommender
        from app.ml.weakness_predictor import WeaknessAnalyzer
        app.state.elective_recommender = ElectiveRecommender()
        app.state.weakness_analyzer = WeaknessAnalyzer()
        logger.info("ML models loaded successfully")
    except Exception as e:
        logger.warning(f"ML models could not be loaded: {e}")
    
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

# CORS middleware - use settings for origins (includes 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)


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
        "timestamp": datetime.utcnow().isoformat(),
        "document_models_loaded": len(document_models)
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


# CV Upload Endpoint
@app.post("/parse-cv")
async def parse_cv(
    cv: UploadFile = File(...),
    uid: str = Form(...),
    authorization: Optional[str] = Header(None),
    current_user: str = Depends(get_current_user)
):
    """CV upload with validation and Firebase storage"""
    # Validate file type
    if not cv.content_type == "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Validate file size
    content = await cv.read()
    await cv.seek(0)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File size must be less than {MAX_FILE_SIZE//1024//1024}MB")

    # Validate uid
    if uid != current_user:
        raise HTTPException(status_code=403, detail="Unauthorized: UID mismatch")

    # Read and parse PDF
    try:
        pdf_content = await cv.read()
        pdf = PdfReader(io.BytesIO(pdf_content))
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""

        # Enhanced parsing
        from app.services.cv_parser import parse_cv_text
        expertise = parse_cv_text(text)

        # Upload to Firebase Storage
        bucket = storage.bucket()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        blob_name = f"cvs/{uid}/{timestamp}_{cv.filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(pdf_content, content_type="application/pdf")

        # Generate signed URL
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


# Debug endpoint to verify Beanie initialization
@app.get("/debug/beanie-status")
async def debug_beanie_status():
    """Debug endpoint to check Beanie document models status"""
    status = {}
    for model in document_models:
        try:
            # Try to access the collection
            collection_name = model.Settings.name if hasattr(model, 'Settings') and hasattr(model.Settings, 'name') else model.__name__.lower()
            count = await model.count()
            status[model.__name__] = {
                "collection": collection_name,
                "initialized": True,
                "document_count": count
            }
        except Exception as e:
            status[model.__name__] = {
                "initialized": False,
                "error": str(e)
            }
    
    return {
        "total_models": len(document_models),
        "models_status": status
    }


@app.get("/debug/verify-token")
async def debug_verify_token(authorization: Optional[str] = Header(None)):
    """Debug endpoint to test token verification"""
    from app.core.firebase import verify_firebase_token, get_firebase_app
    
    # Check Firebase initialization
    try:
        firebase_app = get_firebase_app()
        firebase_status = "initialized"
    except Exception as e:
        firebase_status = f"error: {str(e)}"
    
    if not authorization:
        return {
            "status": "error",
            "message": "No Authorization header provided",
            "firebase_status": firebase_status,
            "hint": "Send request with header: Authorization: Bearer <your-token>"
        }
    
    # Extract token
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return {
            "status": "error", 
            "message": "Invalid Authorization header format",
            "expected": "Bearer <token>",
            "received": authorization[:50] + "..." if len(authorization) > 50 else authorization
        }
    
    token = parts[1]
    
    # Token info
    token_info = {
        "length": len(token),
        "parts": len(token.split(".")),
        "preview": token[:20] + "..." + token[-20:] if len(token) > 50 else token
    }
    
    # Try to verify
    try:
        decoded = verify_firebase_token(token)
        return {
            "status": "success",
            "message": "Token verified successfully",
            "firebase_status": firebase_status,
            "token_info": token_info,
            "decoded": {
                "uid": decoded.get("uid"),
                "email": decoded.get("email"),
                "email_verified": decoded.get("email_verified"),
                "auth_time": decoded.get("auth_time"),
                "iat": decoded.get("iat"),
                "exp": decoded.get("exp")
            }
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__,
            "firebase_status": firebase_status,
            "token_info": token_info,
            "traceback": traceback.format_exc()
        }


# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )