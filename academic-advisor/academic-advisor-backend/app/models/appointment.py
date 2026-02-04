# app/models/appointment.py
"""
Appointment Model - Updated for In-Person Only meetings
"""

from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SlotType(str, Enum):
    REGULAR = "regular"
    OFFICE_HOURS = "office_hours"
    BY_REQUEST = "by_request"  # Created in response to a meeting request


class SlotStatus(str, Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class AppointmentSlot(Document):
    """Appointment slot created by faculty"""
    
    faculty_id: Indexed(str)  # Firebase UID
    student_id: Optional[str] = None  # Firebase UID if booked
    
    # Slot details
    date: datetime
    start_time: str  # "HH:MM"
    end_time: str    # "HH:MM"
    type: SlotType = SlotType.REGULAR
    status: SlotStatus = SlotStatus.AVAILABLE
    
    # ============== UPDATED: In-Person Only ==============
    venue: str  # Required - office/room location
    building: Optional[str] = None  # Optional building name
    room_number: Optional[str] = None  # Optional room number
    
    # REMOVED: meeting_link, meeting_platform (no virtual meetings)
    
    # Booking details
    topic: Optional[str] = None
    description: Optional[str] = None
    
    # Link to meeting request (if created from request)
    meeting_request_id: Optional[str] = None
    
    # Recurrence
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None  # "weekly", "biweekly"
    parent_slot_id: Optional[str] = None  # For recurring slots
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    booked_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None  # "student" or "faculty"
    cancellation_reason: Optional[str] = None
    
    class Settings:
        name = "appointment_slots"
        indexes = [
            "faculty_id",
            "student_id",
            "date",
            "status",
            "meeting_request_id",
            [("faculty_id", 1), ("date", 1)],
            [("faculty_id", 1), ("status", 1)],
            [("date", 1), ("status", 1)],
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "faculty_id": "faculty_firebase_uid",
                "date": "2024-01-15T00:00:00",
                "start_time": "14:00",
                "end_time": "14:30",
                "venue": "Room 301, CS Building",
                "type": "regular",
                "status": "available"
            }
        }


class AppointmentBooking(Document):
    """Booking record when a slot is booked"""
    
    slot_id: Indexed(str)  # References AppointmentSlot
    faculty_id: Indexed(str)
    student_id: Indexed(str)
    
    # Booking details
    topic: str
    description: Optional[str] = None
    status: BookingStatus = BookingStatus.CONFIRMED
    
    # Meeting location (copied from slot for easy access)
    venue: str
    date: datetime
    start_time: str
    end_time: str
    
    # Link to meeting request (if applicable)
    meeting_request_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    
    # Feedback
    student_attended: Optional[bool] = None
    faculty_notes: Optional[str] = None
    
    class Settings:
        name = "appointment_bookings"
        indexes = [
            "slot_id",
            "faculty_id",
            "student_id",
            "status",
            "meeting_request_id",
            "date",
            [("faculty_id", 1), ("date", 1)],
            [("student_id", 1), ("date", 1)],
        ]