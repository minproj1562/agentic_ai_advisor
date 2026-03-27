from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.core.security import get_current_user, FirebaseUser
from app.services.academic_service import AcademicService
from app.database.repositories.subject_repository import SubjectRepository

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Request/Response Models ====================

class SubjectInput(BaseModel):
    subject_code: str = Field(..., min_length=1)
    subject_name: str = Field(..., min_length=1)
    credits: int = Field(default=3, ge=1, le=10)
    internal_marks: float = Field(default=0, ge=0, le=100)
    external_marks: float = Field(default=0, ge=0, le=100)
    internal_max: float = Field(default=20, ge=0, le=100)
    external_max: float = Field(default=80, ge=0, le=100)
    total_marks: Optional[float] = None
    grade: Optional[str] = None
    grade_points: Optional[float] = None
    is_elective: bool = False
    is_practical: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "subject_code": "CSIT301",
                "subject_name": "Data Structures",
                "credits": 3,
                "internal_marks": 18,
                "external_marks": 65,
                "internal_max": 20,
                "external_max": 80,
                "is_elective": False,
                "is_practical": False
            }
        }


class AddScoresRequest(BaseModel):
    semester_number: int = Field(..., ge=1, le=8)
    academic_year: str = Field(..., min_length=4)
    study_hours: Optional[float] = Field(default=4.0, ge=0, le=16)
    subjects: List[SubjectInput] = Field(..., min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "semester_number": 5,
                "academic_year": "2024-25",
                "study_hours": 4.5,
                "subjects": [
                    {
                        "subject_code": "CSIT301",
                        "subject_name": "Data Structures",
                        "credits": 3,
                        "internal_marks": 18,
                        "external_marks": 65,
                        "internal_max": 20,
                        "external_max": 80
                    }
                ]
            }
        }


class ProfileCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    roll_number: str = Field(..., min_length=1)
    seat_number: Optional[str] = Field(None, pattern="^[0-9]{6}$", description="6-digit seat number")
    branch: str = Field(default="IT")
    admission_year: int = Field(..., ge=2010, le=2030)
    email: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "roll_number": "CSIT/2022/045",
                "seat_number": "692610",
                "branch": "IT",
                "admission_year": 2022,
                "email": "john@example.com"
            }
        }


class UpdateSeatNumberRequest(BaseModel):
    seat_number: str = Field(..., pattern="^[0-9]{6}$", description="6-digit seat number")
    semester: Optional[int] = Field(None, ge=1, le=8)


# ==================== Endpoints ====================

