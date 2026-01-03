# app/models/student.py
from beanie import Document, Indexed, Link
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TrendEnum(str, Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"

class Subject(BaseModel):
    id: str
    name: str
    code: str
    score: float
    credits: int
    trend: TrendEnum
    weakness: List[str] = Field(default_factory=list)
    strength: List[str] = Field(default_factory=list)
    semester: str
    grade: Optional[str] = None
    attendance: Optional[float] = None
    assignments_completed: Optional[int] = None
    quiz_scores: List[float] = Field(default_factory=list)

class StudentInfo(BaseModel):
    uid: str
    year: str
    semester: str
    branch: str
    rollNumber: str
    email: str
    name: str
    batch: str
    section: Optional[str] = None

class StudentPerformance(Document):
    student_info: StudentInfo
    subjects: List[Subject]
    overall_cgpa: float
    semester_sgpa: float
    strong_subjects: List[str] = Field(default_factory=list)
    weak_subjects: List[str] = Field(default_factory=list)
    completed_credits: int
    total_credits: int
    interests: List[str] = Field(default_factory=list)
    career_goals: List[str] = Field(default_factory=list)
    skills_matrix: Dict[str, float] = Field(default_factory=dict)
    
    # Additional metrics
    attendance_average: float = 0.0
    assignment_completion_rate: float = 0.0
    performance_trend: TrendEnum = TrendEnum.STABLE
    predicted_next_sgpa: Optional[float] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "student_performance"
        indexes = [
            "student_info.uid",
            "student_info.semester",
            "student_info.branch",
            [("student_info.uid", 1), ("updated_at", -1)]
        ]