#academic-advisor-backend/app/api/v1/cv.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
import logging

from app.core.security import get_current_user
from app.core.firebase import get_storage_bucket, generate_signed_url
from app.models.cv import (
    CVUpload, CVAnalysis, ParsedCV, CVUploadResponse, CVStatusResponse, 
    CVAnalysisResponse, ProcessingStatus, FileValidationResult, CVValidationResult
)
from app.services.cv_parser import CVParser
from app.services.nlp_service import NLPService
from app.services.skill_extractor import SkillExtractor
from app.services.research_service import ResearchAreaService
from app.utils.validators import validate_file, validate_cv_content, validate_parsed_cv_data
from app.core.exceptions import CustomException
from app.core.config import settings

router = APIRouter()

cv_parser = CVParser()
nlp_service = NLPService()
skill_extractor = SkillExtractor()
research_service = ResearchAreaService()

logger = logging.getLogger(__name__)

@router.post("/upload", response_model=CVUploadResponse)
async def upload_cv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and process CV with advanced NLP analysis and research area extraction
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
                code=validation_result.get("code", "VALIDATION_ERROR")
            )
        
        # Generate unique ID for this upload
        upload_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        
        # Parse CV content for initial validation
        try:
            parsed_data = await cv_parser.parse(content, file.filename)
            content_validation = await validate_cv_content(parsed_data["text"])
            
            if not content_validation["valid"]:
                raise CustomException(
                    status_code=400,
                    detail=content_validation["error"],
                    code=content_validation.get("code", "INVALID_CONTENT")
                )
                
            # Validate parsed data structure
            parsed_validation = await validate_parsed_cv_data(parsed_data)
            if not parsed_validation["valid"]:
                logger.warning(f"Parsed data validation issues for {upload_id}: {parsed_validation}")
                
        except Exception as e:
            logger.error(f"CV parsing failed during validation: {str(e)}")
            raise CustomException(
                status_code=400,
                detail=f"Failed to parse CV content: {str(e)}",
                code="PARSING_FAILED"
            )
        
        # Upload to Firebase Storage
        bucket = get_storage_bucket()
        blob_name = f"cvs/{current_user.uid}/{upload_id}/{file.filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content, content_type=file.content_type)
        
        # Generate signed URL
        file_url = generate_signed_url(blob, expiration_hours=8760)  # 1 year
        
        # Create CV upload record
        cv_upload = CVUpload(
            upload_id=upload_id,
            user_id=current_user.uid,
            file_name=file.filename,
            file_url=file_url,
            file_size=len(content),
            mime_type=file.content_type or "application/octet-stream",
            uploaded_at=datetime.utcnow(),
            status=ProcessingStatus.PENDING,
            validation_results={
                "file_validation": validation_result,
                "content_validation": content_validation,
                "parsed_validation": parsed_validation
            }
        )
        
        # Save upload record to database (implement your database logic)
        # await save_cv_upload_to_db(cv_upload)
        
        # Start background processing
        background_tasks.add_task(
            process_cv_background,
            upload_id=upload_id,
            file_content=content,
            file_name=file.filename,
            user_id=current_user.uid,
            cv_upload_data=cv_upload.dict()
        )
        
        return CVUploadResponse(
            upload_id=upload_id,
            status="processing",
            file_url=file_url,
            message="CV uploaded successfully. Processing in background.",
            validation={
                "file_validation": FileValidationResult(**validation_result),
                "content_validation": CVValidationResult(**content_validation),
                "parsed_validation": CVValidationResult(**parsed_validation)
            },
            estimated_processing_time=45  # seconds
        )
        
    except CustomException as e:
        raise e
    except Exception as e:
        logger.error(f"CV upload error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="CV upload failed due to server error"
        )

