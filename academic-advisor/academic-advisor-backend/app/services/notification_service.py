# app/services/notification_service.py
"""
Notification Service - Handles all notification operations
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import uuid

from app.core.firebase_admin import firebase_manager

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications"""
    
    async def send_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        channels: Optional[List[str]] = None
    ) -> str:
        """Send a notification to a user"""
        try:
            notification_id = str(uuid.uuid4())
            
            notification_data = {
                'id': notification_id,
                'user_id': user_id,
                'type': notification_type,
                'title': title,
                'message': message,
                'data': data or {},
                'read': False,
                'created_at': datetime.utcnow().isoformat(),
            }
            
            # Store in database
            await firebase_manager.create_document(
                collection=f"users/{user_id}/notifications",
                data=notification_data,
                document_id=notification_id
            )
            
            logger.info(f"Notification sent to {user_id}: {title}")
            return notification_id
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            raise
    
    async def send_bulk_notifications(
        self,
        user_ids: List[str],
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Send notifications to multiple users"""
        notification_ids = []
        
        for user_id in user_ids:
            try:
                notif_id = await self.send_notification(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    data=data
                )
                notification_ids.append(notif_id)
            except Exception as e:
                logger.error(f"Failed to notify {user_id}: {e}")
        
        return notification_ids
    
    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        try:
            filters = []
            if unread_only:
                filters.append({'field': 'read', 'operator': '==', 'value': False})
            
            notifications = await firebase_manager.get_collection(
                collection=f"users/{user_id}/notifications",
                filters=filters,
                order_by='created_at',
                order_direction='desc',
                limit=limit
            )
            
            return notifications
            
        except Exception as e:
            logger.error(f"Failed to get notifications: {e}")
            return []
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        try:
            await firebase_manager.update_document(
                collection=f"users/{user_id}/notifications",
                document_id=notification_id,
                data={'read': True, 'read_at': datetime.utcnow().isoformat()}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to mark notification: {e}")
            return False
    
    async def mark_all_as_read(self, user_id: str) -> bool:
        """Mark all notifications as read"""
        try:
            notifications = await self.get_user_notifications(user_id, unread_only=True)
            
            for notif in notifications:
                await self.mark_as_read(notif.get('id'), user_id)
            
            return True
        except Exception as e:
            logger.error(f"Failed to mark all notifications: {e}")
            return False
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications"""
        try:
            notifications = await self.get_user_notifications(user_id, unread_only=True)
            return len(notifications)
        except Exception as e:
            logger.error(f"Failed to get unread count: {e}")
            return 0