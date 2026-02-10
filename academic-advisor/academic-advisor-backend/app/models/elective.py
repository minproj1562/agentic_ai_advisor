# academic-advisor/academic-advisor-backend/app/models/elective.py
from typing import List, Optional, Dict, Any
from beanie import Document
from pydantic import Field, validator, ConfigDict
from datetime import datetime
from enum import Enum

class ElectiveCategory(str, Enum):
    """Categories of electives based on FCRIT curriculum"""
    PROGRAM_ELECTIVE = "Program Elective"  # PEC
    OPEN_ELECTIVE = "Open Elective"  # OEC
    MULTIDISCIPLINARY_MINOR = "Multidisciplinary Minor"  # MDM
    HONOURS_MINOR = "Honours/Minor"
    LIBERAL_LEARNING = "Liberal Learning Course"  # LLC
    SKILL_ENHANCEMENT = "Skill Enhancement Course"  # SEC
    VALUE_EDUCATION = "Value Education Course"  # VEC
    INDIAN_KNOWLEDGE = "Indian Knowledge System"  # IKS

class DifficultyLevel(str, Enum):
    """Difficulty levels"""
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate" 
    ADVANCED = "Advanced"

class Elective(Document):
    """Elective course model aligned with FCRIT B.Tech curriculum"""
    
    # Basic Information
    code: str = Field(..., unique=True, max_length=20)  # e.g., CSE5011, OEC601
    name: str = Field(..., max_length=200)  # Course name
    description: str = Field(default="", max_length=500)  # Course description
    
    # Classification
    category: ElectiveCategory = Field(...)  # Type of elective
    department: str = Field(default="General")  # Department offering the course
    semester: int = Field(..., ge=3, le=8)  # Which semester it's offered
    credits: int = Field(default=3, ge=1, le=8)  # Credit hours
    
    # Prerequisites and requirements
    prerequisites: List[str] = Field(default_factory=list)  # List of prerequisite courses
    min_cgpa_required: Optional[float] = Field(default=None, ge=0.0, le=10.0)  # Min CGPA if required
    
    # Content and Skills
    topics: List[str] = Field(default_factory=list)  # Main topics covered
    skills_covered: List[str] = Field(default_factory=list)  # Skills students will learn
    career_paths: List[str] = Field(default_factory=list)  # Related career opportunities
    
    # Enrollment and Capacity
    max_students: int = Field(default=60, ge=1)
    min_students: int = Field(default=10, ge=1)
    current_enrollment: int = Field(default=0, ge=0)
    
    # Difficulty and Recommendations
    difficulty_level: DifficultyLevel = Field(default=DifficultyLevel.INTERMEDIATE)
    recommended_for: List[str] = Field(default_factory=list)  # e.g., ["CSE", "IT"]
    
    # Instructor Information
    instructor_name: Optional[str] = Field(default=None)
    instructor_email: Optional[str] = Field(default=None)
    
    # Resources
    textbooks: List[str] = Field(default_factory=list)
    online_resources: List[str] = Field(default_factory=list)
    lab_requirements: List[str] = Field(default_factory=list)  # For lab courses
    
    # Honours/Minor Track Information
    is_honours_track: bool = Field(default=False)
    honours_track_name: Optional[str] = Field(default=None)  # e.g., "AI/ML", "Cybersecurity"
    
    # Administrative
    is_available: bool = Field(default=True)  # Is the course currently being offered
    academic_year: str = Field(default="2024-25")
    
    # Analytics (optional, for tracking)
    average_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    completion_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('code')
    def validate_code(cls, v):
        """Validate course code format"""
        if not v or len(v) < 3:
            raise ValueError('Course code must be at least 3 characters')
        return v.upper()
    
    @validator('current_enrollment')
    def validate_enrollment(cls, v, values):
        """Ensure current enrollment doesn't exceed max students"""
        max_students = values.get('max_students', 60)
        if v > max_students:
            raise ValueError(f'Current enrollment ({v}) exceeds maximum capacity ({max_students})')
        return v
    
    class Settings:
        name = "electives"
        indexes = [
            "code",
            "category", 
            "department",
            "semester",
            "is_available",
            "honours_track_name"
        ]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "CSE5011",
                "name": "Cloud Computing Services",
                "description": "Introduction to cloud computing concepts and services",
                "category": "Program Elective",
                "department": "Computer Science",
                "semester": 5,
                "credits": 3,
                "prerequisites": ["Computer Networks", "Operating Systems"],
                "topics": ["Virtualization", "AWS", "Azure", "Docker", "Kubernetes"],
                "skills_covered": ["Cloud Architecture", "DevOps", "Containerization"],
                "career_paths": ["Cloud Architect", "DevOps Engineer", "Site Reliability Engineer"],
                "difficulty_level": "Intermediate",
                "max_students": 60,
                "is_available": True
            }
        }
    )