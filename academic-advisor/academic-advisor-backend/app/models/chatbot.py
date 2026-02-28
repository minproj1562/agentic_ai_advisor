# academic-advisor/academic-advisor-backend/app/models/chatbot.py
"""
Chatbot models — Beanie Documents for MongoDB
Replaces the old SQLAlchemy models entirely
"""

from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid


# ── Enums ────────────────────────────────────────────────

class IntentType(str, Enum):
    SYLLABUS_QUERY = "SYLLABUS_QUERY"
    FACULTY_QUERY = "FACULTY_QUERY"
    PERFORMANCE_QUERY = "PERFORMANCE_QUERY"
    ELECTIVE_QUERY = "ELECTIVE_QUERY"
    CAREER_QUERY = "CAREER_QUERY"
    STUDY_PLAN_QUERY = "STUDY_PLAN_QUERY"
    CLARIFICATION = "CLARIFICATION"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class ResponseType(str, Enum):
    TEXT = "text"
    CONCEPT_EXPLANATION = "concept_explanation"
    SYLLABUS_BREAKDOWN = "syllabus_breakdown"
    FACULTY_LIST = "faculty_list"
    FACULTY_RECOMMENDATION = "faculty_recommendation"
    ELECTIVE_RECOMMENDATION = "elective_recommendation"
    CAREER_GUIDANCE = "career_guidance"
    CAREER_LIST = "career_list"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    STUDY_PLAN = "study_plan"
    COMPARISON_TABLE = "comparison_table"
    ERROR = "error"


class ConfidenceLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# ── Embedded Sub-documents ───────────────────────────────

class ChatMessageDoc(BaseModel):
    """A single message embedded inside a ChatSession"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str                                   # 'user' | 'assistant'
    content: str
    intent: Optional[IntentType] = None
    response_type: Optional[str] = None
    confidence: Optional[ConfidenceLevel] = None
    structured_response: Optional[Dict[str, Any]] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    processing_time_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationContextDoc(BaseModel):
    """Conversation context embedded inside a ChatSession"""
    current_subject: Optional[str] = None
    current_topic: Optional[str] = None
    current_unit: Optional[int] = None
    referenced_faculty: List[str] = Field(default_factory=list)
    discussed_topics: List[str] = Field(default_factory=list)
    student_context: Dict[str, Any] = Field(default_factory=dict)
    last_intent: Optional[IntentType] = None
    context_stack: List[Dict[str, Any]] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Top-level Documents ──────────────────────────────────

class ChatSession(Document):
    """One conversation session"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Indexed(str)
    user_type: str = "student"
    session_token: Indexed(str, unique=True)

    messages: List[ChatMessageDoc] = Field(default_factory=list)
    context: ConversationContextDoc = Field(
        default_factory=ConversationContextDoc
    )

    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=24)
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "chat_sessions"
        indexes = ["user_id", "session_token", "is_active", "expires_at"]


class ChatFeedback(Document):
    """User feedback on a single chatbot response  (Task 22)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Indexed(str)
    message_id: str
    user_id: Indexed(str)

    rating: int = Field(ge=1, le=5)
    feedback_text: Optional[str] = None
    was_helpful: Optional[bool] = None
    intent: Optional[IntentType] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "chat_feedback"
        indexes = ["session_id", "user_id", "rating", "intent"]


class ChatbotAnalyticsDoc(Document):
    """Daily aggregated chatbot analytics  (Task 20)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: Indexed(datetime)

    total_queries: int = 0
    successful_responses: int = 0
    out_of_scope_queries: int = 0

    intent_distribution: Dict[str, int] = Field(default_factory=dict)
    avg_response_time_ms: float = 0
    avg_confidence: float = 0

    user_satisfaction_avg: float = 0
    feedback_count: int = 0

    common_topics: List[Dict[str, Any]] = Field(default_factory=list)
    error_count: int = 0
    unique_users: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "chatbot_analytics"
        indexes = ["date"]