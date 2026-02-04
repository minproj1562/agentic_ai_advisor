"""
API Router - Aggregates all endpoint routers
"""

from fastapi import APIRouter
import logging
import importlib

logger = logging.getLogger(__name__)

api_router = APIRouter()

# ==================== Fixed router loading function ====================

def safe_include_router(module_path: str, prefix: str, tags: list):
    """Safely import and include a router with detailed error logging"""
    try:
        # Import the full module path
        module = importlib.import_module(module_path)
        
        # Always look for 'router' attribute
        router = getattr(module, 'router', None)
        
        if router is None:
            logger.error(f"❌ No 'router' found in {module_path}")
            return False
        
        api_router.include_router(router, prefix=prefix, tags=tags)
        logger.info(f"✅ Loaded: {prefix} from {module_path}")
        return True
        
    except ImportError as e:
        logger.error(f"❌ ImportError for {module_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error loading {module_path}: {type(e).__name__}: {e}")
        return False


# ==================== Load all routers ====================

# Auth
safe_include_router("app.api.v1.auth", "/auth", ["Authentication"])

# Students
safe_include_router("app.api.v1.students", "/students", ["Students"])
safe_include_router("app.api.v1.endpoints.students", "/students", ["Students Endpoints"])
safe_include_router("app.api.v1.student_analysis", "/student-analysis", ["Student Analysis"])
safe_include_router("app.api.v1.endpoints.student_analysis", "/student-analysis", ["Student Analysis Endpoints"])
safe_include_router("app.api.v1.endpoints.student_profile", "/student-profile", ["Student Profile"])
safe_include_router("app.api.v1.endpoints.student_projects_enhanced", "/student-projects", ["Student Projects"])

# Faculty
safe_include_router("app.api.v1.faculty", "/faculty", ["Faculty"])
safe_include_router("app.api.v1.endpoints.faculty_profile", "/faculty-profile", ["Faculty Profile"])

# Meetings
safe_include_router("app.api.v1.endpoints.meeting_requests", "/meetings", ["Meeting Requests"])
safe_include_router("app.api.v1.endpoints.appointments", "/appointments", ["Appointments"])

# Notifications
safe_include_router("app.api.v1.endpoints.notifications", "/notifications", ["Notifications"])

# Messages
safe_include_router("app.api.v1.messages", "/messages", ["Messages"])
safe_include_router("app.api.v1.endpoints.messages", "/messages", ["Messages Endpoints"])

# CV
safe_include_router("app.api.v1.cv", "/cv", ["CV Processing"])

# Recommendations
safe_include_router("app.api.v1.recommendations", "/recommendations", ["Recommendations"])

# Resources
safe_include_router("app.api.v1.resources", "/resources", ["Resources"])
safe_include_router("app.api.v1.endpoints.resources", "/resources", ["Resources Endpoints"])

# Academic
safe_include_router("app.api.v1.endpoints.academic", "/academic", ["Academic"])

# Electives
safe_include_router("app.api.v1.endpoints.electives", "/electives", ["Electives"])

# Weakness
safe_include_router("app.api.v1.endpoints.weakness", "/weakness", ["Weakness Analysis"])

# Analytics
safe_include_router("app.api.v1.endpoints.analytics", "/analytics", ["Analytics"])

# ML Insights
safe_include_router("app.api.v1.endpoints.ml_insights", "/ml-insights", ["ML Insights"])

# Achievements
safe_include_router("app.api.v1.endpoints.achievements", "/achievements", ["Achievements"])

# Research
safe_include_router("app.api.v1.endpoints.research_area", "/research", ["Research"])

# Publications
safe_include_router("app.api.v1.endpoints.publications", "/publications", ["Publications"])

# WebSocket
safe_include_router("app.api.v1.websocket", "/ws", ["WebSocket"])

logger.info("🚀 API router initialization complete")