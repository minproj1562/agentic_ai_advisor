# academic-advisor-backend/app/api/v1/auth.py
"""
Authentication API endpoints
Handles student/faculty/admin login and password management
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import jwt  # pip install PyJWT

from app.core.security import FirebaseUser, get_current_user
from app.utils.password import (
    generate_student_password,
    hash_password,
    verify_password,
    validate_roll_number,
    validate_password_strength,
)
from app.database.connection import get_mongo_database
from app.utils.helpers import get_logger

logger = get_logger(__name__)
router = APIRouter()

# ── JWT config for students ──────────────────────────────────────────────────
# Use a strong secret in production (.env)
import os
STUDENT_JWT_SECRET  = os.getenv("STUDENT_JWT_SECRET", "student-secret-change-in-prod")
STUDENT_JWT_ALGO    = "HS256"
STUDENT_JWT_EXPIRE  = 60 * 24 * 7   # 7 days in minutes


def _create_student_jwt(uid: str, roll_number: str, name: str, branch: str) -> str:
    """Create a plain HS256 JWT for student sessions."""
    now = datetime.utcnow()
    payload = {
        "uid":         uid,
        "roll_number": roll_number,
        "name":        name,
        "branch":      branch,
        "role":        "student",
        "iat":         now,
        "exp":         now + timedelta(minutes=STUDENT_JWT_EXPIRE),
    }
    return jwt.encode(payload, STUDENT_JWT_SECRET, algorithm=STUDENT_JWT_ALGO)


def verify_student_jwt(token: str) -> Dict[str, Any]:
    """
    Verify a student JWT and return its payload.
    Raises HTTPException on failure.
    """
    try:
        payload = jwt.decode(
            token,
            STUDENT_JWT_SECRET,
            algorithms=[STUDENT_JWT_ALGO],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


# ==================== Schemas ====================

class StudentLoginRequest(BaseModel):
    roll_number: str = Field(..., min_length=7, max_length=7)
    password:    str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password:     str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


# ==================== Student Login ====================

@router.post("/student/login")
async def student_login(credentials: StudentLoginRequest):
    """
    Student login with roll number and password.

    Returns a plain JWT (no Firebase).
    Frontend stores it in localStorage and sends it as
    Authorization: Bearer <token> on every request.
    """
    try:
        # 1. Validate roll number format
        is_valid, error_msg = validate_roll_number(credentials.roll_number)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

        # 2. Find student in MongoDB
        db = get_mongo_database()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed",
            )

        student = await db.student_profiles.find_one(
            {"roll_number": credentials.roll_number}
        )

        if not student:
            logger.warning(f"Login attempt for non-existent roll: {credentials.roll_number}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid roll number or password",
            )

        # 3. Verify password
        stored_hash = student.get("password_hash")

        if not stored_hash:
            # First-time login → compare against generated default
            default_pw = generate_student_password(
                credentials.roll_number,
                student.get("admission_year"),
            )
            if credentials.password != default_pw:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid roll number or password",
                )
            # Persist the hash
            await db.student_profiles.update_one(
                {"_id": student["_id"]},
                {
                    "$set": {
                        "password_hash":    hash_password(default_pw),
                        "password_changed": False,
                        "last_login":       datetime.utcnow(),
                    }
                },
            )
        else:
            if not verify_password(credentials.password, stored_hash):
                logger.warning(f"Bad password for roll: {credentials.roll_number}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid roll number or password",
                )
            await db.student_profiles.update_one(
                {"_id": student["_id"]},
                {"$set": {"last_login": datetime.utcnow()}},
            )

        # 4. Resolve user_id (may be a Firebase UID from earlier or a pending_ placeholder)
        user_id = student.get("user_id") or f"student_{credentials.roll_number}"

        # 5. Create plain JWT — no Firebase involved
        token = _create_student_jwt(
            uid=user_id,
            roll_number=credentials.roll_number,
            name=student.get("name", ""),
            branch=student.get("branch", "IT"),
        )

        logger.info(f"✅ Student login: {credentials.roll_number}")

        return {
            "success": True,
            "message": "Login successful",
            "token": token,
            "token_type": "bearer",
            "expires_in": STUDENT_JWT_EXPIRE * 60,   # seconds
            "user": {
                "uid":              user_id,
                "name":             student.get("name", ""),
                "roll_number":      credentials.roll_number,
                "email":            student.get("email"),
                "branch":           student.get("branch", "IT"),
                "semester":         student.get("current_semester", 1),
                "admission_year":   student.get("admission_year"),
                "role":             "student",
                "password_changed": student.get("password_changed", False),
            },
            "requires_password_change": not student.get("password_changed", False),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Student login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again.",
        )


# ==================== Verify Token ====================

@router.get("/verify-token")
async def verify_token_endpoint(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Verify that a stored token is still valid.
    Works for both student JWT and Firebase ID tokens (faculty/admin).
    """
    try:
        db = get_mongo_database()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed",
            )

        if current_user.role == "student":
            student = await db.student_profiles.find_one(
                {"user_id": current_user.uid}
            )
            if not student:
                # Fallback: match by roll_number embedded in uid
                roll = current_user.uid.replace("student_", "")
                student = await db.student_profiles.find_one({"roll_number": roll})

            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student profile not found",
                )

            return {
                "success": True,
                "user": {
                    "uid":         current_user.uid,
                    "name":        student.get("name"),
                    "roll_number": student.get("roll_number"),
                    "email":       student.get("email"),
                    "branch":      student.get("branch"),
                    "semester":    student.get("current_semester"),
                    "role":        "student",
                },
            }

        # Faculty / Admin
        return {
            "success": True,
            "user": {
                "uid":   current_user.uid,
                "email": current_user.email,
                "role":  current_user.role,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


# ==================== Change Password ====================

@router.post("/student/change-password")
async def change_student_password(
    request: ChangePasswordRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Allow student to change their password."""
    try:
        if current_user.role != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can use this endpoint",
            )

        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New passwords do not match",
            )

        is_valid, error_msg = validate_password_strength(request.new_password)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

        db = get_mongo_database()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed",
            )

        student = await db.student_profiles.find_one({"user_id": current_user.uid})
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found",
            )

        # Verify current password
        stored_hash = student.get("password_hash")
        if stored_hash:
            if not verify_password(request.current_password, stored_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect",
                )
        else:
            default_pw = generate_student_password(
                student.get("roll_number"),
                student.get("admission_year"),
            )
            if request.current_password != default_pw:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect",
                )

        await db.student_profiles.update_one(
            {"_id": student["_id"]},
            {
                "$set": {
                    "password_hash":       hash_password(request.new_password),
                    "password_changed":    True,
                    "password_changed_at": datetime.utcnow(),
                }
            },
        )

        return {
            "success": True,
            "message": "Password changed successfully",
            "password_changed_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        )


# ==================== Admin Reset Password ====================

@router.post("/admin/reset-student-password")
async def admin_reset_student_password(
    roll_number: str = Body(..., embed=True),
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Admin endpoint to reset a student's password to default."""
    try:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )

        db = get_mongo_database()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed",
            )

        student = await db.student_profiles.find_one({"roll_number": roll_number})
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {roll_number} not found",
            )

        default_pw  = generate_student_password(roll_number, student.get("admission_year"))
        pw_hash     = hash_password(default_pw)

        await db.student_profiles.update_one(
            {"_id": student["_id"]},
            {
                "$set": {
                    "password_hash":     pw_hash,
                    "password_changed":  False,
                    "password_reset_at": datetime.utcnow(),
                    "password_reset_by": current_user.uid,
                }
            },
        )

        return {
            "success":         True,
            "message":         f"Password reset for {student.get('name')}",
            "roll_number":     roll_number,
            "default_password": default_pw,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password",
        )


