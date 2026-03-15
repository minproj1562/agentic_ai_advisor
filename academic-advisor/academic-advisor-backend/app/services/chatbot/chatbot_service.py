# app/services/chatbot/chatbot_service.py
"""
Optimized Chatbot Service - FIXED VERSION
With proper error handling and service availability checks
"""
import re       # For quiz detection and topic extraction
import time
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════
# LAZY-LOADED SERVICES
# ══════════════════════════════════════════════════════════

_classifier = None
_ctx_mgr = None
_responder = None
_chat_repo = None
_analytics = None
_llm_service = None
_sentiment_service = None
_cache_service = None
_student_data_service = None


def _get_classifier():
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
    global _chat_repo
    if _chat_repo is None:
        try:
            from app.repositories.chat_repository import ChatRepository
            _chat_repo = ChatRepository()
        except Exception as e:
            logger.warning(f"ChatRepository not available: {e}")
    return _chat_repo


def _get_analytics():
    global _analytics
    if _analytics is None:
        try:
            from app.repositories.analytics_repository import AnalyticsRepository
            _analytics = AnalyticsRepository()
        except Exception:
            pass
    return _analytics


def _get_llm_service():
    global _llm_service
    if _llm_service is None:
        try:
            from app.services.chatbot.llm_service import get_llm_service
            _llm_service = get_llm_service()
            logger.info("✅ LLMService loaded")
        except Exception as e:
            logger.warning(f"LLMService not available: {e}")
    return _llm_service


def _get_sentiment_service():
    global _sentiment_service
    if _sentiment_service is None:
        try:
            from app.services.chatbot.sentiment_service import get_sentiment_service
            _sentiment_service = get_sentiment_service()
            logger.info("✅ SentimentService loaded")
        except Exception as e:
            logger.warning(f"SentimentService not available: {e}")
    return _sentiment_service


def _get_cache_service():
    global _cache_service
    if _cache_service is None:
        try:
            from app.services.chatbot.cache_service import get_cache_service
            _cache_service = get_cache_service()
            logger.info("✅ CacheService loaded")
        except Exception as e:
            logger.warning(f"CacheService not available: {e}")
    return _cache_service


def _get_student_data_service():
    global _student_data_service
    if _student_data_service is None:
        try:
            from app.services.chatbot.student_data_service import get_student_data_service
            _student_data_service = get_student_data_service()
            logger.info("✅ StudentDataService loaded")
        except Exception as e:
            logger.warning(f"StudentDataService not available: {e}")
    return _student_data_service


def _safe_enum_value(enum_or_string) -> str:
    """Safely get value from enum or return string as-is."""
    if enum_or_string is None:
        return ""
    if isinstance(enum_or_string, str):
        return enum_or_string
    if hasattr(enum_or_string, 'value'):
        return enum_or_string.value
    return str(enum_or_string)


# ══════════════════════════════════════════════════════════
# CHATBOT SERVICE
# ══════════════════════════════════════════════════════════