async def process_cv_background(
    upload_id: str,
    file_content: bytes,
    file_name: str,
    user_id: str,
    cv_upload_data: Dict[str, Any]
):
    """
    Background task for comprehensive CV processing
    """
    try:
        # Update status to processing
        # await update_upload_status(upload_id, ProcessingStatus.PROCESSING)
        
        # Parse CV with enhanced parser
        parsed_data = await cv_parser.parse(file_content, file_name)
        
        # Perform comprehensive skill extraction
        skill_analysis = await skill_extractor.extract_comprehensive(parsed_data["text"])
        
        # Perform advanced NLP analysis
        nlp_analysis = await nlp_service.analyze_cv_comprehensive(parsed_data["text"])
        
        # Extract research areas and create research profile
        research_analysis = await research_service.extract_research_areas_from_cv(parsed_data["text"], user_id)
        research_potential = await research_service.analyze_cv_for_research_potential(parsed_data["text"])
        
        # Create comprehensive analysis result
        analysis_result = CVAnalysis(
            upload_id=upload_id,
            user_id=user_id,
            parsed_data=ParsedCV(
                text=parsed_data["text"],
                sections=parsed_data.get("sections", {}),
                metadata=parsed_data.get("metadata", {}),
                word_count=parsed_data.get("word_count", 0),
                extraction_methods=parsed_data.get("extraction_methods", []),
                extraction_success=parsed_data.get("extraction_success", True),
                quality_score=parsed_data.get("quality_score")
            ),
            skills=skill_analysis.get("skills", []),
            research_areas=skill_analysis.get("research_areas", []),
            expertise_levels=skill_analysis.get("expertise_levels", {}),
            research_themes=skill_analysis.get("research_themes", []),
            research_profile=skill_analysis.get("research_profile"),
            nlp_analysis=nlp_analysis,
            entities=nlp_analysis.get("entities"),
            education_analysis=nlp_analysis.get("education"),
            experience_analysis=nlp_analysis.get("experience"),
            personal_info=nlp_analysis.get("personal_info"),
            writing_analysis=nlp_analysis.get("writing_analysis"),
            achievements=nlp_analysis.get("achievements", []),
            document_metrics=nlp_analysis.get("document_metrics"),
            status=ProcessingStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            suitability_score=research_potential.get("research_potential_score"),
            recommendations=research_potential.get("recommendations", [])
        )
        
        # Calculate summary
        summary = await create_cv_summary(analysis_result, research_potential)
        
        # Save results to database
        # await save_analysis_to_db(analysis_result)
        # await save_research_areas_to_db(research_analysis)
        
        # Update upload status
        # await update_upload_status(upload_id, ProcessingStatus.COMPLETED)
        
        # Send notification to user
        # await notify_user(user_id, upload_id, "completed", summary)
        
        logger.info(f"CV processing completed for upload_id: {upload_id}")
        
    except Exception as e:
        logger.error(f"Error processing CV {upload_id}: {str(e)}")
        # await update_upload_status(upload_id, ProcessingStatus.FAILED, str(e))
        # await notify_user(user_id, upload_id, "failed", {"error": str(e)})

