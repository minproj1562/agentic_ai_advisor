# app/tasks/semester_updater.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app.database import SessionLocal
from app.services.academic_service import AcademicService
from app.models.academic_record import StudentProfile
import logging

logger = logging.getLogger(__name__)

def update_all_student_semesters():
    """Run daily to auto-update semesters"""
    db = SessionLocal()
    try:
        students = db.query(StudentProfile).all()
        updated_count = 0
        
        for student in students:
            if AcademicService.auto_update_semester(db, student.user_id):
                updated_count += 1
        
        logger.info(f"Updated {updated_count} student semesters")
        
    except Exception as e:
        logger.error(f"Error in semester updater: {e}")
    finally:
        db.close()

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    update_all_student_semesters,
    'cron',
    hour=0,  # Run at midnight
    minute=0
)
scheduler.start()