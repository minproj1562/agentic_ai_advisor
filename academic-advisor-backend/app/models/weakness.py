# app/models/weakness.py
from typing import List, Dict, Any, Optional
from beanie import Document
from pydantic import Field
from datetime import datetime
import uuid

class TopicAnalysis(Document):
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
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str = Field(..., index=True)
    subject_code: str = Field(..., index=True)
    subject_name: str
    
    # Analysis data
    overall_score: float = Field(..., ge=0, le=100)
    semester: str
    exam_pattern: Dict[str, float] = Field(default_factory=dict)
    
    # AI-generated insights
    ai_analysis: Dict[str, Any] = Field(default_factory=dict)
    study_plan: Dict[str, Any] = Field(default_factory=dict)
    predicted_improvement: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    is_current: bool = True
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "weakness_analysis"
        indexes = [
            "student_id",
            "subject_code", 
            "is_current",
            "analysis_date"
        ]