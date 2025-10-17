from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class PublicationType(str, Enum):
    JOURNAL = "journal"
    CONFERENCE = "conference"
    BOOK_CHAPTER = "book-chapter"
    PREPRINT = "preprint"
    PATENT = "patent"

class PublicationStatus(str, Enum):
    PUBLISHED = "published"
    ACCEPTED = "accepted"
    UNDER_REVIEW = "under-review"
    DRAFT = "draft"

class CitationTrend(BaseModel):
    month: str
    count: int

class Collaborator(BaseModel):
    id: Optional[str] = None
    name: str
    affiliation: str
    role: str
    email: Optional[str] = None

class SupplementaryMaterial(BaseModel):
    name: str
    url: str
    type: str
    size: Optional[int] = None

class Publication(Document):
    user_id: Indexed(str)  # Firebase UID
    faculty_id: Optional[str] = None
    
    # Basic Information
    title: Indexed(str)
    authors: List[str]
    journal: str
    conference_proceedings: Optional[str] = None
    publication_type: PublicationType
    publication_date: datetime
    
    # Identifiers
    doi: Optional[Indexed(str, unique=True)] = None
    url: Optional[HttpUrl] = None
    scopus_id: Optional[str] = None
    wos_id: Optional[str] = None
    google_scholar_id: Optional[str] = None
    arxiv_id: Optional[str] = None
    pubmed_id: Optional[str] = None
    
    # Content
    abstract: str
    keywords: List[str] = Field(default_factory=list)
    
    # Metrics
    citations: int = 0
    citation_trend: List[CitationTrend] = Field(default_factory=list)
    impact_factor: Optional[float] = None
    h_index: Optional[int] = None
    views: int = 0
    downloads: int = 0
    altmetric_score: Optional[float] = None
    
    # Classification
    status: PublicationStatus = PublicationStatus.DRAFT
    quartile: Optional[str] = None  # Q1, Q2, Q3, Q4
    is_open_access: bool = False
    
    # Additional Details
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    issn: Optional[str] = None
    
    # Files and Materials
    pdf_url: Optional[str] = None
    supplementary_materials: List[SupplementaryMaterial] = Field(default_factory=list)
    
    # Collaboration
    collaborators: List[Collaborator] = Field(default_factory=list)
    
    # Funding
    funding_source: Optional[str] = None
    grant_number: Optional[str] = None
    
    # Research Areas
    research_areas: List[str] = Field(default_factory=list)
    
    # Metadata
    last_citation_update: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "publications"
        indexes = [
            "user_id",
            "title",
            "publication_date",
            "status",
            "publication_type",
            [("user_id", 1), ("publication_date", -1)],
            [("user_id", 1), ("citations", -1)]
        ]
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Machine Learning for Academic Success Prediction",
                "authors": ["John Doe", "Jane Smith"],
                "journal": "Journal of Educational Data Mining",
                "publication_type": "journal",
                "publication_date": "2024-01-15",
                "abstract": "This paper presents a novel approach...",
                "keywords": ["machine learning", "education", "prediction"]
            }
        }