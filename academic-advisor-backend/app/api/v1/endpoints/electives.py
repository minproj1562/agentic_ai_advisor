# app/api/v1/endpoints/electives.py
from app.ml.elective_recommender import ElectiveRecommender
from app.models.elective import Elective

router = APIRouter()
recommender = ElectiveRecommender()

@router.get("/{student_id}/electives/recommendations")
async def get_elective_recommendations(
    student_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user)
):
    """Get AI-powered elective recommendations"""
    try:
        # Verify authorization
        if current_user.uid != student_id and current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Get student data
        performance = await StudentPerformance.find_one(
            StudentPerformance.student_info.uid == student_id
        ).sort(-StudentPerformance.updated_at)
        
        if not performance:
            raise HTTPException(status_code=404, detail="Student data not found")
        
        # Get available electives for student's semester and branch
        next_semester = f"Semester {int(performance.student_info.semester.split()[-1]) + 1}"
        
        electives = await Elective.find(
            Elective.semester == next_semester,
            Elective.is_active == True
        ).to_list()
        
        # Prepare student data
        student_data = {
            'skills_matrix': performance.skills_matrix,
            'interests': performance.interests,
            'career_goals': performance.career_goals,
            'subjects': [s.dict() for s in performance.subjects],
            'overall_cgpa': performance.overall_cgpa
        }
        
        # Get elective data
        electives_data = [e.dict() for e in electives]
        
        # Generate recommendations
        recommendations = recommender.recommend_electives(
            student_data,
            electives_data,
            top_k=limit
        )
        
        return recommendations
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
