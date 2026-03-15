# check_db_sync.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def show_structure(collection, sample_size=5):
    """
    Reveal structure: field names, types, and example values.
    """
    print("\n  🔎 Structure overview:")
    cursor = collection.find().limit(sample_size)
    async for doc in cursor:
        for k, v in doc.items():
            print(f"    {k:20s} | type={type(v).__name__:10s} | example={str(v)[:60]}")
        print("    " + "-"*50)

async def full_diagnostic():
    print("=" * 60)
    print("FULL DATABASE DIAGNOSTIC")
    print("=" * 60)

    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["academic_advisor"]

    # ── SUBJECTS ──
    print("\n📚 SUBJECTS COLLECTION")
    print("-" * 40)
    count = await db["subjects"].count_documents({})
    print(f"Total: {count}")
    await show_structure(db["subjects"])

    # ── SUBJECT_UNITS ──
    print("\n📖 SUBJECT_UNITS COLLECTION")
    print("-" * 40)
    count = await db["subject_units"].count_documents({})
    print(f"Total: {count}")
    await show_structure(db["subject_units"])

    # ── TOPICS ──
    print("\n🏷️ TOPICS COLLECTION")
    print("-" * 40)
    count = await db["topics"].count_documents({})
    print(f"Total: {count}")
    await show_structure(db["topics"])

    # ── FACULTY ──
    print("\n👨‍🏫 FACULTY COLLECTION")
    print("-" * 40)
    count = await db["faculty"].count_documents({})
    print(f"Total: {count}")
    await show_structure(db["faculty"])

    # ── CAREER_PATHS ──
    print("\n💼 CAREER_PATHS COLLECTION")
    print("-" * 40)
    count = await db["career_paths"].count_documents({})
    print(f"Total: {count}")
    await show_structure(db["career_paths"])

    # ── STUDY_RESOURCES ──
    print("\n📚 STUDY_RESOURCES COLLECTION")
    print("-" * 40)
    count = await db["study_resources"].count_documents({})
    print(f"Total: {count}")
    await show_structure(db["study_resources"])

    # ── STUDENT_PROFILES ──
    print("\n🎓 STUDENT_PROFILES COLLECTION")
    print("-" * 40)
    count = await db["student_profiles"].count_documents({})
    print(f"Total: {count}")
    await show_structure(db["student_profiles"])

    # ── STUDENT_PERFORMANCE ──
    print("\n📊 STUDENT_PERFORMANCE COLLECTION")
    print("-" * 40)
    count = await db["student_performance"].count_documents({})
    print(f"Total: {count}")
    await show_structure(db["student_performance"])

    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)

    client.close()

asyncio.run(full_diagnostic())