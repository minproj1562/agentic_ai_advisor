# academic-advisor-backend/app/ml/models/weakness_detector.py
"""
Weakness Detection ML Model
============================
Uses the trained severity + intervention classifiers from
train_performance_weakness_models.py.

Falls back to rule-based detection if no trained model is available.

FEATURE COLUMNS (must match train_performance_weakness_models.py):
  subject_score, attendance, lab_performance, previous_related_score,
  cgpa, credits, is_practical, class_avg_score, trend_indicator, semester
"""

import os
import json
import logging
import numpy as np
import joblib
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved")

# Must match WEAKNESS_FEATURES in train_performance_weakness_models.py exactly
FEATURE_COLUMNS = [
    "subject_score", "attendance",
    "lab_performance", "previous_related_score",
    "cgpa", "credits", "is_practical",
    "class_avg_score", "trend_indicator", "semester",
]

SEVERITY_MAP = {0: "none", 1: "low", 2: "medium", 3: "high", 4: "critical"}

_DEFAULTS = {
    "subject_score": 55.0,
    "attendance": 75.0,
    "lab_performance": 60.0,
    "previous_related_score": 55.0,
    "cgpa": 6.0,
    "credits": 3,
    "is_practical": 0,
    "class_avg_score": 55.0,
    "trend_indicator": 0,
    "semester": 4,
}


