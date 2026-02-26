# app/core/deps.py

"""
Dependency injection module - Re-exports from security.py for backward compatibility
"""

from app.core.security import (
    FirebaseUser,
    get_current_user,
    get_current_faculty,
    get_current_student,
    verify_firebase_token,
    create_access_token,
    verify_password,
    get_password_hash,
    security,
    pwd_context
)

__all__ = [
    "FirebaseUser",
    "get_current_user",
    "get_current_faculty", 
    "get_current_student",
    "verify_firebase_token",
    "create_access_token",
    "verify_password",
    "get_password_hash",
    "security",
    "pwd_context"
]