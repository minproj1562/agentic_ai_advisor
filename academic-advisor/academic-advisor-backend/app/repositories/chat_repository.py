# app/repositories/chat_repository.py
"""
Chat session / message / feedback data access layer
Fixed to work with updated chatbot.py models
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.models.chatbot import (
    ChatSession,
    ChatMessage,
    ChatMessageDoc,
    ConversationContextDoc,
    ChatFeedback,
    IntentType,
    ResponseType,
    ConfidenceLevel,
)

logger = logging.getLogger(__name__)


class ChatRepository:
    """Repository for chat session and message operations."""

    # ══════════════════════════════════════════════════════
    # SESSION OPERATIONS
    # ══════════════════════════════════════════════════════

    async def get_session_by_token(self, token: str) -> Optional[ChatSession]:
        """Get an active session by its token."""
        try:
            return await ChatSession.find_one(
                ChatSession.session_token == token,
                ChatSession.is_active == True,
                ChatSession.expires_at > datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Error getting session by token: {e}")
            return None

    async def get_active_session(self, user_id: str) -> Optional[ChatSession]:
        """Get the active session for a user."""
        try:
            return await ChatSession.find_one(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True,
                ChatSession.expires_at > datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Error getting active session: {e}")
            return None

    async def create_session(
        self,
        user_id: str,
        user_type: str = "student"
    ) -> ChatSession:
        """Create a new chat session."""
        try:
            session = ChatSession(
                user_id=user_id,
                user_type=user_type,
                session_token=str(uuid.uuid4()),
                expires_at=datetime.utcnow() + timedelta(hours=24),
                metadata={"created_from": "chatbot", "version": "2.0"},
            )
            await session.insert()
            logger.info(f"Created new session for user {user_id}: {session.session_token}")
            return session
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise

    async def get_or_create_session(
        self,
        user_id: str,
        user_type: str,
        session_token: Optional[str] = None,
    ) -> ChatSession:
        """Get existing session or create a new one."""
        try:
            # Try to get session by token first
            if session_token:
                session = await self.get_session_by_token(session_token)
                if session:
                    session.updated_at = datetime.utcnow()
                    session.last_activity = datetime.utcnow()
                    await session.save()
                    return session

            # Try to get active session for user
            session = await self.get_active_session(user_id)
            if session:
                session.last_activity = datetime.utcnow()
                await session.save()
                return session

            # Create new session
            return await self.create_session(user_id, user_type)
        except Exception as e:
            logger.error(f"Error in get_or_create_session: {e}")
            raise

    async def update_session(self, session: ChatSession) -> ChatSession:
        """Save changes to a session."""
        try:
            session.updated_at = datetime.utcnow()
            await session.save()
            return session
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            raise

    async def deactivate_session(self, session_id: str):
        """Mark a session as inactive."""
        try:
            session = await ChatSession.get(session_id)
            if session:
                session.is_active = False
                session.updated_at = datetime.utcnow()
                await session.save()
                logger.info(f"Deactivated session {session_id}")
        except Exception as e:
            logger.error(f"Error deactivating session: {e}")

    async def cleanup_expired_sessions(self) -> int:
        """Cleanup expired sessions."""
        try:
            result = await ChatSession.find(
                ChatSession.expires_at < datetime.utcnow(),
                ChatSession.is_active == True
            ).update({"$set": {"is_active": False}})
            count = result.modified_count if result else 0
            logger.info(f"Cleaned up {count} expired sessions")
            return count
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            return 0

    # ══════════════════════════════════════════════════════
    # MESSAGE OPERATIONS
    # ══════════════════════════════════════════════════════

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: Optional[IntentType] = None,
        response_type: Optional[ResponseType] = None,
        confidence: Optional[ConfidenceLevel] = None,
        structured_response: Optional[Dict[str, Any]] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
        processing_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        **kwargs
    ) -> ChatMessageDoc:
        """Add a message to a session."""
        try:
            session = await ChatSession.get(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            # Create embedded message
            message = ChatMessageDoc(
                role=role,
                content=content,
                intent=intent,
                response_type=response_type,
                confidence=confidence,
                structured_response=structured_response,
                sources=sources or [],
                processing_time_ms=processing_time_ms,
                tokens_used=tokens_used,
            )

            # Add to session
            session.add_message(message, max_messages=50)
            await session.save()

            # Also save to standalone collection for analytics
            await self._archive_message(
                session_id=str(session.id),
                user_id=session.user_id,
                message=message
            )

            return message
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            raise

    async def _archive_message(
        self,
        session_id: str,
        user_id: str,
        message: ChatMessageDoc
    ):
        """Archive message to standalone collection."""
        try:
            archived = ChatMessage(
                session_id=session_id,
                user_id=user_id,
                role=message.role,
                content=message.content,
                intent=message.intent,
                response_type=message.response_type,
                confidence=message.confidence,
                structured_response=message.structured_response,
                sources=message.sources,
                processing_time_ms=message.processing_time_ms,
                tokens_used=message.tokens_used,
                created_at=message.created_at,
            )
            await archived.insert()
        except Exception as e:
            logger.warning(f"Failed to archive message: {e}")

    async def get_messages(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[ChatMessageDoc]:
        """Get recent messages from a session."""
        try:
            session = await ChatSession.get(session_id)
            if session:
                return session.get_recent_messages(limit)
            return []
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []

    async def get_archived_messages(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[ChatMessage]:
        """Get archived messages from standalone collection."""
        try:
            return await ChatMessage.find(
                ChatMessage.session_id == session_id
            ).sort(-ChatMessage.created_at).limit(limit).to_list()
        except Exception as e:
            logger.error(f"Error getting archived messages: {e}")
            return []

    # ══════════════════════════════════════════════════════
    # CONTEXT OPERATIONS
    # ══════════════════════════════════════════════════════

    async def update_context(
        self,
        session_id: str,
        ctx: ConversationContextDoc
    ):
        """Update the conversation context."""
        try:
            session = await ChatSession.get(session_id)
            if session:
                session.context = ctx
                session.updated_at = datetime.utcnow()
                await session.save()
        except Exception as e:
            logger.error(f"Error updating context: {e}")

    async def get_context(
        self,
        session_id: str
    ) -> Optional[ConversationContextDoc]:
        """Get the conversation context."""
        try:
            session = await ChatSession.get(session_id)
            return session.context if session else None
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return None

    # ══════════════════════════════════════════════════════
    # FEEDBACK OPERATIONS
    # ══════════════════════════════════════════════════════

    async def save_feedback(self, feedback: ChatFeedback) -> ChatFeedback:
        """Save user feedback."""
        try:
            await feedback.insert()
            logger.info(f"Saved feedback for session {feedback.session_id}")
            return feedback
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            raise

    async def get_feedback_for_session(
        self,
        session_id: str
    ) -> List[ChatFeedback]:
        """Get all feedback for a session."""
        try:
            return await ChatFeedback.find(
                ChatFeedback.session_id == session_id
            ).to_list()
        except Exception as e:
            logger.error(f"Error getting feedback: {e}")
            return []

    async def get_feedback_stats(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get feedback statistics."""
        try:
            since = datetime.utcnow() - timedelta(days=days)
            feedbacks = await ChatFeedback.find(
                ChatFeedback.created_at >= since
            ).to_list()

            if not feedbacks:
                return {
                    "total": 0,
                    "avg_rating": 0,
                    "positive_count": 0,
                    "negative_count": 0
                }

            total = len(feedbacks)
            avg_rating = sum(f.rating for f in feedbacks) / total
            positive = len([f for f in feedbacks if f.rating >= 4])
            negative = len([f for f in feedbacks if f.rating <= 2])

            return {
                "total": total,
                "avg_rating": round(avg_rating, 2),
                "positive_count": positive,
                "negative_count": negative,
                "positive_rate": round(positive / total * 100, 1) if total else 0
            }
        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}")
            return {}

    # ══════════════════════════════════════════════════════
    # HISTORY OPERATIONS
    # ══════════════════════════════════════════════════════

    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 10,
        include_inactive: bool = False
    ) -> List[ChatSession]:
        """Get sessions for a user."""
        try:
            query = {"user_id": user_id}
            if not include_inactive:
                query["is_active"] = True

            return await ChatSession.find(
                query
            ).sort(-ChatSession.updated_at).limit(limit).to_list()
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []

    async def get_session_summary(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a summary of a session."""
        try:
            session = await ChatSession.get(session_id)
            if not session:
                return None

            return {
                "session_id": str(session.id),
                "session_token": session.session_token,
                "user_id": session.user_id,
                "message_count": session.message_count,
                "is_active": session.is_active,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "context": {
                    "current_subject": session.context.current_subject,
                    "current_topic": session.context.current_topic,
                    "last_intent": session.context.last_intent,
                    "discussed_topics": session.context.discussed_topics,
                }
            }
        except Exception as e:
            logger.error(f"Error getting session summary: {e}")
            return None