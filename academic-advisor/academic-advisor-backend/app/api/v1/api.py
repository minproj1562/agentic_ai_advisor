# app/api/v1/api.py - COMPLETE FILE
from fastapi import APIRouter
from app.api.v1.endpoints import (
    electives,
    student_analysis,
    students,
    weakness,
    analytics,
    publications,
    research_area,
    student_projects_enhanced,
    student_profile,
    ml_insights
)
from app.api.v1 import cv

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    electives.router, 
    prefix="/electives", 
    tags=["electives"]
)

api_router.include_router(
    student_analysis.router, 
    prefix="/student-analysis", 
    tags=["student-analysis"]
)

api_router.include_router(
    students.router,
    prefix="/students",
    tags=["students"]
)

api_router.include_router(
    weakness.router, 
    prefix="/weakness", 
    tags=["weakness-analysis"]
)

api_router.include_router(
    analytics.router, 
    prefix="/analytics", 
    tags=["analytics"]
)

api_router.include_router(
    publications.router, 
    prefix="/publications", 
    tags=["publications"]
)

api_router.include_router(
    research_area.router, 
    prefix="/research", 
    tags=["research"]
)

api_router.include_router(
    cv.router, 
    prefix="/cv", 
    tags=["cv"]
)

api_router.include_router(
    student_profile.router, 
    prefix="/student", 
    tags=["student-profile"]
)

api_router.include_router(
    student_projects_enhanced.router, 
    prefix="/enhanced-projects", 
    tags=["enhanced-projects"]
)

api_router.include_router(
    ml_insights.router, 
    prefix="/ml", 
    tags=["ml-insights"]
)