#academic-advisor-backend/app/api/v1/endpoints/academic.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from beanie import PydanticObjectId

from app.core.security import get_current_user, FirebaseUser
from app.models.student_profile import StudentProfile, SemesterRecord, SubjectScore
from app.services.academic_service import AcademicService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/profile")
async def get_profile(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get student profile"""
    service = AcademicService()
    profile = await service.get_student_profile(current_user)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return {"profile": profile.dict()}

@router.post("/profile/create")
async def create_profile(
    profile_data: dict,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Create or update student profile"""
    try:
        service = AcademicService()
        profile = await service.create_or_update_profile(current_user, profile_data)
        
        return {
            "message": "Profile saved successfully",
            "profile": profile.dict(),
            "current_semester": profile.current_semester,
            "academic_year": profile.current_academic_year
        }
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/scores/add")
async def add_scores(
    semester_data: dict,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Add semester scores"""
    try:
        service = AcademicService()
        result = await service.add_semester_scores(
            current_user,
            semester_data["semester_number"],
            semester_data["academic_year"],
            semester_data["subjects"]
        )
        
        return {
            "message": "Scores added successfully",
            **result
        }
    except Exception as e:
        logger.error(f"Error adding scores: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/scores")
async def get_scores(
    semester_number: Optional[int] = None,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get subject scores"""
    service = AcademicService()
    scores = await service.get_semester_scores(current_user, semester_number)
    
    return {
        "scores": [score.dict() for score in scores]
    }

@router.get("/semesters")
async def get_semesters(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get all semester records"""
    service = AcademicService()
    semesters = await service.get_semester_records(current_user)
    
    return {
        "semesters": [semester.dict() for semester in semesters]
    }

@router.get("/cgpa")
async def get_cgpa(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get current CGPA"""
    service = AcademicService()
    profile = await service.get_student_profile(current_user)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return {
        "cgpa": profile.cgpa,
        "total_credits_earned": profile.total_credits_earned,
        "total_credits_required": profile.total_credits_required
    }