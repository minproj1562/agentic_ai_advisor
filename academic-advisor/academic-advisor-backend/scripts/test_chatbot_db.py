"""
Diagnostic script — shows exactly what's in MongoDB collections
that the chatbot depends on.

Run:  python -m scripts.diagnose_chatbot_db
"""

import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient

# Adjust these to match your .env
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "academic_advisor"


async def main():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    print("=" * 70)
    print(f"  DATABASE: {DATABASE_NAME}")
    print("=" * 70)

    # 1) List all collections with counts
    collections = await db.list_collection_names()
    collections.sort()
    print(f"\n📦 {len(collections)} collections found:\n")
    for name in collections:
        count = await db[name].count_documents({})
        marker = "  "
        if name in ("subjects", "topics", "subject_units", "faculty",
                     "faculty_members", "departments", "career_paths",
                     "chat_sessions", "student_profiles"):
            marker = "⭐"
        print(f"  {marker} {name:40s} → {count:>6d} docs")

    # 2) Check key collections in detail
    KEY_COLLECTIONS = [
        "subjects",
        "topics",
        "subject_units",
        "faculty",
        "faculty_members",
        "departments",
        "career_paths",
        "student_profiles",
    ]

    for col_name in KEY_COLLECTIONS:
        if col_name not in collections:
            print(f"\n{'─'*70}")
            print(f"❌ Collection '{col_name}' — DOES NOT EXIST")
            continue

        col = db[col_name]
        count = await col.count_documents({})
        print(f"\n{'─'*70}")
        print(f"📋 Collection: {col_name}  ({count} documents)")
        print(f"{'─'*70}")

        if count == 0:
            print("   ⚠️  EMPTY — chatbot cannot query this!")
            continue

        # Show field names from first 3 docs
        sample = await col.find().limit(3).to_list(length=3)
        all_fields = set()
        for doc in sample:
            all_fields.update(doc.keys())

        print(f"\n   Fields present: {sorted(all_fields)}")

        # Show sample documents (truncated)
        for i, doc in enumerate(sample):
            print(f"\n   --- Sample {i+1} ---")
            for key, val in doc.items():
                if key == "_id":
                    print(f"      _id: {val}")
                    continue
                val_str = str(val)
                if len(val_str) > 120:
                    val_str = val_str[:120] + "..."
                print(f"      {key}: {val_str}")

        # Collection-specific checks
        if col_name == "subjects":
            # Check semester distribution
            pipeline = [
                {"$group": {"_id": "$semester", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
            sem_dist = await col.aggregate(pipeline).to_list(length=20)
            print(f"\n   📊 Semester distribution:")
            for s in sem_dist:
                sem_val = s["_id"]
                print(f"      semester={sem_val!r} ({type(sem_val).__name__}) → {s['count']} subjects")

            # Check field names for credits, semester
            doc1 = sample[0] if sample else {}
            for check_field in ["semester", "credits", "code", "name", "department",
                                "subject_type", "units", "description"]:
                present = check_field in doc1
                val = doc1.get(check_field, "—")
                print(f"      Field '{check_field}': {'✅' if present else '❌'} {type(val).__name__}={str(val)[:60]}")

        elif col_name in ("faculty", "faculty_members"):
            doc1 = sample[0] if sample else {}
            # Check all possible subject field names
            for check_field in ["teaching_subjects", "subjects_taught", "subjects",
                                "specializations", "department", "designation",
                                "name", "email", "research_areas"]:
                present = check_field in doc1
                val = doc1.get(check_field, "—")
                print(f"      Field '{check_field}': {'✅' if present else '❌'} {type(val).__name__}={str(val)[:80]}")

        elif col_name == "topics":
            doc1 = sample[0] if sample else {}
            for check_field in ["name", "topic_name", "subject_name", "subject_code",
                                "subject", "unit_number", "unit_title", "unit",
                                "definition", "key_points", "keywords"]:
                present = check_field in doc1
                val = doc1.get(check_field, "—")
                print(f"      Field '{check_field}': {'✅' if present else '❌'} {type(val).__name__}={str(val)[:80]}")

        elif col_name == "subject_units":
            doc1 = sample[0] if sample else {}
            for check_field in ["subject_code", "subject", "unit_number", "title",
                                "unit_title", "topics", "description"]:
                present = check_field in doc1
                val = doc1.get(check_field, "—")
                print(f"      Field '{check_field}': {'✅' if present else '❌'} {type(val).__name__}={str(val)[:80]}")

    # 3) Quick faculty subject search test
    print(f"\n{'='*70}")
    print("🧪 FACULTY SEARCH TEST")
    print(f"{'='*70}")

    for col_name in ["faculty", "faculty_members"]:
        if col_name not in collections:
            print(f"   {col_name}: collection not found")
            continue

        col = db[col_name]
        count = await col.count_documents({})
        if count == 0:
            print(f"   {col_name}: EMPTY")
            continue

        # Try searching for "Operating" in all possible fields
        for field in ["teaching_subjects", "subjects_taught", "subjects",
                      "specializations", "research_areas"]:
            results = await col.find(
                {field: {"$regex": "Operating|Machine|Data", "$options": "i"}}
            ).limit(3).to_list(length=3)
            if results:
                print(f"   ✅ {col_name}.{field} → {len(results)} results")
                for r in results[:2]:
                    print(f"      → {r.get('name', '?')} | {field}={r.get(field, '?')}")
            else:
                print(f"   ❌ {col_name}.{field} → 0 results")

    # 4) Quick subject semester search test
    print(f"\n{'='*70}")
    print("🧪 SEMESTER SUBJECT SEARCH TEST")
    print(f"{'='*70}")

    col = db["subjects"]
    for sem_val in [1, 2, 3, 4, "1", "2", "3", "4"]:
        results = await col.find({"semester": sem_val}).to_list(length=5)
        if results:
            print(f"   ✅ semester={sem_val!r} → {len(results)} subjects: {[r.get('name','?') for r in results[:3]]}")
        else:
            print(f"   ❌ semester={sem_val!r} → 0 results")

    # 5) Check if there's a different collection for subjects
    print(f"\n{'='*70}")
    print("🧪 ALTERNATIVE COLLECTION SEARCH")
    print(f"{'='*70}")

    for alt_name in ["courses", "syllabus", "curriculum", "subject_details"]:
        if alt_name in collections:
            count = await db[alt_name].count_documents({})
            print(f"   ⭐ Found '{alt_name}' with {count} docs!")
            sample = await db[alt_name].find().limit(1).to_list(length=1)
            if sample:
                print(f"      Fields: {sorted(sample[0].keys())}")

    print(f"\n{'='*70}")
    print("✅ DIAGNOSIS COMPLETE")
    print(f"{'='*70}")
    print("\nCopy the output above and share it to get targeted fixes.")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())