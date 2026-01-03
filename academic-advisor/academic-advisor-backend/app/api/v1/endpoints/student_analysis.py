#academic-advisor-backend/app/api/v1/endpoints/student_analysis.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.models.student_profile import StudentProfile, SemesterRecord, SubjectScore
from app.services.academic_service import AcademicService

router = APIRouter()

@router.get("/{student_id}")
async def get_student_analysis(
    student_id: str, 
    include_predictions: bool = True, 
    include_recommendations: bool = True, 
    time_range: str = "all",
    current_user: Dict[str, Any] = Depends(lambda: {"uid": "test_user"})
):
    """Get comprehensive student analysis"""
    try:
        # Verify the student exists and user has access
        if student_id != current_user["uid"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        profile = await StudentProfile.find_one(StudentProfile.user_id == student_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Student profile not found")
        
        # Get semester records
        semesters = await SemesterRecord.find(
            SemesterRecord.student_id == student_id
        ).sort(SemesterRecord.semester_number).to_list()
        
        # Get all subjects
        all_subjects = []
        weaknesses = []
        
        for semester in semesters:
            subjects = await SubjectScore.find(
                SubjectScore.semester_id == semester.id
            ).to_list()
            
            all_subjects.extend(subjects)
            
            # Identify weaknesses from failed or low-scoring subjects
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
            if semesters[-1].sgpa > semesters[-2].sgpa:
                improvement_trend = "improving"
            elif semesters[-1].sgpa < semesters[-2].sgpa:
                improvement_trend = "declining"
        
        # Prepare performance data
        sgpa_trend = [
            {
                "semester": sem.semester_number,
                "sgpa": sem.sgpa,
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
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")