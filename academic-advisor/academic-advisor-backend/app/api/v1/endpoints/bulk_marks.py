# academic-advisor-backend/app/api/v1/endpoints/bulk_marks.py
"""
Bulk Marks Upload API — University Marksheet Format
COMPLETE FIXED VERSION — includes View/Edit endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional, List
import logging, io, json
from datetime import datetime

from app.dependencies import get_admin_user
from app.core.security import FirebaseUser
from app.services.bulk_marks_service import bulk_marks_service, calculate_grade
from app.services.pending_marks_service import pending_marks_service
from app.models.pending_marks import PendingStudentMarks
from app.models.student_profile import StudentProfile, SubjectScore
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


# ═══════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════

class StudentInput(BaseModel):
    roll_number: str
    name: str
    seat_number: Optional[str] = None
    email: Optional[str] = None


class AddStudentsRequest(BaseModel):
    students: List[StudentInput]
    branch: str
    admission_year: int


class UpdateSubjectMarks(BaseModel):
    subject_code: str
    internal_marks: float = 0
    external_marks: float = 0


class UpdateStudentMarksRequest(BaseModel):
    semester: int
    academic_year: str
    subjects: List[UpdateSubjectMarks]


# ═══════════════════════════════════════════════════════════
# TEMPLATE ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/template")
async def download_template(
    semester: int = Query(..., ge=1, le=8),
    branch: str = Query(...),
    academic_year: str = Query("2024-25"),
    admission_year: int = Query(2022, ge=2018, le=2030),
    prefill_students: bool = Query(True, description="Pre-fill with existing student roll numbers"),
    elective_choices: Optional[str] = Query(
        None,
        description='JSON: {"PEC1":"ITPEC5014"} or simple: PEC1=ITPEC5014'
    ),
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """
    Download university-format XLSX template.
    If prefill_students=true (default), student roll numbers and names
    from the database are pre-filled in the template.
    """
    ec = None
    if elective_choices:
        try:
            ec = json.loads(elective_choices)
        except json.JSONDecodeError:
            ec = {}
            for pair in elective_choices.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    ec[k.strip()] = v.strip()

    try:
        if prefill_students:
            buf = await bulk_marks_service.generate_template_with_students(
                semester=semester,
                branch=branch,
                academic_year=academic_year,
                admission_year=admission_year,
                elective_choices=ec,
                prefill_branch=branch,
            )
        else:
            buf = bulk_marks_service.generate_template(
                semester=semester,
                branch=branch,
                academic_year=academic_year,
                admission_year=admission_year,
                elective_choices=ec,
            )

        fname = f"marks_sem{semester}_{branch}_{academic_year.replace('-', '_')}.xlsx"
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Template error: {e}", exc_info=True)
        raise HTTPException(500, f"Template generation failed: {e}")


@router.get("/templates/all")
async def download_all_templates(
    branch: str = Query(...),
    academic_year: str = Query("2024-25"),
    admission_year: int = Query(2022, ge=2018, le=2030),
    semesters: Optional[str] = Query(None, description="Comma-separated list of semesters, e.g., '1,2,3,4,5'"),
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """Download templates for multiple semesters as a ZIP file."""
    try:
        sem_list = None
        if semesters:
            sem_list = [int(s.strip()) for s in semesters.split(",") if s.strip().isdigit()]
            sem_list = [s for s in sem_list if 1 <= s <= 8]

        zip_buffer = await bulk_marks_service.generate_all_semester_templates(
            branch=branch,
            academic_year=academic_year,
            admission_year=admission_year,
            semesters=sem_list,
        )

        fname = f"marks_templates_{branch}_{admission_year}_{academic_year.replace('-', '_')}.zip"
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )
    except Exception as e:
        logger.error(f"Batch template error: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@router.get("/download-marks-template")
async def download_marks_template(
    semester: int = Query(..., ge=1, le=8),
    branch: str = Query(...),
    academic_year: str = Query("2024-25"),
    admission_year: int = Query(2022, ge=2018, le=2030),
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """
    Download template PRE-FILLED with existing marks data.
    Admin can edit in Excel and re-upload to update marks.
    """
    try:
        buf = await bulk_marks_service.generate_template_with_marks(
            semester=semester,
            branch=branch,
            academic_year=academic_year,
            admission_year=admission_year,
        )

        fname = (
            f"marks_edit_sem{semester}_{branch}_"
            f"{academic_year.replace('-', '_')}.xlsx"
        )
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Download marks template error: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to generate marks template: {str(e)}")


# ═══════════════════════════════════════════════════════════
# STUDENT MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/students")
async def get_students_for_upload(
    branch: str = Query(...),
    admission_year: Optional[int] = Query(None),
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """Get list of students for a branch."""
    try:
        students = await bulk_marks_service.get_students_for_template(
            branch=branch,
            admission_year=admission_year,
        )
        return {
            "students": students,
            "total": len(students),
            "branch": branch,
            "admission_year": admission_year,
        }
    except Exception as e:
        logger.error(f"Student fetch error: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@router.get("/students/summary")
async def get_students_summary(
    branch: Optional[str] = Query(None),
    admission_year: Optional[int] = Query(None),
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """Get summary of students grouped by branch and admission year."""
    try:
        summary = await bulk_marks_service.get_students_summary(
            branch=branch,
            admission_year=admission_year,
        )
        return summary
    except Exception as e:
        logger.error(f"Student summary error: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@router.post("/students/add")
async def add_students(
    request: AddStudentsRequest,
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """Add multiple students to the database."""
    try:
        result = await bulk_marks_service.add_students_batch(
            students_data=[s.model_dump() for s in request.students],
            branch=request.branch,
            admission_year=request.admission_year,
        )
        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Add students error: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@router.get("/students/export")
async def export_students(
    branch: str = Query(...),
    admission_year: Optional[int] = Query(None),
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """Export student list to Excel file."""
    try:
        excel_buffer = await bulk_marks_service.export_students_to_excel(
            branch=branch,
            admission_year=admission_year,
        )

        fname = f"students_{branch}"
        if admission_year:
            fname += f"_{admission_year}"
        fname += ".xlsx"

        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )
    except Exception as e:
        logger.error(f"Export students error: {e}", exc_info=True)
        raise HTTPException(500, str(e))


# ═══════════════════════════════════════════════════════════
# UPLOAD / PARSE ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.post("/upload")
async def upload_marks(
    file: UploadFile = File(...),
    semester: int = Form(..., ge=1, le=8),
    branch: str = Form(...),
    academic_year: str = Form(...),
    admission_year: int = Form(..., ge=2018, le=2030),
    save: bool = Form(False),
    overwrite: bool = Form(True),
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """
    Upload XLS/XLSX/CSV → parse university format → preview or save.
    Mapping:  CA → internal_marks,  MSE+ESE → external_marks
    """
    if not file.filename:
        raise HTTPException(400, "No file")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("xls", "xlsx", "csv"):
        raise HTTPException(400, f"Unsupported .{ext} — use .xlsx/.xls/.csv")

    content = await file.read()
    if not content:
        raise HTTPException(400, "Empty file")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 10 MB)")

    try:
        parsed, meta = bulk_marks_service.parse_file(
            content, file.filename, semester, branch, academic_year, admission_year,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Parse: {e}", exc_info=True)
        raise HTTPException(400, f"Parse failed: {e}")

    if not parsed:
        raise HTTPException(400, "No student rows found")

    try:
        if save:
            result = await bulk_marks_service.save(
                parsed, semester, academic_year, branch, overwrite,
                admin_email=current_user.email
            )
        else:
            result = await bulk_marks_service.preview(parsed, semester, branch, academic_year)
    except Exception as e:
        logger.error(f"Process: {e}", exc_info=True)
        raise HTTPException(500, f"Processing failed: {e}")

    return {"success": True, "mode": "save" if save else "preview", "metadata": meta, **result.to_dict()}


@router.post("/convert-csv")
async def convert_to_csv(
    file: UploadFile = File(...),
    semester: int = Form(..., ge=1, le=8),
    branch: str = Form(...),
    academic_year: str = Form("2024-25"),
    admission_year: int = Form(2022),
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """Convert XLS/XLSX → normalised CSV (no saving)."""
    content = await file.read()
    if not content:
        raise HTTPException(400, "Empty file")
    try:
        parsed, _ = bulk_marks_service.parse_file(
            content, file.filename or "upload.xlsx",
            semester, branch, academic_year, admission_year,
        )
    except Exception as e:
        raise HTTPException(400, str(e))

    csv_str = bulk_marks_service.to_csv(parsed)
    buf = io.BytesIO(csv_str.encode("utf-8"))
    return StreamingResponse(
        buf, media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="marks_sem{semester}_{branch}.csv"'},
    )


# ═══════════════════════════════════════════════════════════
# VIEW / EDIT MARKS ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/semester-marks")
async def get_semester_marks(
    semester: int = Query(..., ge=1, le=8),
    branch: str = Query(...),
    admission_year: int = Query(2022, ge=2018, le=2030),
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """
    Get all students' marks for a specific semester.
    Used by admin to view and edit marks inline.
    """
    try:
        query_filter = {
            "branch": {"$regex": f"^{branch}$", "$options": "i"},
            "admission_year": admission_year,
        }

        students = await StudentProfile.find(query_filter).sort("roll_number").to_list()

        results = []
        for student in students:
            sem_record = None
            for sr in student.semester_records:
                if sr.semester_number == semester:
                    sem_record = sr
                    break

            student_data = {
                "roll_number": student.roll_number,
                "name": student.name,
                "user_id": student.user_id,
                "is_placeholder": student.user_id.startswith("pending_"),
                "has_marks": sem_record is not None,
                "semester_data": None,
            }

            if sem_record:
                student_data["semester_data"] = {
                    "semester_number": sem_record.semester_number,
                    "academic_year": sem_record.academic_year,
                    "sgpa": sem_record.sgpa,
                    "total_credits": sem_record.total_credits,
                    "credits_earned": sem_record.credits_earned,
                    "is_complete": sem_record.is_complete,
                    "subjects": [
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
                            "is_practical": s.is_practical,
                        }
                        for s in sem_record.subjects
                    ],
                }

            results.append(student_data)

        # Also check pending marks for unlinked students
        pending_data = []
        try:
            pending = await PendingStudentMarks.find({
                "semester_number": semester,
                "branch": {"$regex": f"^{branch}$", "$options": "i"},
                "linked_to_profile": False,
            }).to_list()

            pending_data = [
                {
                    "roll_number": p.roll_number,
                    "student_name": p.student_name,
                    "semester_number": p.semester_number,
                    "sgpa": p.sgpa,
                    "subjects_count": len(p.subjects),
                    "uploaded_by": p.uploaded_by,
                    "upload_timestamp": str(p.upload_timestamp),
                }
                for p in pending
            ]
        except Exception as e:
            logger.warning(f"Could not fetch pending marks: {e}")

        students_with_marks = [r for r in results if r["has_marks"]]
        students_without_marks = [r for r in results if not r["has_marks"]]

        return {
            "semester": semester,
            "branch": branch,
            "admission_year": admission_year,
            "total_students": len(results),
            "students_with_marks": len(students_with_marks),
            "students_without_marks": len(students_without_marks),
            "students": results,
            "unlinked_pending": pending_data,
        }
    except Exception as e:
        logger.error(f"Get semester marks error: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to load semester marks: {str(e)}")


@router.put("/student-marks/{roll_number}")
async def update_student_marks(
    roll_number: str,
    request: UpdateStudentMarksRequest,
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """
    Update marks for a specific student inline.
    Recalculates grades, SGPA, and CGPA automatically.
    """
    try:
        from app.core.curriculum import get_semester_subjects

        profile = await bulk_marks_service._find_profile(roll_number)
        if not profile:
            raise HTTPException(404, f"Student {roll_number} not found")

        # Find the semester record
        sem_idx = next(
            (i for i, sr in enumerate(profile.semester_records)
             if sr.semester_number == request.semester),
            None,
        )

        if sem_idx is None:
            raise HTTPException(
                404,
                f"No marks for semester {request.semester} for {roll_number}"
            )

        sem_record = profile.semester_records[sem_idx]

        # Update each subject
        for update in request.subjects:
            subj_idx = next(
                (i for i, s in enumerate(sem_record.subjects)
                 if s.subject_code == update.subject_code),
                None,
            )

            if subj_idx is None:
                logger.warning(
                    f"Subject {update.subject_code} not found for {roll_number}"
                )
                continue

            subj = sem_record.subjects[subj_idx]
            subj.internal_marks = update.internal_marks
            subj.external_marks = update.external_marks
            subj.total_marks = update.internal_marks + update.external_marks

            # Recalculate grade
            max_marks = 100.0
            try:
                curriculum_subjects = get_semester_subjects(
                    request.semester, profile.admission_year
                )
                for cs in curriculum_subjects:
                    if cs.subject_code == update.subject_code:
                        max_marks = float(cs.internal_max + cs.external_max)
                        break
            except Exception:
                pass

            gi = calculate_grade(subj.total_marks, max_marks)
            subj.grade = gi["grade"]
            subj.grade_points = gi["points"]

        # Recalculate SGPA for this semester
        tgp = tc = ce = 0.0
        for s in sem_record.subjects:
            c = float(s.credits)
            tc += c
            if s.grade != "F":
                tgp += s.grade_points * c
                ce += c

        sem_record.sgpa = round(tgp / tc, 2) if tc > 0 else 0.0
        sem_record.credits_earned = int(ce)
        sem_record.total_credits = int(tc)

        profile.semester_records[sem_idx] = sem_record

        # Recalculate CGPA across all semesters
        agp = ac = ace = 0.0
        for sr in profile.semester_records:
            if sr.is_complete and sr.total_credits > 0:
                agp += sr.sgpa * sr.total_credits
                ac += sr.total_credits
                ace += sr.credits_earned

        profile.cgpa = round(agp / ac, 2) if ac > 0 else 0.0
        profile.total_credits_earned = int(ace)
        profile.last_updated = datetime.now()
        profile.marks_synced_at = datetime.now()
        profile.pending_marks_checked = False

        await profile.replace()

        # Also update pending marks if they exist
        try:
            pending = await PendingStudentMarks.find_one({
                "roll_number": roll_number,
                "semester_number": request.semester,
            })
            if pending:
                pending.subjects = sem_record.subjects
                pending.sgpa = sem_record.sgpa
                pending.total_credits = sem_record.total_credits
                pending.credits_earned = sem_record.credits_earned
                pending.upload_timestamp = datetime.now()
                pending.linked_to_profile = False
                await pending.replace()
        except Exception as e:
            logger.warning(f"Could not update pending marks: {e}")

        logger.info(
            f"✅ Admin updated marks for {roll_number}: "
            f"Sem {request.semester} SGPA={sem_record.sgpa}, CGPA={profile.cgpa}"
        )

        return {
            "success": True,
            "roll_number": roll_number,
            "semester": request.semester,
            "updated_sgpa": sem_record.sgpa,
            "updated_cgpa": profile.cgpa,
            "subjects_updated": len(request.subjects),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update marks error: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to update marks: {str(e)}")


# ═══════════════════════════════════════════════════════════
# PENDING MARKS ENDPOINT
# ═══════════════════════════════════════════════════════════

@router.get("/pending-marks")
async def get_pending_marks(
    branch: Optional[str] = Query(None),
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """Get summary of pending marks (students not yet registered)"""
    try:
        summary = await pending_marks_service.get_pending_marks_summary(branch)
        return summary
    except Exception as e:
        logger.error(f"Pending marks error: {e}", exc_info=True)
        raise HTTPException(500, str(e))