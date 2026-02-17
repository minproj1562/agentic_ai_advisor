#academic-advisor-backend/app/api/v1/endpoints/readiness.py
"""
Readiness Analysis API
Matches the frontend service at /api/v1/readiness/*
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from app.models.readiness import (
    ReadinessRequest,
    ReadinessResponse,
    ReadinessSummaryResponse,
    ElectiveReadinessResponse,
    HonoursReadinessResponse,
    SubjectRequirementMap,
    RequiredSubject,
)
from app.services.readiness_service import get_readiness_service, ReadinessService
from app.core.security import get_current_user, FirebaseUser

router = APIRouter()
logger = logging.getLogger(__name__)


def _service() -> ReadinessService:
    return get_readiness_service()


# ─── POST /calculate ─────────────────────────────────────────

@router.post("/calculate", response_model=ReadinessResponse)
async def calculate_readiness(
    req: ReadinessRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """
    Full 8-step readiness analysis.
    If interests / electives / honours are omitted they are fetched from the DB.
    """
    try:
        svc = _service()
        result = await svc.calculate_readiness(
            student_id=req.student_id,
            interests=req.interests,
            electives=req.electives,
            honours=req.honours_minors,
        )
        return result
    except Exception as e:
        logger.error(f"Readiness calculation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /{student_id} ───────────────────────────────────────

@router.get("/{student_id}", response_model=ReadinessResponse)
async def get_readiness(
    student_id: str,
    interests: Optional[str] = Query(None, description="Comma-separated"),
    electives: Optional[str] = Query(None),
    honours: Optional[str] = Query(None),
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Calculate (or re-calculate) readiness.  Query params are optional."""
    try:
        svc = _service()
        int_list = [i.strip() for i in interests.split(",")] if interests else None
        elec_list = [e.strip() for e in electives.split(",")] if electives else None
        hon_list = [h.strip() for h in honours.split(",")] if honours else None

        return await svc.calculate_readiness(
            student_id=student_id,
            interests=int_list,
            electives=elec_list,
            honours=hon_list,
        )
    except Exception as e:
        logger.error(f"GET readiness error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /{student_id}/summary ────────────────────────────────

@router.get("/{student_id}/summary", response_model=ReadinessSummaryResponse)
async def get_readiness_summary(
    student_id: str,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Lightweight summary for dashboard widgets."""
    try:
        return await _service().get_summary(student_id)
    except Exception as e:
        logger.error(f"Readiness summary error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /{student_id}/for-elective/{code} ────────────────────

@router.get(
    "/{student_id}/for-elective/{elective_code}",
    response_model=ElectiveReadinessResponse,
)
async def get_elective_readiness(
    student_id: str,
    elective_code: str,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Check readiness for one specific elective."""
    try:
        return await _service().check_elective_readiness(student_id, elective_code)
    except Exception as e:
        logger.error(f"Elective readiness error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /{student_id}/for-honours/{programme} ────────────────

@router.get(
    "/{student_id}/for-honours/{programme}",
    response_model=HonoursReadinessResponse,
)
async def get_honours_readiness(
    student_id: str,
    programme: str,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Check readiness for one specific honours / minor programme."""
    try:
        return await _service().check_honours_readiness(student_id, programme)
    except Exception as e:
        logger.error(f"Honours readiness error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
#  ADMIN: Manage requirement maps
# ════════════════════════════════════════════════════════════════

@router.get("/admin/requirement-maps")
async def list_requirement_maps(
    target_type: Optional[str] = None,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """List all requirement maps (optionally filtered by type)."""
    query = {"is_active": True}
    if target_type:
        query["target_type"] = target_type
    maps = await SubjectRequirementMap.find(query).to_list()
    return [
        {
            "id": str(m.id),
            "target_type": m.target_type,
            "target_name": m.target_name,
            "target_aliases": m.target_aliases,
            "target_code": m.target_code,
            "min_cgpa": m.min_cgpa,
            "subjects_count": len(m.required_subjects),
            "required_subjects": [
                {
                    "subject_name": rs.subject_name,
                    "importance": rs.importance,
                    "importance_label": rs.importance_label,
                    "min_score": rs.min_score,
                    "weight": rs.weight,
                }
                for rs in m.required_subjects
            ],
        }
        for m in maps
    ]


@router.post("/admin/requirement-maps")
async def create_requirement_map(
    data: Dict[str, Any],
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Create or update a requirement map (faculty / admin)."""
    try:
        target_type = data["target_type"]
        target_name = data["target_name"]

        existing = await SubjectRequirementMap.find_one(
            SubjectRequirementMap.target_type == target_type,
            SubjectRequirementMap.target_name == target_name,
        )

        subjects = [RequiredSubject(**s) for s in data.get("required_subjects", [])]

        if existing:
            existing.required_subjects = subjects
            existing.target_aliases = data.get("target_aliases", existing.target_aliases)
            existing.target_code = data.get("target_code", existing.target_code)
            existing.min_cgpa = data.get("min_cgpa", existing.min_cgpa)
            existing.description = data.get("description", existing.description)
            existing.updated_at = datetime.utcnow()
            await existing.save()
            return {"status": "updated", "id": str(existing.id)}

        doc = SubjectRequirementMap(
            target_type=target_type,
            target_name=target_name,
            target_aliases=data.get("target_aliases", []),
            target_code=data.get("target_code"),
            required_subjects=subjects,
            min_cgpa=data.get("min_cgpa"),
            description=data.get("description"),
        )
        await doc.insert()
        return {"status": "created", "id": str(doc.id)}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/reseed")
async def reseed_requirement_maps(
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Wipe and re-seed all requirement maps from defaults (admin only)."""
    try:
        await SubjectRequirementMap.find_all().delete()
        ReadinessService._seeded = False
        svc = _service()
        await svc._ensure_seeded()
        count = await SubjectRequirementMap.count()
        return {"status": "reseeded", "total_maps": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))