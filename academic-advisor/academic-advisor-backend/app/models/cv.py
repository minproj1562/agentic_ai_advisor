#academic-advisor-backend/app/models/cv.py
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import re
from app.core.exceptions import CustomException, CVValidationException, CVParseException, CVAnalysisException

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class SkillCategory(str, Enum):
    PROGRAMMING = "programming"
    DATA_SCIENCE = "data_science"
    WEB_DEVELOPMENT = "web_development"
    CLOUD = "cloud"
    DATABASE = "database"
    RESEARCH_METHODS = "research_methods"
    ACADEMIC_SKILLS = "academic_skills"
    SOFT_SKILLS = "soft_skills"
    OTHER = "other"

class ExpertiseLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class ResearchDomain(str, Enum):
    COMPUTER_SCIENCE = "computer_science"
    ENGINEERING = "engineering"
    SCIENCES = "sciences"
    SOCIAL_SCIENCES = "social_sciences"
    BUSINESS = "business"
    ARTS = "arts"
    OTHER = "other"

class ResearchMaturity(str, Enum):
    EMERGING = "emerging"
    DEVELOPING = "developing"
    ESTABLISHED = "established"

class ExtractedSkill(BaseModel):
    name: str
    category: SkillCategory
    confidence: float = Field(ge=0, le=100)
    type: str
    context: Optional[str] = None
    importance_score: Optional[float] = Field(None, ge=0, le=100)
    research_relevance: Optional[float] = Field(None, ge=0, le=100)
    sources: List[str] = Field(default_factory=list)
    
    @validator('name')
    def validate_skill_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Skill name cannot be empty")
        if len(v) > 100:
            raise ValueError("Skill name too long")
        return v.strip()

