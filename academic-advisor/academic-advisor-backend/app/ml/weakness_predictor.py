# academic-advisor/academic-advisor-backend/app/ml/weakness_predictor.py
"""
Weakness Detector — Trained ML Model
======================================
Classifies academic weakness severity per subject using trained LightGBM/XGBoost.
Falls back to rule-based logic if no trained model is available.
"""

import os
import json
import logging
import numpy as np
import joblib
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved")

FEATURE_COLUMNS = [
    "subject_score", "attendance", #"assignment_score", "quiz_average",
    "lab_performance", "previous_related_score", #"study_hours",
    #"difficulty_factor", 
    "cgpa", "credits", "is_practical",
    "class_avg_score", 
    #"score_vs_class_avg", 
    "trend_indicator", "semester",
]

SEVERITY_NAMES = {0: "none", 1: "low", 2: "medium", 3: "high", 4: "critical"}
SEVERITY_ORDER = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

# Subject difficulty lookup (used when difficulty_factor not provided)
SUBJECT_DIFFICULTY = {
    "Engineering Mathematics-III": 0.82, "Engineering Mathematics-IV": 0.78,
    "Data Structures and Algorithms": 0.68, "Database Management Systems": 0.58,
    "Digital Logic & Design": 0.65, "Operating Systems": 0.72,
    "Computer Networks": 0.67, "Software Engineering": 0.50,
    "Microcontroller & Embedded Systems": 0.75, "Python": 0.38,
    "C++": 0.52, "Java": 0.55,
    "Automata Theory": 0.85, "Design & Analysis of Algorithms": 0.78,
    "Artificial Intelligence": 0.70, "Cryptography & Network Security": 0.80,
    "Full Stack Development": 0.48, "IoT": 0.60,
}

_DEFAULTS = {
    "subject_score": 50, "attendance": 70, 
    #"assignment_score": 60,
    #"quiz_average": 50, 
    "lab_performance": 55, "previous_related_score": 55,
    #"study_hours": 3, "difficulty_factor": 0.65,
    "cgpa": 6.0,
    "credits": 3, "is_practical": 0, "class_avg_score": 55,
    #"score_vs_class_avg": 0, 
    "trend_indicator": 0, "semester": 4,
}