async def create_cv_summary(analysis: CVAnalysis, research_potential: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a comprehensive CV summary
    """
    # Extract key skills (top 10 by importance)
    key_skills = sorted(
        analysis.skills, 
        key=lambda x: x.importance_score or 0, 
        reverse=True
    )[:10]
    
    # Calculate total experience
    total_experience = analysis.experience_analysis.total_experience_years if analysis.experience_analysis else 0
    
    # Get highest education
    highest_education = analysis.education_analysis.highest_degree if analysis.education_analysis else "Unknown"
    
    # Calculate overall score
    score = analysis.suitability_score or 70  # Default score
    
    # Get research focus
    research_focus = analysis.research_profile.research_focus if analysis.research_profile else "General"
    
    # Get technical competencies
    technical_competencies = [
        skill.name for skill in analysis.research_profile.technical_competencies 
        if analysis.research_profile
    ][:5]
    
    # Generate summary text
    summary_parts = []
    
    if analysis.experience_analysis:
        summary_parts.append(
            f"Professional with {total_experience} years of experience in {analysis.experience_analysis.career_level} roles."
        )
    
    if analysis.education_analysis:
        summary_parts.append(
            f"Holds a {highest_degree} degree with focus in {research_focus}."
        )
    
    if key_skills:
        top_skill_names = [skill.name for skill in key_skills[:3]]
        summary_parts.append(
            f"Skilled in {', '.join(top_skill_names)} with demonstrated expertise in relevant technologies."
        )
    
    if analysis.research_profile:
        maturity = analysis.research_profile.maturity_level.value
        summary_parts.append(
            f"Shows {maturity} research potential with strong technical competencies."
        )
    
    summary = " ".join(summary_parts) if summary_parts else "Comprehensive professional profile with diverse skills and experience."
    
    return {
        "upload_id": analysis.upload_id,
        "summary": summary,
        "key_skills": [skill.name for skill in key_skills],
        "total_experience": f"{total_experience} years",
        "highest_education": highest_education,
        "score": score,
        "research_focus": research_focus,
        "technical_competencies": technical_competencies,
        "recommendations": analysis.recommendations
    }

@router.get("/status/{upload_id}", response_model=CVStatusResponse)
async def get_processing_status(
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get CV processing status with detailed progress information
    """
    # Implement database lookup
    # status_data = await get_status_from_db(upload_id, current_user.uid)
    
    # Mock response for now
    return CVStatusResponse(
        upload_id=upload_id,
        status=ProcessingStatus.COMPLETED,
        progress=100,
        result_url=f"/api/v1/cv/results/{upload_id}",
        estimated_completion_time=datetime.utcnow()
    )

@router.get("/results/{upload_id}", response_model=CVAnalysisResponse)
async def get_cv_results(
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get processed CV results with comprehensive analysis
    """
    # Implement database lookup
    # analysis = await get_analysis_from_db(upload_id, current_user.uid)
    # summary = await get_summary_from_db(upload_id, current_user.uid)
    # research_potential = await get_research_potential_from_db(upload_id, current_user.uid)
    
    # Mock response for demonstration
    mock_analysis = CVAnalysis(
        upload_id=upload_id,
        user_id=current_user.uid,
        parsed_data=ParsedCV(
            text="Sample CV text...",
            sections={"education": "Education section", "experience": "Experience section"},
            metadata={"pages": 2},
            word_count=500,
            extraction_methods=["pymupdf"],
            extraction_success=True,
            quality_score=85
        ),
        skills=[],
        research_areas=[],
        expertise_levels={},
        research_themes=[],
        nlp_analysis={},
        status=ProcessingStatus.COMPLETED,
        completed_at=datetime.utcnow(),
        suitability_score=85,
        recommendations=["Consider adding more specific technical skills", "Highlight research achievements"]
    )
    
    mock_summary = {
        "upload_id": upload_id,
        "summary": "Experienced professional with strong technical background and research potential.",
        "key_skills": ["Python", "Machine Learning", "Research"],
        "total_experience": "5 years",
        "highest_education": "Master's",
        "score": 85,
        "research_focus": "computer_science",
        "technical_competencies": ["Python", "TensorFlow", "Data Analysis"],
        "recommendations": ["Pursue advanced research opportunities", "Develop publication record"]
    }
    
    return CVAnalysisResponse(
        upload_id=upload_id,
        analysis=mock_analysis,
        summary=mock_summary,
        research_potential=None,
        processing_metadata={
            "processing_time_seconds": 45,
            "extraction_quality": "high",
            "analysis_completeness": "full"
        }
    )

@router.delete("/{upload_id}")
async def delete_cv(
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete uploaded CV and its analysis
    """
    # Implement deletion logic
    # await delete_cv_from_storage(upload_id, current_user.uid)
    # await delete_analysis_from_db(upload_id, current_user.uid)
    
    return {"message": "CV and analysis deleted successfully"}

@router.post("/{upload_id}/research-areas")
async def extract_research_areas_from_cv(
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Extract and create research areas from processed CV
    """
    try:
        # Get CV analysis
        # analysis = await get_analysis_from_db(upload_id, current_user.uid)
        
        # Extract research areas
        # research_areas = await research_service.extract_research_areas_from_cv(
        #     analysis.parsed_data.text, 
        #     current_user.uid
        # )
        
        # Return research areas
        return {
            "upload_id": upload_id,
            "research_areas": [],  # research_areas
            "message": "Research areas extracted successfully"
        }
        
    except Exception as e:
        logger.error(f"Research area extraction failed for {upload_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to extract research areas"
        )