# app/schemas/student_schemas.py
"""
Pydantic schemas for student-related data
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator


class StudentBase(BaseModel):
    """Base student schema"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    student_id: str = Field(..., min_length=1, max_length=20)
    department: str = Field(..., regex="^(CS|ECE|MECH|CIVIL|EEE)$")
    batch: int = Field(..., ge=2015, le=2030)
    current_semester: int = Field(..., ge=1, le=10)


class StudentCreate(StudentBase):
    """Schema for creating a student"""
    password: str = Field(..., min_length=8)
    phone: Optional[str] = Field(None, regex="^[0-9]{10}$")


class StudentUpdate(BaseModel):
    """Schema for updating student data"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, regex="^[0-9]{10}$")
    current_semester: Optional[int] = Field(None, ge=1, le=10)
    linkedin_profile: Optional[str] = None
    github_profile: Optional[str] = None
    skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None


class PerformanceData(BaseModel):
    """Performance data schema"""
    semester: int = Field(..., ge=1, le=10)
    sgpa: float = Field(..., ge=0, le=10)
    credits_earned: int = Field(..., ge=0)
    attendance: float = Field(..., ge=0, le=100)
    subjects: List[Dict[str, Any]]
    created_at: Optional[datetime] = None
    
    @validator('sgpa')
    def validate_sgpa(cls, v):
        return round(v, 2)


class WeaknessData(BaseModel):
    """Weakness data schema"""
    subject: str
    severity: str = Field(..., regex="^(low|medium|high|critical)$")
    average_score: float = Field(..., ge=0, le=100)
    gap: float
    topics: List[str]
    improvement_plan: Dict[str, Any]
    resources: List[Dict[str, Any]]
    confidence: float = Field(..., ge=0, le=1)


class PerformanceTrend(BaseModel):
    semester: int
    sgpa: float
    attendance: Optional[float] = None


class PerformanceStatistics(BaseModel):
    average_sgpa: float
    max_sgpa: float
    min_sgpa: float
    total_semesters: int
    improvement_rate: Optional[float] = None


class PerformanceDataResponse(BaseModel):
    sgpa_trend: List[PerformanceTrend]
    attendance_trend: List[PerformanceTrend]
    statistics: PerformanceStatistics


class Weakness(BaseModel):
    id: str
    category: str
    description: str
    severity: str
    status: str
    created_at: datetime


class Recommendation(BaseModel):
    id: str
    type: str
    description: str
    priority: str
    status: str
    created_at: datetime


class Prediction(BaseModel):
    risk_score: float
    trend: str
    confidence: float
    predicted_cgpa: Optional[float] = None
    next_semester_prediction: Optional[Dict[str, Any]] = None


class AnalysisMetadata(BaseModel):
    version: str
    timestamp: datetime
    confidence: float


class StudentAnalysisResponse(BaseModel):
    """Student analysis response schema"""
    student_id: str
    name: str
    department: str
    batch: int
    current_semester: int
    cgpa: float
    sgpa_trend: List[float]
    latest_sgpa: float
    attendance: float
    weaknesses: List[WeaknessData]
    weakness_count: int
    risk_score: float
    risk_level: str
    improvement_trend: str
    recommendations_pending: int
    predictions: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "student_id": "STU001",
                "name": "John Doe",
                "department": "CS",
                "batch": 2021,
                "current_semester": 5,
                "cgpa": 7.5,
                "sgpa_trend": [7.0, 7.2, 7.5, 7.8, 8.0],
                "latest_sgpa": 8.0,
                "attendance": 85.5,
                "weaknesses": [],
                "weakness_count": 0,
                "risk_score": 25.0,
                "risk_level": "low",
                "improvement_trend": "improving",
                "recommendations_pending": 2
            }
        }


class StudentDetailResponse(BaseModel):
    """Detailed student response with all data"""
    id: str
    name: str
    email: str
    department: str
    current_semester: int
    cgpa: float
    risk_score: float
    risk_level: str
    attendance: float
    performance_data: PerformanceDataResponse
    weaknesses: List[Weakness]
    recommendations: List[Recommendation]
    predictions: Dict[str, Any]
    analysis_metadata: AnalysisMetadata


class BulkAnalysisRequest(BaseModel):
    """Request for bulk analysis"""
    department: Optional[str] = None
    semester: Optional[int] = None
    batch: Optional[int] = None
    include_predictions: bool = True
    include_recommendations: bool = False


class RecommendationSchema(BaseModel):
    """Recommendation schema"""
    type: str = Field(..., regex="^(academic|attendance|subject_improvement|career|skills)$")
    priority: str = Field(..., regex="^(low|medium|high)$")
    title: str
    description: str
    actions: List[str]
    resources: Optional[List[Dict[str, Any]]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_viewed: bool = False
    is_accepted: bool = False


class PaginationInfo(BaseModel):
    skip: int
    limit: int
    total: int
    has_more: bool


class StudentListResponse(BaseModel):
    students: List[StudentAnalysisResponse]
    pagination: PaginationInfo