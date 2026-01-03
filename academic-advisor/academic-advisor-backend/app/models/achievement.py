# app/models/achievement.py
from typing import Optional, List, Dict, Any
from beanie import Document
from pydantic import Field
from datetime import datetime
import uuid
from enum import Enum

class AchievementCategory(str, Enum):
    RESEARCH = "research"
    TEACHING = "teaching" 
    SERVICE = "service"
    AWARD = "award"
    PUBLICATION = "publication"
    CONFERENCE = "conference"
    GRANT = "grant"
    PATENT = "patent"
    STUDENT_SUPERVISION = "student_supervision"
    OTHER = "other"

class AchievementStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    REJECTED = "rejected"

class Achievement(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    faculty_id: str
    title: str
    description: Optional[str] = None
    category: AchievementCategory
    date: datetime
    impact_score: Optional[float] = None
    verified: bool = False
    verification_date: Optional[datetime] = None
    verified_by: Optional[str] = None
    evidence_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    status: AchievementStatus = AchievementStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "achievements"
        indexes = [
            "faculty_id",
            "category", 
            "date",
            "verified"
        ]

class AchievementAnalytics(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    faculty_id: str
    total_achievements: int = 0
    verified_count: int = 0
    this_year_count: int = 0
    avg_impact_score: float = 0.0
    growth_rate: float = 0.0
    category_distribution: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "achievement_analytics"
        indexes = ["faculty_id"]