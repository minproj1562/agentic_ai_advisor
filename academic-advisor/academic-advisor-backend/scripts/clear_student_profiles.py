# scripts/clear_student_profiles.py
"""
Clear all generated student profiles and related data from MongoDB.
This removes:
  - student_profiles
  - student_performance
  - recommendation_records
  - recommendation_feedback
  - training_data_points
  - student_interest_profiles
  - student_interests
  - weakness_analysis_results

Usage:
    python -m scripts.clear_student_profiles
    python -m scripts.clear_student_profiles --yes   # Skip confirmation
"""

import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

COLLECTIONS_TO_CLEAR = [
    "student_profiles",
    "student_performance",
    "recommendation_records",
    "recommendation_feedback",
    "training_data_points",
    "student_interest_profiles",
    "student_interests",
    "weakness_analysis_results",
    "student_projects",
]


async def main(skip_confirm: bool = False):
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DATABASE", "academic_advisor")

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    print("=" * 70)
    print("  CLEAR ALL STUDENT PROFILES & RELATED DATA")
    print("=" * 70)
    print(f"\n  Database: {db_name}")
    print(f"  Host:     {mongo_url[:50]}...")
    print(f"\n  Collections to clear:")

    total_docs = 0
    counts = {}
    for coll_name in COLLECTIONS_TO_CLEAR:
        count = await db[coll_name].count_documents({})
        counts[coll_name] = count
        total_docs += count
        status = f"  {count:>6,d} docs" if count > 0 else "  (empty)"
        print(f"    • {coll_name:40s} {status}")

    print(f"\n  Total documents to delete: {total_docs:,d}")

    if total_docs == 0:
        print("\n  ✅ All collections are already empty. Nothing to do.")
        client.close()
        return

    if not skip_confirm:
        print("\n  ⚠️  This action is IRREVERSIBLE.")
        confirm = input("  Type 'DELETE' to proceed: ").strip()
        if confirm != "DELETE":
            print("  ❌ Cancelled.")
            client.close()
            return

    print("\n  Deleting...")
    for coll_name in COLLECTIONS_TO_CLEAR:
        if counts[coll_name] > 0:
            result = await db[coll_name].delete_many({})
            print(f"    ✅ {coll_name}: deleted {result.deleted_count:,d} documents")
        else:
            print(f"    ⏭️  {coll_name}: already empty")

    # Verify
    print("\n  Verification:")
    for coll_name in COLLECTIONS_TO_CLEAR:
        remaining = await db[coll_name].count_documents({})
        status = "✅ empty" if remaining == 0 else f"❌ {remaining} remaining!"
        print(f"    {coll_name}: {status}")

    client.close()
    print("\n  ✅ All student data cleared successfully!")
    print("  Next steps:")
    print("    1. Generate student roster:  python -m scripts.generate_student_roster_xlsx")
    print("    2. Upload roster via admin portal")
    print("    3. Upload marks via admin portal (IT - Copy.xlsx)")


if __name__ == "__main__":
    skip = "--yes" in sys.argv or "-y" in sys.argv
    asyncio.run(main(skip_confirm=skip))
