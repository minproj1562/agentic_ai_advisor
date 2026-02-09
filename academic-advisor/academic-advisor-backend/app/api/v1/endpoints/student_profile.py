# app/api/v1/endpoints/student_profile.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.models.student_profile import StudentProfile, SemesterRecord, SubjectScore
from app.core.security import get_current_user, FirebaseUser

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Request/Response Models ====================

class StudentProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    roll_number: str = Field(..., min_length=1, max_length=50)
    branch: str = Field(..., min_length=1, max_length=20)
    admission_year: int = Field(..., ge=2010, le=2030)
    email: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "roll_number": "CSIT/2022/045",
                "branch": "IT",
                "admission_year": 2022,
                "email": "john@example.com"
            }
        }


class StudentProfileResponse(BaseModel):
    id: Optional[str] = None
    user_id: str
    roll_number: str
    name: str
    email: str
    branch: str
    admission_year: int
    current_semester: int
    current_academic_year: str
    cgpa: float
    total_credits_earned: int
    total_credits_required: int
    created_at: datetime
    last_updated: datetime

    class Config:
        from_attributes = True


# ==================== Helper Functions ====================

def calculate_academic_details(admission_year: int) -> dict:
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    years_diff = current_year - admission_year

    if current_month >= 7:
        current_semester = (years_diff * 2) + 1
        academic_year = f"{current_year}-{str(current_year + 1)[2:]}"
    else:
        current_semester = years_diff * 2
        academic_year = f"{current_year - 1}-{str(current_year)[2:]}"

    current_semester = max(1, min(current_semester, 8))
    return {
        "current_semester": current_semester,
        "current_academic_year": academic_year
    }


def profile_to_response(profile: StudentProfile) -> StudentProfileResponse:
    return StudentProfileResponse(
        id=str(profile.id) if profile.id else None,
        user_id=profile.user_id,
        roll_number=profile.roll_number,
        name=profile.name,
        email=profile.email,
        branch=profile.branch,
        admission_year=profile.admission_year,
        current_semester=profile.current_semester,
        current_academic_year=profile.current_academic_year,
        cgpa=profile.cgpa,
        total_credits_earned=profile.total_credits_earned,
        total_credits_required=profile.total_credits_required,
        created_at=profile.created_at,
        last_updated=profile.last_updated
    )


def serialize_subject(sub: SubjectScore) -> Dict[str, Any]:
    return {
        "subject_code": sub.subject_code,
        "subject_name": sub.subject_name,
        "credits": sub.credits,
        "internal_marks": sub.internal_marks,
        "external_marks": sub.external_marks,
        "total_marks": sub.total_marks,
        "grade": sub.grade,
        "grade_points": sub.grade_points,
        "is_elective": sub.is_elective,
        "is_practical": sub.is_practical
    }


def serialize_semester(sem: SemesterRecord) -> Dict[str, Any]:
    return {
        "semester_number": sem.semester_number,
        "academic_year": sem.academic_year,
        "sgpa": sem.sgpa,
        "total_credits": sem.total_credits,
        "credits_earned": sem.credits_earned,
        "is_complete": sem.is_complete,
        "created_at": sem.created_at.isoformat() if sem.created_at else None,
        "subjects": [serialize_subject(s) for s in sem.subjects]
    }


# ==================== API Endpoints ====================

