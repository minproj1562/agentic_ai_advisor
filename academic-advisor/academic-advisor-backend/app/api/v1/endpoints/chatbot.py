# app/api/v1/endpoints/chatbot.py
"""
Chatbot API — chat, history, suggestions, feedback, analytics
Enhanced with proper orchestration and optional authentication
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging
import time

logger = logging.getLogger(__name__)
router = APIRouter()


# ══════════════════════════════════════════════════════════
# SAFE IMPORTS
# ══════════════════════════════════════════════════════════

_SERVICES_AVAILABLE = True
_IMPORT_ERROR = None

try:
    from app.services.chatbot.chatbot_service import ChatbotService
    from app.services.chatbot.intent_classifier import IntentClassifier
except ImportError as e:
    _SERVICES_AVAILABLE = False
    _IMPORT_ERROR = str(e)
    logger.error(f"Failed to import chatbot services: {e}")
    ChatbotService = None
    IntentClassifier = None

try:
    from app.repositories.analytics_repository import AnalyticsRepository
except ImportError:
    AnalyticsRepository = None
    logger.warning("AnalyticsRepository not available")

try:
    from app.repositories.chat_repository import ChatRepository
except ImportError:
    ChatRepository = None
    logger.warning("ChatRepository not available")

try:
    from app.models.chatbot import ChatFeedback
except ImportError:
    ChatFeedback = None
    logger.warning("ChatFeedback model not available")

# Import auth - make it optional
try:
    from app.core.deps import get_current_user, FirebaseUser
    _AUTH_AVAILABLE = True
except ImportError:
    _AUTH_AVAILABLE = False
    FirebaseUser = None
    logger.warning("Authentication not available - running without auth")
    
    async def get_current_user():
        return None


# ══════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ══════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_token: Optional[str] = None
    include_student_data: bool = True
    student_data: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    type: str
    intent: str
    content: Dict[str, Any]
    confidence: str
    session_token: Optional[str] = None
    processing_time_ms: Optional[int] = None
    sources: Optional[List[Dict]] = None


class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None
    was_helpful: Optional[bool] = None


class ClearSessionRequest(BaseModel):
    session_token: str


# ══════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════

def _get_user_id(req: Request, current_user=None) -> str:
    """Extract REAL Firebase UID from the auth token."""
    # 1. From dependency injection
    if current_user and hasattr(current_user, 'uid'):
        return current_user.uid

    # 2. From request state (set by auth middleware)
    if hasattr(req.state, "user") and req.state.user:
        uid = req.state.user.get("uid")
        if uid:
            return uid

    # 3. From X-User-Id header
    user_id = req.headers.get("X-User-Id")
    if user_id:
        return user_id

    # 4. Decode Firebase token directly
    auth_header = req.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            from firebase_admin import auth as fb_auth
            decoded = fb_auth.verify_id_token(token, check_revoked=False)
            uid = decoded.get("uid")
            if uid:
                logger.info(f"✅ Decoded Firebase UID: {uid[:12]}...")
                return uid
        except Exception as e:
            logger.warning(f"Firebase token decode failed: {e}")

    return "anonymous"

def _get_user_type(current_user=None) -> str:
    """Determine user type."""
    if current_user and hasattr(current_user, 'role'):
        return current_user.role
    return "student"


# ══════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════

@router.get("/health")
async def health_check():
    """Check if the chatbot service is healthy."""
    status = {
        "status": "healthy" if _SERVICES_AVAILABLE else "degraded",
        "service": "chatbot",
        "services_available": _SERVICES_AVAILABLE,
        "auth_available": _AUTH_AVAILABLE,
        "timestamp": time.time()
    }
    
    if not _SERVICES_AVAILABLE:
        status["error"] = _IMPORT_ERROR
        return JSONResponse(status_code=503, content=status)
    
    try:
        if ChatbotService:
            ChatbotService()
        if IntentClassifier:
            IntentClassifier()
        return status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "chatbot",
                "error": str(e)
            }
        )


# ══════════════════════════════════════════════════════════
# MAIN CHAT ENDPOINT
# ══════════════════════════════════════════════════════════

@router.post("/chat")
async def chat(body: ChatRequest, req: Request):
    """
    Main chat endpoint - processes user messages and returns bot responses.
    Works with or without authentication.
    """
    start_time = time.time()
    
    if not _SERVICES_AVAILABLE or not ChatbotService:
        return JSONResponse(
            status_code=503,
            content={
                "type": "error",
                "intent": "ERROR",
                "content": {
                    "message": "Chatbot service is temporarily unavailable.",
                    "error": _IMPORT_ERROR
                },
                "confidence": "Low"
            }
        )
    
    try:
        user_id = _get_user_id(req)
        user_type = "student"
        
        logger.info(f"Chat request from user: {user_id}, message: {body.message[:50]}...")
        
        chatbot_service = ChatbotService()
        
        response = await chatbot_service.process_message(
            user_id=user_id,
            user_type=user_type,
            message=body.message.strip(),
            session_token=body.session_token,
            student_data=body.student_data,
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Ensure response is a dict
        if isinstance(response, str):
            response = {
                "type": "text",
                "intent": "GENERAL",
                "content": {"message": response},
                "confidence": "High",
                "processing_time_ms": processing_time
            }
        elif isinstance(response, dict):
            response["processing_time_ms"] = processing_time
        
        logger.info(f"Chat response generated in {processing_time}ms")
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        processing_time = int((time.time() - start_time) * 1000)
        
        return JSONResponse(
            status_code=500,
            content={
                "type": "error",
                "intent": "ERROR",
                "content": {"message": f"An error occurred: {str(e)}"},
                "confidence": "Low",
                "processing_time_ms": processing_time
            }
        )


# ══════════════════════════════════════════════════════════
# SUGGESTIONS ENDPOINT
# ══════════════════════════════════════════════════════════

@router.get("/suggestions")
async def get_suggestions(
    req: Request,
    session_token: Optional[str] = None
):
    """Get contextual suggestions based on conversation history."""
    default_suggestions = [
        "How to become a data scientist?",
        "Explain deadlock in OS",
        "Who teaches Machine Learning?",
        "Show my academic performance",
        "Recommend electives for AI career"
    ]
    
    if not _SERVICES_AVAILABLE or not ChatbotService:
        return {"success": True, "suggestions": default_suggestions}
    
    try:
        user_id = _get_user_id(req)
        chatbot_service = ChatbotService()
        suggestions = await chatbot_service.get_suggestions(user_id, session_token)
        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        logger.error(f"Suggestions error: {e}", exc_info=True)
        return {"success": True, "suggestions": default_suggestions}


# ══════════════════════════════════════════════════════════
# HISTORY ENDPOINT
# ══════════════════════════════════════════════════════════

@router.get("/history")
async def get_history(
    req: Request,
    session_token: Optional[str] = None,
    limit: int = 20
):
    """Get conversation history for the current session."""
    if not _SERVICES_AVAILABLE or not ChatbotService:
        return {"success": False, "messages": [], "error": "Service unavailable"}
    
    try:
        user_id = _get_user_id(req)
        chatbot_service = ChatbotService()
        messages = await chatbot_service.get_conversation_history(user_id, session_token, limit)
        return {
            "success": True,
            "messages": messages,
            "count": len(messages),
            "session_token": session_token
        }
    except Exception as e:
        logger.error(f"History error: {e}", exc_info=True)
        return {"success": False, "messages": [], "error": str(e)}


# ══════════════════════════════════════════════════════════
# CLEAR SESSION ENDPOINT
# ══════════════════════════════════════════════════════════

@router.post("/clear")
async def clear_session(
    req: Request,
    body: Optional[ClearSessionRequest] = None,
    session_token: str = ""
):
    """Clear/end the current conversation session."""
    try:
        token = body.session_token if body else session_token
        if token and _SERVICES_AVAILABLE and ChatbotService:
            user_id = _get_user_id(req)
            chatbot_service = ChatbotService()
            await chatbot_service.clear_session(user_id, token)
        
        return {"success": True, "status": "cleared", "message": "Session cleared successfully"}
    except Exception as e:
        logger.error(f"Clear session error: {e}", exc_info=True)
        return {"success": False, "status": "error", "error": str(e)}


# ══════════════════════════════════════════════════════════
# FEEDBACK ENDPOINT
# ══════════════════════════════════════════════════════════

@router.post("/feedback")
async def submit_feedback(body: FeedbackRequest, req: Request):
    """Submit feedback for a chatbot response."""
    if not ChatRepository or not ChatFeedback:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Feedback service unavailable"}
        )
    
    try:
        user_id = _get_user_id(req)
        chat_repo = ChatRepository()
        
        feedback = ChatFeedback(
            session_id=body.session_id,
            message_id=body.message_id,
            user_id=user_id,
            rating=body.rating,
            feedback_text=body.feedback_text,
            was_helpful=body.was_helpful,
        )
        
        await chat_repo.save_feedback(feedback)
        
        return {"success": True, "status": "success", "message": "Thank you for your feedback!"}
    except Exception as e:
        logger.error(f"Feedback error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save feedback")


# ══════════════════════════════════════════════════════════
# ANALYTICS ENDPOINT
# ══════════════════════════════════════════════════════════

@router.get("/analytics")
async def get_analytics(days: int = 7):
    """Get chatbot usage analytics."""
    if not AnalyticsRepository:
        return {
            "success": False,
            "error": "Analytics service unavailable",
            "period_days": days,
            "total_queries": 0
        }
    
    try:
        analytics_repo = AnalyticsRepository()
        summary = await analytics_repo.get_summary(days)
        return {"success": True, "period_days": days, "analytics": summary}
    except Exception as e:
        logger.error(f"Analytics error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get analytics")


# ══════════════════════════════════════════════════════════
# TEST ENDPOINT (Development only)
# ══════════════════════════════════════════════════════════

@router.get("/test")
async def test_chatbot():
    """Test endpoint to verify chatbot is working."""
    if not _SERVICES_AVAILABLE:
        return {
            "status": "error",
            "message": "Chatbot services not available",
            "error": _IMPORT_ERROR
        }
    
    try:
        # Test classifier
        classifier = IntentClassifier()
        test_queries = [
            ("hello", "GREETING"),
            ("what is deadlock", "SYLLABUS_QUERY"),
            ("who teaches os", "FACULTY_QUERY"),
            ("careers in data science", "CAREER_QUERY"),
        ]
        
        results = []
        for query, expected in test_queries:
            intent, confidence = classifier.classify(query)
            intent_str = intent.value if hasattr(intent, 'value') else str(intent)
            results.append({
                "query": query,
                "expected": expected,
                "got": intent_str,
                "confidence": round(confidence, 2),
                "correct": intent_str == expected
            })
        
        return {
            "status": "ok",
            "message": "Chatbot is working",
            "test_results": results
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }