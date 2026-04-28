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
        from app.ml.models.recommendation_engine import get_engine

        student_id = _get_student_id(current_user)
        student_data = await recommendation_service.get_student_data(student_id)

        engine = await get_engine()
        result = engine.analyze_elective_choice(
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
        from app.ml.models.recommendation_engine import get_engine
        engine = await get_engine()
        electives = engine.recommend_electives(
            marks=data.marks,
            interests=data.interests,
            projects=[],
            cgpa=sum(data.marks.values()) / max(len(data.marks), 1) / 10,
            use_ml=engine.is_trained,
        )
        open_electives = engine.recommend_open_electives(
            marks=data.marks,
            interests=data.interests,
            projects=[],
            cgpa=sum(data.marks.values()) / max(len(data.marks), 1) / 10,
            use_ml=engine.oe_is_trained,
        )
        return {
            "electives": electives,
            "open_electives": open_electives,
            "model_trained": engine.is_trained,
            "oe_model_trained": engine.oe_is_trained,
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
        from app.ml.models.recommendation_engine import get_engine
        engine = await get_engine()
        is_trained = engine.is_trained
        oe_is_trained = engine.oe_is_trained
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


# ═══════════════════════════════════════════════════════════════
#  ELECTIVE CHOICE TRACKING — for retraining
# ═══════════════════════════════════════════════════════════════

class RecordChoiceRequest(BaseModel):
    """Track which elective the student actually chose."""
    chosen_elective_code: str
    chosen_elective_name: str
    is_open_elective: bool = False
    semester: int = 5
    reason: str = ""


@router.post("/record-choice")
async def record_elective_choice(
    request: RecordChoiceRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """
    Record which elective the student actually selected.
    This data is used to retrain the recommendation model with real choices.
    """
    try:
        from app.services.recommendation_service import recommendation_service
        from app.models.recommendation import TrainingDataPoint

        student_id = _get_student_id(current_user)
        student_data = await recommendation_service.get_student_data(student_id)

        engine = recommendation_service.engine

        # Create training data point from the actual choice
        try:
            features = engine.extract_features(
                marks=student_data['marks'],
                interests=student_data['interests'],
                projects=student_data['projects'],
            )
            td = TrainingDataPoint(
                student_features=features.tolist(),
                marks=student_data['marks'],
                interests={i: 1.0 for i in student_data['interests']},
                project_skills=student_data.get('project_skills', []),
                label=request.chosen_elective_code,
                label_type="open_elective" if request.is_open_elective else "program_elective",
                source="student_choice",
            )
            await td.insert()
        except Exception as e:
            logger.warning(f"Training data creation failed: {e}")

        # Log the choice for admin visibility
        logger.info(f"Student {student_id} chose elective: {request.chosen_elective_code}")

        return {
            "status": "success",
            "message": f"Choice recorded: {request.chosen_elective_name}",
            "data": {
                "student_id": student_id,
                "chosen": request.chosen_elective_code,
                "semester": request.semester,
                "will_improve_model": True,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording choice: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
#  IMPROVEMENT ROADMAP — for lower-scored electives
# ═══════════════════════════════════════════════════════════════

class RoadmapRequest(BaseModel):
    """Request an improvement roadmap for a specific elective."""
    elective_code: str
    is_open_elective: bool = False


@router.post("/roadmap")
async def get_improvement_roadmap(
    request: RoadmapRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """
    Generate a detailed improvement roadmap for a lower-scored elective.
    Shows prerequisite gaps, weak subjects, and a 4-week study plan.
    If the elective has prerequisite subjects that are weak, redirects
    to weakness analysis for those subjects.
    """
    try:
        from app.services.recommendation_service import recommendation_service
        from app.ml.models.recommendation_engine import (
            get_engine, ELECTIVE_META, SUBJECT_WEIGHTS,
            OPEN_ELECTIVE_META, OE_SUBJECT_WEIGHTS,
            _canonicalise_marks,
        )

        student_id = _get_student_id(current_user)
        student_data = await recommendation_service.get_student_data(student_id)
        engine = await get_engine()

        # Get the relevant meta and weights
        # The frontend sends the course code (ITPEC5015), but ELECTIVE_META uses short keys (CCS)
        # Try multiple lookup strategies across both engine instance and module-level constants
        def _find_elective(code, is_oe=False):
            """Find elective by key or by 'code' field, trying multiple sources."""
            if is_oe:
                sources = [
                    (getattr(engine, 'OPEN_ELECTIVE_META', {}), getattr(engine, '_dyn_oe_subject_weights', {})),
                    (OPEN_ELECTIVE_META, OE_SUBJECT_WEIGHTS),
                ]
            else:
                sources = [
                    (getattr(engine, 'ELECTIVE_META', {}), getattr(engine, '_dyn_subject_weights', {})),
                    (ELECTIVE_META, SUBJECT_WEIGHTS),
                ]

            for meta_dict, weights_dict in sources:
                # Direct key match (e.g., code = "CCS")
                if code in meta_dict:
                    return meta_dict[code], weights_dict.get(code, {})
                # Reverse lookup by course code (e.g., code = "ITPEC5015")
                for key, m in meta_dict.items():
                    if isinstance(m, dict) and m.get("code") == code:
                        return m, weights_dict.get(key, {})
            return {}, {}

        meta, weights = _find_elective(request.elective_code, request.is_open_elective)

        if not meta:
            raise HTTPException(status_code=404, detail=f"Elective '{request.elective_code}' not found")

        canon_marks = _canonicalise_marks(student_data['marks'])

        # Analyze prerequisite performance
        prerequisite_analysis = []
        weak_prerequisites = []
        strong_prerequisites = []

        for subj, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            score = canon_marks.get(subj, 0)
            status = "strong" if score >= 60 else "needs_improvement" if score >= 40 else "critical"

            entry = {
                "subject": subj,
                "current_score": score,
                "weight": weight,
                "importance": "Critical" if weight >= 3.0 else "Important" if weight >= 2.0 else "Supporting",
                "status": status,
                "target_score": 70,
                "gap": max(0, round(70 - score, 1)),
            }
            prerequisite_analysis.append(entry)

            if status in ("needs_improvement", "critical"):
                weak_prerequisites.append(entry)
            else:
                strong_prerequisites.append(entry)

        # Generate weekly study plan (4 weeks)
        weeks = []
        if weak_prerequisites:
            # Sort by importance (weight) then gap
            weak_sorted = sorted(weak_prerequisites, key=lambda x: (-x["weight"], -x["gap"]))

            for i in range(4):
                week_subjects = weak_sorted[i::4]  # distribute across weeks
                if week_subjects:
                    weeks.append({
                        "week": i + 1,
                        "focus_subjects": [s["subject"] for s in week_subjects],
                        "goals": [
                            f"Improve {s['subject']} from {s['current_score']}% to {min(s['current_score'] + 10, 100)}%"
                            for s in week_subjects
                        ],
                        "activities": [
                            f"Revise core concepts of {s['subject']}" if s["status"] == "critical"
                            else f"Practice problem-solving in {s['subject']}"
                            for s in week_subjects
                        ],
                    })

        # Overall readiness assessment
        total_weight = sum(weights.values()) if weights else 1
        weighted_score = sum(
            canon_marks.get(subj, 0) * w for subj, w in weights.items()
        ) / total_weight if total_weight else 0

        readiness_pct = round(min(weighted_score, 100), 1)
        if readiness_pct >= 70:
            readiness_level = "Ready"
            readiness_message = "You have a strong foundation for this elective."
        elif readiness_pct >= 50:
            readiness_level = "Moderate"
            readiness_message = "Some prerequisite gaps exist. Follow the roadmap to strengthen weak areas."
        else:
            readiness_level = "Needs Preparation"
            readiness_message = "Significant prerequisite gaps. Consider focusing on fundamentals first."

        return {
            "elective_code": request.elective_code,
            "elective_name": meta.get("name", request.elective_code),
            "readiness": {
                "percentage": readiness_pct,
                "level": readiness_level,
                "message": readiness_message,
            },
            "prerequisite_analysis": prerequisite_analysis,
            "weak_areas": weak_prerequisites,
            "strong_areas": strong_prerequisites,
            "study_plan": {
                "total_weeks": len(weeks),
                "weeks": weeks,
            },
            "skills_to_gain": meta.get("skills", []),
            "career_paths": meta.get("career_paths", []),
            "redirect_to_weakness": len(weak_prerequisites) > 0,
            "weakness_subjects": [w["subject"] for w in weak_prerequisites],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Roadmap generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
#  TRAIN FROM REAL DATA — uses Excel marks
# ═══════════════════════════════════════════════════════════════

@router.post("/train-real")
async def train_from_real_data(
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Train recommendation models using real student marks from Excel data."""
    try:
        if current_user.role not in ['admin', 'faculty']:
            raise HTTPException(status_code=403, detail="Only admins/faculty can trigger training")

        from app.ml.train_real_data import run_training_pipeline
        metadata = run_training_pipeline()

        if metadata is None:
            raise HTTPException(status_code=500, detail="Training failed — Excel file not found")

        return {
            "status": "success",
            "message": "Models trained with real student data",
            "metrics": metadata,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Real data training failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")