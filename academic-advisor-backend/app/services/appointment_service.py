#academic-advisor-backend/app/services/appointment_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from beanie import PydanticObjectId
import uuid

from app.models.appointment import AppointmentSlot, AppointmentBooking, SlotType, SlotStatus, BookingStatus
from app.core.security import FirebaseUser
import logging

logger = logging.getLogger(__name__)

class AppointmentService:
    
    async def get_faculty_slots(
        self,
        faculty_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AppointmentSlot]:
        """Get all slots for a faculty member"""
        query = {"faculty_id": faculty_id}
        
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            if "date" in query and isinstance(query["date"], dict):
                query["date"]["$lte"] = end_date
            else:
                query["date"] = {"$lte": end_date}
        
        slots = await AppointmentSlot.find(query).sort("date").to_list()
        return slots
    
    async def create_slot(
        self,
        faculty_id: str,
        date: datetime,
        start_time: str,
        end_time: str,
        slot_type: SlotType = SlotType.REGULAR
    ) -> AppointmentSlot:
        """Create a single appointment slot"""
        slot = AppointmentSlot(
            faculty_id=faculty_id,
            date=date,
            start_time=start_time,
            end_time=end_time,
            type=slot_type
        )
        await slot.insert()
        return slot
    
    async def create_recurring_slots(
        self,
        faculty_id: str,
        start_date: datetime,
        start_time: str,
        end_time: str,
        pattern: str,
        slot_type: SlotType = SlotType.REGULAR,
        weeks: int = 4
    ) -> List[AppointmentSlot]:
        """Create recurring appointment slots"""
        slots = []
        current_date = start_date
        
        for _ in range(weeks):
            slot = await self.create_slot(
                faculty_id=faculty_id,
                date=current_date,
                start_time=start_time,
                end_time=end_time,
                slot_type=slot_type
            )
            slot.is_recurring = True
            slot.recurrence_pattern = pattern
            await slot.save()
            slots.append(slot)
            
            if pattern == 'weekly':
                current_date += timedelta(weeks=1)
            elif pattern == 'daily':
                current_date += timedelta(days=1)
            elif pattern == 'biweekly':
                current_date += timedelta(weeks=2)
        
        return slots
    
    async def book_slot(
        self,
        slot_id: str,
        student_id: str,
        topic: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Book an appointment slot"""
        slot = await AppointmentSlot.get(slot_id)
        if not slot:
            raise ValueError("Slot not found")
        
        if slot.status != SlotStatus.AVAILABLE:
            raise ValueError("Slot is not available")
        
        # Update slot
        slot.student_id = student_id
        slot.status = SlotStatus.BOOKED
        slot.topic = topic
        slot.description = description
        slot.booked_at = datetime.now()
        await slot.save()
        
        # Create booking record
        booking = AppointmentBooking(
            slot_id=str(slot.id),
            faculty_id=slot.faculty_id,
            student_id=student_id,
            topic=topic,
            description=description
        )
        await booking.insert()
        
        return {
            "booking_id": str(booking.id),
            "slot": slot.dict(),
            "booking": booking.dict()
        }
    
    async def cancel_slot(
        self, 
        slot_id: str, 
        reason: Optional[str] = None
    ):
        """Cancel an appointment slot"""
        slot = await AppointmentSlot.get(slot_id)
        if not slot:
            raise ValueError("Slot not found")
        
        slot.status = SlotStatus.CANCELLED
        slot.cancelled_at = datetime.now()
        await slot.save()
        
        # Also cancel any associated booking
        if slot.student_id:
            booking = await AppointmentBooking.find_one({
                "slot_id": str(slot.id),
                "status": BookingStatus.CONFIRMED
            })
            if booking:
                booking.status = BookingStatus.CANCELLED
                booking.cancelled_at = datetime.now()
                await booking.save()
    
    async def reschedule_slot(
        self,
        slot_id: str,
        new_date: datetime,
        new_start_time: str,
        new_end_time: str
    ) -> AppointmentSlot:
        """Reschedule an appointment"""
        slot = await AppointmentSlot.get(slot_id)
        if not slot:
            raise ValueError("Slot not found")
        
        # Create new slot with same details
        new_slot = AppointmentSlot(
            faculty_id=slot.faculty_id,
            date=new_date,
            start_time=new_start_time,
            end_time=new_end_time,
            type=slot.type,
            status=SlotStatus.AVAILABLE
        )
        await new_slot.insert()
        
        # Update booking if exists
        if slot.student_id:
            booking = await AppointmentBooking.find_one({
                "slot_id": str(slot.id)
            })
            if booking:
                booking.slot_id = str(new_slot.id)
                await booking.save()
            
            new_slot.student_id = slot.student_id
            new_slot.status = SlotStatus.BOOKED
            new_slot.topic = slot.topic
            new_slot.description = slot.description
            await new_slot.save()
        
        # Cancel old slot
        await self.cancel_slot(slot_id, "Rescheduled")
        
        return new_slot
    
    async def get_student_bookings(
        self,
        student_id: str,
        status: Optional[BookingStatus] = None
    ) -> List[AppointmentBooking]:
        """Get all bookings for a student"""
        query = {"student_id": student_id}
        if status:
            query["status"] = status
        
        bookings = await AppointmentBooking.find(query).sort("created_at").to_list()
        return bookings
    
    async def get_faculty_bookings(
        self,
        faculty_id: str,
        status: Optional[BookingStatus] = None
    ) -> List[AppointmentBooking]:
        """Get all bookings for a faculty member"""
        query = {"faculty_id": faculty_id}
        if status:
            query["status"] = status
        
        bookings = await AppointmentBooking.find(query).sort("created_at").to_list()
        return bookings
    
    async def send_booking_notification(self, slot_id: str, student_id: str):
        """Send notification for booking"""
        # This would integrate with your notification service
        # For now, just log the notification
        logger.info(f"Booking notification: Slot {slot_id} booked by student {student_id}")
        
    async def get_available_slots(
        self,
        faculty_id: str,
        date: Optional[datetime] = None
    ) -> List[AppointmentSlot]:
        """Get available slots for a faculty member"""
        query = {
            "faculty_id": faculty_id,
            "status": SlotStatus.AVAILABLE
        }
        
        if date:
            query["date"] = {
                "$gte": date.replace(hour=0, minute=0, second=0),
                "$lte": date.replace(hour=23, minute=59, second=59)
            }
        
        slots = await AppointmentSlot.find(query).sort("date").to_list()
        return slots