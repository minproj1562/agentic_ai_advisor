# scripts/link_students_to_firebase.py
"""
Link Firebase Auth users (role=student) to MongoDB StudentProfile documents.

Two modes:
  --auto    : Auto-assign seeded profiles to Firebase students
  --manual  : Interactive — pick which profile goes to which user

Usage:
    python -m scripts.link_students_to_firebase --auto
    python -m scripts.link_students_to_firebase --manual
    python -m scripts.link_students_to_firebase --dry-run
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth, firestore

from app.models.student_profile import StudentProfile
from app.models.student_performance import StudentPerformance, StudentInfo, Subject
from app.config import settings


def init_firebase():
    """Initialize Firebase Admin SDK."""
    if firebase_admin._apps:
        return firestore.client()

    cred_path = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS",
        settings.FIREBASE_CREDENTIALS_PATH
    )
    if not os.path.exists(cred_path):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cred_path = os.path.join(base, settings.FIREBASE_CREDENTIALS_PATH)

    if not os.path.exists(cred_path):
        print(f"❌ Firebase credentials not found: {cred_path}")
        sys.exit(1)

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'storageBucket': settings.FIREBASE_STORAGE_BUCKET
    })
    print(f"✅ Firebase initialized")
    return firestore.client()


def get_firebase_students(db):
    """Get all Firebase users with role=student from Firestore."""
    students = []
    try:
        users_ref = db.collection('users')
        docs = users_ref.where('role', '==', 'student').stream()
        for doc in docs:
            data = doc.to_dict()
            students.append({
                'uid': doc.id,
                'email': data.get('email', ''),
                'name': data.get('name', ''),
                'role': data.get('role', ''),
            })
    except Exception as e:
        print(f"⚠️ Firestore query failed: {e}")
        # Fallback: iterate Firebase Auth users
        print("  Falling back to Firebase Auth user list...")
        try:
            page = firebase_auth.list_users()
            while page:
                for user in page.users:
                    # Check custom claims for role
                    claims = user.custom_claims or {}
                    if claims.get('role') == 'student':
                        students.append({
                            'uid': user.uid,
                            'email': user.email or '',
                            'name': user.display_name or '',
                            'role': 'student',
                        })
                page = page.get_next_page()
        except Exception as e2:
            print(f"⚠️ Firebase Auth list failed: {e2}")

    # If no role-based students found, ask for manual input
    if not students:
        print("\n⚠️ No students found in Firebase with role='student'.")
        print("   You can manually enter Firebase UIDs.\n")
        while True:
            uid = input("Enter Firebase UID (or 'done' to stop): ").strip()
            if uid.lower() == 'done':
                break
            email = input("  Email: ").strip()
            name = input("  Name: ").strip()
            students.append({'uid': uid, 'email': email, 'name': name, 'role': 'student'})

    return students


async def link_students(mode='auto', dry_run=False):
    print("\n" + "=" * 70)
    print("🔗 Link Firebase Students → MongoDB StudentProfiles")
    print("=" * 70)

    if dry_run:
        print("⚠️  DRY RUN — No changes will be made\n")

    # Initialize
    db = init_firebase()
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.MONGODB_DATABASE],
        document_models=[StudentProfile, StudentPerformance, StudentInfo, Subject]
    )
    print(f"✅ MongoDB connected: {settings.MONGODB_DATABASE}\n")

    # Get Firebase students
    fb_students = get_firebase_students(db)
    print(f"📋 Firebase students found: {len(fb_students)}")
    for s in fb_students:
        print(f"   • {s['name']} ({s['email']}) — UID: {s['uid']}")

    # Get MongoDB profiles
    all_profiles = await StudentProfile.find().to_list()
    print(f"\n📋 MongoDB StudentProfiles: {len(all_profiles)}")

    # Separate already-linked vs unlinked
    linked = []
    unlinked = []
    fb_uids = {s['uid'] for s in fb_students}

    for p in all_profiles:
        if p.user_id in fb_uids:
            linked.append(p)
        elif p.user_id.startswith("student_"):
            unlinked.append(p)
        else:
            # Check if it's a valid Firebase UID
            try:
                firebase_auth.get_user(p.user_id)
                linked.append(p)
            except:
                unlinked.append(p)

    print(f"\n  ✅ Already linked: {len(linked)}")
    for p in linked:
        print(f"     • {p.name} (UID: {p.user_id})")
    print(f"  🔄 Available to link: {len(unlinked)}")
    for p in unlinked:
        print(f"     • {p.name} — Sem {p.current_semester}, CGPA {p.cgpa}, Branch {p.branch}")

    # Find Firebase students not yet linked
    linked_uids = {p.user_id for p in linked}
    fb_unlinked = [s for s in fb_students if s['uid'] not in linked_uids]

    if not fb_unlinked:
        print("\n✅ All Firebase students are already linked!")
        client.close()
        return

    if not unlinked:
        print("\n⚠️ No unlinked MongoDB profiles available.")
        print("   Creating new profiles for Firebase students...\n")
        for fb_s in fb_unlinked:
            await _create_profile_for_firebase_user(fb_s, dry_run)
        client.close()
        return

    print(f"\n🔗 Need to link {len(fb_unlinked)} Firebase student(s)")

    # ── AUTO MODE ──
    if mode == 'auto':
        print("\n🤖 AUTO MODE — Assigning profiles sequentially\n")
        for i, fb_s in enumerate(fb_unlinked):
            if i >= len(unlinked):
                print(f"  ⚠️ No more profiles available for {fb_s['name']}")
                print(f"     Creating new profile...")
                if not dry_run:
                    await _create_profile_for_firebase_user(fb_s, dry_run)
                continue

            profile = unlinked[i]
            old_id = profile.user_id
            old_name = profile.name

            print(f"  [{i+1}] {fb_s['name']} ({fb_s['email']})")
            print(f"      Firebase UID: {fb_s['uid']}")
            print(f"      → Assigning profile: {old_name} (Sem {profile.current_semester}, CGPA {profile.cgpa})")

            if not dry_run:
                profile.user_id = fb_s['uid']
                profile.name = fb_s['name']
                profile.email = fb_s['email']
                profile.last_updated = datetime.utcnow()
                await profile.save()

                # Update StudentPerformance
                await _update_performance_refs(old_id, fb_s['uid'], fb_s['name'])

            print(f"      ✅ {'Would link' if dry_run else 'Linked!'}")
            print()

    # ── MANUAL MODE ──
    elif mode == 'manual':
        print("\n👤 MANUAL MODE — Choose profile for each student\n")
        for fb_s in fb_unlinked:
            print(f"\n  Firebase student: {fb_s['name']} ({fb_s['email']})")
            print(f"  UID: {fb_s['uid']}")
            print(f"\n  Available profiles:")
            for j, p in enumerate(unlinked):
                print(f"    [{j+1}] {p.name} — Sem {p.current_semester}, "
                      f"CGPA {p.cgpa}, Branch {p.branch}, "
                      f"Roll {p.roll_number}")
            print(f"    [0] Create new empty profile")
            print(f"    [s] Skip this student")

            choice = input(f"\n  Choose (1-{len(unlinked)}, 0, or s): ").strip()

            if choice.lower() == 's':
                print("  ⏭️ Skipped")
                continue

            if choice == '0':
                if not dry_run:
                    await _create_profile_for_firebase_user(fb_s, dry_run)
                continue

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(unlinked):
                    profile = unlinked[idx]
                    old_id = profile.user_id

                    if not dry_run:
                        profile.user_id = fb_s['uid']
                        profile.name = fb_s['name']
                        profile.email = fb_s['email']
                        profile.last_updated = datetime.utcnow()
                        await profile.save()
                        await _update_performance_refs(old_id, fb_s['uid'], fb_s['name'])

                    print(f"  ✅ {'Would link' if dry_run else 'Linked!'} → "
                          f"Sem {profile.current_semester}, CGPA {profile.cgpa}")
                    unlinked.pop(idx)  # Remove from available
                else:
                    print("  ❌ Invalid choice")
            except ValueError:
                print("  ❌ Invalid input")

    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)

    final_profiles = await StudentProfile.find().to_list()
    linked_count = sum(1 for p in final_profiles if not p.user_id.startswith("student_"))
    print(f"  Total profiles: {len(final_profiles)}")
    print(f"  Linked to Firebase: {linked_count}")
    print(f"  Unlinked (seeded): {len(final_profiles) - linked_count}")

    client.close()
    print("\n✅ Done!")


async def _update_performance_refs(old_id: str, new_id: str, new_name: str):
    """Update StudentPerformance and StudentInfo references."""
    try:
        # Update StudentInfo
        info = await StudentInfo.find_one({"uid": old_id})
        if info:
            info.uid = new_id
            await info.save()

        # Update StudentPerformance via raw query
        from app.database.connection import get_mongo_database
        db = get_mongo_database()
        if db:
            await db["student_performance"].update_many(
                {"student_info.uid": old_id},
                {"$set": {"student_info.uid": new_id, "updated_at": datetime.utcnow()}}
            )
    except Exception as e:
        print(f"    ⚠️ Performance ref update: {e}")


async def _create_profile_for_firebase_user(fb_user: dict, dry_run: bool):
    """Create a basic StudentProfile for a Firebase user."""
    if dry_run:
        print(f"  📝 Would create profile for {fb_user['name']}")
        return

    profile = StudentProfile(
        user_id=fb_user['uid'],
        name=fb_user['name'],
        email=fb_user['email'],
        branch="IT",
        admission_year=2022,
        current_semester=6,
        current_academic_year="2024-2025",
        cgpa=0.0,
        total_credits_earned=0,
        total_credits_required=160,
        semester_records=[],
        skills=[],
        interests=[],
        career_goals=[],
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow(),
    )
    await profile.insert()
    print(f"  ✅ Created empty profile for {fb_user['name']}")
    print(f"     → Student can add academic data via dashboard")


def main():
    parser = argparse.ArgumentParser(
        description="Link Firebase students to MongoDB StudentProfiles"
    )
    parser.add_argument("--auto", action="store_true",
                        help="Auto-assign profiles sequentially")
    parser.add_argument("--manual", action="store_true",
                        help="Interactive manual assignment")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without changes")
    args = parser.parse_args()

    mode = 'manual' if args.manual else 'auto'
    asyncio.run(link_students(mode=mode, dry_run=args.dry_run))


if __name__ == "__main__":
    main()