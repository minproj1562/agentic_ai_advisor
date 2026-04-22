# academic-advisor/academic-advisor-backend/app/api/v1/admin.py
"""
Admin API endpoints
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime

from app.dependencies import get_admin_user
from app.core.security import FirebaseUser
from app.services.admin_service import (
    AdminService,
    APPROVED_FACULTY_EMAILS,
    _is_valid_faculty_email,
    FACULTY_EMAIL_DOMAIN,
)
from app.utils.helpers import get_logger

logger = get_logger(__name__)
router = APIRouter()

admin_service = AdminService()


# ==================== REQUEST SCHEMAS ====================

class CreateFacultyRequest(BaseModel):
    """
    Request body for POST /admin/faculty/create

    Password is NO LONGER sent from the frontend.
    The backend always uses DEFAULT_FACULTY_PASSWORD ("Fcrit@123").

    All fields are validated before the service layer is called
    so that Firebase Auth is never touched for obviously bad input.
    """
    email:       EmailStr
    name:        str
    department:  str
    designation: str = "Assistant Professor"

    @field_validator("email")
    @classmethod
    def must_be_fcrit_email(cls, v: str) -> str:
        normalised = v.lower().strip()
        if not _is_valid_faculty_email(normalised):
            raise ValueError(
                f"Faculty email must be in the format "
                f"firstname.lastname{FACULTY_EMAIL_DOMAIN}. "
                f"Example: poonam.bari@fcrit.ac.in"
            )
        return normalised

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v

    @field_validator("department")
    @classmethod
    def department_not_empty(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Department cannot be empty")
        return v


# ==================== DASHBOARD STATS ====================

@router.get("/stats")
async def get_admin_stats(
    current_user: FirebaseUser = Depends(get_admin_user)
):
    """Get system-wide dashboard statistics"""
    try:
        stats = await admin_service.get_dashboard_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching admin stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")


# ==================== STUDENT MANAGEMENT ====================

@router.get("/students")
async def list_all_students(
    department: Optional[str] = None,
    semester:   Optional[int] = None,
    batch:      Optional[str] = None,
    search:     Optional[str] = None,
    sort_by:    str = Query("updated_at", pattern="^(name|cgpa|semester|updated_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    skip:  int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    current_user: FirebaseUser = Depends(get_admin_user)
):
    """List all students with optional filters"""
    try:
        result = await admin_service.get_all_students(
            department=department,
            semester=semester,
            batch=batch,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            skip=skip,
            limit=limit,
        )
        return result
    except Exception as e:
        logger.error(f"Error listing students: {e}")
        raise HTTPException(status_code=500, detail="Failed to list students")


@router.get("/students/{uid}")
async def get_student_detail(
    uid: str,
    current_user: FirebaseUser = Depends(get_admin_user)
):
    """Get detailed student data including performance, projects, weaknesses"""
    try:
        detail = await admin_service.get_student_detail(uid)
        if not detail:
            raise HTTPException(status_code=404, detail="Student not found")
        return detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student {uid}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch student")


# ==================== FACULTY MANAGEMENT ====================

@router.get("/faculty")
async def list_all_faculty(
    department: Optional[str] = None,
    status:     Optional[str] = None,
    search:     Optional[str] = None,
    skip:  int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    current_user: FirebaseUser = Depends(get_admin_user)
):
    """List all faculty members"""
    try:
        result = await admin_service.get_all_faculty(
            department=department,
            status=status,
            search=search,
            skip=skip,
            limit=limit,
        )
        return result
    except Exception as e:
        logger.error(f"Error listing faculty: {e}")
        raise HTTPException(status_code=500, detail="Failed to list faculty")


@router.get("/faculty/{uid}")
async def get_faculty_detail(
    uid: str,
    current_user: FirebaseUser = Depends(get_admin_user)
):
    """Get detailed faculty profile"""
    try:
        detail = await admin_service.get_faculty_detail(uid)
        if not detail:
            raise HTTPException(status_code=404, detail="Faculty not found")
        return detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching faculty {uid}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch faculty")


@router.post("/faculty/create")
async def create_faculty_account(
    payload: CreateFacultyRequest,
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """
    Create a new faculty account.

    Password is NOT accepted from the frontend.
    The backend always sets the default password (Fcrit@123).
    The faculty member is required to change it on first login
    via the must_change_password flag set in Firestore.

    • Validates email format (firstname.lastname@fcrit.ac.in).
    • Warns (but does NOT block) if the email is not in the
      pre-approved list — admins can still onboard new staff.
    • Creates Firebase Auth user with DEFAULT_FACULTY_PASSWORD.
    • Creates Firestore 'users' document with must_change_password=True.
    • Creates MongoDB Faculty document via Beanie.

    Request body
    ------------
    ```json
    {
      "email":       "poonam.bari@fcrit.ac.in",
      "name":        "Poonam Bari",
      "department":  "IT",
      "designation": "Assistant Professor"
    }
    ```

    Response (201)
    --------------
    ```json
    {
      "uid":                  "<firebase-uid>",
      "mongo_id":             "<mongodb-object-id>",
      "email":                "poonam.bari@fcrit.ac.in",
      "name":                 "Poonam Bari",
      "department":           "IT",
      "designation":          "Assistant Professor",
      "is_approved_email":    true,
      "status":               "pending_setup",
      "default_password":     "Fcrit@123",
      "must_change_password": true,
      "created_at":           "2025-01-01T00:00:00"
    }
    ```
    """
    try:
        result = await admin_service.create_faculty_account(
            email=payload.email,
            name=payload.name,
            department=payload.department,
            designation=payload.designation,
        )

        logger.info(
            "Admin %s created faculty account: %s (dept=%s)",
            current_user.uid,
            payload.email,
            payload.department,
        )

        from fastapi.responses import JSONResponse
        return JSONResponse(content=result, status_code=201)

    except ValueError as ve:
        error_msg = str(ve)
        logger.warning(
            "Faculty creation rejected for %s: %s",
            payload.email,
            error_msg,
        )
        if "already exists" in error_msg.lower():
            raise HTTPException(status_code=409, detail=error_msg)
        raise HTTPException(status_code=422, detail=error_msg)

    except Exception as e:
        logger.error(
            "Unexpected error creating faculty %s: %s",
            payload.email,
            e,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to create faculty account. Please try again.",
        )


@router.get("/faculty/approved-emails")
async def get_approved_faculty_emails(
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """
    Return the list of pre-approved faculty email addresses.
    Useful for the admin UI to show which emails are already
    whitelisted vs. new additions.
    """
    return {
        "approved_emails": sorted(APPROVED_FACULTY_EMAILS),
        "total":           len(APPROVED_FACULTY_EMAILS),
        "domain":          FACULTY_EMAIL_DOMAIN,
    }


# ==================== CURRICULUM MANAGEMENT ====================

@router.get("/curriculum")
async def get_curriculum(
    semester:       Optional[int] = Query(None, ge=1, le=8),
    admission_year: int = Query(2024, ge=2020, le=2030),
    current_user: FirebaseUser = Depends(get_admin_user)
):
    """Get curriculum subjects for a semester"""
    try:
        data = await admin_service.get_curriculum(
            semester=semester,
            admission_year=admission_year,
        )
        return data
    except Exception as e:
        logger.error(f"Error fetching curriculum: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch curriculum")


@router.get("/curriculum/electives")
async def get_elective_options(
    current_user: FirebaseUser = Depends(get_admin_user)
):
    """Get all elective groups and their options"""
    try:
        return await admin_service.get_all_elective_options()
    except Exception as e:
        logger.error(f"Error fetching electives: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch electives")


@router.put("/curriculum/electives/{elective_id}")
async def update_elective(
    elective_id: str,
    update_data: dict = Body(...),
    current_user: FirebaseUser = Depends(get_admin_user)
):
    """Update an elective course"""
    try:
        result = await admin_service.update_elective(elective_id, update_data)
        return {"message": "Elective updated", "data": result}
    except Exception as e:
        logger.error(f"Error updating elective: {e}")
        raise HTTPException(status_code=500, detail="Failed to update elective")


@router.post("/curriculum/electives")
async def create_elective(
    elective_data: dict = Body(...),
    current_user: FirebaseUser = Depends(get_admin_user)
):
    """Create a new elective course"""
    try:
        result = await admin_service.create_elective(elective_data)
        return {"message": "Elective created", "data": result}
    except Exception as e:
        logger.error(f"Error creating elective: {e}")
        raise HTTPException(status_code=500, detail="Failed to create elective")


@router.delete("/curriculum/electives/{elective_id}")
async def delete_elective(
    elective_id: str,
    current_user: FirebaseUser = Depends(get_admin_user)
):
    """Delete an elective course"""
    try:
        await admin_service.delete_elective(elective_id)
        return {"message": "Elective deleted"}
    except Exception as e:
        logger.error(f"Error deleting elective: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete elective")


# ==================== ANALYTICS ====================

@router.get("/analytics/overview")
async def get_analytics_overview(
    current_user: FirebaseUser = Depends(get_admin_user)
):
    """Get system-wide analytics"""
    try:
        return await admin_service.get_analytics_overview()
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")


@router.get("/analytics/department-comparison")
async def get_department_comparison(
    current_user: FirebaseUser = Depends(get_admin_user)
):
    """Get department-wise comparison metrics"""
    try:
        return await admin_service.get_department_comparison()
    except Exception as e:
        logger.error(f"Error fetching department comparison: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch comparison")


# ==================== USER MANAGEMENT ====================

@router.get("/users/counts")
async def get_user_counts(
    current_user: FirebaseUser = Depends(get_admin_user)
):
    """Get user counts by role from Firestore"""
    try:
        return await admin_service.get_user_counts()
    except Exception as e:
        logger.error(f"Error fetching user counts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user counts")