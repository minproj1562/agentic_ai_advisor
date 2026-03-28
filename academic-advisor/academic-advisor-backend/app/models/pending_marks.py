#academic-advisor/academic-advisor-backend/app/models/pending_marks.py
from beanie import Document
from typing import List, Optional
from datetime import datetime
from pydantic import Field
from app.models.student_profile import SubjectScore

class PendingStudentMarks(Document):
    """Marks data for students who haven't registered yet"""
    roll_number: str = Field(..., index=True)
    seat_number: Optional[str] = Field(None, index=True)  # Added seat number
    student_name: str
    branch: str
    admission_year: int
    semester_number: int
    academic_year: str
    subjects: List[SubjectScore] = []
    sgpa: float = 0.0
    total_credits: int = 0
    credits_earned: int = 0
    uploaded_by: str  # Admin who uploaded
    upload_timestamp: datetime = Field(default_factory=datetime.now)
    linked_to_profile: bool = False
    linked_user_id: Optional[str] = None
    
    class Settings:
        name = "pending_student_marks"
        indexes = [
            "roll_number",
            "seat_number",
            "branch",
            "semester_number",
            [("roll_number", 1), ("semester_number", 1)],
            [("seat_number", 1), ("semester_number", 1)]
        ]