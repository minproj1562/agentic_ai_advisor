from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class ResearchCategory(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    EMERGING = "emerging"

class ExpertiseLevel(str, Enum):
    EXPERT = "expert"
    ADVANCED = "advanced"
    INTERMEDIATE = "intermediate"

class ProjectStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PLANNED = "planned"

class SubArea(BaseModel):
    name: str
    description: str
    publications: int = 0

class ResearchProject(BaseModel):
    id: str
    title: str
    status: ProjectStatus
    start_date: datetime
    end_date: Optional[datetime] = None

class Expertise(BaseModel):
    level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
    years_of_experience: int = 0
    recognitions: List[str] = Field(default_factory=list)

class Impact(BaseModel):
    academic_impact: float = 0
    industry_impact: float = 0
    societal_impact: float = 0

class TrendData(BaseModel):
    year: int
    count: int

class ResearchArea(Document):
    user_id: Indexed(str)  # Firebase UID
    
    # Basic Information
    name: Indexed(str)
    description: str
    category: ResearchCategory
    
    # Keywords and Classification
    keywords: List[str] = Field(default_factory=list)
    sub_areas: List[SubArea] = Field(default_factory=list)
    related_areas: List[str] = Field(default_factory=list)
    
    # Metrics
    publications: int = 0
    citations: int = 0
    grants: int = 0
    grant_amount: float = 0
    
    # Collaboration
    collaborators: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Projects
    projects: List[ResearchProject] = Field(default_factory=list)
    
    # Expertise
    expertise: Expertise = Field(default_factory=Expertise)
    
    # Impact
    impact: Impact = Field(default_factory=Impact)
    
    # Trends
    publication_trend: List[TrendData] = Field(default_factory=list)
    citation_trend: List[TrendData] = Field(default_factory=list)
    collaboration_trend: List[TrendData] = Field(default_factory=list)
    
    # Technical Details
    technologies: List[str] = Field(default_factory=list)
    methodologies: List[str] = Field(default_factory=list)
    applications: List[str] = Field(default_factory=list)
    funding_sources: List[str] = Field(default_factory=list)
    
    # Metadata
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "research_areas"
        indexes = [
            "user_id",
            "name",
            "category",
            [("user_id", 1), ("category", 1)]
        ]