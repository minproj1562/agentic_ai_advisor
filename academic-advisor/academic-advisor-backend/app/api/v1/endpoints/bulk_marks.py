#academic-advisor/academic-advisor-backend/app/api/v1/endpoints/bulk_marks.py
"""
Bulk Marks Upload API — University Marksheet Format
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional
import logging, io, json

from app.dependencies import get_admin_user
from app.core.security import FirebaseUser
from app.services.bulk_marks_service import bulk_marks_service

logger = logging.getLogger(__name__)
router = APIRouter()


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
    # Parse elective choices (handle both JSON and simple format)
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


@router.get("/students")
async def get_students_for_upload(
    branch: str = Query(...),
    admission_year: Optional[int] = Query(None),
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """
    Get list of students for a branch (used by frontend to show pre-fill preview).
    """
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
                admin_email=current_user.email  # Pass admin email
            )
        else:
            result = await bulk_marks_service.preview(parsed, semester, branch, academic_year)
    except Exception as e:
        logger.error(f"Process: {e}", exc_info=True)
        raise HTTPException(500, f"Processing failed: {e}")

    return {"success": True, "mode": "save" if save else "preview", "metadata": meta, **result.to_dict()}

@router.get("/pending-marks")
async def get_pending_marks(
    branch: Optional[str] = Query(None),
    current_user: FirebaseUser = Depends(get_admin_user),
):
    """Get summary of pending marks (students not yet registered)"""
    summary = await pending_marks_service.get_pending_marks_summary(branch)
    return summary

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