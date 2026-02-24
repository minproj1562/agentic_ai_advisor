from datetime import datetime
from typing import Optional, List, Dict, Any
from beanie import Document, Indexed, Link, before_event, Insert, Replace
from pydantic import Field, BaseModel
import uuid


class Department(Document):
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


class Subject(Document):
    code: str = Indexed(unique=True)
    name: str
    department: Link[Department]
    semester: int
    credits: int
    subject_type: str
    category: Optional[str] = None
    teaching_scheme: Dict[str, int] = Field(default_factory=lambda: {"L": 0, "T": 0, "P": 0})
    description: Optional[str] = None
    learning_outcomes: List[str] = Field(default_factory=list)
    reference_books: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    examination_scheme: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "subjects"


class SubjectUnit(Document):
    subject: Link[Subject]
    unit_number: int
    title: str
    description: Optional[str] = None
    lecture_hours: Optional[int] = None
    keywords: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "subject_units"


class Topic(Document):
    unit: Link[SubjectUnit]
    name: str
    definition: Optional[str] = None
    explanation: Optional[str] = None
    key_points: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)
    exam_weightage: Optional[float] = None
    exam_frequency: Optional[str] = None
    previous_year_questions: List[str] = Field(default_factory=list)
    related_topics: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    difficulty_level: str = "medium"
    video_links: List[str] = Field(default_factory=list)
    reference_links: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "topics"


class Faculty(Document):
    employee_id: str = Indexed(unique=True)
    firebase_uid: Optional[str] = Indexed(unique=True, sparse=True)
    name: str
    email: str = Indexed(unique=True)
    phone: Optional[str] = None
    profile_image: Optional[str] = None
    department: Link[Department]
    designation: str
    qualification: Optional[str] = None
    experience_years: int = 0
    joining_date: Optional[datetime] = None
    specializations: List[str] = Field(default_factory=list)
    research_areas: List[str] = Field(default_factory=list)
    publications_count: int = 0
    teaching_style: Optional[str] = None
    mentoring_areas: List[str] = Field(default_factory=list)
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


class FacultySubject(Document):
    faculty: Link[Faculty]
    subject: Link[Subject]
    academic_year: str
    semester: int
    section: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "faculty_subjects"


class CareerPath(Document):
    title: str = Indexed(unique=True)
    category: str
    description: str
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


class ProgramElective(Document):
    code: str = Indexed(unique=True)
    name: str
    department: Link[Department]
    semester: int
    credits: int = 3
    category: str = "PEC"
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "program_electives"


class OpenElective(Document):
    code: str = Indexed(unique=True)
    name: str
    semester: int
    credits: int = 3
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "open_electives"


class LiberalLearningCourse(Document):
    code: str = Indexed(unique=True)
    name: str
    semester: int = 6
    credits: int = 2
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "liberal_learning_courses"


class MDMCourse(Document):
    code: str = Indexed(unique=True)
    name: str
    department: Link[Department]
    semester: int
    credits: int
    subject_type: str = "core"
    category: str = "MDM"
    teaching_scheme: Dict[str, int] = Field(default_factory=lambda: {"L": 0, "T": 0, "P": 0})
    description: Optional[str] = None
    examination_scheme: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "mdm_courses"


class Abbreviation(Document):
    code: str = Indexed(unique=True)
    full_form: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "abbreviations"


class CreditStructure(Document):
    program: str
    total_credits: int
    min_credits_per_semester: int
    max_credits_per_semester: int
    semester_wise_distribution: Dict[str, Dict[str, Any]]
    category_wise_total: Dict[str, int]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "credit_structures"