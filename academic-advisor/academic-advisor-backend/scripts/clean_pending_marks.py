import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def clean_pending_marks():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['academic_advisor']
    
    # Check how many there are
    count_before = await db.pending_student_marks.count_documents({})
    print(f"Found {count_before} pending marks records to clean.")
    
    # Delete all
    res = await db.pending_student_marks.delete_many({})
    print(f"Successfully deleted {res.deleted_count} old pending marks records.")
    
    # Optional: We could also remove any 'seat_number_history' from StudentProfile if needed, 
    # but that doesn't hurt. We definitely should reset marks_synced_at so they can fetch anew.
    res2 = await db.student_profiles.update_many(
        {}, 
        {"$set": {"pending_marks_checked": False}, "$unset": {"marks_synced_at": ""}}
    )
    print(f"Reset sync flags for {res2.modified_count} student profiles.")

if __name__ == "__main__":
    asyncio.run(clean_pending_marks())
