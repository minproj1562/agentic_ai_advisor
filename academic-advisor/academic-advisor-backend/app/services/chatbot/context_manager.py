# app/services/chatbot/context_manager.py
"""
Context manager — Beanie/MongoDB based
Handles session continuity, reference resolution, entity extraction
FIXED: Handle both string and enum types for intent
"""

import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Safe import of models
try:
    from app.models.chatbot import (
        ChatSession,
        ChatMessageDoc,
        ConversationContextDoc,
        IntentType,
        ResponseType,
        ConfidenceLevel,
    )
    MODELS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Chatbot models not available: {e}")
    MODELS_AVAILABLE = False
    IntentType = None
    ResponseType = None

try:
    from app.repositories.chat_repository import ChatRepository
    REPO_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ChatRepository not available: {e}")
    REPO_AVAILABLE = False
    ChatRepository = None

# ── Constants ───────────────────────────────────────────
MAX_CONTEXT_MESSAGES = 10
SESSION_TIMEOUT_HOURS = 24
CONTEXT_STACK_SIZE = 5

# ── Subject patterns ────────────────────────────────────
_SUBJECT_PATTERNS = {
    "operating systems": ["operating system", "os ", "os,", "os?", " os"],
    "database management systems": ["dbms", "database", "sql", "db "],
    "data structures and algorithms": ["data structure", "dsa", "algorithms", "ds ", "algo"],
    "computer networks": ["computer network", "cn ", "networking", "networks", " cn"],
    "machine learning": ["machine learning", "ml ", "ml,", " ml"],
    "artificial intelligence": ["artificial intelligence", "ai ", "ai,", " ai", "aiml"],
    "software engineering": ["software engineering", "se ", "sdlc"],
    "cloud computing": ["cloud computing", "cloud ", "aws", "azure"],
    "cryptography & network security": ["cryptography", "crypto", "security", "cns"],
    "design & analysis of algorithms": ["daa", "design analysis algorithm", "algorithm design"],
    "compiler design": ["compiler", "compiler design", "lexical", "parsing"],
    "web technology": ["web technology", "web tech", "web development", "html", "css", "javascript", "web dev"],
    "theory of computation": ["toc", "theory of computation", "automata", "turing"],
    "discrete mathematics": ["discrete math", "discrete structure", "graph theory", "dm "],
    "computer organization": ["computer organization", "coa", "architecture", "co "],
    "object oriented programming": ["oop", "oops", "object oriented"],
    "python programming": ["python", "py "],
    "java programming": ["java", "j2ee"],
    "c programming": ["c programming", " c ", "c language"],
}

# ── Topic keywords ──────────────────────────────────────
_TOPIC_KEYWORDS = [
    # OS topics
    "deadlock", "mutex", "semaphore", "process", "thread", "scheduling",
    "memory management", "paging", "segmentation", "virtual memory",
    "file system", "disk scheduling", "synchronization", "cpu scheduling",
    # DBMS topics
    "normalization", "sql", "joins", "indexing", "transaction",
    "acid", "concurrency", "er diagram", "relational algebra", "bcnf", "3nf",
    # DSA topics
    "sorting", "searching", "tree", "graph", "linked list",
    "stack", "queue", "heap", "hash", "dynamic programming",
    "greedy", "recursion", "bfs", "dfs", "dijkstra", "binary tree",
    # Networks
    "tcp", "udp", "http", "dns", "routing", "ip", "osi",
    "subnetting", "socket", "firewall", "osi model",
    # ML/AI
    "regression", "classification", "clustering", "neural network",
    "decision tree", "random forest", "svm", "knn", "cnn", "rnn",
    "deep learning", "supervised", "unsupervised",
]


def _safe_enum_value(enum_or_string) -> Optional[str]:
    """Safely get value from enum or return string as-is."""
    if enum_or_string is None:
        return None
    if isinstance(enum_or_string, str):
        return enum_or_string
    if hasattr(enum_or_string, 'value'):
        return enum_or_string.value
    return str(enum_or_string)


