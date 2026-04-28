# scripts/find_wrong_semesters.py
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.student_profile import StudentProfile
from app.config import settings

async def find():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    await init_beanie(database=db, document_models=[StudentProfile])

    students = await StudentProfile.find_all().to_list()
    found = 0
    for s in students:
        for sr in s.semester_records:
            if sr.semester_number in (3, 6):
                print(f"\nStudent {s.roll_number}: semester {sr.semester_number}")
                for sub in sr.subjects:
                    print(f"  - {sub.subject_code}: {sub.subject_name}")
                found += 1
    if found == 0:
        print("No semester 3 or 6 records found in any student.")

if __name__ == "__main__":
    asyncio.run(find())