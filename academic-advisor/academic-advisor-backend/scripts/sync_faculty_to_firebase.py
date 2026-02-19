# academic-advisor/academic-advisor-backend/app/scripts/sync_faculty_to_firebase.py
"""
Faculty MongoDB ↔ Firebase Sync Script
=======================================
Reads faculty from MongoDB, creates real Firebase Auth + Firestore accounts,
and updates all MongoDB references to use real Firebase UIDs.

Usage:
  python scripts/sync_faculty_to_firebase.py
  python scripts/sync_faculty_to_firebase.py --dry-run
  python scripts/sync_faculty_to_firebase.py --default-password "FacultyPass@2024"
  python scripts/sync_faculty_to_firebase.py --skip-existing
"""

import asyncio
import argparse
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth, firestore

from app.config import settings
from app.models.faculty import Faculty, FacultyStatus
from app.models.meeting_request import MeetingRequest
from app.models.student_profile import StudentProfile
from app.models.student_performance import StudentPerformance
from app.models.messages import Message, Conversation


# ==================== Configuration ====================

DEFAULT_PASSWORD = "Faculty@FCRIT2024"  # Faculty will be asked to change on first login

# All document models needed for Beanie init
DOCUMENT_MODELS = [
    Faculty,
    MeetingRequest,
    StudentProfile,
    StudentPerformance,
    Message,
    Conversation,
]


# ==================== Firebase Helpers ====================

def init_firebase():
    """Initialize Firebase Admin SDK"""
    if firebase_admin._apps:
        return firestore.client()
    
    cred_path = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS",
        settings.FIREBASE_CREDENTIALS_PATH
    )
    
    if not os.path.exists(cred_path):
        # Try relative to project root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cred_path = os.path.join(base_dir, settings.FIREBASE_CREDENTIALS_PATH)
    
    if not os.path.exists(cred_path):
        print(f"❌ Firebase credentials not found at: {cred_path}")
        sys.exit(1)
    
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'storageBucket': settings.FIREBASE_STORAGE_BUCKET
    })
    
    print(f"✅ Firebase initialized from: {cred_path}")
    return firestore.client()


def get_or_create_firebase_user(
    email: str,
    password: str,
    display_name: str,
    dry_run: bool = False
) -> Tuple[Optional[str], str]:
    """
    Get existing Firebase Auth user by email, or create a new one.
    Returns (uid, status) where status is 'existing', 'created', or 'error'
    """
    try:
        # Check if user already exists
        existing_user = firebase_auth.get_user_by_email(email)
        return existing_user.uid, "existing"
    except firebase_auth.UserNotFoundError:
        pass
    except Exception as e:
        print(f"    ⚠️  Error checking user {email}: {e}")
        return None, f"error: {e}"
    
    if dry_run:
        return f"dry_run_uid_{email}", "would_create"
    
    try:
        new_user = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            email_verified=False
        )
        
        # Set custom claims for role
        firebase_auth.set_custom_user_claims(new_user.uid, {
            'role': 'faculty'
        })
        
        return new_user.uid, "created"
    except Exception as e:
        print(f"    ❌ Error creating user {email}: {e}")
        return None, f"error: {e}"


def create_firestore_user_doc(
    db,
    uid: str,
    faculty: Faculty,
    dry_run: bool = False
):
    """
    Create or update the Firestore users/{uid} document.
    This is what AuthContext reads on login.
    """
    user_data = {
        'uid': uid,
        'email': faculty.email,
        'name': faculty.name,
        'role': 'faculty',
        'department': faculty.department,
        'designation': faculty.designation,
        'profileComplete': faculty.profile_setup_complete,
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow(),
    }
    
    if dry_run:
        return
    
    try:
        doc_ref = db.collection('users').document(uid)
        existing = doc_ref.get()
        
        if existing.exists:
            # Update only missing fields, don't overwrite
            existing_data = existing.to_dict()
            updates = {}
            for key, value in user_data.items():
                if key not in existing_data or existing_data[key] is None:
                    updates[key] = value
            
            # Always ensure role is faculty
            updates['role'] = 'faculty'
            updates['updatedAt'] = datetime.utcnow()
            
            if updates:
                doc_ref.update(updates)
        else:
            doc_ref.set(user_data)
    except Exception as e:
        print(f"    ⚠️  Firestore doc error for {uid}: {e}")


