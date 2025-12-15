# app/dependencies.py
"""
FastAPI Dependencies
Reusable dependencies for dependency injection
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import settings
from app.core.firebase_admin import firebase_manager
from app.utils.helpers import get_logger

logger = get_logger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# ---------------------------
# Authentication & User Roles
# ---------------------------

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Get current authenticated user from JWT token and Firebase
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        uid: str = payload.get("uid")
        if uid is None:
            raise credentials_exception

        # Fetch user from Firebase
        user = await firebase_manager.get_document(
            collection="users",
            document_id=uid
        )
        if user is None:
            raise credentials_exception

        return user

    except JWTError:
        raise credentials_exception
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise credentials_exception


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Ensure the current user is active
    """
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_admin_user(
    current_user: dict = Depends(get_current_active_user)
) -> dict:
    """
    Restrict access to admin users
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_faculty_user(
    current_user: dict = Depends(get_current_active_user)
) -> dict:
    """
    Restrict access to faculty or admin users
    """
    if current_user.get("role") not in ["faculty", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faculty access required"
        )
    return current_user


async def get_student_user(
    current_user: dict = Depends(get_current_active_user)
) -> dict:
    """
    Restrict access to student users
    """
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
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
    """
    Common pagination parameters
    """
    def __init__(self, skip: int = 0, limit: int = 100):
        self.skip = max(skip, 0)
        self.limit = min(limit, 100)


class FilterParams:
    """
    Common filter parameters
    """
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