class WeaknessDetector:
    """
    ML-backed weakness detector.

    Primary path: uses trained XGBoost/LightGBM severity classifier
                  + LightGBM intervention classifier.
    Fallback path: rule-based heuristics if no model is available.
    """

    def __init__(self):
        self.severity_model    = None
        self.intervention_model= None
        self.scaler            = None
        self.severity_map      = SEVERITY_MAP
        self.is_trained        = False
        self._load()

    # ── Model loading ────────────────────────────────────────────

    def _load(self):
        sev_path = os.path.join(MODEL_DIR, "weakness_severity_model.joblib")
        int_path = os.path.join(MODEL_DIR, "weakness_intervention_model.joblib")
        scl_path = os.path.join(MODEL_DIR, "weakness_scaler.joblib")
        map_path = os.path.join(MODEL_DIR, "weakness_severity_map.json")
        try:
            if os.path.exists(sev_path) and os.path.exists(scl_path):
                self.severity_model     = joblib.load(sev_path)
                self.intervention_model = joblib.load(int_path) if os.path.exists(int_path) else None
                self.scaler             = joblib.load(scl_path)
                self.is_trained         = True
                if os.path.exists(map_path):
                    with open(map_path) as f:
                        raw = json.load(f)
                    # JSON keys are strings; convert to int
                    self.severity_map = {int(k): v for k, v in raw.items()}
                logger.info("✅ WeaknessDetector loaded (trained model)")
            else:
                logger.warning("⚠️  Weakness model not found — using rule-based fallback")
        except Exception as e:
            logger.error(f"Failed to load weakness model: {e}")

    # ── Feature extraction ────────────────────────────────────────

    def extract_features(self, data: Dict[str, Any]) -> np.ndarray:
        """
        Build feature vector from a subject-level data dict.

        Accepted keys (all optional — missing keys use defaults):
          subject_score, attendance, lab_performance,
          previous_related_score, cgpa, credits, is_practical,
          class_avg_score, trend_indicator, semester
        """
        return np.array(
            [float(data.get(col, _DEFAULTS.get(col, 0))) for col in FEATURE_COLUMNS],
            dtype=np.float32,
        )

    # ── Primary detection method (called by ml_service.py) ───────

    def detect(self, subject_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect weakness for a single subject.

        Args:
            subject_data: dict with keys matching FEATURE_COLUMNS.

        Returns:
            {
              severity: str ("none"/"low"/"medium"/"high"/"critical"),
              severity_level: int (0-4),
              needs_intervention: bool,
              confidence: float,
              score: float (subject_score used),
              rule_based: bool (True if fallback was used),
            }
        """
        score = float(subject_data.get("subject_score", 55.0))

        if self.is_trained and self.severity_model is not None:
            try:
                feat = self.extract_features(subject_data)
                feat_scaled = self.scaler.transform([feat])

                sev_pred = int(self.severity_model.predict(feat_scaled)[0])
                sev_str  = self.severity_map.get(sev_pred, "none")

                # Intervention prediction
                needs_int = False
                if self.intervention_model is not None:
                    needs_int = bool(self.intervention_model.predict(feat_scaled)[0])
                else:
                    needs_int = sev_pred >= 3

                # Confidence from probability if available
                confidence = 0.8
                if hasattr(self.severity_model, "predict_proba"):
                    probs = self.severity_model.predict_proba(feat_scaled)[0]
                    confidence = float(probs[sev_pred])

                return {
                    "severity":        sev_str,
                    "severity_level":  sev_pred,
                    "needs_intervention": needs_int,
                    "confidence":      round(confidence, 3),
                    "score":           score,
                    "rule_based":      False,
                }
            except Exception as e:
                logger.warning(f"ML detect failed, using heuristic: {e}")

        # ── Rule-based fallback ──
        return self._rule_based_detect(subject_data)

    def _rule_based_detect(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simple rule-based weakness detection (fallback)."""
        score      = float(data.get("subject_score", 55.0))
        attendance = float(data.get("attendance", 75.0))
        trend      = int(data.get("trend_indicator", 0))

        if score < 25 or (score < 35 and attendance < 50):
            sev, sev_int = "critical", 4
        elif score < 35:
            sev, sev_int = "high", 3
        elif score < 45 or (score < 55 and attendance < 60):
            sev, sev_int = "medium", 2
        elif score < 55:
            sev, sev_int = "low", 1
        else:
            sev, sev_int = "none", 0

        # Attendance modifier
        if attendance < 60 and sev_int < 3:
            sev_int = min(sev_int + 1, 4)
            sev     = self.severity_map.get(sev_int, "high")

        needs_int = sev_int >= 3 or (sev_int == 2 and trend == -1)

        return {
            "severity":           sev,
            "severity_level":     sev_int,
            "needs_intervention": needs_int,
            "confidence":         0.6,
            "score":              score,
            "rule_based":         True,
        }

    # ── Batch detection ──────────────────────────────────────────

    def detect_batch(
        self, subjects_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect weaknesses for multiple subjects at once (efficient)."""
        if not subjects_data:
            return []

        if self.is_trained and self.severity_model is not None:
            try:
                features = np.array(
                    [self.extract_features(d) for d in subjects_data],
                    dtype=np.float32,
                )
                scaled = self.scaler.transform(features)

                sev_preds = self.severity_model.predict(scaled)
                int_preds = (
                    self.intervention_model.predict(scaled)
                    if self.intervention_model is not None
                    else sev_preds >= 3
                )

                confidences = (
                    np.max(self.severity_model.predict_proba(scaled), axis=1)
                    if hasattr(self.severity_model, "predict_proba")
                    else np.full(len(subjects_data), 0.8)
                )

                return [
                    {
                        "severity":           self.severity_map.get(int(s), "none"),
                        "severity_level":     int(s),
                        "needs_intervention": bool(ni),
                        "confidence":         round(float(c), 3),
                        "score":              float(d.get("subject_score", 0)),
                        "rule_based":         False,
                    }
                    for d, s, ni, c in zip(subjects_data, sev_preds, int_preds, confidences)
                ]
            except Exception as e:
                logger.warning(f"Batch ML detect failed: {e}")

        return [self._rule_based_detect(d) for d in subjects_data]

    # ── Legacy interface (kept for backward compatibility) ────────

    def detect_weaknesses(
        self, student_performance: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Legacy method: accepts a dict of {subject_name: subject_data}.
        Returns list of weakness dicts for subjects with severity != none.

        Kept for backward compatibility with old callers.
        """
        weaknesses = []
        for subject_name, subject_data in student_performance.items():
            if not isinstance(subject_data, dict):
                continue

            # Map legacy keys to FEATURE_COLUMNS keys
            mapped = {
                "subject_score":          float(subject_data.get("score", 55)),
                "attendance":             float(subject_data.get("attendance", 75)),
                "lab_performance":        float(subject_data.get("lab_performance", 60)),
                "previous_related_score": float(subject_data.get("previous_score", 55)),
                "cgpa":                   float(subject_data.get("cgpa", 6.0)),
                "credits":                int(subject_data.get("credits", 3)),
                "is_practical":           int(subject_data.get("is_practical", 0)),
                "class_avg_score":        float(subject_data.get("class_avg", 55)),
                "trend_indicator":        int(subject_data.get("trend", 0)),
                "semester":               int(subject_data.get("semester", 4)),
            }

            result = self.detect(mapped)
            if result["severity"] != "none":
                result["subject"] = subject_name
                # Legacy fields
                result["gap"]         = max(0, 40 - result["score"])
                result["suggestions"] = self._suggestions(
                    result["severity"], subject_name
                )
                weaknesses.append(result)

        weaknesses.sort(key=lambda x: x["severity_level"], reverse=True)
        return weaknesses

    @staticmethod
    def _suggestions(severity: str, subject: str) -> List[str]:
        base = {
            "critical": [
                f"Urgent: Schedule consultation for {subject}",
                "Join intensive tutoring",
                "Dedicate ≥3 hours/day to this subject",
            ],
            "high": [
                f"Priority: Focus on {subject}",
                "Form or join a study group",
                "Complete all practice problems",
            ],
            "medium": [
                "Review fundamental concepts",
                "Solve previous year papers",
                "Attend all classes",
            ],
            "low": [
                "Maintain consistent practice",
                "Aim for higher scores",
            ],
        }
        return base.get(severity, ["Keep up the good work"])

    # ── Intervention recommendations (legacy) ────────────────────

    def get_intervention_recommendations(
        self, weaknesses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        from collections import defaultdict
        severity_counts = defaultdict(int)
        for w in weaknesses:
            severity_counts[w.get("severity", "none")] += 1

        interventions = []
        if severity_counts["critical"] > 0:
            interventions.append({
                "type": "urgent",
                "action": "Immediate faculty intervention required",
                "subjects": [w.get("subject", "") for w in weaknesses if w.get("severity") == "critical"],
                "timeline": "within 24 hours",
            })
        if severity_counts["high"] > 1:
            interventions.append({
                "type": "high_priority",
                "action": "Enrolment in remedial classes recommended",
                "subjects": [w.get("subject", "") for w in weaknesses if w.get("severity") == "high"],
                "timeline": "within 1 week",
            })
        if len(weaknesses) > 3:
            interventions.append({
                "type": "comprehensive",
                "action": "Complete academic performance review needed",
                "timeline": "within 2 weeks",
            })
        return interventions


# Singleton
weakness_detector = WeaknessDetector()