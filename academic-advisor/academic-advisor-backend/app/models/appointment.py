#academic-advisor-backend/app/models/appointment.py
from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SlotType(str, Enum):
    REGULAR = "Regular"
    EMERGENCY = "Emergency"
    GROUP = "Group"

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

class AppointmentSlot(Document):
    faculty_id: Indexed(str)  # Firebase UID of faculty
    student_id: Optional[str] = None  # Firebase UID of student if booked
    
    # Slot details
    date: datetime
    start_time: str  # Format: "HH:MM"
    end_time: str    # Format: "HH:MM"
    type: SlotType = SlotType.REGULAR
    status: SlotStatus = SlotStatus.AVAILABLE
    
    # Booking details
    topic: Optional[str] = None
    description: Optional[str] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None  # "daily", "weekly", "biweekly"
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    booked_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    class Settings:
        name = "appointment_slots"
        indexes = [
            "faculty_id",
            "date",
            "status",
            [("faculty_id", 1), ("date", 1)],
            [("faculty_id", 1), ("status", 1)]
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "faculty_id": "faculty_firebase_uid",
                "date": "2024-01-15T00:00:00",
                "start_time": "14:00",
                "end_time": "15:00",
                "type": "Regular",
                "status": "available"
            }
        }

class AppointmentBooking(Document):
    slot_id: Indexed(str)  # References AppointmentSlot.id
    faculty_id: Indexed(str)
    student_id: Indexed(str)
    
    # Booking details
    topic: str
    description: Optional[str] = None
    status: BookingStatus = BookingStatus.CONFIRMED
    
    # Meeting details
    meeting_link: Optional[str] = None
    meeting_platform: Optional[str] = None  # "google_meet", "teams", "zoom"
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    cancelled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Settings:
        name = "appointment_bookings"
        indexes = [
            "slot_id",
            "faculty_id", 
            "student_id",
            "status",
            [("faculty_id", 1), ("date", 1)]
        ]