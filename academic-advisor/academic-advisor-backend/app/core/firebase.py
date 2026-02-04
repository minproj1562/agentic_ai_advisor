# app/core/firebase.py
import firebase_admin
from firebase_admin import credentials, auth, storage
from typing import Dict, Any, Optional
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Store initialized app reference
_firebase_app: Optional[firebase_admin.App] = None
_initialized = False

def get_firebase_app():
    """Get or initialize Firebase app"""
    global _firebase_app, _initialized
    
    if _initialized and _firebase_app is not None:
        return _firebase_app
    
    # Check if already initialized by another module
    if firebase_admin._apps:
        _firebase_app = firebase_admin.get_app()
        _initialized = True
        logger.info("✅ Using existing Firebase app")
        return _firebase_app
    
    # Initialize Firebase Admin SDK
    try:
        # Import settings here to avoid circular import
        from app.core.config import settings
        
        cred_path = settings.FIREBASE_CREDENTIALS_PATH
        
        # Check for absolute path or relative path
        if not os.path.isabs(cred_path):
            # Try relative to current working directory
            if not os.path.exists(cred_path):
                # Try relative to this file's directory
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                cred_path = os.path.join(base_dir, settings.FIREBASE_CREDENTIALS_PATH)
        
        if not os.path.exists(cred_path):
            logger.error(f"❌ Firebase credentials file not found: {cred_path}")
            logger.error(f"   Current working directory: {os.getcwd()}")
            raise FileNotFoundError(f"Firebase credentials file not found: {cred_path}")
        
        logger.info(f"📁 Loading Firebase credentials from: {cred_path}")
        
        cred = credentials.Certificate(cred_path)
        
        # Get project ID from credentials for logging
        import json
        with open(cred_path) as f:
            cred_data = json.load(f)
            project_id = cred_data.get('project_id', 'unknown')
            logger.info(f"🔑 Firebase Project ID: {project_id}")
        
        init_options = {}
        if hasattr(settings, 'FIREBASE_STORAGE_BUCKET') and settings.FIREBASE_STORAGE_BUCKET:
            init_options['storageBucket'] = settings.FIREBASE_STORAGE_BUCKET
        
        _firebase_app = firebase_admin.initialize_app(cred, init_options)
        _initialized = True
        
        logger.info(f"✅ Firebase Admin SDK initialized successfully")
        logger.info(f"   Project: {project_id}")
        if init_options.get('storageBucket'):
            logger.info(f"   Storage Bucket: {init_options['storageBucket']}")
        
        return _firebase_app
        
    except Exception as e:
        logger.error(f"❌ Firebase initialization failed: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def verify_firebase_token(id_token: str) -> Dict[str, Any]:
    """
    Verify a Firebase ID token and return the decoded token.
    """
    # Validate input
    if not id_token:
        logger.error("❌ Empty token provided")
        raise ValueError("Token is empty")
    
    if not isinstance(id_token, str):
        logger.error(f"❌ Token is not a string, got: {type(id_token)}")
        raise ValueError(f"Token must be a string, got {type(id_token)}")
    
    # Check token format (should be a JWT with 3 parts)
    token_parts = id_token.split('.')
    if len(token_parts) != 3:
        logger.error(f"❌ Invalid token format. Expected 3 parts, got {len(token_parts)}")
        logger.error(f"   Token preview: {id_token[:50]}..." if len(id_token) > 50 else f"   Token: {id_token}")
        raise ValueError("Invalid token format - not a valid JWT")
    
    logger.debug(f"🔐 Verifying token (length: {len(id_token)}, parts: {len(token_parts)})")
    
    try:
        # Ensure Firebase is initialized
        get_firebase_app()
        
        # Verify the token
        decoded_token = auth.verify_id_token(id_token, check_revoked=False)
        
        uid = decoded_token.get('uid', 'unknown')
        email = decoded_token.get('email', 'unknown')
        
        logger.info(f"✅ Token verified successfully for user: {uid} ({email})")
        
        return decoded_token
        
    except auth.InvalidIdTokenError as e:
        logger.error(f"❌ Invalid ID token: {e}")
        raise Exception(f"Invalid authentication token: {str(e)}")
    except auth.ExpiredIdTokenError as e:
        logger.error(f"❌ Expired ID token: {e}")
        raise Exception(f"Authentication token expired: {str(e)}")
    except auth.RevokedIdTokenError as e:
        logger.error(f"❌ Revoked ID token: {e}")
        raise Exception(f"Authentication token has been revoked: {str(e)}")
    except auth.CertificateFetchError as e:
        logger.error(f"❌ Certificate fetch error: {e}")
        raise Exception(f"Failed to fetch Firebase certificates: {str(e)}")
    except ValueError as e:
        logger.error(f"❌ Value error during token verification: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Token verification failed: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise Exception(f"Token verification error: {type(e).__name__}: {str(e)}")


def get_storage_bucket():
    """Get Firebase Storage bucket"""
    try:
        get_firebase_app()
        bucket = storage.bucket()
        if not bucket:
            raise Exception("Storage bucket not configured")
        return bucket
    except Exception as e:
        logger.error(f"Failed to get storage bucket: {e}")
        raise


async def upload_file_to_storage(file_content: bytes, destination_path: str, content_type: str = None):
    """Upload file to Firebase Storage"""
    try:
        bucket = get_storage_bucket()
        blob = bucket.blob(destination_path)
        
        if content_type:
            blob.upload_from_string(file_content, content_type=content_type)
        else:
            blob.upload_from_string(file_content)
        
        logger.info(f"File uploaded to: {destination_path}")
        return blob
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise


def generate_signed_url(blob, expiration_hours: int = 24):
    """Generate signed URL for file access"""
    try:
        expiration = datetime.utcnow() + timedelta(hours=expiration_hours)
        url = blob.generate_signed_url(expiration=expiration, method='GET')
        return url
    except Exception as e:
        logger.error(f"Failed to generate signed URL: {e}")
        raise


async def delete_file_from_storage(file_path: str):
    """Delete file from Firebase Storage"""
    try:
        bucket = get_storage_bucket()
        blob = bucket.blob(file_path)
        blob.delete()
        logger.info(f"File deleted: {file_path}")
        return True
    except Exception as e:
        logger.error(f"File deletion failed: {e}")
        raise