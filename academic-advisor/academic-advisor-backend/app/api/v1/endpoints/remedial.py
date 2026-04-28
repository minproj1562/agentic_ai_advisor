# app/api/v1/endpoints/remedial.py
"""
Remedial Student Management API Endpoints
==========================================
Faculty can add/track/resolve remedial students.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.dependencies import get_current_user
from app.core.security import FirebaseUser
from app.models.remedial import RemedialEntry, RemedialStatus, ProgressNote
from app.models.faculty import Faculty

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/faculty/remedial", tags=["remedial"])


class RemedialCreateRequest(BaseModel):
    student_id: str
    student_name: str = ""
    student_roll: str = ""
    semester: int
    subject: str
    reason: str = ""
    initial_marks: Optional[float] = None
    target_marks: Optional[float] = None


class ProgressNoteRequest(BaseModel):
    note: str
    marks_change: Optional[float] = None


@router.post("")
async def add_remedial(
    req: RemedialCreateRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Add a student as remedial for a subject."""
    faculty = await Faculty.find_one(Faculty.user_id == current_user.uid)
    faculty_name = faculty.name if faculty else ""

    entry = RemedialEntry(
        faculty_id=current_user.uid,
        faculty_name=faculty_name,
        student_id=req.student_id,
        student_name=req.student_name,
        student_roll=req.student_roll,
        semester=req.semester,
        subject=req.subject,
        reason=req.reason,
        initial_marks=req.initial_marks,
        current_marks=req.initial_marks,
        target_marks=req.target_marks,
    )
    await entry.insert()
    return {"message": "Remedial entry created", "id": str(entry.id), "data": entry.dict()}


@router.get("")
async def list_remedial(
    status: Optional[str] = None,
    semester: Optional[int] = None,
    subject: Optional[str] = None,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """List remedial students for this faculty."""
    query = {"faculty_id": current_user.uid}
    if status:
        query["status"] = status
    if semester:
        query["semester"] = semester
    if subject:
        query["subject"] = subject

    entries = await RemedialEntry.find(query).sort("-created_at").to_list()
    return {"count": len(entries), "entries": [e.dict() for e in entries]}


@router.put("/{entry_id}/progress")
async def add_progress_note(
    entry_id: str,
    req: ProgressNoteRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Add a progress note to a remedial entry."""
    entry = await RemedialEntry.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if entry.faculty_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized")

    faculty = await Faculty.find_one(Faculty.user_id == current_user.uid)
    note = ProgressNote(
        note=req.note,
        added_by=faculty.name if faculty else "",
        marks_change=req.marks_change,
    )
    entry.progress_notes.append(note)

    if req.marks_change and entry.current_marks is not None:
        entry.current_marks += req.marks_change
        if entry.current_marks >= (entry.target_marks or 50):
            entry.status = RemedialStatus.IMPROVING

    entry.updated_at = datetime.utcnow()
    await entry.save()
    return {"message": "Progress note added", "data": entry.dict()}


@router.put("/{entry_id}/resolve")
async def resolve_remedial(
    entry_id: str,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Mark a remedial entry as resolved."""
    entry = await RemedialEntry.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if entry.faculty_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized")

    entry.status = RemedialStatus.RESOLVED
    entry.resolved_at = datetime.utcnow()
    entry.updated_at = datetime.utcnow()
    await entry.save()
    return {"message": "Remedial entry resolved", "data": entry.dict()}


@router.get("/student/{student_id}")
async def get_student_remedial(
    student_id: str,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get remedial entries for a specific student."""
    entries = await RemedialEntry.find(
        RemedialEntry.student_id == student_id
    ).sort("-created_at").to_list()
    return {"count": len(entries), "entries": [e.dict() for e in entries]}
