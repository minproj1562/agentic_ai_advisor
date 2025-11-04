# app/api/v1/endpoints/resources.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.models.resource import StudyResource
from app.services.resource_matcher import ResourceMatcher

router = APIRouter()
resource_matcher = ResourceMatcher()

@router.get("/{student_id}/resources/recommendations")
async def get_resource_recommendations(
    student_id: str,
    subject: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user)
):
    """Get personalized study resource recommendations"""
    try:
        # Verify authorization
        if current_user.uid != student_id and current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Get student performance data
        performance = await StudentPerformance.find_one(
            StudentPerformance.student_info.uid == student_id
        ).sort(-StudentPerformance.updated_at)
        
        if not performance:
            raise HTTPException(status_code=404, detail="Student data not found")
        
        # Build query filters
        query_filters = {"is_active": True}
        
        if subject:
            query_filters["tags"] = {"$in": [subject]}
        if topic:
            query_filters["topics_covered"] = {"$in": [topic]}
        if difficulty:
            query_filters["difficulty"] = difficulty
        if resource_type:
            query_filters["type"] = resource_type
        
        # Get resources
        resources = await StudyResource.find(query_filters).to_list(limit * 2)
        
        # Match resources to student
        matched_resources = resource_matcher.match_resources(
            student_data=performance.dict(),
            resources=[r.dict() for r in resources],
            limit=limit
        )
        
        return matched_resources
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{student_id}/resources/{resource_id}/activity")
async def track_resource_activity(
    student_id: str,
    resource_id: str,
    activity_type: str,
    progress: float = 0.0,
    rating: Optional[float] = None,
    feedback: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Track student interaction with resources"""
    try:
        # Verify authorization
        if current_user.uid != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Create or update activity record
        activity = await StudentResourceActivity.find_one(
            StudentResourceActivity.student_id == student_id,
            StudentResourceActivity.resource_id == resource_id
        )
        
        if activity:
            activity.activity_type = activity_type
            activity.progress = max(activity.progress, progress)
            activity.time_spent += 60  # Add 1 minute per interaction
            if rating:
                activity.rating = rating
            if feedback:
                activity.feedback = feedback
            activity.last_accessed = datetime.now()
        else:
            activity = StudentResourceActivity(
                student_id=student_id,
                resource_id=resource_id,
                activity_type=activity_type,
                progress=progress,
                rating=rating,
                feedback=feedback,
                time_spent=60
            )
        
        await activity.save()
        
        return {"status": "success", "activity": activity.dict()}
    
    except Exception as e:
        logger.error(f"Error tracking activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))