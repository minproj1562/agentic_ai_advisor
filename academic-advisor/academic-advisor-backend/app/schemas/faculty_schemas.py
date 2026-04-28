# app/schemas/faculty_schemas.py
"""
Faculty Pydantic Schemas for API Request/Response
Complete with visibility controls and update support
"""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== Enums ====================

class FacultyStatusEnum(str, Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    INACTIVE = "inactive"
    PENDING_SETUP = "pending_setup"
    PENDING_REVIEW = "pending_review"  # For major changes needing approval


class FieldVisibility(str, Enum):
    PUBLIC = "public"      # Visible to all students
    DEPARTMENT = "department"  # Visible to same department only
    PRIVATE = "private"    # Not visible to students


class MeetingSlotType(str, Enum):
    RECURRING = "recurring"  # Weekly recurring
    ONE_TIME = "one_time"    # One-time slot


# ==================== Visibility Settings ====================

class VisibilitySettings(BaseModel):
    """Controls what students can see"""
    phone: FieldVisibility = FieldVisibility.PRIVATE
    email: FieldVisibility = FieldVisibility.PUBLIC
    office_location: FieldVisibility = FieldVisibility.PUBLIC
    personal_website: FieldVisibility = FieldVisibility.PUBLIC
    linkedin: FieldVisibility = FieldVisibility.PUBLIC
    google_scholar: FieldVisibility = FieldVisibility.PUBLIC


# ==================== Request Schemas ====================

class FacultyRegistrationRequest(BaseModel):
    """Initial faculty registration data"""
    email: EmailStr
    name: str
    department: str
    designation: str
    phone: Optional[str] = None
    institution: Optional[str] = None


class DegreeInput(BaseModel):
    """Input for degree/qualification"""
    degree: str
    field: str
    institution: str
    year: Optional[int] = None
    thesis_title: Optional[str] = None
    
    @field_validator('year')
    @classmethod
    def validate_year(cls, v):
        if v and (v < 1950 or v > datetime.now().year + 5):
            raise ValueError('Invalid graduation year')
        return v


# app/schemas/faculty_schemas.py

class MeetingSlotInput(BaseModel):
    """Input for adding meeting slot"""
    day: str  # "Monday", "Tuesday", etc.
    start_time: str  # "10:00"
    end_time: str    # "11:00"
    venue: str = ""  # ✅ FIX: Allow empty venue with default
    slot_type: MeetingSlotType = MeetingSlotType.RECURRING
    specific_date: Optional[str] = None
    
    @field_validator('day')
    @classmethod
    def validate_day(cls, v):
        valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        if v not in valid_days:
            raise ValueError(f'Day must be one of {valid_days}')
        return v
    
    # ✅ ADD: Validate time format
    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time(cls, v):
        import re
        if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError(f'Time must be in HH:MM format (e.g., 10:00)')
        return v
    
    # ✅ ADD: Validate end_time is after start_time
    @field_validator('end_time')
    @classmethod
    def validate_end_after_start(cls, v, info):
        if 'start_time' in info.data:
            start = info.data['start_time']
            if v <= start:
                raise ValueError('End time must be after start time')
        return v


class ProfileSetupRequest(BaseModel):
    """Request for completing faculty profile setup"""
    
    # Personal info
    name: Optional[str] = None  # Can update name from CV
    phone: Optional[str] = None
    photo_url: Optional[str] = None
    
    # Academic qualifications
    highest_degree: str
    specialization: str
    graduation_university: str
    graduation_year: Optional[int] = None
    all_degrees: List[DegreeInput] = Field(default_factory=list)
    
    # Current position
    designation: str
    department: str
    institution: str
    years_of_experience: int = 0
    joining_year: Optional[int] = None
    
    # Research
    primary_research_areas: List[str] = Field(default_factory=list, max_length=5)
    secondary_interests: List[str] = Field(default_factory=list)
    research_keywords: List[str] = Field(default_factory=list)
    
    # Teaching
    current_subjects: List[str] = Field(default_factory=list)
    past_subjects: List[str] = Field(default_factory=list)
    preferred_teaching_areas: List[str] = Field(default_factory=list)
    
    # Availability
    office_location: str
    office_hours: str  # "Mon-Wed 10:00-12:00"
    preferred_meeting_duration: int = 30  # minutes
    available_slots: List[MeetingSlotInput] = Field(default_factory=list)
    
    # Publications (optional)
    total_publications: int = 0
    journal_papers: int = 0
    conference_papers: int = 0
    notable_works: List[str] = Field(default_factory=list, max_length=5)
    h_index: Optional[int] = None
    
    # Others (dynamic)
    awards: List[str] = Field(default_factory=list)
    patents: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    industry_experience: Optional[str] = None
    professional_memberships: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    
    # Visibility settings
    visibility: Optional[VisibilitySettings] = None


class ProfileUpdateRequest(BaseModel):
    """
    Partial update to faculty profile.
    Only provided fields will be updated.
    """
    
    # Personal info updates
    name: Optional[str] = None
    phone: Optional[str] = None
    photo_url: Optional[str] = None
    
    # Academic updates
    highest_degree: Optional[str] = None
    specialization: Optional[str] = None
    graduation_university: Optional[str] = None
    graduation_year: Optional[int] = None
    all_degrees: Optional[List[DegreeInput]] = None
    
    # Position updates
    designation: Optional[str] = None
    department: Optional[str] = None
    institution: Optional[str] = None
    years_of_experience: Optional[int] = None
    joining_year: Optional[int] = None
    
    # Research updates
    primary_research_areas: Optional[List[str]] = None
    secondary_interests: Optional[List[str]] = None
    research_keywords: Optional[List[str]] = None
    
    # Teaching updates
    current_subjects: Optional[List[str]] = None
    past_subjects: Optional[List[str]] = None
    preferred_teaching_areas: Optional[List[str]] = None
    
    # Availability updates
    office_location: Optional[str] = None
    office_hours: Optional[str] = None
    preferred_meeting_duration: Optional[int] = None
    available_slots: Optional[List[MeetingSlotInput]] = None  # ✅ ADD THIS LINE
    
    # Publications updates
    total_publications: Optional[int] = None
    journal_papers: Optional[int] = None
    conference_papers: Optional[int] = None
    notable_works: Optional[List[str]] = None
    h_index: Optional[int] = None
    
    # Others
    awards: Optional[List[str]] = None
    patents: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    industry_experience: Optional[str] = None
    professional_memberships: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    
    # Visibility
    visibility: Optional[VisibilitySettings] = None


class AvailabilityUpdateRequest(BaseModel):
    """Request to update availability"""
    office_location: Optional[str] = None
    office_hours: Optional[str] = None
    available_slots: List[MeetingSlotInput] = Field(default_factory=list)
    preferred_meeting_duration: Optional[int] = None


class CVReuploadRequest(BaseModel):
    """Request for re-uploading CV with merge options"""
    merge_mode: str = "smart"  # "smart", "overwrite", "keep_existing"
    # smart: Only fill empty fields
    # overwrite: Replace all fields with CV data
    # keep_existing: Keep all existing, only add new info


# ==================== Response Schemas ====================

class CVUploadResponse(BaseModel):
    """Response after CV upload"""
    success: bool
    cv_url: Optional[str] = None
    file_name: str
    parsed_data: Dict[str, Any]
    suggested_profile: Dict[str, Any]
    extraction_warnings: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    message: str


class FacultyBasicInfo(BaseModel):
    """Basic faculty info for listings"""
    user_id: str
    name: str
    email: str
    department: str
    designation: str
    photo_url: Optional[str] = None
    specializations: List[str] = []
    profile_completeness: float = 0.0


class FacultyProfileResponse(BaseModel):
    """Full faculty profile response"""
    user_id: str
    name: str
    email: str
    department: str
    designation: str
    status: FacultyStatusEnum
    profile_setup_complete: bool
    profile_completeness: float
    
    # Uniform profile (if complete)
    uniform_profile: Optional[Dict[str, Any]] = None
    
    # CV info
    cv_url: Optional[str] = None
    cv_uploaded_at: Optional[datetime] = None
    cv_file_name: Optional[str] = None
    
    # Visibility settings
    visibility: Optional[VisibilitySettings] = None
    
    # Stats
    mentee_count: int = 0
    available_slots_count: int = 0
    
    created_at: datetime
    updated_at: datetime


class FacultyStudentView(BaseModel):
    """What students see when viewing a faculty profile"""
    user_id: str
    
    # Personal (limited based on visibility)
    name: str
    email: Optional[str] = None  # Based on visibility
    phone: Optional[str] = None  # Based on visibility
    photo_url: Optional[str] = None
    
    # Academic
    highest_degree: str
    specialization: str
    university: str
    
    # Position
    designation: str
    department: str
    institution: str
    years_of_experience: int
    
    # Research
    primary_research_areas: List[str]
    secondary_interests: List[str] = []
    research_keywords: List[str]
    
    # Teaching
    current_subjects: List[str]
    preferred_teaching_areas: List[str] = []
    
    # Availability (for meeting requests)
    office_location: Optional[str] = None  # Based on visibility
    office_hours: str
    available_slots: List[Dict[str, Any]]
    preferred_meeting_duration: int = 30
    
    # Publications (summary only)
    publication_count: int = 0
    notable_works: List[str] = []
    h_index: Optional[int] = None
    
    # Others (awards, certifications shown publicly)
    awards: List[str] = []
    certifications: List[str] = []
    languages: List[str] = []
    
    # Meta
    profile_completeness: float
    is_available_for_meetings: bool = True


class ProfileCompletenessResponse(BaseModel):
    """Detailed breakdown of profile completeness"""
    overall: float = Field(..., ge=0, le=100)
    sections: Dict[str, float] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class FacultyListResponse(BaseModel):
    """Response for faculty listing"""
    faculty: List[FacultyBasicInfo]
    total: int
    page: int
    page_size: int
    has_more: bool


class SetupStatusResponse(BaseModel):
    """Response for checking setup status"""
    profile_exists: bool
    setup_complete: bool
    needs_setup: bool  # True if should redirect to setup
    status: str
    cv_uploaded: bool
    profile_completeness: float
    missing_required: List[str] = Field(default_factory=list)


# ==================== Meeting Request Schemas ====================

class MeetingRequestCreate(BaseModel):
    """Student creates a meeting request"""
    faculty_id: str
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=20, max_length=1000)
    preferred_dates: List[str] = Field(default_factory=list)
    urgency: str = "normal"  # "low", "normal", "high"


class MeetingRequestResponse(BaseModel):
    """Meeting request details"""
    request_id: str
    student_id: str
    student_name: str
    faculty_id: str
    faculty_name: str
    subject: str
    message: str
    status: str
    created_at: datetime
    scheduled_meeting: Optional[Dict[str, Any]] = None
    faculty_response: Optional[str] = None


class MeetingScheduleRequest(BaseModel):
    """Faculty schedules a meeting (accepts request)"""
    date: str  # "2024-03-15"
    start_time: str  # "10:00"
    end_time: str    # "10:30"
    venue: str
    response_message: Optional[str] = None


class MeetingRejectRequest(BaseModel):
    """Faculty rejects a meeting request"""
    reason: str = Field(..., min_length=10, max_length=500)


class FacultyMeetingRequestsResponse(BaseModel):
    """List of meeting requests for faculty"""
    pending: List[MeetingRequestResponse]
    accepted: List[MeetingRequestResponse]
    past: List[MeetingRequestResponse]
    total_pending: int