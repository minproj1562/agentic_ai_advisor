# app/api/v1/faculty.py
"""
Faculty API endpoints - FIXED
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from datetime import datetime

from app.dependencies import get_faculty_user
from app.core.security import FirebaseUser
from app.services.faculty_service import FacultyService
from app.core.firebase_admin import firebase_manager
from app.models.faculty import Faculty
from app.utils.helpers import get_logger

logger = get_logger(__name__)
router = APIRouter()

faculty_service = FacultyService()


async def _get_faculty_department(user_id: str) -> Optional[str]:
    """Helper to get faculty department from database"""
    try:
        faculty = await Faculty.find_one(Faculty.user_id == user_id)
        return faculty.department if faculty else None
    except Exception:
        return None


@router.get("/dashboard")
async def get_faculty_dashboard(
    current_user: FirebaseUser = Depends(get_faculty_user)
):
    """
    Get faculty dashboard data
    """
    try:
        # Get department from faculty document
        department = await _get_faculty_department(current_user.uid)
        
        dashboard_data = await faculty_service.get_dashboard_data(
            faculty_id=current_user.uid,
            department=department
        )
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error fetching faculty dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard")


@router.get("/students")
async def get_assigned_students(
    skip: int = 0,
    limit: int = 100,
    risk_level: Optional[str] = None,
    current_user: FirebaseUser = Depends(get_faculty_user)
):
    """
    Get students assigned to faculty
    """
    try:
        # Get department from faculty document
        department = await _get_faculty_department(current_user.uid)
        
        students = await faculty_service.get_assigned_students(
            faculty_id=current_user.uid,
            department=department,
            filters={'risk_level': risk_level} if risk_level else {},
            skip=skip,
            limit=limit
        )
        
        return students
        
    except Exception as e:
        logger.error(f"Error fetching students: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch students")


@router.get("/students/{student_id}/analysis")
async def get_student_analysis(
    student_id: str,
    current_user: FirebaseUser = Depends(get_faculty_user)
):
    """
    Get detailed analysis for a specific student
    """
    try:
        # Verify faculty has access to this student
        if not await faculty_service.verify_student_access(
            faculty_id=current_user.uid,
            student_id=student_id
        ):
            raise HTTPException(status_code=403, detail="Access denied")
        
        analysis = await faculty_service.get_student_analysis(student_id)
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch analysis")


@router.post("/students/{student_id}/intervention")
async def create_intervention(
    student_id: str,
    intervention_data: dict,
    background_tasks: BackgroundTasks,
    current_user: FirebaseUser = Depends(get_faculty_user)
):
    """
    Create intervention for at-risk student
    """
    try:
        intervention = await faculty_service.create_intervention(
            faculty_id=current_user.uid,
            student_id=student_id,
            intervention_data=intervention_data
        )
        
        # Send notification to student
        background_tasks.add_task(
            faculty_service.notify_student_intervention,
            student_id,
            intervention
        )
        
        return intervention
        
    except Exception as e:
        logger.error(f"Error creating intervention: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create intervention")


@router.get("/analytics/department")
async def get_department_analytics(
    time_range: str = Query("current_semester"),
    current_user: FirebaseUser = Depends(get_faculty_user)
):
    """
    Get department-level analytics
    """
    try:
        department = await _get_faculty_department(current_user.uid)
        
        analytics = await faculty_service.get_department_analytics(
            department=department,
            time_range=time_range
        )
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")


@router.post("/announcements")
async def create_announcement(
    announcement: dict,
    background_tasks: BackgroundTasks,
    current_user: FirebaseUser = Depends(get_faculty_user)
):
    """
    Create announcement for students
    """
    try:
        # Get faculty details
        faculty = await Faculty.find_one(Faculty.user_id == current_user.uid)
        faculty_name = faculty.name if faculty else current_user.email
        department = faculty.department if faculty else None
        
        # Create announcement
        announcement_id = await firebase_manager.create_document(
            collection="announcements",
            data={
                **announcement,
                'faculty_id': current_user.uid,
                'faculty_name': faculty_name,
                'department': department,
                'created_at': datetime.utcnow().isoformat()
            }
        )
        
        # Send notifications
        if department:
            background_tasks.add_task(
                faculty_service.broadcast_announcement,
                announcement_id,
                department
            )
        
        return {"message": "Announcement created", "id": announcement_id}
        
    except Exception as e:
        logger.error(f"Error creating announcement: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create announcement")


@router.get("/schedule")
async def get_faculty_schedule(
    current_user: FirebaseUser = Depends(get_faculty_user)
):
    """
    Get faculty schedule and appointments
    """
    try:
        schedule = await faculty_service.get_schedule(
            faculty_id=current_user.uid
        )
        
        return schedule
        
    except Exception as e:
        logger.error(f"Error fetching schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch schedule")


@router.post("/feedback/{student_id}")
async def submit_student_feedback(
    student_id: str,
    feedback: dict,
    current_user: FirebaseUser = Depends(get_faculty_user)
):
    """
    Submit feedback for a student
    """
    try:
        feedback_id = await faculty_service.submit_feedback(
            faculty_id=current_user.uid,
            student_id=student_id,
            feedback=feedback
        )
        
        return {"message": "Feedback submitted", "id": feedback_id}
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")