# app/models/chatbot.py
"""
Chatbot models — Beanie Documents for MongoDB
Complete implementation with all required models
"""

from beanie import Document, Indexed, Link, PydanticObjectId
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid


# ══════════════════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════════════════

class IntentType(str, Enum):
    SYLLABUS_QUERY = "SYLLABUS_QUERY"
    FACULTY_QUERY = "FACULTY_QUERY"
    PERFORMANCE_QUERY = "PERFORMANCE_QUERY"
    ELECTIVE_QUERY = "ELECTIVE_QUERY"
    CAREER_QUERY = "CAREER_QUERY"
    STUDY_PLAN_QUERY = "STUDY_PLAN_QUERY"
    CLARIFICATION = "CLARIFICATION"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    GENERAL = "GENERAL"


class ResponseType(str, Enum):
    TEXT = "text"
    CONCEPT_EXPLANATION = "concept_explanation"
    SYLLABUS_BREAKDOWN = "syllabus_breakdown"
    FACULTY_LIST = "faculty_list"
    FACULTY_DETAIL = "faculty_detail"
    FACULTY_RECOMMENDATION = "faculty_recommendation"
    ELECTIVE_RECOMMENDATION = "elective_recommendation"
    CAREER_GUIDANCE = "career_guidance"
    CAREER_LIST = "career_list"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    STUDY_PLAN = "study_plan"
    COMPARISON_TABLE = "comparison_table"
    TOPIC_LIST = "topic_list"
    ERROR = "error"


class ConfidenceLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# ══════════════════════════════════════════════════════════
# EMBEDDED MODELS (Used within Documents)
# ══════════════════════════════════════════════════════════