class ChatbotService:
    """
    Main chatbot orchestrator with:
    - Sentiment-aware responses
    - LLM enhancement for complex queries
    - Response caching for speed
    - Human advisor suggestions when needed
    """

    def __init__(self):
        """Lightweight initialization."""
        logger.debug("ChatbotService created (optimized)")

    async def process_message(
        self,
        user_id: str,
        user_type: str,
        message: str,
        session_token: Optional[str] = None,
        student_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Process a user message and return a response.
        """
        start_time = time.time()
        
        try:
            # Get services lazily
            classifier = _get_classifier()
            ctx_mgr = _get_ctx_mgr()
            responder = _get_responder()
            cache_service = _get_cache_service()
            sentiment_service = _get_sentiment_service()
            llm_service = _get_llm_service()
            student_service = _get_student_data_service()
            
            from app.services.chatbot.intent_classifier import IntentType
            
            # ─── Step 1: Analyze Sentiment ───────────────────
            sentiment = None
            sentiment_dict = None
            if sentiment_service:
                try:
                    sentiment = sentiment_service.analyze(message)
                    sentiment_dict = sentiment.to_dict() if sentiment else None
                    logger.debug(f"Sentiment: mood={sentiment.mood}")
                except Exception as e:
                    logger.warning(f"Sentiment analysis failed: {e}")
            
            # ─── Step 2: Get/Create Session ──────────────────
            session = await ctx_mgr.get_or_create_session(user_id, user_type, session_token)
            session_id = str(session.id)
            
            # Store user message
            try:
                await ctx_mgr.add_message(session_id, "user", message)
            except Exception as e:
                logger.warning(f"Failed to store user message: {e}")
            
            # ─── Step 3: Check Cache ─────────────────────────
            cache_context = {"intent": None}
            if student_data:
                cache_context["semester"] = student_data.get("semester")
                cache_context["branch"] = student_data.get("branch")
            
            if cache_service:
                try:
                    cached_response = await cache_service.get_response(message, cache_context)
                    if cached_response:
                        logger.debug("Cache hit!")
                        response = self._adapt_to_sentiment(cached_response, sentiment)
                        response["from_cache"] = True
                        response["session_token"] = session.session_token
                        response["processing_time_ms"] = int((time.time() - start_time) * 1000)
                        if sentiment_dict:
                            response["sentiment"] = {"mood": sentiment_dict.get("mood", "neutral")}
                        return response
                except Exception as e:
                    logger.warning(f"Cache lookup failed: {e}")
            
            # ─── Step 4: Get Context & Classify Intent ───────
            context = {}
            try:
                context = await ctx_mgr.get_context_summary(session_id)
            except Exception as e:
                logger.warning(f"Failed to get context: {e}")
            
            resolved_query = message
            try:
                resolved_query = await ctx_mgr.resolve_references(message, session_id)
            except Exception as e:
                logger.warning(f"Reference resolution failed: {e}")

            # ─── Step 4b: Follow-up / Detail Detection (NEW) ──
            is_detailed_request = False
            context_topic = None
            context_subject = None
            try:
                resolved_query, is_detailed_request, context_topic, context_subject = \
                    await ctx_mgr.resolve_follow_up(resolved_query, session_id)
                if context_topic:
                    logger.info(f"Follow-up detected: topic={context_topic}, detailed={is_detailed_request}")
            except Exception as e:
                logger.warning(f"Follow-up resolution failed: {e}")
            
            intent, confidence_score = classifier.classify(resolved_query, context)
            logger.info(f"Intent: {_safe_enum_value(intent)}, Confidence: {confidence_score:.2f}")
            
            # ─── Step 5a: Handle Mentor Query ────────────
            try:
                from app.services.chatbot.intent_classifier import IntentType as IT
                if intent == IT.MENTOR_QUERY or _safe_enum_value(intent) == "MENTOR_QUERY":
                    # Let it flow through to response generator
                    pass
            except:
                pass
            # ─── Step 5: Handle Greeting ─────────────────────
            if intent == IntentType.GREETING:
                # Use response generator for all greeting/conversational handling
                # This ensures "thank you", "gn", "who are you" all get proper responses
                response = await responder.generate_response(
                    resolved_query, intent, context, student_data
                )
                if isinstance(response, str):
                    response = {
                        "type": "text", "intent": "GREETING",
                        "content": {"message": response},
                        "confidence": "High"
                    }
                # NEVER send greetings to LLM
                response["session_token"] = session.session_token
                response["processing_time_ms"] = int((time.time() - start_time) * 1000)
                if sentiment_dict:
                    response["sentiment"] = {"mood": sentiment_dict.get("mood", "neutral")}
                
                try:
                    await self._store_response(session_id, response, intent, ctx_mgr, start_time)
                except: pass
                return response
            
            # ─── Step 6: Handle Out-of-Scope ─────────────────
            if intent == IntentType.OUT_OF_SCOPE:
                response = await responder.generate_response(
                    resolved_query, intent, context, student_data
                )
                if isinstance(response, str):
                    response = {
                        "type": "text", "intent": "OUT_OF_SCOPE",
                        "content": {"message": response},
                        "confidence": "High"
                    }
                # Add advisor suggestion for existential queries
                ql = message.lower()
                if any(w in ql for w in ["kill", "suicide", "self harm", "end it",
                                          "why do i live", "meaning of life"]):
                    response["advisor_suggestion"] = {
                        "message": "💙 If you're going through a tough time, please reach out to your college counselor or call iCall helpline: 9152987821",
                        "action": "Contact college counselor",
                        "reason": "wellbeing"
                    }
                
                response["session_token"] = session.session_token
                response["processing_time_ms"] = int((time.time() - start_time) * 1000)
                try:
                    await self._store_response(session_id, response, intent, ctx_mgr, start_time)
                except: pass
                return response
            
            # ─── Step 7: Load Student Data ───────────────────
            # Always try DB lookup, merge with frontend-provided data
            db_student_data = None
            if student_service:
                try:
                    db_student_data = await student_service.get_student_data(user_id)
                except Exception as e:
                    logger.warning(f"Failed to load student data: {e}")
            
            if db_student_data:
                # DB data found — merge with any frontend context
                if student_data:
                    for key, val in student_data.items():
                        if key.startswith("_"):
                            continue
                        if key not in db_student_data or db_student_data[key] is None:
                            db_student_data[key] = val
                student_data = db_student_data
            elif not student_data:
                # No data from frontend either — try to get name from Firebase
                student_data = {}
                try:
                    from firebase_admin import auth as fb_auth
                    fb_user = fb_auth.get_user(user_id)
                    if fb_user:
                        student_data["name"] = fb_user.display_name or ""
                        student_data["email"] = fb_user.email or ""
                except:
                    pass
            
            if student_data:
                try:
                    await ctx_mgr.enrich_with_student_data(session_id, student_data)
                    cache_context["semester"] = student_data.get("semester")
                    cache_context["branch"] = student_data.get("branch")
                except Exception as e:
                    logger.warning(f"Failed to enrich context: {e}")
            
            # ─── Step 8: Generate Base Response ──────────────
            response = await responder.generate_response(
                resolved_query, intent, context, student_data
            )
            
            # Handle string responses
            if isinstance(response, str):
                response = {
                    "type": "text",
                    "intent": _safe_enum_value(intent),
                    "content": {"message": response},
                    "confidence": "High" if confidence_score > 0.7 else "Medium",
                }
            
            # Ensure response is a dict
            if not isinstance(response, dict):
                response = {
                    "type": "text",
                    "intent": _safe_enum_value(intent),
                    "content": {"message": str(response)},
                    "confidence": "Medium",
                }

            # ─── Step 8b: Quiz Detection ─────────────────────
            ql_check = message.lower().strip()
            is_quiz = bool(re.search(r'\b(quiz|test\s*me|mcq)\b', ql_check))
            
            if is_quiz:
                quiz_topic = re.sub(
                    r'\b(quiz|test|me|on|about|for|in|mcq|questions?)\b',
                    '', ql_check
                ).strip().rstrip("?!. ")
                
                # Fallback to context
                if not quiz_topic and context:
                    quiz_topic = (
                        context.get("current_topic") or 
                        context.get("current_subject") or ""
                    )
                
                if quiz_topic:
                    try:
                        quiz_response = await responder.generate_quiz(topic=quiz_topic)
                        if quiz_response.get("type") == "quiz":
                            response = quiz_response
                    except Exception as e:
                        logger.warning(f"Quiz generation failed: {e}")
            
            # ─── Step 9: LLM Enhancement ─────────────────
            base_confidence = response.get("confidence", "Medium")
            base_type = response.get("type", "text")
            intent_str_llm = _safe_enum_value(intent)
            handler_errored = response.get("_handler_error", False)

            # Types that should NEVER be overridden by LLM
            DB_TYPES = {
                "semester_subjects", "faculty_list", "faculty_recommendation",
                "mentor_recommendation", "performance_analysis", "syllabus_breakdown",
                "quiz", "resource_list", "elective_recommendation", "study_plan",
                "career_guidance", "career_list", "concept_explanation",
            }
            RULE_INTENTS = {"GREETING", "OUT_OF_SCOPE"}

            should_use_llm = (
                llm_service
                and hasattr(llm_service, 'is_available')
                and llm_service.is_available
                and base_type not in DB_TYPES
                and intent_str_llm not in RULE_INTENTS
                and (
                    base_confidence == "Low"       # Low confidence from handler
                    or handler_errored             # Handler threw an error
                    or base_type == "error"         # Explicit error type
                )
            )

            if should_use_llm:
                try:
                    ctx_type = {
                        "SYLLABUS_QUERY": "syllabus",
                        "CAREER_QUERY": "career",
                        "PERFORMANCE_QUERY": "performance",
                    }.get(intent_str_llm, "default")

                    if sentiment and (sentiment.is_frustrated or sentiment.is_confused):
                        ctx_type = "frustrated_user"

                    llm_query = resolved_query
                    topic_hint = response.get("content", {}).get("_topic_hint")
                    if topic_hint and intent_str_llm == "SYLLABUS_QUERY":
                        llm_query = f"Explain the concept of {topic_hint} for an engineering student"

                    # ── Detailed flashcard path (NEW) ────────
                    used_detailed = False
                    detail_topic = context_topic or topic_hint
                    detail_subject = context_subject or ""

                    if not detail_subject:
                        try:
                            from app.services.chatbot.response_generator import _extract_subject
                            detail_subject = _extract_subject(resolved_query) or ""
                        except Exception:
                            pass

                    if (
                        intent_str_llm == "SYLLABUS_QUERY"
                        and is_detailed_request
                        and detail_topic
                        and llm_service
                        and hasattr(llm_service, 'generate_detailed_explanation')
                    ):
                        existing_pts = response.get("content", {}).get("key_points", [])
                        conv_history = []
                        try:
                            conv_history = await ctx_mgr.get_conversation_history(session_id, limit=6)
                            conv_history = [
                                {"role": getattr(m, 'role', 'user'), "content": getattr(m, 'content', '')}
                                for m in conv_history
                            ]
                        except Exception:
                            pass

                        detailed = await llm_service.generate_detailed_explanation(
                            topic=detail_topic,
                            subject=detail_subject,
                            existing_points=existing_pts if existing_pts else None,
                            conversation_history=conv_history if conv_history else None,
                        )

                        if detailed and detailed.get("cards"):
                            # Get curated resources
                            inline_resources = []
                            try:
                                from app.services.chatbot.response_generator import ResponseGenerator as _RG
                                _rg_inst = _RG()
                                inline_resources = _rg_inst._get_curated_resources(
                                    detail_subject or detail_topic
                                )[:3]
                            except Exception:
                                pass

                            response = {
                                "type": "concept_explanation",
                                "intent": intent_str_llm,
                                "content": {
                                    "topic": detail_topic,
                                    "subject": detail_subject,
                                    "cards": detailed["cards"],
                                    "resources": inline_resources,
                                    "suggestions": [
                                        f"Quiz me on {detail_topic}",
                                        f"Resources for {detail_subject or detail_topic}",
                                        f"Who teaches {detail_subject or detail_topic}?",
                                    ],
                                },
                                "confidence": "High",
                                "llm_generated": True,
                            }
                            used_detailed = True

                    # ── Standard LLM fallback ────────────────
                    if not used_detailed:
                        llm_text = await llm_service.generate_response(
                            llm_query,
                            context_type=ctx_type,
                            student_context=student_data,
                            sentiment=sentiment_dict,
                        )

                        if llm_text:
                            if intent_str_llm == "SYLLABUS_QUERY":
                                topic_name = topic_hint or detail_topic or resolved_query.strip("?!. ").title()
                                for prefix in [
                                    "Explain ", "Define ", "What Is ", "What Are ",
                                    "Tell Me About ", "Help Me Understand ",
                                    "Describe ", "Teach Me ", "Teach ",
                                    "Let Me Explain ", "Meaning Of ",
                                    "What Does ", "How Does ",
                                ]:
                                    if topic_name.startswith(prefix):
                                        topic_name = topic_name[len(prefix):]
                                        break
                                topic_name = topic_name.strip("?!. ").rstrip(" Mean")

                                subject_name = detail_subject
                                if not subject_name:
                                    try:
                                        from app.services.chatbot.response_generator import _extract_subject
                                        subject_name = _extract_subject(resolved_query) or ""
                                    except Exception:
                                        subject_name = ""

                                response = {
                                    "type": "concept_explanation",
                                    "intent": intent_str_llm,
                                    "content": {
                                        "topic": topic_name,
                                        "subject": subject_name,
                                        "definition": llm_text,
                                        "key_points": [],
                                        "examples": [],
                                        "suggestions": [
                                            f"Quiz me on {topic_name}",
                                            f"Resources for {subject_name or topic_name}",
                                            f"Who teaches {subject_name or topic_name}?",
                                        ],
                                    },
                                    "confidence": "Medium",
                                    "llm_generated": True,
                                }
                            else:
                                response = {
                                    "type": "text",
                                    "intent": intent_str_llm,
                                    "content": {
                                        "message": llm_text,
                                        "suggestions": response.get("content", {}).get("suggestions", []),
                                    },
                                    "confidence": "Medium",
                                    "llm_generated": True,
                                }
                except Exception as e:
                    logger.warning(f"LLM enhancement failed: {e}")
                    if handler_errored or base_type == "error":
                        response = {
                            "type": "text",
                            "intent": intent_str_llm,
                            "content": {
                                "message": "I couldn't find specific information on that right now. "
                                           "Here are some things I can help with:",
                                "suggestions": [
                                    "Syllabus for sem 3", "Who teaches ML?",
                                    "Explain deadlock", "Career in data science",
                                    "Show my performance",
                                ],
                            },
                            "confidence": "Medium",
                        }

            # Step 9b: Enhance structured responses with AI insights
            if (
                llm_service and llm_service.is_available
                and base_type in ("performance_analysis", "career_guidance", "study_plan")
                and not response.get("llm_generated")
            ):
                try:
                    response = await llm_service.enhance_response(response, resolved_query, student_data)
                except Exception as e:
                    logger.warning(f"LLM enhance failed: {e}")

            # ─── Step 9c: Save topic/subject to context (NEW) ──
            try:
                resp_content = response.get("content", {})
                save_topic = (
                    resp_content.get("topic")
                    or context_topic
                    or resp_content.get("_topic_hint")
                )
                save_subject = (
                    resp_content.get("subject")
                    or context_subject
                    or resp_content.get("name")
                )
                if save_topic or save_subject:
                    await ctx_mgr.update_topic_context(
                        session_id,
                        topic=save_topic,
                        subject=save_subject,
                    )
            except Exception as e:
                logger.warning(f"Failed to save topic context: {e}")
            
            
            # ─── Step 10: Adapt to Sentiment ─────────────────
            response = self._adapt_to_sentiment(response, sentiment)
            
            # ─── Step 11: Add Advisor Suggestion ─────────────
            if sentiment and sentiment.suggest_human_advisor:
                response = self._add_advisor_suggestion(response, sentiment)
            elif confidence_score < 0.4:
                response = self._add_advisor_suggestion(response, sentiment, reason="low_confidence")
            
            # ─── Step 12: Cache & Store ──────────────────────
            processing_time = int((time.time() - start_time) * 1000)
            
            # Cache response (if cacheable)
            if cache_service and response.get("confidence") != "Low":
                try:
                    cache_context["intent"] = _safe_enum_value(intent)
                    await cache_service.set_response(message, response, cache_context)
                except Exception as e:
                    logger.warning(f"Cache storage failed: {e}")
            
            # Store in session
            try:
                await self._store_response(session_id, response, intent, ctx_mgr, start_time)
            except Exception as e:
                logger.warning(f"Failed to store response: {e}")
            
            # Add metadata
            response["session_token"] = session.session_token
            response["processing_time_ms"] = processing_time
            
            if sentiment_dict:
                response["sentiment"] = {
                    "mood": sentiment_dict.get("mood", "neutral"),
                    "confidence": sentiment_dict.get("confidence", 0.5),
                }
            
            # Record analytics
            try:
                await self._record_analytics(
                    _safe_enum_value(intent),
                    processing_time,
                    response.get("confidence", "Medium"),
                    True,
                    user_id
                )
            except Exception as e:
                logger.warning(f"Analytics recording failed: {e}")
            
            return response
            
        except Exception as e:
            logger.error(f"ChatbotService error: {e}", exc_info=True)
            processing_time = int((time.time() - start_time) * 1000)
            
            return {
                "type": "error",
                "intent": "ERROR",
                "content": {
                    "message": "I encountered an issue processing your request. Please try again or contact support if the problem persists.",
                },
                "confidence": "Low",
                "processing_time_ms": processing_time,
                "advisor_suggestion": {
                    "message": "💡 If you continue experiencing issues, please speak with your faculty advisor.",
                    "action": "Contact your department office",
                    "reason": "error"
                }
            }

    def _create_greeting_response(self, student_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Create greeting response."""
        name = ""
        if student_data and student_data.get("name"):
            name = f" {student_data['name']}"
        
        return {
            "type": "text",
            "intent": "GREETING",
            "content": {
                "message": f"Hello{name}! 👋 I'm your Academic Advisor Assistant.\n\n"
                          "I can help you with:\n\n"
                          "📚 **Syllabus & Concepts** - Explain topics like OS, DBMS, ML\n"
                          "👨‍🏫 **Faculty Info** - Who teaches what\n"
                          "📊 **Performance** - Analyze your grades\n"
                          "💼 **Career Guidance** - Roadmaps for tech careers\n"
                          "📖 **Electives** - Course recommendations\n"
                          "📅 **Study Plans** - Exam preparation\n\n"
                          "What would you like to know?",
                "suggestions": [
                    "Explain deadlock in OS",
                    "Who teaches ML?",
                    "Career in AI/ML",
                    "Show my performance",
                ]
            },
            "confidence": "High"
        }

    def _create_out_of_scope_response(self, sentiment) -> Dict[str, Any]:
        """Create response for out-of-scope queries."""
        message = "I'm an academic advisor and can only help with academic-related queries. 📚"
        
        if sentiment and sentiment.is_frustrated:
            message = "I understand you might want help with other topics, but I'm specifically designed for academic guidance. Let me help you with something academic instead! 📚"
        
        return {
            "type": "text",
            "intent": "OUT_OF_SCOPE",
            "content": {
                "message": message,
                "scope": [
                    "📚 Syllabus and course content",
                    "👨‍🏫 Faculty information",
                    "📊 Academic performance analysis",
                    "💼 Career guidance in tech",
                    "📖 Elective recommendations",
                    "📅 Study planning"
                ],
                "suggestions": [
                    "Explain deadlock in OS",
                    "Career path for data science",
                    "Show my performance analysis"
                ],
                "hint": "Please ask me something related to your academics!"
            },
            "confidence": "High"
        }

    def _adapt_to_sentiment(
        self,
        response: Dict[str, Any],
        sentiment
    ) -> Dict[str, Any]:
        """Adapt response based on user sentiment."""
        if not sentiment or not isinstance(response, dict):
            return response
        
        content = response.get("content", {})
        if not isinstance(content, dict):
            return response
        
        # Add empathetic intro if needed
        if sentiment.is_frustrated or sentiment.is_confused or sentiment.is_anxious:
            try:
                sentiment_service = _get_sentiment_service()
                if sentiment_service:
                    intro = sentiment_service.get_adaptive_intro(sentiment)
                    
                    if intro and "message" in content:
                        if not content["message"].startswith(intro):
                            content["message"] = intro + content["message"]
            except Exception as e:
                logger.warning(f"Sentiment adaptation failed: {e}")
        
        # Add encouragement for positive interactions
        if sentiment.is_positive and "message" in content:
            if not any(word in content["message"].lower() for word in ["glad", "happy", "great", "😊"]):
                content["message"] = content["message"].rstrip() + " 😊"
        
        response["content"] = content
        response["sentiment_adapted"] = True
        
        return response

    def _add_advisor_suggestion(
        self,
        response: Dict[str, Any],
        sentiment,
        reason: str = "sentiment"
    ) -> Dict[str, Any]:
        """Add suggestion to consult human advisor."""
        suggestion = {
            "message": "💡 For more personalized guidance, consider speaking with your faculty advisor.",
            "action": "Schedule a meeting with your academic advisor",
            "reason": reason,
        }
        
        if sentiment and sentiment.is_anxious:
            suggestion["message"] = "💡 If you're feeling stressed about academics, your faculty advisor or college counselor can provide personalized support."
        
        response["advisor_suggestion"] = suggestion
        return response

    def _get_llm_context_type(self, intent, sentiment) -> str:
        """Determine LLM context type based on intent and sentiment."""
        from app.services.chatbot.intent_classifier import IntentType
        
        if sentiment and sentiment.is_frustrated:
            return "frustrated_user"
        
        intent_str = _safe_enum_value(intent)
        
        intent_to_context = {
            "SYLLABUS_QUERY": "syllabus",
            "CAREER_QUERY": "career",
            "PERFORMANCE_QUERY": "performance",
        }
        
        return intent_to_context.get(intent_str, "default")

    async def _store_response(
        self,
        session_id: str,
        response: Dict,
        intent,
        ctx_mgr,
        start_time: float
    ):
        """Store response in session."""
        try:
            from app.models.chatbot import ConfidenceLevel, ResponseType
            
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
            except (ValueError, KeyError):
                response_type = ResponseType.TEXT
            
            await ctx_mgr.add_message(
                session_id,
                "assistant",
                json.dumps(response.get("content", {})),
                intent=intent,
                response_type=response_type,
                confidence=confidence_enum,
                structured_response=response,
                sources=response.get("sources", []),
                processing_time_ms=processing_time,
            )
        except Exception as e:
            logger.warning(f"Failed to store response: {e}")

    async def get_conversation_history(
        self,
        user_id: str,
        token: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Get conversation history."""
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
                    "id": getattr(msg, 'id', str(i)),
                    "role": msg.role,
                    "content": msg.structured_response or {"message": msg.content},
                    "timestamp": msg.created_at.isoformat() if hasattr(msg, 'created_at') else None,
                    "intent": _safe_enum_value(msg.intent) if hasattr(msg, 'intent') else None,
                    "type": _safe_enum_value(msg.response_type) if hasattr(msg, 'response_type') else None,
                }
                for i, msg in enumerate(messages)
            ]
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []

    async def clear_session(self, user_id: str, token: str):
        """Clear session."""
        try:
            chat_repo = _get_chat_repo()
            ctx_mgr = _get_ctx_mgr()
            
            if chat_repo and token:
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
        """Get contextual suggestions."""
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

            last_intent = _safe_enum_value(ctx.last_intent)
            
            if last_intent == "CAREER_QUERY":
                suggestions.append("Create a study plan for this career")
                suggestions.append("What electives help for this career?")

            if last_intent == "PERFORMANCE_QUERY":
                suggestions.append("How can I improve my weak subjects?")

            # Fill with defaults
            suggestions.extend(default_suggestions)
            # Remove duplicates while preserving order
            seen = set()
            unique = []
            for s in suggestions:
                if s not in seen:
                    seen.add(s)
                    unique.append(s)
            return unique[:5]

        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return default_suggestions

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