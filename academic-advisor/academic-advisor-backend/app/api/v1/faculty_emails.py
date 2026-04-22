# academic-advisor-backend/app/api/v1/faculty_emails.py
"""
Public endpoint — returns all faculty emails stored in MongoDB.

Why public (no auth)?
---------------------
The Login page needs to validate/hint faculty emails BEFORE the user
is authenticated. We cannot attach a Bearer token at that point, so
this endpoint is intentionally unauthenticated.

It only exposes email, name, department, and status — no sensitive data.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from app.models.faculty import Faculty
from app.utils.helpers import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/approved-emails")
async def get_faculty_emails() -> Dict[str, Any]:
    """
    Returns all faculty records from MongoDB.

    Used by:
    - Login page  → validate email format + show green/yellow hint
    - FacultyManagement → populate the "click to use" email list
    - auth.service.ts   → non-blocking approval check

    Response shape
    --------------
    {
        "emails": [
            {
                "email": "poonam.bari@fcrit.ac.in",
                "name":  "Poonam Bari",
                "department": "IT",
                "status": "pending_setup"
            },
            ...
        ],
        "total":  14,
        "domain": "@fcrit.ac.in"
    }
    """
    try:
        # Fetch all faculty from MongoDB via Beanie ORM
        # We only need 4 fields — no need to load the full document
        faculty_list = await Faculty.find_all().to_list()

        emails: List[Dict[str, Any]] = []
        for f in faculty_list:
            # Skip records without an email (data integrity guard)
            if not f.email:
                continue
            emails.append(
                {
                    "email":      f.email.lower().strip(),
                    "name":       f.name or "",
                    "department": f.department or "",
                    "status":     f.status.value
                                  if hasattr(f.status, "value")
                                  else str(f.status),
                }
            )

        logger.info(
            "Faculty emails endpoint called — returning %d records",
            len(emails),
        )

        return {
            "emails": emails,
            "total":  len(emails),
            "domain": "@fcrit.ac.in",
        }

    except Exception as e:
        logger.error("Error fetching faculty emails: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch faculty emails",
        )