# academic-advisor-backend/scripts/migrations/fix_seat_numbers.py
"""
Fix seat numbers in MongoDB - trim 6-digit seat numbers to 5 digits
Run: python -m scripts.migrations.fix_seat_numbers
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

async def fix_seat_numbers():
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    
    # Connect directly with motor (bypass Beanie validation)
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    collection = db["student_profiles"]
    
    print("🔍 Scanning for invalid seat numbers...")
    
    # Find all documents with seat numbers
    cursor = collection.find({
        "$or": [
            {"current_seat_number": {"$exists": True, "$ne": None}},
            {"seat_number_history": {"$exists": True, "$ne": []}}
        ]
    })
    
    fixed_count = 0
    
    async for doc in cursor:
        updates = {}
        needs_update = False
        
        # Fix current_seat_number
        current_seat = doc.get("current_seat_number")
        if current_seat and len(str(current_seat)) != 5:
            if len(str(current_seat)) == 6:
                # Trim to last 5 digits
                new_seat = str(current_seat)[-5:]
                updates["current_seat_number"] = new_seat
                needs_update = True
                print(f"  📝 User {doc.get('user_id')}: current_seat_number {current_seat} → {new_seat}")
            else:
                # Invalid length, set to None
                updates["current_seat_number"] = None
                needs_update = True
                print(f"  ⚠️ User {doc.get('user_id')}: current_seat_number {current_seat} → None (invalid length)")
        
        # Fix seat_number_history
        history = doc.get("seat_number_history", [])
        if history:
            new_history = []
            history_changed = False
            
            for record in history:
                seat_num = record.get("seat_number", "")
                if len(str(seat_num)) == 6:
                    record["seat_number"] = str(seat_num)[-5:]
                    history_changed = True
                    print(f"  📝 User {doc.get('user_id')}: history seat {seat_num} → {record['seat_number']}")
                elif len(str(seat_num)) != 5:
                    history_changed = True
                    print(f"  ⚠️ User {doc.get('user_id')}: removing invalid history seat {seat_num}")
                    continue  # Skip invalid entries
                new_history.append(record)
            
            if history_changed:
                updates["seat_number_history"] = new_history
                needs_update = True
        
        if needs_update:
            await collection.update_one(
                {"_id": doc["_id"]},
                {"$set": updates}
            )
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} document(s)")
    
    # Verify
    print("\n🔍 Verifying...")
    cursor = collection.find({"current_seat_number": {"$exists": True, "$ne": None}})
    async for doc in cursor:
        seat = doc.get("current_seat_number")
        status = "✅" if seat and len(str(seat)) == 5 else "❌"
        print(f"  {status} User {doc.get('user_id')}: seat_number = {seat}")
    
    client.close()
    print("\n🎉 Migration complete!")


if __name__ == "__main__":
    asyncio.run(fix_seat_numbers())