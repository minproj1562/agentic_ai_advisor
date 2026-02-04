# app/models/faculty.py
"""
Faculty Model with Uniform Profile Structure
Supports CV parsing and standardized profile display
"""

from beanie import Document, Indexed
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FacultyStatus(str, Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    INACTIVE = "inactive"
    PENDING_SETUP = "pending_setup"  # New status for profile setup


# ==================== Uniform Profile Sub-Models ====================

class PersonalInfo(BaseModel):
    """Personal information - Always shown to students"""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    photo_url: Optional[str] = None


class Degree(BaseModel):
    """Individual degree/qualification"""
    degree: str  # PhD, M.Tech, B.Tech, etc.
    field: str  # Computer Science, etc.
    institution: str
    year: Optional[int] = None
    thesis_title: Optional[str] = None


class AcademicQualifications(BaseModel):
    """Academic qualifications - Always shown"""
    highest_degree: str  # PhD, Master's, Bachelor's
    specialization: str
    university: str
    graduation_year: Optional[int] = None
    all_degrees: List[Degree] = Field(default_factory=list)


class CurrentPosition(BaseModel):
    """Current position details - Always shown"""
    designation: str  # Professor, Associate Professor, Assistant Professor
    department: str
    institution: str
    years_of_experience: int = 0
    joining_year: Optional[int] = None


class ResearchExpertise(BaseModel):
    """Research areas and expertise - Always shown"""
    primary_areas: List[str] = Field(default_factory=list, max_length=5)
    secondary_interests: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class TeachingInfo(BaseModel):
    """Teaching information - Always shown"""
    current_subjects: List[str] = Field(default_factory=list)
    past_subjects: List[str] = Field(default_factory=list)
    preferred_areas: List[str] = Field(default_factory=list)


class MeetingSlot(BaseModel):
    """Available meeting slot"""
    day: str  # Monday, Tuesday, etc.
    start_time: str  # "10:00"
    end_time: str  # "11:00"
    venue: str  # Office location for in-person meetings
    is_available: bool = True

class VisibilitySettings(BaseModel):
    """Controls what information is visible to students"""
    phone: str = "private"  # "public", "department", "private"
    email: str = "public"
    office_location: str = "public"
    personal_website: str = "public"
    linkedin: str = "public"
    google_scholar: str = "public"

class FacultyAvailability(BaseModel):
    """Availability for meetings - Always shown"""
    office_location: str
    office_hours: str  # "Mon-Wed 10:00-12:00"
    available_slots: List[MeetingSlot] = Field(default_factory=list)
    preferred_meeting_duration: int = 30  # minutes


class PublicationSummary(BaseModel):
    """Publication summary - Shown if count > 0"""
    total_count: int = 0
    journal_papers: int = 0
    conference_papers: int = 0
    books_chapters: int = 0
    notable_works: List[str] = Field(default_factory=list, max_length=5)  # Top 5 titles
    h_index: Optional[int] = None
    citations: Optional[int] = None


# Update UniformFacultyProfile to include visibility
class UniformFacultyProfile(BaseModel):
    """
    Uniform structure for all faculty profiles
    This is what students see when viewing faculty
    """
    # Required sections (always shown)
    personal_info: PersonalInfo
    academic_qualifications: AcademicQualifications
    current_position: CurrentPosition
    research_expertise: ResearchExpertise
    teaching: TeachingInfo
    availability: FacultyAvailability
    
    # Optional sections (shown if data exists)
    publications: Optional[PublicationSummary] = None
    
    # Dynamic section for unique attributes
    others: Dict[str, Any] = Field(default_factory=dict)
    
    # NEW: Visibility controls
    visibility: Optional[VisibilitySettings] = None
    
    # Metadata
    profile_completeness: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# Legacy models for backward compatibility
class Qualification(BaseModel):
    degree: str
    field: str
    institution: str
    year: Optional[int] = None


class ResearchArea(BaseModel):
    name: str
    keywords: List[str] = Field(default_factory=list)


class Publication(BaseModel):
    title: str
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    authors: List[str] = Field(default_factory=list)


# ==================== Main Faculty Document ====================

class Faculty(Document):
    """
    Faculty Document Model for MongoDB/Beanie
    Stores both raw CV data and uniform profile
    """
    
    # Firebase UID - Primary identifier
    user_id: Indexed(str, unique=True)
    
    # Basic Information (from registration)
    name: str
    email: EmailStr
    department: str
    designation: str
    employee_id: Optional[str] = None
    
    # Contact
    phone: Optional[str] = None
    office_location: Optional[str] = None
    
    # Legacy fields (kept for backward compatibility)
    qualifications: List[Qualification] = Field(default_factory=list)
    specializations: List[str] = Field(default_factory=list)
    research_areas: List[ResearchArea] = Field(default_factory=list)
    publications: List[Publication] = Field(default_factory=list)
    years_of_experience: Optional[int] = None
    teaching_subjects: List[str] = Field(default_factory=list)
    
    # CV Data
    cv_url: Optional[str] = None
    cv_file_name: Optional[str] = None
    cv_uploaded_at: Optional[datetime] = None
    cv_parsed_data: Dict[str, Any] = Field(default_factory=dict)  # Raw parsed data
    
    # ============== NEW: Uniform Profile ==============
    uniform_profile: Optional[UniformFacultyProfile] = None
    profile_setup_complete: bool = False
    
    # Skills extracted from CV
    skills: List[str] = Field(default_factory=list)
    
    # Mentorship
    mentee_ids: List[str] = Field(default_factory=list)
    max_mentees: int = 10
    
    # Availability for meetings
    available_slots: List[MeetingSlot] = Field(default_factory=list)
    
    # Status
    status: FacultyStatus = FacultyStatus.PENDING_SETUP
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "faculty"
        indexes = [
            "user_id",
            "email",
            "department",
            "status",
            [("department", 1), ("status", 1)],
            [("specializations", 1)],
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "firebase_uid_123",
                "name": "Dr. John Doe",
                "email": "john.doe@example.edu",
                "department": "Computer Engineering",
                "designation": "Associate Professor",
                "specializations": ["Machine Learning", "Data Science"],
                "teaching_subjects": ["AI", "ML", "Data Structures"],
                "status": "active"
            }
        }
    
    def calculate_profile_completeness(self) -> float:
        """Calculate how complete the profile is (0-100%)"""
        if not self.uniform_profile:
            return 0.0
        
        score = 0.0
        total_weight = 0.0
        
        # Personal info (20%)
        weight = 20.0
        total_weight += weight
        pi = self.uniform_profile.personal_info
        if pi.name:
            score += weight * 0.4
        if pi.email:
            score += weight * 0.3
        if pi.phone:
            score += weight * 0.2
        if pi.photo_url:
            score += weight * 0.1
        
        # Academic qualifications (20%)
        weight = 20.0
        total_weight += weight
        aq = self.uniform_profile.academic_qualifications
        if aq.highest_degree:
            score += weight * 0.3
        if aq.specialization:
            score += weight * 0.3
        if aq.university:
            score += weight * 0.2
        if len(aq.all_degrees) > 0:
            score += weight * 0.2
        
        # Current position (15%)
        weight = 15.0
        total_weight += weight
        cp = self.uniform_profile.current_position
        if cp.designation:
            score += weight * 0.4
        if cp.department:
            score += weight * 0.3
        if cp.years_of_experience > 0:
            score += weight * 0.3
        
        # Research expertise (20%)
        weight = 20.0
        total_weight += weight
        re = self.uniform_profile.research_expertise
        if len(re.primary_areas) > 0:
            score += weight * 0.5
        if len(re.keywords) > 0:
            score += weight * 0.3
        if len(re.secondary_interests) > 0:
            score += weight * 0.2
        
        # Teaching (10%)
        weight = 10.0
        total_weight += weight
        ti = self.uniform_profile.teaching
        if len(ti.current_subjects) > 0:
            score += weight * 0.6
        if len(ti.past_subjects) > 0:
            score += weight * 0.4
        
        # Availability (15%)
        weight = 15.0
        total_weight += weight
        av = self.uniform_profile.availability
        if av.office_location:
            score += weight * 0.4
        if av.office_hours:
            score += weight * 0.3
        if len(av.available_slots) > 0:
            score += weight * 0.3
        
        return round((score / total_weight) * 100, 1) if total_weight > 0 else 0.0
    
    def get_student_view(self) -> Dict[str, Any]:
        """Get the profile data that students can see"""
        if not self.uniform_profile:
            # Return basic info if uniform profile not set
            return {
                "name": self.name,
                "email": self.email,
                "department": self.department,
                "designation": self.designation,
                "specializations": self.specializations,
                "profile_complete": False
            }
        
        return {
            "personal_info": {
                "name": self.uniform_profile.personal_info.name,
                "email": self.uniform_profile.personal_info.email,
                "photo_url": self.uniform_profile.personal_info.photo_url
            },
            "academic_qualifications": self.uniform_profile.academic_qualifications.dict(),
            "current_position": self.uniform_profile.current_position.dict(),
            "research_expertise": self.uniform_profile.research_expertise.dict(),
            "teaching": self.uniform_profile.teaching.dict(),
            "availability": {
                "office_location": self.uniform_profile.availability.office_location,
                "office_hours": self.uniform_profile.availability.office_hours,
                "available_slots": [s.dict() for s in self.uniform_profile.availability.available_slots]
            },
            "publications": self.uniform_profile.publications.dict() if self.uniform_profile.publications else None,
            "others": self.uniform_profile.others,
            "profile_completeness": self.uniform_profile.profile_completeness,
            "profile_complete": True
        }
