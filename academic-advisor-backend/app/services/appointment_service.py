import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from app.core.firebase import db

class AppointmentService:
    async def get_faculty_slots(
        self,
        faculty_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[dict]:
        """Get all slots for a faculty member"""
        query = db.collection('appointment_slots').where('faculty_id', '==', faculty_id)
        
        if start_date:
            query = query.where('date', '>=', start_date)
        if end_date:
            query = query.where('date', '<=', end_date)
        
        slots = query.stream()
        
        return [
            {
                'id': doc.id,
                **doc.to_dict(),
                'date': doc.to_dict()['date'].isoformat() if 'date' in doc.to_dict() else None
            }
            for doc in slots
        ]
    
    async def create_slot(
        self,
        faculty_id: str,
        date: datetime,
        start_time: str,
        end_time: str,
        slot_type: str = "Regular"
    ) -> dict:
        """Create a single appointment slot"""
        slot_id = str(uuid.uuid4())
        slot_data = {
            'id': slot_id,
            'faculty_id': faculty_id,
            'date': date,
            'startTime': start_time,
            'endTime': end_time,
            'type': slot_type,
            'isBooked': False,
            'created_at': datetime.now()
        }
        
        db.collection('appointment_slots').document(slot_id).set(slot_data)
        return slot_data
    
    async def create_recurring_slots(
        self,
        faculty_id: str,
        start_date: datetime,
        start_time: str,
        end_time: str,
        pattern: str,
        slot_type: str = "Regular",
        weeks: int = 4
    ) -> List[dict]:
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
    ) -> dict:
        """Book an appointment slot"""
        slot_ref = db.collection('appointment_slots').document(slot_id)
        
        # Update slot
        slot_ref.update({
            'isBooked': True,
            'studentId': student_id,
            'topic': topic,
            'description': description,
            'booked_at': datetime.now()
        })
        
        # Create booking record
        booking_data = {
            'slot_id': slot_id,
            'student_id': student_id,
            'topic': topic,
            'description': description,
            'status': 'confirmed',
            'created_at': datetime.now()
        }
        
        booking_ref = db.collection('bookings').add(booking_data)
        
        return {
            'booking_id': booking_ref[1].id,
            **booking_data
        }
    
    async def cancel_slot(self, slot_id: str, reason: Optional[str] = None):
        """Cancel an appointment slot"""
        slot_ref = db.collection('appointment_slots').document(slot_id)
        
        slot_ref.update({
            'status': 'cancelled',
            'cancellation_reason': reason,
            'cancelled_at': datetime.now()
        })
    
    async def reschedule_slot(
        self,
        slot_id: str,
        new_date: datetime,
        new_start_time: str,
        new_end_time: str
    ) -> dict:
        """Reschedule an appointment"""
        slot_ref = db.collection('appointment_slots').document(slot_id)
        
        updates = {
            'date': new_date,
            'startTime': new_start_time,
            'endTime': new_end_time,
            'rescheduled': True,
            'rescheduled_at': datetime.now()
        }
        
        slot_ref.update(updates)
        
        # Get updated slot
        updated_slot = slot_ref.get()
        return {'id': updated_slot.id, **updated_slot.to_dict()}
    
    async def send_booking_notification(self, slot_id: str, student_id: str):
        """Send notification for booking"""
        # Implementation for sending notifications
        pass
