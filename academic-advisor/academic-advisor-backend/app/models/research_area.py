# app/models/research_area.py
from beanie import Document, Indexed
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
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

class PublicationType(str, Enum):
    JOURNAL = "journal"
    CONFERENCE = "conference"
    BOOK_CHAPTER = "book-chapter"
    PREPRINT = "preprint"
    PATENT = "patent"

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

class CitationTrend(BaseModel):
    month: str
    count: int

class Collaborator(BaseModel):
    id: Optional[str] = None
    name: str
    affiliation: str
    role: str
    email: Optional[str] = None

class ResearchPaper(BaseModel):
    """Research Paper model for analytics service"""
    id: str
    faculty_id: str
    title: str
    authors: List[str]
    publication_date: datetime
    journal: Optional[str] = None
    conference: Optional[str] = None
    publication_type: PublicationType
    citations: int = 0
    abstract: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    is_open_access: bool = False
    research_areas: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

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
    
    # Papers (for analytics)
    papers: List[ResearchPaper] = Field(default_factory=list)
    
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
            [("user_id", 1), ("category", 1)],
            [("user_id", 1), ("publications", -1)]
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "firebase_uid_123",
                "name": "Machine Learning",
                "description": "Research in machine learning algorithms and applications",
                "category": "primary",
                "keywords": ["ai", "neural networks", "deep learning"],
                "publications": 15,
                "citations": 120,
                "grants": 3,
                "grant_amount": 150000,
                "papers": [
                    {
                        "id": "paper_1",
                        "faculty_id": "faculty_123",
                        "title": "Advanced Neural Networks",
                        "authors": ["John Doe", "Jane Smith"],
                        "publication_date": "2024-01-15T00:00:00",
                        "journal": "Journal of AI Research",
                        "publication_type": "journal",
                        "citations": 25,
                        "research_areas": ["Machine Learning", "Neural Networks"]
                    }
                ]
            }
        }