# app/api/v1/recommendations.py
"""
Recommendations API Router
Supports Program Electives + Open Electives (Sem VII)
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel  # ← FIX: was missing
from datetime import datetime
import logging

from app.core.security import FirebaseUser, get_current_user
from app.schemas.recommendation_schemas import (
    GenerateRecommendationsRequest,
    RecommendationFeedbackRequest,
    ManualMarksInput,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_student_id(current_user: FirebaseUser) -> str:
    if not current_user or not current_user.uid:
        raise HTTPException(status_code=400, detail="Student ID not found in token")
    return current_user.uid


class WhatIfRequest(BaseModel):
    chosen_elective: str
    is_open_elective: bool = False


@router.post("/what-if")
async def what_if_analysis(
    request: WhatIfRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """
    Analyze: 'What if I choose THIS elective?'
    Returns risk level, gaps, preparation plan, and comparison with top choice.
    """
    try:
        from app.services.recommendation_service import recommendation_service
        from app.ml.models.recommendation_engine import recommendation_engine

        student_id = _get_student_id(current_user)
        student_data = await recommendation_service.get_student_data(student_id)

        result = recommendation_engine.analyze_elective_choice(
            chosen_elective=request.chosen_elective,
            marks=student_data['marks'],
            interests=student_data['interests'],
            projects=student_data['projects'],
            cgpa=student_data['cgpa'],
            is_open_elective=request.is_open_elective,
        )
        return result
    except Exception as e:
        logger.error(f"What-if analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_recommendations(
    request: GenerateRecommendationsRequest = Body(
        default=GenerateRecommendationsRequest()
    ),
    current_user: FirebaseUser = Depends(get_current_user),
):
    try:
        from app.services.recommendation_service import recommendation_service
        student_id = _get_student_id(current_user)
        result = await recommendation_service.generate_recommendations(
            student_id=student_id,
            include_electives=request.include_electives,
            include_open_electives=request.include_open_electives,
            include_honours=request.include_honours,
            include_career=request.include_career,
            force_refresh=request.force_refresh,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(
    request: RecommendationFeedbackRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    try:
        from app.services.recommendation_service import recommendation_service
        student_id = _get_student_id(current_user)
        await recommendation_service.record_feedback(
            student_id=student_id,
            recommendation_type=request.type,
            recommendation_id=request.recommendation_id,
            rating=request.rating,
            feedback_text=request.feedback,
        )
        return {"message": "Feedback recorded successfully", "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to record feedback")


@router.post("/refresh")
async def refresh_recommendations(
    current_user: FirebaseUser = Depends(get_current_user),
):
    try:
        from app.services.recommendation_service import recommendation_service
        student_id = _get_student_id(current_user)
        result = await recommendation_service.generate_recommendations(
            student_id=student_id, force_refresh=True,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to refresh")


@router.get("/model-info")
async def get_model_info(
    current_user: FirebaseUser = Depends(get_current_user),
):
    try:
        from app.services.recommendation_service import recommendation_service
        return await recommendation_service.get_model_info()
    except Exception as e:
        logger.error(f"Error getting model info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-manual")
async def test_with_manual_data(
    data: ManualMarksInput,
    current_user: FirebaseUser = Depends(get_current_user),
):
    try:
        from app.ml.models.recommendation_engine import recommendation_engine
        electives = recommendation_engine.recommend_electives(
            marks=data.marks,
            interests=data.interests,
            projects=[],
            cgpa=sum(data.marks.values()) / max(len(data.marks), 1) / 10,
            use_ml=recommendation_engine.is_trained,
        )
        open_electives = recommendation_engine.recommend_open_electives(
            marks=data.marks,
            interests=data.interests,
            projects=[],
            cgpa=sum(data.marks.values()) / max(len(data.marks), 1) / 10,
            use_ml=recommendation_engine.oe_is_trained,
        )
        return {
            "electives": electives,
            "open_electives": open_electives,
            "model_trained": recommendation_engine.is_trained,
            "oe_model_trained": recommendation_engine.oe_is_trained,
            "note": "Test endpoint - data not saved",
        }
    except Exception as e:
        logger.error(f"Error in manual test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training-status")
async def get_training_status(
    current_user: FirebaseUser = Depends(get_current_user),
):
    try:
        from app.ml.models.recommendation_engine import recommendation_engine
        is_trained = recommendation_engine.is_trained
        oe_is_trained = recommendation_engine.oe_is_trained
    except ImportError:
        is_trained = False
        oe_is_trained = False

    return {
        "is_trained": is_trained,
        "oe_is_trained": oe_is_trained,
        "model_version": "3.0.0",
        "models": {
            "program_electives": (
                ["RandomForest", "KNN"] if is_trained else ["Rule-Based"]
            ),
            "open_electives": (
                ["RandomForest"] if oe_is_trained else ["Rule-Based"]
            ),
        },
        "last_checked": datetime.utcnow().isoformat(),
    }


@router.post("/train")
async def train_model(
    current_user: FirebaseUser = Depends(get_current_user),
):
    try:
        if current_user.role not in ['admin', 'faculty']:
            raise HTTPException(
                status_code=403,
                detail="Only admins/faculty can trigger training",
            )
        from app.ml.utils.training import train_recommendation_model
        metrics = await train_recommendation_model()
        return {
            "status": "success",
            "message": "Both models trained",
            "metrics": metrics,
        }
    except HTTPException:
        raise
    except ImportError as e:
        logger.error(f"Training module not found: {e}")
        raise HTTPException(
            status_code=500, detail="Training module not available"
        )
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")