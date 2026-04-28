# app/core/security.py
"""
Security — verifies BOTH student plain JWTs and Firebase ID tokens.

Student  → HS256 JWT  (issued by /auth/student/login)
Faculty  → Firebase ID token (issued by Firebase Auth)
Admin    → Firebase ID token (issued by Firebase Auth)
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import logging

from app.core.firebase import verify_firebase_token as _verify_firebase_token_util

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=True)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

STUDENT_JWT_SECRET = os.getenv("STUDENT_JWT_SECRET", "student-secret-change-in-prod")
STUDENT_JWT_ALGO   = "HS256"
STUDENT_JWT_EXPIRE = 60 * 24 * 7  # 7 days in minutes


# ──────────────────────────────────────────────────────────────
# Public re-export so deps.py can import verify_firebase_token
# from this module (backward compatibility)
# ──────────────────────────────────────────────────────────────

def verify_firebase_token(token: str) -> Dict[str, Any]:
    """
    Thin wrapper — delegates to app.core.firebase.verify_firebase_token.
    Exported here so that deps.py (backward-compat shim) can import it
    from a single place.
    """
    return _verify_firebase_token_util(token)


# ──────────────────────────────────────────────────────────────
# create_access_token  (student JWT — matches auth.py logic)
# ──────────────────────────────────────────────────────────────

def create_access_token(
    uid: str,
    roll_number: str = "",
    name: str = "",
    branch: str = "",
    role: str = "student",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a plain HS256 JWT for student sessions.

    Parameters
    ----------
    uid         : Firebase UID or placeholder (e.g. "student_5023152")
    roll_number : Student roll number
    name        : Student display name
    branch      : Academic branch (e.g. "IT")
    role        : Always "student" for this token type
    expires_delta : Override default 7-day expiry if needed
    """
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=STUDENT_JWT_EXPIRE))

    payload = {
        "uid":         uid,
        "roll_number": roll_number,
        "name":        name,
        "branch":      branch,
        "role":        role,
        "iat":         now,
        "exp":         expire,
    }
    return pyjwt.encode(payload, STUDENT_JWT_SECRET, algorithm=STUDENT_JWT_ALGO)


# ──────────────────────────────────────────────────────────────
# User model
# ──────────────────────────────────────────────────────────────

class FirebaseUser:
    """Unified user model for all roles."""

    def __init__(self, uid: str, email: str, role: str = "student", extra: Dict = None):
        self.uid   = uid
        self.email = email
        self.role  = role
        self.extra = extra or {}

    @property
    def is_faculty(self) -> bool:
        return self.role == "faculty"

    @property
    def is_student(self) -> bool:
        return self.role == "student"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def __repr__(self):
        return f"FirebaseUser(uid={self.uid}, email={self.email}, role={self.role})"


# ──────────────────────────────────────────────────────────────
# Token verification helpers
# ──────────────────────────────────────────────────────────────

def _try_student_jwt(token: str) -> Optional[FirebaseUser]:
    """
    Try to decode token as a student HS256 JWT.
    Returns FirebaseUser on success, None if it is not a student JWT.
    Raises HTTPException if the token IS a student JWT but is expired.
    """
    try:
        payload = pyjwt.decode(
            token,
            STUDENT_JWT_SECRET,
            algorithms=[STUDENT_JWT_ALGO],
        )
        # Must carry role=student to be treated as a student JWT
        if payload.get("role") != "student":
            return None

        return FirebaseUser(
            uid=payload["uid"],
            email=payload.get("roll_number", ""),
            role="student",
            extra={
                "roll_number": payload.get("roll_number"),
                "name":        payload.get("name"),
                "branch":      payload.get("branch"),
            },
        )
    except pyjwt.ExpiredSignatureError:
        logger.warning("Student JWT expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired — please log in again",
        )
    except pyjwt.InvalidTokenError:
        # Not a student JWT — caller will try Firebase next
        return None


def _try_firebase_token(token: str) -> FirebaseUser:
    """
    Verify token as a Firebase ID token (faculty / admin).
    Raises HTTPException on failure.
    """
    try:
        decoded = _verify_firebase_token_util(token)
        uid     = decoded.get("uid")
        email   = decoded.get("email", "")
        role    = decoded.get("role", "student")

        # Custom claims may be nested
        if "claims" in decoded:
            role = decoded["claims"].get("role", role)

        logger.info(f"✅ Firebase token verified: {email} ({role})")
        return FirebaseUser(uid=uid, email=email, role=role)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Firebase token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


# ──────────────────────────────────────────────────────────────
# FastAPI dependency
# ──────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> FirebaseUser:
    """
    Universal auth dependency.

    1. Try student HS256 JWT first (fast, no network call)
    2. Fall back to Firebase ID token (faculty / admin)
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token provided",
        )

    token = credentials.credentials

    # ── Step 1: Student JWT ──
    student_user = _try_student_jwt(token)
    if student_user is not None:
        logger.debug(f"✅ Student JWT: {student_user.extra.get('roll_number')}")
        return student_user

    # ── Step 2: Firebase ID token (faculty / admin) ──
    return _try_firebase_token(token)


# ──────────────────────────────────────────────────────────────
# Role guards
# ──────────────────────────────────────────────────────────────

async def get_current_faculty(
    current_user: FirebaseUser = Depends(get_current_user),
) -> FirebaseUser:
    if not current_user.is_faculty:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faculty access required",
        )
    return current_user


async def get_current_student(
    current_user: FirebaseUser = Depends(get_current_user),
) -> FirebaseUser:
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )
    return current_user


# ──────────────────────────────────────────────────────────────
# Password helpers
# ──────────────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)