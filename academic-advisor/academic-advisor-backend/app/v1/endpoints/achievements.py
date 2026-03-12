# app/api/v1/achievements.py
"""
Achievements endpoints using Beanie (MongoDB)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta
import re

from app.core.security import get_current_user
from app.models.achievement import Achievement  # Beanie document
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
    current_user: dict = Depends(get_current_user)
):
    """
    Get all achievements for a faculty member with filtering and sorting.
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Cache key based on parameters
    cache_key = f"achievements:{faculty_id}:{category}:{sort}:{skip}:{limit}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    # Build query
    query = Achievement.find(Achievement.faculty_id == faculty_id)

    if category and category != 'all':
        query = query.find(Achievement.category == category)

    # Sorting
    if sort == "date":
        query = query.sort(-Achievement.date)  # descending
    elif sort == "impact":
        query = query.sort(-Achievement.impact_score)
    elif sort == "category":
        query = query.sort(Achievement.category, -Achievement.date)

    # Pagination
    achievements = await query.skip(skip).limit(limit).to_list()

    # Cache for 5 minutes
    await cache_service.set(cache_key, achievements, expire=300)
    return achievements


@router.get("/achievements/analytics", response_model=AchievementAnalyticsResponse)
async def get_achievement_analytics(
    faculty_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get analytics and statistics for achievements.
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    cache_key = f"achievement_analytics:{faculty_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    current_year = datetime.now().year
    last_year = current_year - 1

    # Count total achievements
    total = await Achievement.find(Achievement.faculty_id == faculty_id).count()

    # Count verified
    verified = await Achievement.find(
        Achievement.faculty_id == faculty_id,
        Achievement.verified == True
    ).count()

    # This year
    this_year = await Achievement.find(
        Achievement.faculty_id == faculty_id,
        Achievement.date >= datetime(current_year, 1, 1),
        Achievement.date < datetime(current_year + 1, 1, 1)
    ).count()

    # Last year
    last_year_count = await Achievement.find(
        Achievement.faculty_id == faculty_id,
        Achievement.date >= datetime(last_year, 1, 1),
        Achievement.date < datetime(current_year, 1, 1)
    ).count()

    # Average impact score (using aggregation)
    pipeline = [
        {"$match": {"faculty_id": faculty_id}},
        {"$group": {
            "_id": None,
            "avg_impact": {"$avg": "$impact_score"}
        }}
    ]
    agg_result = await Achievement.aggregate(pipeline).to_list()
    avg_impact = agg_result[0]["avg_impact"] if agg_result else 0

    # Growth rate
    growth_rate = 0
    if last_year_count > 0:
        growth_rate = ((this_year - last_year_count) / last_year_count) * 100

    # Category distribution
    cat_pipeline = [
        {"$match": {"faculty_id": faculty_id}},
        {"$group": {
            "_id": "$category",
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    cat_results = await Achievement.aggregate(cat_pipeline).to_list()
    category_dist = [{"category": r["_id"], "count": r["count"]} for r in cat_results]

    # Recent achievements
    recent = await Achievement.find(
        Achievement.faculty_id == faculty_id
    ).sort(-Achievement.date).limit(5).to_list()

    analytics = {
        "total_achievements": total,
        "verified_count": verified,
        "this_year_count": this_year,
        "avg_impact_score": round(avg_impact, 2),
        "growth_rate": round(growth_rate, 1),
        "category_distribution": category_dist,
        "recent_achievements": recent
    }

    await cache_service.set(cache_key, analytics, expire=600)  # 10 minutes
    return analytics


@router.post("/achievements", response_model=AchievementResponse, status_code=201)
async def create_achievement(
    faculty_id: str,
    achievement_data: AchievementCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new achievement.
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        # Create document
        achievement = Achievement(
            **achievement_data.model_dump(),
            faculty_id=faculty_id,
            created_at=datetime.utcnow()
        )

        # Calculate impact score if not provided
        if not achievement.impact_score:
            achievement.impact_score = await achievement_service.calculate_impact_score(
                achievement
            )

        await achievement.insert()

        # Invalidate cache
        await cache_service.delete_pattern(f"achievements:{faculty_id}:*")
        await cache_service.delete(f"achievement_analytics:{faculty_id}")

        # Background tasks
        background_tasks.add_task(
            notification_service.send_achievement_notification,
            faculty_id,
            achievement
        )
        background_tasks.add_task(
            achievement_service.log_activity,
            faculty_id,
            "achievement_created",
            str(achievement.id)
        )

        return achievement

    except Exception as e:
        # Beanie doesn't have an explicit rollback; errors are raised immediately
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/achievements/{achievement_id}", response_model=AchievementResponse)
async def update_achievement(
    faculty_id: str,
    achievement_id: str,
    achievement_data: AchievementUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing achievement.
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    achievement = await Achievement.find_one(
        Achievement.id == achievement_id,
        Achievement.faculty_id == faculty_id
    )

    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    # Update only provided fields
    update_data = achievement_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(achievement, field, value)

    achievement.updated_at = datetime.utcnow()
    await achievement.save()

    # Invalidate cache
    await cache_service.delete_pattern(f"achievements:{faculty_id}:*")
    await cache_service.delete(f"achievement_analytics:{faculty_id}")

    return achievement


@router.delete("/achievements/{achievement_id}", status_code=204)
async def delete_achievement(
    faculty_id: str,
    achievement_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an achievement.
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    achievement = await Achievement.find_one(
        Achievement.id == achievement_id,
        Achievement.faculty_id == faculty_id
    )

    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    await achievement.delete()

    # Invalidate cache
    await cache_service.delete_pattern(f"achievements:{faculty_id}:*")
    await cache_service.delete(f"achievement_analytics:{faculty_id}")

    return None


@router.post("/achievements/{achievement_id}/verify")
async def verify_achievement(
    faculty_id: str,
    achievement_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Request verification for an achievement.
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    achievement = await Achievement.find_one(
        Achievement.id == achievement_id,
        Achievement.faculty_id == faculty_id
    )

    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    # Add to verification queue (background task)
    background_tasks.add_task(
        achievement_service.request_verification,
        achievement
    )

    return {"message": "Verification request submitted"}


@router.get("/achievements/export")
async def export_achievements(
    faculty_id: str,
    format: str = Query("csv", regex="^(csv|pdf|json)$"),
    current_user: dict = Depends(get_current_user)
):
    """
    Export achievements in various formats.
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    achievements = await Achievement.find(
        Achievement.faculty_id == faculty_id
    ).to_list()

    if format == "csv":
        return await achievement_service.export_to_csv(achievements)
    elif format == "pdf":
        return await achievement_service.export_to_pdf(achievements)
    else:  # json
        return achievements