# app/models/meeting_request.py
"""
Meeting Request Model for Faculty-Student In-Person Meetings
"""

from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class MeetingRequestStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class ScheduledMeeting(BaseModel):
    """Scheduled meeting details - In-person only"""
    date: str  # ISO format date
    start_time: str  # "10:00"
    end_time: str    # "10:30"
    venue: str       # In-college location (e.g., "Room 301, CS Building")
    additional_notes: Optional[str] = None


class MeetingRequest(Document):
    """
    Meeting Request Document
    Students request meetings, faculty accepts/rejects and schedules
    """
    
    # Unique request ID
    request_id: Indexed(str, unique=True)
    
    # Student info
    student_id: Indexed(str)
    student_name: str
    student_email: str
    student_department: Optional[str] = None
    student_semester: Optional[int] = None
    
    # Faculty info
    faculty_id: Indexed(str)
    faculty_name: str
    
    # Request details
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=10, max_length=1000)
    urgency: str = "normal"  # "low", "normal", "high"
    
    # Status
    status: MeetingRequestStatus = MeetingRequestStatus.PENDING
    
    # Scheduled meeting (if accepted)
    scheduled_meeting: Optional[ScheduledMeeting] = None
    
    # Faculty response
    faculty_response: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "meeting_requests"
        indexes = [
            "request_id",
            "student_id",
            "faculty_id",
            "status",
            [("faculty_id", 1), ("status", 1)],
            [("student_id", 1), ("created_at", -1)],
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_12345",
                "student_id": "student_uid",
                "student_name": "John Doe",
                "student_email": "john@example.com",
                "faculty_id": "faculty_uid",
                "faculty_name": "Dr. Smith",
                "subject": "Discussion about ML project",
                "message": "I need guidance on my final year project...",
                "urgency": "normal",
                "status": "pending"
            }
        }