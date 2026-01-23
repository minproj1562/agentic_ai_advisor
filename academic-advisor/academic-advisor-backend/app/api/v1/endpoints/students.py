# academic-advisor-backend/app/api/v1/endpoints/students.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.student_profile import StudentProfile
from app.core.security import get_current_user, FirebaseUser  # ADD THIS
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

class PerformanceResponse(BaseModel):
    studentInfo: dict
    subjects: List[dict]
    overallCGPA: float
    semesterSGPA: float
    strongSubjects: List[str]
    weakSubjects: List[str]
    completedCredits: int
    totalCredits: int
    interests: List[str]
    careerGoals: List[str]
    skillsMatrix: dict

@router.get("/{student_id}/performance", response_model=PerformanceResponse)
async def get_student_performance(
    student_id: str,
    current_user: FirebaseUser = Depends(get_current_user)  # FIX THIS
):
    """Get student performance metrics"""
    try:
        # Verify authorization
        if current_user.uid != student_id:  # FIX THIS
            raise HTTPException(status_code=403, detail="Not authorized")
        
        profile = await StudentProfile.find_one(
            {"user_id": student_id}
     )
        
        if not profile:
            # Return default structure if no performance data exists
            return PerformanceResponse(
                studentInfo={
                    "uid": student_id,
                    "year": "Unknown",
                    "semester": "Unknown", 
                    "branch": "Unknown",
                    "roll_number": "Unknown"
                },
                subjects=[],
                overallCGPA=0.0,
                semesterSGPA=0.0,
                strongSubjects=[],
                weakSubjects=[],
                completedCredits=0,
                totalCredits=160,
                interests=[],
                careerGoals=[],
                skillsMatrix={}
            )
        
        # Get latest semester
        latest_semester = profile.semester_records[-1] if profile.semester_records else None
        
        # Get all subjects from latest semester
        subjects = []
        if latest_semester:
            subjects = [
                {
                    "subject_code": s.subject_code,
                    "subject_name": s.subject_name,
                    "credits": s.credits,
                    "grade": s.grade,
                    "total_marks": s.total_marks,
                    "is_practical": s.is_practical
                }
                for s in latest_semester.subjects
            ]
        
        # Identify strong and weak subjects
        strong_subjects = []
        weak_subjects = []
        
        if latest_semester:
            for subject in latest_semester.subjects:
                if subject.total_marks >= 75:
                    strong_subjects.append(subject.subject_name)
                elif subject.total_marks < 50:
                    weak_subjects.append(subject.subject_name)
        
        return PerformanceResponse(
            studentInfo={
                "uid": profile.user_id,
                "year": str(profile.admission_year),
                "semester": str(profile.current_semester),
                "branch": profile.branch,
                "roll_number": profile.roll_number
            },
            subjects=subjects,
            overallCGPA=profile.cgpa,
            semesterSGPA=latest_semester.sgpa if latest_semester else 0.0,
            strongSubjects=strong_subjects,
            weakSubjects=weak_subjects,
            completedCredits=profile.total_credits_earned,
            totalCredits=profile.total_credits_required,
            interests=profile.interests or [],
            careerGoals=profile.career_goals or [],
            skillsMatrix={}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ADD MISSING ENDPOINTS

@router.get("/{student_id}/resources")
async def get_student_resources(
    student_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get resources for student"""
    try:
        if current_user.uid != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # TODO: Implement actual resource fetching
        # For now, return empty list
        return {
            "student_id": student_id,
            "resources": [],
            "count": 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/resources/bookmarked")
async def get_bookmarked_resources(
    student_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get bookmarked resources for student"""
    try:
        if current_user.uid != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # TODO: Implement actual bookmarked resource fetching
        # For now, return empty list
        return {
            "student_id": student_id,
            "bookmarked_resources": [],
            "count": 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bookmarked resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))
