# app/models/readiness.py
"""
Readiness & Dynamic Subject Requirement Models
"""

from beanie import Document
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


# ══════════════════════════════════════════════════════════════
#  ENUMS
# ══════════════════════════════════════════════════════════════

class ReadinessLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    LOW = "low"
    NOT_READY = "not_ready"


class RecommendationType(str, Enum):
    PROCEED = "proceed"
    PROCEED_WITH_CAUTION = "proceed_with_caution"
    IMPROVE_FIRST = "improve_first"
    DO_NOT_PROCEED = "do_not_proceed"


class GoalType(str, Enum):
    INTEREST = "interest"
    ELECTIVE = "elective"
    HONOURS = "honours"


# ══════════════════════════════════════════════════════════════
#  EMBEDDED MODELS
# ══════════════════════════════════════════════════════════════

class RequiredSubject(BaseModel):
    """One prerequisite subject inside a requirement map."""
    subject_name: str
    subject_code: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    importance: float = Field(default=0.5, ge=0, le=1.0)
    importance_label: str = "Medium"
    min_score: float = Field(default=60, ge=0, le=100)
    weight: float = Field(default=1.0, ge=0)


class MatchedSubject(BaseModel):
    """
    A required subject after matching against the student's
    actual academic records.
    """
    subject_name: str
    subject_code: Optional[str] = None
    importance: float = 0.5
    importance_label: str = "Medium"
    min_score: float = 60
    weight: float = 1.0

    # Credits from the student's actual SubjectScore record
    # Default 3 is used when no match is found
    credits: int = 3

    linked_goals: List[str] = Field(default_factory=list)
    goal_types: List[str] = Field(default_factory=list)

    # Filled during Step 2 (match_performance)
    student_score: Optional[float] = None
    is_taken: bool = False
    confidence: float = 0.0

    # Filled during Steps 3–4
    gap: float = 0.0
    is_weakness: bool = False
    severity: str = "low"

    # Confidence flag — separate from severity
    # True when match confidence < 0.7 (partial or word-overlap match)
    low_confidence_flag: bool = False


class WeaknessEntry(BaseModel):
    """
    Final weakness record sent to API consumers and the study-plan generator.

    estimated_hours: total hours to close the gap (not per-week).
    Formula: gap × credits × 0.1 × multipliers
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str
    current_score: float = 0
    target_score: float = 60
    gap: float = 0
    severity: str = "low"
    importance: float = 0.5
    importance_label: str = "Medium"
    confidence: float = 0.8
    low_confidence_flag: bool = False

    # Credits carried through from SubjectScore for accurate hour estimation
    credits: int = 3

    linked_goals: List[str] = Field(default_factory=list)
    goal_types: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    resources: List[Dict[str, Any]] = Field(default_factory=list)

    # Total hours needed to close this gap (study plan divides by weeks)
    estimated_hours: float = 10.0

    priority_rank: int = 0


# ══════════════════════════════════════════════════════════════
#  EFFORT MODELS
# ══════════════════════════════════════════════════════════════

class SubjectStudyEstimate(BaseModel):
    """
    Per-subject effort estimate.

    coverage_ratio         : min(score/min_score, 1.0) — how much is met
    study_hours_to_close_gap: total hours needed (gap × credits × 0.1 × mults)
    """
    subject_name: str
    subject_code: Optional[str] = None
    credits: int = 3
    current_score: float = 0.0
    required_min: float = 60.0
    is_backlog: bool = False
    is_taken: bool = False
    semester: int = 1

    gap_to_target: float = 0.0
    coverage_ratio: float = 0.0
    study_hours_to_close_gap: float = 0.0


class EffortReadinessResult(BaseModel):
    """
    Effort-readiness block embedded in the full readiness response.

    effort_readiness_score:
        Credit-weighted coverage ratio × 100 (0–100).
        Higher = more requirements already satisfied.
        Capped at 60 if any subject is below passing grade (40%).

    estimated_study_load_weekly:
        Named for API compatibility. Actually stores TOTAL gap hours
        (not per-week). Study plan divides by duration_weeks.
    """
    effort_readiness_score: float = 0.0
    estimated_study_load_weekly: float = 0.0
    total_required_min_hours: float = 0.0
    has_backlog: bool = False
    study_load_warning: Optional[str] = None
    per_subject_estimates: List[SubjectStudyEstimate] = Field(
        default_factory=list
    )


# ══════════════════════════════════════════════════════════════
#  MONGODB DOCUMENTS
# ══════════════════════════════════════════════════════════════

class SubjectRequirementMap(Document):
    """
    Stores which subjects are needed for a specific goal.
    The readiness engine reads ONLY from this collection.
    Zero hard-coding in the engine.
    """
    target_type: str = Field(...)
    target_name: str = Field(...)
    target_aliases: List[str] = Field(default_factory=list)
    target_code: Optional[str] = None
    required_subjects: List[RequiredSubject] = Field(default_factory=list)
    min_cgpa: Optional[float] = None
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "subject_requirement_maps"
        indexes = ["target_type", "target_name", "is_active"]


class ReadinessResult(Document):
    """Persisted readiness analysis for a student."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str = Field(..., index=True)

    overall_readiness_score: float = 0
    readiness_level: str = "not_ready"
    recommendation_type: str = "improve_first"
    primary_recommendation: str = ""

    interest_readiness: float = 0
    elective_readiness: float = 0
    honours_readiness: float = 0

    interest_breakdown: Dict[str, float] = Field(default_factory=dict)
    elective_breakdown: Dict[str, float] = Field(default_factory=dict)
    honours_breakdown: Dict[str, float] = Field(default_factory=dict)

    weaknesses: List[Dict[str, Any]] = Field(default_factory=list)
    study_plan: Dict[str, Any] = Field(default_factory=dict)

    has_critical_weakness: bool = False
    has_blockers: bool = False
    is_first_semester: bool = False

    subjects_to_focus: List[str] = Field(default_factory=list)
    estimated_preparation_time: str = ""
    detailed_recommendations: List[str] = Field(default_factory=list)

    interests_analyzed: List[str] = Field(default_factory=list)
    electives_analyzed: List[str] = Field(default_factory=list)
    honours_analyzed: List[str] = Field(default_factory=list)

    # Effort fields
    effort_readiness_score: float = 0.0
    total_gap_hours: float = 0.0
    study_load_warning: Optional[str] = None

    is_current: bool = True
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "readiness_results"
        indexes = ["student_id", "is_current"]


