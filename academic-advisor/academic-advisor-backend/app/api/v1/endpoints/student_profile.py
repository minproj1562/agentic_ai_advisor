# app/api/v1/endpoints/student_profile.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.models.student_profile import StudentProfile, SemesterRecord, SubjectScore
from app.core.security import get_current_user, FirebaseUser

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Request/Response Models ====================

class StudentProfileCreate(BaseModel):
    """Request model for creating/updating student profile"""
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
    """Response model for student profile"""
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
    """Calculate current semester and academic year based on admission year"""
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
    """Convert StudentProfile document to response model"""
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


# ==================== API Endpoints ====================

@router.get("/profile", response_model=StudentProfileResponse)
async def get_student_profile(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get student profile by user ID"""
    try:
        # FIXED: Better error handling for uid access
        if not current_user:
            logger.error("❌ No current user provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        if not hasattr(current_user, 'uid'):
            logger.error(f"❌ Current user object doesn't have uid attribute. Type: {type(current_user)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid user object structure"
            )
        
        user_id = str(current_user.uid)  # Ensure it's a string
        logger.info(f"✅ Fetching profile for user: {user_id}")
        
        profile = await StudentProfile.find_one(
            {"user_id": user_id}
            )
        
        if not profile:
            logger.warning(f"⚠️ Profile not found for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found. Please create your profile first."
            )
        
        # Auto-update semester if needed
        academic_details = calculate_academic_details(profile.admission_year)
        
        if profile.current_semester != academic_details["current_semester"]:
            profile.current_semester = academic_details["current_semester"]
            profile.current_academic_year = academic_details["current_academic_year"]
            profile.last_updated = datetime.now()
            await profile.save()
            logger.info(f"✅ Auto-updated semester to {profile.current_semester}")
        
        return profile_to_response(profile)
        
    except HTTPException:
        raise
    except AttributeError as e:
        logger.error(f"❌ AttributeError accessing user data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error accessing user data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Error fetching profile: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching profile: {type(e).__name__}"
        )


@router.post("/profile/create", response_model=StudentProfileResponse)
async def create_student_profile(
    profile_data: StudentProfileCreate,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Create or update student profile"""
    try:
        # FIXED: Better error handling
        if not current_user or not hasattr(current_user, 'uid'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated properly"
            )
        
        user_id = str(current_user.uid)
        user_email = str(current_user.email) if hasattr(current_user, 'email') else ""
        
        logger.info(f"✅ Creating/updating profile for user: {user_id}")
        
        academic_details = calculate_academic_details(profile_data.admission_year)
        
        existing_profile = await StudentProfile.find_one(
            {"user_id": user_id}
    )
        
        if existing_profile:
            # Update existing profile
            existing_profile.name = profile_data.name
            existing_profile.roll_number = profile_data.roll_number
            existing_profile.branch = profile_data.branch
            existing_profile.admission_year = profile_data.admission_year
            existing_profile.email = profile_data.email or user_email
            existing_profile.current_semester = academic_details["current_semester"]
            existing_profile.current_academic_year = academic_details["current_academic_year"]
            existing_profile.last_updated = datetime.now()
            
            await existing_profile.save()
            logger.info(f"✅ Updated existing profile for user: {user_id}")
            
            return profile_to_response(existing_profile)
        
        # Create new profile
        new_profile = StudentProfile(
            user_id=user_id,
            name=profile_data.name,
            roll_number=profile_data.roll_number,
            branch=profile_data.branch,
            admission_year=profile_data.admission_year,
            email=profile_data.email or user_email,
            current_semester=academic_details["current_semester"],
            current_academic_year=academic_details["current_academic_year"],
            cgpa=0.0,
            total_credits_earned=0,
            total_credits_required=160,
            semester_records=[],
            skills=[],
            interests=[],
            career_goals=[],
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        await new_profile.insert()
        logger.info(f"✅ Created new profile for user: {user_id}")
        
        return profile_to_response(new_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating profile: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating profile: {type(e).__name__}"
        )


@router.put("/profile/update", response_model=StudentProfileResponse)
async def update_student_profile(
    profile_data: StudentProfileCreate,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Update student profile"""
    try:
        user_id = str(current_user.uid)
        logger.info(f"✅ Updating profile for user: {user_id}")
        
        profile = await StudentProfile.find_one(
            {"user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )
        
        academic_details = calculate_academic_details(profile_data.admission_year)
        
        profile.name = profile_data.name
        profile.roll_number = profile_data.roll_number
        profile.branch = profile_data.branch
        profile.admission_year = profile_data.admission_year
        profile.email = profile_data.email or current_user.email or ""
        profile.current_semester = academic_details["current_semester"]
        profile.current_academic_year = academic_details["current_academic_year"]
        profile.last_updated = datetime.now()
        
        await profile.save()
        
        return profile_to_response(profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating profile: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {type(e).__name__}"
        )


@router.delete("/profile/delete")
async def delete_student_profile(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Delete student profile"""
    try:
        user_id = str(current_user.uid)
        logger.info(f"✅ Deleting profile for user: {user_id}")
        
        profile = await StudentProfile.find_one(
            {"user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )
        
        await profile.delete()
        
        return {"message": "Profile deleted successfully", "user_id": user_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting profile: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting profile: {type(e).__name__}"
        )


@router.get("/profile/academic-details")
async def get_academic_details(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get calculated academic details for current user"""
    try:
        user_id = str(current_user.uid)
        
        profile = await StudentProfile.find_one(
            {"user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )
        
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
        logger.error(f"❌ Error getting academic details: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting academic details: {type(e).__name__}"
        )


@router.get("/profile/check")
async def check_profile_exists(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Check if profile exists for current user"""
    try:
        user_id = str(current_user.uid)
        
        profile = await StudentProfile.find_one(
            {"user_id": user_id}
        )
        
        return {
            "exists": profile is not None,
            "user_id": user_id,
            "profile_id": str(profile.id) if profile else None
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking profile: {type(e).__name__}: {e}", exc_info=True)
        return {
            "exists": False,
            "user_id": str(current_user.uid) if current_user else "unknown",
            "error": str(e)
        }
