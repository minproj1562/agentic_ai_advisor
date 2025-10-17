# app/api/v1/cv.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

from app.core.security import get_current_user
from app.core.firebase import get_storage_bucket
from app.models.cv import CVUpload, CVAnalysis, ParsedCV
from app.services.cv_parser import CVParser
from app.services.nlp_service import NLPService
from app.services.skill_extractor import SkillExtractor
from app.utils.validators import validate_file
from app.core.exceptions import CustomException
from app.config import settings

router = APIRouter()

cv_parser = CVParser()
nlp_service = NLPService()
skill_extractor = SkillExtractor()

@router.post("/upload")
async def upload_cv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and process CV with advanced NLP analysis
    """
    try:
        # Validate file
        validation_result = await validate_file(
            file,
            max_size=settings.MAX_FILE_SIZE,
            allowed_types=settings.ALLOWED_FILE_TYPES
        )
        
        if not validation_result["valid"]:
            raise CustomException(
                status_code=400,
                detail=validation_result["error"],
                code="INVALID_FILE"
            )
        
        # Generate unique ID for this upload
        upload_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        
        # Upload to Firebase Storage
        bucket = get_storage_bucket()
        blob_name = f"cvs/{current_user['uid']}/{upload_id}/{file.filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content, content_type=file.content_type)
        
        # Generate signed URL
        file_url = blob.generate_signed_url(
            expiration=datetime(2025, 12, 31),
            method="GET"
        )
        
        # Start background processing
        background_tasks.add_task(
            process_cv_background,
            upload_id=upload_id,
            file_content=content,
            file_name=file.filename,
            user_id=current_user['uid']
        )
        
        return JSONResponse(
            status_code=202,
            content={
                "upload_id": upload_id,
                "status": "processing",
                "file_url": file_url,
                "message": "CV uploaded successfully. Processing in background."
            }
        )
        
    except CustomException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_cv_background(
    upload_id: str,
    file_content: bytes,
    file_name: str,
    user_id: str
):
    """
    Background task for CV processing
    """
    try:
        # Parse CV
        parsed_data = await cv_parser.parse(file_content, file_name)
        
        # Extract skills
        skills = await skill_extractor.extract(parsed_data["text"])
        
        # Perform NLP analysis
        nlp_analysis = await nlp_service.analyze(parsed_data["text"])
        
        # Store results in database
        analysis_result = CVAnalysis(
            upload_id=upload_id,
            user_id=user_id,
            parsed_data=parsed_data,
            skills=skills,
            nlp_analysis=nlp_analysis,
            status="completed",
            completed_at=datetime.utcnow()
        )
        
        # Save to database (implement your database logic)
        # await save_analysis_to_db(analysis_result)
        
        # Send notification to user (via WebSocket or notification service)
        # await notify_user(user_id, upload_id, "completed")
        
    except Exception as e:
        # Log error and update status
        print(f"Error processing CV {upload_id}: {str(e)}")
        # await update_status(upload_id, "failed", str(e))

@router.get("/status/{upload_id}")
async def get_processing_status(
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get CV processing status
    """
    # Implement database lookup
    # status = await get_status_from_db(upload_id, current_user['uid'])
    
    return {
        "upload_id": upload_id,
        "status": "completed",  # or "processing", "failed"
        "progress": 100,
        "result_url": f"/api/v1/cv/results/{upload_id}"
    }

@router.get("/results/{upload_id}")
async def get_cv_results(
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get processed CV results
    """
    # Implement database lookup
    # results = await get_results_from_db(upload_id, current_user['uid'])
    
    # Mock response for now
    return {
        "upload_id": upload_id,
        "skills": [
            {"name": "Python", "confidence": 95, "category": "Programming"},
            {"name": "Machine Learning", "confidence": 88, "category": "AI/ML"},
            {"name": "React", "confidence": 82, "category": "Frontend"}
        ],
        "experience": {
            "total_years": 5,
            "positions": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corp",
                    "duration": "2 years"
                }
            ]
        },
        "education": [
            {
                "degree": "Master of Science",
                "field": "Computer Science",
                "institution": "University"
            }
        ],
        "analysis": {
            "suitability_score": 85,
            "recommendations": [
                "Strong technical background",
                "Consider adding cloud certifications"
            ]
        }
    }

@router.delete("/{upload_id}")
async def delete_cv(
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete uploaded CV and its analysis
    """
    # Implement deletion logic
    return {"message": "CV deleted successfully"}