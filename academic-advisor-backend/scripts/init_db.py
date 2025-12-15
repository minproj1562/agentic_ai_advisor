# scripts/init_db.py
"""
Database initialization script
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.firebase_admin import firebase_manager
from app.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)


async def init_collections():
    """Initialize Firebase collections with sample structure"""
    
    collections = [
        'students',
        'faculty',
        'courses',
        'resources',
        'announcements',
        'interventions',
        'predictions',
        'analytics_cache',
        'notification_queue'
    ]
    
    for collection in collections:
        try:
            # Create a dummy document to initialize collection
            await firebase_manager.create_document(
                collection=collection,
                document_id='_init',
                data={'initialized': True}
            )
            
            # Delete the dummy document
            await firebase_manager.delete_document(
                collection=collection,
                document_id='_init'
            )
            
            logger.info(f"Initialized collection: {collection}")
            
        except Exception as e:
            logger.error(f"Failed to initialize {collection}: {str(e)}")


async def create_indexes():
    """Create necessary indexes for performance"""
    # This would be done in Firebase Console or using Firebase CLI
    logger.info("Indexes should be created in Firebase Console")


async def setup_initial_data():
    """Setup initial data if needed"""
    
    # Create admin user if not exists
    admin_email = "admin@academicadvisor.com"
    
    try:
        admin = await firebase_manager.get_collection(
            collection='users',
            filters=[{'field': 'email', 'operator': '==', 'value': admin_email}]
        )
        
        if not admin:
            await firebase_manager.create_document(
                collection='users',
                data={
                    'email': admin_email,
                    'name': 'System Admin',
                    'role': 'admin',
                    'is_active': True
                }
            )
            logger.info("Created admin user")
        else:
            logger.info("Admin user already exists")
            
    except Exception as e:
        logger.error(f"Failed to setup initial data: {str(e)}")


async def main():
    """Main initialization function"""
    logger.info("Starting database initialization...")
    
    # Initialize Firebase
    from app.core.firebase_admin import initialize_firebase
    initialize_firebase()
    
    # Initialize collections
    await init_collections()
    
    # Create indexes
    await create_indexes()
    
    # Setup initial data
    await setup_initial_data()
    
    logger.info("Database initialization completed!")


if __name__ == "__main__":
    asyncio.run(main())