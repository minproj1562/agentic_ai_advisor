# academic-advisor/academic-advisor-backend/app/repositories/chat_repository.py
"""
Chat session / message / feedback data access layer
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.models.chatbot import (
    ChatSession, ChatMessageDoc, ConversationContextDoc,
    ChatFeedback, IntentType, ConfidenceLevel,
)

logger = logging.getLogger(__name__)


class ChatRepository:

    # ── Sessions ─────────────────────────────────────────

    async def get_session_by_token(self, token: str) -> Optional[ChatSession]:
        return await ChatSession.find_one(
            ChatSession.session_token == token,
            ChatSession.is_active == True,
            ChatSession.expires_at > datetime.utcnow(),
        )

    async def get_active_session(self, user_id: str) -> Optional[ChatSession]:
        return await ChatSession.find_one(
            ChatSession.user_id == user_id,
            ChatSession.is_active == True,
            ChatSession.expires_at > datetime.utcnow(),
        )

    async def create_session(
        self, user_id: str, user_type: str = "student"
    ) -> ChatSession:
        session = ChatSession(
            user_id=user_id,
            user_type=user_type,
            session_token=str(uuid.uuid4()),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            metadata={"created_from": "chatbot"},
        )
        await session.insert()
        return session

    async def get_or_create_session(
        self,
        user_id: str,
        user_type: str,
        session_token: Optional[str] = None,
    ) -> ChatSession:
        if session_token:
            s = await self.get_session_by_token(session_token)
            if s:
                s.updated_at = datetime.utcnow()
                await s.save()
                return s
        s = await self.get_active_session(user_id)
        if s:
            return s
        return await self.create_session(user_id, user_type)

    # ── Messages ─────────────────────────────────────────

    async def add_message(self, session_id: str, role: str, content: str, **kw) -> ChatMessageDoc:
        session = await ChatSession.find_one(ChatSession.id == session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        msg = ChatMessageDoc(role=role, content=content, **kw)
        session.messages.append(msg)
        session.updated_at = datetime.utcnow()

        # cap at 50
        if len(session.messages) > 50:
            session.messages = session.messages[-50:]

        await session.save()
        return msg

    async def get_messages(
        self, session_id: str, limit: int = 20
    ) -> List[ChatMessageDoc]:
        session = await ChatSession.find_one(ChatSession.id == session_id)
        return session.messages[-limit:] if session else []

    # ── Context ──────────────────────────────────────────

    async def update_context(self, session_id: str, ctx: ConversationContextDoc):
        session = await ChatSession.find_one(ChatSession.id == session_id)
        if session:
            session.context = ctx
            session.updated_at = datetime.utcnow()
            await session.save()

    async def get_context(self, session_id: str) -> Optional[ConversationContextDoc]:
        session = await ChatSession.find_one(ChatSession.id == session_id)
        return session.context if session else None

    async def deactivate_session(self, session_id: str):
        session = await ChatSession.find_one(ChatSession.id == session_id)
        if session:
            session.is_active = False
            await session.save()

    # ── Feedback (Task 22) ───────────────────────────────

    async def save_feedback(self, fb: ChatFeedback) -> ChatFeedback:
        await fb.insert()
        return fb

    async def get_feedback_for_session(self, session_id: str) -> List[ChatFeedback]:
        return await ChatFeedback.find(
            ChatFeedback.session_id == session_id
        ).to_list()

    async def get_avg_rating(self, days: int = 30) -> float:
        since = datetime.utcnow() - timedelta(days=days)
        fbs = await ChatFeedback.find(ChatFeedback.created_at >= since).to_list()
        return sum(f.rating for f in fbs) / len(fbs) if fbs else 0.0

    # ── History ──────────────────────────────────────────

    async def get_user_sessions(
        self, user_id: str, limit: int = 10
    ) -> List[ChatSession]:
        return (
            await ChatSession.find(ChatSession.user_id == user_id)
            .sort(-ChatSession.updated_at)
            .limit(limit)
            .to_list()
        )