# ==================== Forgot Password (Student) ====================

class ForgotPasswordRequest(BaseModel):
    roll_number: str = Field(..., min_length=7, max_length=7)
    email: str = Field(..., min_length=5)


@router.post("/student/forgot-password")
async def student_forgot_password(request: ForgotPasswordRequest):
    """
    Student forgot password — verifies roll number + email match,
    then resets password to the default (roll_number-based) password.
    """
    try:
        db = get_mongo_database()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed",
            )

        student = await db.student_profiles.find_one({
            "roll_number": request.roll_number,
        })

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this roll number",
            )

        # Verify email matches (case-insensitive)
        stored_email = (student.get("email") or "").lower().strip()
        request_email = request.email.lower().strip()

        if not stored_email or stored_email != request_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email does not match our records for this roll number",
            )

        # Reset to default password
        default_pw = generate_student_password(
            request.roll_number,
            student.get("admission_year"),
        )
        pw_hash = hash_password(default_pw)

        await db.student_profiles.update_one(
            {"_id": student["_id"]},
            {
                "$set": {
                    "password_hash":     pw_hash,
                    "password_changed":  False,
                    "password_reset_at": datetime.utcnow(),
                }
            },
        )

        logger.info(f"✅ Password reset via forgot-password for {request.roll_number}")

        return {
            "success": True,
            "message": "Password has been reset successfully",
            "default_password": default_pw,
            "requires_change": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forgot password error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password. Please contact admin.",
        )


# ==================== Faculty Password Change ====================

class FacultyChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password:     str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


@router.post("/faculty/change-password")
async def change_faculty_password(
    request: FacultyChangePasswordRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Allow faculty to change their password via Firebase."""
    try:
        if current_user.role not in ("faculty", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Faculty/admin access required",
            )

        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New passwords do not match",
            )

        is_valid, error_msg = validate_password_strength(request.new_password)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

        # Update password in Firebase
        import firebase_admin.auth as fb_auth
        try:
            fb_auth.update_user(current_user.uid, password=request.new_password)
        except Exception as e:
            logger.error(f"Firebase password update failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password in authentication system",
            )

        # Update must_change_password flag in Firestore
        try:
            from app.core.firebase_admin import firestore_db
            if firestore_db:
                firestore_db.collection('users').document(current_user.uid).update({
                    'must_change_password': False,
                    'password_changed_at': datetime.utcnow(),
                })
        except Exception as e:
            logger.warning(f"Firestore flag update failed (non-critical): {e}")

        logger.info(f"✅ Faculty password changed: {current_user.email}")

        return {
            "success": True,
            "message": "Password changed successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Faculty password change error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        )