# academic-advisor-backend/app/api/v1/endpoints/academic.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.core.security import get_current_user, FirebaseUser
from app.services.academic_service import AcademicService

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Request/Response Models ====================

class SubjectInput(BaseModel):
    subject_code: str = Field(..., min_length=1)
    subject_name: str = Field(..., min_length=1)
    credits: int = Field(default=3, ge=1, le=6)
    internal_marks: float = Field(default=0, ge=0, le=20)
    external_marks: float = Field(default=0, ge=0, le=80)
    is_elective: bool = False
    is_practical: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "subject_code": "CSIT301",
                "subject_name": "Data Structures",
                "credits": 3,
                "internal_marks": 18,
                "external_marks": 65,
                "is_elective": False,
                "is_practical": False
            }
        }


class AddScoresRequest(BaseModel):
    semester_number: int = Field(..., ge=1, le=8)
    academic_year: str = Field(..., min_length=4)
    subjects: List[SubjectInput] = Field(..., min_items=1)

    class Config:
        json_schema_extra = {
            "example": {
                "semester_number": 5,
                "academic_year": "2024-25",
                "subjects": [
                    {
                        "subject_code": "CSIT301",
                        "subject_name": "Data Structures",
                        "credits": 3,
                        "internal_marks": 18,
                        "external_marks": 65
                    }
                ]
            }
        }


class ProfileCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    roll_number: str = Field(..., min_length=1)
    branch: str = Field(default="IT")
    admission_year: int = Field(..., ge=2010, le=2030)
    email: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "roll_number": "CSIT/2022/045",
                "branch": "IT",
                "admission_year": 2022,
                "email": "john@example.com"
            }
        }


# ==================== Endpoints ====================

