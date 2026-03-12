# app/services/chatbot/chatbot_service.py
"""
Main Chatbot Orchestrator - With Lazy Loading
Fast initialization, components loaded on first use
"""

import time
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════
# LAZY-LOADED COMPONENTS
# ══════════════════════════════════════════════════════════

_classifier = None
_ctx_mgr = None
_responder = None
_chat_repo = None
_analytics = None


def _get_classifier():
    """Lazy load the intent classifier."""
    global _classifier
    if _classifier is None:
        try:
            from app.services.chatbot.intent_classifier import IntentClassifier
            _classifier = IntentClassifier()
            logger.info("✅ IntentClassifier loaded")
        except Exception as e:
            logger.error(f"Failed to load IntentClassifier: {e}")
            raise
    return _classifier


def _get_ctx_mgr():
    """Lazy load the context manager."""
    global _ctx_mgr
    if _ctx_mgr is None:
        try:
            from app.services.chatbot.context_manager import ContextManager
            _ctx_mgr = ContextManager()
            logger.info("✅ ContextManager loaded")
        except Exception as e:
            logger.error(f"Failed to load ContextManager: {e}")
            raise
    return _ctx_mgr


def _get_responder():
    """Lazy load the response generator."""
    global _responder
    if _responder is None:
        try:
            from app.services.chatbot.response_generator import ResponseGenerator
            _responder = ResponseGenerator()
            logger.info("✅ ResponseGenerator loaded")
        except Exception as e:
            logger.error(f"Failed to load ResponseGenerator: {e}")
            raise
    return _responder


def _get_chat_repo():
    """Lazy load the chat repository."""
    global _chat_repo
    if _chat_repo is None:
        try:
            from app.repositories.chat_repository import ChatRepository
            _chat_repo = ChatRepository()
        except Exception as e:
            logger.warning(f"ChatRepository not available: {e}")
    return _chat_repo


def _get_analytics():
    """Lazy load the analytics repository."""
    global _analytics
    if _analytics is None:
        try:
            from app.repositories.analytics_repository import AnalyticsRepository
            _analytics = AnalyticsRepository()
        except Exception as e:
            logger.warning(f"AnalyticsRepository not available: {e}")
    return _analytics


# ══════════════════════════════════════════════════════════
# CHATBOT SERVICE
# ══════════════════════════════════════════════════════════

