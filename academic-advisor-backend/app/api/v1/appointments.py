# app/api/v1/appointments.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.core.security import get_current_user
from app.services.appointment_service import AppointmentService

router = APIRouter()
appointment_service = AppointmentService()

class SlotCreate(BaseModel):
    date: datetime
    start_time: str
    end_time: str
    type: str = "Regular"
    recurring: bool = False
    recurrence_pattern: Optional[str] = None

class SlotBooking(BaseModel):
    slot_id: str
    student_id: str
    topic: str
    description: Optional[str] = None

@router.get("/faculty/{faculty_id}/slots")
async def get_faculty_slots(
    faculty_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all appointment slots for a faculty member"""
    slots = await appointment_service.get_faculty_slots(
        faculty_id, start_date, end_date
    )
    return slots

@router.post("/faculty/{faculty_id}/slots")
async def create_slot(
    faculty_id: str,
    slot: SlotCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new appointment slot"""
    if current_user['uid'] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    if slot.recurring:
        # Create recurring slots
        slots = await appointment_service.create_recurring_slots(
            faculty_id=faculty_id,
            start_date=slot.date,
            start_time=slot.start_time,
            end_time=slot.end_time,
            pattern=slot.recurrence_pattern,
            slot_type=slot.type
        )
        return {"message": f"Created {len(slots)} recurring slots", "slots": slots}
    else:
        # Create single slot
        new_slot = await appointment_service.create_slot(
            faculty_id=faculty_id,
            date=slot.date,
            start_time=slot.start_time,
            end_time=slot.end_time,
            slot_type=slot.type
        )
        return {"message": "Slot created successfully", "slot": new_slot}

@router.post("/slots/{slot_id}/book")
async def book_slot(
    slot_id: str,
    booking: SlotBooking,
    current_user: dict = Depends(get_current_user)
):
    """Book an appointment slot"""
    result = await appointment_service.book_slot(
        slot_id=slot_id,
        student_id=booking.student_id,
        topic=booking.topic,
        description=booking.description
    )
    
    # Send notification to faculty
    await appointment_service.send_booking_notification(
        slot_id=slot_id,
        student_id=booking.student_id
    )
    
    return {"message": "Slot booked successfully", "booking": result}

@router.delete("/slots/{slot_id}")
async def cancel_slot(
    slot_id: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Cancel an appointment slot"""
    await appointment_service.cancel_slot(slot_id, reason)
    return {"message": "Slot cancelled successfully"}

@router.put("/slots/{slot_id}/reschedule")
async def reschedule_slot(
    slot_id: str,
    new_date: datetime,
    new_start_time: str,
    new_end_time: str,
    current_user: dict = Depends(get_current_user)
):
    """Reschedule an appointment"""
    updated_slot = await appointment_service.reschedule_slot(
        slot_id=slot_id,
        new_date=new_date,
        new_start_time=new_start_time,
        new_end_time=new_end_time
    )
    return {"message": "Slot rescheduled successfully", "slot": updated_slot}