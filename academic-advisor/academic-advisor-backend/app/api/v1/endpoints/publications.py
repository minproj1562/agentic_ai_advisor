#academic-advisor-backend/app/api/v1/endpoints/publications.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from beanie import PydanticObjectId

from app.core.security import get_current_user, FirebaseUser
from app.models.publications import Publication, PublicationType, PublicationStatus  # Fixed import
from app.services.publication_service import PublicationService
from app.core.cache import cache_key_wrapper
import logging

router = APIRouter(prefix="/publications", tags=["publications"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Publication])
@cache_key_wrapper(prefix="publications", ttl=600)
async def get_publications(
    current_user: FirebaseUser = Depends(get_current_user),
    publication_type: Optional[PublicationType] = None,
    status: Optional[PublicationStatus] = None,
    search: Optional[str] = None,
    year: Optional[int] = None,
    sort_by: str = Query("date", regex="^(date|citations|impact)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get user's publications with filters"""
    service = PublicationService()
    publications = await service.get_user_publications(
        user_id=current_user.uid,
        publication_type=publication_type,
        status=status,
        search=search,
        year=year,
        sort_by=sort_by,
        skip=skip,
        limit=limit
    )
    return publications

@router.get("/metrics")
async def get_publication_metrics(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get publication metrics and analytics"""
    service = PublicationService()
    metrics = await service.calculate_metrics(current_user.uid)
    return metrics

@router.get("/{publication_id}", response_model=Publication)
async def get_publication(
    publication_id: PydanticObjectId,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get a specific publication"""
    publication = await Publication.get(publication_id)
    if not publication:
        raise HTTPException(status_code=404, detail="Publication not found")
    
    if publication.user_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Increment views
    publication.views += 1
    await publication.save()
    
    return publication

@router.post("/", response_model=Publication)
async def create_publication(
    publication_data: dict,
    background_tasks: BackgroundTasks,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Create a new publication"""
    try:
        # Create publication
        publication = Publication(
            user_id=current_user.uid,
            **publication_data
        )
        await publication.insert()  # Use insert instead of create
        
        return publication
    except Exception as e:
        logger.error(f"Error creating publication: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{publication_id}", response_model=Publication)
async def update_publication(
    publication_id: PydanticObjectId,
    update_data: dict,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Update a publication"""
    publication = await Publication.get(publication_id)
    if not publication:
        raise HTTPException(status_code=404, detail="Publication not found")
    
    if publication.user_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update fields
    for field, value in update_data.items():
        if hasattr(publication, field):
            setattr(publication, field, value)
    
    publication.updated_at = datetime.now()
    await publication.save()
    
    return publication

@router.delete("/{publication_id}")
async def delete_publication(
    publication_id: PydanticObjectId,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Delete a publication (soft delete)"""
    publication = await Publication.get(publication_id)
    if not publication:
        raise HTTPException(status_code=404, detail="Publication not found")
    
    if publication.user_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    publication.is_active = False
    publication.updated_at = datetime.now()
    await publication.save()
    
    return {"message": "Publication deleted successfully"}

@router.post("/bulk-import")
async def bulk_import_publications(
    publications: List[dict],
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Bulk import publications"""
    if len(publications) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 publications can be imported at once"
        )
    
    service = PublicationService()
    result = await service.bulk_import(current_user.uid, publications)
    
    return result

@router.get("/export/{format}")
async def export_publications(
    format: str = "csv",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Export publications in various formats"""
    if format not in ["csv", "json", "bibtex"]:
        raise HTTPException(status_code=400, detail="Invalid export format")
    
    service = PublicationService()
    
    if format == "csv":
        data = await service.export_to_csv(current_user.uid, start_date, end_date)
        return {"data": data, "format": "csv"}
    elif format == "bibtex":
        data = await service.export_to_bibtex(current_user.uid, start_date, end_date)
        return {"data": data, "format": "bibtex"}
    else:
        # For JSON, return the publications directly
        publications = await service.get_user_publications(current_user.uid)
        return {"publications": [pub.dict() for pub in publications], "format": "json"}

@router.get("/analysis/trends")
async def analyze_publication_trends(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Analyze publication trends and patterns"""
    service = PublicationService()
    analysis = await service.analyze_trends(current_user.uid)
    return analysis

@router.post("/recommend-journals")
async def recommend_journals(
    abstract: str,
    keywords: List[str],
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get journal recommendations based on paper content"""
    service = PublicationService()
    recommendations = await service.recommend_journals(abstract, keywords)
    return recommendations