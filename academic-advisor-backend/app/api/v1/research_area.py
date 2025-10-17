from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from beanie import PydanticObjectId

from app.core.security import get_current_user
from app.core.firebase import User
from app.models.research_area import ResearchArea, ResearchCategory
from app.services.research_service import ResearchAreaService
from app.core.cache import cache_key_wrapper
import logging

router = APIRouter(prefix="/research-areas", tags=["research"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[ResearchArea])
@cache_key_wrapper(prefix="research_areas", ttl=600)
async def get_research_areas(
    current_user: User = Depends(get_current_user),
    category: Optional[ResearchCategory] = None,
    search: Optional[str] = None
):
    """Get user's research areas"""
    service = ResearchAreaService()
    areas = await service.get_user_research_areas(
        user_id=current_user.uid,
        category=category,
        search=search
    )
    return areas

@router.get("/metrics")
async def get_research_metrics(
    current_user: User = Depends(get_current_user)
):
    """Get research area metrics and analytics"""
    service = ResearchAreaService()
    metrics = await service.calculate_metrics(current_user.uid)
    return metrics

@router.get("/{area_id}", response_model=ResearchArea)
async def get_research_area(
    area_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    """Get a specific research area"""
    area = await ResearchArea.get(area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Research area not found")
    
    if area.user_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return area

@router.post("/", response_model=ResearchArea)
async def create_research_area(
    area_data: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Create a new research area"""
    try:
        # Check for duplicates
        existing = await ResearchArea.find_one({
            "user_id": current_user.uid,
            "name": area_data["name"],
            "is_active": True
        })
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Research area with this name already exists"
            )
        
        # Create research area
        area = ResearchArea(
            user_id=current_user.uid,
            **area_data
        )
        await area.create()
        
        # Analyze relationships in background
        background_tasks.add_task(
            ResearchAreaService().analyze_area_relationships,
            area.id,
            current_user.uid
        )
        
        return area
    except Exception as e:
        logger.error(f"Error creating research area: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{area_id}", response_model=ResearchArea)
async def update_research_area(
    area_id: PydanticObjectId,
    update_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Update a research area"""
    area = await ResearchArea.get(area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Research area not found")
    
    if area.user_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update fields
    for field, value in update_data.items():
        if hasattr(area, field):
            setattr(area, field, value)
    
    area.updated_at = datetime.now()
    await area.save()
    
    return area

@router.delete("/{area_id}")
async def delete_research_area(
    area_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    """Delete a research area"""
    area = await ResearchArea.get(area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Research area not found")
    
    if area.user_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    area.is_active = False
    area.updated_at = datetime.now()
    await area.save()
    
    return {"message": "Research area deleted successfully"}

@router.get("/{area_id}/network")
async def get_collaboration_network(
    area_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    """Get collaboration network for a research area"""
    area = await ResearchArea.get(area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Research area not found")
    
    if area.user_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = ResearchAreaService()
    network = await service.get_collaboration_network(area)
    return network

@router.post("/{area_id}/analyze-trends")
async def analyze_trends(
    area_id: PydanticObjectId,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Analyze trends for a research area"""
    area = await ResearchArea.get(area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Research area not found")
    
    if area.user_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Start analysis in background
    background_tasks.add_task(
        ResearchAreaService().analyze_trends,
        area.id,
        current_user.uid
    )
    
    return {"message": "Trend analysis started", "status": "processing"}

@router.get("/analysis/expertise-matrix")
async def get_expertise_matrix(
    current_user: User = Depends(get_current_user)
):
    """Get expertise matrix across all research areas"""
    service = ResearchAreaService()
    matrix = await service.calculate_expertise_matrix(current_user.uid)
    return matrix

@router.post("/suggest-collaborators")
async def suggest_collaborators(
    area_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    """Get collaboration suggestions for a research area"""
    area = await ResearchArea.get(area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Research area not found")
    
    if area.user_id != current_user.uid:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = ResearchAreaService()
    suggestions = await service.suggest_collaborators(area)
    return suggestions

@router.post("/match-opportunities")
async def match_research_opportunities(
    keywords: List[str],
    current_user: User = Depends(get_current_user)
):
    """Match research opportunities based on expertise"""
    service = ResearchAreaService()
    opportunities = await service.match_opportunities(
        user_id=current_user.uid,
        keywords=keywords
    )
    return opportunities