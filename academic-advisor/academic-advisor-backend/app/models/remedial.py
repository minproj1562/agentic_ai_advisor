# app/models/remedial.py
"""
Remedial Student Management Model
==================================
Faculty can add students as remedial for specific subjects,
track progress notes, and mark as resolved.
"""

from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class RemedialStatus(str, Enum):
    ACTIVE = "active"
    IMPROVING = "improving"
    RESOLVED = "resolved"


class ProgressNote(BaseModel):
    """A progress note added by faculty."""
    note: str
    added_by: str = ""  # faculty name
    added_at: datetime = Field(default_factory=datetime.utcnow)
    marks_change: Optional[float] = None  # e.g., +5 marks improvement


class RemedialEntry(Document):
    """Tracks a student under remedial monitoring for a subject."""
    faculty_id: Indexed(str)
    faculty_name: str = ""
    student_id: Indexed(str)
    student_name: str = ""
    student_roll: str = ""
    semester: int
    branch: str = "IT"
    subject: str
    reason: str = ""
    initial_marks: Optional[float] = None
    current_marks: Optional[float] = None
    target_marks: Optional[float] = None
    status: RemedialStatus = RemedialStatus.ACTIVE
    progress_notes: List[ProgressNote] = Field(default_factory=list)
    improvement_plan_id: Optional[str] = None  # Link to ImprovementPlan
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    class Settings:
        name = "remedial_entries"
        indexes = [
            "faculty_id",
            "student_id",
            [("faculty_id", 1), ("status", 1)],
            [("student_id", 1), ("status", 1)],
            [("subject", 1)],
        ]
