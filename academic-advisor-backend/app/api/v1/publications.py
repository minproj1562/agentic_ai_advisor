from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from beanie import PydanticObjectId

from app.core.security import get_current_user
from app.core.firebase import User
from app.models.publication import Publication, PublicationType, PublicationStatus
from app.services.publication_service import PublicationService
from app.services.scholar_service import ScholarService
from app.core.cache import cache_key_wrapper
from app.utils.validators import validate_doi, validate_file_size
import logging

router = APIRouter(prefix="/publications", tags=["publications"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Publication])
@cache_key_wrapper(prefix="publications", ttl=600)
async def get_publications(
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user)
):
    """Get publication metrics and analytics"""
    service = PublicationService()
    metrics = await service.calculate_metrics(current_user.uid)
    return metrics

@router.get("/{publication_id}", response_model=Publication)
async def get_publication(
    publication_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
):
    """Create a new publication"""
    try:
        # Validate DOI if provided
        if publication_data.get("doi"):
            if not validate_doi(publication_data["doi"]):
                raise HTTPException(status_code=400, detail="Invalid DOI format")
        
        # Create publication
        publication = Publication(
            user_id=current_user.uid,
            **publication_data
        )
        await publication.create()
        
        # Schedule citation fetch in background
        if publication.doi or publication.title:
            background_tasks.add_task(
                ScholarService().fetch_citations,
                publication.id,
                publication.title,
                publication.authors[0] if publication.authors else None
            )
        
        return publication
    except Exception as e:
        logger.error(f"Error creating publication: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{publication_id}", response_model=Publication)
async def update_publication(
    publication_id: PydanticObjectId,
    update_data: dict,
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
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

@router.post("/{publication_id}/pdf")
async def upload_pdf(
    publication_id: PydanticObjectId,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload PDF for a publication"""
    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    if not validate_file_size(file, max_size_mb=10):
        raise HTTPException(status_code=400, detail="File size exceeds 10MB")
    
    publication = await Publication.get(publication_id)
    if not publication:
        raise HTTPException(status_code=404, detail="Publication not found")
    
    if publication.user_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = PublicationService()
    pdf_url = await service.upload_pdf(publication, file)
    
    return {"pdf_url": pdf_url}

@router.post("/{publication_id}/sync-citations")
async def sync_citations(
    publication_id: PydanticObjectId,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Sync citations from Google Scholar"""
    publication = await Publication.get(publication_id)
    if not publication:
        raise HTTPException(status_code=404, detail="Publication not found")
    
    if publication.user_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check rate limit (last update should be > 1 hour ago)
    time_since_update = datetime.now() - publication.last_citation_update
    if time_since_update.total_seconds() < 3600:
        raise HTTPException(
            status_code=429,
            detail="Citations can only be synced once per hour"
        )
    
    # Schedule sync in background
    background_tasks.add_task(
        ScholarService().fetch_citations,
        publication.id,
        publication.title,
        publication.authors[0] if publication.authors else None
    )
    
    return {"message": "Citation sync started", "status": "processing"}

@router.post("/bulk-import")
async def bulk_import_publications(
    publications: List[dict],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Bulk import publications"""
    if len(publications) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 publications can be imported at once"
        )
    
    service = PublicationService()
    result = await service.bulk_import(current_user.uid, publications)
    
    # Schedule citation fetching for imported publications
    for pub_id in result["success_ids"]:
        background_tasks.add_task(
            ScholarService().fetch_citations_by_id,
            pub_id
        )
    
    return result

@router.get("/export/{format}")
async def export_publications(
    format: str = "csv",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Export publications in various formats"""
    if format not in ["csv", "json", "bibtex"]:
        raise HTTPException(status_code=400, detail="Invalid export format")
    
    service = PublicationService()
    
    if format == "csv":
        data = await service.export_to_csv(current_user.uid, start_date, end_date)
        return {"data": data, "format": "csv"}
    elif format == "json":
        data = await service.export_to_json(current_user.uid, start_date, end_date)
        return data
    elif format == "bibtex":
        data = await service.export_to_bibtex(current_user.uid, start_date, end_date)
        return {"data": data, "format": "bibtex"}

@router.get("/analysis/trends")
async def analyze_publication_trends(
    current_user: User = Depends(get_current_user)
):
    """Analyze publication trends and patterns"""
    service = PublicationService()
    analysis = await service.analyze_trends(current_user.uid)
    return analysis

@router.get("/analysis/collaborations")
async def analyze_collaborations(
    current_user: User = Depends(get_current_user)
):
    """Analyze collaboration network"""
    service = PublicationService()
    network = await service.analyze_collaboration_network(current_user.uid)
    return network

@router.post("/recommend-journals")
async def recommend_journals(
    abstract: str,
    keywords: List[str],
    current_user: User = Depends(get_current_user)
):
    """Get journal recommendations based on paper content"""
    service = PublicationService()
    recommendations = await service.recommend_journals(abstract, keywords)
    return recommendations