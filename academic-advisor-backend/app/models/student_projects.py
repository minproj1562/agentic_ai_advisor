# app/models/student_projects.py
from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class ProjectType(str, Enum):
    ACADEMIC = "academic"
    PERSONAL = "personal"
    HACKATHON = "hackathon"
    INTERNSHIP = "internship"
    COMPETITION = "competition"
    RESEARCH = "research"
    OPEN_SOURCE = "open_source"
    FREELANCE = "freelance"

class TeamMember(BaseModel):
    name: str
    role: str
    contribution: str
    email: Optional[str] = None
    github_profile: Optional[str] = None

class ProjectFile(BaseModel):
    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_type: str
    file_size: int
    storage_path: str
    uploaded_at: datetime = Field(default_factory=datetime.now)
    analysis_results: Optional[Dict[str, Any]] = None

class InferredInterest(BaseModel):
    domain: str
    confidence: float
    keywords: List[str]
    related_skills: List[str]
    career_paths: List[str]
    industry_relevance: float
    reasoning: str
    evidence: List[str] = Field(default_factory=list)

class StudentProject(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: Indexed(str)
    
    # Basic Information
    title: str
    description: str
    detailed_description: Optional[str] = None
    project_type: ProjectType
    
    # Timeline
    start_date: datetime
    end_date: Optional[datetime] = None
    duration_months: Optional[float] = None
    
    # Technical Details
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    
    # Links
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    documentation_url: Optional[str] = None
    video_url: Optional[str] = None
    
    # Team Information
    is_team_project: bool = False
    team_size: int = 1
    team_members: List[TeamMember] = Field(default_factory=list)
    role_in_project: Optional[str] = None
    
    # Outcomes
    key_achievements: List[str] = Field(default_factory=list)
    challenges_faced: List[str] = Field(default_factory=list)
    learnings: List[str] = Field(default_factory=list)
    impact_metrics: Optional[Dict[str, Any]] = None
    
    # Files
    project_files: List[ProjectFile] = Field(default_factory=list)
    
    # ML Analysis
    inferred_interests: List[InferredInterest] = Field(default_factory=list)
    extracted_skills: List[str] = Field(default_factory=list)
    complexity_score: Optional[float] = None
    innovation_score: Optional[float] = None
    
    # Metadata
    is_public: bool = True
    views_count: int = 0
    likes_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "student_projects"
        indexes = [
            "student_id",
            "project_type",
            "created_at",
            [("student_id", 1), ("created_at", -1)]
        ]

class StudentInterestProfile(Document):
    student_id: Indexed(str, unique=True)
    
    # Aggregated Interests
    primary_domains: List[Dict[str, Any]] = Field(default_factory=list)
    secondary_interests: List[str] = Field(default_factory=list)
    
    # Skills Matrix
    technical_skills: Dict[str, float] = Field(default_factory=dict)
    soft_skills: Dict[str, float] = Field(default_factory=dict)
    domain_expertise: Dict[str, float] = Field(default_factory=dict)
    
    # Career Analysis
    recommended_career_paths: List[Dict[str, Any]] = Field(default_factory=list)
    industry_alignment: Dict[str, float] = Field(default_factory=dict)
    job_market_readiness: float = 0.0
    
    # Learning Path
    skills_to_learn: List[str] = Field(default_factory=list)
    recommended_courses: List[str] = Field(default_factory=list)
    recommended_certifications: List[str] = Field(default_factory=list)
    
    # Statistics
    total_projects: int = 0
    projects_by_type: Dict[str, int] = Field(default_factory=dict)
    average_project_complexity: float = 0.0
    consistency_score: float = 0.0
    
    # Trends
    interest_evolution: List[Dict[str, Any]] = Field(default_factory=list)
    skill_growth_rate: Dict[str, float] = Field(default_factory=dict)
    
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "student_interest_profiles"