# app/api/v1/auth.py
"""
Authentication API endpoints
Handles student/faculty/admin login and password management
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.firebase_admin import firebase_manager
from app.core.security import FirebaseUser, get_current_user
from app.utils.password import (
    generate_student_password,
    hash_password,
    verify_password,
    validate_roll_number,
    validate_password_strength,
    extract_admission_year_from_roll
)
from app.database.connection import get_mongo_database
from app.utils.helpers import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ==================== Schemas ====================

class StudentLoginRequest(BaseModel):
    roll_number: str = Field(..., min_length=7, max_length=7)
    password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class ResetPasswordRequest(BaseModel):
    roll_number: str = Field(..., min_length=7, max_length=7)
    email: str


# ==================== Student Login ====================

@router.post("/student/login")
async def student_login(credentials: StudentLoginRequest):
    """
    Student login with roll number and password.
    
    Flow:
    1. Validate roll number format
    2. Find student in MongoDB (student_profiles)
    3. Verify password
    4. Create/update Firebase Auth user
    5. Return Firebase custom token
    """
    try:
        # Validate roll number
        is_valid, error_msg = validate_roll_number(credentials.roll_number)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Find student in MongoDB
        db = get_mongo_database()
        if db is None:  # ✅ FIXED: Use "is None" instead of "not db"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
        
        student = await db.student_profiles.find_one({
            "roll_number": credentials.roll_number
        })
        
        if not student:
            logger.warning(f"Login attempt for non-existent roll number: {credentials.roll_number}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid roll number or password"
            )
        
        # Verify password
        stored_password_hash = student.get("password_hash")
        
        if not stored_password_hash:
            # First-time login - password not set yet
            # Generate default password and compare
            default_password = generate_student_password(
                credentials.roll_number,
                student.get("admission_year")
            )
            
            if credentials.password != default_password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid roll number or password"
                )
            
            # Hash and store the password for future logins
            password_hash = hash_password(default_password)
            await db.student_profiles.update_one(
                {"_id": student["_id"]},
                {
                    "$set": {
                        "password_hash": password_hash,
                        "password_changed": False,
                        "last_login": datetime.utcnow()
                    }
                }
            )
        else:
            # Verify stored password
            if not verify_password(credentials.password, stored_password_hash):
                logger.warning(f"Invalid password for roll number: {credentials.roll_number}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid roll number or password"
                )
            
            # Update last login
            await db.student_profiles.update_one(
                {"_id": student["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        
        # Get or create Firebase user
        user_id = student.get("user_id")
        
        if not user_id:
            # Create Firebase user
            email = student.get("email") or f"{credentials.roll_number}@student.college.edu"
            
            try:
                from firebase_admin import auth
                
                # Create user in Firebase Auth
                firebase_user = auth.create_user(
                    email=email,
                    password=credentials.password,
                    display_name=student.get("name"),
                    email_verified=False
                )
                
                user_id = firebase_user.uid
                
                # Set custom claims (role)
                auth.set_custom_user_claims(user_id, {"role": "student"})
                
                # Update student profile with user_id
                await db.student_profiles.update_one(
                    {"_id": student["_id"]},
                    {"$set": {"user_id": user_id}}
                )
                
                # Create Firestore user document
                await firebase_manager.create_document(
                    "users",
                    {
                        "uid": user_id,
                        "email": email,
                        "name": student.get("name"),
                        "displayName": student.get("name"),
                        "role": "student",
                        "roll_number": credentials.roll_number,
                        "department": student.get("branch"),
                        "current_semester": student.get("current_semester"),
                        "emailVerified": False,
                    },
                    user_id
                )
                
            except Exception as e:
                logger.error(f"Failed to create Firebase user: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user account"
                )
        
        # Generate custom token for frontend
        from firebase_admin import auth
        custom_token = auth.create_custom_token(user_id)
        
        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "uid": user_id,
                "name": student.get("name"),
                "roll_number": credentials.roll_number,
                "email": student.get("email"),
                "branch": student.get("branch"),
                "semester": student.get("current_semester"),
                "role": "student",
                "password_changed": student.get("password_changed", False),
            },
            "token": custom_token.decode('utf-8'),
            "requires_password_change": not student.get("password_changed", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Student login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


# ==================== Change Password ====================

@router.post("/student/change-password")
async def change_student_password(
    request: ChangePasswordRequest,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Allow student to change their password.
    """
    try:
        # Verify user is a student
        if current_user.role != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can use this endpoint"
            )
        
        # Validate new password
        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New passwords do not match"
            )
        
        is_valid, error_msg = validate_password_strength(request.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Get student from MongoDB
        db = get_mongo_database()
        if db is None:  # ✅ FIXED: Use "is None" instead of "not db"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
        
        student = await db.student_profiles.find_one({"user_id": current_user.uid})
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )
        
        # Verify current password
        stored_hash = student.get("password_hash")
        if stored_hash:
            if not verify_password(request.current_password, stored_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect"
                )
        else:
            # If no password_hash, verify against default password
            default_password = generate_student_password(
                student.get("roll_number"),
                student.get("admission_year")
            )
            if request.current_password != default_password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect"
                )
        
        # Hash new password
        new_password_hash = hash_password(request.new_password)
        
        # Update in MongoDB
        await db.student_profiles.update_one(
            {"_id": student["_id"]},
            {
                "$set": {
                    "password_hash": new_password_hash,
                    "password_changed": True,
                    "password_changed_at": datetime.utcnow()
                }
            }
        )
        
        # Update Firebase Auth password
        try:
            from firebase_admin import auth
            auth.update_user(
                current_user.uid,
                password=request.new_password
            )
        except Exception as e:
            logger.warning(f"Failed to update Firebase password: {e}")
        
        return {
            "success": True,
            "message": "Password changed successfully",
            "password_changed_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


# ==================== Reset Password (Admin) ====================

@router.post("/admin/reset-student-password")
async def admin_reset_student_password(
    roll_number: str = Body(..., embed=True),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Admin endpoint to reset a student's password to default.
    """
    try:
        # Verify admin role
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Find student
        db = get_mongo_database()
        if db is None:  # ✅ FIXED: Use "is None" instead of "not db"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
        
        student = await db.student_profiles.find_one({"roll_number": roll_number})
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with roll number {roll_number} not found"
            )
        
        # Generate default password
        default_password = generate_student_password(
            roll_number,
            student.get("admission_year")
        )
        
        # Hash it
        password_hash = hash_password(default_password)
        
        # Update MongoDB
        await db.student_profiles.update_one(
            {"_id": student["_id"]},
            {
                "$set": {
                    "password_hash": password_hash,
                    "password_changed": False,
                    "password_reset_at": datetime.utcnow(),
                    "password_reset_by": current_user.uid
                }
            }
        )
        
        # Update Firebase if user exists
        if student.get("user_id"):
            try:
                from firebase_admin import auth
                auth.update_user(
                    student["user_id"],
                    password=default_password
                )
            except Exception as e:
                logger.warning(f"Failed to update Firebase password: {e}")
        
        return {
            "success": True,
            "message": f"Password reset to default for {student.get('name')}",
            "roll_number": roll_number,
            "default_password": default_password,  # Return for admin to share with student
            "password_format": f"{roll_number}@{student.get('admission_year')}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )