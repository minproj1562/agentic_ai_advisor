"""
FastAPI Dependencies - UPDATED
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

# REMOVED: Duplicate get_current_user - use the one from security.py
from app.core.security import get_current_user, get_current_faculty, get_current_student, FirebaseUser

from app.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)

# OAuth2 scheme
oauth2_scheme = HTTPBearer(auto_error=True)


# ---------------------------
# Role-based access (already in security.py, just import and use)
# ---------------------------

async def get_faculty_user(
    current_user: FirebaseUser = Depends(get_current_user)
) -> FirebaseUser:
    """
    Restrict access to faculty users
    NOTE: This allows ONLY faculty role, not students
    """
    if current_user.role != "faculty":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Faculty access required. Current role: {current_user.role}"
        )
    return current_user


async def get_student_user(
    current_user: FirebaseUser = Depends(get_current_user)
) -> FirebaseUser:
    """
    Restrict access to student users
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )
    return current_user


async def get_admin_user(
    current_user: FirebaseUser = Depends(get_current_user)
) -> FirebaseUser:
    """
    Restrict access to admin users
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ---------------------------
# Service & Manager Providers
# ---------------------------

def get_websocket_manager():
    from app.core.websocket import ConnectionManager
    return ConnectionManager()


def get_cache_manager():
    from app.core.cache import CacheManager
    return CacheManager()


def get_ml_analyzer():
    from app.services.ml_performance_analysis import ml_analyzer
    return ml_analyzer


def get_student_service():
    from app.services.student_analysis_service import StudentAnalysisService
    return StudentAnalysisService()


# ---------------------------
# Common Query Parameters
# ---------------------------

class PaginationParams:
    """Common pagination parameters"""
    def __init__(self, skip: int = 0, limit: int = 100):
        self.skip = max(skip, 0)
        self.limit = min(limit, 100)


class FilterParams:
    """Common filter parameters"""
    def __init__(
        self,
        department: Optional[str] = None,
        semester: Optional[int] = None,
        batch: Optional[int] = None
    ):
        self.department = department
        self.semester = semester
        self.batch = batch

    def to_firebase_filters(self):
        """Convert to Firebase filter format"""
        filters = []
        if self.department:
            filters.append({"field": "department", "operator": "==", "value": self.department})
        if self.semester:
            filters.append({"field": "current_semester", "operator": "==", "value": self.semester})
        if self.batch:
            filters.append({"field": "batch", "operator": "==", "value": self.batch})
        return filters