# scripts/reseed_readiness.py
import asyncio
import sys
sys.path.insert(0, '.')

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.readiness import SubjectRequirementMap
from app.services._seed_readiness_data import build_seed_documents

async def reseed():
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    await init_beanie(database=db, document_models=[SubjectRequirementMap])
    
    # Delete all existing maps
    deleted = await SubjectRequirementMap.find_all().delete()
    print(f"Deleted {deleted.deleted_count if hasattr(deleted, 'deleted_count') else 'all'} existing maps")
    
    # Insert new seed data
    docs = build_seed_documents()
    for doc in docs:
        await doc.insert()
    
    print(f"✅ Seeded {len(docs)} requirement maps")
    
    # List what was seeded
    interests = await SubjectRequirementMap.find({"target_type": "interest"}).to_list()
    electives = await SubjectRequirementMap.find({"target_type": "elective"}).to_list()
    honours = await SubjectRequirementMap.find({"target_type": "honours"}).to_list()
    
    print(f"\n📚 Interests: {[i.target_name for i in interests]}")
    print(f"📖 Electives: {[e.target_name for e in electives]}")
    print(f"🎓 Honours: {[h.target_name for h in honours]}")

if __name__ == "__main__":
    asyncio.run(reseed())