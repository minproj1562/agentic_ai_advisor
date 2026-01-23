# app/models/faculty.py
from beanie import Document, Indexed
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FacultyStatus(str, Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    INACTIVE = "inactive"


class Qualification(BaseModel):
    degree: str
    field: str
    institution: str
    year: Optional[int] = None


class Publication(BaseModel):
    title: str
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    authors: List[str] = Field(default_factory=list)


class ResearchArea(BaseModel):
    name: str
    keywords: List[str] = Field(default_factory=list)


class MeetingSlot(BaseModel):
    day: str  # e.g., "Monday"
    start_time: str  # e.g., "10:00"
    end_time: str  # e.g., "11:00"
    venue: Optional[str] = None
    is_available: bool = True


class Faculty(Document):
    # Basic Information
    user_id: Indexed(str, unique=True)
    name: str
    email: EmailStr
    department: str
    designation: str
    employee_id: Optional[str] = None
    
    # Contact
    phone: Optional[str] = None
    office_location: Optional[str] = None
    
    # Academic Information
    qualifications: List[Qualification] = Field(default_factory=list)
    specializations: List[str] = Field(default_factory=list)
    research_areas: List[ResearchArea] = Field(default_factory=list)
    publications: List[Publication] = Field(default_factory=list)
    
    # Experience
    years_of_experience: Optional[int] = None
    teaching_subjects: List[str] = Field(default_factory=list)
    
    # CV Data (parsed from uploaded CV)
    cv_url: Optional[str] = None
    cv_parsed_data: Dict[str, Any] = Field(default_factory=dict)
    skills: List[str] = Field(default_factory=list)
    
    # Mentorship
    mentee_ids: List[str] = Field(default_factory=list)
    max_mentees: int = 10
    
    # Availability for meetings
    available_slots: List[MeetingSlot] = Field(default_factory=list)
    
    # Status
    status: FacultyStatus = FacultyStatus.ACTIVE
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "faculty"
        indexes = [
            "user_id",
            "email",
            "department",
            [("department", 1), ("status", 1)]
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "firebase_uid_123",
                "name": "Dr. John Doe",
                "email": "john.doe@example.edu",
                "department": "Computer Engineering",
                "designation": "Associate Professor",
                "specializations": ["Machine Learning", "Data Science"],
                "teaching_subjects": ["AI", "ML", "Data Structures"]
            }
        }