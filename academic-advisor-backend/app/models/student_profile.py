# academic-advisor-backend/app/models/student_profile.py
from beanie import Document, Indexed
from pydantic import Field, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum

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

class StudentProfile(Document):
    # Primary identifier - Firebase UID
    user_id: Indexed(str, unique=True)
    
    # Basic information
    roll_number: Indexed(str, unique=True)
    name: str
    email: Optional[EmailStr] = None
    branch: Branch
    admission_year: int
    current_semester: int = 1
    current_academic_year: str = Field(default_factory=lambda: f"{datetime.now().year}-{datetime.now().year + 1}")
    
    # Academic metrics
    cgpa: float = 0.0
    total_credits_earned: int = 0
    total_credits_required: int = 160
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "student_profiles"
        indexes = [
            "user_id",
            "roll_number", 
            "branch",
            "admission_year"
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "firebase_uid_123",
                "roll_number": "CSIT/2022/045",
                "name": "John Doe",
                "email": "john@example.com",
                "branch": "IT",
                "admission_year": 2022,
                "current_semester": 3,
                "current_academic_year": "2024-25",
                "cgpa": 8.5,
                "total_credits_earned": 48,
                "total_credits_required": 160
            }
        }

class SemesterRecord(Document):
    student_id: Indexed(str)  # References StudentProfile.user_id
    semester_number: int
    academic_year: str
    
    # Academic performance
    sgpa: Optional[float] = None
    credits_earned: int = 0
    total_subjects: int = 0
    passed_subjects: int = 0
    failed_subjects: int = 0
    attendance_percentage: float = 75.0
    
    # Status
    is_completed: bool = False
    
    # Dates
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "semester_records"
        indexes = [
            "student_id",
            "semester_number",
            [("student_id", 1), ("semester_number", 1)]
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "student_id": "firebase_uid_123",
                "semester_number": 3,
                "academic_year": "2024-25",
                "sgpa": 8.2,
                "credits_earned": 24,
                "total_subjects": 6,
                "passed_subjects": 6,
                "failed_subjects": 0,
                "attendance_percentage": 85.5,
                "is_completed": True
            }
        }

class SubjectScore(Document):
    student_id: Indexed(str)  # References StudentProfile.user_id
    semester_id: str  # References SemesterRecord.id
    semester_number: int
    
    # Subject information
    subject_code: str
    subject_name: str
    credits: int
    
    # Marks
    internal_marks: float = 0.0  # Out of 20
    external_marks: float = 0.0  # Out of 80
    total_marks: float = 0.0     # Out of 100
    
    # Grading
    grade: Optional[Grade] = None
    grade_points: Optional[float] = None
    
    # Subject type
    is_elective: bool = False
    is_practical: bool = False
    is_backlog: bool = False
    attempt_number: int = 1
    
    # Analysis
    weaknesses: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "subject_scores"
        indexes = [
            "student_id",
            "semester_id",
            "subject_code",
            [("student_id", 1), ("semester_number", 1)]
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "student_id": "firebase_uid_123",
                "semester_id": "semester_record_id",
                "semester_number": 3,
                "subject_code": "CSIT301",
                "subject_name": "Data Structures and Algorithms",
                "credits": 3,
                "internal_marks": 18.0,
                "external_marks": 65.0,
                "total_marks": 83.0,
                "grade": "A",
                "grade_points": 8.0,
                "is_elective": False,
                "is_practical": False,
                "is_backlog": False,
                "attempt_number": 1,
                "weaknesses": ["Linked Lists", "Tree Traversal"]
            }
        }