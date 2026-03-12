# scripts/check_syllabus_data.py
"""
Script to verify syllabus data in MongoDB
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models.syllabus import Subject, Topic, Department, SubjectUnit


async def check_data():
    """Check what syllabus data exists in MongoDB."""
    print("=" * 60)
    print("📊 Checking Syllabus Data in MongoDB")
    print("=" * 60)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    # Initialize Beanie
    await init_beanie(
        database=db,
        document_models=[Subject, Topic, Department, SubjectUnit]
    )
    
    # Check counts
    print("\n📈 Collection Counts:")
    print("-" * 40)
    
    dept_count = await Department.find().count()
    print(f"  Departments: {dept_count}")
    
    subject_count = await Subject.find().count()
    print(f"  Subjects: {subject_count}")
    
    topic_count = await Topic.find().count()
    print(f"  Topics (standalone): {topic_count}")
    
    unit_count = await SubjectUnit.find().count()
    print(f"  Units (standalone): {unit_count}")
    
    # List subjects
    if subject_count > 0:
        print("\n📚 Subjects in Database:")
        print("-" * 40)
        subjects = await Subject.find().to_list()
        for i, s in enumerate(subjects[:20], 1):
            units = getattr(s, 'units', [])
            topic_count = sum(len(getattr(u, 'topics', [])) for u in units)
            print(f"  {i}. [{s.code}] {s.name} (Sem {s.semester}) - {len(units)} units, {topic_count} topics")
        
        if len(subjects) > 20:
            print(f"  ... and {len(subjects) - 20} more")
    
    # List some topics
    if topic_count > 0:
        print("\n📝 Sample Topics (standalone collection):")
        print("-" * 40)
        topics = await Topic.find().limit(10).to_list()
        for t in topics:
            print(f"  - {t.name} [{t.subject_code}]")
    
    # Check embedded topics
    print("\n🔍 Checking Embedded Topics in Subjects:")
    print("-" * 40)
    
    subjects_with_topics = 0
    total_embedded_topics = 0
    
    subjects = await Subject.find().to_list()
    for s in subjects:
        units = getattr(s, 'units', [])
        for unit in units:
            topics = getattr(unit, 'topics', [])
            if topics:
                subjects_with_topics += 1
                total_embedded_topics += len(topics)
                break
    
    print(f"  Subjects with embedded topics: {subjects_with_topics}")
    print(f"  Total embedded topics: {total_embedded_topics}")
    
    # Sample search
    print("\n🔎 Testing Topic Search:")
    print("-" * 40)
    
    test_queries = ["deadlock", "normalization", "process", "thread", "sql"]
    
    from app.database.repositories.subject_repository import SubjectRepository
    repo = SubjectRepository()
    
    for query in test_queries:
        result = await repo.find_topic_by_name(query)
        if result:
            print(f"  ✅ '{query}' -> Found in {result.get('subject_name', 'Unknown')}")
        else:
            print(f"  ❌ '{query}' -> Not found")
    
    print("\n" + "=" * 60)
    print("✅ Check complete!")
    print("=" * 60)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(check_data())