@router.get("/me", response_model=StudentProfileResponse)
async def get_my_profile(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get current student's profile"""
    return await get_student_profile(current_user)


@router.get("/me/full")
async def get_full_profile(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get FULL student profile INCLUDING semester records, SGPA trend, weaknesses.
    This is the SINGLE SOURCE OF TRUTH for the student dashboard and performance charts.
    """
    try:
        if not current_user or not hasattr(current_user, 'uid'):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

        user_id = str(current_user.uid)
        profile = await StudentProfile.find_one({"user_id": user_id})

        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")

        # Auto-update semester
        academic_details = calculate_academic_details(profile.admission_year)
        if profile.current_semester != academic_details["current_semester"]:
            profile.current_semester = academic_details["current_semester"]
            profile.current_academic_year = academic_details["current_academic_year"]
            profile.last_updated = datetime.now()
            await profile.save()

        # Build sorted completed semesters
        completed_semesters = sorted(
            [s for s in profile.semester_records if s.is_complete],
            key=lambda x: x.semester_number
        )

        sgpa_values = [s.sgpa for s in completed_semesters]

        # Trend calculation
        if len(sgpa_values) >= 2:
            trend = "improving" if sgpa_values[-1] > sgpa_values[-2] else ("declining" if sgpa_values[-1] < sgpa_values[-2] else "stable")
        else:
            trend = "stable"

        latest_sgpa = sgpa_values[-1] if sgpa_values else 0.0
        previous_sgpa = sgpa_values[-2] if len(sgpa_values) >= 2 else latest_sgpa
        percentage_change = round(((latest_sgpa - previous_sgpa) / previous_sgpa) * 100, 2) if previous_sgpa > 0 else 0.0

        # Weakness detection
        weaknesses = []
        for sem in completed_semesters:
            for sub in sem.subjects:
                if sub.grade in ("F", "P", "C") or sub.grade_points <= 5:
                    weaknesses.append({
                        "subject": sub.subject_name,
                        "subject_code": sub.subject_code,
                        "semester": sem.semester_number,
                        "grade": sub.grade,
                        "total_marks": sub.total_marks,
                        "severity": "critical" if sub.grade == "F" else ("high" if sub.grade == "P" else "medium")
                    })

        return {
            "user_id": profile.user_id,
            "name": profile.name,
            "roll_number": profile.roll_number,
            "email": profile.email,
            "branch": profile.branch,
            "admission_year": profile.admission_year,
            "current_semester": profile.current_semester,
            "current_academic_year": profile.current_academic_year,
            "cgpa": profile.cgpa,
            "total_credits_earned": profile.total_credits_earned,
            "total_credits_required": profile.total_credits_required,
            "interests": profile.interests or [],
            "skills": profile.skills or [],
            "career_goals": profile.career_goals or [],
            "latest_sgpa": latest_sgpa,
            "previous_sgpa": previous_sgpa,
            "trend": trend,
            "percentage_change": percentage_change,
            "semester_records": [serialize_semester(s) for s in profile.semester_records],
            "completed_semesters_count": len(completed_semesters),
            "sgpa_trend": [
                {
                    "semester": s.semester_number,
                    "sgpa": s.sgpa,
                    "credits": s.credits_earned,
                    "academic_year": s.academic_year,
                    "subjects_count": len(s.subjects)
                }
                for s in completed_semesters
            ],
            "weaknesses": weaknesses,
            "weakness_count": len(weaknesses),
            "completion_percentage": round(
                (profile.total_credits_earned / profile.total_credits_required) * 100, 1
            ) if profile.total_credits_required > 0 else 0,
            "last_updated": profile.last_updated.isoformat() if profile.last_updated else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching full profile: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/create", response_model=StudentProfileResponse)
async def create_profile_shortcut(
    profile_data: StudentProfileCreate,
    current_user: FirebaseUser = Depends(get_current_user)
):
    return await create_student_profile(profile_data, current_user)


@router.get("/profile", response_model=StudentProfileResponse)
async def get_student_profile(
    current_user: FirebaseUser = Depends(get_current_user)
):
    try:
        if not current_user or not hasattr(current_user, 'uid'):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

        user_id = str(current_user.uid)
        profile = await StudentProfile.find_one({"user_id": user_id})

        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")

        academic_details = calculate_academic_details(profile.admission_year)
        if profile.current_semester != academic_details["current_semester"]:
            profile.current_semester = academic_details["current_semester"]
            profile.current_academic_year = academic_details["current_academic_year"]
            profile.last_updated = datetime.now()
            await profile.save()

        return profile_to_response(profile)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching profile: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/profile/create", response_model=StudentProfileResponse)
async def create_student_profile(
    profile_data: StudentProfileCreate,
    current_user: FirebaseUser = Depends(get_current_user)
):
    try:
        if not current_user or not hasattr(current_user, 'uid'):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

        user_id = str(current_user.uid)
        user_email = str(current_user.email) if hasattr(current_user, 'email') and current_user.email else ""
        academic_details = calculate_academic_details(profile_data.admission_year)

        existing_profile = await StudentProfile.find_one({"user_id": user_id})

        if existing_profile:
            existing_profile.name = profile_data.name
            existing_profile.roll_number = profile_data.roll_number
            existing_profile.branch = profile_data.branch
            existing_profile.admission_year = profile_data.admission_year
            existing_profile.email = profile_data.email or user_email
            existing_profile.current_semester = academic_details["current_semester"]
            existing_profile.current_academic_year = academic_details["current_academic_year"]
            existing_profile.last_updated = datetime.now()
            await existing_profile.save()
            return profile_to_response(existing_profile)

        new_profile = StudentProfile(
            user_id=user_id,
            name=profile_data.name,
            roll_number=profile_data.roll_number,
            branch=profile_data.branch,
            admission_year=profile_data.admission_year,
            email=profile_data.email or user_email,
            current_semester=academic_details["current_semester"],
            current_academic_year=academic_details["current_academic_year"],
            cgpa=0.0, total_credits_earned=0, total_credits_required=160,
            semester_records=[], skills=[], interests=[], career_goals=[],
            created_at=datetime.now(), last_updated=datetime.now()
        )
        await new_profile.insert()
        return profile_to_response(new_profile)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating profile: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/profile/update", response_model=StudentProfileResponse)
async def update_student_profile(
    profile_data: StudentProfileCreate,
    current_user: FirebaseUser = Depends(get_current_user)
):
    try:
        user_id = str(current_user.uid)
        profile = await StudentProfile.find_one({"user_id": user_id})
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

        academic_details = calculate_academic_details(profile_data.admission_year)
        profile.name = profile_data.name
        profile.roll_number = profile_data.roll_number
        profile.branch = profile_data.branch
        profile.admission_year = profile_data.admission_year
        profile.email = profile_data.email or (current_user.email if hasattr(current_user, 'email') else "")
        profile.current_semester = academic_details["current_semester"]
        profile.current_academic_year = academic_details["current_academic_year"]
        profile.last_updated = datetime.now()
        await profile.save()
        return profile_to_response(profile)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/profile/delete")
async def delete_student_profile(current_user: FirebaseUser = Depends(get_current_user)):
    try:
        user_id = str(current_user.uid)
        profile = await StudentProfile.find_one({"user_id": user_id})
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
        await profile.delete()
        return {"message": "Profile deleted successfully", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting profile: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/profile/academic-details")
async def get_academic_details(current_user: FirebaseUser = Depends(get_current_user)):
    try:
        user_id = str(current_user.uid)
        profile = await StudentProfile.find_one({"user_id": user_id})
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

        academic_details = calculate_academic_details(profile.admission_year)
        return {
            "user_id": user_id,
            "current_semester": academic_details["current_semester"],
            "academic_year": academic_details["current_academic_year"],
            "admission_year": profile.admission_year,
            "branch": profile.branch,
            "cgpa": profile.cgpa,
            "total_credits_earned": profile.total_credits_earned,
            "calculated_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/profile/check")
async def check_profile_exists(current_user: FirebaseUser = Depends(get_current_user)):
    try:
        user_id = str(current_user.uid)
        profile = await StudentProfile.find_one({"user_id": user_id})
        return {"exists": profile is not None, "user_id": user_id, "profile_id": str(profile.id) if profile else None}
    except Exception as e:
        return {"exists": False, "user_id": str(current_user.uid) if current_user else "unknown", "error": str(e)}