# ==================== Re-export Schemas for Backward Compatibility ====================
# Import common request/response schemas that endpoints expect from this module
try:
    from app.schemas.faculty_schemas import (
        ProfileUpdateRequest,
        ProfileSetupRequest,
        FacultyProfileResponse,
        FacultyStudentView,
        CVUploadResponse,
        MeetingRequestCreate,
        MeetingRequestResponse,
        MeetingScheduleRequest,
        MeetingRejectRequest,
        FacultyMeetingRequestsResponse,
        FacultyRegistrationRequest,
        FacultyBasicInfo,
        FacultyListResponse,
        SetupStatusResponse,
        AvailabilityUpdateRequest,
        ProfileCompletenessResponse
    )
    
    # Re-export for backward compatibility
    __all__ = [
        'Faculty',
        'FacultyStatus',
        'PersonalInfo',
        'Degree',
        'AcademicQualifications',
        'CurrentPosition',
        'ResearchExpertise',
        'TeachingInfo',
        'MeetingSlot',
        'VisibilitySettings',
        'FacultyAvailability',
        'PublicationSummary',
        'UniformFacultyProfile',
        'Qualification',
        'ResearchArea',
        'Publication',
        # Schemas
        'ProfileUpdateRequest',
        'ProfileSetupRequest',
        'FacultyProfileResponse',
        'FacultyStudentView',
        'CVUploadResponse',
        'MeetingRequestCreate',
        'MeetingRequestResponse',
        'MeetingScheduleRequest',
        'MeetingRejectRequest',
        'FacultyMeetingRequestsResponse',
        'FacultyRegistrationRequest',
        'FacultyBasicInfo',
        'FacultyListResponse',
        'SetupStatusResponse',
        'AvailabilityUpdateRequest',
        'ProfileCompletenessResponse'
    ]
except ImportError:
    # If schemas file doesn't exist, provide basic compatibility
    from pydantic import BaseModel, Field
    from typing import Optional, List
    
    class ProfileUpdateRequest(BaseModel):
        """Basic ProfileUpdateRequest for compatibility"""
        name: Optional[str] = None
        department: Optional[str] = None
        designation: Optional[str] = None
        specialization: Optional[List[str]] = None
        phone: Optional[str] = None
        office_location: Optional[str] = None