class Experience(BaseModel):
    company: str
    role: str
    start_date: Optional[str]
    end_date: Optional[str]
    duration: Optional[str]
    description: str
    technologies: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    is_current: bool = False
    
    @validator('company')
    def validate_company(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Company name cannot be empty")
        return v.strip()
    
    @validator('role')
    def validate_role(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Role cannot be empty")
        return v.strip()

class Education(BaseModel):
    degree: str
    field: str
    institution: str
    start_date: Optional[str]
    end_date: Optional[str]
    gpa: Optional[float] = Field(None, ge=0, le=4.0)
    achievements: List[str] = Field(default_factory=list)
    is_completed: bool = True
    
    @validator('degree')
    def validate_degree(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Degree cannot be empty")
        return v.strip()
    
    @validator('institution')
    def validate_institution(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Institution cannot be empty")
        return v.strip()

class ResearchArea(BaseModel):
    name: str
    field: ResearchDomain
    subfield: Optional[str]
    confidence: float = Field(ge=0, le=100)
    type: str
    relevance_score: Optional[float] = Field(None, ge=0, le=100)
    matched_text: Optional[str]
    sources: List[str] = Field(default_factory=list)
    
    @validator('name')
    def validate_research_area_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Research area name cannot be empty")
        return v.strip()

class ExpertiseAssessment(BaseModel):
    skill_name: str
    score: float = Field(ge=0, le=100)
    level: ExpertiseLevel
    confidence: float = Field(ge=0, le=100)
    evidence: List[str] = Field(default_factory=list)
    
    @validator('skill_name')
    def validate_skill_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Skill name cannot be empty")
        return v.strip()

class ResearchTheme(BaseModel):
    theme: str
    score: float = Field(ge=0, le=100)
    indicators: List[str] = Field(default_factory=list)
    
    @validator('theme')
    def validate_theme(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Theme cannot be empty")
        return v.strip()

class ResearchProfile(BaseModel):
    overall_score: float = Field(ge=0, le=100)
    primary_domains: List[ResearchArea] = Field(default_factory=list)
    technical_competencies: List[ExtractedSkill] = Field(default_factory=list)
    research_themes: List[ResearchTheme] = Field(default_factory=list)
    maturity_level: ResearchMaturity
    skill_distribution: Dict[str, int] = Field(default_factory=dict)
    research_focus: str
    
    @validator('overall_score')
    def validate_score(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Score must be between 0 and 100")
        return v

class EntityExtraction(BaseModel):
    organizations: List[Dict[str, Any]] = Field(default_factory=list)
    locations: List[Dict[str, Any]] = Field(default_factory=list)
    dates: List[Dict[str, Any]] = Field(default_factory=list)
    quantities: List[Dict[str, Any]] = Field(default_factory=list)
    other: List[Dict[str, Any]] = Field(default_factory=list)

class EducationAnalysis(BaseModel):
    degrees: List[Education] = Field(default_factory=list)
    highest_degree: str
    education_level: str
    
    @validator('highest_degree')
    def validate_highest_degree(cls, v):
        valid_degrees = ['PhD', "Master's", "Bachelor's", "Associate", "Unknown"]
        if v not in valid_degrees:
            raise ValueError(f"Highest degree must be one of {valid_degrees}")
        return v

class ExperienceAnalysis(BaseModel):
    positions: List[Experience] = Field(default_factory=list)
    total_experience_years: float = Field(ge=0)
    career_level: str
    
    @validator('career_level')
    def validate_career_level(cls, v):
        valid_levels = ['entry-level', 'junior', 'mid-level', 'senior']
        if v not in valid_levels:
            raise ValueError(f"Career level must be one of {valid_levels}")
        return v

class PersonalInfo(BaseModel):
    email: Optional[str]
    phone: Optional[str]
    locations: List[str] = Field(default_factory=list)
    
    @validator('email')
    def validate_email(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError("Invalid email format")
        return v

class WritingAnalysis(BaseModel):
    avg_sentence_length: float = Field(ge=0)
    avg_word_length: float = Field(ge=0)
    vocabulary_richness: float = Field(ge=0, le=1)
    action_verb_count: int = Field(ge=0)
    action_verb_ratio: float = Field(ge=0, le=1)
    writing_quality: str
    
    @validator('writing_quality')
    def validate_writing_quality(cls, v):
        valid_qualities = ['excellent', 'good', 'average', 'needs_improvement']
        if v not in valid_qualities:
            raise ValueError(f"Writing quality must be one of {valid_qualities}")
        return v

class Achievement(BaseModel):
    achievement: str
    metric: Optional[str]
    confidence: float = Field(ge=0, le=100)
    type: str
    
    @validator('achievement')
    def validate_achievement(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Achievement cannot be empty")
        return v.strip()

class DocumentMetrics(BaseModel):
    sentence_count: int = Field(ge=0)
    word_count: int = Field(ge=0)
    character_count: int = Field(ge=0)
    readability_score: float = Field(ge=0, le=100)
    professional_tone_score: float = Field(ge=0, le=100)

class CVUpload(BaseModel):
    upload_id: str
    user_id: str
    file_name: str
    file_url: str
    file_size: int = Field(ge=0)
    mime_type: str
    uploaded_at: datetime
    status: ProcessingStatus = ProcessingStatus.PENDING
    validation_results: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('upload_id')
    def validate_upload_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Upload ID cannot be empty")
        return v.strip()

class ParsedCV(BaseModel):
    text: str
    sections: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    word_count: int = Field(ge=0)
    extraction_methods: List[str] = Field(default_factory=list)
    extraction_success: bool = True
    quality_score: Optional[float] = Field(None, ge=0, le=100)
    
    @validator('text')
    def validate_text(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Parsed text cannot be empty")
        return v.strip()

class CVAnalysis(BaseModel):
    upload_id: str
    user_id: str
    parsed_data: ParsedCV
    skills: List[ExtractedSkill] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    research_areas: List[ResearchArea] = Field(default_factory=list)
    expertise_levels: Dict[str, ExpertiseAssessment] = Field(default_factory=dict)
    research_themes: List[ResearchTheme] = Field(default_factory=list)
    research_profile: Optional[ResearchProfile] = None
    nlp_analysis: Dict[str, Any] = Field(default_factory=dict)
    entities: Optional[EntityExtraction] = None
    education_analysis: Optional[EducationAnalysis] = None
    experience_analysis: Optional[ExperienceAnalysis] = None
    personal_info: Optional[PersonalInfo] = None
    writing_analysis: Optional[WritingAnalysis] = None
    achievements: List[Achievement] = Field(default_factory=list)
    document_metrics: Optional[DocumentMetrics] = None
    status: ProcessingStatus
    completed_at: Optional[datetime]
    suitability_score: Optional[float] = Field(None, ge=0, le=100)
    recommendations: List[str] = Field(default_factory=list)
    processing_errors: List[str] = Field(default_factory=list)
    
    @validator('upload_id')
    def validate_upload_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Upload ID cannot be empty")
        return v.strip()

class CVSummary(BaseModel):
    upload_id: str
    summary: str
    key_skills: List[str] = Field(default_factory=list)
    total_experience: str
    highest_education: str
    score: float = Field(ge=0, le=100)
    research_focus: Optional[str] = None
    technical_competencies: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    @validator('summary')
    def validate_summary(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Summary cannot be empty")
        return v.strip()

class CVProcessingResult(BaseModel):
    upload_id: str
    user_id: str
    status: ProcessingStatus
    progress: float = Field(ge=0, le=100)
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    estimated_completion_time: Optional[datetime] = None
    extracted_data: Optional[CVAnalysis] = None
    
    @validator('progress')
    def validate_progress(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Progress must be between 0 and 100")
        return v

class CVSearchQuery(BaseModel):
    skills: List[str] = Field(default_factory=list)
    research_areas: List[str] = Field(default_factory=list)
    experience_min: Optional[int] = Field(None, ge=0)
    experience_max: Optional[int] = Field(None, ge=0)
    education_level: Optional[str] = None
    location: Optional[str] = None
    
    @validator('education_level')
    def validate_education_level(cls, v):
        if v and v not in ['bachelors', 'masters', 'doctoral']:
            raise ValueError("Education level must be one of: bachelors, masters, doctoral")
        return v

class CVMatchResult(BaseModel):
    upload_id: str
    user_id: str
    match_score: float = Field(ge=0, le=100)
    matching_skills: List[str] = Field(default_factory=list)
    matching_research_areas: List[str] = Field(default_factory=list)
    experience_match: Optional[float] = Field(None, ge=0, le=100)
    education_match: Optional[float] = Field(None, ge=0, le=100)
    recommendations: List[str] = Field(default_factory=list)

# Response models for API
class CVUploadResponse(BaseModel):
    upload_id: str
    status: str
    file_url: str
    message: str
    validation: Dict[str, Any]
    estimated_processing_time: int = Field(default=30, description="Estimated processing time in seconds")

class CVStatusResponse(BaseModel):
    upload_id: str
    status: ProcessingStatus
    progress: float = Field(ge=0, le=100)
    result_url: Optional[str]
    error_message: Optional[str]
    estimated_completion_time: Optional[datetime]

class CVAnalysisResponse(BaseModel):
    upload_id: str
    analysis: CVAnalysis
    summary: CVSummary
    research_potential: Optional[ResearchProfile]
    processing_metadata: Dict[str, Any]

class CVSearchResponse(BaseModel):
    results: List[CVMatchResult]
    total_matches: int = Field(ge=0)
    search_metadata: Dict[str, Any]

# Validation models
class CVValidationResult(BaseModel):
    valid: bool
    error: Optional[str] = None
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class FileValidationResult(BaseModel):
    valid: bool
    filename: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None
    extension: Optional[str] = None
    error: Optional[str] = None
    code: Optional[str] = None

# Export all models
__all__ = [
    'ProcessingStatus',
    'SkillCategory',
    'ExpertiseLevel',
    'ResearchDomain',
    'ResearchMaturity',
    'ExtractedSkill',
    'Experience',
    'Education',
    'ResearchArea',
    'ExpertiseAssessment',
    'ResearchTheme',
    'ResearchProfile',
    'EntityExtraction',
    'EducationAnalysis',
    'ExperienceAnalysis',
    'PersonalInfo',
    'WritingAnalysis',
    'Achievement',
    'DocumentMetrics',
    'CVUpload',
    'ParsedCV',
    'CVAnalysis',
    'CVSummary',
    'CVProcessingResult',
    'CVSearchQuery',
    'CVMatchResult',
    'CVUploadResponse',
    'CVStatusResponse',
    'CVAnalysisResponse',
    'CVSearchResponse',
    'CVValidationResult',
    'FileValidationResult'
]