#academic-advisor-backend/app/core/firebase.py
from firebase_admin import storage, auth, credentials
import firebase_admin
from app.core.config import settings

# Initialize Firebase if not already initialized
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {
                'storageBucket': settings.FIREBASE_STORAGE_BUCKET
            })
            print("✅ Firebase initialized successfully")
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            raise

# Get storage bucket
def get_storage_bucket():
    initialize_firebase()
    return storage.bucket()

# Verify Firebase token
def verify_firebase_token(token: str):
    initialize_firebase()
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise e

# Upload file to Firebase Storage
async def upload_file_to_storage(file_content: bytes, destination_path: str, content_type: str = None):
    bucket = get_storage_bucket()
    blob = bucket.blob(destination_path)
    
    if content_type:
        blob.upload_from_string(file_content, content_type=content_type)
    else:
        blob.upload_from_string(file_content)
    
    return blob

# Generate signed URL for file
def generate_signed_url(blob, expiration_hours: int = 1):
    from datetime import datetime, timedelta
    expiration = datetime.utcnow() + timedelta(hours=expiration_hours)
    return blob.generate_signed_url(expiration=expiration, method='GET')

# Delete file from Firebase Storage
async def delete_file_from_storage(file_path: str):
    bucket = get_storage_bucket()
    blob = bucket.blob(file_path)
    blob.delete()
    return True