# ==================== MongoDB Update Helpers ====================

async def update_mongodb_references(
    old_id: str,
    new_id: str,
    faculty_name: str,
    dry_run: bool = False
):
    """
    Update all MongoDB documents that reference the old faculty user_id
    """
    changes = []
    
    if old_id == new_id:
        return changes
    
    # 1. Update MeetingRequests where faculty_id matches
    meeting_requests = await MeetingRequest.find(
        MeetingRequest.faculty_id == old_id
    ).to_list()
    
    if meeting_requests:
        changes.append(f"MeetingRequests (faculty_id): {len(meeting_requests)}")
        if not dry_run:
            for req in meeting_requests:
                req.faculty_id = new_id
                await req.save()
    
    # 2. Update MeetingRequests where student sent to this faculty
    # (faculty_id field - already covered above)
    
    # 3. Update Conversations where faculty is a participant
    conversations = await Conversation.find({
        "$or": [
            {"participant1_id": old_id},
            {"participant2_id": old_id}
        ]
    }).to_list()
    
    if conversations:
        changes.append(f"Conversations: {len(conversations)}")
        if not dry_run:
            for conv in conversations:
                if conv.participant1_id == old_id:
                    conv.participant1_id = new_id
                if conv.participant2_id == old_id:
                    conv.participant2_id = new_id
                await conv.save()
    
    # 4. Update Messages where faculty is sender/receiver
    messages = await Message.find({
        "$or": [
            {"sender_id": old_id},
            {"receiver_id": old_id}
        ]
    }).to_list()
    
    if messages:
        changes.append(f"Messages: {len(messages)}")
        if not dry_run:
            for msg in messages:
                if msg.sender_id == old_id:
                    msg.sender_id = new_id
                if msg.receiver_id == old_id:
                    msg.receiver_id = new_id
                await msg.save()
    
    # 5. Update StudentProfile mentee references
    # Faculty has mentee_ids list - students might reference faculty too
    # The faculty.mentee_ids contains student IDs, not faculty IDs
    # But if any StudentProfile has a field referencing faculty_id, update it
    
    return changes


# ==================== Main Sync Logic ====================

