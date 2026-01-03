# app/models/performance.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class SubjectScore(BaseModel):
    subject_code: str
    subject_name: str
    credits: int
    marks_obtained: float
    total_marks: float
    grade: str
    grade_points: float

class AssignmentScore(BaseModel):
    assignment_id: str
    title: str
    marks_obtained: float
    total_marks: float
    submission_date: datetime
    feedback: Optional[str] = None

class QuizScore(BaseModel):
    quiz_id: str
    title: str
    score: float
    total_score: float
    attempted_date: datetime
    topics: List[str]

class ExamScore(BaseModel):
    exam_id: str
    exam_type: str  # midterm, final, etc.
    score: float
    total_score: float
    exam_date: datetime
    subjects: List[SubjectScore]

class PerformanceMetrics(BaseModel):
    student_id: str
    semester: int
    academic_year: str
    
    # Academic Scores
    subjects: List[SubjectScore]
    sgpa: float = Field(..., ge=0, le=10)
    cgpa: float = Field(..., ge=0, le=10)
    
    # Detailed Assessments
    assignments: List[AssignmentScore]
    quizzes: List[QuizScore]
    exams: List[ExamScore]
    
    # Attendance
    total_classes: int
    attended_classes: int
    attendance_percentage: float
    
    # Participation
    class_participation_score: float = Field(..., ge=0, le=100)
    extra_curricular_points: float = Field(..., ge=0, le=100)
    
    # Behavioral Metrics
    library_hours: float
    lab_hours: float
    project_submissions: int
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PerformanceTrend(BaseModel):
    student_id: str
    
    # Trend Analysis
    sgpa_trend: List[float]  # Last 5 semesters
    cgpa_trend: List[float]
    attendance_trend: List[float]
    
    # Statistical Metrics
    sgpa_mean: float
    sgpa_std: float
    performance_consistency: float  # 0-1 scale
    
    # Predictions
    predicted_next_sgpa: float
    predicted_final_cgpa: float
    prediction_confidence: float
    
    # Risk Indicators
    failing_risk: float  # 0-1 scale
    dropout_risk: float  # 0-1 scale
    improvement_potential: float  # 0-1 scale
    
    analysis_date: datetime = Field(default_factory=datetime.utcnow)

class WeaknessAnalysis(BaseModel):
    student_id: str
    
    weak_subjects: List[Dict[str, Any]]  # {subject, score, topics, resources}
    weak_topics: List[Dict[str, Any]]  # {topic, subject, difficulty_score}
    
    skill_gaps: List[str]
    knowledge_gaps: List[str]
    
    recommended_tutorials: List[Dict[str, Any]]
    recommended_mentors: List[str]
    recommended_study_hours: int
    
    analysis_confidence: float
    last_analyzed: datetime = Field(default_factory=datetime.utcnow)