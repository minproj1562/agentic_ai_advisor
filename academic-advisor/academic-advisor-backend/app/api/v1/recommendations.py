# app/api/v1/recommendations.py
"""
Recommendations API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime

from app.dependencies import get_current_user, get_student_user
from app.services.recommendation_service import RecommendationService
from app.core.firebase_admin import firebase_manager
from app.utils.helpers import get_logger

logger = get_logger(__name__)
router = APIRouter()

recommendation_service = RecommendationService()


@router.get("/courses")
async def get_course_recommendations(
    include_electives: bool = Query(True),
    include_minors: bool = Query(True),
    current_user: dict = Depends(get_student_user)
):
    """
    Get personalized course recommendations
    """
    try:
        recommendations = await recommendation_service.get_course_recommendations(
            student_id=current_user['student_id'],
            include_electives=include_electives,
            include_minors=include_minors
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error fetching course recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recommendations")


@router.get("/career-paths")
async def get_career_path_recommendations(
    current_user: dict = Depends(get_student_user)
):
    """
    Get career path recommendations based on profile
    """
    try:
        career_paths = await recommendation_service.get_career_paths(
            student_id=current_user['student_id']
        )
        
        return career_paths
        
    except Exception as e:
        logger.error(f"Error fetching career paths: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch career paths")


@router.get("/resources")
async def get_learning_resources(
    subject: Optional[str] = None,
    difficulty: Optional[str] = Query(None, regex="^(beginner|intermediate|advanced)$"),
    current_user: dict = Depends(get_student_user)
):
    """
    Get recommended learning resources
    """
    try:
        resources = await recommendation_service.get_learning_resources(
            student_id=current_user['student_id'],
            subject=subject,
            difficulty=difficulty
        )
        
        return resources
        
    except Exception as e:
        logger.error(f"Error fetching resources: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch resources")


@router.get("/skills")
async def get_skill_recommendations(
    current_user: dict = Depends(get_student_user)
):
    """
    Get skill development recommendations
    """
    try:
        skills = await recommendation_service.get_skill_recommendations(
            student_id=current_user['student_id']
        )
        
        return skills
        
    except Exception as e:
        logger.error(f"Error fetching skill recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recommendations")


@router.get("/mentors")
async def get_mentor_recommendations(
    current_user: dict = Depends(get_student_user)
):
    """
    Get mentor recommendations
    """
    try:
        mentors = await recommendation_service.get_mentor_recommendations(
            student_id=current_user['student_id']
        )
        
        return mentors
        
    except Exception as e:
        logger.error(f"Error fetching mentor recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recommendations")


@router.post("/feedback/{recommendation_id}")
async def provide_recommendation_feedback(
    recommendation_id: str,
    feedback: dict,
    current_user: dict = Depends(get_student_user)
):
    """
    Provide feedback on a recommendation
    """
    try:
        await recommendation_service.record_feedback(
            recommendation_id=recommendation_id,
            student_id=current_user['student_id'],
            feedback=feedback
        )
        
        return {"message": "Feedback recorded successfully"}
        
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")


@router.get("/personalized-plan")
async def get_personalized_plan(
    current_user: dict = Depends(get_student_user)
):
    """
    Get complete personalized academic plan
    """
    try:
        plan = await recommendation_service.generate_personalized_plan(
            student_id=current_user['student_id']
        )
        
        return plan
        
    except Exception as e:
        logger.error(f"Error generating plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate plan")