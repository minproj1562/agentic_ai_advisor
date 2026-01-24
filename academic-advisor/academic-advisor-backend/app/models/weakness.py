# app/models/weakness.py
from typing import List, Dict, Any, Optional
from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid


class AnalysisBasis(str, Enum):
    """Basis for weakness analysis"""
    INTEREST = "interest"
    ELECTIVES = "electives"
    HONOURS_MINORS = "honours_minors"
    PERFORMANCE = "performance"
    COMBINED = "combined"


class SeverityLevel(str, Enum):
    """Severity levels for weaknesses"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WeaknessTopic(BaseModel):
    """Individual topic weakness"""
    topic_name: str
    score: float = Field(..., ge=0, le=100)
    weight: float = Field(default=0.5, ge=0, le=1)
    weakness_level: SeverityLevel = SeverityLevel.LOW
    improvement_suggestions: List[str] = Field(default_factory=list)
    recommended_resources: List[Dict[str, str]] = Field(default_factory=list)
    practice_exercises: List[str] = Field(default_factory=list)
    estimated_hours_to_improve: int = 10


class WeaknessArea(BaseModel):
    """A weakness area identified through analysis"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str
    topic: Optional[str] = None
    current_score: float = Field(default=0, ge=0, le=100)
    target_score: float = Field(default=70, ge=0, le=100)
    gap_percentage: float = Field(default=0, ge=0, le=100)
    severity: SeverityLevel = SeverityLevel.LOW
    confidence: float = Field(default=0.8, ge=0, le=1)
    
    # What this weakness relates to
    related_to: str = ""  # e.g., "Machine Learning interest", "Cloud Computing elective"
    analysis_basis: AnalysisBasis = AnalysisBasis.PERFORMANCE
    
    # Improvement data
    improvement_suggestions: List[str] = Field(default_factory=list)
    recommended_resources: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_improvement_time: str = "2-4 weeks"
    priority: int = Field(default=1, ge=1, le=5)
    
    # Impact assessment
    impact_on_interest: Optional[str] = None
    impact_on_elective: Optional[str] = None
    impact_on_career: Optional[str] = None


class WeaknessAnalysisRequest(BaseModel):
    """Request model for weakness analysis"""
    student_id: str
    analysis_basis: AnalysisBasis = AnalysisBasis.COMBINED
    interests: Optional[List[str]] = None
    recommended_electives: Optional[List[str]] = None
    honours_minors: Optional[List[str]] = None
    include_resources: bool = True
    include_study_plan: bool = True


class WeaknessAnalysisResponse(BaseModel):
    """Response model for weakness analysis"""
    student_id: str
    analysis_basis: AnalysisBasis
    weaknesses: List[WeaknessArea]
    overall_risk_score: float = Field(default=0, ge=0, le=100)
    priority_areas: List[str] = Field(default_factory=list)
    recommended_resources: List[Dict[str, Any]] = Field(default_factory=list)
    study_plan: Optional[Dict[str, Any]] = None
    analysis_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Summary statistics
    total_weaknesses: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    
    # Insights
    key_insights: List[str] = Field(default_factory=list)
    improvement_potential: float = 0.0


class TopicAnalysis(Document):
    """MongoDB document for topic analysis"""
    topic_name: str
    score: float = Field(..., ge=0, le=100)
    weight: float = Field(..., ge=0, le=1)
    weakness_level: str = Field(..., description="low, medium, high, critical")
    improvement_suggestions: List[str] = Field(default_factory=list)
    recommended_resources: List[str] = Field(default_factory=list)
    practice_exercises: List[str] = Field(default_factory=list)
    
    class Settings:
        name = "topic_analysis"


class WeaknessAnalysisResult(Document):
    """MongoDB document for storing weakness analysis results"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str = Field(..., index=True)
    
    # Analysis metadata
    analysis_basis: str = Field(default="combined")
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    
    # Scores and metrics
    overall_score: float = Field(default=0, ge=0, le=100)
    overall_risk_score: float = Field(default=0, ge=0, le=100)
    semester: Optional[str] = None
    
    # Detailed analysis
    weaknesses: List[Dict[str, Any]] = Field(default_factory=list)
    priority_areas: List[str] = Field(default_factory=list)
    exam_pattern: Dict[str, float] = Field(default_factory=dict)
    
    # AI-generated insights
    ai_analysis: Dict[str, Any] = Field(default_factory=dict)
    study_plan: Dict[str, Any] = Field(default_factory=dict)
    predicted_improvement: Dict[str, Any] = Field(default_factory=dict)
    key_insights: List[str] = Field(default_factory=list)
    
    # Resources
    recommended_resources: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Interest and elective relations
    related_interests: List[str] = Field(default_factory=list)
    related_electives: List[str] = Field(default_factory=list)
    related_honours: List[str] = Field(default_factory=list)
    
    # Metadata
    is_current: bool = True
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "weakness_analysis"
        indexes = [
            "student_id",
            "analysis_basis",
            "subject_code", 
            "is_current",
            "analysis_date"
        ]


class StudentInterestProfile(Document):
    """MongoDB document for student interests"""
    user_id: str = Field(..., index=True)
    interests: List[str] = Field(default_factory=list)
    interest_levels: Dict[str, int] = Field(default_factory=dict)  # interest -> rating 1-5
    career_goals: List[str] = Field(default_factory=list)
    preferred_electives: List[str] = Field(default_factory=list)
    honours_minors_interest: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    skill_levels: Dict[str, int] = Field(default_factory=dict)  # skill -> rating 1-5
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "student_interests"
        indexes = ["user_id"]