# academic-advisor-backend/app/ml/__init__.py
"""
ML Package — Academic Advisor
Provides model health checks and status reporting.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

def _get_best_model_name() -> str:
    """Read best model name from training metadata."""
    try:
        meta_path = os.path.join(
            os.path.dirname(__file__), "saved_models", "training_metadata.json"
        )
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            best = meta.get("best_model", "Ensemble")
            acc = meta.get("best_accuracy", 0)
            return f"{best} ({acc*100:.1f}% acc)"
    except Exception:
        pass
    return "Ensemble ML"


def get_model_status() -> dict:
    """Quick health check for all ML models."""
    status = {}

    try:
        from app.ml.models.recommendation_engine import recommendation_engine
        status["elective_recommender"] = {
            "loaded": recommendation_engine.is_trained,
            "type": _get_best_model_name(),
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