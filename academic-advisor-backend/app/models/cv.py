# app/models/cv.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ExtractedSkill(BaseModel):
    name: str
    category: str
    confidence: float = Field(ge=0, le=100)
    type: str
    context: Optional[str] = None
    importance_score: Optional[float] = None

class Experience(BaseModel):
    company: str
    role: str
    start_date: Optional[str]
    end_date: Optional[str]
    duration: Optional[str]
    description: str
    technologies: List[str] = []

class Education(BaseModel):
    degree: str
    field: str
    institution: str
    start_date: Optional[str]
    end_date: Optional[str]
    gpa: Optional[float]
    achievements: List[str] = []

class CVUpload(BaseModel):
    upload_id: str
    user_id: str
    file_name: str
    file_url: str
    file_size: int
    mime_type: str
    uploaded_at: datetime
    status: ProcessingStatus = ProcessingStatus.PENDING

class ParsedCV(BaseModel):
    text: str
    sections: Dict[str, str]
    metadata: Dict[str, Any]
    word_count: int
    
class CVAnalysis(BaseModel):
    upload_id: str
    user_id: str
    parsed_data: ParsedCV
    skills: List[ExtractedSkill]
    experience: List[Experience]
    education: List[Education]
    nlp_analysis: Dict[str, Any]
    status: ProcessingStatus
    completed_at: Optional[datetime]
    suitability_score: Optional[float]
    recommendations: List[str] = []
    
class CVSummary(BaseModel):
    upload_id: str
    summary: str
    key_skills: List[str]
    total_experience: str
    highest_education: str
    score: float