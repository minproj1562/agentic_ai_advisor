# academic-advisor/academic-advisor-backend/app/services/chatbot/context_manager.py
"""
Context manager — Beanie/MongoDB based
Handles session continuity, reference resolution, entity extraction
"""

import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models.chatbot import (
    ChatSession, ChatMessageDoc, ConversationContextDoc, IntentType,
)
from app.repositories.chat_repository import ChatRepository

logger = logging.getLogger(__name__)

_SUBJECT_PATTERNS = {
    "operating systems":         ["operating system", "os "],
    "database management systems": ["dbms", "database"],
    "data structures and algorithms": ["data structure", "dsa", "algorithms"],
    "computer networks":         ["computer network", "cn ", "networking"],
    "machine learning":          ["machine learning", "ml "],
    "artificial intelligence":   ["artificial intelligence", "ai "],
    "software engineering":      ["software engineering", "se "],
    "cloud computing":           ["cloud computing", "cloud"],
    "cryptography & network security": ["cryptography", "crypto", "security"],
    "design & analysis of algorithms": ["daa", "design analysis algorithm"],
}

_TOPIC_KEYWORDS = [
    "deadlock", "mutex", "semaphore", "normalization", "sql",
    "sorting", "searching", "tree", "graph", "linked list",
    "tcp", "udp", "http", "dns", "routing", "paging",
    "regression", "classification", "clustering", "neural network",
    "process", "thread", "scheduling", "memory management",
]


class ContextManager:
    MAX_STACK = 5

    def __init__(self):
        self.repo = ChatRepository()

    # ── Public API ───────────────────────────────────────

    async def get_or_create_session(
        self, user_id: str, user_type: str, token: Optional[str] = None
    ) -> ChatSession:
        return await self.repo.get_or_create_session(user_id, user_type, token)

    async def add_message(self, session_id: str, role: str, content: str, **kw):
        msg = await self.repo.add_message(session_id, role, content, **kw)
        if role == "user":
            await self._update_ctx_user(session_id, content)
        elif role == "assistant" and kw.get("intent"):
            await self._update_ctx_assistant(session_id, kw["intent"])
        return msg

    async def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        ctx = await self.repo.get_context(session_id)
        if not ctx:
            return {}
        return {
            "current_subject": ctx.current_subject,
            "current_topic": ctx.current_topic,
            "current_unit": ctx.current_unit,
            "discussed_topics": ctx.discussed_topics,
            "last_intent": ctx.last_intent.value if ctx.last_intent else None,
            "referenced_faculty": ctx.referenced_faculty,
            "student_context": ctx.student_context,
        }

    async def resolve_references(self, query: str, session_id: str) -> str:
        ctx = await self.repo.get_context(session_id)
        if not ctx:
            return query
        resolved = query
        pairs = {
            r"\bit\b": ctx.current_topic,
            r"\bthis subject\b": ctx.current_subject,
            r"\bthe subject\b": ctx.current_subject,
            r"\bthat\b": ctx.current_topic,
        }
        for pat, rep in pairs.items():
            if rep:
                resolved = re.sub(pat, rep, resolved, flags=re.IGNORECASE)
        return resolved

    async def enrich_with_student_data(
        self, session_id: str, data: Dict[str, Any]
    ):
        ctx = await self.repo.get_context(session_id)
        if ctx:
            ctx.student_context = data
            ctx.updated_at = datetime.utcnow()
            await self.repo.update_context(session_id, ctx)

    async def get_conversation_history(
        self, session_id: str, limit: int = 20
    ) -> List[ChatMessageDoc]:
        return await self.repo.get_messages(session_id, limit)

    async def clear_session(self, session_id: str):
        await self.repo.deactivate_session(session_id)

    # ── Private helpers ──────────────────────────────────

    async def _update_ctx_user(self, sid: str, content: str):
        ctx = await self.repo.get_context(sid)
        if not ctx:
            return
        ent = self._extract_entities(content)
        if ent.get("subject"):
            ctx.current_subject = ent["subject"]
        if ent.get("topic"):
            ctx.current_topic = ent["topic"]
        if ent.get("unit"):
            ctx.current_unit = ent["unit"]
        if ent.get("faculty"):
            ctx.referenced_faculty.append(ent["faculty"])

        ctx.context_stack.append(
            {"content": content, "entities": ent,
             "ts": datetime.utcnow().isoformat()}
        )
        ctx.context_stack = ctx.context_stack[-self.MAX_STACK:]
        ctx.updated_at = datetime.utcnow()
        await self.repo.update_context(sid, ctx)

    async def _update_ctx_assistant(self, sid: str, intent):
        ctx = await self.repo.get_context(sid)
        if not ctx:
            return
        ctx.last_intent = intent
        if ctx.current_topic and ctx.current_topic not in ctx.discussed_topics:
            ctx.discussed_topics.append(ctx.current_topic)
        ctx.updated_at = datetime.utcnow()
        await self.repo.update_context(sid, ctx)

    @staticmethod
    def _extract_entities(text: str) -> Dict[str, Any]:
        ent: Dict[str, Any] = {}
        low = f" {text.lower()} "

        for subj, patterns in _SUBJECT_PATTERNS.items():
            if any(p in low for p in patterns):
                ent["subject"] = subj
                break

        m = re.search(r"unit\s*(\d+)", low)
        if m:
            ent["unit"] = int(m.group(1))

        for kw in _TOPIC_KEYWORDS:
            if kw in low:
                ent["topic"] = kw
                break

        fm = re.search(
            r"\b(dr\.?|prof\.?|professor)\s+([a-z]+(?:\s+[a-z]+)?)",
            text, re.IGNORECASE,
        )
        if fm:
            ent["faculty"] = fm.group(2).strip()
        return ent