# academic-advisor/academic-advisor-backend/app/api/v1/admin.py
"""
Admin API endpoints
Provides admin-only access to system-wide data, user management, and curriculum editing.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from datetime import datetime

from app.dependencies import get_admin_user
from app.core.security import FirebaseUser
from app.services.admin_service import AdminService
from app.utils.helpers import get_logger

logger = get_logger(__name__)
router = APIRouter()

admin_service = AdminService()


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
    semester: Optional[int] = None,
    batch: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("updated_at", regex="^(name|cgpa|semester|updated_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    skip: int = Query(0, ge=0),
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
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
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


# ==================== CURRICULUM MANAGEMENT ====================

@router.get("/curriculum")
async def get_curriculum(
    semester: Optional[int] = Query(None, ge=1, le=8),
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
    
# app/api/v1/admin.py
# ADD these endpoints

from fastapi import UploadFile, File
import pandas as pd
import io

@router.post("/students/bulk-upload")
async def bulk_upload_students(
    file: UploadFile = File(...),
    current_user: FirebaseUser = Depends(get_admin_user)
):
    """
    Bulk upload students from Excel file.
    
    Expected columns:
    - Name (required)
    - Roll Number (required)
    - Email (required)
    - Department/Branch (required)
    - Admission Year (optional, extracted from roll if missing)
    - Current Semester (optional, calculated if missing)
    - Seat Number (optional)
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be Excel (.xlsx, .xls) or CSV (.csv)"
            )
        
        # Read file
        contents = await file.read()
        
        # Parse based on file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # Normalize column names (case-insensitive, strip spaces)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Map common column variations
        column_mapping = {
            'roll_no': 'roll_number',
            'rollno': 'roll_number',
            'roll': 'roll_number',
            'dept': 'branch',
            'department': 'branch',
            'sem': 'current_semester',
            'semester': 'current_semester',
            'year': 'admission_year',
            'adm_year': 'admission_year',
        }
        
        df.rename(columns=column_mapping, inplace=True)
        
        # Convert DataFrame to list of dicts
        students_data = df.to_dict('records')
        
        # Clean None/NaN values
        for student in students_data:
            for key, value in list(student.items()):
                if pd.isna(value):
                    student[key] = None
        
        # Bulk create
        result = await admin_service.bulk_create_students(students_data)
        
        return {
            "message": f"Processed {result['total_processed']} students",
            "summary": {
                "created": result['created'],
                "skipped": result['skipped'],
                "errors": result['errors'],
            },
            "details": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk upload error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )


@router.get("/students/export-template")
async def download_student_template(
    current_user: FirebaseUser = Depends(get_admin_user)
):
    """
    Download Excel template for bulk student upload.
    """
    try:
        import pandas as pd
        from fastapi.responses import StreamingResponse
        
        # Create template DataFrame
        template_data = {
            "Name": ["John Doe", "Jane Smith"],
            "Roll Number": ["5023152", "5023153"],
            "Email": ["john@college.edu", "jane@college.edu"],
            "Branch": ["IT", "COMP"],
            "Admission Year": [2023, 2023],
            "Current Semester": [3, 3],
            "Seat Number": ["69261", "69262"]  # Optional
        }
        
        df = pd.DataFrame(template_data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Students')
            
            # Add instructions sheet
            instructions = pd.DataFrame({
                "Field": ["Name", "Roll Number", "Email", "Branch", "Admission Year", "Current Semester", "Seat Number"],
                "Required": ["Yes", "Yes", "Yes", "Yes", "No*", "No*", "No"],
                "Description": [
                    "Full name of student",
                    "7-digit roll number (e.g., 5023152)",
                    "College email address",
                    "Department code (IT, COMP, EXTC, MECH, ELEC)",
                    "Year of admission (auto-extracted from roll if not provided)",
                    "Current semester (1-8) (auto-calculated if not provided)",
                    "5-digit seat number for exam (changes each semester)"
                ]
            })
            instructions.to_excel(writer, index=False, sheet_name='Instructions')
        
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=student_upload_template.xlsx"
            }
        )
        
    except Exception as e:
        logger.error(f"Template download error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate template"
        )