import AcademicService
from .research_service import ResearchAreaService
from .publication_service import PublicationService
from .achievement_service import AchievementService
from .messaging_service import MessagingService
from .appointment_service import AppointmentService  # Add this

__all__ = [
    "AcademicService",
    "ResearchAreaService", 
    "PublicationService",
    "AchievementService",
    "MessagingService",
    "AppointmentService"  # Add this
]