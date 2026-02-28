# academic-advisor/academic-advisor-backend/scripts/seed_chatbot_data.py
"""
Master chatbot seeding script
Seeds career data + creates initial analytics document
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.core.config import settings
from app.models.career import CareerPath
from app.models.chatbot import ChatSession, ChatFeedback, ChatbotAnalyticsDoc

logger = logging.getLogger(__name__)

ALL_MODELS = [CareerPath, ChatSession, ChatFeedback, ChatbotAnalyticsDoc]


async def seed_all():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.MONGODB_DATABASE],
        document_models=ALL_MODELS,
    )

    # 1) Career data
    from scripts.seed_career_data import seed_careers
    career_count = await seed_careers()

    # 2) Initial analytics doc for today
    from app.repositories.analytics_repository import AnalyticsRepository
    repo = AnalyticsRepository()
    await repo.get_or_create_today()

    print(f"✅ Chatbot seeding complete:")
    print(f"   - {career_count} career paths")
    print(f"   - Analytics document initialized")

    client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_all())