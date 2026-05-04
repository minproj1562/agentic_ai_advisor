# app/services/effort_calculator.py
"""
Effort-Based Readiness Calculator
====================================
Derives study effort from marks and credits only.
No attendance, LMS, or self-reported data assumed.

Effort score = credit-weighted coverage ratio (NOT hour ratio).
Higher score = more subjects already meeting requirements.

Study hours = gap × credits × 0.1 × multipliers
"""

import logging
from typing import Dict, List, Optional, Any

from app.models.readiness import SubjectStudyEstimate, EffortReadinessResult
from app.core.readiness_config import (
    PASSING_SCORE,
    EFFORT_CAP_WITH_BACKLOG,
    HOURS_PER_MARK_PER_CREDIT,
    BACKLOG_HOURS_MULTIPLIER,
    SENIOR_HOURS_MULTIPLIER,
    MAX_HOURS_PER_CREDIT,
    MIN_HOURS_PER_CREDIT,
    ACADEMIC_WEIGHT_DEFAULT,
    ACADEMIC_WEIGHT_FIRST_SEM,
    EFFORT_WEIGHT_DEFAULT,
    EFFORT_WEIGHT_FIRST_SEM,
    HEAVY_STUDY_WARNING_TOTAL,
    MODERATE_STUDY_WARNING_TOTAL,
    SEMESTER_MULTIPLIERS,
)

logger = logging.getLogger(__name__)