class ChatMessageDoc(BaseModel):
    """
    Embedded message document - stored within ChatSession.
    For lightweight storage of recent messages.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # "user" or "assistant"
    content: str
    intent: Optional[IntentType] = None
    response_type: Optional[ResponseType] = None
    confidence: Optional[ConfidenceLevel] = None
    structured_response: Optional[Dict[str, Any]] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    processing_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class ConversationContextDoc(BaseModel):
    """
    Conversation context embedded inside ChatSession.
    Tracks current state of the conversation.
    """
    current_subject: Optional[str] = None
    current_subject_code: Optional[str] = None
    current_topic: Optional[str] = None
    current_unit: Optional[int] = None
    referenced_faculty: List[str] = Field(default_factory=list)
    discussed_topics: List[str] = Field(default_factory=list)
    discussed_subjects: List[str] = Field(default_factory=list)
    student_context: Dict[str, Any] = Field(default_factory=dict)
    last_intent: Optional[IntentType] = None
    last_response_type: Optional[ResponseType] = None
    context_stack: List[Dict[str, Any]] = Field(default_factory=list)
    follow_up_expected: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True

    def push_to_stack(self, entry: Dict[str, Any], max_size: int = 5):
        """Push an entry onto the context stack, maintaining max size."""
        self.context_stack.append(entry)
        if len(self.context_stack) > max_size:
            self.context_stack = self.context_stack[-max_size:]

    def get_last_context(self) -> Optional[Dict[str, Any]]:
        """Get the most recent context entry."""
        return self.context_stack[-1] if self.context_stack else None


# ══════════════════════════════════════════════════════════
# TOP-LEVEL DOCUMENTS (MongoDB Collections)
# ══════════════════════════════════════════════════════════

class ChatSession(Document):
    """
    One conversation session.
    Contains embedded messages and context for efficiency.
    """
    user_id: Indexed(str)  # Firebase UID
    user_type: str = "student"  # "student" or "faculty"
    session_token: Indexed(str, unique=True)

    # Embedded messages (capped at 50 for performance)
    messages: List[ChatMessageDoc] = Field(default_factory=list)
    
    # Embedded context
    context: ConversationContextDoc = Field(default_factory=ConversationContextDoc)

    # Session state
    is_active: bool = True
    message_count: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=24)
    )
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "chat_sessions"
        indexes = [
            [("user_id", 1), ("is_active", 1)],
            [("session_token", 1)],
            [("expires_at", 1)],
            [("updated_at", -1)],
        ]

    def add_message(self, message: ChatMessageDoc, max_messages: int = 50):
        """Add a message to the session, maintaining max size."""
        self.messages.append(message)
        self.message_count += 1
        self.updated_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        
        # Keep only the last max_messages
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]

    def get_recent_messages(self, limit: int = 10) -> List[ChatMessageDoc]:
        """Get the most recent messages."""
        return self.messages[-limit:]

    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at

    def extend_expiry(self, hours: int = 24):
        """Extend the session expiry time."""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)


class ChatMessage(Document):
    """
    Standalone message document for archival/analytics.
    Used for long-term storage and detailed analysis.
    """
    session_id: Indexed(str)
    user_id: Indexed(str)
    role: str  # "user" or "assistant"
    content: str
    
    # Classification
    intent: Optional[IntentType] = None
    response_type: Optional[ResponseType] = None
    confidence: Optional[ConfidenceLevel] = None
    
    # Response details
    structured_response: Optional[Dict[str, Any]] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metrics
    processing_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "chat_messages"
        indexes = [
            [("session_id", 1), ("created_at", -1)],
            [("user_id", 1), ("created_at", -1)],
            [("intent", 1)],
        ]


class ChatFeedback(Document):
    """User feedback on a chatbot response."""
    session_id: Indexed(str)
    message_id: str
    user_id: Indexed(str)

    rating: int = Field(ge=1, le=5)  # 1-5 stars
    feedback_text: Optional[str] = None
    was_helpful: Optional[bool] = None
    intent: Optional[IntentType] = None
    response_type: Optional[ResponseType] = None
    
    # Additional context
    query: Optional[str] = None
    response_preview: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "chat_feedback"
        indexes = [
            [("session_id", 1)],
            [("user_id", 1)],
            [("rating", 1)],
            [("created_at", -1)],
        ]


class ChatbotAnalyticsDoc(Document):
    """Daily aggregated chatbot analytics."""
    date: Indexed(datetime, unique=True)  # One document per day

    # Query counts
    total_queries: int = 0
    successful_responses: int = 0
    failed_responses: int = 0
    out_of_scope_queries: int = 0

    # Intent distribution
    intent_distribution: Dict[str, int] = Field(default_factory=dict)
    response_type_distribution: Dict[str, int] = Field(default_factory=dict)

    # Performance metrics
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    avg_confidence: float = 0.0

    # User metrics
    unique_users: int = 0
    user_ids: List[str] = Field(default_factory=list)  # For tracking unique users
    
    # Satisfaction
    user_satisfaction_avg: float = 0.0
    feedback_count: int = 0
    positive_feedback_count: int = 0
    negative_feedback_count: int = 0

    # Topics
    common_topics: List[Dict[str, Any]] = Field(default_factory=list)
    common_queries: List[str] = Field(default_factory=list)

    # Errors
    error_count: int = 0
    error_types: Dict[str, int] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "chatbot_analytics"
        indexes = [
            [("date", -1)],
        ]

    def record_query(
        self,
        intent: str,
        response_type: str,
        response_time_ms: int,
        confidence: str,
        success: bool,
        user_id: str,
    ):
        """Record a single query's metrics."""
        self.total_queries += 1
        
        if success:
            self.successful_responses += 1
        else:
            self.failed_responses += 1
        
        if intent == "OUT_OF_SCOPE":
            self.out_of_scope_queries += 1

        # Update intent distribution
        self.intent_distribution[intent] = self.intent_distribution.get(intent, 0) + 1
        
        # Update response type distribution
        if response_type:
            self.response_type_distribution[response_type] = \
                self.response_type_distribution.get(response_type, 0) + 1

        # Update response time metrics
        n = self.total_queries
        self.avg_response_time_ms = (
            (self.avg_response_time_ms * (n - 1) + response_time_ms) / n
        )
        if self.min_response_time_ms == 0 or response_time_ms < self.min_response_time_ms:
            self.min_response_time_ms = response_time_ms
        if response_time_ms > self.max_response_time_ms:
            self.max_response_time_ms = response_time_ms

        # Update confidence
        conf_val = {"High": 1.0, "Medium": 0.6, "Low": 0.3}.get(confidence, 0.5)
        self.avg_confidence = (self.avg_confidence * (n - 1) + conf_val) / n

        # Track unique users
        if user_id not in self.user_ids:
            self.user_ids.append(user_id)
            self.unique_users = len(self.user_ids)

        self.updated_at = datetime.utcnow()


# ══════════════════════════════════════════════════════════
# HELPER CLASSES
# ══════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000)
    session_token: Optional[str] = None
    include_student_data: bool = True
    student_data: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    type: str
    intent: str
    content: Dict[str, Any]
    confidence: str
    session_token: Optional[str] = None
    processing_time_ms: Optional[int] = None
    sources: Optional[List[Dict[str, Any]]] = None


class ContextSummary(BaseModel):
    """Summary of conversation context."""
    current_subject: Optional[str] = None
    current_topic: Optional[str] = None
    current_unit: Optional[int] = None
    discussed_topics: List[str] = Field(default_factory=list)
    last_intent: Optional[str] = None
    referenced_faculty: List[str] = Field(default_factory=list)
    student_context: Dict[str, Any] = Field(default_factory=dict)


# ══════════════════════════════════════════════════════════
# EXPORTS
# ══════════════════════════════════════════════════════════

__all__ = [
    # Enums
    "IntentType",
    "ResponseType",
    "ConfidenceLevel",
    # Embedded Models
    "ChatMessageDoc",
    "ConversationContextDoc",
    # Documents
    "ChatSession",
    "ChatMessage",
    "ChatFeedback",
    "ChatbotAnalyticsDoc",
    # Helper Classes
    "ChatRequest",
    "ChatResponse",
    "ContextSummary",
]