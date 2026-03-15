# check_full.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json

async def check():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["academic_advisor"]
    
    # Get one full document
    doc = await db.student_profiles.find_one({"user_id": "9uiiDYLafNSZoideb3yN3c9jfr02"})
    if doc:
        doc['_id'] = str(doc['_id'])
        print(json.dumps(doc, indent=2, default=str))
    
    client.close()

asyncio.run(check())