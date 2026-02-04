import os
import firebase_admin
from firebase_admin import auth, credentials

# Get the absolute path to serviceAccountKey.json
# Adjust the path based on where your file is located
key_path = os.path.join(os.path.dirname(__file__), "..", "..", "serviceAccountKey.json")

# Initialize
cred = credentials.Certificate(key_path)
firebase_admin.initialize_app(cred)

# Set faculty role
uid = "W7LunS0pb3ZRAJM1hkR7C4bcZAu1"  # Your UID
auth.set_custom_user_claims(uid, {"role": "faculty"})
print(f"✅ User {uid} is now faculty")