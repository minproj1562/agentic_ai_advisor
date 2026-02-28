# academic-advisor/academic-advisor-backend/app/services/chatbot/chatbot_service.py
"""
Main Chatbot Orchestrator  (Task 12)
Unified service on Beanie/MongoDB
Routes intents to appropriate handlers
"""

import time
import json
import logging
from typing import Dict, Any, Optional, List

from app.services.chatbot.intent_classifier import IntentClassifier, IntentType
from app.services.chatbot.context_manager import ContextManager
from app.services.chatbot.response_generator import ResponseGenerator
from app.repositories.chat_repository import ChatRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.models.chatbot import ConfidenceLevel

logger = logging.getLogger(__name__)


class ChatbotService:

    def __init__(self):
        self.classifier = IntentClassifier()
        self.ctx_mgr = ContextManager()
        self.responder = ResponseGenerator()
        self.chat_repo = ChatRepository()
        self.analytics = AnalyticsRepository()

    # ── Main entry ───────────────────────────────────────

    async def process_message(
        self,
        user_id: str,
        user_type: str,
        message: str,
        session_token: Optional[str] = None,
        student_data: Optional[Dict] = None,
    ) -> Dict[str, Any] | str:
        t0 = time.time()

        try:
            # 1  session
            session = await self.ctx_mgr.get_or_create_session(
                user_id, user_type, session_token
            )

            # 2  store user msg
            await self.ctx_mgr.add_message(session.id, "user", message)

            # 3  resolve refs
            ctx = await self.ctx_mgr.get_context_summary(session.id)
            resolved = await self.ctx_mgr.resolve_references(message, session.id)

            # 4  classify
            intent, conf_score = self.classifier.classify(resolved, ctx)
            logger.info(f"Intent={intent.value}  conf={conf_score:.2f}")

            # 5  out-of-scope → plain text
            if intent == IntentType.OUT_OF_SCOPE:
                await self.ctx_mgr.add_message(
                    session.id, "assistant", "Beyond my scope",
                    intent=intent, confidence=ConfidenceLevel.HIGH,
                )
                ms = int((time.time() - t0) * 1000)
                await self._analytics(intent.value, ms, "High", True, user_id)
                return "Beyond my scope"

            # 6  student data (Task 14)
            if not student_data:
                student_data = await self._load_student(user_id)
            if student_data:
                await self.ctx_mgr.enrich_with_student_data(session.id, student_data)

            # 7  route to handler
            if intent in (IntentType.SYLLABUS_QUERY, IntentType.FACULTY_QUERY):
                response = await self._delegate_persona_a(
                    resolved, intent, student_data
                )
            else:
                response = await self.responder.generate_response(
                    resolved, intent, ctx, student_data
                )

            # 8  string short-circuit
            if isinstance(response, str):
                await self.ctx_mgr.add_message(
                    session.id, "assistant", response, intent=intent
                )
                ms = int((time.time() - t0) * 1000)
                await self._analytics(intent.value, ms, "High", True, user_id)
                return response

            # 9  store structured
            ms = int((time.time() - t0) * 1000)
            conf_str = response.get("confidence", "Medium")
            conf_enum = {"High": ConfidenceLevel.HIGH,
                         "Medium": ConfidenceLevel.MEDIUM,
                         "Low": ConfidenceLevel.LOW}.get(conf_str, ConfidenceLevel.MEDIUM)

            await self.ctx_mgr.add_message(
                session.id, "assistant",
                json.dumps(response.get("content", {})),
                intent=intent,
                response_type=response.get("type"),
                confidence=conf_enum,
                structured_response=response,
                sources=response.get("sources", []),
                processing_time_ms=ms,
            )

            response["session_token"] = session.session_token
            response["processing_time_ms"] = ms

            await self._analytics(intent.value, ms, conf_str, True, user_id)
            return response

        except Exception as e:
            logger.error(f"ChatbotService error: {e}", exc_info=True)
            await self.analytics.record_error()
            return {
                "type": "error", "intent": "ERROR",
                "content": {"message": "An error occurred processing your request."},
                "confidence": "Low",
            }

    # ── Person A delegation ──────────────────────────────

    async def _delegate_persona_a(
        self, query: str, intent: IntentType, stu: Optional[Dict]
    ) -> Dict[str, Any]:
        """Try Person A's DynamicChatbotService, fallback gracefully"""
        try:
            from app.services.chatbot.dynamic_chatbot_service import (
                DynamicChatbotService,
            )
            svc = DynamicChatbotService()
            if intent == IntentType.SYLLABUS_QUERY:
                return await svc.handle_syllabus_query(query)
            elif intent == IntentType.FACULTY_QUERY:
                return await svc.handle_faculty_query(query)
        except Exception as e:
            logger.warning(f"Person A handler unavailable: {e}")

        # Fallback
        topic_map = {
            IntentType.SYLLABUS_QUERY: (
                "I can explain academic concepts. "
                "Try asking: 'Explain deadlock', 'What is normalization?'"
            ),
            IntentType.FACULTY_QUERY: (
                "I can help find faculty mentors. "
                "Try: 'Who teaches DBMS?', 'Recommend a mentor for ML'"
            ),
        }
        return {
            "type": "text",
            "intent": intent.value,
            "content": {"message": topic_map.get(intent, "How can I help?")},
            "confidence": "Medium",
        }

    # ── Student data loader (Task 14) ────────────────────

    async def _load_student(self, uid: str) -> Optional[Dict]:
        try:
            from app.models.student_profile import StudentProfile

            p = await StudentProfile.find_one(StudentProfile.firebase_uid == uid)
            if not p:
                return None

            subjects, weak, strong, trend = [], [], [], []
            for sem in (p.semester_records or []):
                trend.append({
                    "semester": sem.semester,
                    "sgpa": sem.sgpa,
                    "credits": sem.credits_earned,
                })
                for s in (sem.subjects or []):
                    sc = getattr(s, "total", None) or getattr(s, "marks_obtained", 0)
                    subjects.append({
                        "name": s.subject_name, "code": s.subject_code,
                        "score": sc, "grade": getattr(s, "grade", ""),
                    })
                    if sc < 50:
                        weak.append(s.subject_name)
                    elif sc >= 75:
                        strong.append(s.subject_name)

            return {
                "name": p.name, "branch": p.branch,
                "semester": p.current_semester, "cgpa": p.cgpa,
                "latest_sgpa": trend[-1]["sgpa"] if trend else 0,
                "sgpa_trend": trend, "subjects": subjects,
                "weak_subjects": list(set(weak)),
                "strong_subjects": list(set(strong)),
                "interests": getattr(p, "interests", []),
                "skills": [],
            }
        except Exception as e:
            logger.warning(f"Student data load failed: {e}")
            return None

    # ── Conversation history / suggestions ───────────────

    async def get_conversation_history(
        self, user_id: str, token: Optional[str] = None, limit: int = 20
    ) -> List[Dict]:
        if token:
            session = await self.chat_repo.get_session_by_token(token)
        else:
            session = await self.chat_repo.get_active_session(user_id)
        if not session:
            return []
        return [
            {
                "id": m.id, "role": m.role,
                "content": m.structured_response or m.content,
                "timestamp": m.created_at.isoformat(),
                "intent": m.intent.value if m.intent else None,
            }
            for m in session.messages[-limit:]
        ]

    async def clear_session(self, user_id: str, token: str):
        s = await self.chat_repo.get_session_by_token(token)
        if s and s.user_id == user_id:
            await self.ctx_mgr.clear_session(s.id)

    async def get_suggestions(
        self, user_id: str, token: Optional[str] = None
    ) -> List[str]:
        defaults = [
            "How to become a data scientist?",
            "Show my academic performance",
            "Which electives for ML career?",
            "Create a study plan",
            "Career options in cybersecurity?",
        ]
        if not token:
            return defaults
        s = await self.chat_repo.get_session_by_token(token)
        if not s:
            return defaults
        ctx = s.context
        extra = []
        if ctx.current_subject:
            extra.append(f"Career paths related to {ctx.current_subject}?")
        if ctx.last_intent == IntentType.CAREER_QUERY:
            extra.append("Create a study plan to prepare for this career")
        if ctx.last_intent == IntentType.PERFORMANCE_QUERY:
            extra.append("Which electives can help my weak areas?")
        return (extra + defaults)[:5]

    # ── Analytics helper ─────────────────────────────────

    async def _analytics(
        self, intent: str, ms: int, conf: str, ok: bool, uid: str
    ):
        try:
            await self.analytics.record_query(intent, ms, conf, ok, uid)
        except Exception as e:
            logger.warning(f"Analytics write failed: {e}")