class ContextManager:
    """Manages conversation context and session state."""

    def __init__(self):
        if REPO_AVAILABLE and ChatRepository:
            self.repo = ChatRepository()
        else:
            self.repo = None
            logger.warning("ChatRepository not available - context persistence disabled")

    # ══════════════════════════════════════════════════════
    # PUBLIC API
    # ══════════════════════════════════════════════════════

    async def get_or_create_session(
        self,
        user_id: str,
        user_type: str,
        token: Optional[str] = None
    ):
        """Get existing session (if not expired) or create new one."""
        if self.repo:
            return await self.repo.get_or_create_session(user_id, user_type, token)
        
        # Fallback: create a mock session
        from datetime import datetime, timedelta
        import uuid
        
        class MockSession:
            def __init__(self):
                self.id = str(uuid.uuid4())
                self.user_id = user_id
                self.user_type = user_type
                self.session_token = str(uuid.uuid4())
                self.messages = []
                self.context = type('Context', (), {
                    'current_subject': None,
                    'current_topic': None,
                    'current_unit': None,
                    'discussed_topics': [],
                    'discussed_subjects': [],
                    'last_intent': None,
                    'last_response_type': None,
                    'referenced_faculty': [],
                    'student_context': {},
                    'follow_up_expected': False,
                    'context_stack': [],
                    'updated_at': datetime.utcnow(),
                    'push_to_stack': lambda self, entry, max_size=5: None,
                })()
                self.is_active = True
                self.created_at = datetime.utcnow()
                self.expires_at = datetime.utcnow() + timedelta(hours=24)
        
        return MockSession()

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent=None,
        response_type=None,
        confidence=None,
        structured_response: Optional[Dict] = None,
        sources: Optional[List] = None,
        processing_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        **kwargs,
    ):
        """Add a message and update context accordingly."""
        if self.repo:
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
                await self._update_context_from_user(session_id, content, getattr(msg, 'id', 'unknown'))
            elif role == "assistant" and intent:
                await self._update_context_from_assistant(session_id, intent, response_type)

            return msg
        
        return None

    async def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        """Return a summary of the current conversation context."""
        if not self.repo:
            return {}
            
        ctx = await self.repo.get_context(session_id)
        if not ctx:
            return {}
        
        return {
            "current_subject": ctx.current_subject,
            "current_subject_code": getattr(ctx, 'current_subject_code', None),
            "current_topic": ctx.current_topic,
            "current_unit": getattr(ctx, 'current_unit', None),
            "discussed_topics": ctx.discussed_topics or [],
            "discussed_subjects": getattr(ctx, 'discussed_subjects', []) or [],
            "last_intent": _safe_enum_value(ctx.last_intent),
            "last_response_type": _safe_enum_value(ctx.last_response_type),
            "referenced_faculty": ctx.referenced_faculty or [],
            "student_context": ctx.student_context or {},
            "follow_up_expected": getattr(ctx, 'follow_up_expected', False),
        }

    async def resolve_references(self, query: str, session_id: str) -> str:
        """Replace pronouns with actual subject/topic/faculty from context."""
        if not self.repo:
            return query
            
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
                try:
                    resolved = re.sub(pattern, replacement, resolved, flags=re.IGNORECASE)
                except re.error:
                    continue

        return resolved

    async def enrich_with_student_data(self, session_id: str, data: Dict[str, Any]):
        """Attach student performance data to the context."""
        if not self.repo:
            return
            
        ctx = await self.repo.get_context(session_id)
        if ctx:
            ctx.student_context = data
            ctx.updated_at = datetime.utcnow()
            await self.repo.update_context(session_id, ctx)

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = MAX_CONTEXT_MESSAGES
    ) -> List:
        """Retrieve recent messages."""
        if self.repo:
            return await self.repo.get_messages(session_id, limit)
        return []

    async def clear_session(self, session_id: str):
        """Mark a session as inactive."""
        if self.repo:
            await self.repo.deactivate_session(session_id)

    async def set_follow_up_expected(self, session_id: str, expected: bool = True):
        """Mark that a follow-up question is expected."""
        if not self.repo:
            return
            
        ctx = await self.repo.get_context(session_id)
        if ctx:
            ctx.follow_up_expected = expected
            ctx.updated_at = datetime.utcnow()
            await self.repo.update_context(session_id, ctx)

    # ══════════════════════════════════════════════════════
    # FOLLOW-UP RESOLUTION & TOPIC CONTEXT (NEW)
    # ══════════════════════════════════════════════════════

    _FOLLOW_UP_PATTERNS = [
        re.compile(r'^explain\s*(it\s*)?(in\s+detail|more|further|deeply?)?\s*$', re.I),
        re.compile(r'^(tell|explain)\s+(me\s+)?(more|in\s+detail|in[\s-]+depth)\s*$', re.I),
        re.compile(r'^(more|details?|elaborate|expand|go\s+deeper|in[\s-]+depth)\s*$', re.I),
        re.compile(r'^what\s+(else|more)\s*$', re.I),
        re.compile(r'^(yes|yeah|yep|continue|go\s+on|please)\s*$', re.I),
        re.compile(r'^(can\s+you|could\s+you)\s+(explain|elaborate|expand|detail)', re.I),
    ]

    _DETAIL_KEYWORDS = re.compile(
        r'\b(?:in\s+detail|in[\s-]+depth|detailed|elaborate|more\s+about|'
        r'explain\s+more|go\s+deeper|comprehensive|thorough|with\s+examples?)\b',
        re.I,
    )

    async def resolve_follow_up(
        self, query: str, session_id: str
    ) -> tuple:
        """
        Detect follow-up / detail queries and enrich with context.
        Returns: (resolved_query, is_detailed, context_topic, context_subject)
        """
        ql = query.lower().strip().rstrip("?!.")
        is_detailed = bool(self._DETAIL_KEYWORDS.search(ql))
        is_follow_up = any(p.match(ql) for p in self._FOLLOW_UP_PATTERNS)

        if not is_follow_up and not is_detailed:
            return query, False, None, None

        if not self.repo:
            return query, is_detailed, None, None

        try:
            ctx = await self.repo.get_context(session_id)
            if not ctx:
                return query, is_detailed, None, None

            topic = ctx.current_topic
            subject = ctx.current_subject

            if is_follow_up and topic:
                return f"Explain {topic} in detail", True, topic, subject
            if is_detailed and topic:
                return f"Explain {topic} in detail", True, topic, subject
            if is_follow_up and subject:
                return f"Tell me about {subject}", False, None, subject

            return query, is_detailed, topic, subject
        except Exception as e:
            logger.warning(f"resolve_follow_up error: {e}")
            return query, is_detailed, None, None

    async def update_topic_context(
        self,
        session_id: str,
        topic: Optional[str] = None,
        subject: Optional[str] = None,
    ):
        """Write the current topic/subject back into context after a response."""
        if not self.repo:
            return
        try:
            ctx = await self.repo.get_context(session_id)
            if not ctx:
                return
            if topic:
                ctx.current_topic = topic
                if topic not in (ctx.discussed_topics or []):
                    ctx.discussed_topics = (ctx.discussed_topics or []) + [topic]
            if subject:
                ctx.current_subject = subject
                discussed = getattr(ctx, 'discussed_subjects', []) or []
                if subject not in discussed:
                    if hasattr(ctx, 'discussed_subjects'):
                        ctx.discussed_subjects = discussed + [subject]
            ctx.updated_at = datetime.utcnow()
            await self.repo.update_context(session_id, ctx)
        except Exception as e:
            logger.warning(f"update_topic_context error: {e}")

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
        if not self.repo:
            return
            
        ctx = await self.repo.get_context(session_id)
        if not ctx:
            return

        # Extract entities from the message
        entities = self._extract_entities(content)

        # Update context with extracted entities
        if entities.get("subject"):
            ctx.current_subject = entities["subject"]
            if hasattr(ctx, 'discussed_subjects') and ctx.current_subject not in ctx.discussed_subjects:
                ctx.discussed_subjects.append(ctx.current_subject)
        
        if entities.get("subject_code"):
            if hasattr(ctx, 'current_subject_code'):
                ctx.current_subject_code = entities["subject_code"]
        
        if entities.get("topic"):
            ctx.current_topic = entities["topic"]
            if ctx.current_topic not in ctx.discussed_topics:
                ctx.discussed_topics.append(ctx.current_topic)
        
        if entities.get("unit"):
            if hasattr(ctx, 'current_unit'):
                ctx.current_unit = entities["unit"]
        
        if entities.get("faculty"):
            if entities["faculty"] not in ctx.referenced_faculty:
                ctx.referenced_faculty.append(entities["faculty"])
            # Keep only last 5 faculty references
            ctx.referenced_faculty = ctx.referenced_faculty[-5:]

        # Push to context stack
        if hasattr(ctx, 'push_to_stack'):
            ctx.push_to_stack({
                "message_id": message_id,
                "content": content[:100],
                "entities": entities,
                "timestamp": datetime.utcnow().isoformat(),
            }, max_size=CONTEXT_STACK_SIZE)

        ctx.updated_at = datetime.utcnow()
        await self.repo.update_context(session_id, ctx)

    async def _update_context_from_assistant(
        self,
        session_id: str,
        intent,
        response_type=None
    ):
        """Update context after an assistant message."""
        if not self.repo:
            return
            
        ctx = await self.repo.get_context(session_id)
        if not ctx:
            return

        # Store as string to avoid enum serialization issues
        ctx.last_intent = _safe_enum_value(intent)
        ctx.last_response_type = _safe_enum_value(response_type)
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