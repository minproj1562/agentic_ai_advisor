#academic-advisor-backend/app/models/resource.py
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
from beanie import Document
from pydantic import Field

class StudyResource(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    type: str  # Video Course, PDF Notes, etc.
    duration: str
    provider: str
    platform: str
    rating: float
    reviews: int
    difficulty: str
    icon: str
    tags: List[str] = Field(default_factory=list)
    last_updated: str
    language: str
    exam_relevance: str
    url: str
    thumbnail_url: Optional[str] = None
    
    # Content metadata
    description: str
    topics_covered: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    target_audience: List[str] = Field(default_factory=list)
    
    # Quality metrics
    completion_rate: float = 0.0
    effectiveness_score: float = 0.0
    student_feedback: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Recommendation data
    related_topics: List[str] = Field(default_factory=list)
    embedding_vector: Optional[List[float]] = None
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "study_resources"
        indexes = [
            "type",
            "difficulty",
            "tags",
            "topics_covered",
            "rating"
        ]