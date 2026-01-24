# app/database.py - COMPLETE UPDATED VERSION
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# Import all models - UPDATED with weakness models
from app.models.student_profile import StudentProfile, SemesterRecord, SubjectScore
from app.models.student import StudentPerformance
from app.models.elective import Elective, InstructorInfo
from app.models.weakness import (
    WeaknessAnalysisResult, 
    TopicAnalysis,
    StudentInterestProfile  # ← ADDED
)
from app.models.analytics import Analytics
from app.models.messages import Message, Conversation
from app.models.achievement import Achievement, AchievementAnalytics
from app.models.publications import Publication
from app.models.research_area import ResearchArea
from app.models.appointment import AppointmentSlot, AppointmentBooking

async def init_db():
    """Initialize database connection and Beanie ODM"""
    try:
        # Create Motor client
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Initialize beanie with all document models
        await init_beanie(
            database=client[settings.DATABASE_NAME],
            document_models=[
                # Student models
                StudentProfile,
                StudentPerformance,
                SemesterRecord,
                SubjectScore,
                StudentInterestProfile,  # ← ADDED for weakness analysis
                
                # Academic models
                Elective,
                InstructorInfo,
                
                # Weakness analysis models
                WeaknessAnalysisResult,  # ← ADDED
                TopicAnalysis,           # ← ADDED
                
                # Analytics
                Analytics,
                
                # Messaging
                Message,
                Conversation,
                
                # Achievements
                Achievement,
                AchievementAnalytics,
                
                # Research
                Publication,
                ResearchArea,
                
                # Appointments
                AppointmentSlot,
                AppointmentBooking
            ]
        )
        
        print("✅ Database initialized successfully")
        print(f"📊 Registered {len([StudentProfile, StudentPerformance, WeaknessAnalysisResult, TopicAnalysis, StudentInterestProfile, Elective, InstructorInfo, Analytics, Message, Conversation, Achievement, AchievementAnalytics, Publication, ResearchArea, AppointmentSlot, AppointmentBooking])} document models")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False