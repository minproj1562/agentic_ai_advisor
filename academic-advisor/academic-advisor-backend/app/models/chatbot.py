# academic-advisor-backend/app/models/chatbot.py

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Enum, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
import enum

from app.database.base import Base


class IntentType(str, enum.Enum):
    SYLLABUS_QUERY = "SYLLABUS_QUERY"
    FACULTY_QUERY = "FACULTY_QUERY"
    PERFORMANCE_QUERY = "PERFORMANCE_QUERY"
    ELECTIVE_QUERY = "ELECTIVE_QUERY"
    CAREER_QUERY = "CAREER_QUERY"
    STUDY_PLAN_QUERY = "STUDY_PLAN_QUERY"
    CLARIFICATION = "CLARIFICATION"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class ResponseType(str, enum.Enum):
    TEXT = "text"
    CONCEPT_EXPLANATION = "concept_explanation"
    SYLLABUS_BREAKDOWN = "syllabus_breakdown"
    FACULTY_LIST = "faculty_list"
    FACULTY_RECOMMENDATION = "faculty_recommendation"
    ELECTIVE_RECOMMENDATION = "elective_recommendation"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    STUDY_PLAN = "study_plan"
    COMPARISON_TABLE = "comparison_table"
    ERROR = "error"


class ConfidenceLevel(str, enum.Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ConversationSession(Base):
    """Stores conversation sessions for context management"""
    __tablename__ = "conversation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    user_type = Column(String(50), nullable=False)  # 'student' or 'faculty'
    session_token = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON, default={})
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    context = relationship("ConversationContext", back_populates="session", uselist=False, cascade="all, delete-orphan")


class ChatMessage(Base):
    """Stores individual chat messages"""
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("conversation_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    intent = Column(Enum(IntentType), nullable=True)
    response_type = Column(Enum(ResponseType), nullable=True)
    confidence = Column(Enum(ConfidenceLevel), nullable=True)
    structured_response = Column(JSON, nullable=True)
    retrieved_sources = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    
    # Relationships
    session = relationship("ConversationSession", back_populates="messages")


class ConversationContext(Base):
    """Stores conversation context for continuity"""
    __tablename__ = "conversation_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("conversation_sessions.id"), unique=True, nullable=False)
    current_subject = Column(String(255), nullable=True)
    current_topic = Column(String(255), nullable=True)
    current_unit = Column(Integer, nullable=True)
    referenced_faculty = Column(ARRAY(String), default=[])
    discussed_topics = Column(JSON, default=[])
    student_context = Column(JSON, default={})  # Performance data, enrolled subjects, etc.
    last_intent = Column(Enum(IntentType), nullable=True)
    context_stack = Column(JSON, default=[])  # For resolving pronouns and references
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("ConversationSession", back_populates="context")


class SyllabusContent(Base):
    """Stores syllabus data for RAG retrieval"""
    __tablename__ = "syllabus_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_code = Column(String(20), nullable=False, index=True)
    subject_name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=False)
    unit_number = Column(Integer, nullable=False)
    unit_title = Column(String(255), nullable=False)
    topics = Column(JSON, nullable=False)  # List of topics
    detailed_content = Column(Text, nullable=True)
    learning_objectives = Column(JSON, default=[])
    exam_weightage = Column(Float, nullable=True)
    reference_books = Column(JSON, default=[])
    prerequisites = Column(JSON, default=[])
    keywords = Column(ARRAY(String), default=[])
    embedding_vector = Column(JSON, nullable=True)  # Store embedding for similarity search
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FacultyProfile(Base):
    """Enhanced faculty profile for chatbot queries"""
    __tablename__ = "faculty_profiles_enhanced"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    faculty_id = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    designation = Column(String(100), nullable=True)
    subjects_taught = Column(JSON, default=[])  # List of subject codes/names
    experience_years = Column(Integer, nullable=True)
    teaching_style = Column(String(255), nullable=True)
    research_areas = Column(JSON, default=[])
    mentoring_focus = Column(JSON, default=[])
    specializations = Column(JSON, default=[])
    available_for_mentoring = Column(Boolean, default=True)
    rating = Column(Float, nullable=True)
    office_hours = Column(JSON, default={})
    contact_preferences = Column(JSON, default={})
    embedding_vector = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AcademicKnowledgeBase(Base):
    """Stores curated academic knowledge for RAG"""
    __tablename__ = "academic_knowledge_base"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(100), nullable=False, index=True)  # 'concept', 'career', 'elective', etc.
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    keywords = Column(ARRAY(String), default=[])
    related_subjects = Column(JSON, default=[])
    department = Column(String(100), nullable=True)
    difficulty_level = Column(String(50), nullable=True)
    exam_relevance = Column(String(255), nullable=True)
    source = Column(String(255), nullable=True)
    embedding_vector = Column(JSON, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatbotAnalytics(Base):
    """Analytics for chatbot performance monitoring"""
    __tablename__ = "chatbot_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime, nullable=False, index=True)
    total_queries = Column(Integer, default=0)
    successful_responses = Column(Integer, default=0)
    out_of_scope_queries = Column(Integer, default=0)
    intent_distribution = Column(JSON, default={})
    avg_response_time_ms = Column(Float, nullable=True)
    avg_confidence = Column(Float, nullable=True)
    user_satisfaction_score = Column(Float, nullable=True)
    common_topics = Column(JSON, default=[])
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)