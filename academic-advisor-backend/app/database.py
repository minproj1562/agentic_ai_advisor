#academic-advisor-backend/app/database.py
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# Import all your models
from app.models.student_profile import StudentProfile, SemesterRecord, SubjectScore
from app.models.elective import Elective, InstructorInfo
from app.models.analytics import WeaknessAnalysisResult, TopicAnalysis
from app.models.messages import Message, Conversation
from app.models.achievement import Achievement, AchievementAnalytics
from app.models.publications import Publication
from app.models.research_area import ResearchArea
from app.models.appointment import AppointmentSlot, AppointmentBooking  # Add this

async def init_db():
    try:
        # Create Motor client
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        
        # Initialize beanie with all document models
        await init_beanie(
            database=client[settings.DATABASE_NAME],
            document_models=[
                StudentProfile,
                SemesterRecord,
                SubjectScore,
                Elective,
                InstructorInfo,
                WeaknessAnalysisResult,
                TopicAnalysis,
                Message,
                Conversation,
                Achievement,
                AchievementAnalytics,
                Publication,
                ResearchArea,
                AppointmentSlot,  # Add this
                AppointmentBooking  # Add this
            ]
        )
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False