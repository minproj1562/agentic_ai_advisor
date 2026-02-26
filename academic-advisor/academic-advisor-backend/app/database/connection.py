# app/database/connection.py
"""
Firebase database connection configuration
"""

from app.core.firebase_admin import firebase_manager
from app.core.config import settings

# Mock engine for compatibility with existing code
engine = None

# Mock session functions for compatibility
def get_db():
    """
    Mock database session for compatibility.
    Returns Firebase manager instance.
    """
    return firebase_manager

def init_db():
    """
    Initialize Firebase connection.
    This is called during app startup.
    """
    try:
        # Firebase is already initialized in firebase_manager
        print("✅ Firebase database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return False

# Export for compatibility
__all__ = ['engine', 'get_db', 'init_db']