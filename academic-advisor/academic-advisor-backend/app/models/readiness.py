#academic-advisor-backend/app/models/readiness.py
"""
Readiness & Dynamic Subject Requirement Models
All requirement maps are stored in MongoDB — nothing hardcoded in the engine.
"""

from beanie import Document
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


# ─── Enums ───────────────────────────────────────────────────────

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


# ─── Embedded Models ─────────────────────────────────────────────

class RequiredSubject(BaseModel):
    """One prerequisite / foundational subject inside a requirement map."""
    subject_name: str
    subject_code: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    importance: float = Field(default=0.5, ge=0, le=1.0)
    importance_label: str = "Medium"          # Critical / High / Medium / Low
    min_score: float = Field(default=60, ge=0, le=100)
    weight: float = Field(default=1.0, ge=0)


class MatchedSubject(BaseModel):
    """A required subject after matching it with the student's actual score."""
    subject_name: str
    subject_code: Optional[str] = None
    importance: float = 0.5
    importance_label: str = "Medium"
    min_score: float = 60
    weight: float = 1.0
    linked_goals: List[str] = Field(default_factory=list)
    goal_types: List[str] = Field(default_factory=list)

    # Filled during Step 2
    student_score: Optional[float] = None
    is_taken: bool = False
    confidence: float = 0.0

    # Filled during Steps 3–4
    gap: float = 0.0
    is_weakness: bool = False
    severity: str = "low"


class WeaknessEntry(BaseModel):
    """Final weakness record exposed to the API / study-plan generator."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str
    current_score: float = 0
    target_score: float = 60
    gap: float = 0
    severity: str = "low"
    importance: float = 0.5
    importance_label: str = "Medium"
    confidence: float = 0.8
    linked_goals: List[str] = Field(default_factory=list)
    goal_types: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    resources: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_hours: int = 10
    priority_rank: int = 0


# ─── MongoDB Document: Requirement Map ──────────────────────────

class SubjectRequirementMap(Document):
    """
    Stores which subjects are needed for a specific interest / elective / honours.
    The readiness engine reads *only* from this collection — zero hard-coding.
    """
    target_type: str = Field(...)                # interest | elective | honours
    target_name: str = Field(...)                # e.g. "Machine Learning"
    target_aliases: List[str] = Field(default_factory=list)   # ["ML", "ml"]
    target_code: Optional[str] = None            # e.g. "ITPEC5012"
    required_subjects: List[RequiredSubject] = Field(default_factory=list)
    min_cgpa: Optional[float] = None
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "subject_requirement_maps"
        indexes = [
            "target_type",
            "target_name",
            "is_active",
        ]


# ─── MongoDB Document: Persisted Readiness Result ───────────────

class ReadinessResult(Document):
    """Persisted readiness analysis for a student (for history / caching)."""
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

    is_current: bool = True
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "readiness_results"
        indexes = ["student_id", "is_current"]


# ─── API Response Schemas (Pydantic, *not* Documents) ────────────

class ReadinessResponse(BaseModel):
    student_id: str
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

    has_critical_weakness: bool = False
    has_blockers: bool = False
    is_first_semester: bool = False

    subjects_to_focus: List[str] = Field(default_factory=list)
    estimated_preparation_time: str = ""
    detailed_recommendations: List[str] = Field(default_factory=list)

    weaknesses: List[Dict[str, Any]] = Field(default_factory=list)
    study_plan: Dict[str, Any] = Field(default_factory=dict)

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
    readiness_score: float = 0
    is_ready: bool = False
    recommendation: str = ""
    subjects_to_focus: List[str] = Field(default_factory=list)
    preparation_time: str = ""


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