#academic-advisor-backend/app/models/academic_record.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True)
    roll_number = Column(String(50), unique=True)
    name = Column(String(100))
    email = Column(String(100), unique=True)
    branch = Column(String(50))  # IT, COMP, EXTC, MECH, etc.
    admission_year = Column(Integer)  # 2021, 2022, etc.
    current_semester = Column(Integer)
    current_academic_year = Column(String(20))  # "2024-25"
    cgpa = Column(Float, default=0.0)
    total_credits_earned = Column(Integer, default=0)
    total_credits_required = Column(Integer, default=160)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    semester_records = relationship("SemesterRecord", back_populates="student", cascade="all, delete-orphan")
    subject_scores = relationship("SubjectScore", back_populates="student", cascade="all, delete-orphan")

class SemesterRecord(Base):
    __tablename__ = "semester_records"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(100), ForeignKey("student_profiles.user_id"))
    semester_number = Column(Integer)
    academic_year = Column(String(20))  # "2023-24"
    sgpa = Column(Float)
    credits_earned = Column(Integer)
    total_subjects = Column(Integer)
    passed_subjects = Column(Integer)
    failed_subjects = Column(Integer, default=0)
    attendance_percentage = Column(Float, default=75.0)
    is_completed = Column(Boolean, default=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("StudentProfile", back_populates="semester_records")
    subjects = relationship("SubjectScore", back_populates="semester", cascade="all, delete-orphan")

class SubjectScore(Base):
    __tablename__ = "subject_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(100), ForeignKey("student_profiles.user_id"))
    semester_id = Column(Integer, ForeignKey("semester_records.id"))
    subject_code = Column(String(50))
    subject_name = Column(String(200))
    credits = Column(Integer)
    
    # Score breakup
    internal_marks = Column(Float)  # Out of 20
    external_marks = Column(Float)  # Out of 80
    total_marks = Column(Float)     # Out of 100
    grade = Column(String(5))       # O, A+, A, B+, B, C, P, F
    grade_points = Column(Float)    # 10, 9, 8, 7, 6, 5, 4, 0
    
    # Additional details
    is_elective = Column(Boolean, default=False)
    is_practical = Column(Boolean, default=False)
    is_backlog = Column(Boolean, default=False)
    attempt_number = Column(Integer, default=1)
    
    weaknesses = Column(JSON)  # List of weak topics identified
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = relationship("StudentProfile", back_populates="subject_scores")
    semester = relationship("SemesterRecord", back_populates="subjects")