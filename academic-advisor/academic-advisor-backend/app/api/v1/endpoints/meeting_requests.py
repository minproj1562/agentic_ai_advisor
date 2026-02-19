# academic-advisor-backend/app/api/v1/endpoints/meeting_requests.py
"""
Meeting Request Management for Faculty-Student Meetings - FIXED
In-person meetings only (within college premises)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

from app.core.security import get_current_user, FirebaseUser
from app.models.meeting_request import MeetingRequest, MeetingRequestStatus, ScheduledMeeting
from app.models.faculty import Faculty
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
router = APIRouter()
notification_service = NotificationService()


# ==================== Helper ====================

def parse_meeting_date_naive(date_value) -> Optional[datetime]:
    """
    Parse a meeting date into a timezone-NAIVE datetime for safe comparison.
    Handles: str ISO format, datetime with/without tz, None
    """
    if date_value is None:
        return None

    try:
        if isinstance(date_value, str):
            # Remove trailing Z and any timezone offset to keep naive
            clean = date_value.replace('Z', '+00:00')
            dt = datetime.fromisoformat(clean)
        elif isinstance(date_value, datetime):
            dt = date_value
        else:
            return None

        # Strip timezone info so we can compare with datetime.utcnow()
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)

        return dt
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse meeting date '{date_value}': {e}")
        return None


# ==================== Student Endpoints ====================

@router.post("/student/create")
async def create_meeting_request(
    request_data: Dict[str, Any],
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Student creates a meeting request to faculty
    """
    try:
        student_id = current_user.uid
        faculty_id = request_data.get('faculty_id')

        if not faculty_id:
            raise HTTPException(status_code=400, detail="Faculty ID is required")

        # Verify faculty exists
        faculty = await Faculty.find_one(Faculty.user_id == faculty_id)
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty not found")

        # Create meeting request
        meeting_request = MeetingRequest(
            request_id=str(uuid.uuid4()),
            student_id=student_id,
            student_name=current_user.email.split('@')[0],
            student_email=current_user.email,
            faculty_id=faculty_id,
            faculty_name=faculty.name,
            subject=request_data.get('subject', ''),
            message=request_data.get('message', ''),
            urgency=request_data.get('urgency', 'normal'),
            status=MeetingRequestStatus.PENDING,
            created_at=datetime.utcnow()
        )

        await meeting_request.insert()

        # Notify faculty
        try:
            await notification_service.send_notification(
                user_id=faculty_id,
                notification_type='meeting_request',
                title='New Meeting Request',
                message=f'{current_user.email} has requested a meeting about: {request_data.get("subject")}',
                data={'request_id': meeting_request.request_id}
            )
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")

        return {
            "success": True,
            "request_id": meeting_request.request_id,
            "message": "Meeting request sent successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating meeting request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create meeting request")


@router.get("/student/requests")
async def get_student_requests(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get all meeting requests made by student
    """
    try:
        student_id = current_user.uid

        requests = await MeetingRequest.find(
            MeetingRequest.student_id == student_id
        ).sort(-MeetingRequest.created_at).to_list()

        return [
            {
                "request_id": r.request_id,
                "faculty_id": r.faculty_id,
                "faculty_name": r.faculty_name,
                "subject": r.subject,
                "message": r.message,
                "urgency": r.urgency,
                "status": r.status.value,
                "created_at": r.created_at.isoformat(),
                "scheduled_meeting": r.scheduled_meeting.dict() if r.scheduled_meeting else None,
                "faculty_response": r.faculty_response
            }
            for r in requests
        ]

    except Exception as e:
        logger.error(f"Error getting student requests: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch requests")


@router.post("/student/cancel/{request_id}")
async def cancel_meeting_request(
    request_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Student cancels their own meeting request
    """
    try:
        student_id = current_user.uid

        meeting_request = await MeetingRequest.find_one(
            MeetingRequest.request_id == request_id,
            MeetingRequest.student_id == student_id
        )

        if not meeting_request:
            raise HTTPException(status_code=404, detail="Meeting request not found")

        if meeting_request.status not in [MeetingRequestStatus.PENDING, MeetingRequestStatus.ACCEPTED]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel a request with status: {meeting_request.status.value}"
            )

        meeting_request.status = MeetingRequestStatus.CANCELLED
        meeting_request.updated_at = datetime.utcnow()
        await meeting_request.save()

        # Notify faculty about cancellation
        try:
            await notification_service.send_notification(
                user_id=meeting_request.faculty_id,
                notification_type='meeting_cancelled',
                title='Meeting Cancelled',
                message=f'{meeting_request.student_name} has cancelled their meeting request: {meeting_request.subject}',
                data={'request_id': request_id}
            )
        except Exception as e:
            logger.warning(f"Failed to send cancellation notification: {e}")

        return {
            "success": True,
            "message": "Meeting request cancelled successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel request")


# ==================== Faculty Endpoints ====================

@router.get("/faculty/requests")
async def get_faculty_requests(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get all meeting requests received by faculty
    """
    try:
        faculty_id = current_user.uid

        all_requests = await MeetingRequest.find(
            MeetingRequest.faculty_id == faculty_id
        ).sort(-MeetingRequest.created_at).to_list()

        # Categorize requests
        pending = []
        accepted = []
        past = []

        now = datetime.utcnow()

        for r in all_requests:
            request_data = {
                "request_id": r.request_id,
                "student_id": r.student_id,
                "student_name": r.student_name,
                "student_email": r.student_email,
                "student_department": r.student_department,
                "student_semester": r.student_semester,
                "faculty_id": r.faculty_id,
                "faculty_name": r.faculty_name,
                "subject": r.subject,
                "message": r.message,
                "urgency": r.urgency,
                "status": r.status.value,
                "created_at": r.created_at.isoformat(),
                "scheduled_meeting": r.scheduled_meeting.dict() if r.scheduled_meeting else None,
                "faculty_response": r.faculty_response
            }

            if r.status == MeetingRequestStatus.PENDING:
                pending.append(request_data)
            elif r.status == MeetingRequestStatus.ACCEPTED:
                # Check if meeting is in past — use safe naive parser
                if r.scheduled_meeting:
                    meeting_date = parse_meeting_date_naive(r.scheduled_meeting.date)
                    if meeting_date is not None and meeting_date < now:
                        past.append(request_data)
                    else:
                        accepted.append(request_data)
                else:
                    accepted.append(request_data)
            elif r.status in [MeetingRequestStatus.COMPLETED, MeetingRequestStatus.REJECTED, MeetingRequestStatus.CANCELLED]:
                past.append(request_data)

        return {
            "pending": pending,
            "accepted": accepted,
            "past": past,
            "total_pending": len(pending)
        }

    except Exception as e:
        logger.error(f"Error getting faculty requests: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch requests: {str(e)}")


@router.post("/faculty/accept/{request_id}")
async def accept_meeting_request(
    request_id: str,
    schedule_data: Dict[str, Any],
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Faculty accepts a meeting request and schedules it
    """
    try:
        faculty_id = current_user.uid

        # Find the request
        meeting_request = await MeetingRequest.find_one(
            MeetingRequest.request_id == request_id,
            MeetingRequest.faculty_id == faculty_id
        )

        if not meeting_request:
            raise HTTPException(status_code=404, detail="Meeting request not found")

        if meeting_request.status != MeetingRequestStatus.PENDING:
            raise HTTPException(status_code=400, detail="Request is not pending")

        # Create scheduled meeting
        scheduled_meeting = ScheduledMeeting(
            date=schedule_data.get('date'),
            start_time=schedule_data.get('start_time'),
            end_time=schedule_data.get('end_time'),
            venue=schedule_data.get('venue'),
            additional_notes=schedule_data.get('response_message')
        )

        # Update request
        meeting_request.status = MeetingRequestStatus.ACCEPTED
        meeting_request.scheduled_meeting = scheduled_meeting
        meeting_request.faculty_response = schedule_data.get('response_message')
        meeting_request.updated_at = datetime.utcnow()

        await meeting_request.save()

        # Notify student
        try:
            await notification_service.send_notification(
                user_id=meeting_request.student_id,
                notification_type='meeting_accepted',
                title='Meeting Request Accepted',
                message=f'Your meeting request has been accepted. Scheduled for {schedule_data.get("date")} at {schedule_data.get("start_time")}',
                data={
                    'request_id': request_id,
                    'venue': schedule_data.get('venue'),
                    'date': schedule_data.get('date'),
                    'time': schedule_data.get('start_time')
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")

        return {
            "success": True,
            "message": "Meeting scheduled successfully",
            "scheduled_meeting": scheduled_meeting.dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to accept request")


@router.post("/faculty/reject/{request_id}")
async def reject_meeting_request(
    request_id: str,
    reject_data: Dict[str, Any],
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Faculty rejects a meeting request
    """
    try:
        faculty_id = current_user.uid

        meeting_request = await MeetingRequest.find_one(
            MeetingRequest.request_id == request_id,
            MeetingRequest.faculty_id == faculty_id
        )

        if not meeting_request:
            raise HTTPException(status_code=404, detail="Meeting request not found")

        if meeting_request.status != MeetingRequestStatus.PENDING:
            raise HTTPException(status_code=400, detail="Request is not pending")

        meeting_request.status = MeetingRequestStatus.REJECTED
        meeting_request.faculty_response = reject_data.get('reason', '')
        meeting_request.updated_at = datetime.utcnow()

        await meeting_request.save()

        # Notify student
        try:
            await notification_service.send_notification(
                user_id=meeting_request.student_id,
                notification_type='meeting_rejected',
                title='Meeting Request Declined',
                message=f'Your meeting request was declined. Reason: {reject_data.get("reason", "No reason provided")}',
                data={'request_id': request_id}
            )
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")

        return {
            "success": True,
            "message": "Meeting request declined"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reject request")


@router.post("/faculty/complete/{request_id}")
async def mark_meeting_complete(
    request_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Faculty marks a meeting as completed
    """
    try:
        faculty_id = current_user.uid

        meeting_request = await MeetingRequest.find_one(
            MeetingRequest.request_id == request_id,
            MeetingRequest.faculty_id == faculty_id
        )

        if not meeting_request:
            raise HTTPException(status_code=404, detail="Meeting request not found")

        meeting_request.status = MeetingRequestStatus.COMPLETED
        meeting_request.updated_at = datetime.utcnow()

        await meeting_request.save()

        return {
            "success": True,
            "message": "Meeting marked as completed"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete request")