class EffortCalculator:
    """
    Stateless calculator.
    All methods are pure functions — no DB access, no side effects.
    """

    # ════════════════════════════════════════════════════════════
    #  PUBLIC API
    # ════════════════════════════════════════════════════════════

    def compute(
        self,
        *,
        subject_scores: Dict[str, Dict[str, Any]],
        required_subjects: List[Dict[str, Any]],
        semester: int,
        is_first_semester: bool,
    ) -> EffortReadinessResult:
        """
        Compute effort readiness from marks and credits only.

        Effort score = Σ(coverage_ratio × credits) / Σ(credits) × 100

        coverage_ratio per subject:
            = min(student_score / min_score, 1.0)  if taken
            = 0.0                                   if not taken (later sem)
            = excluded                              if not taken (first sem)

        Parameters
        ----------
        subject_scores    : {name: {score, credits, code, grade}}
                            from _load_student_scores()
        required_subjects : [{subject_name, min_score, importance}]
                            from merged target profile
        semester          : student's current semester (1–8)
        is_first_semester : True when completed_semesters <= 1
        """
        estimates: List[SubjectStudyEstimate] = []
        has_backlog = False

        coverage_numerator = 0.0
        coverage_denominator = 0.0
        total_study_hours = 0.0

        for req in required_subjects:
            subject_name = req.get("subject_name", "Unknown")
            required_min = float(req.get("min_score", 60.0))

            student_data = self._match_subject(subject_scores, subject_name)

            if student_data:
                current_score = float(student_data.get("score", 0.0))
                credits = int(student_data.get("credits") or 3)
                is_taken = True
                is_backlog_subject = (
                    current_score < PASSING_SCORE
                )
            else:
                current_score = 0.0
                credits = 3
                is_taken = False
                # Only flag backlog if student should have taken it
                is_backlog_subject = not is_first_semester

            if is_backlog_subject:
                has_backlog = True

            # ── Coverage ratio ────────────────────────────────
            if is_taken:
                coverage_ratio = (
                    min(current_score / required_min, 1.0)
                    if required_min > 0
                    else 1.0
                )
                coverage_numerator += coverage_ratio * credits
                coverage_denominator += credits
            elif is_first_semester:
                # Not yet available — exclude from calculation
                coverage_ratio = 0.0
            else:
                # Should have been taken — zero coverage
                coverage_ratio = 0.0
                coverage_numerator += 0.0
                coverage_denominator += credits

            # ── Gap and study hours ───────────────────────────
            if is_taken:
                gap = max(0.0, required_min - current_score)
            elif is_first_semester:
                gap = 0.0
            else:
                gap = required_min

            hours = self._compute_study_hours(
                gap=gap,
                credits=credits,
                is_backlog=is_backlog_subject,
                semester=semester,
            )
            total_study_hours += hours

            estimates.append(SubjectStudyEstimate(
                subject_name=subject_name,
                subject_code=req.get("subject_code"),
                credits=credits,
                current_score=round(current_score, 1),
                required_min=required_min,
                is_backlog=is_backlog_subject,
                is_taken=is_taken,
                semester=semester,
                gap_to_target=round(gap, 1),
                coverage_ratio=round(coverage_ratio, 3),
                study_hours_to_close_gap=round(hours, 1),
            ))

        # ── Effort score ──────────────────────────────────────
        if coverage_denominator > 0:
            raw_effort = (
                coverage_numerator / coverage_denominator
            ) * 100.0
        else:
            # All subjects excluded (pure first-semester case)
            raw_effort = 100.0

        if has_backlog:
            raw_effort = min(raw_effort, EFFORT_CAP_WITH_BACKLOG)

        effort_score = round(max(0.0, min(100.0, raw_effort)), 1)

        warning = self._build_warning(
            total_study_hours=total_study_hours,
            has_backlog=has_backlog,
        )

        return EffortReadinessResult(
            effort_readiness_score=effort_score,
            estimated_study_load_weekly=round(total_study_hours, 1),
            total_required_min_hours=round(coverage_denominator * 2.0, 1),
            has_backlog=has_backlog,
            study_load_warning=warning,
            per_subject_estimates=estimates,
        )

    def blend_scores(
        self,
        *,
        academic_readiness: float,
        effort_readiness: float,
        is_first_semester: bool,
    ) -> float:
        """
        Blend academic and effort scores into overall readiness.

        Weights (both on 0–100 scale, sum to 1.0):
          Normal:         0.80 academic + 0.20 effort
          First semester: 0.90 academic + 0.10 effort
        """
        if is_first_semester:
            a_w = ACADEMIC_WEIGHT_FIRST_SEM
            e_w = EFFORT_WEIGHT_FIRST_SEM
        else:
            a_w = ACADEMIC_WEIGHT_DEFAULT
            e_w = EFFORT_WEIGHT_DEFAULT

        blended = (academic_readiness * a_w) + (effort_readiness * e_w)
        return round(min(100.0, max(0.0, blended)), 1)

    # ════════════════════════════════════════════════════════════
    #  PRIVATE: STUDY HOURS
    # ════════════════════════════════════════════════════════════

    @staticmethod
    def _compute_study_hours(
        *,
        gap: float,
        credits: int,
        is_backlog: bool,
        semester: int,
    ) -> float:
        """
        Estimate total hours to close a score gap.

        Formula
        -------
        base_hours = gap × credits × 0.1

        Multipliers:
            backlog  (score < 40): × 1.5
            semester >= 5:         × 1.2

        Bounds: [credits × 1, credits × 20]

        Examples
        --------
        gap=20, credits=3, normal, sem=3:
            base = 20 × 3 × 0.1 = 6 hrs ✓

        gap=40, credits=4, backlog, sem=6:
            base = 40 × 4 × 0.1 = 16
            × 1.5 × 1.2 = 28.8 hrs ✓

        gap=0: returns 0.0 ✓
        """
        if gap <= 0:
            return 0.0

        base_hours = gap * credits * HOURS_PER_MARK_PER_CREDIT

        multiplier = 1.0
        if is_backlog:
            multiplier *= BACKLOG_HOURS_MULTIPLIER
        multiplier *= SEMESTER_MULTIPLIERS.get(semester, 1.0)

        hours = base_hours * multiplier

        min_hours = float(credits * MIN_HOURS_PER_CREDIT)
        max_hours = float(credits * MAX_HOURS_PER_CREDIT)

        return max(min_hours, min(max_hours, hours))

    # ════════════════════════════════════════════════════════════
    #  PRIVATE: WARNING
    # ════════════════════════════════════════════════════════════

    @staticmethod
    def _build_warning(
        *,
        total_study_hours: float,
        has_backlog: bool,
    ) -> Optional[str]:
        """
        Return a warning string or None.

        Thresholds are on TOTAL hours (not per-week).
        Study plan converts total to weekly via duration.
        """
        if total_study_hours > HEAVY_STUDY_WARNING_TOTAL:
            return (
                f"High remediation load detected "
                f"({total_study_hours:.0f} total hours estimated). "
                "Consider reducing elective count or spreading "
                "preparation over multiple semesters."
            )
        if total_study_hours > MODERATE_STUDY_WARNING_TOTAL:
            return (
                f"Moderate study load ahead "
                f"({total_study_hours:.0f} total hours estimated). "
                "Plan your weekly schedule carefully."
            )
        if has_backlog:
            return (
                "One or more subjects are below passing grade (40%). "
                "Clear all backlogs before adding new electives or honours."
            )
        return None

    # ════════════════════════════════════════════════════════════
    #  PRIVATE: SUBJECT MATCHING
    # ════════════════════════════════════════════════════════════

    @staticmethod
    def _match_subject(
        subject_scores: Dict[str, Dict[str, Any]],
        target: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Find student record for a required subject.

        Three-pass matching:
        1. Exact name (case-insensitive)
        2. Substring (target in name, or name in target)
        3. Word overlap (≥2 words, or 1 if target is single word)
        """
        target_lower = target.lower().strip()
        target_words = set(target_lower.split())

        for name, data in subject_scores.items():
            if name.lower().strip() == target_lower:
                return data

        for name, data in subject_scores.items():
            nl = name.lower().strip()
            if target_lower in nl or nl in target_lower:
                return data

        for name, data in subject_scores.items():
            name_words = set(name.lower().split())
            overlap = target_words & name_words
            if len(overlap) >= 2 or (
                len(overlap) >= 1 and len(target_words) == 1
            ):
                return data

        return None


# ════════════════════════════════════════════════════════════════
#  SINGLETON
# ════════════════════════════════════════════════════════════════

_instance: Optional[EffortCalculator] = None


def get_effort_calculator() -> EffortCalculator:
    global _instance
    if _instance is None:
        _instance = EffortCalculator()
    return _instance