class ChatbotService:
    """Main chatbot service with lazy loading for fast startup."""

    def __init__(self):
        """Lightweight initialization - no heavy components loaded here."""
        logger.debug("ChatbotService created (lightweight)")

    async def process_message(
        self,
        user_id: str,
        user_type: str,
        message: str,
        session_token: Optional[str] = None,
        student_data: Optional[Dict] = None,
    ) -> Dict[str, Any] | str:
        """
        Process a user message and return a response.
        Components are loaded lazily on first use.
        """
        start_time = time.time()

        try:
            # Get components lazily
            classifier = _get_classifier()
            ctx_mgr = _get_ctx_mgr()
            responder = _get_responder()

            from app.services.chatbot.intent_classifier import IntentType
            from app.models.chatbot import ConfidenceLevel, ResponseType

            # 1. Get or create session
            session = await ctx_mgr.get_or_create_session(user_id, user_type, session_token)
            session_id = str(session.id)

            # 2. Store user message
            await ctx_mgr.add_message(session_id, "user", message)

            # 3. Get context and resolve references
            context = await ctx_mgr.get_context_summary(session_id)
            resolved_query = await ctx_mgr.resolve_references(message, session_id)

            # 4. Classify intent
            intent, confidence_score = classifier.classify(resolved_query, context)
            logger.info(f"Intent: {intent.value}, Confidence: {confidence_score:.2f}")

            # 5. Handle out-of-scope immediately
            if intent == IntentType.OUT_OF_SCOPE:
                await ctx_mgr.add_message(
                    session_id, "assistant", "Beyond my scope",
                    intent=intent, confidence=ConfidenceLevel.HIGH
                )
                processing_time = int((time.time() - start_time) * 1000)
                await self._record_analytics(intent.value, processing_time, "High", True, user_id)
                return "Beyond my scope"

            # 6. Load student data if not provided
            if not student_data:
                student_data = await self._load_student_data(user_id)
            if student_data:
                await ctx_mgr.enrich_with_student_data(session_id, student_data)

            # 7. Generate response
            response = await responder.generate_response(
                resolved_query, intent, context, student_data
            )

            # 8. Handle string response
            if isinstance(response, str):
                await ctx_mgr.add_message(session_id, "assistant", response, intent=intent)
                processing_time = int((time.time() - start_time) * 1000)
                await self._record_analytics(intent.value, processing_time, "High", True, user_id)
                return response

            # 9. Store structured response
            processing_time = int((time.time() - start_time) * 1000)
            confidence_str = response.get("confidence", "Medium")
            confidence_enum = {
                "High": ConfidenceLevel.HIGH,
                "Medium": ConfidenceLevel.MEDIUM,
                "Low": ConfidenceLevel.LOW
            }.get(confidence_str, ConfidenceLevel.MEDIUM)

            response_type_str = response.get("type", "text")
            try:
                response_type = ResponseType(response_type_str)
            except ValueError:
                response_type = None

            await ctx_mgr.add_message(
                session_id, "assistant",
                json.dumps(response.get("content", {})),
                intent=intent,
                response_type=response_type,
                confidence=confidence_enum,
                structured_response=response,
                sources=response.get("sources", []),
                processing_time_ms=processing_time,
            )

            # 10. Add metadata to response
            response["session_token"] = session.session_token
            response["processing_time_ms"] = processing_time

            # 11. Record analytics
            await self._record_analytics(
                intent.value, processing_time, confidence_str, True, user_id
            )

            return response

        except Exception as e:
            logger.error(f"ChatbotService error: {e}", exc_info=True)
            processing_time = int((time.time() - start_time) * 1000)
            
            # Try to record error
            try:
                analytics = _get_analytics()
                if analytics:
                    await analytics.record_error()
            except:
                pass
            
            return {
                "type": "error",
                "intent": "ERROR",
                "content": {"message": f"An error occurred: {str(e)}"},
                "confidence": "Low",
                "processing_time_ms": processing_time
            }

    async def get_conversation_history(
        self,
        user_id: str,
        token: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Get conversation history for a user."""
        try:
            chat_repo = _get_chat_repo()
            if not chat_repo:
                return []

            if token:
                session = await chat_repo.get_session_by_token(token)
            else:
                session = await chat_repo.get_active_session(user_id)

            if not session:
                return []

            messages = session.get_recent_messages(limit)
            return [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.structured_response or {"message": msg.content},
                    "timestamp": msg.created_at.isoformat(),
                    "intent": msg.intent.value if msg.intent else None,
                    "type": msg.response_type.value if msg.response_type else None,
                }
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []

    async def clear_session(self, user_id: str, token: str):
        """Clear/deactivate a session."""
        try:
            chat_repo = _get_chat_repo()
            ctx_mgr = _get_ctx_mgr()
            
            if chat_repo:
                session = await chat_repo.get_session_by_token(token)
                if session and session.user_id == user_id:
                    await ctx_mgr.clear_session(str(session.id))
        except Exception as e:
            logger.error(f"Error clearing session: {e}")

    async def get_suggestions(
        self,
        user_id: str,
        token: Optional[str] = None
    ) -> List[str]:
        """Get contextual suggestions based on conversation history."""
        default_suggestions = [
            "Explain deadlock in OS",
            "Who teaches Machine Learning?",
            "How to become a data scientist?",
            "Show my academic performance",
            "Recommend electives for AI career",
        ]

        try:
            if not token:
                return default_suggestions

            chat_repo = _get_chat_repo()
            if not chat_repo:
                return default_suggestions

            session = await chat_repo.get_session_by_token(token)
            if not session:
                return default_suggestions

            ctx = session.context
            suggestions = []

            from app.services.chatbot.intent_classifier import IntentType

            # Context-based suggestions
            if ctx.current_subject:
                suggestions.append(f"What are the topics in {ctx.current_subject}?")
                suggestions.append(f"Who teaches {ctx.current_subject}?")

            if ctx.current_topic:
                suggestions.append(f"Explain {ctx.current_topic} in detail")
                suggestions.append(f"Examples of {ctx.current_topic}")

            if ctx.last_intent == IntentType.CAREER_QUERY:
                suggestions.append("Create a study plan for this career")
                suggestions.append("What electives help for this career?")

            if ctx.last_intent == IntentType.PERFORMANCE_QUERY:
                suggestions.append("How can I improve my weak subjects?")
                suggestions.append("Which electives suit my strengths?")

            if ctx.last_intent == IntentType.FACULTY_QUERY:
                suggestions.append("What are their office hours?")
                suggestions.append("Request a meeting")

            # Fill with defaults
            suggestions.extend(default_suggestions)
            return suggestions[:5]

        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return default_suggestions

    async def _load_student_data(self, user_id: str) -> Optional[Dict]:
        """Load student performance data from the database."""
        try:
            from app.models.student_profile import StudentProfile

            profile = await StudentProfile.find_one(
                StudentProfile.firebase_uid == user_id
            )
            if not profile:
                profile = await StudentProfile.find_one(
                    StudentProfile.user_id == user_id
                )

            if not profile:
                return None

            # Build student data dict
            subjects = []
            weak_subjects = []
            strong_subjects = []
            sgpa_trend = []

            for sem in (profile.semester_records or []):
                sgpa_trend.append({
                    "semester": sem.semester_number,
                    "sgpa": sem.sgpa,
                    "credits": sem.credits_earned,
                })
                for subj in (sem.subjects or []):
                    score = getattr(subj, 'total_marks', 0) or getattr(subj, 'marks_obtained', 0)
                    subjects.append({
                        "name": subj.subject_name,
                        "code": subj.subject_code,
                        "score": score,
                        "grade": getattr(subj, 'grade', ''),
                    })
                    if score < 50:
                        weak_subjects.append(subj.subject_name)
                    elif score >= 75:
                        strong_subjects.append(subj.subject_name)

            return {
                "name": profile.name,
                "branch": profile.branch,
                "semester": profile.current_semester,
                "cgpa": profile.cgpa,
                "latest_sgpa": sgpa_trend[-1]["sgpa"] if sgpa_trend else 0,
                "sgpa_trend": sgpa_trend,
                "subjects": subjects,
                "weak_subjects": list(set(weak_subjects)),
                "strong_subjects": list(set(strong_subjects)),
                "interests": getattr(profile, 'interests', []),
                "career_goals": getattr(profile, 'career_goals', []),
                "skills": getattr(profile, 'skills', []),
            }
        except Exception as e:
            logger.warning(f"Failed to load student data: {e}")
            return None

    async def _record_analytics(
        self,
        intent: str,
        processing_time_ms: int,
        confidence: str,
        success: bool,
        user_id: str
    ):
        """Record query analytics."""
        try:
            analytics = _get_analytics()
            if analytics:
                await analytics.record_query(
                    intent, processing_time_ms, confidence, success, user_id
                )
        except Exception as e:
            logger.warning(f"Failed to record analytics: {e}")