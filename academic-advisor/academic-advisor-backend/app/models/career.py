# academic-advisor/academic-advisor-backend/app/models/career.py
"""
Career Path model for MongoDB (Beanie Document)
FCRIT IT Department — Indian & Global Market Focus
"""

from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class CareerCategory(str, Enum):
    SOFTWARE_DEVELOPMENT = "Software Development"
    DATA_AND_AI = "Data & AI"
    CLOUD_AND_DEVOPS = "Cloud & DevOps"
    SECURITY = "Security"
    NETWORKING_AND_IOT = "Networking & IoT"
    MANAGEMENT = "Management & Analysis"
    RESEARCH = "Research"
    DESIGN = "Design & UX"


class DemandLevel(str, Enum):
    VERY_HIGH = "Very High"
    HIGH = "High"
    MODERATE = "Moderate"
    EMERGING = "Emerging"
    NICHE = "Niche"


class RoadmapStep(BaseModel):
    step: int
    title: str
    description: str
    duration: str
    resources: List[str] = Field(default_factory=list)


class SalaryRange(BaseModel):
    entry_level: str = "3-6 LPA"
    mid_level: str = "8-15 LPA"
    senior_level: str = "15-30 LPA"
    top_companies: str = "20-50+ LPA"
    currency: str = "INR"
    note: str = ""


class CareerPath(Document):
    """Career path document for chatbot career guidance"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Basic info
    title: str = Field(..., max_length=200)
    category: CareerCategory
    description: str = Field(..., max_length=1500)

    # Skills & Requirements
    required_skills: List[str] = Field(default_factory=list)
    recommended_subjects: List[str] = Field(default_factory=list)
    recommended_electives: List[str] = Field(default_factory=list)
    min_cgpa_recommended: float = Field(default=6.0, ge=0, le=10)

    # Career details
    job_titles: List[str] = Field(default_factory=list)
    salary_range: SalaryRange = Field(default_factory=SalaryRange)

    # Companies
    top_companies_india: List[str] = Field(default_factory=list)
    top_companies_global: List[str] = Field(default_factory=list)

    # Growth & Market
    market_demand: DemandLevel = DemandLevel.HIGH
    growth_potential: str = "High"

    # Certifications
    certifications: List[str] = Field(default_factory=list)

    # Roadmap
    roadmap: List[RoadmapStep] = Field(default_factory=list)

    # Search & Matching
    keywords: List[str] = Field(default_factory=list)
    related_careers: List[str] = Field(default_factory=list)

    # Metadata
    is_active: bool = True
    department: str = "IT"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "career_paths"
        indexes = [
            "category",
            "is_active",
            "market_demand",
            "keywords",
        ]