# academic-advisor-backend/app/ml/__init__.py
"""
ML Package — Academic Advisor
Provides model health checks and status reporting.
"""

import logging

logger = logging.getLogger(__name__)


def get_model_status() -> dict:
    """Quick health check for all ML models."""
    status = {}

    try:
        from app.ml.models.recommendation_engine import recommendation_engine
        status["elective_recommender"] = {
            "loaded": recommendation_engine.is_trained,
            "type": "RandomForest(200) + KNN(5)",
        }
    except Exception as e:
        status["elective_recommender"] = {"loaded": False, "error": str(e)}

    try:
        from app.ml.models.performance_predictor import performance_predictor
        status["performance_predictor"] = {
            "loaded": performance_predictor.is_trained,
            "type": performance_predictor.model_name,
        }
    except Exception as e:
        status["performance_predictor"] = {"loaded": False, "error": str(e)}

    try:
        from app.ml.models.weakness_detector import weakness_detector
        status["weakness_detector"] = {
            "loaded": weakness_detector.is_trained,
            "type": weakness_detector.model_name,
        }
    except Exception as e:
        status["weakness_detector"] = {"loaded": False, "error": str(e)}

    return status