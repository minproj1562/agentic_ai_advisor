# academic-advisor-backend/app/models/mentorship.py
from typing import List, Optional, Dict, Any
from beanie import Document
from pydantic import Field, validator
from datetime import datetime, time
from enum import Enum
import uuid

class MentorshipSlotType(str, Enum):
    ONE_ON_ONE = "One-on-One"
    GROUP = "Group"
    EMERGENCY = "Emergency"

class MentorshipSessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class SessionTopic(str, Enum):
    ACADEMIC_ADVICE = "academic_advice"
    CAREER_GUIDANCE = "career_guidance"
    RESEARCH_SUPPORT = "research_support"
    PROJECT_GUIDANCE = "project_guidance"
    PERSONAL_DEVELOPMENT = "personal_development"
    TECHNICAL_SKILLS = "technical_skills"
    OTHER = "other"

class AvailabilityDay(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

class FacultyMentorshipSettings(Document):
    """Faculty mentorship preferences and settings"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    faculty_id: str = Field(..., index=True)
    
    # Availability settings
    available_days: List[AvailabilityDay] = Field(default_factory=list)
    working_hours_start: str = Field(default="09:00")
    working_hours_end: str = Field(default="17:00")
    
    # Session preferences
    default_session_duration: int = Field(default=30, description="Default duration in minutes")
    max_sessions_per_day: int = Field(default=8)
    min_advance_booking_hours: int = Field(default=24)
    max_advance_booking_days: int = Field(default=30)
    
    # Session types offered
    offered_session_types: List[MentorshipSlotType] = Field(
        default_factory=lambda: [MentorshipSlotType.ONE_ON_ONE, MentorshipSlotType.GROUP]
    )
    
    # Topics expertise
    expertise_topics: List[SessionTopic] = Field(default_factory=list)
    custom_topics: List[str] = Field(default_factory=list)
    
    # Virtual meeting preferences
    default_meeting_platform: Optional[str] = Field(None)
    meeting_links: Dict[str, str] = Field(default_factory=dict)
    
    # Notification preferences
    email_notifications: bool = Field(default=True)
    sms_notifications: bool = Field(default=False)
    reminder_before_hours: List[int] = Field(default_factory=lambda: [24, 1])
    
    # Auto-confirmation settings
    auto_confirm_sessions: bool = Field(default=False)
    require_student_preparation: bool = Field(default=True)
    
    # Maximum mentees
    max_active_mentees: Optional[int] = Field(None)
    current_mentee_count: int = Field(default=0)
    
    # Office location
    office_location: Optional[str] = Field(None)
    virtual_office_hours: bool = Field(default=True)
    
    # Additional preferences
    preferred_languages: List[str] = Field(default_factory=lambda: ["English"])
    special_accommodations: List[str] = Field(default_factory=list)
    
    # Metadata
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "faculty_mentorship_settings"
        indexes = [
            "faculty_id",
            "is_active"
        ]
    
    @validator('working_hours_end')
    def validate_working_hours(cls, v, values):
        if 'working_hours_start' in values:
            try:
                start = datetime.strptime(values['working_hours_start'], '%H:%M').time()
                end = datetime.strptime(v, '%H:%M').time()
                if end <= start:
                    raise ValueError('Working hours end must be after start')
            except ValueError:
                raise ValueError('Working hours must be in HH:MM format')
        return v

class MentorshipSlot(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    faculty_id: str = Field(..., index=True)
    student_id: Optional[str] = Field(None, index=True)
    
    # Session details
    date: datetime = Field(..., description="Date of the session")
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")
    duration: int = Field(..., description="Duration in minutes")
    
    # Session type and details
    slot_type: MentorshipSlotType = Field(default=MentorshipSlotType.ONE_ON_ONE)
    topic: Optional[SessionTopic] = Field(default=SessionTopic.ACADEMIC_ADVICE)
    custom_topic: Optional[str] = Field(None)
    
    # Location and mode
    location: Optional[str] = Field(None)
    is_virtual: bool = Field(default=True)
    meeting_link: Optional[str] = Field(None)
    
    # Status and booking
    is_booked: bool = Field(default=False)
    status: MentorshipSessionStatus = Field(default=MentorshipSessionStatus.SCHEDULED)
    
    # Additional metadata
    title: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    max_participants: int = Field(default=1)
    current_participants: int = Field(default=0)
    
    # Student information (if booked)
    student_name: Optional[str] = Field(None)
    student_roll_number: Optional[str] = Field(None)
    student_concern: Optional[str] = Field(None)
    
    # Faculty notes
    faculty_notes: Optional[str] = Field(None)
    agenda: List[str] = Field(default_factory=list)
    
    # Feedback and ratings
    rating: Optional[float] = Field(None, ge=1, le=5)
    student_feedback: Optional[str] = Field(None)
    faculty_feedback: Optional[str] = Field(None)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    booked_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    
    class Settings:
        name = "mentorship_slots"
        indexes = [
            "faculty_id",
            "student_id",
            "date",
            "status",
            "slot_type",
            "is_booked"
        ]
    
    @validator('end_time')
    def validate_times(cls, v, values):
        if 'start_time' in values:
            try:
                start = datetime.strptime(values['start_time'], '%H:%M').time()
                end = datetime.strptime(v, '%H:%M').time()
                if end <= start:
                    raise ValueError('End time must be after start time')
            except ValueError:
                raise ValueError('Times must be in HH:MM format')
        return v

class MentorshipSession(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slot_id: str = Field(..., index=True)
    faculty_id: str = Field(..., index=True)
    student_id: str = Field(..., index=True)
    
    # Session details
    date: datetime = Field(..., description="Date of the session")
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")
    duration: int = Field(..., description="Duration in minutes")
    
    # Session type and topic
    slot_type: MentorshipSlotType = Field(default=MentorshipSlotType.ONE_ON_ONE)
    topic: SessionTopic = Field(default=SessionTopic.ACADEMIC_ADVICE)
    custom_topic: Optional[str] = Field(None)
    
    # Location and mode
    location: Optional[str] = Field(None)
    is_virtual: bool = Field(default=True)
    meeting_link: Optional[str] = Field(None)
    
    # Status
    status: MentorshipSessionStatus = Field(default=MentorshipSessionStatus.SCHEDULED)
    
    # Participant information
    student_name: str = Field(...)
    student_roll_number: str = Field(...)
    faculty_name: str = Field(...)
    
    # Session content
    title: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    agenda: List[str] = Field(default_factory=list)
    discussion_points: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    
    # Student inputs
    student_concern: Optional[str] = Field(None)
    student_preparation: Optional[str] = Field(None)
    
    # Faculty inputs
    faculty_notes: Optional[str] = Field(None)
    faculty_preparation: Optional[str] = Field(None)
    
    # Follow-up
    follow_up_required: bool = Field(default=False)
    follow_up_date: Optional[datetime] = Field(None)
    follow_up_actions: List[str] = Field(default_factory=list)
    
    # Feedback and evaluation
    student_rating: Optional[float] = Field(None, ge=1, le=5)
    student_feedback: Optional[str] = Field(None)
    faculty_rating: Optional[float] = Field(None, ge=1, le=5)
    faculty_feedback: Optional[str] = Field(None)
    
    # Outcomes
    outcomes_achieved: List[str] = Field(default_factory=list)
    improvements_suggested: List[str] = Field(default_factory=list)
    resources_provided: List[str] = Field(default_factory=list)
    
    # Attendance
    student_attended: Optional[bool] = Field(None)
    faculty_attended: Optional[bool] = Field(None)
    attendance_notes: Optional[str] = Field(None)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    booked_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)
    cancelled_at: Optional[datetime] = Field(None)
    
    class Settings:
        name = "mentorship_sessions"
        indexes = [
            "faculty_id",
            "student_id", 
            "date",
            "status",
            "slot_type",
            "topic"
        ]

    # Add this to academic-advisor-backend/app/models/mentorship.py after the other models

class MentorshipStatistics(Document):
    """Mentorship statistics and analytics"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    faculty_id: str = Field(..., index=True)
    
    # Session statistics
    total_sessions: int = Field(default=0)
    completed_sessions: int = Field(default=0)
    cancelled_sessions: int = Field(default=0)
    no_show_sessions: int = Field(default=0)
    
    # Time statistics
    total_session_hours: float = Field(default=0.0)
    avg_session_duration: float = Field(default=0.0)
    
    # Rating statistics
    avg_student_rating: float = Field(default=0.0)
    avg_faculty_rating: float = Field(default=0.0)
    total_ratings: int = Field(default=0)
    
    # Topic distribution
    topic_distribution: Dict[SessionTopic, int] = Field(default_factory=dict)
    
    # Monthly trends
    monthly_sessions: Dict[str, int] = Field(default_factory=dict)  # Format: "YYYY-MM": count
    monthly_hours: Dict[str, float] = Field(default_factory=dict)   # Format: "YYYY-MM": hours
    
    # Student engagement
    unique_students: int = Field(default=0)
    returning_students: int = Field(default=0)
    student_engagement_rate: float = Field(default=0.0)
    
    # Response metrics
    avg_response_time_hours: float = Field(default=0.0)
    booking_confirmation_rate: float = Field(default=0.0)
    
    # Performance indicators
    student_satisfaction_score: float = Field(default=0.0)
    faculty_engagement_score: float = Field(default=0.0)
    overall_mentorship_health: float = Field(default=0.0)
    
    # Timestamps
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    period_start: datetime = Field(...)
    period_end: datetime = Field(...)
    
    class Settings:
        name = "mentorship_statistics"
        indexes = [
            "faculty_id",
            "calculated_at",
            [("faculty_id", 1), ("calculated_at", -1)]
        ]