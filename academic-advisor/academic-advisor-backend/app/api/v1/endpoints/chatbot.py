# academic-advisor/academic-advisor-backend/app/api/v1/endpoints/chatbot.py
"""
Chatbot API — chat, history, suggestions, feedback (Task 22), analytics (Task 20)
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field
import logging

from app.services.chatbot.chatbot_service import ChatbotService
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.chat_repository import ChatRepository
from app.models.chatbot import ChatFeedback

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_token: Optional[str] = None
    include_student_data: bool = True


class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None
    was_helpful: Optional[bool] = None


# ── Helpers ──────────────────────────────────────────────

def _uid(req: Request) -> str:
    if hasattr(req.state, "user") and req.state.user:
        return req.state.user.get("uid", "anonymous")
    return req.headers.get("X-User-Id", "anonymous")


# ── Endpoints ────────────────────────────────────────────

@router.post("/chat")
async def chat(body: ChatRequest, req: Request):
    try:
        svc = ChatbotService()
        resp = await svc.process_message(
            user_id=_uid(req),
            user_type="student",
            message=body.message.strip(),
            session_token=body.session_token,
        )
        if isinstance(resp, str):
            return PlainTextResponse(content=resp)
        return JSONResponse(content=resp)
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={
            "type": "error", "intent": "ERROR",
            "content": {"message": "An error occurred."},
            "confidence": "Low",
        })


@router.get("/suggestions")
async def suggestions(req: Request, session_token: Optional[str] = None):
    svc = ChatbotService()
    return {"suggestions": await svc.get_suggestions(_uid(req), session_token)}


@router.get("/history")
async def history(
    req: Request, session_token: Optional[str] = None, limit: int = 20
):
    svc = ChatbotService()
    msgs = await svc.get_conversation_history(_uid(req), session_token, limit)
    return {"messages": msgs, "session_token": session_token}


@router.post("/clear")
async def clear(req: Request, session_token: str = ""):
    if session_token:
        svc = ChatbotService()
        await svc.clear_session(_uid(req), session_token)
    return {"status": "cleared"}


@router.post("/feedback")
async def feedback(body: FeedbackRequest, req: Request):
    """Task 22 — Feedback API"""
    try:
        repo = ChatRepository()
        fb = ChatFeedback(
            session_id=body.session_id,
            message_id=body.message_id,
            user_id=_uid(req),
            rating=body.rating,
            feedback_text=body.feedback_text,
            was_helpful=body.was_helpful,
        )
        await repo.save_feedback(fb)
        return {"status": "success", "message": "Thank you for your feedback!"}
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(500, "Failed to save feedback")


@router.get("/analytics")
async def analytics(days: int = 7):
    """Task 20 — Analytics endpoint"""
    try:
        return await AnalyticsRepository().get_summary(days)
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(500, "Failed to get analytics")