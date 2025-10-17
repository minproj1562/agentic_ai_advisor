# app/schemas/achievement.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum

class AchievementCategory(str, Enum):
    award = "award"
    certification = "certification"
    milestone = "milestone"
    recognition = "recognition"
    grant = "grant"

class AchievementCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    category: AchievementCategory
    organization: str = Field(..., min_length=2, max_length=200)
    date: datetime
    url: Optional[str] = None
    amount: Optional[float] = None
    tags: List[str] = []
    collaborators: List[str] = []
    visibility: str = "public"
    
    @validator('url')
    def validate_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        return [tag.lower() for tag in v]

class AchievementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[AchievementCategory] = None
    organization: Optional[str] = None
    date: Optional[datetime] = None
    url: Optional[str] = None
    amount: Optional[float] = None
    tags: Optional[List[str]] = None
    collaborators: Optional[List[str]] = None
    visibility: Optional[str] = None

class AchievementResponse(BaseModel):
    id: str
    faculty_id: str
    title: str
    description: str
    category: str
    organization: str
    date: datetime
    url: Optional[str]
    amount: Optional[float]
    impact_score: Optional[float]
    tags: List[str]
    collaborators: List[str]
    attachments: List[dict]
    visibility: str
    verified: bool
    verified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AchievementAnalyticsResponse(BaseModel):
    total_achievements: int
    verified_count: int
    this_year_count: int
    avg_impact_score: float
    growth_rate: float
    category_distribution: List[dict]
    recent_achievements: List[AchievementResponse]