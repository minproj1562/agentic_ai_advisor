# academic-advisor-backend/main.py
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
from typing import Optional
from app.config import settings
from app.api.v1.api import api_router
from app.models import (
    StudentPerformance,
    Elective,
    StudyResource,
    WeaknessAnalysisResult,
    StudentResourceActivity,
    Message,
    Conversation
)

cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
cred = credentials.Certificate(cred_path)
initialize_app(cred)
# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Document models for Beanie
document_models = [
    StudentPerformance,
    Elective,
    StudyResource,
    WeaknessAnalysisResult,
    StudentResourceActivity,
    Message,
    Conversation
]

# OAuth2 scheme (enhanced)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize Firebase Admin (production-ready)
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
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.MONGODB_DATABASE],
        document_models=document_models
    )
    logger.info("MongoDB connected successfully")
    
    # Initialize ML models
    from app.ml.elective_recommender import ElectiveRecommender
    from app.ml.weakness_predictor import WeaknessAnalyzer
    app.state.elective_recommender = ElectiveRecommender()
    app.state.weakness_analyzer = WeaknessAnalyzer()
    logger.info("ML models loaded successfully")
    
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

# Enhanced CORS middleware (merged origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        content={"detail": "Internal server error"}
    )

# Health check endpoint (enhanced)
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }

# Root endpoint (enhanced)
@app.get("/")
async def read_root():
    return {
        "message": "Academic Advisor Backend is running", 
        "status": "ok", 
        "version": settings.APP_VERSION,
        "time": datetime.utcnow().isoformat()
    }

# Enhanced CV Upload Endpoint (production-ready)
@app.post("/parse-cv")
async def parse_cv(
    cv: UploadFile = File(...),
    uid: str = Form(...),
    authorization: Optional[str] = Header(None),
    current_user: str = Depends(get_current_user)
):
    """Enhanced CV upload with validation and Firebase storage"""
    # Validate file type
    if not cv.content_type == "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Validate file size
    cv_size = await cv.seek(0, io.SEEK_END)
    await cv.seek(0)
    if cv_size > MAX_FILE_SIZE:
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

        # Enhanced parsing (integrate with your NLP service)
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

# Main entry point (production-ready)
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )