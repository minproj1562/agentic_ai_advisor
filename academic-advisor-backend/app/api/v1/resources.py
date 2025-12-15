# app/api/v1/resources.py
"""
Resources API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse

from app.dependencies import get_current_user, get_faculty_user, get_student_user
from app.services.resource_service import ResourceService
from app.core.firebase_admin import firebase_manager
from app.utils.helpers import get_logger

logger = get_logger(__name__)
router = APIRouter()

resource_service = ResourceService()


@router.get("/library")
async def get_digital_library(
    subject: Optional[str] = None,
    resource_type: Optional[str] = Query(None, regex="^(book|video|article|tutorial)$"),
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    Get digital library resources
    """
    try:
        resources = await resource_service.get_library_resources(
            subject=subject,
            resource_type=resource_type,
            skip=skip,
            limit=limit
        )
        
        return resources
        
    except Exception as e:
        logger.error(f"Error fetching library resources: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch resources")


@router.post("/upload")
async def upload_resource(
    file: UploadFile = File(...),
    metadata: dict = {},
    current_user: dict = Depends(get_faculty_user)
):
    """
    Upload educational resource (faculty only)
    """
    try:
        # Validate file
        if file.size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=400, detail="File too large")
        
        # Read file
        content = await file.read()
        
        # Upload to Firebase Storage
        file_path = f"resources/{current_user['department']}/{file.filename}"
        url = await firebase_manager.upload_file(
            file_path=file_path,
            file_data=content,
            content_type=file.content_type
        )
        
        # Store metadata
        resource_id = await resource_service.create_resource(
            title=metadata.get('title', file.filename),
            description=metadata.get('description'),
            url=url,
            resource_type=metadata.get('type', 'document'),
            subject=metadata.get('subject'),
            uploaded_by=current_user['uid'],
            department=current_user['department']
        )
        
        return {
            "message": "Resource uploaded successfully",
            "resource_id": resource_id,
            "url": url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading resource: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload resource")


@router.get("/youtube")
async def get_youtube_resources(
    query: str,
    max_results: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    Get YouTube educational videos
    """
    try:
        videos = await resource_service.search_youtube_resources(
            query=query,
            max_results=max_results
        )
        
        return videos
        
    except Exception as e:
        logger.error(f"Error fetching YouTube resources: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch videos")


@router.get("/practice-problems")
async def get_practice_problems(
    subject: str,
    difficulty: Optional[str] = Query(None, regex="^(easy|medium|hard)$"),
    topic: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get practice problems
    """
    try:
        problems = await resource_service.get_practice_problems(
            subject=subject,
            difficulty=difficulty,
            topic=topic,
            student_level=current_user.get('current_semester', 1)
        )
        
        return problems
        
    except Exception as e:
        logger.error(f"Error fetching practice problems: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch problems")


@router.post("/practice-problems/{problem_id}/submit")
async def submit_solution(
    problem_id: str,
    solution: dict,
    current_user: dict = Depends(get_student_user)
):
    """
    Submit solution to practice problem
    """
    try:
        result = await resource_service.evaluate_solution(
            problem_id=problem_id,
            student_id=current_user['student_id'],
            solution=solution
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error submitting solution: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit solution")


@router.get("/study-materials/{course_id}")
async def get_course_materials(
    course_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get study materials for a specific course
    """
    try:
        materials = await resource_service.get_course_materials(
            course_id=course_id,
            user_role=current_user.get('role')
        )
        
        return materials
        
    except Exception as e:
        logger.error(f"Error fetching course materials: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch materials")


@router.get("/download/{resource_id}")
async def download_resource(
    resource_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Download a resource
    """
    try:
        resource = await resource_service.get_resource_for_download(
            resource_id=resource_id,
            user_id=current_user['uid']
        )
        
        return StreamingResponse(
            resource['content'],
            media_type=resource['content_type'],
            headers={
                "Content-Disposition": f"attachment; filename={resource['filename']}"
            }
        )
        
    except Exception as e:
        logger.error(f"Error downloading resource: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download resource")