# app/api/v1/achievements.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.core.security import get_current_user
from app.core.database import get_db
from app.models.achievement import Achievement, AchievementCategory, AchievementAnalytics
from app.schemas.achievement import (
    AchievementCreate,
    AchievementUpdate,
    AchievementResponse,
    AchievementAnalyticsResponse,
    AchievementFilter
)
from app.services.achievement_service import AchievementService
from app.services.notification_service import NotificationService
from app.services.cache_service import CacheService
from app.utils.pagination import paginate

router = APIRouter()
achievement_service = AchievementService()
notification_service = NotificationService()
cache_service = CacheService()

@router.get("/achievements", response_model=List[AchievementResponse])
async def get_achievements(
    faculty_id: str,
    category: Optional[str] = Query(None),
    sort: Optional[str] = Query("date", regex="^(date|impact|category)$"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all achievements for a faculty member with filtering and sorting
    """
    # Verify authorization
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Check cache
    cache_key = f"achievements:{faculty_id}:{category}:{sort}:{skip}:{limit}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached
    
    # Build query
    query = db.query(Achievement).filter(Achievement.faculty_id == faculty_id)
    
    # Apply filters
    if category and category != 'all':
        query = query.filter(Achievement.category == category)
    
    # Apply sorting
    if sort == "date":
        query = query.order_by(desc(Achievement.date))
    elif sort == "impact":
        query = query.order_by(desc(Achievement.impact_score))
    elif sort == "category":
        query = query.order_by(Achievement.category, desc(Achievement.date))
    
    # Paginate
    achievements = query.offset(skip).limit(limit).all()
    
    # Cache results
    await cache_service.set(cache_key, achievements, expire=300)  # 5 minutes
    
    return achievements

@router.get("/achievements/analytics", response_model=AchievementAnalyticsResponse)
async def get_achievement_analytics(
    faculty_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get analytics and statistics for achievements
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Check cache
    cache_key = f"achievement_analytics:{faculty_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached
    
    # Calculate analytics
    current_year = datetime.now().year
    last_year = current_year - 1
    
    total = db.query(func.count(Achievement.id)).filter(
        Achievement.faculty_id == faculty_id
    ).scalar()
    
    verified = db.query(func.count(Achievement.id)).filter(
        and_(
            Achievement.faculty_id == faculty_id,
            Achievement.verified == True
        )
    ).scalar()
    
    this_year = db.query(func.count(Achievement.id)).filter(
        and_(
            Achievement.faculty_id == faculty_id,
            func.extract('year', Achievement.date) == current_year
        )
    ).scalar()
    
    last_year_count = db.query(func.count(Achievement.id)).filter(
        and_(
            Achievement.faculty_id == faculty_id,
            func.extract('year', Achievement.date) == last_year
        )
    ).scalar()
    
    avg_impact = db.query(func.avg(Achievement.impact_score)).filter(
        Achievement.faculty_id == faculty_id
    ).scalar() or 0
    
    # Calculate growth rate
    growth_rate = 0
    if last_year_count > 0:
        growth_rate = ((this_year - last_year_count) / last_year_count) * 100
    
    # Category distribution
    category_dist = db.query(
        Achievement.category,
        func.count(Achievement.id).label('count')
    ).filter(
        Achievement.faculty_id == faculty_id
    ).group_by(Achievement.category).all()
    
    analytics = {
        "total_achievements": total,
        "verified_count": verified,
        "this_year_count": this_year,
        "avg_impact_score": round(float(avg_impact), 2),
        "growth_rate": round(growth_rate, 1),
        "category_distribution": [
            {"category": cat, "count": count} 
            for cat, count in category_dist
        ],
        "recent_achievements": db.query(Achievement).filter(
            Achievement.faculty_id == faculty_id
        ).order_by(desc(Achievement.date)).limit(5).all()
    }
    
    # Cache for 10 minutes
    await cache_service.set(cache_key, analytics, expire=600)
    
    return analytics

@router.post("/achievements", response_model=AchievementResponse, status_code=201)
async def create_achievement(
    faculty_id: str,
    achievement_data: AchievementCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new achievement
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        # Create achievement
        achievement = Achievement(
            **achievement_data.dict(),
            faculty_id=faculty_id,
            created_at=datetime.utcnow()
        )
        
        # Calculate impact score if not provided
        if not achievement.impact_score:
            achievement.impact_score = await achievement_service.calculate_impact_score(
                achievement
            )
        
        db.add(achievement)
        db.commit()
        db.refresh(achievement)
        
        # Invalidate cache
        await cache_service.delete_pattern(f"achievements:{faculty_id}:*")
        await cache_service.delete(f"achievement_analytics:{faculty_id}")
        
        # Send notification in background
        background_tasks.add_task(
            notification_service.send_achievement_notification,
            faculty_id,
            achievement
        )
        
        # Log activity
        background_tasks.add_task(
            achievement_service.log_activity,
            faculty_id,
            "achievement_created",
            achievement.id
        )
        
        return achievement
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/achievements/{achievement_id}", response_model=AchievementResponse)
async def update_achievement(
    faculty_id: str,
    achievement_id: str,
    achievement_data: AchievementUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing achievement
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    achievement = db.query(Achievement).filter(
        and_(
            Achievement.id == achievement_id,
            Achievement.faculty_id == faculty_id
        )
    ).first()
    
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    
    # Update fields
    for field, value in achievement_data.dict(exclude_unset=True).items():
        setattr(achievement, field, value)
    
    achievement.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(achievement)
    
    # Invalidate cache
    await cache_service.delete_pattern(f"achievements:{faculty_id}:*")
    await cache_service.delete(f"achievement_analytics:{faculty_id}")
    
    return achievement

@router.delete("/achievements/{achievement_id}", status_code=204)
async def delete_achievement(
    faculty_id: str,
    achievement_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an achievement
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    achievement = db.query(Achievement).filter(
        and_(
            Achievement.id == achievement_id,
            Achievement.faculty_id == faculty_id
        )
    ).first()
    
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    
    db.delete(achievement)
    db.commit()
    
    # Invalidate cache
    await cache_service.delete_pattern(f"achievements:{faculty_id}:*")
    await cache_service.delete(f"achievement_analytics:{faculty_id}")
    
    return None

@router.post("/achievements/{achievement_id}/verify")
async def verify_achievement(
    faculty_id: str,
    achievement_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Request verification for an achievement
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    achievement = db.query(Achievement).filter(
        and_(
            Achievement.id == achievement_id,
            Achievement.faculty_id == faculty_id
        )
    ).first()
    
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    
    # Add to verification queue
    background_tasks.add_task(
        achievement_service.request_verification,
        achievement
    )
    
    return {"message": "Verification request submitted"}

@router.get("/achievements/export")
async def export_achievements(
    faculty_id: str,
    format: str = Query("csv", regex="^(csv|pdf|json)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Export achievements in various formats
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    achievements = db.query(Achievement).filter(
        Achievement.faculty_id == faculty_id
    ).all()
    
    if format == "csv":
        return await achievement_service.export_to_csv(achievements)
    elif format == "pdf":
        return await achievement_service.export_to_pdf(achievements)
    else:
        return achievements