class WeaknessDetector:
    """ML-powered weakness severity classifier."""

    def __init__(self):
        self.severity_model = None
        self.intervention_model = None
        self.scaler = None
        self.is_trained = False
        self.model_name = "unknown"
        self.feature_importance: Dict[str, float] = {}
        self._load()

    def _load(self):
        sev_path = os.path.join(MODEL_DIR, "weakness_severity_model.joblib")
        int_path = os.path.join(MODEL_DIR, "weakness_intervention_model.joblib")
        scaler_path = os.path.join(MODEL_DIR, "weakness_scaler.joblib")
        report_path = os.path.join(MODEL_DIR, "weakness_training_report.json")
        try:
            if os.path.exists(sev_path) and os.path.exists(scaler_path):
                self.severity_model = joblib.load(sev_path)
                self.scaler = joblib.load(scaler_path)
                if os.path.exists(int_path):
                    self.intervention_model = joblib.load(int_path)
                self.is_trained = True
                if os.path.exists(report_path):
                    with open(report_path) as f:
                        report = json.load(f)
                    self.model_name = report.get("severity_best_model", "unknown")
                    self.feature_importance = report.get("feature_importance", {})
                logger.info(f"✅ WeaknessDetector loaded ({self.model_name})")
            else:
                logger.warning("⚠️ Weakness model files not found. Using rule-based fallback.")
        except Exception as e:
            logger.error(f"Failed to load weakness model: {e}")

    # ── Feature extraction ──────────────────────────────────────

    def extract_features(self, data: Dict[str, Any]) -> np.ndarray:
        features = []
        for col in FEATURE_COLUMNS:
            val = data.get(col, _DEFAULTS.get(col, 0))
            features.append(float(val))
        return np.array(features, dtype=np.float32)

    @staticmethod
    def build_subject_features(
        subject_name: str,
        score: float,
        student_data: Dict[str, Any],
        attendance: float = 75,
        assignment_score: float = 65,
        quiz_average: float = 55,
        lab_performance: float = 60,
        previous_score: float = 55,
        class_avg: float = 55,
        trend: int = 0,
    ) -> Dict[str, Any]:
        """Build a feature dict for a single subject from available data."""
        difficulty = SUBJECT_DIFFICULTY.get(subject_name, 0.65)
        is_practical = 1 if "lab" in subject_name.lower() or "programming" in subject_name.lower() else 0
        cgpa = student_data.get("cgpa", student_data.get("overall_cgpa", 6.0))
        semester = student_data.get("current_semester", student_data.get("semester", 4))

        return {
            "subject_score": score,
            "attendance": attendance,
            #"assignment_score": assignment_score,
            #"quiz_average": quiz_average,
            "lab_performance": lab_performance,
            "previous_related_score": previous_score,
            #"study_hours": student_data.get("study_hours", 3),
            #"difficulty_factor": difficulty,
            "cgpa": cgpa,
            "credits": 4 if not is_practical else 1,
            "is_practical": is_practical,
            "class_avg_score": class_avg,
            #"score_vs_class_avg": score - class_avg,
            "trend_indicator": trend,
            "semester": semester,
        }

    # ── Detection ───────────────────────────────────────────────

    def detect(self, subject_features: Dict[str, Any]) -> Dict[str, Any]:
        """Detect weakness for a single subject."""
        features = self.extract_features(subject_features)
        score = subject_features.get("subject_score", 50)
        subject_name = subject_features.get("subject_name", "Unknown")

        if self.is_trained and self.severity_model is not None:
            feat_scaled = self.scaler.transform([features])
            severity_int = int(self.severity_model.predict(feat_scaled)[0])
            severity = SEVERITY_NAMES.get(severity_int, "medium")

            # Get probability for confidence
            if hasattr(self.severity_model, "predict_proba"):
                proba = self.severity_model.predict_proba(feat_scaled)[0]
                confidence = float(max(proba))
            else:
                confidence = 0.75

            # Intervention prediction
            needs_intervention = False
            if self.intervention_model is not None:
                needs_intervention = bool(self.intervention_model.predict(feat_scaled)[0])
            else:
                needs_intervention = severity_int >= 3
        else:
            severity, severity_int, confidence = self._rule_based_severity(subject_features)
            needs_intervention = severity_int >= 3

        # Generate suggestions
        weak_topics = self._identify_weak_topics(subject_name, score)
        suggestions = self._generate_suggestions(subject_name, severity, weak_topics)

        return {
            "subject": subject_name,
            "severity": severity,
            "severity_level": severity_int,
            "score": score,
            "gap": round(max(0, 60 - score), 1),
            "confidence": round(confidence, 2),
            "needs_intervention": needs_intervention,
            "weak_topics": weak_topics,
            "suggestions": suggestions,
            "model_used": self.model_name if self.is_trained else "rule_based",
            "factors": {
                "low_score": score < 50,
                "poor_attendance": subject_features.get("attendance", 75) < 65,
                "incomplete_assignments": subject_features.get("assignment_score", 65) < 50,
                "low_quiz_avg": subject_features.get("quiz_average", 55) < 45,
            },
        }

    def detect_all_subjects(
        self,
        student_data: Dict[str, Any],
        subjects: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Detect weaknesses across all subjects for a student.
        
        Args:
            student_data: student-level info (cgpa, semester, etc.)
            subjects: list of dicts with at least {name, score} per subject
        """
        weaknesses = []

        for subj in subjects:
            name = subj.get("subject_name", subj.get("name", "Unknown"))
            score = subj.get("total_marks", subj.get("score", 50))
            
            feat = self.build_subject_features(
                subject_name=name,
                score=score,
                student_data=student_data,
                attendance=subj.get("attendance", 75),
                assignment_score=subj.get("assignment_completion", subj.get("assignments_completed", 65)),
                quiz_average=float(np.mean(subj.get("quiz_scores", [55]))) if subj.get("quiz_scores") else 55,
                lab_performance=subj.get("lab_performance", 60),
                previous_score=subj.get("previous_score", 55),
                class_avg=subj.get("class_avg", 55),
                trend={"up": 1, "down": -1, "stable": 0}.get(subj.get("trend", "stable"), 0),
            )
            feat["subject_name"] = name

            result = self.detect(feat)
            if result["severity"] != "none":
                weaknesses.append(result)

        weaknesses.sort(key=lambda x: (-x["severity_level"], -x["gap"]))
        return weaknesses

    def get_intervention_recommendations(
        self, weaknesses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate intervention recommendations from weakness list."""
        interventions = []
        severity_counts = defaultdict(int)
        for w in weaknesses:
            severity_counts[w["severity"]] += 1

        if severity_counts.get("critical", 0) > 0:
            subjects = [w["subject"] for w in weaknesses if w["severity"] == "critical"]
            interventions.append({
                "type": "urgent",
                "action": "Immediate faculty intervention required",
                "subjects": subjects,
                "timeline": "within 48 hours",
                "priority": 1,
            })

        if severity_counts.get("high", 0) > 0:
            subjects = [w["subject"] for w in weaknesses if w["severity"] == "high"]
            interventions.append({
                "type": "high_priority",
                "action": "Enroll in remedial/tutoring sessions",
                "subjects": subjects,
                "timeline": "within 1 week",
                "priority": 2,
            })

        if len(weaknesses) > 3:
            interventions.append({
                "type": "comprehensive_review",
                "action": "Schedule complete academic performance review with advisor",
                "timeline": "within 2 weeks",
                "priority": 3,
            })

        return interventions

    # ── Rule-based fallback ─────────────────────────────────────

    @staticmethod
    def _rule_based_severity(data: Dict[str, Any]) -> Tuple[str, int, float]:
        score = data.get("subject_score", 50)
        attend = data.get("attendance", 75)
        assign = data.get("assignment_score", 65)

        if score < 30:
            sev, sev_int, conf = "critical", 4, 0.92
        elif score < 40:
            sev, sev_int, conf = "high", 3, 0.85
        elif score < 50:
            sev, sev_int, conf = "medium", 2, 0.78 if attend < 60 else 0.72
        elif score < 60:
            sev, sev_int, conf = "low", 1, 0.65
        else:
            sev, sev_int, conf = "none", 0, 0.80

        # Bump severity for low attendance / assignments
        if attend < 50 and sev_int < 3:
            sev_int = min(sev_int + 1, 4)
            sev = SEVERITY_NAMES[sev_int]
        if assign < 35 and sev_int < 3:
            sev_int = min(sev_int + 1, 4)
            sev = SEVERITY_NAMES[sev_int]

        return sev, sev_int, conf

    # ── Topic identification & suggestions ──────────────────────

    @staticmethod
    def _identify_weak_topics(subject: str, score: float) -> List[str]:
        if score >= 65:
            return []
        topic_map = {
            "Engineering Mathematics-III": ["Vector Spaces", "Linear Mapping", "Number Theory"],
            "Engineering Mathematics-IV": ["Probability", "Statistics", "Complex Integration"],
            "Data Structures and Algorithms": ["Trees & Graphs", "Hashing", "Dynamic Programming"],
            "Database Management Systems": ["Normalization", "SQL Queries", "Transaction Management"],
            "Operating Systems": ["Process Scheduling", "Memory Management", "Deadlocks"],
            "Computer Networks": ["TCP/IP", "Routing Protocols", "Network Security"],
            "Software Engineering": ["UML Diagrams", "Testing", "Agile Methodology"],
            "Microcontroller & Embedded Systems": ["Assembly Language", "Interrupts", "Interfacing"],
            "Automata Theory": ["Regular Languages", "Context-Free Grammars", "Turing Machines"],
            "Design & Analysis of Algorithms": ["Divide & Conquer", "Greedy", "NP-Completeness"],
            "Artificial Intelligence": ["Search Algorithms", "Knowledge Representation", "Neural Networks"],
            "Cryptography & Network Security": ["Symmetric Encryption", "Public Key", "Hash Functions"],
            "Digital Logic & Design": ["Boolean Algebra", "Flip-Flops", "Sequential Circuits"],
        }
        topics = topic_map.get(subject, ["Core Concepts", "Problem Solving"])
        return topics[:2] if score < 45 else topics[:1]

    @staticmethod
    def _generate_suggestions(subject: str, severity: str, weak_topics: List[str]) -> List[str]:
        suggestions = []
        if severity == "critical":
            suggestions = [
                f"URGENT: Schedule immediate consultation with {subject} faculty",
                "Attend intensive tutoring sessions (3+ hours daily)",
                "Review ALL fundamental concepts from scratch",
                "Complete every available practice problem set",
            ]
        elif severity == "high":
            suggestions = [
                f"Priority focus on {subject} — dedicate extra study time",
                "Join or form a study group for collaborative learning",
                "Solve previous year papers under timed conditions",
            ]
        elif severity == "medium":
            suggestions = [
                "Regular revision of weak concepts",
                "Practice problem-solving daily",
                "Attend all doubt-clearing sessions",
            ]
        elif severity == "low":
            suggestions = [
                "Maintain consistent practice",
                "Target advanced problems to strengthen understanding",
            ]
        if weak_topics:
            suggestions.append(f"Focus on: {', '.join(weak_topics)}")
        return suggestions


# ── Singleton ───────────────────────────────────────────────────
weakness_detector = WeaknessDetector()