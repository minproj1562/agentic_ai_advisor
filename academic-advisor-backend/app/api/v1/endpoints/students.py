#academic-advisor-backend/app/api/v1/endpoints/students.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.student_performance import StudentPerformance, StudentInfo, Subject
from app.services.recommendation_engine import RecommendationService
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)
recommendation_service = RecommendationService()

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
    current_user: Dict[str, Any] = Depends(lambda: {"uid": "test_user"})  # Replace with actual auth
):
    """Get student performance metrics"""
    try:
        # Verify authorization
        if current_user["uid"] != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        performance = await StudentPerformance.find_one(
            StudentPerformance.student_info.uid == student_id
        ).sort(-StudentPerformance.updated_at)
        
        if not performance:
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

@router.get("/{student_id}/electives/recommendations")
async def get_elective_recommendations(
    student_id: str,
    limit: int = Query(10, ge=1, le=20),
    current_user: Dict[str, Any] = Depends(lambda: {"uid": "test_user"})
):
    """Get personalized elective recommendations"""
    try:
        if current_user["uid"] != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        recommendations = await recommendation_service.get_elective_recommendations(student_id, limit)
        return {
            "student_id": student_id,
            "recommendations": [rec.dict() for rec in recommendations],
            "count": len(recommendations),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating elective recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{student_id}/career-paths")
async def get_career_path_recommendations(
    student_id: str,
    current_user: Dict[str, Any] = Depends(lambda: {"uid": "test_user"})
):
    """Get career path recommendations"""
    try:
        if current_user["uid"] != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        career_paths = await recommendation_service.generate_career_path_recommendations(student_id)
        return {
            "student_id": student_id,
            "career_paths": career_paths,
            "count": len(career_paths),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating career path recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))