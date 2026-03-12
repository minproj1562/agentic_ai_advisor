# app/services/chatbot/context_manager.py
"""
Context manager — Beanie/MongoDB based
Handles session continuity, reference resolution, entity extraction
"""

import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models.chatbot import (
    ChatSession,
    ChatMessageDoc,
    ConversationContextDoc,
    IntentType,
    ResponseType,
    ConfidenceLevel,
)
from app.repositories.chat_repository import ChatRepository

logger = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────────
MAX_CONTEXT_MESSAGES = 10
SESSION_TIMEOUT_HOURS = 24
CONTEXT_STACK_SIZE = 5

# ── Subject patterns ────────────────────────────────────
_SUBJECT_PATTERNS = {
    "operating systems": ["operating system", "os ", "os,"],
    "database management systems": ["dbms", "database", "sql"],
    "data structures and algorithms": ["data structure", "dsa", "algorithms", "ds "],
    "computer networks": ["computer network", "cn ", "networking", "networks"],
    "machine learning": ["machine learning", "ml ", "ml,"],
    "artificial intelligence": ["artificial intelligence", "ai ", "ai,"],
    "software engineering": ["software engineering", "se ", "sdlc"],
    "cloud computing": ["cloud computing", "cloud ", "aws", "azure"],
    "cryptography & network security": ["cryptography", "crypto", "security", "cns"],
    "design & analysis of algorithms": ["daa", "design analysis algorithm", "algorithm design"],
    "compiler design": ["compiler", "compiler design", "lexical", "parsing"],
    "web technology": ["web technology", "web tech", "web development", "html", "css", "javascript"],
    "theory of computation": ["toc", "theory of computation", "automata", "turing"],
    "discrete mathematics": ["discrete math", "discrete structure", "graph theory"],
    "computer organization": ["computer organization", "coa", "architecture"],
}

# ── Topic keywords ──────────────────────────────────────
_TOPIC_KEYWORDS = [
    # OS topics
    "deadlock", "mutex", "semaphore", "process", "thread", "scheduling",
    "memory management", "paging", "segmentation", "virtual memory",
    "file system", "disk scheduling", "synchronization",
    # DBMS topics
    "normalization", "sql", "joins", "indexing", "transaction",
    "acid", "concurrency", "er diagram", "relational algebra",
    # DSA topics
    "sorting", "searching", "tree", "graph", "linked list",
    "stack", "queue", "heap", "hash", "dynamic programming",
    "greedy", "recursion", "bfs", "dfs", "dijkstra",
    # Networks
    "tcp", "udp", "http", "dns", "routing", "ip", "osi",
    "subnetting", "socket", "firewall",
    # ML/AI
    "regression", "classification", "clustering", "neural network",
    "decision tree", "random forest", "svm", "knn", "cnn", "rnn",
]


