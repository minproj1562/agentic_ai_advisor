# academic-advisor/academic-advisor-backend/app/ml/models/performance_predictor.py
"""
Performance Predictor — Trained ML Model
==========================================
Predicts next semester SGPA using the best model selected during training.
Falls back to heuristics if no trained model is available.
"""

import os
import json
import logging
import numpy as np
import joblib
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved")

FEATURE_COLUMNS = [
    "current_cgpa", "current_sgpa", "previous_sgpa", "sgpa_trend",
    "attendance", "assignment_completion", "quiz_average",
    "lab_performance", "project_score", "study_hours",
    "participation_score", "extracurricular", "dept_avg",
    "num_subjects", "num_backlogs", "num_strong_subjects", "num_weak_subjects",
    "avg_subject_score", "min_subject_score", "max_subject_score", "std_subject_score",
    "practical_avg", "theory_avg", "credits_completed_ratio", "semester",
]

# Defaults for imputation when a feature is missing
_DEFAULTS = {
    "current_cgpa": 6.0, "current_sgpa": 6.0, "previous_sgpa": 6.0,
    "sgpa_trend": 0.0, "attendance": 75.0, "assignment_completion": 65.0,
    "quiz_average": 55.0, "lab_performance": 60.0, "project_score": 55.0,
    "study_hours": 4.0, "participation_score": 50.0, "extracurricular": 30.0,
    "dept_avg": 6.2, "num_subjects": 6, "num_backlogs": 0,
    "num_strong_subjects": 2, "num_weak_subjects": 1,
    "avg_subject_score": 55.0, "min_subject_score": 35.0,
    "max_subject_score": 75.0, "std_subject_score": 12.0,
    "practical_avg": 60.0, "theory_avg": 52.0,
    "credits_completed_ratio": 0.3, "semester": 4,
}


