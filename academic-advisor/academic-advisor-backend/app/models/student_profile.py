# academic-advisor-backend/app/models/student_profile.py

from beanie import Document
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

# DO NOT IMPORT FROM THIS FILE ITSELF!


class Branch(str, Enum):
    IT = "IT"
    COMP = "COMP"
    EXTC = "EXTC"
    MECH = "MECH"
    ELEC = "ELEC"


class Grade(str, Enum):
    O = "O"
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C = "C"
    P = "P"
    F = "F"


class SubjectScore(BaseModel):
    """Subject score - EMBEDDED model"""
    subject_code: str = ""
    subject_name: str = ""
    credits: int = 3
    internal_marks: float = 0.0
    external_marks: float = 0.0
    total_marks: float = 0.0
    grade: str = ""
    grade_points: float = 0.0
    is_elective: bool = False
    is_practical: bool = False

    class Config:
        arbitrary_types_allowed = True


class SemesterRecord(BaseModel):
    """Semester record - EMBEDDED model"""
    semester_number: int = 1
    academic_year: str = ""
    subjects: List[SubjectScore] = []
    sgpa: float = 0.0
    total_credits: int = 0
    credits_earned: int = 0
    is_complete: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True


class StudentProfile(Document):
    """Student profile - MongoDB Document"""
    user_id: str
    roll_number: str = ""
    name: str = ""
    email: str = ""
    branch: str = "IT"
    admission_year: int = 2020
    current_semester: int = 1
    current_academic_year: str = ""
    cgpa: float = 0.0
    total_credits_earned: int = 0
    total_credits_required: int = 160
    semester_records: List[SemesterRecord] = []
    skills: List[str] = []
    interests: List[str] = []
    career_goals: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    study_hours: float = Field(default=4.0, ge=0, le=16, description="Average daily study hours (self-reported)")

    class Settings:
        name = "student_profiles"
        use_state_management = True