@router.get("/profile")
async def get_profile(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get student profile"""
    try:
        service = AcademicService()
        profile = await service.get_student_profile(current_user)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please create your profile first."
            )

        return {
            "profile": {
                "user_id": profile.user_id,
                "name": profile.name,
                "roll_number": profile.roll_number,
                "seat_number": profile.current_seat_number,
                "seat_number_history": [
                    {
                        "seat_number": sr.seat_number,
                        "semester": sr.semester,
                        "academic_year": sr.academic_year
                    }
                    for sr in profile.seat_number_history
                ],
                "branch": profile.branch,
                "admission_year": profile.admission_year,
                "current_semester": profile.current_semester,
                "current_academic_year": profile.current_academic_year,
                "cgpa": profile.cgpa,
                "total_credits_earned": profile.total_credits_earned,
                "total_credits_required": profile.total_credits_required,
                "email": profile.email,
                "marks_synced": profile.marks_synced_at is not None,
                "study_hours": profile.study_hours
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/profile/create")
async def create_profile(
    profile_data: ProfileCreateRequest,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Create or update student profile"""
    try:
        service = AcademicService()
        profile = await service.create_or_update_profile(
            current_user, 
            profile_data.model_dump()
        )

        return {
            "message": "Profile saved successfully",
            "current_semester": profile.current_semester,
            "current_academic_year": profile.current_academic_year,
            "name": profile.name,
            "roll_number": profile.roll_number,
            "branch": profile.branch,
            "admission_year": profile.admission_year,
            "marks_synced": profile.marks_synced_at is not None,
            "profile": {
                "user_id": profile.user_id,
                "name": profile.name,
                "roll_number": profile.roll_number,
                "seat_number": profile.current_seat_number,
                "branch": profile.branch,
                "admission_year": profile.admission_year,
                "current_semester": profile.current_semester,
                "current_academic_year": profile.current_academic_year
            }
        }
    except Exception as e:
        logger.error(f"Error creating profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/profile/seat-number")
async def update_seat_number(
    request: UpdateSeatNumberRequest = Body(...),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Update student's seat number"""
    try:
        service = AcademicService()
        profile = await service.update_seat_number(
            current_user, 
            request.seat_number,
            request.semester
        )
        
        return {
            "message": "Seat number updated successfully",
            "seat_number": request.seat_number,
            "marks_synced": profile.marks_synced_at is not None
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating seat number: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/scores/add")
async def add_scores(
    request: AddScoresRequest,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Add semester scores"""
    try:
        service = AcademicService()

        # Convert Pydantic models to dicts
        subjects_data = [s.model_dump() for s in request.subjects]

        # Include study hours in the service call
        result = await service.add_semester_scores(
            current_user,
            request.semester_number,
            request.academic_year,
            subjects_data,
            study_hours=request.study_hours  # Pass study hours if your service supports it
        )

        return {
            "message": f"Semester {request.semester_number} scores added successfully",
            **result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding scores: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/scores")
async def get_scores(
    semester_number: Optional[int] = Query(None),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get subject scores"""
    try:
        service = AcademicService()
        scores = await service.get_semester_scores(current_user, semester_number)
        
        # Get study hours if available
        profile = await service.get_student_profile(current_user)
        study_hours = profile.study_hours if profile else None

        return {
            "semester_number": semester_number,
            "count": len(scores),
            "study_hours": study_hours,
            "scores": [
                {
                    "subject_code": s.subject_code,
                    "subject_name": s.subject_name,
                    "credits": s.credits,
                    "internal_marks": s.internal_marks,
                    "external_marks": s.external_marks,
                    "total_marks": s.total_marks,
                    "grade": s.grade,
                    "grade_points": s.grade_points,
                    "is_elective": s.is_elective,
                    "is_practical": s.is_practical
                }
                for s in scores
            ]
        }
    except Exception as e:
        logger.error(f"Error getting scores: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/semesters")
async def get_semesters(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get all semester records"""
    try:
        service = AcademicService()
        semesters = await service.get_semester_records(current_user)

        return {
            "count": len(semesters),
            "semesters": [
                {
                    "semester_number": s.semester_number,
                    "academic_year": s.academic_year,
                    "sgpa": s.sgpa,
                    "total_credits": s.total_credits,
                    "credits_earned": s.credits_earned,
                    "is_complete": s.is_complete,
                    "subjects_count": len(s.subjects)
                }
                for s in semesters
            ]
        }
    except Exception as e:
        logger.error(f"Error getting semesters: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/cgpa")
async def get_cgpa(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get current CGPA"""
    try:
        service = AcademicService()
        profile = await service.get_student_profile(current_user)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        return {
            "cgpa": profile.cgpa,
            "total_credits_earned": profile.total_credits_earned,
            "total_credits_required": profile.total_credits_required,
            "completion_percentage": round(
                (profile.total_credits_earned / profile.total_credits_required) * 100, 1
            ) if profile.total_credits_required > 0 else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CGPA: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/summary")
async def get_academic_summary(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get complete academic summary"""
    try:
        service = AcademicService()
        profile = await service.get_student_profile(current_user)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        completed_semesters = [s for s in profile.semester_records if s.is_complete]

        return {
            "user_id": profile.user_id,
            "name": profile.name,
            "roll_number": profile.roll_number,
            "seat_number": profile.current_seat_number,
            "branch": profile.branch,
            "admission_year": profile.admission_year,
            "current_semester": profile.current_semester,
            "current_academic_year": profile.current_academic_year,
            "cgpa": profile.cgpa,
            "total_credits_earned": profile.total_credits_earned,
            "total_credits_required": profile.total_credits_required,
            "completion_percentage": round(
                (profile.total_credits_earned / profile.total_credits_required) * 100, 1
            ) if profile.total_credits_required > 0 else 0,
            "completed_semesters": len(completed_semesters),
            "semester_sgpas": [
                {"semester": s.semester_number, "sgpa": s.sgpa, "credits": s.credits_earned}
                for s in completed_semesters
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/scores/semester/{semester_number}")
async def delete_semester(
    semester_number: int,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Delete a semester's scores"""
    try:
        from app.models.student_profile import StudentProfile

        profile = await StudentProfile.find_one(
            StudentProfile.user_id == current_user.uid
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        original_len = len(profile.semester_records)
        profile.semester_records = [
            s for s in profile.semester_records 
            if s.semester_number != semester_number
        ]

        if len(profile.semester_records) == original_len:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Semester {semester_number} not found"
            )

        # Recalculate CGPA
        if profile.semester_records:
            total_points = sum(s.sgpa * s.total_credits for s in profile.semester_records if s.is_complete)
            total_credits = sum(s.total_credits for s in profile.semester_records if s.is_complete)
            profile.cgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
            profile.total_credits_earned = sum(s.credits_earned for s in profile.semester_records)
        else:
            profile.cgpa = 0.0
            profile.total_credits_earned = 0

        profile.last_updated = datetime.now()
        await profile.save()

        return {
            "message": f"Semester {semester_number} deleted successfully",
            "updated_cgpa": profile.cgpa,
            "remaining_semesters": len(profile.semester_records)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting semester: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/subjects/available/{semester}")
async def get_available_subjects_for_semester(
    semester: int,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get available subjects for a specific semester based on student's curriculum"""
    try:
        service = AcademicService()
        subjects_data = await service.get_available_subjects(current_user, semester)

        return {
            "success": True,
            **subjects_data
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting available subjects: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ==================== SUBJECTS ENDPOINTS ====================

@router.get("/subjects")
async def list_subjects(
    semester: Optional[int] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    List subjects with optional filtering.
    
    - **semester**: Filter by semester number (1-8)
    - **department**: Filter by department code (e.g., "CSE", "IT")
    - **search**: Full-text search on subject name/code/topics
    """
    try:
        subject_repo = SubjectRepository()
        
        if search:
            # Full-text search
            subjects = await subject_repo.text_search(search, limit=limit)
        elif semester:
            # Filter by semester
            subjects = await subject_repo.get_subjects_by_semester(semester, department)
        else:
            # Get all (with optional department filter)
            coll = await subject_repo._get_collection()
            query = {}
            if department:
                query["department"] = {"$regex": department, "$options": "i"}
            
            cursor = coll.find(query).skip(skip).limit(limit)
            docs = await cursor.to_list(length=limit)
            subjects = [subject_repo.Subject(**doc) for doc in docs] if docs else []
        
        return {
            "success": True,
            "count": len(subjects),
            "subjects": [
                {
                    "code": s.code,
                    "name": s.name,
                    "semester": s.semester,
                    "credits": s.credits,
                    "subject_type": s.subject_type,
                    "category": getattr(s, 'category', None),
                    "teaching_scheme": s.teaching_scheme,
                    "description": getattr(s, 'description', None),
                }
                for s in subjects
            ],
            "filters": {
                "semester": semester,
                "department": department,
                "search": search
            }
        }
    except Exception as e:
        logger.error(f"Error listing subjects: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/subjects/{code}")
async def get_subject_by_code(
    code: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get detailed information about a specific subject by its code.
    
    Returns the full subject including units and topics.
    """
    try:
        subject_repo = SubjectRepository()
        subject = await subject_repo.get_by_code(code.upper())
        
        if not subject:
            # Try case-insensitive search
            subject = await subject_repo.get_by_code(code)
        
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject with code '{code}' not found"
            )
        
        # Build response with units and topics
        result = {
            "code": subject.code,
            "name": subject.name,
            "semester": subject.semester,
            "credits": subject.credits,
            "subject_type": subject.subject_type,
            "category": getattr(subject, 'category', None),
            "teaching_scheme": subject.teaching_scheme,
            "description": getattr(subject, 'description', None),
            "learning_outcomes": getattr(subject, 'learning_outcomes', []),
            "reference_books": getattr(subject, 'reference_books', []),
            "prerequisites": getattr(subject, 'prerequisites', []),
            "examination_scheme": getattr(subject, 'examination_scheme', {}),
            "is_active": getattr(subject, 'is_active', True),
        }
        
        # Fetch units if available (depends on data structure)
        # Note: You may need to adjust this based on how units are stored
        if hasattr(subject, 'units'):
            result["units"] = subject.units
        
        return {
            "success": True,
            "subject": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subject {code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/subjects/{code}/syllabus")
async def get_subject_syllabus(
    code: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get the complete syllabus for a subject including all units and topics.
    """
    try:
        subject_repo = SubjectRepository()
        subject = await subject_repo.get_subject_syllabus(code.upper())
        
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject with code '{code}' not found"
            )
        
        return {
            "success": True,
            "subject_code": subject.code,
            "subject_name": subject.name,
            "semester": subject.semester,
            "credits": subject.credits,
            "syllabus": {
                "description": getattr(subject, 'description', ''),
                "learning_outcomes": getattr(subject, 'learning_outcomes', []),
                "units": getattr(subject, 'units', []),  # Adjust based on your data structure
                "reference_books": getattr(subject, 'reference_books', []),
                "prerequisites": getattr(subject, 'prerequisites', []),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting syllabus for {code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/subjects/search/topics")
async def search_topics(
    query: str,
    limit: int = 10,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Search for topics across all subjects.
    
    Returns matching topics with their subject and unit context.
    """
    try:
        if not query or len(query) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query must be at least 2 characters"
            )
        
        subject_repo = SubjectRepository()
        topics = await subject_repo.search_topics(query, limit=limit)
        
        return {
            "success": True,
            "query": query,
            "count": len(topics),
            "topics": topics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching topics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/subjects/semester/{semester_number}")
async def get_subjects_by_semester(
    semester_number: int,
    department: Optional[str] = None,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get all subjects for a specific semester.
    
    - **semester_number**: Semester number (1-8)
    - **department**: Optional department filter
    """
    try:
        if semester_number < 1 or semester_number > 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Semester number must be between 1 and 8"
            )
        
        subject_repo = SubjectRepository()
        subjects = await subject_repo.get_subjects_by_semester(semester_number, department)
        
        # Group by type
        grouped = {
            "core": [],
            "elective": [],
            "lab": [],
            "other": []
        }
        
        for s in subjects:
            subject_data = {
                "code": s.code,
                "name": s.name,
                "credits": s.credits,
                "subject_type": s.subject_type,
                "teaching_scheme": s.teaching_scheme,
            }
            
            if s.subject_type in ['PCC', 'BSC', 'ESC']:
                grouped["core"].append(subject_data)
            elif s.subject_type in ['PEC', 'OEC']:
                grouped["elective"].append(subject_data)
            elif s.subject_type in ['LBC', 'SBL']:
                grouped["lab"].append(subject_data)
            else:
                grouped["other"].append(subject_data)
        
        return {
            "success": True,
            "semester": semester_number,
            "department": department,
            "total_count": len(subjects),
            "subjects": grouped,
            "total_credits": sum(s.credits for s in subjects)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subjects for semester {semester_number}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )    
