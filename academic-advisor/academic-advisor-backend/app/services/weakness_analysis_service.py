# academic-advisor-backend/app/services/weakness_analysis_service.py
"""
ML-Powered Weakness Analysis Service
======================================
Replaces all rule-based severity thresholds with trained ML model predictions.

BEFORE (rule-based):
    if score < 40: severity = CRITICAL
    elif score < 50: severity = HIGH
    
AFTER (ML-based):
    features = {score, attendance, assignments, quizzes, difficulty, trend, ...}
    result = weakness_detector.detect(features)  # 15-feature ML model
    severity = result["severity"]  # considers ALL factors simultaneously
"""

import logging
import traceback
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np

from app.models.weakness import (
    WeaknessArea,
    WeaknessAnalysisRequest,
    WeaknessAnalysisResponse,
    WeaknessAnalysisResult,
    StudentInterestProfile,
    AnalysisBasis,
    SeverityLevel
)

logger = logging.getLogger(__name__)

# ── Import trained ML models ──
try:
    from app.ml.models.weakness_detector import weakness_detector as _ml_detector
    _ML_AVAILABLE = _ml_detector is not None and _ml_detector.is_trained
    if _ML_AVAILABLE:
        logger.info("✅ ML WeaknessDetector loaded for weakness analysis service")
    else:
        logger.warning("⚠️ WeaknessDetector not trained — will use ML fallback (rule-based inside model)")
except ImportError:
    _ml_detector = None
    _ML_AVAILABLE = False
    logger.warning("⚠️ WeaknessDetector import failed — using pure rule-based fallback")

try:
    from app.ml.models.performance_predictor import performance_predictor as _perf_predictor
    _PERF_AVAILABLE = _perf_predictor is not None and _perf_predictor.is_trained
except ImportError:
    _perf_predictor = None
    _PERF_AVAILABLE = False


