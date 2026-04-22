# academic-advisor/academic-advisor-backend/app/core/firebase_admin.py
"""
Firebase Admin SDK Integration
Handles all Firebase operations including Firestore, Auth, and Storage
"""

import asyncio
import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional, Union

import firebase_admin
from firebase_admin import auth, credentials, firestore, storage
from google.cloud.firestore_v1 import DocumentSnapshot, Query
from google.cloud.firestore_v1.base_query import FieldFilter

from app.config import settings
from app.core.exceptions import FirebaseException
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class FirebaseManager:
    """
    Enterprise Firebase Manager with all operations
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize()
            self._initialized = True
    
    def _initialize(self):
        """Initialize Firebase Admin SDK"""
        try:
            if not hasattr(settings, 'FIREBASE_CREDENTIALS_PATH') or not settings.FIREBASE_CREDENTIALS_PATH:
                logger.warning("FIREBASE_CREDENTIALS_PATH not set, using default credentials")
                cred = credentials.ApplicationDefault()
            else:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            
            firebase_config = {}
            if hasattr(settings, 'FIREBASE_STORAGE_BUCKET') and settings.FIREBASE_STORAGE_BUCKET:
                firebase_config['storageBucket'] = settings.FIREBASE_STORAGE_BUCKET
            if hasattr(settings, 'FIREBASE_DATABASE_URL') and settings.FIREBASE_DATABASE_URL:
                firebase_config['databaseURL'] = settings.FIREBASE_DATABASE_URL
            
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, firebase_config)
            
            self.db = firestore.client()
            
            if hasattr(settings, 'FIREBASE_STORAGE_BUCKET') and settings.FIREBASE_STORAGE_BUCKET:
                self.bucket = storage.bucket()
            else:
                self.bucket = None
            
            logger.info("✅ Firebase Admin SDK initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase: {str(e)}")
            raise FirebaseException(f"Firebase initialization failed: {str(e)}")
    
    # ==================== Firestore Operations ====================
    
    async def get_document(
        self,
        collection: str,
        document_id: str,
        subcollections: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a document from Firestore"""
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                
                if subcollections:
                    for subcol in subcollections:
                        subcol_data = []
                        subcol_ref = doc_ref.collection(subcol)
                        for subdoc in subcol_ref.stream():
                            subdoc_data = subdoc.to_dict()
                            subdoc_data['id'] = subdoc.id
                            subcol_data.append(subdoc_data)
                        data[subcol] = subcol_data
                
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting document {collection}/{document_id}: {str(e)}")
            raise FirebaseException(f"Failed to get document: {str(e)}")
    
    async def get_collection(
        self,
        collection: str,
        filters: List[Dict[str, Any]] = None,
        order_by: str = None,
        order_direction: str = "asc",
        limit: int = None,
        offset: int = None
    ) -> List[Dict[str, Any]]:
        """Get documents from a collection with filters"""
        try:
            query = self.db.collection(collection)
            
            if filters:
                for filter_item in filters:
                    field = filter_item.get('field')
                    operator = filter_item.get('operator', '==')
                    value = filter_item.get('value')
                    
                    if operator == '==':
                        query = query.where(field, '==', value)
                    elif operator == '!=':
                        query = query.where(field, '!=', value)
                    elif operator == '<':
                        query = query.where(field, '<', value)
                    elif operator == '<=':
                        query = query.where(field, '<=', value)
                    elif operator == '>':
                        query = query.where(field, '>', value)
                    elif operator == '>=':
                        query = query.where(field, '>=', value)
                    elif operator == 'in':
                        query = query.where(field, 'in', value)
                    elif operator == 'array-contains':
                        query = query.where(field, 'array_contains', value)
            
            if order_by:
                direction = firestore.Query.DESCENDING if order_direction == "desc" else firestore.Query.ASCENDING
                query = query.order_by(order_by, direction=direction)
            
            if offset:
                query = query.offset(offset)
            
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting collection {collection}: {str(e)}")
            raise FirebaseException(f"Failed to get collection: {str(e)}")
    
    async def create_document(
        self,
        collection: str,
        data: Dict[str, Any],
        document_id: str = None
    ) -> str:
        """Create a new document in Firestore"""
        try:
            data['created_at'] = firestore.SERVER_TIMESTAMP
            data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            if document_id:
                doc_ref = self.db.collection(collection).document(document_id)
                doc_ref.set(data)
                return document_id
            else:
                doc_ref = self.db.collection(collection).document()
                doc_ref.set(data)
                return doc_ref.id
                
        except Exception as e:
            logger.error(f"Error creating document in {collection}: {str(e)}")
            raise FirebaseException(f"Failed to create document: {str(e)}")
    
    async def update_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any],
        merge: bool = True
    ) -> bool:
        """Update a document in Firestore"""
        try:
            data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = self.db.collection(collection).document(document_id)
            
            if merge:
                doc_ref.update(data)
            else:
                doc_ref.set(data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating document {collection}/{document_id}: {str(e)}")
            raise FirebaseException(f"Failed to update document: {str(e)}")

    async def set_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any],
        merge: bool = True,
    ) -> bool:
        """
        Create or overwrite a Firestore document.

        Parameters
        ----------
        collection : str
            Firestore collection name, e.g. 'users'.
        document_id : str
            Document ID (usually Firebase Auth UID for users).
        data : dict
            Fields to write.
        merge : bool
            True  → merge with existing fields (like update_document).
            False → overwrite the entire document (used when creating
                    a brand-new faculty account).

        Returns
        -------
        bool  True on success.

        Notes
        -----
        Unlike ``create_document``, this does NOT inject
        ``created_at`` / ``updated_at`` automatically so that the
        caller has full control over the payload.
        """
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            if merge:
                doc_ref.set(data, merge=True)
            else:
                doc_ref.set(data)
            return True
        except Exception as e:
            logger.error(
                f"Error in set_document {collection}/{document_id}: {str(e)}"
            )
            raise FirebaseException(f"Failed to set document: {str(e)}")
    
    async def delete_document(
        self,
        collection: str,
        document_id: str
    ) -> bool:
        """Delete a document from Firestore"""
        try:
            self.db.collection(collection).document(document_id).delete()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {collection}/{document_id}: {str(e)}")
            raise FirebaseException(f"Failed to delete document: {str(e)}")
    
    async def batch_write(
        self,
        operations: List[Dict[str, Any]]
    ) -> bool:
        """Perform batch write operations"""
        try:
            batch = self.db.batch()
            
            for op in operations:
                operation_type = op.get('type')
                collection = op.get('collection')
                document_id = op.get('document_id')
                data = op.get('data', {})
                
                if operation_type == 'create':
                    doc_ref = self.db.collection(collection).document(document_id or self._generate_id())
                    batch.set(doc_ref, data)
                    
                elif operation_type == 'update':
                    doc_ref = self.db.collection(collection).document(document_id)
                    batch.update(doc_ref, data)
                    
                elif operation_type == 'delete':
                    doc_ref = self.db.collection(collection).document(document_id)
                    batch.delete(doc_ref)
            
            batch.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error in batch write: {str(e)}")
            raise FirebaseException(f"Batch write failed: {str(e)}")
    
    # ==================== Realtime Database Operations ====================
    
    def setup_realtime_listener(
        self,
        collection: str,
        callback: callable,
        filters: List[Dict[str, Any]] = None
    ) -> callable:
        """Setup a realtime listener for a collection"""
        try:
            query = self.db.collection(collection)
            
            if filters:
                for filter_item in filters:
                    field = filter_item.get('field')
                    operator = filter_item.get('operator', '==')
                    value = filter_item.get('value')
                    query = query.where(field, operator, value)
            
            def on_snapshot(doc_snapshot, changes, read_time):
                for change in changes:
                    data = change.document.to_dict()
                    data['id'] = change.document.id
                    data['change_type'] = change.type.name
                    asyncio.create_task(callback(data))
            
            doc_watch = query.on_snapshot(on_snapshot)
            return doc_watch
            
        except Exception as e:
            logger.error(f"Error setting up listener for {collection}: {str(e)}")
            raise FirebaseException(f"Failed to setup listener: {str(e)}")
    
    # ==================== Authentication Operations ====================
    
    async def create_user(
        self,
        email: str,
        password: str,
        display_name: str = None,
        photo_url: str = None,
        custom_claims: Dict[str, Any] = None
    ) -> str:
        """
        Create a new Firebase user.
        Returns the UID string.
        """
        try:
            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                photo_url=photo_url,
                email_verified=False
            )
            
            if custom_claims:
                auth.set_custom_user_claims(user.uid, custom_claims)
            
            return user.uid
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise FirebaseException(f"Failed to create user: {str(e)}")

    async def create_firebase_user(
        self,
        email: str,
        password: str,
        display_name: str,
    ) -> Dict[str, Any]:
        """
        Create a Firebase Auth user and return a dict.

        Unlike ``create_user`` (which returns only the UID string),
        this method returns ``{"uid": str, "email": str}`` so the
        caller can store the UID before creating downstream records.

        Raises
        ------
        ValueError
            • If a Firebase Auth account already exists for the email.
            • If the Firebase Admin SDK call fails for any reason.

        Notes
        -----
        This is a thin wrapper around ``auth.create_user`` that:
        - normalises the ``EmailAlreadyExistsError`` into a ``ValueError``
          with a human-readable message (no Firebase internals leaked).
        - keeps the rollback path in ``admin_service.py`` clean because
          the UID is always available from the returned dict.
        """
        try:
            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=False,
            )
            logger.info(
                "Firebase Auth user created via create_firebase_user: "
                "uid=%s email=%s",
                user_record.uid,
                email,
            )
            return {"uid": user_record.uid, "email": user_record.email}

        except auth.EmailAlreadyExistsError:
            raise ValueError(
                f"A Firebase Auth account already exists for {email}"
            )
        except Exception as e:
            logger.error(
                "create_firebase_user failed for %s: %s", email, e
            )
            raise ValueError(
                f"Firebase Auth create_user failed: {str(e)}"
            )

    async def delete_firebase_user(self, uid: str) -> None:
        """
        Delete a Firebase Auth user by UID.

        Used exclusively for rollbacks inside
        ``admin_service.create_faculty_account`` when a downstream
        step (Firestore or MongoDB) fails after the Auth user was
        already created.

        Unlike ``delete_user`` (which raises ``FirebaseException``),
        this method logs errors instead of raising so that a rollback
        failure never masks the original error that triggered it.
        """
        try:
            auth.delete_user(uid)
            logger.info(
                "Firebase Auth user deleted (rollback): uid=%s", uid
            )
        except Exception as e:
            logger.error(
                "delete_firebase_user rollback FAILED for uid=%s: %s",
                uid,
                e,
            )
    
    async def verify_token(
        self,
        token: str
    ) -> Dict[str, Any]:
        """Verify a Firebase ID token"""
        try:
            decoded_token = auth.verify_id_token(token)
            return decoded_token
            
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            raise FirebaseException(f"Invalid token: {str(e)}")
    
    async def get_user(
        self,
        uid: str
    ) -> Optional[Dict[str, Any]]:
        """Get user by UID"""
        try:
            user = auth.get_user(uid)
            
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'photo_url': user.photo_url,
                'email_verified': user.email_verified,
                'disabled': user.disabled,
                'custom_claims': user.custom_claims,
                'provider_data': user.provider_data,
                'creation_time': user.user_metadata.creation_timestamp,
                'last_sign_in_time': user.user_metadata.last_sign_in_timestamp,
            }
            
        except Exception as e:
            logger.error(f"Error getting user {uid}: {str(e)}")
            return None
    
    async def update_user(
        self,
        uid: str,
        **kwargs
    ) -> bool:
        """Update user properties"""
        try:
            auth.update_user(uid, **kwargs)
            return True
            
        except Exception as e:
            logger.error(f"Error updating user {uid}: {str(e)}")
            raise FirebaseException(f"Failed to update user: {str(e)}")
    
    async def delete_user(
        self,
        uid: str
    ) -> bool:
        """
        Delete a Firebase Auth user.
        Returns True on success.
        Raises FirebaseException on failure.
        """
        try:
            auth.delete_user(uid)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user {uid}: {str(e)}")
            raise FirebaseException(f"Failed to delete user: {str(e)}")
    
    # ==================== Storage Operations ====================
    
    async def upload_file(
        self,
        file_path: str,
        file_data: bytes,
        content_type: str = None,
        metadata: Dict[str, str] = None
    ) -> str:
        """Upload a file to Firebase Storage"""
        try:
            if not self.bucket:
                raise FirebaseException("Firebase Storage not configured")
                
            blob = self.bucket.blob(file_path)
            
            if metadata:
                blob.metadata = metadata
            
            blob.upload_from_string(
                file_data,
                content_type=content_type
            )
            
            blob.make_public()
            
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {str(e)}")
            raise FirebaseException(f"Failed to upload file: {str(e)}")
    
    async def download_file(
        self,
        file_path: str
    ) -> bytes:
        """Download a file from Firebase Storage"""
        try:
            if not self.bucket:
                raise FirebaseException("Firebase Storage not configured")
                
            blob = self.bucket.blob(file_path)
            return blob.download_as_bytes()
            
        except Exception as e:
            logger.error(f"Error downloading file {file_path}: {str(e)}")
            raise FirebaseException(f"Failed to download file: {str(e)}")
    
    async def delete_file(
        self,
        file_path: str
    ) -> bool:
        """Delete a file from Firebase Storage"""
        try:
            if not self.bucket:
                raise FirebaseException("Firebase Storage not configured")
                
            blob = self.bucket.blob(file_path)
            blob.delete()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            raise FirebaseException(f"Failed to delete file: {str(e)}")
    
    async def get_file_url(
        self,
        file_path: str,
        expiration: timedelta = timedelta(hours=1)
    ) -> str:
        """Get a signed URL for a file"""
        try:
            if not self.bucket:
                raise FirebaseException("Firebase Storage not configured")
                
            blob = self.bucket.blob(file_path)
            url = blob.generate_signed_url(
                expiration=datetime.utcnow() + expiration,
                method='GET'
            )
            return url
            
        except Exception as e:
            logger.error(f"Error getting file URL {file_path}: {str(e)}")
            raise FirebaseException(f"Failed to get file URL: {str(e)}")
    
    # ==================== Helper Methods ====================
    
    def _generate_id(self) -> str:
        """Generate a unique document ID"""
        return self.db.collection('_').document().id
    
    async def transaction(self, callback: callable) -> Any:
        """Perform a transaction"""
        @firestore.transactional
        def update_in_transaction(transaction):
            return callback(transaction)
        
        transaction = self.db.transaction()
        return update_in_transaction(transaction)
    
    async def get_server_timestamp(self):
        """Get server timestamp"""
        return firestore.SERVER_TIMESTAMP
    
    async def get_collection_count(
        self,
        collection: str,
        filters: List[Dict[str, Any]] = None
    ) -> int:
        """Get count of documents in a collection"""
        try:
            query = self.db.collection(collection)
            
            if filters:
                for filter_item in filters:
                    field = filter_item.get('field')
                    operator = filter_item.get('operator', '==')
                    value = filter_item.get('value')
                    query = query.where(field, operator, value)
            
            docs = query.stream()
            count = 0
            for _ in docs:
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting collection {collection}: {str(e)}")
            raise FirebaseException(f"Failed to count collection: {str(e)}")


# Global Firebase Manager instance
firebase_manager = FirebaseManager()


def initialize_firebase():
    """Initialize Firebase (called from main.py)"""
    global firebase_manager
    firebase_manager = FirebaseManager()
    return firebase_manager


async def check_firebase_health() -> Dict[str, Any]:
    """Check Firebase connectivity"""
    try:
        test_id = f"health_check_{datetime.utcnow().timestamp()}"
        
        await firebase_manager.create_document(
            '_health',
            {'test': True, 'timestamp': datetime.utcnow().isoformat()},
            test_id
        )
        
        doc = await firebase_manager.get_document('_health', test_id)
        
        await firebase_manager.delete_document('_health', test_id)
        
        storage_status = "not_configured"
        if firebase_manager.bucket:
            try:
                test_url = await firebase_manager.upload_file(
                    '_health/check.txt',
                    b'health check',
                    'text/plain'
                )
                await firebase_manager.delete_file('_health/check.txt')
                storage_status = "connected"
            except Exception as storage_error:
                storage_status = f"error: {str(storage_error)}"
        
        return {
            "status": "healthy",
            "firestore": "connected",
            "storage": storage_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }