"""
Beanie (MongoDB) Models for Student Analysis
Enterprise-level document models with indexing, relationships, and audit trails
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import re

from beanie import Document, Indexed, Link, before_event, Insert, Replace, Save
from pydantic import Field, validator, BaseModel


class TimestampMixin:
    """Mixin for automatic timestamp management"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AuditMixin:
    """Mixin for audit trail"""
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    version: int = 1
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None


class Student(Document, TimestampMixin, AuditMixin):
    """
    Student model with comprehensive profile and performance tracking
    """
    # Primary fields
    student_id: str = Indexed(unique=True)
    name: str = Indexed()
    email: str = Indexed(unique=True)
    phone: Optional[str] = None

    # Academic details
    department: str = Indexed()
    batch: int = Indexed()
    current_semester: int
    admission_year: int

    # Performance metrics
    cgpa: float = 0.0
    total_credits: int = 0
    attendance_percentage: float = 0.0

    # Profile data
    profile_image: Optional[str] = None
    linkedin_profile: Optional[str] = None
    github_profile: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)

    # Status flags
    is_active: bool = True
    is_graduated: bool = False
    has_warnings: bool = False
    risk_level: str = "low"  # low, medium, high

    # Metadata
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    last_analysis_date: Optional[datetime] = None

    # Relationships (links to other documents)
    # These will be populated with actual document IDs
    performances: List[Link["Performance"]] = Field(default_factory=list)
    weaknesses: List[Link["Weakness"]] = Field(default_factory=list)
    recommendations: List[Link["Recommendation"]] = Field(default_factory=list)
    analysis_history: List[Link["AnalysisHistory"]] = Field(default_factory=list)

    class Settings:
        name = "students"
        indexes = [
            [("department", 1), ("batch", 1)],          # compound index
            [("cgpa", 1), ("risk_level", 1)],
        ]

    @validator("email")
    def validate_email(cls, v):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v.lower()

    @validator("cgpa")
    def validate_cgpa(cls, v):
        if not 0 <= v <= 10:
            raise ValueError("CGPA must be between 0 and 10")
        return round(v, 2)

    @validator("current_semester")
    def validate_semester(cls, v):
        if not 1 <= v <= 8:
            raise ValueError("Semester must be between 1 and 8")
        return v

    @property
    def full_profile_score(self) -> int:
        """Calculate profile completeness score (0-100)"""
        score = 0
        if self.profile_image:
            score += 10
        if self.linkedin_profile:
            score += 15
        if self.github_profile:
            score += 15
        if len(self.skills) > 0:
            score += 30
        if len(self.interests) > 0:
            score += 10
        if self.cgpa > 7:
            score += 20
        return score

    @property
    def years_in_college(self) -> int:
        """Calculate years spent in college"""
        return datetime.utcnow().year - self.admission_year

    @property
    def graduation_year(self) -> int:
        """Expected graduation year"""
        return self.admission_year + 4

    def calculate_risk_level(self) -> str:
        """Calculate student's academic risk level based on current data"""
        if self.cgpa < 5.0 or self.attendance_percentage < 65:
            return "high"
        elif self.cgpa < 6.5 or self.attendance_percentage < 75:
            return "medium"
        return "low"

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert model to dictionary (useful for API responses)"""
        data = {
            "id": str(self.id),
            "student_id": self.student_id,
            "name": self.name,
            "email": self.email if include_sensitive else None,
            "department": self.department,
            "batch": self.batch,
            "current_semester": self.current_semester,
            "cgpa": self.cgpa,
            "attendance_percentage": self.attendance_percentage,
            "risk_level": self.risk_level,
            "profile_score": self.full_profile_score,
            "is_active": self.is_active,
        }
        return data

    @before_event(Insert, Replace, Save)
    async def update_risk_level(self):
        """Automatically update risk level before saving"""
        self.risk_level = self.calculate_risk_level()
        self.version += 1


class Performance(Document, TimestampMixin):
    """
    Semester-wise performance tracking
    """
    student: Link[Student]

    # Semester details
    semester: int
    academic_year: str  # e.g., "2023-24"

    # Performance metrics
    sgpa: float
    credits_earned: int = 0
    credits_registered: int = 0

    # Subject-wise performance
    subjects: List[Dict[str, Any]] = Field(default_factory=list)  # list of subject performances
    grades: Dict[str, str] = Field(default_factory=dict)          # subject code -> grade

    # Attendance and participation
    attendance_percentage: float = 0.0
    assignments_completed: int = 0
    assignments_total: int = 0

    # Extra-curricular
    events_participated: int = 0
    achievements: List[str] = Field(default_factory=list)

    # Analysis results
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    improvement_areas: List[str] = Field(default_factory=list)

    # Predictive metrics
    predicted_sgpa: Optional[float] = None
    confidence_score: Optional[float] = None

    class Settings:
        name = "performances"
        indexes = [
            [("student", 1), ("semester", 1)],                     # ensure fast lookup
            {"keys": [("student", 1), ("semester", 1), ("academic_year", 1)], "unique": True},
        ]

    @validator("sgpa")
    def validate_sgpa(cls, v):
        if not 0 <= v <= 10:
            raise ValueError("SGPA must be between 0 and 10")
        return round(v, 2)

    @property
    def completion_rate(self) -> float:
        """Calculate assignment completion rate"""
        if self.assignments_total == 0:
            return 0.0
        return (self.assignments_completed / self.assignments_total) * 100

    @property
    def credit_completion_rate(self) -> float:
        """Calculate credit completion rate"""
        if self.credits_registered == 0:
            return 0.0
        return (self.credits_earned / self.credits_registered) * 100

    def calculate_grade_distribution(self) -> Dict[str, int]:
        """Calculate distribution of grades"""
        distribution: Dict[str, int] = {}
        for grade in self.grades.values():
            distribution[grade] = distribution.get(grade, 0) + 1
        return distribution


class Weakness(Document, TimestampMixin):
    """
    Identified weaknesses and improvement areas
    """
    student: Link[Student]

    # Weakness details
    subject: str = Indexed()
    topic: Optional[str] = None
    severity: str = Indexed()  # low, medium, high, critical

    # Metrics
    current_score: Optional[float] = None
    expected_score: Optional[float] = None
    gap_percentage: Optional[float] = None

    # Analysis
    identified_date: datetime = Field(default_factory=datetime.utcnow)
    last_reviewed: Optional[datetime] = None
    improvement_rate: Optional[float] = None  # Percentage improvement over time

    # Recommendations
    recommended_resources: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)

    # Status
    status: str = "active"  # active, improving, resolved
    priority: int = 1        # 1-5, 5 being highest

    # ML metadata
    ml_confidence: Optional[float] = None
    ml_model_version: Optional[str] = None

    class Settings:
        name = "weaknesses"
        indexes = [
            [("student", 1), ("subject", 1)],
            [("severity", 1), ("status", 1)],
        ]

    @validator("severity")
    def validate_severity(cls, v):
        valid = {"low", "medium", "high", "critical"}
        if v not in valid:
            raise ValueError(f"Severity must be one of {valid}")
        return v

    @validator("priority")
    def validate_priority(cls, v):
        if not 1 <= v <= 5:
            raise ValueError("Priority must be between 1 and 5")
        return v

    def calculate_improvement_score(self, new_score: float) -> float:
        """Calculate improvement based on new score"""
        if self.current_score and new_score > self.current_score:
            return ((new_score - self.current_score) / self.current_score) * 100
        return 0.0


class Recommendation(Document, TimestampMixin):
    """
    Personalized recommendations for students
    """
    student: Link[Student]

    # Recommendation details
    type: str = Indexed()  # course, resource, activity, mentor
    title: str
    description: Optional[str] = None

    # Metadata
    priority: int = 1
    relevance_score: Optional[float] = None
    expected_impact: Optional[str] = None  # low, medium, high

    # Tracking
    is_viewed: bool = False
    is_accepted: bool = False
    viewed_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None

    # Outcome
    feedback: Optional[str] = None
    effectiveness_score: Optional[float] = None

    # Validity
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None

    class Settings:
        name = "recommendations"
        indexes = [
            [("student", 1), ("type", 1)],
            "priority",
        ]


class AnalysisHistory(Document, TimestampMixin):
    """
    Track all analysis runs for audit and improvement
    """
    student: Link[Student]

    # Analysis details
    analysis_type: str = Indexed()
    analysis_date: datetime = Field(default_factory=datetime.utcnow)

    # Results
    results: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)

    # Model information
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    model_accuracy: Optional[float] = None

    # Performance
    execution_time: Optional[float] = None  # in seconds
    data_points_analyzed: Optional[int] = None

    # Status
    status: str = "completed"  # pending, running, completed, failed
    error_message: Optional[str] = None

    class Settings:
        name = "analysis_history"
        indexes = [
            [("student", 1), ("analysis_date", -1)],
            "analysis_type",
        ]