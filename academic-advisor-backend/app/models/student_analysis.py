"""
SQLAlchemy Models for Student Analysis
Enterprise-level ORM with indexing, relationships, and audit trails
"""

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, ForeignKey, 
    Boolean, JSON, Text, Index, UniqueConstraint, CheckConstraint,
    event, func
)
from sqlalchemy.orm import relationship, validates, Session
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import hashlib

Base = declarative_base()

class TimestampMixin:
    """Mixin for automatic timestamp management"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
class AuditMixin:
    """Mixin for audit trail"""
    created_by = Column(String(50))
    updated_by = Column(String(50))
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)

class Student(Base, TimestampMixin, AuditMixin):
    """
    Student model with comprehensive profile and performance tracking
    """
    __tablename__ = 'students'
    
    # Primary fields
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(15))
    
    # Academic details
    department = Column(String(10), nullable=False, index=True)
    batch = Column(Integer, nullable=False, index=True)
    current_semester = Column(Integer, nullable=False)
    admission_year = Column(Integer, nullable=False)
    
    # Performance metrics
    cgpa = Column(Float, default=0.0, index=True)
    total_credits = Column(Integer, default=0)
    attendance_percentage = Column(Float, default=0.0)
    
    # Profile data
    profile_image = Column(Text)
    linkedin_profile = Column(String(200))
    github_profile = Column(String(200))
    skills = Column(JSON, default=list)
    interests = Column(JSON, default=list)
    
    # Status flags
    is_active = Column(Boolean, default=True, index=True)
    is_graduated = Column(Boolean, default=False)
    has_warnings = Column(Boolean, default=False)
    risk_level = Column(String(20), default='low')  # low, medium, high
    
    # Metadata
    metadata_json = Column(JSON, default=dict)
    last_analysis_date = Column(DateTime)
    
    # Relationships
    performances = relationship("Performance", back_populates="student", 
                                cascade="all, delete-orphan",
                                lazy='dynamic')
    weaknesses = relationship("Weakness", back_populates="student",
                             cascade="all, delete-orphan",
                             lazy='dynamic')
    recommendations = relationship("Recommendation", back_populates="student",
                                  cascade="all, delete-orphan")
    analysis_history = relationship("AnalysisHistory", back_populates="student",
                                   cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_student_dept_batch', 'department', 'batch'),
        Index('idx_student_cgpa_risk', 'cgpa', 'risk_level'),
        CheckConstraint('cgpa >= 0 AND cgpa <= 10', name='check_cgpa_range'),
        CheckConstraint('current_semester >= 1 AND current_semester <= 10', name='check_semester_range'),
    )
    
    # Validations
    @validates('email')
    def validate_email(self, key, email):
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError("Invalid email format")
        return email.lower()
    
    @validates('cgpa')
    def validate_cgpa(self, key, cgpa):
        if not 0 <= cgpa <= 10:
            raise ValueError("CGPA must be between 0 and 10")
        return round(cgpa, 2)
    
    # Hybrid properties for computed fields
    @hybrid_property
    def full_profile_score(self):
        """Calculate profile completeness score"""
        score = 0
        if self.profile_image: score += 10
        if self.linkedin_profile: score += 15
        if self.github_profile: score += 15
        if len(self.skills) > 0: score += 30
        if len(self.interests) > 0: score += 10
        if self.cgpa > 7: score += 20
        return score
    
    @hybrid_property
    def years_in_college(self):
        """Calculate years spent in college"""
        return datetime.utcnow().year - self.admission_year
    
    @hybrid_property
    def graduation_year(self):
        """Expected graduation year"""
        return self.admission_year + 4
    
    def calculate_risk_level(self) -> str:
        """Calculate student's academic risk level"""
        if self.cgpa < 5.0 or self.attendance_percentage < 65:
            return 'high'
        elif self.cgpa < 6.5 or self.attendance_percentage < 75:
            return 'medium'
        return 'low'
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert model to dictionary"""
        data = {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'email': self.email if include_sensitive else None,
            'department': self.department,
            'batch': self.batch,
            'current_semester': self.current_semester,
            'cgpa': self.cgpa,
            'attendance_percentage': self.attendance_percentage,
            'risk_level': self.risk_level,
            'profile_score': self.full_profile_score,
            'is_active': self.is_active
        }
        return data
    
    def __repr__(self):
        return f"<Student {self.student_id}: {self.name}>"

class Performance(Base, TimestampMixin):
    """
    Semester-wise performance tracking
    """
    __tablename__ = 'performances'
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(50), ForeignKey('students.id'), nullable=False)
    
    # Semester details
    semester = Column(Integer, nullable=False)
    academic_year = Column(String(10), nullable=False)  # e.g., "2023-24"
    
    # Performance metrics
    sgpa = Column(Float, nullable=False)
    credits_earned = Column(Integer, default=0)
    credits_registered = Column(Integer, default=0)
    
    # Subject-wise performance
    subjects = Column(JSON, default=list)  # List of subject performances
    grades = Column(JSON, default=dict)    # Subject code to grade mapping
    
    # Attendance and participation
    attendance_percentage = Column(Float, default=0.0)
    assignments_completed = Column(Integer, default=0)
    assignments_total = Column(Integer, default=0)
    
    # Extra-curricular
    events_participated = Column(Integer, default=0)
    achievements = Column(JSON, default=list)
    
    # Analysis results
    strengths = Column(JSON, default=list)
    weaknesses = Column(JSON, default=list)
    improvement_areas = Column(JSON, default=list)
    
    # Predictive metrics
    predicted_sgpa = Column(Float)
    confidence_score = Column(Float)
    
    # Relationships
    student = relationship("Student", back_populates="performances")
    
    # Indexes
    __table_args__ = (
        Index('idx_performance_student_sem', 'student_id', 'semester'),
        UniqueConstraint('student_id', 'semester', 'academic_year', name='unique_student_semester'),
        CheckConstraint('sgpa >= 0 AND sgpa <= 10', name='check_sgpa_range'),
    )
    
    @validates('sgpa')
    def validate_sgpa(self, key, sgpa):
        if not 0 <= sgpa <= 10:
            raise ValueError("SGPA must be between 0 and 10")
        return round(sgpa, 2)
    
    @hybrid_property
    def completion_rate(self):
        """Calculate assignment completion rate"""
        if self.assignments_total == 0:
            return 0
        return (self.assignments_completed / self.assignments_total) * 100
    
    @hybrid_property
    def credit_completion_rate(self):
        """Calculate credit completion rate"""
        if self.credits_registered == 0:
            return 0
        return (self.credits_earned / self.credits_registered) * 100
    
    def calculate_grade_distribution(self) -> Dict[str, int]:
        """Calculate distribution of grades"""
        distribution = {}
        for grade in self.grades.values():
            distribution[grade] = distribution.get(grade, 0) + 1
        return distribution
    
    def __repr__(self):
        return f"<Performance {self.student_id} - Sem {self.semester}: {self.sgpa}>"

class Weakness(Base, TimestampMixin):
    """
    Identified weaknesses and improvement areas
    """
    __tablename__ = 'weaknesses'
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(50), ForeignKey('students.id'), nullable=False)
    
    # Weakness details
    subject = Column(String(100), nullable=False)
    topic = Column(String(200))
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Metrics
    current_score = Column(Float)
    expected_score = Column(Float)
    gap_percentage = Column(Float)
    
    # Analysis
    identified_date = Column(DateTime, default=datetime.utcnow)
    last_reviewed = Column(DateTime)
    improvement_rate = Column(Float)  # Percentage improvement over time
    
    # Recommendations
    recommended_resources = Column(JSON, default=list)
    recommended_actions = Column(JSON, default=list)
    
    # Status
    status = Column(String(20), default='active')  # active, improving, resolved
    priority = Column(Integer, default=1)  # 1-5, 5 being highest
    
    # ML metadata
    ml_confidence = Column(Float)
    ml_model_version = Column(String(20))
    
    # Relationships
    student = relationship("Student", back_populates="weaknesses")
    
    # Indexes
    __table_args__ = (
        Index('idx_weakness_student_subject', 'student_id', 'subject'),
        Index('idx_weakness_severity_status', 'severity', 'status'),
    )
    
    @validates('severity')
    def validate_severity(self, key, severity):
        valid_severities = ['low', 'medium', 'high', 'critical']
        if severity not in valid_severities:
            raise ValueError(f"Severity must be one of {valid_severities}")
        return severity
    
    def calculate_improvement_score(self, new_score: float) -> float:
        """Calculate improvement based on new score"""
        if self.current_score and new_score > self.current_score:
            return ((new_score - self.current_score) / self.current_score) * 100
        return 0.0
    
    def __repr__(self):
        return f"<Weakness {self.student_id} - {self.subject}: {self.severity}>"

class Recommendation(Base, TimestampMixin):
    """
    Personalized recommendations for students
    """
    __tablename__ = 'recommendations'
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(50), ForeignKey('students.id'), nullable=False)
    
    # Recommendation details
    type = Column(String(50), nullable=False)  # course, resource, activity, mentor
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Metadata
    priority = Column(Integer, default=1)
    relevance_score = Column(Float)
    expected_impact = Column(String(20))  # low, medium, high
    
    # Tracking
    is_viewed = Column(Boolean, default=False)
    is_accepted = Column(Boolean, default=False)
    viewed_at = Column(DateTime)
    accepted_at = Column(DateTime)
    
    # Outcome
    feedback = Column(Text)
    effectiveness_score = Column(Float)
    
    # Validity
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    
    # Relationships
    student = relationship("Student", back_populates="recommendations")
    
    # Indexes
    __table_args__ = (
        Index('idx_recommendation_student_type', 'student_id', 'type'),
        Index('idx_recommendation_priority', 'priority'),
    )
    
    def __repr__(self):
        return f"<Recommendation {self.student_id} - {self.type}: {self.title}>"

class AnalysisHistory(Base, TimestampMixin):
    """
    Track all analysis runs for audit and improvement
    """
    __tablename__ = 'analysis_history'
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(50), ForeignKey('students.id'), nullable=False)
    
    # Analysis details
    analysis_type = Column(String(50), nullable=False)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    
    # Results
    results = Column(JSON, default=dict)
    metrics = Column(JSON, default=dict)
    
    # Model information
    model_name = Column(String(50))
    model_version = Column(String(20))
    model_accuracy = Column(Float)
    
    # Performance
    execution_time = Column(Float)  # in seconds
    data_points_analyzed = Column(Integer)
    
    # Status
    status = Column(String(20), default='completed')  # pending, running, completed, failed
    error_message = Column(Text)
    
    # Relationships
    student = relationship("Student", back_populates="analysis_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_analysis_history_student_date', 'student_id', 'analysis_date'),
        Index('idx_analysis_history_type', 'analysis_type'),
    )
    
    def __repr__(self):
        return f"<AnalysisHistory {self.student_id} - {self.analysis_type}: {self.analysis_date}>"

# Event listeners for automatic updates
@event.listens_for(Student, 'before_update')
def update_student_risk_level(mapper, connection, target):
    """Automatically update risk level before save"""
    target.risk_level = target.calculate_risk_level()
    target.version += 1

@event.listens_for(Performance, 'after_insert')
def update_student_cgpa(mapper, connection, target):
    """Update student CGPA after new performance entry"""
    # This would trigger a recalculation of overall CGPA
    pass

# Create indexes programmatically
def create_indexes(engine):
    """Create additional indexes for performance optimization"""
    from sqlalchemy import text
    
    with engine.connect() as conn:
        # Full-text search index on student name
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_student_name_fulltext ON students USING gin(to_tsvector('english', name))"))
        
        # Composite indexes for common queries
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_student_active_dept ON students(is_active, department) WHERE is_deleted = false"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_performance_high_achievers ON performances(sgpa) WHERE sgpa > 8.0"))