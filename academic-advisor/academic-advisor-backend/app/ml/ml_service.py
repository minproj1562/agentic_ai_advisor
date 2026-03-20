# academic-advisor/academic-advisor-backend/app/ml/ml_service.py
"""
ML Prediction Service — Updated to use trained models
=======================================================
Uses trained PerformancePredictor and WeaknessDetector when available,
falls back to heuristics otherwise.
"""

import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Import trained model singletons
try:
    from app.ml.models.performance_predictor import performance_predictor
    from app.ml.models.weakness_detector import weakness_detector
    _MODELS_AVAILABLE = True
    logger.info("✅ Trained ML models imported successfully")
except ImportError as e:
    _MODELS_AVAILABLE = False
    performance_predictor = None
    weakness_detector = None
    logger.warning(f"⚠️ Trained models not available: {e}")


class MLPredictionService:
    def __init__(self):
        self.logger = logger
        self.models_available = _MODELS_AVAILABLE

    async def predict_average_performance(self, features: List[Dict[str, Any]]) -> float:
        """Predict next month's average performance."""
        try:
            if not features:
                return 7.0

            if self.models_available and performance_predictor and performance_predictor.is_trained:
                predictions = []
                for feat in features:
                    # Map to predictor feature format
                    pred_input = {
                        "current_cgpa": feat.get("current_cgpa", feat.get("cgpa", 6.0)),
                        "current_sgpa": feat.get("current_sgpi", feat.get("current_sgpa", 6.0)),
                        "previous_sgpa": feat.get("previous_sgpi", feat.get("previous_sgpa", 6.0)),
                        "sgpa_trend": feat.get("current_sgpi", 6) - feat.get("previous_sgpi", 6),
                        "attendance": feat.get("attendance", 75),
                        "assignment_completion": feat.get("assignment_completion", 65),
                        "quiz_average": feat.get("quiz_average", 55),
                        "lab_performance": feat.get("lab_performance", 60),
                        "project_score": feat.get("project_score", 55),
                        "study_hours": feat.get("study_hours", 4),
                        "semester": feat.get("semester", 4),
                    }
                    result = performance_predictor.predict(pred_input)
                    predictions.append(result["predicted_sgpa"])
                return float(np.mean(predictions))
            else:
                # Original heuristic fallback
                df = pd.DataFrame(features)
                current_key = "current_sgpi" if "current_sgpi" in df.columns else "current_sgpa"
                prev_key = "previous_sgpi" if "previous_sgpi" in df.columns else "previous_sgpa"
                current_avg = df[current_key].mean() if current_key in df.columns else 7.0
                previous_avg = df[prev_key].mean() if prev_key in df.columns else current_avg
                trend = current_avg - previous_avg
                return max(0, min(10, current_avg + trend * 0.1))

        except Exception as e:
            self.logger.error(f"Error predicting performance: {e}")
            return 7.0

    async def predict_at_risk_students(self, features: List[Dict[str, Any]]) -> List[float]:
        """Predict at-risk probability for each student."""
        try:
            if not features:
                return []

            if self.models_available and performance_predictor and performance_predictor.is_trained:
                risk_scores = []
                for feat in features:
                    pred_input = {
                        "current_cgpa": feat.get("current_cgpa", feat.get("cgpa", 6.0)),
                        "current_sgpa": feat.get("current_sgpi", feat.get("current_sgpa", 6.0)),
                        "previous_sgpa": feat.get("previous_sgpi", feat.get("previous_sgpa", 6.0)),
                        "sgpa_trend": feat.get("current_sgpi", 6) - feat.get("previous_sgpi", 6),
                        "attendance": feat.get("attendance", 75),
                        "assignment_completion": feat.get("assignment_completion", 65),
                        "semester": feat.get("semester", 4),
                    }
                    result = performance_predictor.predict(pred_input)
                    predicted = result["predicted_sgpa"]
                    
                    # Convert SGPA prediction to risk score (0-1)
                    if predicted < 4.5:
                        risk = 0.9
                    elif predicted < 5.5:
                        risk = 0.7
                    elif predicted < 6.5:
                        risk = 0.4
                    elif predicted < 7.5:
                        risk = 0.2
                    else:
                        risk = 0.05
                    
                    # Attendance modifier
                    att = feat.get("attendance", 75)
                    if att < 60:
                        risk = min(1.0, risk + 0.2)
                    elif att < 75:
                        risk = min(1.0, risk + 0.1)
                    
                    risk_scores.append(risk)
                return risk_scores
            else:
                # Original heuristic
                risk_scores = []
                for feat in features:
                    risk = 0.0
                    sgpi_key = "current_sgpi" if "current_sgpi" in feat else "current_sgpa"
                    if feat.get(sgpi_key, 10) < 6.0:
                        risk += 0.4
                    prev_key = "previous_sgpi" if "previous_sgpi" in feat else "previous_sgpa"
                    if feat.get(sgpi_key, 0) < feat.get(prev_key, 0):
                        risk += 0.3
                    if feat.get("attendance", 100) < 75:
                        risk += 0.2
                    if feat.get("assignment_completion", 100) < 70:
                        risk += 0.1
                    risk_scores.append(min(1.0, risk))
                return risk_scores

        except Exception as e:
            self.logger.error(f"Error predicting at-risk students: {e}")
            return [0.0] * len(features)

    async def calculate_success_probability(
        self,
        features: List[Dict[str, Any]],
        target_sgpi: float = 7.5,
    ) -> float:
        """Calculate probability of meeting target SGPI."""
        try:
            if not features:
                return 0.5

            if self.models_available and performance_predictor and performance_predictor.is_trained:
                predictions = []
                for feat in features:
                    pred_input = {
                        "current_sgpa": feat.get("current_sgpi", feat.get("current_sgpa", 6.0)),
                        "previous_sgpa": feat.get("previous_sgpi", feat.get("previous_sgpa", 6.0)),
                        "attendance": feat.get("attendance", 75),
                        "assignment_completion": feat.get("assignment_completion", 65),
                    }
                    result = performance_predictor.predict(pred_input)
                    predictions.append(result["predicted_sgpa"])

                above_target = sum(1 for p in predictions if p >= target_sgpi)
                return min(1.0, above_target / len(predictions) + 0.1)
            else:
                sgpi_key = "current_sgpi" if features and "current_sgpi" in features[0] else "current_sgpa"
                above = sum(1 for f in features if f.get(sgpi_key, 0) >= target_sgpi)
                return above / len(features) if features else 0.5

        except Exception as e:
            self.logger.error(f"Error calculating success probability: {e}")
            return 0.5

    async def generate_recommendations(
        self,
        faculty_id: str,
        features: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate AI-powered recommendations."""
        recommendations = []
        
        if not features:
            return ["No student data available for analysis."]
        
        sgpi_key = "current_sgpi" if "current_sgpi" in features[0] else "current_sgpa"
        avg_sgpi = np.mean([f.get(sgpi_key, 0) for f in features])
        at_risk_count = sum(1 for f in features if f.get(sgpi_key, 0) < 6.0)

        if self.models_available and weakness_detector and weakness_detector.is_trained:
            # Use trained model for smarter recommendations
            all_weaknesses = []
            for feat in features[:10]:  # Sample for efficiency
                subj_features = {
                    "subject_score": feat.get("avg_score", 55),
                    "attendance": feat.get("attendance", 75),
                    "assignment_score": feat.get("assignment_completion", 65),
                    "cgpa": feat.get("current_cgpa", feat.get("cgpa", 6)),
                }
                result = weakness_detector.detect(subj_features)
                if result["severity"] in ("critical", "high"):
                    all_weaknesses.append(result)

            if len(all_weaknesses) > 3:
                recommendations.append(
                    f"⚠️ {len(all_weaknesses)} critical/high weaknesses detected across mentees. "
                    "Schedule group remediation sessions."
                )

        if avg_sgpi < 7.0:
            recommendations.append(
                "Focus on foundational concepts and regular practice sessions for struggling students."
            )
        if at_risk_count > len(features) * 0.3:
            recommendations.append(
                "More than 30% students are at-risk. Consider additional support programs."
            )
        low_att = sum(1 for f in features if f.get("attendance", 100) < 75)
        if low_att > 0:
            recommendations.append(
                f"{low_att} students have low attendance. Address through personalized counseling."
            )
        recommendations.extend([
            "Schedule regular progress review meetings with each mentee.",
            "Encourage participation in academic support programs.",
        ])
        return recommendations[:5]