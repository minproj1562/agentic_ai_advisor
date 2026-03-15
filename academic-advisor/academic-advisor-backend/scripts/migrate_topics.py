# scripts/migrate_topics.py
"""
Extracts embedded topics from subjects.units[].topics[] into
the standalone 'topics' collection.

Uses RAW MongoDB for reading (bypasses Beanie validation issues)
and Beanie for writing new Topic documents.

Run: python -m scripts.migrate_topics
"""

import asyncio
import logging
import re
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


async def main():
    from app.config import settings

    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]

    # Only init Beanie for Topic (writing) — skip Subject to avoid validation
    from app.models.syllabus import (
        Department, Subject, SubjectUnit, Topic,
        Abbreviation, ProgramElective, OpenElective,
        LiberalLearningCourse, MDMCourse, CreditStructure,
    )
    from app.models.faculty import Faculty
    from app.models.career import CareerPath
    from app.models.chatbot import (
        ChatSession, ChatMessage, ChatFeedback, ChatbotAnalyticsDoc,
    )
    from app.models.student_profile import StudentProfile

    await init_beanie(
        database=db,
        document_models=[
            Department, Subject, SubjectUnit, Topic,
            Abbreviation, ProgramElective, OpenElective,
            LiberalLearningCourse, MDMCourse, CreditStructure,
            Faculty, CareerPath,
            ChatSession, ChatMessage, ChatFeedback, ChatbotAnalyticsDoc,
            StudentProfile,
        ],
    )

    print("=" * 60)
    print("  TOPIC MIGRATION + DATA CHECK")
    print("=" * 60)

    # ══════════════════════════════════════════════════════
    # 1. READ SUBJECTS USING RAW MONGODB (bypasses validation)
    # ══════════════════════════════════════════════════════

    subjects_coll = db["subjects"]
    raw_subjects = await subjects_coll.find({}).to_list(length=500)
    print(f"\n📚 Found {len(raw_subjects)} subjects (raw MongoDB read)")

    # Show subject distribution
    sem_counts: dict = {}
    for s in raw_subjects:
        sem = s.get("semester", 0)
        sem_counts[sem] = sem_counts.get(sem, 0) + 1
    for sem in sorted(sem_counts.keys()):
        if sem > 0:
            # Get names
            names = [s.get("name", "?") for s in raw_subjects if s.get("semester") == sem]
            preview = ", ".join(names[:4])
            more = f" +{len(names)-4} more" if len(names) > 4 else ""
            print(f"   Sem {sem}: {sem_counts[sem]} subjects ({preview}{more})")

    # ══════════════════════════════════════════════════════
    # 2. CHECK EXISTING TOPICS
    # ══════════════════════════════════════════════════════

    topics_coll = db["topics"]
    topic_count_before = await topics_coll.count_documents({})
    print(f"\n📝 Topics collection currently has: {topic_count_before} documents")

    # ══════════════════════════════════════════════════════
    # 3. EXTRACT TOPICS FROM SUBJECTS
    # ══════════════════════════════════════════════════════

    extracted = 0
    skipped = 0
    errors = 0

    for subj in raw_subjects:
        subj_name = subj.get("name", "Unknown")
        subj_code = subj.get("code", "")
        units = subj.get("units", []) or []

        for unit in units:
            if not isinstance(unit, dict):
                continue

            unit_num = unit.get("unit_number", unit.get("unit", 0))
            unit_title = unit.get("title", unit.get("name", f"Unit {unit_num}"))
            topics_list = unit.get("topics", [])

            for topic_entry in topics_list:
                # Handle string topics: "Deadlock"
                if isinstance(topic_entry, str):
                    topic_name = topic_entry.strip()
                    topic_def = ""
                    topic_kp = []
                    topic_examples = []
                    topic_keywords_extra = []
                # Handle dict topics: {"name": "Deadlock", "definition": "..."}
                elif isinstance(topic_entry, dict):
                    topic_name = (
                        topic_entry.get("name", "") or
                        topic_entry.get("title", "") or
                        topic_entry.get("topic", "")
                    ).strip()
                    topic_def = topic_entry.get("definition", "") or ""
                    topic_kp = topic_entry.get("key_points", []) or []
                    topic_examples = topic_entry.get("examples", []) or []
                    topic_keywords_extra = topic_entry.get("keywords", []) or []
                else:
                    continue

                if not topic_name or len(topic_name) < 2:
                    continue

                # Check if already exists (using raw MongoDB)
                existing = await topics_coll.find_one({
                    "name": {"$regex": f"^{re.escape(topic_name)}$", "$options": "i"},
                    "subject_code": subj_code,
                })
                if existing:
                    skipped += 1
                    continue

                # Build keywords
                keywords = [
                    w.lower() for w in re.split(r'[\s,&/()\-]+', topic_name)
                    if len(w) > 2
                ]
                keywords.append(topic_name.lower())
                keywords.extend([k.lower() for k in topic_keywords_extra if isinstance(k, str)])
                # Remove duplicates
                keywords = list(set(keywords))

                # Insert using raw MongoDB (to avoid any Beanie validation)
                try:
                    await topics_coll.insert_one({
                        "name": topic_name,
                        "subject_name": subj_name,
                        "subject_code": subj_code,
                        "unit_number": unit_num if isinstance(unit_num, int) else None,
                        "unit_title": unit_title,
                        "definition": topic_def,
                        "explanation": "",
                        "key_points": topic_kp,
                        "examples": topic_examples,
                        "keywords": keywords,
                        "difficulty_level": "medium",
                        "exam_frequency": None,
                        "related_topics": [],
                        "prerequisites": [],
                        "video_links": [],
                        "reference_links": [],
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    })
                    extracted += 1
                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        logger.warning(f"   ⚠️ Failed to insert '{topic_name}': {e}")

    topic_count_after = await topics_coll.count_documents({})
    print(f"\n✅ Extracted {extracted} topics (skipped {skipped} duplicates, {errors} errors)")
    print(f"📝 Topics collection now has: {topic_count_after} documents")

    # Show samples
    sample = await topics_coll.find({}).limit(10).to_list(length=10)
    print(f"\n   Sample topics:")
    for t in sample:
        print(f"   → {t.get('name', '?')} [{t.get('subject_name', '?')}] (Unit: {t.get('unit_title', '?')})")

    # ══════════════════════════════════════════════════════
    # 4. CHECK FACULTY DATA
    # ══════════════════════════════════════════════════════

    print(f"\n👨‍🏫 Faculty check:")
    faculty_coll = db["faculty"]
    faculty_count = await faculty_coll.count_documents({})
    print(f"   'faculty' collection: {faculty_count} documents")

    # Show faculty with subjects
    faculty_cursor = faculty_coll.find({}).limit(15)
    faculty_list = await faculty_cursor.to_list(length=15)
    for f in faculty_list:
        ts = f.get("teaching_subjects", []) or []
        specs = f.get("specializations", []) or []
        name = f.get("name", "?")
        if ts:
            print(f"   • {name}: teaches {', '.join(ts[:3])}")
        elif specs:
            print(f"   • {name}: specialises in {', '.join(specs[:3])} (⚠️ no teaching_subjects)")
        else:
            print(f"   • {name}: ⚠️ No subjects or specializations")

    # Check if populate_all_faculty used different field names
    if faculty_count > 0:
        sample_fac = await faculty_coll.find_one({})
        fields = list(sample_fac.keys()) if sample_fac else []
        # Check for 'subjects' vs 'teaching_subjects'
        if "subjects" in fields and "teaching_subjects" not in fields:
            print(f"\n   ⚠️ Faculty uses 'subjects' field instead of 'teaching_subjects'!")
            print(f"   Fixing field names...")
            result = await faculty_coll.update_many(
                {"subjects": {"$exists": True}},
                {"$rename": {"subjects": "teaching_subjects"}}
            )
            print(f"   ✅ Renamed 'subjects' → 'teaching_subjects' in {result.modified_count} docs")
        
        if "expertise" in fields and "specializations" not in fields:
            print(f"   ⚠️ Faculty uses 'expertise' field instead of 'specializations'!")
            result = await faculty_coll.update_many(
                {"expertise": {"$exists": True}},
                {"$rename": {"expertise": "specializations"}}
            )
            print(f"   ✅ Renamed 'expertise' → 'specializations' in {result.modified_count} docs")

    # ══════════════════════════════════════════════════════
    # 5. SEARCH TESTS
    # ══════════════════════════════════════════════════════

    print(f"\n🔍 Topic search tests:")
    test_queries = ["deadlock", "normalization", "gini", "tcp", "sorting",
                    "paging", "linked list", "sql", "scheduling", "regression"]
    for q in test_queries:
        found = await topics_coll.find_one({
            "$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"keywords": {"$regex": q, "$options": "i"}},
            ]
        })
        if found:
            print(f"   ✅ '{q}' → {found.get('name', '?')} [{found.get('subject_name', '?')}]")
        else:
            print(f"   ❌ '{q}' → NOT FOUND (will use built-in fallback)")

    print(f"\n🔍 Faculty search tests:")
    test_subjects = ["Machine Learning", "Operating System", "Database", "Data Structures"]
    for subj in test_subjects:
        found = await faculty_coll.find_one({
            "$or": [
                {"teaching_subjects": {"$regex": subj, "$options": "i"}},
                {"specializations": {"$regex": subj, "$options": "i"}},
            ]
        })
        if found:
            print(f"   ✅ '{subj}' → {found.get('name', '?')}")
        else:
            print(f"   ❌ '{subj}' → NO FACULTY FOUND")

    # ══════════════════════════════════════════════════════
    # 6. CAREER CHECK
    # ══════════════════════════════════════════════════════

    career_coll = db["career_paths"]
    career_count = await career_coll.count_documents({})
    print(f"\n💼 Careers: {career_count} documents")
    if career_count > 0:
        careers = await career_coll.find({}).limit(5).to_list(length=5)
        for c in careers:
            print(f"   • {c.get('title', '?')} ({c.get('market_demand', '?')})")

    # ══════════════════════════════════════════════════════
    # 7. STUDENT PROFILES CHECK
    # ══════════════════════════════════════════════════════

    student_coll = db["student_profiles"]
    student_count = await student_coll.count_documents({})
    print(f"\n🎓 Student profiles: {student_count}")
    if student_count > 0:
        students = await student_coll.find({}).limit(3).to_list(length=3)
        for s in students:
            sems = len(s.get("semester_records", []))
            print(f"   • {s.get('name', '?')} — CGPA: {s.get('cgpa', 0)} — {sems} semester records")

    print("\n" + "=" * 60)
    print("  ✅ Migration complete!")
    print("  Next: restart backend with `uvicorn app.main:app --reload`")
    print("=" * 60 + "\n")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())