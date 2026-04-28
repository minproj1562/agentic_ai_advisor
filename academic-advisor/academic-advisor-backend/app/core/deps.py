# app/core/deps.py
"""
Dependency injection module — re-exports from security.py for backward compatibility.

All symbols that other modules import from deps.py are defined or
re-exported from security.py.  Do NOT add business logic here.
"""

from app.core.security import (
    FirebaseUser,
    get_current_user,
    get_current_faculty,
    get_current_student,
    verify_firebase_token,   # now defined in security.py (wraps firebase.py)
    create_access_token,     # now defined in security.py
    verify_password,
    get_password_hash,
    security,
    pwd_context,
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
    "pwd_context",
]