async def sync_faculty_to_firebase(
    default_password: str = DEFAULT_PASSWORD,
    dry_run: bool = False,
    skip_existing: bool = False,
    specific_email: Optional[str] = None
):
    """
    Main sync function
    """
    print("\n" + "=" * 70)
    print("🔄 Faculty MongoDB → Firebase Sync")
    print("=" * 70)
    
    if dry_run:
        print("⚠️  DRY RUN MODE - No changes will be made\n")
    
    # Initialize Firebase
    db = init_firebase()
    
    # Initialize MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.MONGODB_DATABASE],
        document_models=DOCUMENT_MODELS
    )
    print(f"✅ MongoDB connected: {settings.MONGODB_DATABASE}\n")
    
    # Get all faculty
    query = {}
    if specific_email:
        query = {"email": specific_email}
    
    faculty_list = await Faculty.find(query).to_list()
    print(f"📋 Found {len(faculty_list)} faculty in MongoDB\n")
    
    if not faculty_list:
        print("No faculty to sync. Run seed_data.py first.")
        return
    
    # Track results
    results = {
        "synced": [],
        "already_synced": [],
        "created": [],
        "skipped": [],
        "errors": [],
        "references_updated": []
    }
    
    for i, faculty in enumerate(faculty_list, 1):
        old_id = faculty.user_id
        email = faculty.email
        name = faculty.name
        
        print(f"[{i}/{len(faculty_list)}] {name}")
        print(f"    Email: {email}")
        print(f"    Current user_id: {old_id}")
        
        # Check if already a real Firebase UID (not synthetic)
        is_synthetic = old_id.startswith("faculty_") and len(old_id) < 20
        
        if not is_synthetic:
            # Might already be a real Firebase UID
            try:
                firebase_auth.get_user(old_id)
                print(f"    ✅ Already synced (real Firebase UID)")
                results["already_synced"].append({
                    "name": name,
                    "email": email,
                    "uid": old_id
                })
                
                if skip_existing:
                    continue
                
                # Still ensure Firestore doc exists
                create_firestore_user_doc(db, old_id, faculty, dry_run)
                continue
            except firebase_auth.UserNotFoundError:
                # UID looks real but doesn't exist - treat as needing sync
                pass
            except Exception:
                pass
        
        # Step 1: Get or create Firebase Auth user
        new_uid, status = get_or_create_firebase_user(
            email=email,
            password=default_password,
            display_name=name,
            dry_run=dry_run
        )
        
        if not new_uid:
            print(f"    ❌ Failed: {status}")
            results["errors"].append({
                "name": name,
                "email": email,
                "error": status
            })
            continue
        
        print(f"    Firebase Auth: {status} → UID: {new_uid}")
        
        # Step 2: Create Firestore user document
        create_firestore_user_doc(db, new_uid, faculty, dry_run)
        print(f"    Firestore doc: {'would create' if dry_run else 'created/updated'}")
        
        # Step 3: Update MongoDB references
        if old_id != new_uid:
            ref_changes = await update_mongodb_references(
                old_id, new_uid, name, dry_run
            )
            
            if ref_changes:
                print(f"    References updated: {', '.join(ref_changes)}")
                results["references_updated"].append({
                    "name": name,
                    "old_id": old_id,
                    "new_id": new_uid,
                    "changes": ref_changes
                })
            
            # Step 4: Update Faculty document itself
            if not dry_run:
                faculty.user_id = new_uid
                faculty.updated_at = datetime.utcnow()
                await faculty.save()
            
            print(f"    MongoDB user_id: {old_id} → {new_uid}")
        
        if status == "created" or status == "would_create":
            results["created"].append({
                "name": name,
                "email": email,
                "uid": new_uid,
                "old_id": old_id,
                "password": default_password
            })
        else:
            results["synced"].append({
                "name": name,
                "email": email,
                "uid": new_uid,
                "old_id": old_id
            })
        
        print()
    
    # ==================== Summary ====================
    print("\n" + "=" * 70)
    print("📊 SYNC SUMMARY")
    print("=" * 70)
    
    print(f"\n✅ Newly created in Firebase:  {len(results['created'])}")
    for r in results["created"]:
        print(f"   {r['name']} ({r['email']}) → {r['uid']}")
    
    print(f"\n🔗 Already existed (re-linked): {len(results['synced'])}")
    for r in results["synced"]:
        print(f"   {r['name']} ({r['email']}) → {r['uid']}")
    
    print(f"\n⏭️  Already synced (skipped):    {len(results['already_synced'])}")
    
    print(f"\n🔄 References updated:          {len(results['references_updated'])}")
    for r in results["references_updated"]:
        print(f"   {r['name']}: {r['old_id']} → {r['new_id']}")
        for change in r["changes"]:
            print(f"      - {change}")
    
    if results["errors"]:
        print(f"\n❌ Errors: {len(results['errors'])}")
        for r in results["errors"]:
            print(f"   {r['name']} ({r['email']}): {r['error']}")
    
    # Login credentials
    if results["created"]:
        print("\n" + "=" * 70)
        print("🔑 LOGIN CREDENTIALS (newly created accounts)")
        print("=" * 70)
        print(f"Default password: {default_password}")
        print("⚠️  Faculty should change password on first login!\n")
        
        for r in results["created"]:
            print(f"  Email:    {r['email']}")
            print(f"  Password: {default_password}")
            print(f"  UID:      {r['uid']}")
            print()
    
    # Save results to file
    results_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"sync_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    )
    
    serializable_results = json.loads(json.dumps(results, default=str))
    with open(results_file, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    client.close()
    print("\n✅ Sync complete!")


# ==================== CLI ====================

def main():
    parser = argparse.ArgumentParser(
        description="Sync faculty from MongoDB to Firebase Auth + Firestore"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without making them"
    )
    parser.add_argument(
        "--default-password",
        type=str,
        default=DEFAULT_PASSWORD,
        help=f"Default password for new accounts (default: {DEFAULT_PASSWORD})"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip faculty that already have valid Firebase UIDs"
    )
    parser.add_argument(
        "--email",
        type=str,
        default=None,
        help="Sync only a specific faculty by email"
    )
    
    args = parser.parse_args()
    
    asyncio.run(sync_faculty_to_firebase(
        default_password=args.default_password,
        dry_run=args.dry_run,
        skip_existing=args.skip_existing,
        specific_email=args.email
    ))


if __name__ == "__main__":
    main()