# academic-advisor-backend/app/api/v1/api.py
"""
API Router aggregation - All v1 endpoints
"""

from fastapi import APIRouter

# Import all endpoint routers
from app.api.v1.endpoints.student_profile import router as student_profile_router
from app.api.v1.endpoints.academic import router as academic_router
from app.api.v1.endpoints.students import router as students_router
from app.api.v1.endpoints.electives import router as electives_router
from app.api.v1.endpoints.weakness import router as weakness_router
from app.api.v1.endpoints.resources import router as resources_router
from app.api.v1.endpoints.meeting_requests import router as meeting_requests_router
from app.api.v1.endpoints.student_projects_enhanced import router as projects_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.student_analysis import router as student_analysis_router  # ADD THIS

# Import auth router
from app.api.v1.auth import router as auth_router

# Optional routers (may not exist)
try:
    from app.api.v1.endpoints.faculty_profile import router as faculty_profile_router
    HAS_FACULTY_PROFILE = True
except ImportError:
    HAS_FACULTY_PROFILE = False

try:
    from app.api.v1.endpoints.ml_insights import router as ml_insights_router
    HAS_ML_INSIGHTS = True
except ImportError:
    HAS_ML_INSIGHTS = False

# Create main API router
api_router = APIRouter()

# Include all routers with proper prefixes and tags
api_router.include_router(
    auth_router, 
    prefix="/auth", 
    tags=["Authentication"]
)

api_router.include_router(
    student_profile_router, 
    prefix="/student-profile", 
    tags=["Student Profile"]
)

api_router.include_router(
    academic_router, 
    prefix="/academic", 
    tags=["Academic Data"]
)

# ADD THIS - Student Analysis Router (for dashboard data)
api_router.include_router(
    student_analysis_router, 
    prefix="/student-analysis", 
    tags=["Student Analysis"]
)

api_router.include_router(
    students_router, 
    prefix="/students", 
    tags=["Students"]
)

api_router.include_router(
    electives_router, 
    prefix="/electives", 
    tags=["Elective Recommendations"]
)

api_router.include_router(
    weakness_router, 
    prefix="/weakness", 
    tags=["Weakness Analysis"]
)

api_router.include_router(
    resources_router, 
    prefix="/resources", 
    tags=["Study Resources"]
)

api_router.include_router(
    meeting_requests_router, 
    prefix="/meetings", 
    tags=["Meeting Requests"]
)

api_router.include_router(
    projects_router, 
    prefix="/projects", 
    tags=["Student Projects"]
)

api_router.include_router(
    notifications_router, 
    prefix="/notifications", 
    tags=["Notifications"]
)

api_router.include_router(
    analytics_router, 
    prefix="/analytics", 
    tags=["Analytics"]
)

# Optional routers
if HAS_FACULTY_PROFILE:
    api_router.include_router(
        faculty_profile_router, 
        prefix="/faculty-profile", 
        tags=["Faculty Profile"]
    )

if HAS_ML_INSIGHTS:
    api_router.include_router(
        ml_insights_router, 
        prefix="/ml-insights", 
        tags=["ML Insights"]
    )