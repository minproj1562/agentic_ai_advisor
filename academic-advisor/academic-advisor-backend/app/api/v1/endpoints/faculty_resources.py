# app/api/v1/endpoints/faculty_resources.py
"""
Faculty Resource API Endpoints
================================
Upload links, PDFs, PPTs, docs and manage learning resources.
Uses Cloudinary for file uploads.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List

from app.dependencies import get_current_user
from app.core.security import FirebaseUser
from app.models.faculty_resource import FacultyResource, FacultyResourceType
from app.models.faculty import Faculty

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/faculty/resources", tags=["faculty-resources"])


class ResourceCreateRequest(BaseModel):
    title: str
    description: str = ""
    resource_type: str = "link"
    url: Optional[str] = None
    semester: int = 0
    branch: str = "IT"
    subject: str = ""
    tags: List[str] = []


@router.post("")
async def create_resource(
    req: ResourceCreateRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Create a resource (link-based)."""
    faculty = await Faculty.find_one(Faculty.user_id == current_user.uid)
    faculty_name = faculty.name if faculty else current_user.email or ""

    resource = FacultyResource(
        faculty_id=current_user.uid,
        faculty_name=faculty_name,
        title=req.title,
        description=req.description,
        resource_type=FacultyResourceType(req.resource_type),
        url=req.url,
        semester=req.semester,
        branch=req.branch,
        subject=req.subject,
        tags=req.tags,
    )
    await resource.insert()
    return {"message": "Resource created", "id": str(resource.id), "data": resource.dict()}


@router.post("/upload")
async def upload_resource(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    semester: int = Form(0),
    branch: str = Form("IT"),
    subject: str = Form(""),
    tags: str = Form(""),
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Upload a file (PDF/PPT/DOC) to Cloudinary."""
    try:
        import cloudinary
        import cloudinary.uploader
        from app.config import settings

        # Configure Cloudinary
        cloudinary.config(
            cloud_name=getattr(settings, 'CLOUDINARY_CLOUD_NAME', ''),
            api_key=getattr(settings, 'CLOUDINARY_API_KEY', ''),
            api_secret=getattr(settings, 'CLOUDINARY_API_SECRET', ''),
        )

        # Determine resource type from file extension
        ext = file.filename.split('.')[-1].lower() if file.filename else "other"
        type_map = {"pdf": "pdf", "pptx": "ppt", "ppt": "ppt", "doc": "doc", "docx": "doc"}
        resource_type = type_map.get(ext, "other")

        # Upload to Cloudinary
        contents = await file.read()
        result = cloudinary.uploader.upload(
            contents,
            resource_type="raw",
            folder="faculty_resources",
            public_id=f"{current_user.uid}_{file.filename}",
        )

        faculty = await Faculty.find_one(Faculty.user_id == current_user.uid)
        faculty_name = faculty.name if faculty else current_user.email or ""

        resource = FacultyResource(
            faculty_id=current_user.uid,
            faculty_name=faculty_name,
            title=title,
            description=description,
            resource_type=FacultyResourceType(resource_type),
            file_url=result.get("secure_url", ""),
            file_public_id=result.get("public_id", ""),
            file_size_bytes=len(contents),
            semester=semester,
            branch=branch,
            subject=subject,
            tags=[t.strip() for t in tags.split(",") if t.strip()],
        )
        await resource.insert()

        return {
            "message": "File uploaded",
            "id": str(resource.id),
            "file_url": resource.file_url,
            "data": resource.dict(),
        }

    except ImportError:
        raise HTTPException(status_code=500, detail="Cloudinary not configured. Install cloudinary package.")
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("")
async def list_resources(
    semester: Optional[int] = None,
    branch: Optional[str] = None,
    subject: Optional[str] = None,
    resource_type: Optional[str] = None,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """List resources (filterable)."""
    query = {"is_active": True}
    if semester:
        query["semester"] = semester
    if branch:
        query["branch"] = branch
    if subject:
        query["subject"] = subject
    if resource_type:
        query["resource_type"] = resource_type

    resources = await FacultyResource.find(query).sort("-created_at").to_list()
    return {
        "count": len(resources),
        "resources": [r.dict() for r in resources],
    }


@router.get("/my")
async def my_resources(
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get resources uploaded by current faculty."""
    resources = await FacultyResource.find(
        FacultyResource.faculty_id == current_user.uid
    ).sort("-created_at").to_list()
    return {"count": len(resources), "resources": [r.dict() for r in resources]}


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: str,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Delete a resource."""
    resource = await FacultyResource.get(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if resource.faculty_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Delete from Cloudinary if uploaded
    if resource.file_public_id:
        try:
            import cloudinary.uploader
            cloudinary.uploader.destroy(resource.file_public_id, resource_type="raw")
        except Exception as e:
            logger.warning(f"Cloudinary delete failed: {e}")

    await resource.delete()
    return {"message": "Resource deleted"}


# Student-facing endpoint
@router.get("/student")
async def student_resources(
    semester: Optional[int] = None,
    branch: str = "IT",
    subject: Optional[str] = None,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get resources for students (filtered by semester/branch)."""
    query = {"is_active": True, "branch": branch}
    if semester:
        query["$or"] = [{"semester": semester}, {"semester": 0}]
    if subject:
        query["subject"] = subject

    resources = await FacultyResource.find(query).sort("-created_at").to_list()
    return {"count": len(resources), "resources": [r.dict() for r in resources]}
