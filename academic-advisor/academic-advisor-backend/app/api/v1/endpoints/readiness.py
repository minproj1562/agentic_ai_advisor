# app/api/v1/endpoints/readiness.py
"""
Readiness Analysis API
Path order is CRITICAL — specific routes must come before /{student_id}
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


# ════════════════════════════════════════════════════════════════
#  FIXED ROUTE ORDER
#  Rule: All static/specific paths MUST be registered BEFORE
#        any path with a variable segment like /{student_id}
#
#  Wrong order causes FastAPI to match "summary" or "admin"
#  as a student_id string, returning wrong results.
# ════════════════════════════════════════════════════════════════


# ─── POST /calculate ─────────────────────────────────────────
# Static path — registered first, no conflict

@router.post("/calculate", response_model=ReadinessResponse)
async def calculate_readiness(
    req: ReadinessRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """
    Full readiness analysis via POST body.
    If interests / electives / honours are omitted they are
    resolved from the student's saved profile in the database.
    """
    try:
        result = await _service().calculate_readiness(
            student_id=req.student_id,
            interests=req.interests,
            electives=req.electives,
            honours=req.honours_minors,
        )
        return result
    except Exception as e:
        logger.error(f"Readiness calculation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── ADMIN ROUTES — Must be before /{student_id} ─────────────

@router.get("/admin/requirement-maps")
async def list_requirement_maps(
    target_type: Optional[str] = None,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """List all active requirement maps, optionally filtered by type."""
    try:
        query: Dict[str, Any] = {"is_active": True}
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
    except Exception as e:
        logger.error(f"List requirement maps error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/requirement-maps")
async def create_requirement_map(
    data: Dict[str, Any],
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Create or update a requirement map."""
    try:
        target_type = data["target_type"]
        target_name = data["target_name"]

        existing = await SubjectRequirementMap.find_one(
            SubjectRequirementMap.target_type == target_type,
            SubjectRequirementMap.target_name == target_name,
        )

        subjects = [
            RequiredSubject(**s)
            for s in data.get("required_subjects", [])
        ]

        if existing:
            existing.required_subjects = subjects
            existing.target_aliases = data.get(
                "target_aliases", existing.target_aliases
            )
            existing.target_code = data.get(
                "target_code", existing.target_code
            )
            existing.min_cgpa = data.get("min_cgpa", existing.min_cgpa)
            existing.description = data.get(
                "description", existing.description
            )
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

    except KeyError as e:
        raise HTTPException(
            status_code=400, detail=f"Missing required field: {e}"
        )
    except Exception as e:
        logger.error(f"Create requirement map error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/reseed")
async def reseed_requirement_maps(
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Wipe and re-seed all requirement maps from defaults."""
    try:
        await SubjectRequirementMap.find_all().delete()
        ReadinessService._seeded = False
        svc = _service()
        await svc._ensure_seeded()
        count = await SubjectRequirementMap.count()
        return {"status": "reseeded", "total_maps": count}
    except Exception as e:
        logger.error(f"Reseed error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── /{student_id}/summary ────────────────────────────────────
# Must be before /{student_id} to avoid being swallowed

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


# ─── /{student_id}/for-elective/{elective_code} ───────────────
# Must be before /{student_id}

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
        return await _service().check_elective_readiness(
            student_id, elective_code
        )
    except Exception as e:
        logger.error(f"Elective readiness error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── /{student_id}/for-honours/{programme} ────────────────────
# Must be before /{student_id}

@router.get(
    "/{student_id}/for-honours/{programme}",
    response_model=HonoursReadinessResponse,
)
async def get_honours_readiness(
    student_id: str,
    programme: str,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Check readiness for one specific honours programme."""
    try:
        return await _service().check_honours_readiness(
            student_id, programme
        )
    except Exception as e:
        logger.error(f"Honours readiness error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /{student_id} ───────────────────────────────────────
# LAST — catches all remaining /{student_id} requests

@router.get("/{student_id}", response_model=ReadinessResponse)
async def get_readiness(
    student_id: str,
    interests: Optional[str] = Query(
        None, description="Comma-separated interest names"
    ),
    electives: Optional[str] = Query(
        None, description="Comma-separated elective names or codes"
    ),
    honours: Optional[str] = Query(
        None, description="Comma-separated honours/minor programme names"
    ),
    current_user: FirebaseUser = Depends(get_current_user),
):
    """
    Calculate (or re-calculate) readiness for a student.
    Query params are optional — if omitted, goals are loaded from DB.
    """
    try:
        int_list = (
            [i.strip() for i in interests.split(",") if i.strip()]
            if interests else None
        )
        elec_list = (
            [e.strip() for e in electives.split(",") if e.strip()]
            if electives else None
        )
        hon_list = (
            [h.strip() for h in honours.split(",") if h.strip()]
            if honours else None
        )

        return await _service().calculate_readiness(
            student_id=student_id,
            interests=int_list,
            electives=elec_list,
            honours=hon_list,
        )
    except Exception as e:
        logger.error(f"GET readiness error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))