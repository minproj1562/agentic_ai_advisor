#academic-advisor-backend/app/models/student_performance.py
from typing import List, Optional, Dict, Any
from beanie import Document
from pydantic import Field
from datetime import datetime
import uuid

class Subject(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    score: float
    credits: int
    trend: str  # 'up', 'down', 'stable'
    weaknesses: List[str] = Field(default_factory=list)
    semester: int
    grade: str
    grade_points: float

    class Settings:
        name = "subjects"

class StudentInfo(Document):
    uid: str
    year: str
    semester: str
    branch: str
    roll_number: str

    class Settings:
        name = "student_info"

class StudentPerformance(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_info: StudentInfo
    subjects: List[Subject] = Field(default_factory=list)
    overall_cgpa: float = 0.0
    semester_sgpa: float = 0.0
    strong_subjects: List[str] = Field(default_factory=list)
    weak_subjects: List[str] = Field(default_factory=list)
    completed_credits: int = 0
    total_credits: int = 160
    interests: List[str] = Field(default_factory=list)
    career_goals: List[str] = Field(default_factory=list)
    skills_matrix: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "student_performance"
        indexes = [
            "student_info.uid",
            "student_info.roll_number"
        ]