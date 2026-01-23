# academic-advisor-backend/app/api/v1/endpoints/student_analysis.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.models.student_profile import StudentProfile
from app.core.security import get_current_user, FirebaseUser
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{student_id}")
async def get_student_analysis(
    student_id: str, 
    include_predictions: bool = True, 
    include_recommendations: bool = True, 
    time_range: str = "all",
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get comprehensive student analysis"""
    try:
        # Verify the student exists and user has access
        if student_id != current_user.uid:
            raise HTTPException(status_code=403, detail="Access denied")
        
        profile = await StudentProfile.find_one(StudentProfile.user_id == student_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        # Get semester records from profile
        semesters = profile.semester_records or []
        
        # Get all subjects and identify weaknesses
        all_subjects = []
        weaknesses = []
        
        for semester in semesters:
            subjects = semester.subjects or []
            all_subjects.extend(subjects)
            
            for subject in subjects:
                if subject.grade == 'F' or subject.total_marks < 40:
                    weaknesses.append({
                        "subject": subject.subject_name,
                        "topic": "Fundamental Concepts",
                        "severity": "high" if subject.grade == 'F' else "medium",
                        "gap": 100 - subject.total_marks if subject.grade != 'F' else 60
                    })
        
        # Calculate improvement trend
        improvement_trend = "stable"
        if len(semesters) >= 2:
            last_sgpa = semesters[-1].sgpa if semesters[-1].sgpa else 0
            prev_sgpa = semesters[-2].sgpa if semesters[-2].sgpa else 0
            if last_sgpa > prev_sgpa:
                improvement_trend = "improving"
            elif last_sgpa < prev_sgpa:
                improvement_trend = "declining"
        
        # Prepare performance data
        sgpa_trend = [
            {
                "semester": sem.semester_number,
                "sgpa": sem.sgpa or 0,
                "credits": sem.credits_earned or 0
            }
            for sem in semesters if sem.sgpa is not None
        ]
        
        return {
            "student_id": student_id,
            "current_semester": profile.current_semester,
            "department": profile.branch,
            "latest_sgpa": sgpa_trend[-1]["sgpa"] if sgpa_trend else 0,
            "cgpa": profile.cgpa,
            "improvement_trend": improvement_trend,
            "weaknesses": weaknesses,
            "performance_data": {
                "sgpa_trend": sgpa_trend
            },
            "metadata": {
                "total_credits": profile.total_credits_earned
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in student analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")