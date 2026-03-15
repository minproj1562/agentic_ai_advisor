# app/api/v1/api.py
"""
API v1 Router - Aggregates all endpoint routers
FIXED: Uses MongoDB-based student analysis endpoints (same pattern as admin)
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

api_router = APIRouter()

# ==================== CORE ROUTERS ====================

from app.api.v1.auth import router as auth_router
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

from app.api.v1.endpoints.students import router as students_router
api_router.include_router(students_router, prefix="/students", tags=["Students"])

from app.api.v1.faculty import router as faculty_router
api_router.include_router(faculty_router, prefix="/faculty", tags=["Faculty"])

from app.api.v1.recommendations import router as recommendations_router
api_router.include_router(recommendations_router, prefix="/recommendations", tags=["Recommendations"])

from app.api.v1.resources import router as resources_router
api_router.include_router(resources_router, prefix="/resources", tags=["Resources"])

from app.api.v1.messages import router as messages_router
api_router.include_router(messages_router, prefix="/messages", tags=["Messages"])

# ──────────────────────────────────────────────────────────────
# CHANGED: Use the MongoDB/Beanie endpoints.student_analysis
# instead of the Firebase-based app.api.v1.student_analysis
# ──────────────────────────────────────────────────────────────
from app.api.v1.endpoints.student_analysis import router as student_analysis_router
api_router.include_router(student_analysis_router, prefix="/student-analysis", tags=["Student Analysis"])

# ==================== ENDPOINT ROUTERS ====================

from app.api.v1.endpoints.academic import router as academic_router
api_router.include_router(academic_router, prefix="/academic", tags=["Academic Data"])

from app.api.v1.endpoints.electives import router as electives_router
api_router.include_router(electives_router, prefix="/electives", tags=["Elective Recommendations"])

from app.api.v1.endpoints.analytics import router as analytics_router
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])

from app.api.v1.endpoints.achievements import router as achievements_router
api_router.include_router(achievements_router, prefix="/achievements", tags=["Achievements"])

from app.api.v1.endpoints.weakness import router as weakness_router
api_router.include_router(weakness_router, prefix="/weakness", tags=["Weakness Analysis"])

from app.api.v1.endpoints.student_profile import router as student_profile_router
api_router.include_router(student_profile_router, prefix="/student-profile", tags=["Student Profile"])

from app.api.v1.endpoints.student_projects_enhanced import router as student_projects_router
api_router.include_router(student_projects_router, prefix="/student-projects", tags=["Student Projects"])

from app.api.v1.endpoints.notifications import router as notifications_router
api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])

from app.api.v1.endpoints.meeting_requests import router as meeting_requests_router
api_router.include_router(meeting_requests_router, prefix="/meetings", tags=["Meeting Requests"])

from app.api.v1.endpoints import readiness as readiness_endpoints
api_router.include_router(readiness_endpoints.router, prefix="/readiness", tags=["Readiness Analysis"])

from app.api.v1.endpoints.chatbot import router as chatbot_router
api_router.include_router(chatbot_router, prefix="/chatbot", tags=["Chatbot"])

from app.api.v1.admin import router as admin_router
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])

# ==================== OPTIONAL ROUTERS ====================

def _safe_include(module_path: str, attr: str, prefix: str, tags: list):
    try:
        import importlib
        mod = importlib.import_module(module_path)
        router = getattr(mod, attr)
        api_router.include_router(router, prefix=prefix, tags=tags)
        logger.info(f"✅ Router mounted: {prefix}")
    except Exception as e:
        logger.error(f"❌ Failed to mount {prefix}: {type(e).__name__}: {e}", exc_info=True)

_safe_include("app.api.v1.endpoints.ml_insights", "router", "/ml-insights", ["ML Insights"])
_safe_include("app.api.v1.endpoints.faculty_profile", "router", "/faculty-profile", ["Faculty Profile"])
_safe_include("app.api.v1.endpoints.publications", "router", "/publications", ["Publications"])
_safe_include("app.api.v1.endpoints.research_area", "router", "/research-areas", ["Research Areas"])