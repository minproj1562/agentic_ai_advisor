#academic-advisor-backend/app/models/elective.py
from typing import List, Optional, Dict, Any
from beanie import Document, Link
from pydantic import Field, HttpUrl
from datetime import datetime
from enum import Enum

class DifficultyLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"

class ElectiveCategory(str, Enum):
    TECHNICAL = "Technical"
    MANAGEMENT = "Management"
    RESEARCH = "Research"
    INTERDISCIPLINARY = "Interdisciplinary"

class InstructorInfo(Document):
    name: str = Field(..., max_length=100)
    email: str = Field(..., max_length=100)
    department: str = Field(..., max_length=100)
    expertise: List[str] = Field(default_factory=list)
    rating: float = Field(default=0.0, ge=0, le=5)
    total_ratings: int = Field(default=0, ge=0)
    profile_picture: Optional[str] = None
    office_location: Optional[str] = None
    office_hours: Optional[str] = None
    
    class Settings:
        name = "instructor_info"

class Elective(Document):
    code: str = Field(..., unique=True)
    name: str = Field(..., max_length=200)
    description: str
    category: ElectiveCategory
    difficulty: DifficultyLevel
    
    # Academic details
    credits: int = Field(..., ge=1, le=6)
    prerequisites: List[str] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)
    
    # Skills and career impact
    skills_developed: List[str] = Field(default_factory=list)
    career_impact: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    
    # Instructor information
    instructor: Link[InstructorInfo]
    
    # Capacity and scheduling
    max_students: int = Field(default=60, ge=1)
    current_enrollment: int = Field(default=0, ge=0)
    semester_offered: List[int] = Field(default_factory=list)
    
    # Resources
    syllabus_url: Optional[HttpUrl] = None
    reference_books: List[str] = Field(default_factory=list)
    
    # Analytics
    average_rating: float = Field(default=0.0, ge=0, le=5)
    success_rate: float = Field(default=0.0, ge=0, le=100)
    recommendation_score: float = Field(default=0.0, ge=0, le=100)
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "electives"
        indexes = [
            "code",
            "category",
            "difficulty", 
            "tags",
            "is_active"
        ]