class ContextManager:
    """Manages conversation context and session state."""

    def __init__(self):
        self.repo = ChatRepository()

    # ══════════════════════════════════════════════════════
    # PUBLIC API
    # ══════════════════════════════════════════════════════

    async def get_or_create_session(
        self,
        user_id: str,
        user_type: str,
        token: Optional[str] = None
    ) -> ChatSession:
        """Get existing session (if not expired) or create new one."""
        return await self.repo.get_or_create_session(user_id, user_type, token)

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: Optional[IntentType] = None,
        response_type: Optional[ResponseType] = None,
        confidence: Optional[ConfidenceLevel] = None,
        structured_response: Optional[Dict] = None,
        sources: Optional[List] = None,
        processing_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        **kwargs,
    ) -> ChatMessageDoc:
        """Add a message and update context accordingly."""
        msg = await self.repo.add_message(
            session_id=session_id,
            role=role,
            content=content,
            intent=intent,
            response_type=response_type,
            confidence=confidence,
            structured_response=structured_response,
            sources=sources,
            processing_time_ms=processing_time_ms,
            tokens_used=tokens_used,
            **kwargs,
        )

        # Update context based on role
        if role == "user":
            await self._update_context_from_user(session_id, content, msg.id)
        elif role == "assistant" and intent:
            await self._update_context_from_assistant(session_id, intent, response_type)

        return msg

    async def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        """Return a summary of the current conversation context."""
        ctx = await self.repo.get_context(session_id)
        if not ctx:
            return {}
        
        return {
            "current_subject": ctx.current_subject,
            "current_subject_code": ctx.current_subject_code,
            "current_topic": ctx.current_topic,
            "current_unit": ctx.current_unit,
            "discussed_topics": ctx.discussed_topics,
            "discussed_subjects": ctx.discussed_subjects,
            "last_intent": ctx.last_intent.value if ctx.last_intent else None,
            "last_response_type": ctx.last_response_type.value if ctx.last_response_type else None,
            "referenced_faculty": ctx.referenced_faculty,
            "student_context": ctx.student_context,
            "follow_up_expected": ctx.follow_up_expected,
        }

    async def resolve_references(self, query: str, session_id: str) -> str:
        """Replace pronouns with actual subject/topic/faculty from context."""
        ctx = await self.repo.get_context(session_id)
        if not ctx:
            return query

        resolved = query

        # Subject/topic references
        replacements = {
            r"\bit\b": ctx.current_topic,
            r"\bthis\b": ctx.current_topic,
            r"\bthat\b": ctx.current_topic,
            r"\bthis subject\b": ctx.current_subject,
            r"\bthe subject\b": ctx.current_subject,
            r"\bthis topic\b": ctx.current_topic,
            r"\bthe topic\b": ctx.current_topic,
            r"\bthis course\b": ctx.current_subject,
        }

        # Faculty references
        if ctx.referenced_faculty:
            last_faculty = ctx.referenced_faculty[-1]
            faculty_replacements = {
                r"\bhe\b": last_faculty,
                r"\bshe\b": last_faculty,
                r"\bthey\b": last_faculty,
                r"\bthem\b": last_faculty,
                r"\bhim\b": last_faculty,
                r"\bher\b": last_faculty,
                r"\bthis professor\b": last_faculty,
                r"\bthat professor\b": last_faculty,
                r"\bthe professor\b": last_faculty,
                r"\bthis faculty\b": last_faculty,
            }
            replacements.update(faculty_replacements)

        # Apply substitutions
        for pattern, replacement in replacements.items():
            if replacement:
                resolved = re.sub(pattern, replacement, resolved, flags=re.IGNORECASE)

        return resolved

    async def enrich_with_student_data(self, session_id: str, data: Dict[str, Any]):
        """Attach student performance data to the context."""
        ctx = await self.repo.get_context(session_id)
        if ctx:
            ctx.student_context = data
            ctx.updated_at = datetime.utcnow()
            await self.repo.update_context(session_id, ctx)

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = MAX_CONTEXT_MESSAGES
    ) -> List[ChatMessageDoc]:
        """Retrieve recent messages."""
        return await self.repo.get_messages(session_id, limit)

    async def clear_session(self, session_id: str):
        """Mark a session as inactive."""
        await self.repo.deactivate_session(session_id)

    async def set_follow_up_expected(self, session_id: str, expected: bool = True):
        """Mark that a follow-up question is expected."""
        ctx = await self.repo.get_context(session_id)
        if ctx:
            ctx.follow_up_expected = expected
            ctx.updated_at = datetime.utcnow()
            await self.repo.update_context(session_id, ctx)

    # ══════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ══════════════════════════════════════════════════════

    async def _update_context_from_user(
        self,
        session_id: str,
        content: str,
        message_id: str
    ):
        """Update context after a user message."""
        ctx = await self.repo.get_context(session_id)
        if not ctx:
            return

        # Extract entities from the message
        entities = self._extract_entities(content)

        # Update context with extracted entities
        if entities.get("subject"):
            ctx.current_subject = entities["subject"]
            if ctx.current_subject not in ctx.discussed_subjects:
                ctx.discussed_subjects.append(ctx.current_subject)
        
        if entities.get("subject_code"):
            ctx.current_subject_code = entities["subject_code"]
        
        if entities.get("topic"):
            ctx.current_topic = entities["topic"]
            if ctx.current_topic not in ctx.discussed_topics:
                ctx.discussed_topics.append(ctx.current_topic)
        
        if entities.get("unit"):
            ctx.current_unit = entities["unit"]
        
        if entities.get("faculty"):
            if entities["faculty"] not in ctx.referenced_faculty:
                ctx.referenced_faculty.append(entities["faculty"])
            # Keep only last 5 faculty references
            ctx.referenced_faculty = ctx.referenced_faculty[-5:]

        # Push to context stack
        ctx.push_to_stack({
            "message_id": message_id,
            "content": content[:100],  # First 100 chars
            "entities": entities,
            "timestamp": datetime.utcnow().isoformat(),
        }, max_size=CONTEXT_STACK_SIZE)

        ctx.updated_at = datetime.utcnow()
        await self.repo.update_context(session_id, ctx)

    async def _update_context_from_assistant(
        self,
        session_id: str,
        intent: IntentType,
        response_type: Optional[ResponseType] = None
    ):
        """Update context after an assistant message."""
        ctx = await self.repo.get_context(session_id)
        if not ctx:
            return

        ctx.last_intent = intent
        ctx.last_response_type = response_type
        ctx.updated_at = datetime.utcnow()
        
        await self.repo.update_context(session_id, ctx)

    @staticmethod
    def _extract_entities(text: str) -> Dict[str, Any]:
        """Extract academic entities from text."""
        entities: Dict[str, Any] = {}
        text_lower = f" {text.lower()} "

        # Subject extraction
        for subject, patterns in _SUBJECT_PATTERNS.items():
            if any(p in text_lower for p in patterns):
                entities["subject"] = subject
                break

        # Subject code extraction (e.g., CSC401, ITPCC301)
        code_match = re.search(r'\b([A-Z]{2,4}\d{3,4})\b', text, re.IGNORECASE)
        if code_match:
            entities["subject_code"] = code_match.group(1).upper()

        # Unit number extraction
        unit_match = re.search(r'unit\s*(\d+)', text_lower)
        if unit_match:
            entities["unit"] = int(unit_match.group(1))

        # Topic extraction
        for keyword in _TOPIC_KEYWORDS:
            if keyword in text_lower:
                entities["topic"] = keyword
                break

        # Faculty name extraction (Dr. X, Prof. Y, Professor Z)
        faculty_match = re.search(
            r'\b(dr\.?|prof\.?|professor)\s+([a-z]+(?:\s+[a-z]+)?)',
            text,
            re.IGNORECASE,
        )
        if faculty_match:
            entities["faculty"] = faculty_match.group(2).strip().title()

        return entities