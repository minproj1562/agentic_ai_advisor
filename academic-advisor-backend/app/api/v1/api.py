# app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import (
    students,
    electives,
    weaknesses,
    resources,
    messages,
    appointments,
    analytics,
    achievements,
    publications,
    research_area,
    cv
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(electives.router, prefix="/electives", tags=["electives"])
api_router.include_router(weaknesses.router, prefix="/weaknesses", tags=["weaknesses"])
api_router.include_router(resources.router, prefix="/resources", tags=["resources"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(achievements.router, prefix="/achievements", tags=["achievements"])
api_router.include_router(publications.router, prefix="/publications", tags=["publications"])
api_router.include_router(research_area.router, prefix="/research", tags=["research"])
api_router.include_router(cv.router, prefix="/cv", tags=["cv"])