# app/models/student.py
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TrendStatus(str, Enum):
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"

class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    student_id: str = Field(..., min_length=1, max_length=50)
    department: str
    semester: int = Field(..., ge=1, le=10)
    enrollment_year: int
    phone: Optional[str] = None
    address: Optional[str] = None

class StudentCreate(StudentBase):
    password: str = Field(..., min_length=6)
    
class StudentUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[int] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class StudentPerformance(BaseModel):
    student_id: str
    semester: int
    subjects: List[Dict[str, Any]]
    sgpa: float = Field(..., ge=0, le=10)
    cgpa: float = Field(..., ge=0, le=10)
    attendance_percentage: float = Field(..., ge=0, le=100)
    assignments_completed: int
    total_assignments: int
    quiz_scores: List[float]
    exam_scores: List[float]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StudentAnalytics(BaseModel):
    student_id: str
    current_cgpa: float
    current_sgpa: float
    trend: TrendStatus
    risk_level: RiskLevel
    weak_subjects: List[Dict[str, Any]]
    strong_subjects: List[Dict[str, Any]]
    predicted_next_sgpa: float
    confidence_score: float
    improvement_areas: List[str]
    recommended_resources: List[Dict[str, Any]]
    last_updated: datetime

class StudentProfile(StudentBase):
    id: str
    uid: str
    performance_history: List[StudentPerformance] = []
    analytics: Optional[StudentAnalytics] = None
    cv_url: Optional[str] = None
    skills: List[str] = []
    interests: List[str] = []
    career_goals: List[str] = []
    achievements: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class StudentDashboardData(BaseModel):
    profile: StudentProfile
    current_performance: StudentPerformance
    analytics: StudentAnalytics
    notifications: List[Dict[str, Any]]
    upcoming_deadlines: List[Dict[str, Any]]
    recommended_actions: List[Dict[str, Any]]