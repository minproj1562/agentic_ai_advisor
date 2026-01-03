#academic-advisor-backend/app/api/v1/endpoints/appointments.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from beanie import PydanticObjectId

from app.core.security import get_current_user, FirebaseUser
from app.services.appointment_service import AppointmentService
from app.models.appointment import SlotType, SlotStatus
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/faculty/{faculty_id}/slots")
async def get_faculty_slots(
    faculty_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get all appointment slots for a faculty member"""
    service = AppointmentService()
    try:
        slots = await service.get_faculty_slots(
            faculty_id, start_date, end_date
        )
        return {"slots": [slot.dict() for slot in slots]}
    except Exception as e:
        logger.error(f"Error getting faculty slots: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/faculty/{faculty_id}/slots")
async def create_slot(
    faculty_id: str,
    slot_data: dict,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Create a new appointment slot"""
    if current_user.uid != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    service = AppointmentService()
    try:
        if slot_data.get("recurring", False):
            # Create recurring slots
            slots = await service.create_recurring_slots(
                faculty_id=faculty_id,
                start_date=slot_data["date"],
                start_time=slot_data["start_time"],
                end_time=slot_data["end_time"],
                pattern=slot_data.get("recurrence_pattern", "weekly"),
                slot_type=SlotType(slot_data.get("type", "Regular")),
                weeks=slot_data.get("weeks", 4)
            )
            return {
                "message": f"Created {len(slots)} recurring slots", 
                "slots": [slot.dict() for slot in slots]
            }
        else:
            # Create single slot
            slot = await service.create_slot(
                faculty_id=faculty_id,
                date=slot_data["date"],
                start_time=slot_data["start_time"],
                end_time=slot_data["end_time"],
                slot_type=SlotType(slot_data.get("type", "Regular"))
            )
            return {
                "message": "Slot created successfully", 
                "slot": slot.dict()
            }
    except Exception as e:
        logger.error(f"Error creating slot: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/slots/{slot_id}/book")
async def book_slot(
    slot_id: str,
    booking_data: dict,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Book an appointment slot"""
    service = AppointmentService()
    try:
        result = await service.book_slot(
            slot_id=slot_id,
            student_id=current_user.uid,
            topic=booking_data["topic"],
            description=booking_data.get("description")
        )
        
        # Send notification to faculty
        await service.send_booking_notification(slot_id, current_user.uid)
        
        return {
            "message": "Slot booked successfully", 
            "booking": result
        }
    except Exception as e:
        logger.error(f"Error booking slot: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/slots/{slot_id}")
async def cancel_slot(
    slot_id: str,
    reason: Optional[str] = None,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Cancel an appointment slot"""
    service = AppointmentService()
    try:
        await service.cancel_slot(slot_id, reason)
        return {"message": "Slot cancelled successfully"}
    except Exception as e:
        logger.error(f"Error cancelling slot: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/slots/{slot_id}/reschedule")
async def reschedule_slot(
    slot_id: str,
    reschedule_data: dict,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Reschedule an appointment"""
    service = AppointmentService()
    try:
        updated_slot = await service.reschedule_slot(
            slot_id=slot_id,
            new_date=reschedule_data["new_date"],
            new_start_time=reschedule_data["new_start_time"],
            new_end_time=reschedule_data["new_end_time"]
        )
        return {
            "message": "Slot rescheduled successfully", 
            "slot": updated_slot.dict()
        }
    except Exception as e:
        logger.error(f"Error rescheduling slot: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/student/bookings")
async def get_student_bookings(
    status: Optional[str] = None,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get student's bookings"""
    service = AppointmentService()
    try:
        bookings = await service.get_student_bookings(
            current_user.uid, 
            status
        )
        return {"bookings": [booking.dict() for booking in bookings]}
    except Exception as e:
        logger.error(f"Error getting student bookings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available/{faculty_id}")
async def get_available_slots(
    faculty_id: str,
    date: Optional[datetime] = None,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get available slots for a faculty member"""
    service = AppointmentService()
    try:
        slots = await service.get_available_slots(faculty_id, date)
        return {"slots": [slot.dict() for slot in slots]}
    except Exception as e:
        logger.error(f"Error getting available slots: {e}")
        raise HTTPException(status_code=500, detail=str(e))