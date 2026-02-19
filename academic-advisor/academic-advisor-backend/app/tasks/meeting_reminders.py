# academic-advisor/academic-advisor-backend/app/tasks/meeting_reminders.py
"""
Meeting Reminder Background Task
Periodically checks for upcoming meetings and sends reminder notifications
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.models.meeting_request import MeetingRequest, MeetingRequestStatus
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
notification_service = NotificationService()

# Track which meetings already received reminders (in-memory; resets on restart)
_reminded_meetings: set = set()


def parse_meeting_datetime(scheduled) -> Optional[datetime]:
    """Parse meeting date + start_time into a single datetime"""
    try:
        date_str = scheduled.date
        time_str = scheduled.start_time

        # Parse date (handles both "2024-01-15" and "2024-01-15T00:00:00Z")
        if 'T' in date_str:
            meeting_date = datetime.fromisoformat(date_str.replace('Z', '+00:00').replace('+00:00', '')).date()
        else:
            meeting_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Parse time
        parts = time_str.split(':')
        hours, minutes = int(parts[0]), int(parts[1])

        return datetime(meeting_date.year, meeting_date.month, meeting_date.day, hours, minutes)
    except Exception as e:
        logger.warning(f"Failed to parse meeting datetime: {e}")
        return None


async def send_meeting_reminder(meeting: MeetingRequest, minutes_until: int):
    """Send reminder notifications to both student and faculty"""
    reminder_key = f"{meeting.request_id}_{minutes_until}"
    if reminder_key in _reminded_meetings:
        return

    time_label = f"{minutes_until} minutes" if minutes_until < 60 else f"{minutes_until // 60} hour(s)"
    venue = meeting.scheduled_meeting.venue if meeting.scheduled_meeting else "TBD"
    meeting_time = meeting.scheduled_meeting.start_time if meeting.scheduled_meeting else ""

    # Remind student
    try:
        await notification_service.send_notification(
            user_id=meeting.student_id,
            notification_type='meeting_reminder',
            title=f'Meeting in {time_label}',
            message=f'Your meeting with {meeting.faculty_name} is in {time_label} at {venue} ({meeting_time})',
            data={
                'request_id': meeting.request_id,
                'venue': venue,
                'time': meeting_time,
                'type': 'reminder'
            }
        )
    except Exception as e:
        logger.warning(f"Failed to send student reminder: {e}")

    # Remind faculty
    try:
        await notification_service.send_notification(
            user_id=meeting.faculty_id,
            notification_type='meeting_reminder',
            title=f'Meeting in {time_label}',
            message=f'Your meeting with {meeting.student_name} is in {time_label} at {venue} ({meeting_time})',
            data={
                'request_id': meeting.request_id,
                'venue': venue,
                'time': meeting_time,
                'type': 'reminder'
            }
        )
    except Exception as e:
        logger.warning(f"Failed to send faculty reminder: {e}")

    _reminded_meetings.add(reminder_key)
    logger.info(f"✅ Reminder sent for meeting {meeting.request_id} ({time_label} before)")


async def check_upcoming_meetings():
    """Check for meetings that need reminders"""
    try:
        accepted_meetings = await MeetingRequest.find(
            MeetingRequest.status == MeetingRequestStatus.ACCEPTED,
        ).to_list()

        now = datetime.utcnow()

        for meeting in accepted_meetings:
            if not meeting.scheduled_meeting:
                continue

            meeting_dt = parse_meeting_datetime(meeting.scheduled_meeting)
            if not meeting_dt:
                continue

            diff = meeting_dt - now
            minutes_until = diff.total_seconds() / 60

            # Send 1-hour reminder
            if 55 <= minutes_until <= 65:
                await send_meeting_reminder(meeting, 60)

            # Send 15-minute reminder
            if 10 <= minutes_until <= 20:
                await send_meeting_reminder(meeting, 15)

    except Exception as e:
        logger.error(f"Error checking upcoming meetings: {e}")


async def meeting_reminder_loop():
    """Background loop that runs every 5 minutes"""
    logger.info("🔔 Meeting reminder task started")

    # Wait for app to fully initialize
    await asyncio.sleep(10)

    while True:
        try:
            await check_upcoming_meetings()
        except Exception as e:
            logger.error(f"Meeting reminder loop error: {e}")

        await asyncio.sleep(300)  # Check every 5 minutes


def start_reminder_task():
    """Start the reminder background task (call from lifespan)"""
    asyncio.create_task(meeting_reminder_loop())
    logger.info("🔔 Meeting reminder background task scheduled")