# ══════════════════════════════════════════════════════════════
#  API RESPONSE SCHEMAS
# ══════════════════════════════════════════════════════════════

class PrerequisiteDetail(BaseModel):
    """Detailed prerequisite status for a single subject."""
    subject_name: str
    subject_code: Optional[str] = None
    current_score: float = 0
    required_score: float = 60
    gap: float = 0
    coverage_ratio: float = 0.0
    importance: float = 0.5
    importance_label: str = "Medium"
    status: str = "missing"
    is_taken: bool = False
    confidence: float = 0.0
    low_confidence_flag: bool = False


class ReadinessResponse(BaseModel):
    student_id: str

    # Core scores
    overall_readiness_score: float = 0
    readiness_level: str = "not_ready"
    recommendation_type: str = "improve_first"
    primary_recommendation: str = ""

    # Category scores
    interest_readiness: float = 0
    elective_readiness: float = 0
    honours_readiness: float = 0

    interest_breakdown: Dict[str, float] = Field(default_factory=dict)
    elective_breakdown: Dict[str, float] = Field(default_factory=dict)
    honours_breakdown: Dict[str, float] = Field(default_factory=dict)

    # Flags
    has_critical_weakness: bool = False
    has_blockers: bool = False
    is_first_semester: bool = False

    # Focus + timing
    subjects_to_focus: List[str] = Field(default_factory=list)
    estimated_preparation_time: str = ""
    detailed_recommendations: List[str] = Field(default_factory=list)

    # Weaknesses + study plan
    weaknesses: List[Dict[str, Any]] = Field(default_factory=list)
    study_plan: Dict[str, Any] = Field(default_factory=dict)

    # Effort fields (new)
    effort_readiness_score: float = 0.0
    total_gap_hours: float = 0.0
    study_load_warning: Optional[str] = None
    effort_detail: Optional[Dict[str, Any]] = None

    analysis_timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


class ReadinessSummaryResponse(BaseModel):
    student_id: str
    overall_readiness: float = 0
    level: str = "not_ready"
    can_proceed: bool = False
    critical_issues: bool = False
    primary_action: str = ""
    timestamp: str = ""


class ElectiveReadinessResponse(BaseModel):
    student_id: str
    elective: str
    elective_code: Optional[str] = None
    readiness_score: float = 0
    readiness_level: str = "not_ready"
    is_ready: bool = False
    recommendation: str = ""
    prerequisites: List[PrerequisiteDetail] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    subjects_to_focus: List[str] = Field(default_factory=list)
    preparation_plan: List[str] = Field(default_factory=list)
    preparation_time: str = ""
    estimated_preparation_weeks: int = 0


class HonoursReadinessResponse(BaseModel):
    student_id: str
    programme: str
    readiness_score: float = 0
    is_eligible: bool = False
    recommendation: str = ""
    blockers: List[str] = Field(default_factory=list)
    preparation_time: str = ""
    detailed_steps: List[str] = Field(default_factory=list)


class ReadinessRequest(BaseModel):
    student_id: str
    interests: Optional[List[str]] = None
    electives: Optional[List[str]] = None
    honours_minors: Optional[List[str]] = None