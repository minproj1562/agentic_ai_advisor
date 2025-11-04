# app/api/v1/endpoints/students.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from app.models.student import StudentPerformance, Subject
from app.core.security import get_current_user
from app.services.recommendation_engine import RecommendationService
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
    current_user = Depends(get_current_user)
):
    """Get student performance metrics"""
    try:
        # Verify authorization
        if current_user.uid != student_id and current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Not authorized")
        
        performance = await StudentPerformance.find_one(
            StudentPerformance.student_info.uid == student_id
        ).sort(-StudentPerformance.updated_at)
        
        if not performance:
            raise HTTPException(status_code=404, detail="Performance data not found")
        
        return PerformanceResponse(
            studentInfo=performance.student_info.dict(),
            subjects=[s.dict() for s in performance.subjects],
            overallCGPA=performance.overall_cgpa,
            semesterSGPA=performance.semester_sgpa,
            strongSubjects=performance.strong_subjects,
            weakSubjects=performance.weak_subjects,
            completedCredits=performance.completed_credits,
            totalCredits=performance.total_credits,
            interests=performance.interests,
            careerGoals=performance.career_goals,
            skillsMatrix=performance.skills_matrix
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))
