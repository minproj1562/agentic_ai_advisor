# scripts/check_analytics.py

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

async def check():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    # Check existing documents
    docs = await db['chatbot_analytics'].find().to_list(10)
    print('Existing analytics docs:')
    for doc in docs:
        doc_id = doc.get("_id")
        print(f"  _id: {doc_id} (type: {type(doc_id).__name__})")
    
    if not docs:
        print('  (no documents)')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check())