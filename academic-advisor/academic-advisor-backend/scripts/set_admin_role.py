#academic-advisor/academic-advisor-backend/scripts/set_admin_role.py
"""
Script to set admin role for a Firebase user.

Usage:
    python -m scripts.set_admin_role --email admin@example.com
    python -m scripts.set_admin_role --uid FIREBASE_UID
"""

import argparse
import firebase_admin
from firebase_admin import auth, credentials
import os
import json


def init_firebase():
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)


def set_admin_role(uid: str = None, email: str = None):
    init_firebase()

    if email and not uid:
        try:
            user = auth.get_user_by_email(email)
            uid = user.uid
            print(f"Found user: {user.email} (uid: {uid})")
        except Exception as e:
            print(f"❌ User not found: {e}")
            return

    if not uid:
        print("❌ Must provide --uid or --email")
        return

    # Set custom claims
    auth.set_custom_user_claims(uid, {"role": "admin"})
    print(f"✅ Admin role set for uid: {uid}")
    print("   The user must log out and log back in for changes to take effect.")

    # Verify
    user = auth.get_user(uid)
    print(f"   Current claims: {user.custom_claims}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set admin role for a Firebase user")
    parser.add_argument("--uid", type=str, help="Firebase UID")
    parser.add_argument("--email", type=str, help="User email")
    args = parser.parse_args()

    set_admin_role(uid=args.uid, email=args.email)