class WeaknessAnalysisService:
    """
    ML-powered service for analyzing student weaknesses.
    
    Uses trained WeaknessDetector (LightGBM/XGBoost) to classify severity
    based on 15 features instead of simple score thresholds.
    
    A student scoring 58% with 40% attendance and declining quizzes
    gets flagged as HIGH severity — something rule-based logic misses.
    """

    # ═══════════════════════════════════════════════════════════
    # INTEREST → SUBJECT MAPPINGS (what subjects matter for each interest)
    # ═══════════════════════════════════════════════════════════

    INTEREST_SUBJECT_MAP: Dict[str, Dict[str, float]] = {
        "Machine Learning": {
            "Engineering Mathematics-III": 1.0,
            "Engineering Mathematics-IV": 0.9,
            "Python": 0.95,
            "Data Structures and Algorithms": 0.8,
            "Database Management Systems": 0.7,
            "Artificial Intelligence": 0.95,
        },
        "Artificial Intelligence": {
            "Engineering Mathematics-III": 0.95,
            "Python": 0.9,
            "Data Structures and Algorithms": 0.9,
            "Design & Analysis of Algorithms": 0.85,
            "Automata Theory": 0.7,
        },
        "Data Science": {
            "Engineering Mathematics-IV": 1.0,
            "Python": 0.95,
            "Database Management Systems": 0.9,
            "Engineering Mathematics-III": 0.8,
            "Data Structures and Algorithms": 0.75,
        },
        "Web Development": {
            "Database Management Systems": 0.9,
            "Full Stack Development": 0.95,
            "Computer Networks": 0.8,
            "Software Engineering": 0.75,
            "Python": 0.7,
        },
        "Cloud Computing": {
            "Computer Networks": 0.95,
            "Operating Systems": 0.9,
            "Database Management Systems": 0.8,
            "Cryptography & Network Security": 0.8,
            "Software Engineering": 0.7,
        },
        "Cybersecurity": {
            "Computer Networks": 1.0,
            "Operating Systems": 0.9,
            "Cryptography & Network Security": 0.95,
            "Data Structures and Algorithms": 0.7,
        },
        "IoT": {
            "Microcontroller & Embedded Systems": 0.95,
            "Computer Networks": 0.9,
            "Digital Logic & Design": 0.8,
            "Python": 0.7,
            "C++": 0.75,
        },
        "Mobile Development": {
            "Data Structures and Algorithms": 0.85,
            "Database Management Systems": 0.8,
            "Software Engineering": 0.7,
            "Computer Networks": 0.65,
        },
        "DevOps": {
            "Operating Systems": 0.95,
            "Computer Networks": 0.85,
            "Software Engineering": 0.85,
            "Python": 0.75,
        },
        "Blockchain": {
            "Cryptography & Network Security": 0.95,
            "Data Structures and Algorithms": 0.9,
            "Computer Networks": 0.8,
            "Database Management Systems": 0.7,
        },
    }

    # ═══════════════════════════════════════════════════════════
    # ELECTIVE → PREREQUISITE MAPPINGS
    # Sem 5: CCS, DWM    |    Sem 6: ML, WT
    # ═══════════════════════════════════════════════════════════

    ELECTIVE_PREREQUISITES: Dict[str, Dict[str, Tuple[float, str]]] = {
        "Machine Learning": {
            "Python": (0.95, "Critical"),
            "Engineering Mathematics-III": (0.9, "Critical"),
            "Engineering Mathematics-IV": (0.85, "High"),
            "Data Structures and Algorithms": (0.8, "High"),
            "Artificial Intelligence": (0.85, "High"),
        },
        "ML": {
            "Python": (0.95, "Critical"),
            "Engineering Mathematics-III": (0.9, "Critical"),
            "Data Structures and Algorithms": (0.8, "High"),
            "Artificial Intelligence": (0.85, "High"),
        },
        "Wireless Technology": {
            "Computer Networks": (0.95, "Critical"),
            "Microcontroller & Embedded Systems": (0.9, "High"),
            "Digital Logic & Design": (0.75, "Medium"),
            "IoT": (0.85, "High"),
        },
        "WT": {
            "Computer Networks": (0.95, "Critical"),
            "Microcontroller & Embedded Systems": (0.9, "High"),
            "IoT": (0.85, "High"),
        },
        "Data Warehouse and Mining": {
            "Database Management Systems": (0.95, "Critical"),
            "Data Structures and Algorithms": (0.85, "High"),
            "Python": (0.8, "Medium"),
            "Engineering Mathematics-IV": (0.75, "Medium"),
        },
        "DWM": {
            "Database Management Systems": (0.95, "Critical"),
            "Data Structures and Algorithms": (0.85, "High"),
            "Python": (0.8, "Medium"),
        },
        "Cloud Computing Services": {
            "Computer Networks": (0.9, "Critical"),
            "Operating Systems": (0.9, "Critical"),
            "Database Management Systems": (0.8, "Medium"),
            "Full Stack Development": (0.85, "High"),
            "Software Engineering": (0.75, "Medium"),
        },
        "CCS": {
            "Computer Networks": (0.9, "Critical"),
            "Operating Systems": (0.9, "Critical"),
            "Full Stack Development": (0.85, "High"),
        },
    }

    # ═══════════════════════════════════════════════════════════
    # HONOURS/MINOR → PREREQUISITES
    # IT Honours: AIML, Cybersecurity  |  Rest are Minors
    # ═══════════════════════════════════════════════════════════

    HONOURS_PREREQUISITES: Dict[str, Dict[str, Tuple[float, str]]] = {
        "AI & Machine Learning": {
            "Engineering Mathematics-III": (1.0, "Critical"),
            "Python": (0.95, "Critical"),
            "Data Structures and Algorithms": (0.9, "Critical"),
            "Engineering Mathematics-IV": (0.85, "High"),
            "Artificial Intelligence": (0.9, "Critical"),
        },
        "AIML": {
            "Engineering Mathematics-III": (1.0, "Critical"),
            "Python": (0.95, "Critical"),
            "Data Structures and Algorithms": (0.9, "Critical"),
            "Artificial Intelligence": (0.9, "Critical"),
        },
        "Cybersecurity": {
            "Computer Networks": (0.95, "Critical"),
            "Operating Systems": (0.9, "Critical"),
            "Cryptography & Network Security": (0.95, "Critical"),
            "Data Structures and Algorithms": (0.8, "High"),
        },
        "Data Science": {
            "Engineering Mathematics-IV": (1.0, "Critical"),
            "Python": (0.95, "Critical"),
            "Database Management Systems": (0.9, "Critical"),
            "Data Structures and Algorithms": (0.8, "High"),
        },
        "Cloud Computing": {
            "Computer Networks": (0.95, "Critical"),
            "Operating Systems": (0.95, "Critical"),
            "Database Management Systems": (0.85, "High"),
            "Software Engineering": (0.75, "Medium"),
        },
        "IoT & Embedded Systems": {
            "Microcontroller & Embedded Systems": (0.95, "Critical"),
            "Computer Networks": (0.9, "High"),
            "Digital Logic & Design": (0.8, "High"),
            "Python": (0.75, "Medium"),
        },
        "Full Stack Development": {
            "Database Management Systems": (0.9, "Critical"),
            "Full Stack Development": (0.95, "Critical"),
            "Computer Networks": (0.85, "High"),
            "Software Engineering": (0.8, "High"),
        },
    }

    def __init__(self):
        self.logger = logger
        self._ml_available = _ML_AVAILABLE
        if self._ml_available:
            self.logger.info("✅ WeaknessAnalysisService using TRAINED ML model")
        else:
            self.logger.info("⚠️ WeaknessAnalysisService using ML model with rule-based fallback")

    # ═══════════════════════════════════════════════════════════
    #  CORE ML METHOD — replaces all rule-based severity
    # ═══════════════════════════════════════════════════════════

    def _ml_detect_weakness(
        self,
        subject_name: str,
        score: float,
        student_data: Dict[str, Any],
        weight: float = 1.0,
        importance: str = "Medium",
    ) -> Dict[str, Any]:
        """
        Use trained ML model to detect weakness severity.
        
        REPLACES: _calculate_severity() which was just:
            if weighted_score < 35: return CRITICAL
            elif weighted_score < 50: return HIGH
        
        NOW considers 15 features simultaneously:
            score, attendance, assignments, quizzes, lab_performance,
            previous_score, study_hours, difficulty, cgpa, credits,
            is_practical, class_avg, score_vs_avg, trend, semester
        
        The ML model was trained on 60,000+ student-subject pairs
        covering all score ranges (5-100).
        """
        # Extract available metrics from student data
        attendance = self._extract_attendance(student_data, subject_name)
        assignment_score = self._extract_assignment_score(student_data, subject_name)
        quiz_avg = self._extract_quiz_average(student_data, subject_name)
        lab_perf = self._extract_lab_performance(student_data, subject_name)
        prev_score = self._find_previous_score(student_data, subject_name)
        study_hours = student_data.get("study_hours", 3)
        cgpa = student_data.get("cgpa", student_data.get("overall_cgpa", 6.0))
        semester = self._parse_semester(student_data.get("semester", "4"))
        trend = self._get_trend_indicator(student_data, subject_name)

        if _ml_detector is not None:
            # Build features and call trained model
            features = _ml_detector.build_subject_features(
                subject_name=subject_name,
                score=score,
                student_data={"cgpa": cgpa, "semester": semester, "study_hours": study_hours},
                attendance=attendance,
                assignment_score=assignment_score,
                quiz_average=quiz_avg,
                lab_performance=lab_perf,
                previous_score=prev_score,
                class_avg=55,  # Will be overridden if available
                trend=trend,
            )
            features["subject_name"] = subject_name
            result = _ml_detector.detect(features)
        else:
            # Fallback: create a basic result using simple logic
            result = self._fallback_detect(subject_name, score, attendance, assignment_score, quiz_avg)

        return result

    def _fallback_detect(
        self, subject: str, score: float, attendance: float,
        assignment: float, quiz_avg: float
    ) -> Dict[str, Any]:
        """Rule-based fallback when ML model unavailable."""
        risk = 0
        if score < 30: risk += 50
        elif score < 40: risk += 40
        elif score < 50: risk += 30
        elif score < 60: risk += 20
        elif score < 70: risk += 10

        if attendance < 50: risk += 20
        elif attendance < 65: risk += 12
        elif attendance < 75: risk += 5

        if assignment < 40: risk += 12
        elif assignment < 60: risk += 6

        if quiz_avg < 40: risk += 8
        elif quiz_avg < 55: risk += 4

        if risk >= 65:
            sev, sev_int = "critical", 4
        elif risk >= 48:
            sev, sev_int = "high", 3
        elif risk >= 32:
            sev, sev_int = "medium", 2
        elif risk >= 18:
            sev, sev_int = "low", 1
        else:
            sev, sev_int = "none", 0

        return {
            "subject": subject, "severity": sev, "severity_level": sev_int,
            "score": score, "gap": max(0, 60 - score),
            "confidence": 0.55, "needs_intervention": sev_int >= 3,
            "weak_topics": [], "suggestions": [],
            "model_used": "rule_fallback",
            "factors": {"low_score": score < 50, "poor_attendance": attendance < 65,
                        "incomplete_assignments": assignment < 50},
        }

    # ═══════════════════════════════════════════════════════════
    #  FEATURE EXTRACTION HELPERS (from student data)
    # ═══════════════════════════════════════════════════════════

    def _extract_attendance(self, student_data: Dict, subject_name: str) -> float:
        """Extract attendance — tries subject-level, then overall."""
        subjects = student_data.get("subjects", {})
        if subject_name in subjects:
            subj_data = subjects[subject_name]
            if isinstance(subj_data, dict):
                att = subj_data.get("attendance")
                if att is not None:
                    return float(att)
        return float(student_data.get("attendance_average", student_data.get("attendance", 75)))

    def _extract_assignment_score(self, student_data: Dict, subject_name: str) -> float:
        subjects = student_data.get("subjects", {})
        if subject_name in subjects:
            subj_data = subjects[subject_name]
            if isinstance(subj_data, dict):
                val = subj_data.get("assignments_completed", subj_data.get("assignment_score"))
                if val is not None:
                    return float(val)
        return float(student_data.get("assignment_completion_rate", 65))

    def _extract_quiz_average(self, student_data: Dict, subject_name: str) -> float:
        subjects = student_data.get("subjects", {})
        if subject_name in subjects:
            subj_data = subjects[subject_name]
            if isinstance(subj_data, dict):
                quizzes = subj_data.get("quiz_scores", [])
                if quizzes:
                    return float(np.mean(quizzes))
        return 55.0

    def _extract_lab_performance(self, student_data: Dict, subject_name: str) -> float:
        name_lower = subject_name.lower()
        is_lab = any(kw in name_lower for kw in ["lab", "practical", "programming"])
        subjects = student_data.get("subjects", {})
        if subject_name in subjects:
            subj_data = subjects[subject_name]
            if isinstance(subj_data, dict):
                return float(subj_data.get("score", 60))
        return 65 if is_lab else 55

    def _find_previous_score(self, student_data: Dict, subject_name: str) -> float:
        """Find score in prerequisite subject."""
        PREREQ_MAP = {
            "Engineering Mathematics-IV": "Engineering Mathematics-III",
            "Design & Analysis of Algorithms": "Data Structures and Algorithms",
            "Cryptography & Network Security": "Computer Networks",
            "Artificial Intelligence": "Engineering Mathematics-III",
        }
        prereq = PREREQ_MAP.get(subject_name)
        if prereq:
            score = self._find_subject_score(student_data.get("subjects", {}), prereq)
            if score is not None:
                return score
        return 55.0

    def _get_trend_indicator(self, student_data: Dict, subject_name: str) -> int:
        subjects = student_data.get("subjects", {})
        if subject_name in subjects:
            subj = subjects[subject_name]
            if isinstance(subj, dict):
                trend = subj.get("trend", "stable")
                if hasattr(trend, "value"):
                    trend = trend.value
                return {"up": 1, "improving": 1, "down": -1, "declining": -1}.get(trend, 0)
        return 0

    def _parse_semester(self, sem_val) -> int:
        try:
            return int(str(sem_val).strip())
        except (ValueError, TypeError):
            return 4

    # ═══════════════════════════════════════════════════════════
    #  MAIN ANALYSIS ENTRY POINT
    # ═══════════════════════════════════════════════════════════

    async def analyze_weaknesses(
        self, request: WeaknessAnalysisRequest
    ) -> WeaknessAnalysisResponse:
        try:
            student_id = request.student_id
            student_data = await self._get_student_data(student_id)

            interests = request.interests
            if not interests and request.analysis_basis in [
                AnalysisBasis.INTEREST, AnalysisBasis.COMBINED
            ]:
                interests = await self._get_student_interests(student_id)

            electives = request.recommended_electives
            if not electives and request.analysis_basis in [
                AnalysisBasis.ELECTIVES, AnalysisBasis.COMBINED
            ]:
                electives = await self._get_recommended_electives(student_id, student_data)

            honours_minors = request.honours_minors
            if not honours_minors and request.analysis_basis in [
                AnalysisBasis.HONOURS_MINORS, AnalysisBasis.COMBINED
            ]:
                honours_minors = await self._get_recommended_honours(student_id, student_data)

            if request.analysis_basis == AnalysisBasis.INTEREST:
                weaknesses = await self._analyze_by_interests(student_data, interests or [])
            elif request.analysis_basis == AnalysisBasis.ELECTIVES:
                weaknesses = await self._analyze_by_electives(student_data, electives or [])
            elif request.analysis_basis == AnalysisBasis.HONOURS_MINORS:
                weaknesses = await self._analyze_by_honours(student_data, honours_minors or [])
            elif request.analysis_basis == AnalysisBasis.PERFORMANCE:
                weaknesses = await self._analyze_by_performance(student_data)
            else:
                weaknesses = await self._analyze_combined(
                    student_data, interests or [], electives or [], honours_minors or []
                )

            response = self._build_response(
                student_id=student_id,
                analysis_basis=request.analysis_basis,
                weaknesses=weaknesses,
                include_resources=request.include_resources,
                include_study_plan=request.include_study_plan,
                student_data=student_data,
            )

            await self._save_analysis_result(response, interests, electives, honours_minors)
            return response

        except Exception as e:
            self.logger.error(f"Error analyzing weaknesses: {e}")
            raise

    # ═══════════════════════════════════════════════════════════
    #  ML-POWERED ANALYSIS METHODS (replacing rule-based)
    # ═══════════════════════════════════════════════════════════

    async def _analyze_by_interests(
        self, student_data: Dict[str, Any], interests: List[str]
    ) -> List[WeaknessArea]:
        """Analyze weaknesses using ML model based on student's interests."""
        weaknesses = []
        subjects = student_data.get("subjects", {})

        for interest in interests:
            required = self.INTEREST_SUBJECT_MAP.get(interest)
            if not required:
                continue

            for req_subject, weight in required.items():
                student_score = self._find_subject_score(subjects, req_subject)

                if student_score is None:
                    # Subject not taken — flag as potential weakness
                    weaknesses.append(self._create_weakness_area(
                        subject=req_subject, current_score=0,
                        related_to=f"{interest} interest",
                        analysis_basis=AnalysisBasis.INTEREST,
                        topic=f"Prerequisite for {interest}",
                        severity=SeverityLevel.MEDIUM,
                        confidence=0.6,
                        impact_on_interest=f"Required foundation for {interest}",
                    ))
                else:
                    # ── ML MODEL CALL ──
                    ml_result = self._ml_detect_weakness(
                        req_subject, student_score, student_data, weight
                    )
                    severity_str = ml_result["severity"]

                    if severity_str != "none":
                        # Boost severity for high-weight subjects
                        if weight >= 0.85 and severity_str == "low":
                            severity_str = "medium"  # Important subjects get bumped
                            ml_result["confidence"] = min(ml_result["confidence"] + 0.05, 0.95)

                        weaknesses.append(self._create_weakness_area(
                            subject=req_subject,
                            current_score=student_score,
                            related_to=f"{interest} interest",
                            analysis_basis=AnalysisBasis.INTEREST,
                            topic=f"Foundation for {interest}",
                            severity=SeverityLevel(severity_str),
                            confidence=ml_result["confidence"] * weight,
                            impact_on_interest=f"ML model detected weakness affecting {interest}",
                            ml_factors=ml_result.get("factors", {}),
                        ))

        return weaknesses

    async def _analyze_by_electives(
        self, student_data: Dict[str, Any], electives: List[str]
    ) -> List[WeaknessArea]:
        """Analyze weaknesses for elective prerequisites using ML model."""
        weaknesses = []
        subjects = student_data.get("subjects", {})

        for elective in electives:
            prerequisites = self.ELECTIVE_PREREQUISITES.get(elective)
            if not prerequisites:
                continue

            for prereq, (weight, importance) in prerequisites.items():
                student_score = self._find_subject_score(subjects, prereq)

                if student_score is None:
                    sev = SeverityLevel.HIGH if importance == "Critical" else SeverityLevel.MEDIUM
                    weaknesses.append(self._create_weakness_area(
                        subject=prereq, current_score=0,
                        related_to=f"{elective} elective",
                        analysis_basis=AnalysisBasis.ELECTIVES,
                        topic=f"Prerequisite for {elective}",
                        severity=sev, confidence=0.7,
                        impact_on_elective=f"Required before taking {elective}",
                    ))
                else:
                    # ── ML MODEL CALL ──
                    ml_result = self._ml_detect_weakness(
                        prereq, student_score, student_data, weight, importance
                    )
                    severity_str = ml_result["severity"]

                    # For Critical prerequisites, bump severity if model says "low"
                    if importance == "Critical" and severity_str == "low":
                        severity_str = "medium"
                    elif importance == "Critical" and severity_str == "none" and student_score < 65:
                        severity_str = "low"

                    if severity_str != "none":
                        weaknesses.append(self._create_weakness_area(
                            subject=prereq,
                            current_score=student_score,
                            related_to=f"{elective} elective",
                            analysis_basis=AnalysisBasis.ELECTIVES,
                            topic=f"Prerequisite for {elective} ({importance})",
                            severity=SeverityLevel(severity_str),
                            confidence=ml_result["confidence"] * weight,
                            impact_on_elective=f"ML: {severity_str} weakness for {elective}",
                            ml_factors=ml_result.get("factors", {}),
                        ))

        return weaknesses

    async def _analyze_by_honours(
        self, student_data: Dict[str, Any], honours_minors: List[str]
    ) -> List[WeaknessArea]:
        """Analyze weaknesses for honours/minor prerequisites using ML model."""
        weaknesses = []
        subjects = student_data.get("subjects", {})

        for program in honours_minors:
            prerequisites = self.HONOURS_PREREQUISITES.get(program)
            if not prerequisites:
                # Try partial match
                for key in self.HONOURS_PREREQUISITES:
                    if key.lower() in program.lower() or program.lower() in key.lower():
                        prerequisites = self.HONOURS_PREREQUISITES[key]
                        break
            if not prerequisites:
                continue

            for prereq, (weight, importance) in prerequisites.items():
                student_score = self._find_subject_score(subjects, prereq)

                # Honours require HIGHER thresholds
                if student_score is None:
                    weaknesses.append(self._create_weakness_area(
                        subject=prereq, current_score=0,
                        related_to=f"{program}",
                        analysis_basis=AnalysisBasis.HONOURS_MINORS,
                        topic=f"Required for {program}",
                        severity=SeverityLevel.HIGH, confidence=0.8,
                        impact_on_career=f"Essential for {program} eligibility",
                    ))
                else:
                    # ── ML MODEL CALL ──
                    ml_result = self._ml_detect_weakness(
                        prereq, student_score, student_data, weight, importance
                    )
                    severity_str = ml_result["severity"]

                    # Honours programs need higher scores
                    # If ML says "none" but score < 70, still flag as "low" for honours
                    if severity_str == "none" and student_score < 70 and weight >= 0.85:
                        severity_str = "low"
                        ml_result["confidence"] = 0.65
                    elif severity_str == "low" and importance == "Critical":
                        severity_str = "medium"

                    if severity_str != "none":
                        weaknesses.append(self._create_weakness_area(
                            subject=prereq,
                            current_score=student_score,
                            related_to=f"{program}",
                            analysis_basis=AnalysisBasis.HONOURS_MINORS,
                            topic=f"Required for {program} ({importance})",
                            severity=SeverityLevel(severity_str),
                            confidence=ml_result["confidence"] * weight,
                            impact_on_career=f"Must improve for {program} readiness",
                            ml_factors=ml_result.get("factors", {}),
                        ))

        return weaknesses

    async def _analyze_by_performance(
        self, student_data: Dict[str, Any]
    ) -> List[WeaknessArea]:
        """Analyze ALL subjects using ML model — no threshold gating."""
        weaknesses = []
        subjects = student_data.get("subjects", {})

        for subject_name, data in subjects.items():
            score = data.get("score", 0) if isinstance(data, dict) else 0

            # ── ML MODEL CALL for EVERY subject ──
            # The ML model decides if it's a weakness, not hardcoded score < 60
            ml_result = self._ml_detect_weakness(
                subject_name, score, student_data
            )
            severity_str = ml_result["severity"]

            if severity_str != "none":
                trend = data.get("trend", "stable") if isinstance(data, dict) else "stable"
                if hasattr(trend, "value"):
                    trend = trend.value

                # Extra context for declining subjects
                related_to = "Academic performance"
                if trend in ("down", "declining") and severity_str in ("low", "medium"):
                    related_to = "Declining performance (ML detected)"

                weaknesses.append(self._create_weakness_area(
                    subject=subject_name,
                    current_score=score,
                    related_to=related_to,
                    analysis_basis=AnalysisBasis.PERFORMANCE,
                    topic="ML-detected weakness",
                    severity=SeverityLevel(severity_str),
                    confidence=ml_result["confidence"],
                    ml_factors=ml_result.get("factors", {}),
                ))

        return weaknesses

    async def _analyze_combined(
        self, student_data: Dict[str, Any],
        interests: List[str], electives: List[str], honours_minors: List[str]
    ) -> List[WeaknessArea]:
        all_weaknesses = []
        if interests:
            all_weaknesses.extend(await self._analyze_by_interests(student_data, interests))
        if electives:
            all_weaknesses.extend(await self._analyze_by_electives(student_data, electives))
        if honours_minors:
            all_weaknesses.extend(await self._analyze_by_honours(student_data, honours_minors))
        all_weaknesses.extend(await self._analyze_by_performance(student_data))
        return self._merge_weaknesses(all_weaknesses)

    # ═══════════════════════════════════════════════════════════
    #  PERFORMANCE PREDICTION INTEGRATION
    # ═══════════════════════════════════════════════════════════

    def _get_performance_prediction(self, student_data: Dict[str, Any]) -> Optional[Dict]:
        """Get SGPA prediction from trained performance model."""
        if not _PERF_AVAILABLE or _perf_predictor is None:
            return None
        try:
            pred = _perf_predictor.predict(student_data)
            return pred
        except Exception as e:
            self.logger.warning(f"Performance prediction failed: {e}")
            return None

    # ═══════════════════════════════════════════════════════════
    #  DATA FETCHING (unchanged from original)
    # ═══════════════════════════════════════════════════════════

    async def _get_student_data(self, student_id: str) -> Dict[str, Any]:
        """Fetch student academic data from database"""
        try:
            from app.models.student import StudentPerformance
            from app.models.student_profile import StudentProfile

            performance = await StudentPerformance.find_one(
                StudentPerformance.student_info.uid == student_id
            )

            if performance:
                subject_scores = {}
                for subject in performance.subjects:
                    subject_scores[subject.name] = {
                        "score": subject.score,
                        "credits": subject.credits,
                        "trend": subject.trend.value if hasattr(subject.trend, "value") else subject.trend,
                        "weakness": subject.weakness,
                        "strength": subject.strength,
                        "attendance": getattr(subject, "attendance", None),
                        "quiz_scores": getattr(subject, "quiz_scores", []),
                        "assignments_completed": getattr(subject, "assignments_completed", None),
                    }
                return {
                    "student_id": student_id,
                    "cgpa": performance.overall_cgpa,
                    "sgpa": performance.semester_sgpa,
                    "semester": performance.student_info.semester,
                    "branch": performance.student_info.branch,
                    "subjects": subject_scores,
                    "strong_subjects": performance.strong_subjects,
                    "weak_subjects": performance.weak_subjects,
                    "interests": performance.interests,
                    "career_goals": performance.career_goals,
                    "skills_matrix": performance.skills_matrix,
                    "attendance_average": getattr(performance, "attendance_average", 75),
                    "assignment_completion_rate": getattr(performance, "assignment_completion_rate", 65),
                }

            profile = await StudentProfile.find_one(StudentProfile.user_id == student_id)
            if profile:
                subject_scores = {}
                for semester in profile.semester_records:
                    for subject in semester.subjects:
                        score = subject.total_marks
                        if score > 100:
                            score = min(score, 100)
                        existing = subject_scores.get(subject.subject_name)
                        if not existing or score > existing["score"]:
                            subject_scores[subject.subject_name] = {
                                "score": score,
                                "credits": subject.credits,
                                "grade": subject.grade,
                                "code": subject.subject_code,
                                "trend": "stable",
                            }
                return {
                    "student_id": student_id,
                    "cgpa": profile.cgpa,
                    "sgpa": profile.semester_records[-1].sgpa if profile.semester_records else 0,
                    "semester": profile.current_semester,
                    "branch": profile.branch,
                    "subjects": subject_scores,
                    "strong_subjects": [],
                    "weak_subjects": [],
                    "interests": getattr(profile, "interests", []) or [],
                    "career_goals": getattr(profile, "career_goals", []) or [],
                    "skills_matrix": {},
                }

            self.logger.warning(f"⚠️ No student data found for {student_id}")
            return self._get_default_student_data(student_id)

        except Exception as e:
            self.logger.error(f"Error fetching student data: {e}")
            traceback.print_exc()
            return self._get_default_student_data(student_id)

    def _get_default_student_data(self, student_id: str) -> Dict[str, Any]:
        return {
            "student_id": student_id, "cgpa": 7.5, "sgpa": 7.8,
            "semester": "5", "branch": "IT",
            "subjects": {
                "Data Structures and Algorithms": {"score": 75, "credits": 4, "trend": "up"},
                "Database Management Systems": {"score": 68, "credits": 4, "trend": "stable"},
                "Computer Networks": {"score": 72, "credits": 3, "trend": "up"},
                "Operating Systems": {"score": 70, "credits": 4, "trend": "stable"},
                "Python": {"score": 82, "credits": 3, "trend": "up"},
                "Engineering Mathematics-III": {"score": 65, "credits": 4, "trend": "down"},
            },
            "strong_subjects": ["Python", "Data Structures and Algorithms"],
            "weak_subjects": ["Engineering Mathematics-III"],
            "interests": ["Machine Learning", "Web Development"],
            "career_goals": ["Software Engineer"],
            "skills_matrix": {"Python": 0.8, "JavaScript": 0.6, "SQL": 0.7},
        }

    async def _get_student_interests(self, student_id: str) -> List[str]:
        try:
            interest_profile = await StudentInterestProfile.find_one(
                StudentInterestProfile.user_id == student_id
            )
            if interest_profile and interest_profile.interests:
                return interest_profile.interests

            from app.models.student_profile import StudentProfile
            profile = await StudentProfile.find_one(StudentProfile.user_id == student_id)
            if profile and profile.interests:
                new_profile = StudentInterestProfile(
                    user_id=student_id, interests=profile.interests,
                    career_goals=profile.career_goals if profile.career_goals else []
                )
                await new_profile.save()
                return profile.interests

            from app.models.student import StudentPerformance
            performance = await StudentPerformance.find_one(
                StudentPerformance.student_info.uid == student_id
            )
            if performance and performance.interests:
                new_profile = StudentInterestProfile(
                    user_id=student_id, interests=performance.interests
                )
                await new_profile.save()
                return performance.interests

            return []
        except Exception as e:
            self.logger.error(f"Error fetching interests: {e}")
            return []

    async def _get_recommended_electives(self, student_id: str, student_data: Dict) -> List[str]:
        interests = student_data.get("interests", [])
        suggestions = []
        interest_lower = [i.lower() for i in interests]
        for il in interest_lower:
            if any(kw in il for kw in ["machine learning", "ai", "artificial"]):
                suggestions.append("ML")
            if any(kw in il for kw in ["iot", "embedded", "wireless"]):
                suggestions.append("WT")
            if any(kw in il for kw in ["data science", "analytics", "data"]):
                suggestions.append("DWM")
            if any(kw in il for kw in ["cloud", "devops", "web"]):
                suggestions.append("CCS")
        return suggestions or ["ML", "CCS"]

    async def _get_recommended_honours(self, student_id: str, student_data: Dict) -> List[str]:
        cgpa = student_data.get("cgpa", 0)
        interests = student_data.get("interests", [])
        recs = []
        if cgpa >= 7.5:
            interest_lower = " ".join(interests).lower()
            if any(kw in interest_lower for kw in ["machine learning", "ai", "data science"]):
                recs.append("AI & Machine Learning")
            if any(kw in interest_lower for kw in ["security", "cyber", "network"]):
                recs.append("Cybersecurity")
            if any(kw in interest_lower for kw in ["cloud", "devops"]):
                recs.append("Cloud Computing")
            if any(kw in interest_lower for kw in ["iot", "embedded"]):
                recs.append("IoT & Embedded Systems")
        return recs[:2]

    # ═══════════════════════════════════════════════════════════
    #  SUBJECT MATCHING (unchanged from original)
    # ═══════════════════════════════════════════════════════════

    def _find_subject_score(self, subjects: Dict[str, Any], target_subject: str) -> Optional[float]:
        target_lower = target_subject.lower().strip()

        ALIASES: Dict[str, List[str]] = {
            "engineering mathematics-iii": ["math-iii", "mathematics-iii", "math-3", "linear algebra", "bsc301"],
            "engineering mathematics-iv": ["math-iv", "mathematics-iv", "math-4", "statistics", "probability", "bsc401"],
            "python": ["python programming", "python programming lab", "python lab", "py"],
            "data structures and algorithms": ["dsa", "ds", "data structures", "data structure"],
            "database management systems": ["dbms", "database management", "database", "rdbms"],
            "computer networks": ["cn", "networking", "networks"],
            "operating systems": ["os", "operating system"],
            "microcontroller & embedded systems": ["embedded systems", "microprocessor", "mes", "embedded"],
            "software engineering": ["se"],
            "digital logic & design": ["dlda", "digital logic", "digital logic & computer architecture"],
            "artificial intelligence": ["ai"],
            "cryptography & network security": ["crypto", "cns", "cryptography", "security"],
            "automata theory": ["toc", "theory of computer science", "automata"],
            "design & analysis of algorithms": ["daa", "algorithm design"],
            "full stack development": ["fsdl", "full stack", "web development"],
            "iot": ["internet of things"],
        }

        # 1. Exact match
        for name, data in subjects.items():
            if target_lower == name.lower().strip():
                return data.get("score", 0) if isinstance(data, dict) else 0

        # 2. Contains match
        for name, data in subjects.items():
            s_lower = name.lower().strip()
            if target_lower in s_lower or s_lower in target_lower:
                return data.get("score", 0) if isinstance(data, dict) else 0

        # 3. Alias match
        aliases_to_check = set()
        for canonical, alias_list in ALIASES.items():
            if target_lower == canonical or target_lower in alias_list:
                aliases_to_check.add(canonical)
                aliases_to_check.update(alias_list)
        for canonical, alias_list in ALIASES.items():
            if any(a == target_lower for a in alias_list):
                aliases_to_check.add(canonical)
                aliases_to_check.update(alias_list)

        for alias in aliases_to_check:
            for name, data in subjects.items():
                s_lower = name.lower().strip()
                if alias == s_lower or alias in s_lower or s_lower in alias:
                    return data.get("score", 0) if isinstance(data, dict) else 0

        # 4. Word overlap
        target_words = set(target_lower.replace("-", " ").replace("/", " ").split())
        filler = {"and", "of", "the", "in", "for", "to", "a", "an", "&"}
        target_clean = target_words - filler
        for name, data in subjects.items():
            subject_words = set(name.lower().replace("-", " ").replace("/", " ").split()) - filler
            common = target_clean & subject_words
            threshold = 1 if len(target_clean) <= 2 else 2
            if len(common) >= threshold:
                return data.get("score", 0) if isinstance(data, dict) else 0

        return None

    # ═══════════════════════════════════════════════════════════
    #  WEAKNESS AREA CREATION & RESPONSE BUILDING
    # ═══════════════════════════════════════════════════════════

    def _create_weakness_area(
        self, subject: str, current_score: float, related_to: str,
        analysis_basis: AnalysisBasis, topic: Optional[str] = None,
        severity: SeverityLevel = SeverityLevel.MEDIUM,
        confidence: float = 0.8,
        impact_on_interest: Optional[str] = None,
        impact_on_elective: Optional[str] = None,
        impact_on_career: Optional[str] = None,
        ml_factors: Optional[Dict] = None,
    ) -> WeaknessArea:
        target_score = 75 if severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH] else 70
        gap = max(0, target_score - current_score)

        return WeaknessArea(
            subject=subject, topic=topic,
            current_score=current_score, target_score=target_score,
            gap_percentage=gap, severity=severity,
            confidence=min(confidence, 0.95),
            related_to=related_to, analysis_basis=analysis_basis,
            improvement_suggestions=self._get_improvement_suggestions(subject, severity),
            recommended_resources=self._get_resources(subject, severity),
            estimated_improvement_time=self._estimate_improvement_time(gap, severity),
            priority=self._severity_to_priority(severity),
            impact_on_interest=impact_on_interest,
            impact_on_elective=impact_on_elective,
            impact_on_career=impact_on_career,
        )

    def _merge_weaknesses(self, weaknesses: List[WeaknessArea]) -> List[WeaknessArea]:
        merged: Dict[str, WeaknessArea] = {}
        for w in weaknesses:
            key = w.subject.lower()
            if key in merged:
                existing = merged[key]
                if self._severity_to_priority(w.severity) > self._severity_to_priority(existing.severity):
                    existing.severity = w.severity
                    existing.priority = w.priority
                if w.related_to not in existing.related_to:
                    existing.related_to = f"{existing.related_to}, {w.related_to}"
                if w.current_score < existing.current_score:
                    existing.current_score = w.current_score
                    existing.gap_percentage = max(existing.gap_percentage, w.gap_percentage)
                if w.confidence > existing.confidence:
                    existing.confidence = w.confidence
                if w.impact_on_interest and not existing.impact_on_interest:
                    existing.impact_on_interest = w.impact_on_interest
                if w.impact_on_elective and not existing.impact_on_elective:
                    existing.impact_on_elective = w.impact_on_elective
                if w.impact_on_career and not existing.impact_on_career:
                    existing.impact_on_career = w.impact_on_career
            else:
                merged[key] = w
        return list(merged.values())

    def _severity_to_priority(self, severity: SeverityLevel) -> int:
        return {SeverityLevel.CRITICAL: 5, SeverityLevel.HIGH: 4,
                SeverityLevel.MEDIUM: 3, SeverityLevel.LOW: 2}.get(severity, 1)

    def _build_response(
        self, student_id: str, analysis_basis: AnalysisBasis,
        weaknesses: List[WeaknessArea], include_resources: bool,
        include_study_plan: bool, student_data: Optional[Dict] = None,
    ) -> WeaknessAnalysisResponse:
        sorted_weaknesses = sorted(weaknesses, key=lambda x: x.priority, reverse=True)

        critical = sum(1 for w in weaknesses if w.severity == SeverityLevel.CRITICAL)
        high = sum(1 for w in weaknesses if w.severity == SeverityLevel.HIGH)
        medium = sum(1 for w in weaknesses if w.severity == SeverityLevel.MEDIUM)
        low = sum(1 for w in weaknesses if w.severity == SeverityLevel.LOW)

        severity_scores = [self._severity_to_priority(w.severity) for w in weaknesses]
        risk_score = (sum(severity_scores) / (len(severity_scores) * 5) * 100) if severity_scores else 0

        priority_areas = [w.subject for w in sorted_weaknesses if w.priority >= 4][:5]
        key_insights = self._generate_insights(weaknesses, analysis_basis)

        avg_gap = np.mean([w.gap_percentage for w in weaknesses]) if weaknesses else 0
        improvement_potential = min(avg_gap * 0.7, 100)

        # Add performance prediction insight if available
        if student_data and _PERF_AVAILABLE:
            pred = self._get_performance_prediction(student_data)
            if pred:
                key_insights.append(
                    f"📈 ML predicts next semester SGPA: {pred['predicted_sgpa']:.2f} "
                    f"({pred['risk_category']} risk, {pred['model_used']} model)"
                )

        all_resources = []
        if include_resources:
            for w in sorted_weaknesses[:5]:
                all_resources.extend(w.recommended_resources)

        study_plan = None
        if include_study_plan:
            study_plan = self._generate_study_plan(sorted_weaknesses[:5])

        model_info = "ML-powered" if self._ml_available else "ML with rule fallback"
        key_insights.append(f"Analysis method: {model_info}")

        return WeaknessAnalysisResponse(
            student_id=student_id, analysis_basis=analysis_basis,
            weaknesses=sorted_weaknesses, overall_risk_score=round(risk_score, 2),
            priority_areas=priority_areas, recommended_resources=all_resources[:10],
            study_plan=study_plan, total_weaknesses=len(weaknesses),
            critical_count=critical, high_count=high, medium_count=medium, low_count=low,
            key_insights=key_insights, improvement_potential=round(improvement_potential, 2),
        )

    # ═══════════════════════════════════════════════════════════
    #  SUGGESTION GENERATION (same as original)
    # ═══════════════════════════════════════════════════════════

    def _get_improvement_suggestions(self, subject: str, severity: SeverityLevel) -> List[str]:
        base = {
            SeverityLevel.CRITICAL: [
                f"URGENT: Schedule immediate tutoring for {subject}",
                f"Dedicate 2+ hours daily to {subject}",
                f"Meet with {subject} professor during office hours",
                "Join/form a study group",
            ],
            SeverityLevel.HIGH: [
                f"Prioritize {subject} in your study schedule",
                "Practice with previous year papers",
                "Use online resources (NPTEL, Coursera)",
            ],
            SeverityLevel.MEDIUM: [
                f"Regular revision of {subject} concepts",
                "Solve additional practice problems",
                "Attend doubt-clearing sessions",
            ],
            SeverityLevel.LOW: [
                f"Maintain current pace for {subject}",
                "Target advanced topics",
            ],
        }
        return base.get(severity, base[SeverityLevel.MEDIUM])

    def _get_resources(self, subject: str, severity: SeverityLevel) -> List[Dict[str, Any]]:
        q = subject.replace(" ", "+")
        return [
            {"type": "course", "platform": "NPTEL", "title": f"{subject} - IIT Course",
             "url": "https://nptel.ac.in/courses"},
            {"type": "video", "platform": "YouTube", "title": f"Learn {subject}",
             "url": f"https://youtube.com/results?search_query={q}+tutorial"},
            {"type": "practice", "platform": "GeeksforGeeks",
             "title": f"{subject} Practice", "url": f"https://www.geeksforgeeks.org/{q.lower().replace('+', '-')}"},
        ]

    def _estimate_improvement_time(self, gap: float, severity: SeverityLevel) -> str:
        if severity == SeverityLevel.CRITICAL: return "8-12 weeks intensive"
        elif severity == SeverityLevel.HIGH: return "6-8 weeks consistent"
        elif severity == SeverityLevel.MEDIUM: return "4-6 weeks regular"
        else: return "2-4 weeks focused"

    def _generate_insights(self, weaknesses: List[WeaknessArea], basis: AnalysisBasis) -> List[str]:
        insights = []
        critical = [w.subject for w in weaknesses if w.severity == SeverityLevel.CRITICAL]
        if critical:
            insights.append(f"🔴 Critical attention: {', '.join(critical[:3])}")
        high = [w.subject for w in weaknesses if w.severity == SeverityLevel.HIGH]
        if high:
            insights.append(f"🟠 High priority: {', '.join(high[:3])}")
        if basis == AnalysisBasis.INTEREST:
            gaps = [w for w in weaknesses if w.impact_on_interest]
            if gaps: insights.append(f"Your interests require strengthening {len(gaps)} areas")
        if basis == AnalysisBasis.ELECTIVES:
            gaps = [w for w in weaknesses if w.impact_on_elective]
            if gaps: insights.append(f"{len(gaps)} elective prerequisites need improvement")
        if not weaknesses:
            insights.append("✅ No significant weaknesses detected!")
        elif len(weaknesses) <= 2:
            insights.append("Good performance — minor improvements needed")
        elif len(weaknesses) <= 5:
            insights.append("Moderate improvement opportunities — focus on priority areas")
        else:
            insights.append("Multiple areas need attention — follow the study plan")
        return insights

    def _generate_study_plan(self, priority_weaknesses: List[WeaknessArea]) -> Dict[str, Any]:
        plan = {"duration": "8 weeks", "weekly_hours": 15, "phases": [], "milestones": []}
        phase1 = [w.subject for w in priority_weaknesses
                   if w.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]][:2]
        plan["phases"].append({"name": "Foundation Building", "weeks": "1-2",
                                "focus": phase1 or ["Core concepts review"],
                                "goals": ["Master fundamentals", "Complete basic exercises"]})
        plan["phases"].append({"name": "Active Practice", "weeks": "3-5",
                                "focus": [w.subject for w in priority_weaknesses[:3]],
                                "goals": ["Solve practice problems", "Work on assignments"]})
        plan["phases"].append({"name": "Mastery & Review", "weeks": "6-8",
                                "focus": [w.subject for w in priority_weaknesses],
                                "goals": ["Mock tests", "Advanced problems", "Final revision"]})
        plan["milestones"] = [
            {"week": 2, "target": "Complete fundamentals review"},
            {"week": 4, "target": "Score 60%+ in practice tests"},
            {"week": 6, "target": "Score 70%+ in practice tests"},
            {"week": 8, "target": "Achieve target proficiency"},
        ]
        return plan

    # ═══════════════════════════════════════════════════════════
    #  PERSISTENCE (unchanged)
    # ═══════════════════════════════════════════════════════════

    async def _save_analysis_result(self, response, interests, electives, honours_minors):
        try:
            await WeaknessAnalysisResult.find(
                WeaknessAnalysisResult.student_id == response.student_id,
                WeaknessAnalysisResult.is_current == True
            ).update({"$set": {"is_current": False}})

            result = WeaknessAnalysisResult(
                student_id=response.student_id,
                analysis_basis=response.analysis_basis.value,
                overall_score=100 - response.overall_risk_score,
                overall_risk_score=response.overall_risk_score,
                weaknesses=[w.dict() for w in response.weaknesses],
                priority_areas=response.priority_areas,
                ai_analysis={
                    "total_weaknesses": response.total_weaknesses,
                    "critical_count": response.critical_count,
                    "high_count": response.high_count,
                    "medium_count": response.medium_count,
                    "low_count": response.low_count,
                    "ml_powered": self._ml_available,
                },
                study_plan=response.study_plan or {},
                key_insights=response.key_insights,
                recommended_resources=response.recommended_resources,
                related_interests=interests or [],
                related_electives=electives or [],
                related_honours=honours_minors or [],
                is_current=True,
            )
            await result.save()
        except Exception as e:
            self.logger.error(f"Error saving analysis: {e}")

    async def get_latest_analysis(self, student_id: str) -> Optional[WeaknessAnalysisResult]:
        try:
            return await WeaknessAnalysisResult.find_one(
                WeaknessAnalysisResult.student_id == student_id,
                WeaknessAnalysisResult.is_current == True
            )
        except Exception as e:
            self.logger.error(f"Error fetching latest analysis: {e}")
            return None

    async def get_analysis_history(self, student_id: str, limit: int = 10):
        try:
            return await WeaknessAnalysisResult.find(
                WeaknessAnalysisResult.student_id == student_id
            ).sort(-WeaknessAnalysisResult.analysis_date).limit(limit).to_list()
        except Exception as e:
            self.logger.error(f"Error fetching history: {e}")
            return []

    async def sync_interests_from_all_sources(self, student_id: str) -> Dict[str, Any]:
        """Sync interests from all DB sources to StudentInterestProfile."""
        result = {"student_id": student_id, "sources_checked": [], "interests_found": [],
                  "synced": False, "source": None}
        try:
            from app.models.student_profile import StudentProfile
            from app.models.student import StudentPerformance

            ip = await StudentInterestProfile.find_one(StudentInterestProfile.user_id == student_id)
            result["sources_checked"].append("StudentInterestProfile")
            if ip and ip.interests:
                result["interests_found"] = ip.interests
                result["source"] = "StudentInterestProfile"
                return result

            profile = await StudentProfile.find_one(StudentProfile.user_id == student_id)
            result["sources_checked"].append("StudentProfile")
            if profile and profile.interests:
                await StudentInterestProfile(user_id=student_id, interests=profile.interests,
                                              career_goals=profile.career_goals or []).save()
                result.update({"interests_found": profile.interests, "source": "StudentProfile", "synced": True})
                return result

            perf = await StudentPerformance.find_one(StudentPerformance.student_info.uid == student_id)
            result["sources_checked"].append("StudentPerformance")
            if perf and perf.interests:
                await StudentInterestProfile(user_id=student_id, interests=perf.interests).save()
                result.update({"interests_found": perf.interests, "source": "StudentPerformance", "synced": True})
                return result

            return result
        except Exception as e:
            result["error"] = str(e)
            return result


# ═══════════════════════════════════════════════════════════
#  SINGLETON
# ═══════════════════════════════════════════════════════════

_weakness_service: Optional[WeaknessAnalysisService] = None

def get_weakness_analysis_service() -> WeaknessAnalysisService:
    global _weakness_service
    if _weakness_service is None:
        _weakness_service = WeaknessAnalysisService()
    return _weakness_service