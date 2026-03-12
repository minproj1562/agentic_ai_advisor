# academic-advisor-backend/scripts/seed_chatbot_data.py

"""
Master chatbot seeding script
Seeds career data + creates initial analytics document
"""

import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.core.config import settings
from app.models.career import CareerPath
from app.models.chatbot import ChatSession, ChatFeedback, ChatbotAnalyticsDoc

logger = logging.getLogger(__name__)

ALL_MODELS = [CareerPath, ChatSession, ChatFeedback, ChatbotAnalyticsDoc]


async def seed_all():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    # 1) Clear old analytics data BEFORE initializing Beanie
    # This avoids the validation error when Beanie tries to read bad documents
    print("🗑️  Clearing old data with invalid IDs...")
    
    analytics_collection = db["chatbot_analytics"]
    delete_result = await analytics_collection.delete_many({})
    print(f"   - Deleted {delete_result.deleted_count} old analytics documents")
    
    sessions_collection = db["chat_sessions"]
    feedback_collection = db["chat_feedback"]
    
    await sessions_collection.delete_many({})
    await feedback_collection.delete_many({})
    print("   - Cleared chat sessions and feedback")
    
    # 2) Now initialize Beanie (safe because bad docs are deleted)
    await init_beanie(
        database=db,
        document_models=ALL_MODELS,
    )

    # 3) Career data
    from scripts.seed_career_data import seed_careers
    career_count = await seed_careers()

    # 4) Create fresh analytics doc for today
    from app.repositories.analytics_repository import AnalyticsRepository
    repo = AnalyticsRepository()
    await repo.get_or_create_today()

    print(f"\n✅ Chatbot seeding complete:")
    print(f"   - {career_count} career paths")
    print(f"   - Analytics document initialized")

    client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_all())