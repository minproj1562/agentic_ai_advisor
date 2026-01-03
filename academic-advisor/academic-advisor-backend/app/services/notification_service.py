# app/services/notification_service.py
"""
Notification Service for real-time alerts and emails
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings
from app.core.firebase_admin import firebase_manager
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class NotificationService:
    """
    Service for handling notifications via email, push, and real-time updates
    """
    
    def __init__(self):
        self.email_enabled = settings.ENABLE_EMAIL_ALERTS
        self.smtp_config = {
            'host': settings.SMTP_HOST,
            'port': settings.SMTP_PORT,
            'user': settings.SMTP_USER,
            'password': settings.SMTP_PASSWORD
        }
    
    async def send_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        channels: List[str] = None
    ) -> bool:
        """
        Send notification through multiple channels
        """
        channels = channels or ['database', 'realtime']
        success = True
        
        try:
            # Store in database
            if 'database' in channels:
                await self._store_notification(
                    user_id, notification_type, title, message, data
                )
            
            # Send real-time update
            if 'realtime' in channels:
                await self._send_realtime_notification(
                    user_id, notification_type, title, message, data
                )
            
            # Send email
            if 'email' in channels and self.email_enabled:
                user = await firebase_manager.get_document(
                    collection='users',
                    document_id=user_id
                )
                if user and user.get('email'):
                    await self._send_email_notification(
                        user['email'], title, message
                    )
            
            # Send push notification (if implemented)
            if 'push' in channels:
                await self._send_push_notification(
                    user_id, title, message
                )
            
            logger.info(f"Notification sent to {user_id}: {title}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False
    
    async def send_bulk_notifications(
        self,
        user_ids: List[str],
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send notifications to multiple users
        """
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        # Process in batches
        batch_size = 50
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i+batch_size]
            
            tasks = []
            for user_id in batch:
                tasks.append(
                    self.send_notification(
                        user_id, notification_type, title, message, data
                    )
                )
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for user_id, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results['failed'] += 1
                    results['errors'].append({
                        'user_id': user_id,
                        'error': str(result)
                    })
                elif result:
                    results['sent'] += 1
                else:
                    results['failed'] += 1
        
        return results
    
    async def _store_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Store notification in Firebase
        """
        notification = {
            'user_id': user_id,
            'type': notification_type,
            'title': title,
            'message': message,
            'data': data or {},
            'read': False,
            'created_at': datetime.utcnow().isoformat()
        }
        
        await firebase_manager.create_document(
            collection=f'users/{user_id}/notifications',
            data=notification
        )
    
    async def _send_realtime_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Send real-time notification via WebSocket
        """
        from app.api.v1.websocket import manager
        
        notification_data = {
            'type': 'notification',
            'notification_type': notification_type,
            'title': title,
            'message': message,
            'data': data or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await manager.send_personal_message(
            json.dumps(notification_data),
            f'user:{user_id}'
        )
    
    async def _send_email_notification(
        self,
        email: str,
        subject: str,
        body: str
    ):
        """
        Send email notification
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config['user']
            msg['To'] = email
            
            # Create HTML body
            html_body = f"""
            <html>
                <body>
                    <h2>{subject}</h2>
                    <p>{body}</p>
                    <hr>
                    <p style="color: gray; font-size: 12px;">
                        This is an automated message from Academic Advisor System.
                        Please do not reply to this email.
                    </p>
                </body>
            </html>
            """
            
            part = MIMEText(html_body, 'html')
            msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['user'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"Email sent to {email}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise
    
    async def _send_push_notification(
        self,
        user_id: str,
        title: str,
        message: str
    ):
        """
        Send push notification (placeholder for actual implementation)
        """
        # This would integrate with FCM or similar service
        logger.info(f"Push notification would be sent to {user_id}: {title}")
    
    async def send_performance_alert(
        self,
        student_id: str,
        alert_type: str,
        metrics: Dict[str, Any]
    ):
        """
        Send performance-related alerts
        """
        templates = {
            'low_attendance': {
                'title': 'Attendance Alert',
                'message': f"Your attendance has dropped to {metrics.get('attendance', 0)}%. "
                          f"Minimum required is 75%."
            },
            'grade_drop': {
                'title': 'Performance Alert',
                'message': f"Your SGPA has dropped from {metrics.get('previous_sgpa', 0)} "
                          f"to {metrics.get('current_sgpa', 0)}."
            },
            'high_risk': {
                'title': 'Urgent: Academic Risk Alert',
                'message': f"You have been identified as high risk with a score of "
                          f"{metrics.get('risk_score', 0)}%. Immediate action required."
            },
            'improvement': {
                'title': 'Congratulations!',
                'message': f"Your performance has improved! SGPA increased to "
                          f"{metrics.get('current_sgpa', 0)}."
            }
        }
        
        template = templates.get(alert_type)
        if template:
            await self.send_notification(
                user_id=student_id,
                notification_type='performance_alert',
                title=template['title'],
                message=template['message'],
                data=metrics,
                channels=['database', 'realtime', 'email']
            )


async def start_notification_worker():
    """
    Start background worker for processing notifications
    """
    service = NotificationService()
    
    while True:
        try:
            # Check for pending notifications
            pending = await firebase_manager.get_collection(
                collection='notification_queue',
                filters=[{'field': 'status', 'operator': '==', 'value': 'pending'}],
                limit=10
            )
            
            for notification in pending:
                # Process notification
                await service.send_notification(
                    user_id=notification['user_id'],
                    notification_type=notification['type'],
                    title=notification['title'],
                    message=notification['message'],
                    data=notification.get('data')
                )
                
                # Mark as processed
                await firebase_manager.update_document(
                    collection='notification_queue',
                    document_id=notification['id'],
                    data={'status': 'sent', 'sent_at': datetime.utcnow().isoformat()}
                )
            
            # Sleep before next check
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Notification worker error: {str(e)}")
            await asyncio.sleep(30)