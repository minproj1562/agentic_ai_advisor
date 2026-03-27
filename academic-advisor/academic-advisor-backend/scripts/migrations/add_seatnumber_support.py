#academic-advisor/academic-advisor-backend/scripts/migrations/add_seatnumber_support.py
import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.student_profile import StudentProfile
from app.models.pending_marks import PendingStudentMarks
from dotenv import load_dotenv

load_dotenv()

async def migrate():
    """Add seat number fields to existing documents"""
    
    # Initialize database
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    db = client[os.getenv("DB_NAME", "academic_advisor")]
    
    await init_beanie(
        database=db,
        document_models=[StudentProfile, PendingStudentMarks]
    )
    
    print("Starting migration...")
    
    # Update student profiles
    profiles = await StudentProfile.find_all().to_list()
    updated = 0
    
    for profile in profiles:
        if not hasattr(profile, 'current_seat_number'):
            profile.current_seat_number = None
            profile.seat_number_history = []
            profile.marks_synced_at = None
            profile.pending_marks_checked = False
            await profile.save()
            updated += 1
    
    print(f"✅ Updated {updated} student profiles")
    
    # Update pending marks
    pending = await PendingStudentMarks.find_all().to_list()
    updated_pending = 0
    
    for pm in pending:
        if not hasattr(pm, 'seat_number'):
            pm.seat_number = None
            await pm.save()
            updated_pending += 1
    
    print(f"✅ Updated {updated_pending} pending marks records")
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())