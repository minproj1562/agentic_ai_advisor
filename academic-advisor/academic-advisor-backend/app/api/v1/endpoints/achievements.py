#academic-advisor-backend/app/api/v1/endpoints/achievements.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from beanie import PydanticObjectId

from app.core.security import get_current_user
from app.models.achievement import Achievement, AchievementAnalytics, AchievementCategory, AchievementStatus
from app.services.achievement_service import AchievementService
from app.core.cache import cache_key_wrapper
from pydantic import BaseModel

router = APIRouter()
achievement_service = AchievementService()

class AchievementCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: AchievementCategory
    date: datetime
    impact_score: Optional[float] = None
    evidence_url: Optional[str] = None
    tags: List[str] = []

class AchievementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[AchievementCategory] = None
    date: Optional[datetime] = None
    impact_score: Optional[float] = None
    evidence_url: Optional[str] = None
    tags: Optional[List[str]] = None

class AchievementResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    category: AchievementCategory
    date: datetime
    impact_score: Optional[float]
    verified: bool
    status: AchievementStatus
    tags: List[str]
    created_at: datetime
    updated_at: datetime

@router.get("/", response_model=List[AchievementResponse])
@cache_key_wrapper(prefix="achievements", ttl=300)
async def get_achievements(
    faculty_id: str,
    category: Optional[str] = Query(None),
    sort: Optional[str] = Query("date", regex="^(date|impact|category)$"),
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get all achievements for a faculty member"""
    if current_user.uid != faculty_id and not current_user.is_faculty:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Build query
    query = Achievement.find(Achievement.faculty_id == faculty_id)
    
    # Apply filters
    if category and category != 'all':
        query = query.find(Achievement.category == category)
    
    # Apply sorting
    if sort == "date":
        query = query.sort(-Achievement.date)
    elif sort == "impact":
        query = query.sort(-Achievement.impact_score)
    elif sort == "category":
        query = query.sort(Achievement.category, -Achievement.date)
    
    # Paginate
    achievements = await query.skip(skip).limit(limit).to_list()
    return achievements

@router.get("/analytics")
async def get_achievement_analytics(
    faculty_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get achievement analytics"""
    if current_user.uid != faculty_id and not current_user.is_faculty:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    analytics = await achievement_service.calculate_analytics(faculty_id)
    return analytics.dict()

@router.post("/", response_model=AchievementResponse)
async def create_achievement(
    faculty_id: str,
    achievement_data: AchievementCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Create a new achievement"""
    if current_user.uid != faculty_id and not current_user.is_faculty:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Create achievement
    achievement = Achievement(
        **achievement_data.dict(),
        faculty_id=faculty_id
    )
    
    # Calculate impact score if not provided
    if not achievement.impact_score:
        achievement.impact_score = await achievement_service.calculate_impact_score(achievement)
    
    await achievement.insert()
    
    # Update analytics in background
    background_tasks.add_task(
        achievement_service.calculate_analytics,
        faculty_id
    )
    
    return achievement

@router.put("/{achievement_id}", response_model=AchievementResponse)
async def update_achievement(
    faculty_id: str,
    achievement_id: str,
    achievement_data: AchievementUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an achievement"""
    if current_user.uid != faculty_id and not current_user.is_faculty:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    achievement = await Achievement.get(achievement_id)
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    
    if achievement.faculty_id != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Update fields
    update_data = achievement_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(achievement, field, value)
    
    achievement.updated_at = datetime.utcnow()
    await achievement.save()
    
    return achievement

@router.delete("/{achievement_id}")
async def delete_achievement(
    faculty_id: str,
    achievement_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an achievement"""
    if current_user.uid != faculty_id and not current_user.is_faculty:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    achievement = await Achievement.get(achievement_id)
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    
    if achievement.faculty_id != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    await achievement.delete()
    
    # Update analytics
    await achievement_service.calculate_analytics(faculty_id)
    
    return {"message": "Achievement deleted successfully"}

@router.post("/{achievement_id}/verify")
async def verify_achievement(
    faculty_id: str,
    achievement_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Request verification for an achievement"""
    if current_user.uid != faculty_id and not current_user.is_faculty:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    achievement = await Achievement.get(achievement_id)
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    
    if achievement.faculty_id != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    await achievement_service.request_verification(achievement)
    
    return {"message": "Verification request submitted"}

@router.get("/export/{format}")
async def export_achievements(
    faculty_id: str,
    format: str = "csv",
    current_user: dict = Depends(get_current_user)
):
    """Export achievements"""
    if current_user.uid != faculty_id and not current_user.is_faculty:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    achievements = await Achievement.find(
        Achievement.faculty_id == faculty_id
    ).to_list()
    
    if format == "csv":
        csv_data = await achievement_service.export_to_csv(achievements)
        return {"data": csv_data, "format": "csv"}
    elif format == "pdf":
        pdf_url = await achievement_service.export_to_pdf(achievements)
        return {"url": pdf_url, "format": "pdf"}
    else:
        return achievements