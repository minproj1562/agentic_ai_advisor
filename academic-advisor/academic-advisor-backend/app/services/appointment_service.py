"""
Dummy appointment service for backward compatibility
This file prevents import errors while we clean up the codebase
All appointment functionality is now handled via meeting_requests
"""

class AppointmentService:
    """Placeholder class - appointments handled via meeting_requests now"""
    
    async def get_faculty_slots(self, *args, **kwargs):
        return []
    
    async def create_slot(self, *args, **kwargs):
        return {"id": None, "message": "Use meeting requests instead"}
    
    async def book_slot(self, *args, **kwargs):
        return {"success": False, "message": "Use meeting requests instead"}
    
    async def cancel_slot(self, *args, **kwargs):
        return {"success": True}
    
    async def get_available_slots(self, *args, **kwargs):
        return []
    
    async def get_student_bookings(self, *args, **kwargs):
        return []
    
    async def create_recurring_slots(self, *args, **kwargs):
        return []
    
    async def reschedule_slot(self, *args, **kwargs):
        return None
    
    async def get_faculty_bookings(self, *args, **kwargs):
        return []
    
    async def send_booking_notification(self, *args, **kwargs):
        pass

# Create singleton instance for compatibility
appointment_service = AppointmentService()