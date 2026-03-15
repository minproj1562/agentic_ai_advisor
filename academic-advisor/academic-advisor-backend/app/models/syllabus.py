# app/models/syllabus.py
"""
Syllabus models - Flexible for both populated and chatbot standalone topics
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from beanie import Document, Indexed, Link, PydanticObjectId
from pydantic import Field, BaseModel, field_validator, model_validator
from bson import ObjectId


# ══════════════════════════════════════════════════════════
# HELPER FOR FLEXIBLE ID HANDLING
# ══════════════════════════════════════════════════════════

class FlexibleDocument(Document):
    """Base document that handles both ObjectId and string IDs."""
    
    class Settings:
        use_state_management = True
        validate_on_save = True
    
    class Config:
        # Allow extra fields in the document
        extra = "allow"
        # Allow population by field name or alias
        populate_by_name = True


# ══════════════════════════════════════════════════════════
# DEPARTMENT
# ══════════════════════════════════════════════════════════

class Department(FlexibleDocument):
    """Department document."""
    code: str = Indexed(unique=True)
    name: str
    description: Optional[str] = None
    hod_name: Optional[str] = None
    vision: Optional[str] = None
    mission: Optional[List[str]] = None
    programs_offered: Optional[List[str]] = None
    duration: Optional[str] = None
    total_seats: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "departments"


# ══════════════════════════════════════════════════════════
# SUBJECT - Made flexible with optional fields
# ══════════════════════════════════════════════════════════

class Subject(FlexibleDocument):
    """
    Subject/Course document.
    Fields made optional for data compatibility.
    """
    code: str = Indexed(unique=True)
    name: str
    
    # Made optional for compatibility with existing data
    department: Optional[Union[Link[Department], str, Dict]] = None
    semester: Optional[int] = 0
    credits: Optional[float] = 0
    subject_type: Optional[str] = "core"  # Made optional with default
    
    category: Optional[str] = None
    teaching_scheme: Dict[str, Any] = Field(default_factory=lambda: {"L": 0, "T": 0, "P": 0})
    description: Optional[str] = None
    learning_outcomes: List[str] = Field(default_factory=list)
    reference_books: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    examination_scheme: Dict[str, Any] = Field(default_factory=dict)
    units: List[Dict[str, Any]] = Field(default_factory=list)  # Embedded units
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "subjects"

    @model_validator(mode='before')
    @classmethod
    def set_defaults(cls, data: Any) -> Any:
        """Set default values for missing required fields."""
        if isinstance(data, dict):
            if 'subject_type' not in data or data['subject_type'] is None:
                data['subject_type'] = 'core'
            if 'semester' not in data:
                data['semester'] = 0
            if 'credits' not in data:
                data['credits'] = 0
        return data


# ══════════════════════════════════════════════════════════
# SUBJECT UNIT
# ══════════════════════════════════════════════════════════

class SubjectUnit(FlexibleDocument):
    """Subject unit/module document."""
    subject: Optional[Union[Link[Subject], str, Dict]] = None  # Made optional
    subject_code: Optional[str] = None  # Alternative reference
    unit_number: Optional[int] = None
    title: str = ""
    description: Optional[str] = None
    lecture_hours: Optional[int] = None
    keywords: List[str] = Field(default_factory=list)
    learning_outcomes: List[str] = Field(default_factory=list)
    topics: List[Dict[str, Any]] = Field(default_factory=list)  # Embedded topics
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "subject_units"


# ══════════════════════════════════════════════════════════
# TOPIC - Made flexible with optional unit link
# ══════════════════════════════════════════════════════════

class Topic(FlexibleDocument):
    """
    Topic document - can be standalone or linked to a unit.
    Used by chatbot for answering syllabus queries.
    """
    name: str = Indexed()
    
    # Made optional for standalone topics
    unit: Optional[Union[Link[SubjectUnit], str, Dict]] = None
    subject_code: Optional[str] = None  # For direct reference without Link
    unit_number: Optional[int] = None
    unit_title: Optional[str] = None
    subject_name: Optional[str] = None  # Denormalized for easy access
    
    # Content
    definition: Optional[str] = None
    explanation: Optional[str] = None
    key_points: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)
    
    # Exam info
    exam_weightage: Optional[Union[float, str]] = None
    exam_frequency: Optional[str] = None
    previous_year_questions: List[str] = Field(default_factory=list)
    
    # Related content
    related_topics: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    
    # Search optimization
    keywords: List[str] = Field(default_factory=list)
    difficulty_level: str = "medium"
    
    # Resources
    video_links: List[str] = Field(default_factory=list)
    reference_links: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "topics"

    @model_validator(mode='before')
    @classmethod
    def handle_optional_unit(cls, data: Any) -> Any:
        """Allow topics without unit link."""
        if isinstance(data, dict):
            # If unit is not provided, that's fine
            if 'unit' not in data:
                data['unit'] = None
        return data


# ══════════════════════════════════════════════════════════
# FACULTY
# ══════════════════════════════════════════════════════════

class Faculty(FlexibleDocument):
    """Faculty member document."""
    employee_id: str = Indexed(unique=True)
    firebase_uid: Optional[str] = Indexed(unique=True, sparse=True)
    name: str
    email: str = Indexed(unique=True)
    phone: Optional[str] = None
    profile_image: Optional[str] = None
    department: Optional[Union[Link[Department], str, Dict]] = None
    designation: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: int = 0
    joining_date: Optional[datetime] = None
    specializations: List[str] = Field(default_factory=list)
    research_areas: List[str] = Field(default_factory=list)
    publications_count: int = 0
    teaching_style: Optional[str] = None
    mentoring_areas: List[str] = Field(default_factory=list)
    subjects_taught: List[str] = Field(default_factory=list)  # Subject names
    office_location: Optional[str] = None
    office_hours: Dict[str, str] = Field(default_factory=dict)
    is_available_for_mentoring: bool = True
    teaching_rating: Optional[float] = None
    mentoring_rating: Optional[float] = None
    total_reviews: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "faculty_members"


class FacultySubject(FlexibleDocument):
    """Faculty-Subject mapping."""
    faculty: Optional[Union[Link[Faculty], str]] = None
    subject: Optional[Union[Link[Subject], str]] = None
    faculty_name: Optional[str] = None  # Denormalized
    subject_name: Optional[str] = None  # Denormalized
    academic_year: Optional[str] = None
    semester: Optional[int] = None
    section: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "faculty_subjects"


# ══════════════════════════════════════════════════════════
# CAREER PATH
# ══════════════════════════════════════════════════════════

class CareerPath(FlexibleDocument):
    """Career path document."""
    title: str = Indexed(unique=True)
    category: Optional[str] = None
    description: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    recommended_subjects: List[str] = Field(default_factory=list)
    recommended_electives: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    salary_range: Dict[str, str] = Field(default_factory=dict)
    job_titles: List[str] = Field(default_factory=list)
    companies: List[str] = Field(default_factory=list)
    growth_potential: Optional[str] = None
    market_demand: Optional[str] = None
    roadmap: List[str] = Field(default_factory=list)
    resources: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    matching_interests: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "career_paths"


# ══════════════════════════════════════════════════════════
# ELECTIVES
# ══════════════════════════════════════════════════════════

class ProgramElective(FlexibleDocument):
    """Program elective document."""
    code: str = Indexed(unique=True)
    name: str
    department: Optional[Union[Link[Department], str]] = None
    semester: Optional[int] = None
    credits: int = 3
    category: str = "PEC"
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "program_electives"


class OpenElective(FlexibleDocument):
    """Open elective document."""
    code: str = Indexed(unique=True)
    name: str
    semester: Optional[int] = None
    credits: int = 3
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "open_electives"


class LiberalLearningCourse(FlexibleDocument):
    """Liberal learning course document."""
    code: str = Indexed(unique=True)
    name: str
    semester: int = 6
    credits: int = 2
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "liberal_learning_courses"


class MDMCourse(FlexibleDocument):
    """Multi-disciplinary minor course."""
    code: str = Indexed(unique=True)
    name: str
    department: Optional[Union[Link[Department], str]] = None
    semester: Optional[int] = None
    credits: Optional[int] = 3
    subject_type: str = "core"
    category: str = "MDM"
    teaching_scheme: Dict[str, int] = Field(default_factory=lambda: {"L": 0, "T": 0, "P": 0})
    description: Optional[str] = None
    examination_scheme: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "mdm_courses"


# ══════════════════════════════════════════════════════════
# OTHER
# ══════════════════════════════════════════════════════════

class Abbreviation(FlexibleDocument):
    """Abbreviation definitions."""
    code: str = Indexed(unique=True)
    full_form: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "abbreviations"


class CreditStructure(FlexibleDocument):
    """Credit structure for a program."""
    program: str
    total_credits: Optional[int] = 0
    min_credits_per_semester: Optional[int] = 0
    max_credits_per_semester: Optional[int] = 0
    semester_wise_distribution: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    category_wise_total: Dict[str, int] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "credit_structures"


# ══════════════════════════════════════════════════════════
# EXPORTS
# ══════════════════════════════════════════════════════════

__all__ = [
    "Department",
    "Subject",
    "SubjectUnit",
    "Topic",
    "Faculty",
    "FacultySubject",
    "CareerPath",
    "ProgramElective",
    "OpenElective",
    "LiberalLearningCourse",
    "MDMCourse",
    "Abbreviation",
    "CreditStructure",
]