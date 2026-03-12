# scripts/verify_syllabus_db.py
"""
Verify syllabus data is loaded in MongoDB and test repository queries
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie


async def main():
    print("=" * 70)
    print("🔍 VERIFYING MONGODB SYLLABUS DATA")
    print("=" * 70)
    
    # Connect to MongoDB
    from app.config import settings
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    # Import models
    from app.models.syllabus import (
        Department, Subject, SubjectUnit, Topic,
        Abbreviation, ProgramElective, OpenElective,
        MDMCourse, LiberalLearningCourse, CreditStructure
    )
    
    await init_beanie(
        database=db,
        document_models=[
            Department, Subject, SubjectUnit, Topic,
            Abbreviation, ProgramElective, OpenElective,
            MDMCourse, LiberalLearningCourse, CreditStructure
        ]
    )
    
    # ────────────────────────────────────────────────────────
    # 1. Check Collection Counts
    # ────────────────────────────────────────────────────────
    print("\n📊 COLLECTION COUNTS:")
    print("-" * 50)
    
    counts = {
        "Departments": await Department.find().count(),
        "Subjects": await Subject.find().count(),
        "Subject Units": await SubjectUnit.find().count(),
        "Topics": await Topic.find().count(),
        "Abbreviations": await Abbreviation.find().count(),
        "Program Electives": await ProgramElective.find().count(),
        "Open Electives": await OpenElective.find().count(),
        "MDM Courses": await MDMCourse.find().count(),
        "Liberal Learning": await LiberalLearningCourse.find().count(),
    }
    
    for name, count in counts.items():
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {name}: {count}")
    
    # ────────────────────────────────────────────────────────
    # 2. List Subjects
    # ────────────────────────────────────────────────────────
    print("\n📚 SUBJECTS IN DATABASE:")
    print("-" * 50)
    
    subjects = await Subject.find().sort("+semester", "+code").to_list()
    
    if not subjects:
        print("  ❌ No subjects found! Run: python populate_syllabus.py")
    else:
        by_semester = {}
        for s in subjects:
            sem = getattr(s, 'semester', 0)
            if sem not in by_semester:
                by_semester[sem] = []
            by_semester[sem].append(s)
        
        for sem in sorted(by_semester.keys()):
            print(f"\n  Semester {sem}:")
            for s in by_semester[sem]:
                print(f"    [{s.code}] {s.name} ({s.credits} credits)")
    
    # ────────────────────────────────────────────────────────
    # 3. Check Subject Units (Modules)
    # ────────────────────────────────────────────────────────
    print("\n📖 SUBJECT UNITS (Sample):")
    print("-" * 50)
    
    units = await SubjectUnit.find().limit(10).to_list()
    
    if not units:
        print("  ❌ No subject units found!")
    else:
        for unit in units[:5]:
            # Try to get subject info
            subject_name = "Unknown"
            try:
                if hasattr(unit, 'subject') and unit.subject:
                    subject = await unit.subject.fetch()
                    if subject:
                        subject_name = f"[{subject.code}]"
            except:
                pass
            
            print(f"  • {subject_name} Unit {getattr(unit, 'unit_number', '?')}: {unit.title}")
    
    # ────────────────────────────────────────────────────────
    # 4. Check Topics
    # ────────────────────────────────────────────────────────
    print("\n📝 TOPICS IN DATABASE:")
    print("-" * 50)
    
    topics = await Topic.find().limit(20).to_list()
    
    if not topics:
        print("  ⚠️ No standalone topics found (might be embedded in units)")
    else:
        for t in topics[:10]:
            print(f"  • {t.name}")
            if hasattr(t, 'definition') and t.definition:
                print(f"    Definition: {t.definition[:80]}...")
    
    # ────────────────────────────────────────────────────────
    # 5. Test SubjectRepository
    # ────────────────────────────────────────────────────────
    print("\n🔎 TESTING SUBJECT REPOSITORY:")
    print("-" * 50)
    
    try:
        from app.database.repositories.subject_repository import SubjectRepository
        repo = SubjectRepository()
        
        # Test text search
        print("\n  Testing text_search('operating'):")
        results = await repo.text_search("operating", limit=3)
        if results:
            for r in results:
                print(f"    ✅ Found: [{r.get('code')}] {r.get('name')}")
        else:
            print("    ❌ No results")
        
        # Test find_topic_by_name
        test_topics = ["deadlock", "normalization", "process", "thread", "sql", "mutex"]
        print("\n  Testing find_topic_by_name():")
        
        for topic_name in test_topics:
            result = await repo.find_topic_by_name(topic_name)
            if result:
                topic = result.get('topic', {})
                subject = result.get('subject_name', 'Unknown')
                definition = topic.get('definition', '')[:60] + "..." if topic.get('definition') else "No definition"
                print(f"    ✅ '{topic_name}' -> {subject}")
                print(f"       {definition}")
            else:
                print(f"    ❌ '{topic_name}' -> Not found")
        
        # Test get_by_code
        print("\n  Testing get_by_code():")
        if subjects:
            test_code = subjects[0].code
            result = await repo.get_by_code(test_code)
            if result:
                print(f"    ✅ Found: [{result.get('code')}] {result.get('name')}")
                units = result.get('units', [])
                print(f"       Units: {len(units)}")
            else:
                print(f"    ❌ Subject {test_code} not found via repository")
        
    except Exception as e:
        print(f"  ❌ Repository test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # ────────────────────────────────────────────────────────
    # 6. Raw MongoDB Check
    # ────────────────────────────────────────────────────────
    print("\n🗄️ RAW MONGODB COLLECTIONS:")
    print("-" * 50)
    
    collections = await db.list_collection_names()
    for coll in sorted(collections):
        count = await db[coll].count_documents({})
        print(f"  • {coll}: {count} documents")
    
    # ────────────────────────────────────────────────────────
    # Summary
    # ────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    
    total_subjects = counts["Subjects"]
    total_units = counts["Subject Units"]
    
    if total_subjects > 0:
        print("✅ DATABASE HAS SYLLABUS DATA!")
        print(f"   {total_subjects} subjects, {total_units} units loaded")
        print("\n   Your chatbot WILL fetch from MongoDB.")
    else:
        print("❌ DATABASE IS EMPTY!")
        print("\n   Run this to populate:")
        print("   python populate_syllabus.py")
    
    print("=" * 70)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(main())