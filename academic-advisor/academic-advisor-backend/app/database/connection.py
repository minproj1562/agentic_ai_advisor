# app/database/connection.py
"""
Database connection configuration
Supports both Firebase and MongoDB connections
UPDATED: Added set_database() and ensure_indexes() for chatbot support
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════
# MONGODB CONNECTION (for Beanie and direct Motor access)
# ══════════════════════════════════════════════════════════

_mongo_client: Optional[AsyncIOMotorClient] = None
_mongo_database: Optional[AsyncIOMotorDatabase] = None


def set_database(client: AsyncIOMotorClient, database: AsyncIOMotorDatabase):
    """
    Set the global database references.
    Called from main.py lifespan after Beanie initialization.
    """
    global _mongo_client, _mongo_database
    _mongo_client = client
    _mongo_database = database
    logger.info(f"✅ Database connection set: {database.name}")


def get_mongo_client() -> Optional[AsyncIOMotorClient]:
    """Get the MongoDB client instance."""
    global _mongo_client
    if _mongo_client is None:
        try:
            from app.config import settings
            _mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
            logger.info("MongoDB client created")
        except Exception as e:
            logger.error(f"Failed to create MongoDB client: {e}")
            return None
    return _mongo_client


def get_mongo_database() -> Optional[AsyncIOMotorDatabase]:
    """Get the MongoDB database instance."""
    global _mongo_database
    if _mongo_database is None:
        try:
            from app.config import settings
            client = get_mongo_client()
            if client:
                _mongo_database = client[settings.MONGODB_DATABASE]
                logger.info(f"MongoDB database: {settings.MONGODB_DATABASE}")
        except Exception as e:
            logger.error(f"Failed to get MongoDB database: {e}")
            return None
    return _mongo_database


async def get_collection(collection_name: str) -> Optional[AsyncIOMotorCollection]:
    """
    Get a MongoDB collection by name.
    
    Args:
        collection_name: Name of the collection (e.g., "subjects", "faculty")
        
    Returns:
        AsyncIOMotorCollection instance or None if connection fails
        
    Usage:
        collection = await get_collection("subjects")
        doc = await collection.find_one({"code": "CSC401"})
    """
    db = get_mongo_database()
    if db is None:
        logger.error(f"Cannot get collection '{collection_name}': Database not connected")
        return None
    return db[collection_name]


async def ensure_indexes():
    """
    Create necessary database indexes for optimal chatbot performance.
    Called during application startup.
    """
    db = get_mongo_database()
    if db is None:
        logger.warning("Cannot create indexes: Database not connected")
        return
    
    try:
        # Subjects collection indexes
        subjects = db["subjects"]
        await subjects.create_index("code", unique=True, sparse=True)
        await subjects.create_index("semester")
        await subjects.create_index("department")
        try:
            await subjects.create_index(
                [("name", "text"), ("description", "text"), ("learning_outcomes", "text")],
                name="subjects_text_search"
            )
        except Exception as e:
            logger.debug(f"Text index may already exist: {e}")
        
        # Topics collection indexes
        topics = db["topics"]
        await topics.create_index("name")
        try:
            await topics.create_index(
                [("name", "text"), ("definition", "text"), ("keywords", "text")],
                name="topics_text_search"
            )
        except Exception as e:
            logger.debug(f"Topics text index may already exist: {e}")
        
        # Subject units collection indexes
        units = db["subject_units"]
        await units.create_index("subject")
        await units.create_index("unit_number")
        
        # Chat sessions indexes
        sessions = db["chat_sessions"]
        await sessions.create_index("user_id")
        await sessions.create_index("session_token", unique=True, sparse=True)
        await sessions.create_index("expires_at")
        await sessions.create_index("is_active")
        
        # Chat messages indexes
        messages = db["chat_messages"]
        await messages.create_index("session_id")
        await messages.create_index("user_id")
        await messages.create_index([("created_at", -1)])
        
        # Career paths indexes
        careers = db["career_paths"]
        await careers.create_index("category")
        await careers.create_index("is_active")
        try:
            await careers.create_index(
                [("title", "text"), ("description", "text"), ("keywords", "text")],
                name="careers_text_search"
            )
        except Exception as e:
            logger.debug(f"Careers text index may already exist: {e}")
        
        # Faculty indexes (if not already created)
        faculty = db["faculty"]
        await faculty.create_index("user_id", unique=True, sparse=True)
        await faculty.create_index("department")
        await faculty.create_index("status")
        
        logger.info("✅ Database indexes created/verified")
    except Exception as e:
        logger.warning(f"⚠️ Index creation warning (non-fatal): {e}")


async def close_mongo_connection():
    """Close the MongoDB connection."""
    global _mongo_client, _mongo_database
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _mongo_database = None
        logger.info("MongoDB connection closed")


# ══════════════════════════════════════════════════════════
# FIREBASE CONNECTION (for authentication and realtime features)
# ══════════════════════════════════════════════════════════

try:
    from app.core.firebase_admin import firebase_manager
    _firebase_available = True
except ImportError:
    firebase_manager = None
    _firebase_available = False
    logger.warning("Firebase manager not available")


# Legacy compatibility
engine = None


def get_db():
    """
    Get database connection.
    Returns Firebase manager for backward compatibility.
    For MongoDB, use get_collection() or Beanie models directly.
    """
    if _firebase_available:
        return firebase_manager
    return get_mongo_database()


def init_db():
    """
    Initialize database connections.
    Called during app startup.
    """
    try:
        # Initialize MongoDB
        db = get_mongo_database()
        if db is not None:
            logger.info("✅ MongoDB connection initialized")
        
        # Firebase is initialized separately in main.py
        if _firebase_available:
            logger.info("✅ Firebase manager available")
        
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False


# ══════════════════════════════════════════════════════════
# EXPORTS
# ══════════════════════════════════════════════════════════

__all__ = [
    # MongoDB
    'get_mongo_client',
    'get_mongo_database', 
    'get_collection',
    'close_mongo_connection',
    'set_database',
    'ensure_indexes',
    # Legacy/Firebase
    'engine',
    'get_db',
    'init_db',
]