class PerformancePredictor:
    """ML model for predicting next semester SGPA."""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.model_name = "unknown"
        self.feature_importance: Dict[str, float] = {}
        self._load()

    def _load(self):
        model_path = os.path.join(MODEL_DIR, "performance_model.joblib")
        scaler_path = os.path.join(MODEL_DIR, "performance_scaler.joblib")
        report_path = os.path.join(MODEL_DIR, "performance_training_report.json")
        try:
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                self.is_trained = True
                if os.path.exists(report_path):
                    with open(report_path) as f:
                        report = json.load(f)
                    self.model_name = report.get("best_model", "unknown")
                    self.feature_importance = report.get("feature_importance", {})
                logger.info(f"✅ PerformancePredictor loaded ({self.model_name})")
            else:
                logger.warning("⚠️ Performance model files not found. Using heuristic fallback.")
        except Exception as e:
            logger.error(f"Failed to load performance model: {e}")

    # ── Feature extraction ──────────────────────────────────────

    def extract_features(self, data: Dict[str, Any]) -> np.ndarray:
        """
        Extract feature vector from a student data dict.
        
        Accepts keys matching FEATURE_COLUMNS directly,
        OR derives them from `student_data` + `performance_history` style dicts.
        """
        features = []
        for col in FEATURE_COLUMNS:
            val = data.get(col, _DEFAULTS.get(col, 0))
            features.append(float(val))
        return np.array(features, dtype=np.float32)

    @staticmethod
    def extract_from_student_record(
        student_data: Dict[str, Any],
        performance_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Bridge method: convert app-layer student_data + performance_history
        into the flat feature dict expected by extract_features().
        """
        cgpa = student_data.get("cgpa", student_data.get("overall_cgpa", 6.0))
        semester = student_data.get("current_semester", student_data.get("semester", 4))
        attendance = student_data.get("attendance", student_data.get("attendance_average", 75))

        sgpas = [p.get("sgpa", p.get("semester_sgpa", 6.0)) for p in performance_history] if performance_history else [cgpa]
        current_sgpa = sgpas[-1] if sgpas else cgpa
        prev_sgpa = sgpas[-2] if len(sgpas) >= 2 else current_sgpa

        # Aggregate subject scores from latest performance record
        scores = []
        practical_scores = []
        theory_scores = []
        if performance_history:
            latest = performance_history[-1]
            for subj in latest.get("subjects", []):
                s = subj.get("total_marks", subj.get("score", 0))
                scores.append(s)
                if subj.get("is_practical", False):
                    practical_scores.append(s)
                else:
                    theory_scores.append(s)

        if not scores:
            scores = [cgpa * 10]  # rough fallback

        return {
            "current_cgpa": cgpa,
            "current_sgpa": current_sgpa,
            "previous_sgpa": prev_sgpa,
            "sgpa_trend": current_sgpa - prev_sgpa,
            "attendance": attendance,
            "assignment_completion": student_data.get("assignment_completion_rate", 65),
            "quiz_average": student_data.get("quiz_average", 55),
            "lab_performance": student_data.get("lab_performance", 60),
            "project_score": student_data.get("project_score", 55),
            "study_hours": student_data.get("study_hours", 4),
            "participation_score": student_data.get("participation_score", 50),
            "extracurricular": student_data.get("extracurricular", 30),
            "dept_avg": student_data.get("dept_avg", 6.2),
            "num_subjects": len(scores),
            "num_backlogs": sum(1 for s in scores if s < 40),
            "num_strong_subjects": sum(1 for s in scores if s >= 70),
            "num_weak_subjects": sum(1 for s in scores if s < 50),
            "avg_subject_score": float(np.mean(scores)),
            "min_subject_score": float(np.min(scores)),
            "max_subject_score": float(np.max(scores)),
            "std_subject_score": float(np.std(scores)) if len(scores) > 1 else 0,
            "practical_avg": float(np.mean(practical_scores)) if practical_scores else 60,
            "theory_avg": float(np.mean(theory_scores)) if theory_scores else 52,
            "credits_completed_ratio": min((semester - 1) * 20 / 160, 1.0),
            "semester": semester,
        }

    # ── Prediction ──────────────────────────────────────────────

    def predict(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict next SGPA for a single student."""
        features = self.extract_features(student_data)

        if self.is_trained and self.model is not None:
            features_scaled = self.scaler.transform([features])
            predicted = float(self.model.predict(features_scaled)[0])
            predicted = round(np.clip(predicted, 0, 10), 2)
            confidence = self._estimate_confidence(student_data)
        else:
            predicted = self._heuristic_predict(student_data)
            confidence = 0.40

        lower, upper = self._prediction_interval(predicted, confidence)

        return {
            "predicted_sgpa": predicted,
            "confidence": round(confidence, 2),
            "lower_bound": lower,
            "upper_bound": upper,
            "risk_category": self._risk_category(predicted),
            "model_used": self.model_name if self.is_trained else "heuristic",
        }

    def batch_predict(self, students: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predict for multiple students."""
        return [self.predict(s) for s in students]

    def get_feature_importance(self) -> Dict[str, float]:
        """Return feature importance from trained model."""
        if self.feature_importance:
            return self.feature_importance
        if self.is_trained and hasattr(self.model, "feature_importances_"):
            return dict(zip(FEATURE_COLUMNS, self.model.feature_importances_.tolist()))
        return {}

    # ── Helpers ─────────────────────────────────────────────────

    def _heuristic_predict(self, data: Dict[str, Any]) -> float:
        cgpa = data.get("current_cgpa", 6.0)
        sgpa = data.get("current_sgpa", cgpa)
        trend = data.get("sgpa_trend", 0)
        predicted = sgpa * 0.6 + cgpa * 0.3 + trend * 0.3
        return round(np.clip(predicted, 0, 10), 2)

    @staticmethod
    def _estimate_confidence(data: Dict[str, Any]) -> float:
        filled = sum(1 for col in FEATURE_COLUMNS if data.get(col) is not None)
        base = 0.5 + (filled / len(FEATURE_COLUMNS)) * 0.4
        return min(base, 0.92)

    @staticmethod
    def _prediction_interval(predicted: float, confidence: float) -> Tuple[float, float]:
        margin = (1 - confidence) * 1.5 + 0.3
        return (round(max(0, predicted - margin), 2), round(min(10, predicted + margin), 2))

    @staticmethod
    def _risk_category(sgpa: float) -> str:
        if sgpa < 4.5:
            return "critical"
        elif sgpa < 5.5:
            return "high"
        elif sgpa < 6.5:
            return "medium"
        elif sgpa < 7.5:
            return "low"
        return "very_low"


# ── Singleton ───────────────────────────────────────────────────
performance_predictor = PerformancePredictor()