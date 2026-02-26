#  academic-advisor/academic-advisor-backend/app/api/v1/students.py
"""
Student API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse

from app.dependencies import get_current_user, get_student_user, FilterParams, PaginationParams
from app.schemas.student_schemas import StudentCreate, StudentUpdate, StudentAnalysisResponse
from app.services.student_service import StudentService
from app.core.firebase_admin import firebase_manager
from app.utils.helpers import get_logger

logger = get_logger(__name__)
router = APIRouter()

student_service = StudentService()


@router.get("/profile")
async def get_student_profile(
    current_user: dict = Depends(get_student_user)
):
    """
    Get current student's profile
    """
    try:
        student = await firebase_manager.get_document(
            collection="students",
            document_id=current_user['student_id']
        )
        
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        return student
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")


@router.put("/profile")
async def update_student_profile(
    update_data: StudentUpdate,
    current_user: dict = Depends(get_student_user)
):
    """
    Update student profile
    """
    try:
        updated = await firebase_manager.update_document(
            collection="students",
            document_id=current_user['student_id'],
            data=update_data.dict(exclude_unset=True)
        )
        
        return {"message": "Profile updated successfully", "updated": updated}
        
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.post("/upload-cv")
async def upload_cv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_student_user)
):
    """
    Upload CV for analysis
    """
    try:
        # Validate file
        if not file.filename.endswith(('.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="Invalid file format")
        
        if file.size > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(status_code=400, detail="File too large")
        
        # Read file
        content = await file.read()
        
        # Upload to Firebase Storage
        file_path = f"cvs/{current_user['student_id']}/{file.filename}"
        url = await firebase_manager.upload_file(
            file_path=file_path,
            file_data=content,
            content_type=file.content_type
        )
        
        # Analyze CV
        analysis = await student_service.analyze_cv(content, file.filename)
        
        # Update student record
        await firebase_manager.update_document(
            collection="students",
            document_id=current_user['student_id'],
            data={
                'cv_url': url,
                'cv_analysis': analysis,
                'cv_uploaded_at': datetime.utcnow().isoformat()
            }
        )
        
        return {
            "message": "CV uploaded successfully",
            "url": url,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading CV: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload CV")


@router.get("/performance")
async def get_student_performance(
    time_range: Optional[str] = Query("all", regex="^(all|current|last_year)$"),
    current_user: dict = Depends(get_student_user)
):
    """
    Get student's performance data
    """
    try:
        performance = await student_service.get_performance(
            student_id=current_user['student_id'],
            time_range=time_range
        )
        
        return performance
        
    except Exception as e:
        logger.error(f"Error fetching performance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch performance")


@router.get("/recommendations")
async def get_recommendations(
    current_user: dict = Depends(get_student_user)
):
    """
    Get personalized recommendations
    """
    try:
        recommendations = await student_service.get_recommendations(
            student_id=current_user['student_id']
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error fetching recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recommendations")


@router.post("/recommendations/{recommendation_id}/accept")
async def accept_recommendation(
    recommendation_id: str,
    current_user: dict = Depends(get_student_user)
):
    """
    Accept a recommendation
    """
    try:
        await firebase_manager.update_document(
            collection=f"students/{current_user['student_id']}/recommendations",
            document_id=recommendation_id,
            data={
                'is_accepted': True,
                'accepted_at': datetime.utcnow().isoformat()
            }
        )
        
        return {"message": "Recommendation accepted"}
        
    except Exception as e:
        logger.error(f"Error accepting recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to accept recommendation")


@router.get("/electives/suggestions")
async def get_elective_suggestions(
    current_user: dict = Depends(get_student_user)
):
    """
    Get elective course suggestions
    """
    try:
        suggestions = await student_service.get_elective_suggestions(
            student_id=current_user['student_id']
        )
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error fetching elective suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch suggestions")


@router.get("/study-plan")
async def get_study_plan(
    current_user: dict = Depends(get_student_user)
):
    """
    Get personalized study plan
    """
    try:
        plan = await student_service.generate_study_plan(
            student_id=current_user['student_id']
        )
        
        return plan
        
    except Exception as e:
        logger.error(f"Error generating study plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate study plan")