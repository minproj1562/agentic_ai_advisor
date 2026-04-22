# academic-advisor-backend/scripts/seed_faculty.py
"""
One-time seed script to create all pre-approved faculty accounts.

Run once:
    cd academic-advisor-backend
    python -m scripts.seed_faculty

What it does:
    For each email in APPROVED_FACULTY_EMAILS:
    1. Creates Firebase Auth user (password = Fcrit@123)
    2. Creates Firestore 'users' document (must_change_password = True)
    3. Creates MongoDB Faculty document

    Skips any email that already exists in MongoDB.
    Skips any email that already has a Firebase Auth account.

After running:
    - All 14 faculty can log in with Fcrit@123
    - They will be prompted to change password on first login
    - /faculty/approved-emails endpoint returns all 14 emails
"""

import asyncio
import os
import sys
import logging

# ── Add project root to Python path ──────────────────────────────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# Firebase Admin
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth, firestore

# Models
from app.models.faculty import Faculty, FacultyStatus

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────

DEFAULT_PASSWORD    = "Fcrit@123"
FACULTY_EMAIL_DOMAIN = "@fcrit.ac.in"

# ── All 14 pre-approved faculty ───────────────────────────────────────────────
# Format: (email, department, designation)
FACULTY_SEED_DATA = [
    ("poonam.bari@fcrit.ac.in",        "IT",   "Assistant Professor"),
    ("shubhangi.vaikole@fcrit.ac.in",  "IT",   "HOD"),
    ("trupti.lotlikar@fcrit.ac.in",    "IT",   "Assistant Professor"),
    ("anand.pardeshi@fcrit.ac.in",     "IT",   "Assistant Professor"),
    ("dhanashree.hadsul@fcrit.ac.in",  "IT",   "Assistant Professor"),
    ("mukta.nivelkar@fcrit.ac.in",     "IT",   "Assistant Professor"),
    ("lakshmi.gadhikar@fcrit.ac.in",   "IT",   "Assistant Professor"),
    ("neelima.kulkarni@fcrit.ac.in",   "IT",   "Assistant Professor"),
    ("rupali.deshmukh@fcrit.ac.in",    "IT",   "Assistant Professor"),
    ("sharlene.rebeiro@fcrit.ac.in",   "IT",   "Assistant Professor"),
    ("supriya.joshi@fcrit.ac.in",      "IT",   "Assistant Professor"),
    ("suraj.khandare@fcrit.ac.in",     "IT",   "Assistant Professor"),
    ("vaishali.bodade@fcrit.ac.in",    "IT",   "Assistant Professor"),
    ("archana.shirke@fcrit.ac.in",     "IT",   "Assistant Professor"),
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def name_from_email(email: str) -> str:
    """
    'poonam.bari@fcrit.ac.in' → 'Poonam Bari'
    """
    local = email.split("@")[0]
    return " ".join(part.capitalize() for part in local.split("."))


def init_firebase() -> firestore.Client:
    """
    Initialize Firebase Admin SDK.
    Reads FIREBASE_CREDENTIALS_PATH from environment.
    """
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if not firebase_admin._apps:
        if cred_path:
            cred = credentials.Certificate(cred_path)
        else:
            cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized")

    return firestore.client()


async def init_mongodb():
    """
    Initialize Beanie ODM with MongoDB.
    Reads MONGODB_URL and MONGODB_DATABASE from environment.
    """
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name   = os.getenv("MONGODB_DATABASE", "academic_advisor")

    client = AsyncIOMotorClient(mongo_url)
    await init_beanie(
        database=client[db_name],
        document_models=[Faculty],
    )
    logger.info("MongoDB connected: %s / %s", mongo_url, db_name)


# ─── Core seeding logic ───────────────────────────────────────────────────────

async def seed_one_faculty(
    db_firestore: firestore.Client,
    email:        str,
    department:   str,
    designation:  str,
) -> dict:
    """
    Create one faculty account.

    Returns a result dict:
    {
        "email":   str,
        "status":  "created" | "skipped_mongo" | "skipped_firebase" | "error",
        "reason":  str,      # only present on skip/error
        "uid":     str,      # only present on success
    }
    """
    email_lower = email.lower().strip()
    name        = name_from_email(email_lower)

    logger.info("Processing: %s (%s)", email_lower, name)

    # ── Check 1: Already in MongoDB? ─────────────────────────────────────────
    existing = await Faculty.find_one(Faculty.email == email_lower)
    if existing:
        logger.warning("  SKIP — already in MongoDB (uid=%s)", existing.user_id)
        return {
            "email":  email_lower,
            "status": "skipped_mongo",
            "reason": f"MongoDB Faculty document already exists (uid={existing.user_id})",
        }

    # ── Check 2: Already in Firebase Auth? ───────────────────────────────────
    existing_uid: str | None = None
    try:
        firebase_user = firebase_auth.get_user_by_email(email_lower)
        existing_uid  = firebase_user.uid
        logger.warning(
            "  Firebase Auth user already exists (uid=%s) — "
            "will reuse UID and create Firestore + MongoDB records",
            existing_uid,
        )
    except firebase_auth.UserNotFoundError:
        pass  # Good — we will create it
    except Exception as e:
        return {
            "email":  email_lower,
            "status": "error",
            "reason": f"Firebase Auth check failed: {e}",
        }

    # ── Step 1: Create Firebase Auth user (if needed) ────────────────────────
    uid: str
    if existing_uid:
        uid = existing_uid
    else:
        try:
            user_record = firebase_auth.create_user(
                email=email_lower,
                password=DEFAULT_PASSWORD,
                display_name=name,
                email_verified=False,
            )
            uid = user_record.uid
            logger.info("  Firebase Auth user created: uid=%s", uid)
        except Exception as e:
            return {
                "email":  email_lower,
                "status": "error",
                "reason": f"Firebase Auth create_user failed: {e}",
            }

    # ── Step 2: Create Firestore 'users' document ─────────────────────────────
    try:
        now_iso = datetime.utcnow().isoformat()
        db_firestore.collection("users").document(uid).set(
            {
                "uid":         uid,
                "email":       email_lower,
                "displayName": name,
                "role":        "faculty",
                "emailVerified": False,

                # ✅ Faculty must change password on first login
                "must_change_password":  True,
                "default_password_hint": DEFAULT_PASSWORD,

                "metadata": {
                    "createdAt":    now_iso,
                    "lastLoginAt":  None,
                    "lastActiveAt": None,
                    "loginCount":   0,
                    "createdBy":    "seed_script",
                },
                "preferences": {
                    "notifications": {
                        "email": True,
                        "push":  True,
                        "sms":   False,
                    },
                    "theme":    "system",
                    "language": "en",
                },
            },
            merge=False,  # overwrite if exists
        )
        logger.info("  Firestore 'users' document created")
    except Exception as e:
        # Rollback Firebase Auth user if we just created it
        if not existing_uid:
            try:
                firebase_auth.delete_user(uid)
                logger.warning(
                    "  Rolled back Firebase Auth user uid=%s", uid
                )
            except Exception:
                pass
        return {
            "email":  email_lower,
            "status": "error",
            "reason": f"Firestore document creation failed: {e}",
        }

    # ── Step 3: Create MongoDB Faculty document ───────────────────────────────
    try:
        faculty_doc = Faculty(
            user_id=uid,
            name=name,
            email=email_lower,
            department=department,
            designation=designation,
            status=FacultyStatus.PENDING_SETUP,
            specializations=[],
            teaching_subjects=[],
            mentee_ids=[],
            max_mentees=10,
            profile_setup_complete=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await faculty_doc.insert()
        logger.info(
            "  MongoDB Faculty document created: mongo_id=%s",
            str(faculty_doc.id),
        )
    except Exception as e:
        # Rollback both
        if not existing_uid:
            try:
                firebase_auth.delete_user(uid)
            except Exception:
                pass
        try:
            db_firestore.collection("users").document(uid).delete()
        except Exception:
            pass
        return {
            "email":  email_lower,
            "status": "error",
            "reason": f"MongoDB Faculty insert failed: {e}",
        }

    logger.info("  ✅ SUCCESS: %s (uid=%s)", email_lower, uid)
    return {
        "email":  email_lower,
        "status": "created",
        "uid":    uid,
        "name":   name,
    }


async def main():
    logger.info("=" * 60)
    logger.info("Faculty Seed Script")
    logger.info("Default password: %s", DEFAULT_PASSWORD)
    logger.info("Total faculty to seed: %d", len(FACULTY_SEED_DATA))
    logger.info("=" * 60)

    # ── Initialize services ───────────────────────────────────────────────────
    db_firestore = init_firebase()
    await init_mongodb()

    # ── Seed each faculty ─────────────────────────────────────────────────────
    results = {
        "created":          [],
        "skipped_mongo":    [],
        "skipped_firebase": [],
        "errors":           [],
    }

    for email, department, designation in FACULTY_SEED_DATA:
        result = await seed_one_faculty(
            db_firestore=db_firestore,
            email=email,
            department=department,
            designation=designation,
        )

        status = result["status"]
        if status == "created":
            results["created"].append(result["email"])
        elif status == "skipped_mongo":
            results["skipped_mongo"].append(result["email"])
        elif status == "skipped_firebase":
            results["skipped_firebase"].append(result["email"])
        else:
            results["errors"].append(
                f"{result['email']}: {result.get('reason', 'unknown error')}"
            )

        # Small delay to avoid Firebase rate limiting
        await asyncio.sleep(0.5)

    # ── Summary ───────────────────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info("SEED COMPLETE")
    logger.info("=" * 60)
    logger.info(
        "✅ Created:      %d faculty", len(results["created"])
    )
    logger.info(
        "⏭  Skipped (MongoDB already had record): %d",
        len(results["skipped_mongo"]),
    )
    logger.info(
        "⏭  Skipped (Firebase exists, reused):    %d",
        len(results["skipped_firebase"]),
    )
    logger.info(
        "❌ Errors:       %d", len(results["errors"])
    )

    if results["created"]:
        logger.info("")
        logger.info("Created faculty:")
        for email in results["created"]:
            logger.info("  • %s", email)

    if results["errors"]:
        logger.info("")
        logger.info("Errors:")
        for err in results["errors"]:
            logger.info("  ✗ %s", err)

    logger.info("")
    logger.info(
        "All created faculty can now log in with password: %s",
        DEFAULT_PASSWORD,
    )
    logger.info(
        "They will be prompted to change it on first login."
    )
    logger.info("=" * 60)


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(main())