# app/models/achievement.py
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from datetime import datetime

from app.core.database import Base

class AchievementCategory(str, enum.Enum):
    AWARD = "award"
    CERTIFICATION = "certification"
    MILESTONE = "milestone"
    RECOGNITION = "recognition"
    GRANT = "grant"

class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    faculty_id = Column(String, nullable=False, index=True)
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(SQLEnum(AchievementCategory), nullable=False)
    organization = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    
    url = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    impact_score = Column(Float, nullable=True)
    
    tags = Column(JSON, default=list)
    collaborators = Column(JSON, default=list)
    attachments = Column(JSON, default=list)
    
    visibility = Column(String, default='public')
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Achievement {self.title}>"