# app/models/faculty_resource.py
"""
Faculty Resource Model
======================
Faculty can upload/link learning resources (videos, PDFs, PPTs, links)
organized by semester, branch, and subject.
Uses Cloudinary for file uploads.
"""

from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class FacultyResourceType(str, Enum):
    LINK = "link"
    VIDEO = "video"
    PDF = "pdf"
    PPT = "ppt"
    DOC = "doc"
    BOOK = "book"
    OTHER = "other"


class FacultyResource(Document):
    """A learning resource shared by faculty."""
    faculty_id: Indexed(str)
    faculty_name: str = ""
    title: str
    description: str = ""
    resource_type: FacultyResourceType = FacultyResourceType.LINK
    url: Optional[str] = None          # External link
    file_url: Optional[str] = None     # Cloudinary URL for uploads
    file_public_id: Optional[str] = None  # Cloudinary public ID for deletion
    file_size_bytes: Optional[int] = None
    semester: int = 0                  # 0 = all semesters
    branch: str = "IT"
    subject: str = ""
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True
    view_count: int = 0
    download_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "faculty_resources"
        indexes = [
            "faculty_id",
            [("semester", 1), ("branch", 1)],
            [("subject", 1)],
            [("resource_type", 1)],
        ]