@router.get("/profile")
async def get_profile(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get student profile"""
    try:
        service = AcademicService()
        profile = await service.get_student_profile(current_user)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please create your profile first."
            )
        
        return {
            "profile": {
                "user_id": profile.user_id,
                "name": profile.name,
                "roll_number": profile.roll_number,
                "branch": profile.branch,
                "admission_year": profile.admission_year,
                "current_semester": profile.current_semester,
                "current_academic_year": profile.current_academic_year,
                "cgpa": profile.cgpa,
                "total_credits_earned": profile.total_credits_earned,
                "total_credits_required": profile.total_credits_required,
                "email": profile.email
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/profile/create")
async def create_profile(
    profile_data: ProfileCreateRequest,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Create or update student profile"""
    try:
        service = AcademicService()
        profile = await service.create_or_update_profile(
            current_user, 
            profile_data.model_dump()
        )
        
        return {
            "message": "Profile saved successfully",
            "current_semester": profile.current_semester,
            "current_academic_year": profile.current_academic_year,
            "profile": {
                "user_id": profile.user_id,
                "name": profile.name,
                "roll_number": profile.roll_number,
                "branch": profile.branch,
                "admission_year": profile.admission_year,
                "current_semester": profile.current_semester,
                "current_academic_year": profile.current_academic_year
            }
        }
    except Exception as e:
        logger.error(f"Error creating profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/scores/add")
async def add_scores(
    request: AddScoresRequest,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Add semester scores"""
    try:
        service = AcademicService()
        
        # Convert Pydantic models to dicts
        subjects_data = [s.model_dump() for s in request.subjects]
        
        result = await service.add_semester_scores(
            current_user,
            request.semester_number,
            request.academic_year,
            subjects_data
        )
        
        return {
            "message": f"Semester {request.semester_number} scores added successfully",
            **result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding scores: {e}", exc_info=True)
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
    try:
        service = AcademicService()
        scores = await service.get_semester_scores(current_user, semester_number)
        
        return {
            "semester_number": semester_number,
            "count": len(scores),
            "scores": [
                {
                    "subject_code": s.subject_code,
                    "subject_name": s.subject_name,
                    "credits": s.credits,
                    "internal_marks": s.internal_marks,
                    "external_marks": s.external_marks,
                    "total_marks": s.total_marks,
                    "grade": s.grade,
                    "grade_points": s.grade_points,
                    "is_elective": s.is_elective,
                    "is_practical": s.is_practical
                }
                for s in scores
            ]
        }
    except Exception as e:
        logger.error(f"Error getting scores: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/semesters")
async def get_semesters(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get all semester records"""
    try:
        service = AcademicService()
        semesters = await service.get_semester_records(current_user)
        
        return {
            "count": len(semesters),
            "semesters": [
                {
                    "semester_number": s.semester_number,
                    "academic_year": s.academic_year,
                    "sgpa": s.sgpa,
                    "total_credits": s.total_credits,
                    "credits_earned": s.credits_earned,
                    "is_complete": s.is_complete,
                    "subjects_count": len(s.subjects)
                }
                for s in semesters
            ]
        }
    except Exception as e:
        logger.error(f"Error getting semesters: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/cgpa")
async def get_cgpa(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get current CGPA"""
    try:
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
            "total_credits_required": profile.total_credits_required,
            "completion_percentage": round(
                (profile.total_credits_earned / profile.total_credits_required) * 100, 1
            ) if profile.total_credits_required > 0 else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CGPA: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/summary")
async def get_academic_summary(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get complete academic summary"""
    try:
        service = AcademicService()
        profile = await service.get_student_profile(current_user)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        completed_semesters = [s for s in profile.semester_records if s.is_complete]
        
        return {
            "user_id": profile.user_id,
            "name": profile.name,
            "roll_number": profile.roll_number,
            "branch": profile.branch,
            "admission_year": profile.admission_year,
            "current_semester": profile.current_semester,
            "current_academic_year": profile.current_academic_year,
            "cgpa": profile.cgpa,
            "total_credits_earned": profile.total_credits_earned,
            "total_credits_required": profile.total_credits_required,
            "completion_percentage": round(
                (profile.total_credits_earned / profile.total_credits_required) * 100, 1
            ) if profile.total_credits_required > 0 else 0,
            "completed_semesters": len(completed_semesters),
            "semester_sgpas": [
                {"semester": s.semester_number, "sgpa": s.sgpa, "credits": s.credits_earned}
                for s in completed_semesters
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/scores/semester/{semester_number}")
async def delete_semester(
    semester_number: int,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Delete a semester's scores"""
    try:
        from app.models.student_profile import StudentProfile
        
        profile = await StudentProfile.find_one(
            StudentProfile.user_id == current_user.uid
        )
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        original_len = len(profile.semester_records)
        profile.semester_records = [
            s for s in profile.semester_records 
            if s.semester_number != semester_number
        ]
        
        if len(profile.semester_records) == original_len:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Semester {semester_number} not found"
            )
        
        # Recalculate CGPA
        if profile.semester_records:
            total_points = sum(s.sgpa * s.total_credits for s in profile.semester_records if s.is_complete)
            total_credits = sum(s.total_credits for s in profile.semester_records if s.is_complete)
            profile.cgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
            profile.total_credits_earned = sum(s.credits_earned for s in profile.semester_records)
        else:
            profile.cgpa = 0.0
            profile.total_credits_earned = 0
        
        profile.last_updated = datetime.now()
        await profile.save()
        
        return {
            "message": f"Semester {semester_number} deleted successfully",
            "updated_cgpa": profile.cgpa,
            "remaining_semesters": len(profile.semester_records)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting semester: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
@router.get("/subjects/available/{semester}")
async def get_available_subjects_for_semester(
    semester: int,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get available subjects for a specific semester based on student's curriculum"""
    try:
        service = AcademicService()
        subjects_data = await service.get_available_subjects(current_user, semester)
        
        return {
            "success": True,
            **subjects_data
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting available subjects: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )