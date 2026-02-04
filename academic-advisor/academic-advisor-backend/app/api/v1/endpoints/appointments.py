# app/api/v1/endpoints/appointments.py
"""
Appointments API - In-Person Meeting Slots
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from app.core.security import get_current_user, FirebaseUser
from app.models.appointment import AppointmentSlot, SlotType, SlotStatus
from app.services.appointment_service import AppointmentService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
router = APIRouter()

appointment_service = AppointmentService()
notification_service = NotificationService()


@router.get("/faculty/slots")
async def get_faculty_slots(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get faculty's appointment slots"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        slots = await appointment_service.get_faculty_slots(
            faculty_id=current_user.uid,
            start_date=start,
            end_date=end
        )
        
        return {
            "slots": [
                {
                    "id": str(s.id) if hasattr(s, 'id') else None,
                    "date": s.date.isoformat() if s.date else None,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "venue": getattr(s, 'venue', ''),
                    "type": s.type.value if s.type else 'regular',
                    "status": s.status.value if s.status else 'available',
                    "is_booked": s.status == SlotStatus.BOOKED if s.status else False,
                    "student_id": getattr(s, 'student_id', None),
                    "topic": getattr(s, 'topic', None)
                }
                for s in slots
            ]
        }
    except Exception as e:
        logger.error(f"Error getting slots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/faculty/slots")
async def create_slot(
    slot_data: Dict[str, Any],
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Create a new appointment slot"""
    try:
        slot = await appointment_service.create_slot(
            faculty_id=current_user.uid,
            date=datetime.fromisoformat(slot_data['date']),
            start_time=slot_data['start_time'],
            end_time=slot_data['end_time'],
            slot_type=SlotType(slot_data.get('type', 'regular'))
        )
        
        # Set venue
        if hasattr(slot, 'venue'):
            slot.venue = slot_data.get('venue', '')
            await slot.save()
        
        return {
            "success": True,
            "slot_id": str(slot.id) if hasattr(slot, 'id') else None,
            "message": "Slot created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating slot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/faculty/slots/{slot_id}")
async def delete_slot(
    slot_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Delete/cancel an appointment slot"""
    try:
        await appointment_service.cancel_slot(slot_id)
        return {"success": True, "message": "Slot cancelled"}
    except Exception as e:
        logger.error(f"Error deleting slot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available/{faculty_id}")
async def get_available_slots(
    faculty_id: str,
    date: Optional[str] = None
):
    """Get available slots for a faculty (public for students)"""
    try:
        target_date = datetime.fromisoformat(date) if date else None
        
        slots = await appointment_service.get_available_slots(
            faculty_id=faculty_id,
            date=target_date
        )
        
        return {
            "slots": [
                {
                    "id": str(s.id) if hasattr(s, 'id') else None,
                    "date": s.date.isoformat() if s.date else None,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "venue": getattr(s, 'venue', ''),
                    "type": s.type.value if s.type else 'regular'
                }
                for s in slots
            ]
        }
    except Exception as e:
        logger.error(f"Error getting available slots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/book/{slot_id}")
async def book_slot(
    slot_id: str,
    booking_data: Dict[str, Any],
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Book an appointment slot (student)"""
    try:
        result = await appointment_service.book_slot(
            slot_id=slot_id,
            student_id=current_user.uid,
            topic=booking_data.get('topic', ''),
            description=booking_data.get('description')
        )
        
        return {
            "success": True,
            "booking_id": result.get('booking_id'),
            "message": "Appointment booked successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error booking slot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/bookings")
async def get_student_bookings(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get student's bookings"""
    try:
        bookings = await appointment_service.get_student_bookings(
            student_id=current_user.uid
        )
        
        return {
            "bookings": [
                {
                    "id": str(b.id) if hasattr(b, 'id') else None,
                    "slot_id": getattr(b, 'slot_id', None),
                    "faculty_id": getattr(b, 'faculty_id', None),
                    "topic": getattr(b, 'topic', None),
                    "status": b.status.value if hasattr(b, 'status') and b.status else 'pending',
                    "created_at": b.created_at.isoformat() if hasattr(b, 'created_at') and b.created_at else None
                }
                for b in bookings
            ]
        }
    except Exception as e:
        logger.error(f"Error getting bookings: {e}")
        raise HTTPException(status_code=500, detail=str(e))