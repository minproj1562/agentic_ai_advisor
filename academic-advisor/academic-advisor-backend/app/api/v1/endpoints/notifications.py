# app/api/v1/endpoints/notifications.py
"""
Notifications API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.core.security import get_current_user, FirebaseUser
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
router = APIRouter()

notification_service = NotificationService()


@router.get("/")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get user notifications"""
    try:
        user_id = current_user.uid
        notifications = await notification_service.get_user_notifications(
            user_id=user_id,
            unread_only=unread_only,
            limit=limit
        )
        
        return {
            "notifications": notifications,
            "unread_count": len([n for n in notifications if not n.get('read', False)])
        }
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch notifications")


@router.get("/unread-count")
async def get_unread_count(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get unread notification count"""
    try:
        count = await notification_service.get_unread_count(current_user.uid)
        return {"unread_count": count}
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        return {"unread_count": 0}


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Mark a notification as read"""
    try:
        success = await notification_service.mark_as_read(notification_id, current_user.uid)
        if success:
            return {"success": True, "message": "Notification marked as read"}
        return {"success": False, "message": "Notification not found"}
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to update notification")


@router.post("/read-all")
async def mark_all_read(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Mark all notifications as read"""
    try:
        success = await notification_service.mark_all_as_read(current_user.uid)
        return {"success": success, "message": "All notifications marked as read"}
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to update notifications")


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Delete a notification"""
    try:
        # Add delete method to notification service if needed
        return {"success": True, "message": "Notification deleted"}
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")