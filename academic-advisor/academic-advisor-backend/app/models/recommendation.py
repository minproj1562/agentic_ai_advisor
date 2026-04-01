# app/models/recommendation.py
"""
Recommendation data models for MongoDB (Beanie Documents)
Stores recommendation history and user feedback for model fine-tuning
"""

from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class RecommendationType(str, Enum):
    ELECTIVE = "elective"
    OPEN_ELECTIVE = "open_elective"
    HONOURS = "honours"
    MINOR = "minor"
    CAREER = "career"


class RecommendationBasis(BaseModel):
    marks_score: float = 0.0
    interest_score: float = 0.0
    project_score: float = 0.0
    semantic_score: float = 0.0
    ml_model_score: float = 0.0
    rule_based_score: float = 0.0
    marks_weight: float = 0.40
    interest_weight: float = 0.30
    project_weight: float = 0.30


class ElectiveDetail(BaseModel):
    elective_code: str
    elective_name: str
    credits: int = 3
    match_score: float
    match_explanation: str = ""
    prerequisites_met: bool = True
    skill_alignment: List[str] = Field(default_factory=list)
    career_relevance: List[str] = Field(default_factory=list)
    recommendation_basis: Dict[str, float] = Field(default_factory=dict)
    skill_gaps: List[Dict[str, Any]] = Field(default_factory=list)
    pair: Optional[str] = None
    score_breakdown: Optional[Dict[str, Any]] = None
    ranking_explanation: Optional[Dict[str, Any]] = None
    confidence: Optional[Dict[str, Any]] = None


class OpenElectiveDetail(BaseModel):
    """Detail model for Semester-VII Open Elective recommendations."""
    elective_code: str
    elective_name: str
    credits: int = 3
    semester: int = 7
    category: str = "Open Elective"
    match_score: float
    match_explanation: str = ""
    prerequisites_met: bool = True
    skill_alignment: List[str] = Field(default_factory=list)
    career_relevance: List[str] = Field(default_factory=list)
    modules: List[str] = Field(default_factory=list)
    recommendation_basis: Dict[str, float] = Field(default_factory=dict)
    skill_gaps: List[Dict[str, Any]] = Field(default_factory=list)
    score_breakdown: Optional[Dict[str, Any]] = None
    ranking_explanation: Optional[Dict[str, Any]] = None
    confidence: Optional[Dict[str, Any]] = None


class HonoursDetail(BaseModel):
    program: str
    type: str
    match_score: float
    eligibility: bool
    required_cgpa: float
    career_paths: List[str] = Field(default_factory=list)
    explanation: str = ""
    skills_gained: List[str] = Field(default_factory=list)
    score_breakdown: Optional[Dict[str, Any]] = None


class CareerDetail(BaseModel):
    career: str
    match_score: float
    cgpa_eligible: bool
    required_cgpa: float
    salary_range: str = ""
    growth_potential: str = ""
    top_companies: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    preparation_path: List[str] = Field(default_factory=list)
    required_certifications: List[str] = Field(default_factory=list)
    score_breakdown: Optional[Dict[str, Any]] = None


class RecommendationRecord(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: Indexed(str)

    input_marks: Dict[str, float] = Field(default_factory=dict)
    input_interests: List[str] = Field(default_factory=list)
    input_project_count: int = 0
    cgpa: float = 0.0
    semester: int = 4

    electives: List[ElectiveDetail] = Field(default_factory=list)
    open_electives: List[OpenElectiveDetail] = Field(default_factory=list)
    honours: List[HonoursDetail] = Field(default_factory=list)
    careers: List[CareerDetail] = Field(default_factory=list)

    model_version: str = "3.0.0"
    models_used: List[str] = Field(default_factory=list)
    computation_time_ms: float = 0.0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Settings:
        name = "recommendation_records"
        indexes = ["student_id", "created_at"]


class RecommendationFeedback(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: Indexed(str)
    recommendation_type: RecommendationType
    recommendation_id: str
    item_name: str = ""

    rating: int = Field(ge=1, le=5)
    feedback_text: str = ""
    was_followed: Optional[bool] = None

    student_cgpa: float = 0.0
    student_semester: int = 4
    student_marks: Dict[str, float] = Field(default_factory=dict)
    student_interests: List[str] = Field(default_factory=list)
    student_project_skills: List[str] = Field(default_factory=list)
    student_project_count: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "recommendation_feedback"
        indexes = ["student_id", "recommendation_type", "created_at", "rating"]


class TrainingDataPoint(Document):
    student_features: List[float] = Field(default_factory=list)
    marks: Dict[str, float] = Field(default_factory=dict)
    interests: Dict[str, float] = Field(default_factory=dict)
    project_skills: List[str] = Field(default_factory=list)
    label: str = ""
    label_type: str = "program_elective"  # "program_elective" or "open_elective"
    source: str = "synthetic"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "training_data"