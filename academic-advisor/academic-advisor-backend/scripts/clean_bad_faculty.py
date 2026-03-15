"""
Cleanup script to remove the 79 improperly configured faculty
Keeps the 8 properly configured faculty with real Firebase UIDs

Usage:
    python -m scripts.cleanup_bad_faculty
    python -m scripts.cleanup_bad_faculty --dry-run
"""

import asyncio
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.faculty import Faculty
from app.config import settings

# ==================== PROTECTED FACULTY ====================
# These are the 8 properly configured faculty with real Firebase UIDs
PROTECTED_UIDS = {
    "yZqludDZiobRnLUwN7Y8tMHK4yq1",   # Dr. Rajesh Kumar
    "aIR1Kgry9VcM2uOmEQu1doKAM7n2",   # Dr. Priya Sharma
    "LZmSBpC1oTQbMwxtFSzBEbARlnB2",   # Dr. Amit Verma
    "ta7458PS7ddcJUYJPIDUCs9VbE43",    # Dr. Sneha Patel
    "QbQTk0UA9RNSTAbdDMvBVO0aEeO2",   # Dr. Vikram Singh
    "W7LunS0pb3ZRAJM1hkR7C4bcZAu1",   # Anna Shelby
    "nmBdxmOF1TXDIAkilillz2Z63Fo2",   # Cloud Computing Services
}

PROTECTED_EMAILS = {
    "rajesh.kumar@fcrit.ac.in",
    "priya.sharma@fcrit.ac.in",
    "amit.verma@fcrit.ac.in",
    "sneha.patel@fcrit.ac.in",
    "vikram.singh@fcrit.ac.in",
    "academicadvisor642@gmail.com",
    "cloud.computing.services@fcrit.ac.in",
}


async def cleanup_bad_faculty(dry_run: bool = False):
    print("\n" + "=" * 70)
    print("🗑️  Faculty Cleanup — Remove improperly configured faculty")
    print("=" * 70)

    if dry_run:
        print("⚠️  DRY RUN MODE — No changes will be made\n")

    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.MONGODB_DATABASE],
        document_models=[Faculty]
    )
    print(f"✅ Connected to MongoDB: {settings.MONGODB_DATABASE}\n")

    # Get all faculty
    all_faculty = await Faculty.find().to_list()
    print(f"📋 Total faculty in database: {len(all_faculty)}\n")

    # Separate into keep and delete
    keep_list = []
    delete_list = []

    for fac in all_faculty:
        is_protected = (
            fac.user_id in PROTECTED_UIDS or
            fac.email in PROTECTED_EMAILS
        )
        if is_protected:
            keep_list.append(fac)
        else:
            delete_list.append(fac)

    # Show what we're keeping
    print(f"✅ KEEPING {len(keep_list)} faculty:")
    for fac in keep_list:
        print(f"   • {fac.name} ({fac.email}) — UID: {fac.user_id}")

    print(f"\n❌ DELETING {len(delete_list)} faculty:")
    for i, fac in enumerate(delete_list[:20], 1):
        print(f"   {i}. {fac.name} ({fac.email}) — UID: {fac.user_id}")
    if len(delete_list) > 20:
        print(f"   ... and {len(delete_list) - 20} more")

    if not delete_list:
        print("\n✅ Nothing to delete. Database is clean!")
        client.close()
        return

    # Confirm deletion
    if not dry_run:
        print(f"\n⚠️  About to DELETE {len(delete_list)} faculty documents.")
        confirm = input("Type 'YES' to confirm: ").strip()
        if confirm != "YES":
            print("❌ Cancelled.")
            client.close()
            return

        # Delete
        deleted_count = 0
        for fac in delete_list:
            await fac.delete()
            deleted_count += 1

        print(f"\n✅ Deleted {deleted_count} faculty documents.")

        # Verify
        remaining = await Faculty.find().to_list()
        print(f"📊 Faculty remaining in database: {len(remaining)}")
        for fac in remaining:
            print(f"   • {fac.name} ({fac.email})")
    else:
        print(f"\n📝 DRY RUN: Would delete {len(delete_list)} faculty documents.")

    client.close()
    print("\n✅ Cleanup complete!")


def main():
    parser = argparse.ArgumentParser(description="Remove improperly configured faculty")
    parser.add_argument("--dry-run", action="store_true", help="Preview without deleting")
    args = parser.parse_args()
    asyncio.run(cleanup_bad_faculty(dry_run=args.dry_run))


if __name__ == "__main__":
    main()