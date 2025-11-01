# app/api/v1/analytics.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from app.core.security import get_current_user
from app.core.database import get_db
from app.models.analytics import AnalyticsSnapshot, PerformanceMetric, SessionMetric
from app.models.student import Student
from app.models.mentorship import MentorshipSession
from app.models.research import ResearchPaper
from app.schemas.analytics import (
    AnalyticsResponse,
    PerformanceTrendResponse,
    PredictionResponse,
    ComparativeAnalyticsResponse
)
from app.services.analytics_service import AnalyticsService
from app.services.ml_service import MLPredictionService
from app.services.cache_service import CacheService

router = APIRouter()
analytics_service = AnalyticsService()
ml_service = MLPredictionService()
cache_service = CacheService()

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_faculty_analytics(
    faculty_id: str,
    range: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive analytics for faculty member
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Check cache
    cache_key = f"analytics:{faculty_id}:{range}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached
    
    # Calculate date range
    end_date = datetime.utcnow()
    if range == "7d":
        start_date = end_date - timedelta(days=7)
    elif range == "30d":
        start_date = end_date - timedelta(days=30)
    elif range == "90d":
        start_date = end_date - timedelta(days=90)
    else:  # 1y
        start_date = end_date - timedelta(days=365)
    
    # Get all mentees
    mentees = db.query(Student).filter(
        Student.faculty_mentor_id == faculty_id
    ).all()
    
    total_mentees = len(mentees)
    active_mentees = len([m for m in mentees if m.is_active])
    
    # Calculate performance metrics
    avg_sgpi = db.query(func.avg(Student.current_sgpi)).filter(
        Student.faculty_mentor_id == faculty_id
    ).scalar() or 0.0
    
    previous_avg_sgpi = db.query(func.avg(Student.previous_sgpi)).filter(
        Student.faculty_mentor_id == faculty_id
    ).scalar() or 0.0
    
    performance_change = ((avg_sgpi - previous_avg_sgpi) / previous_avg_sgpi * 100) if previous_avg_sgpi > 0 else 0
    
    # Session analytics
    sessions = db.query(MentorshipSession).filter(
        and_(
            MentorshipSession.faculty_id == faculty_id,
            MentorshipSession.date >= start_date,
            MentorshipSession.date <= end_date
        )
    ).all()
    
    completed_sessions = len([s for s in sessions if s.status == 'completed'])
    avg_session_rating = np.mean([s.rating for s in sessions if s.rating]) if sessions else 0
    
    # Research metrics
    papers = db.query(ResearchPaper).filter(
        ResearchPaper.faculty_id == faculty_id
    ).all()
    
    total_citations = sum(paper.citations for paper in papers)
    
    # Performance trends
    performance_trends = await analytics_service.get_performance_trends(
        faculty_id, start_date, end_date, db
    )
    
    # Mentee distribution
    mentee_distribution = await analytics_service.get_mentee_distribution(
        faculty_id, db
    )
    
    # Session analytics details
    session_analytics = await analytics_service.get_session_analytics(
        faculty_id, start_date, end_date, db
    )
    
    # Research metrics
    research_metrics = await analytics_service.get_research_metrics(
        faculty_id, db
    )
    
    # Engagement metrics
    engagement_metrics = await analytics_service.get_engagement_metrics(
        faculty_id, start_date, end_date, db
    )
    
    analytics_data = {
        "overview": {
            "totalMentees": total_mentees,
            "activeMentees": active_mentees,
            "avgPerformance": round(float(avg_sgpi), 2),
            "performanceChange": round(performance_change, 2),
            "sessionsCompleted": completed_sessions,
            "avgSessionRating": round(avg_session_rating, 2),
            "researchPapers": len(papers),
            "citations": total_citations
        },
        "performanceTrends": performance_trends,
        "menteeDistribution": mentee_distribution,
        "sessionAnalytics": session_analytics,
        "researchMetrics": research_metrics,
        "engagementMetrics": engagement_metrics
    }
    
    # Cache for 5 minutes
    await cache_service.set(cache_key, analytics_data, expire=300)
    
    return analytics_data

@router.get("/analytics/predictions", response_model=PredictionResponse)
async def get_predictions(
    faculty_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get ML-based predictions for performance and outcomes
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Check cache
    cache_key = f"predictions:{faculty_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached
    
    # Get historical data
    mentees = db.query(Student).filter(
        Student.faculty_mentor_id == faculty_id
    ).all()
    
    # Prepare features for ML model
    features = []
    for mentee in mentees:
        features.append({
            'current_sgpi': mentee.current_sgpi,
            'previous_sgpi': mentee.previous_sgpi,
            'attendance': mentee.attendance_percentage,
            'assignment_completion': mentee.assignment_completion_rate,
            'sessions_attended': mentee.sessions_attended,
            'days_since_last_session': (datetime.utcnow() - mentee.last_session_date).days if mentee.last_session_date else 30
        })
    
    if not features:
        return {
            "nextMonthPerformance": 0,
            "atRiskCount": 0,
            "successProbability": 0,
            "recommendations": []
        }
    
    # Predict next month's average performance
    next_month_performance = await ml_service.predict_average_performance(features)
    
    # Identify at-risk students
    at_risk_predictions = await ml_service.predict_at_risk_students(features)
    at_risk_count = sum(1 for pred in at_risk_predictions if pred > 0.7)
    
    # Calculate success probability (meeting target SGPI)
    success_probability = await ml_service.calculate_success_probability(
        features, target_sgpi=7.5
    )
    
    # Generate AI recommendations
    recommendations = await ml_service.generate_recommendations(
        faculty_id, features, db
    )
    
    predictions = {
        "nextMonthPerformance": round(next_month_performance, 2),
        "atRiskCount": at_risk_count,
        "successProbability": round(success_probability * 100, 1),
        "recommendations": recommendations
    }
    
    # Cache for 1 hour
    await cache_service.set(cache_key, predictions, expire=3600)
    
    return predictions

@router.get("/analytics/comparative", response_model=ComparativeAnalyticsResponse)
async def get_comparative_analytics(
    faculty_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get comparative analytics against department averages
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Get faculty's department
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    
    # Faculty's average performance
    faculty_avg_sgpi = db.query(func.avg(Student.current_sgpi)).filter(
        Student.faculty_mentor_id == faculty_id
    ).scalar() or 0.0
    
    # Department average performance
    dept_faculty_ids = db.query(Faculty.id).filter(
        Faculty.department == faculty.department
    ).all()
    dept_faculty_ids = [f[0] for f in dept_faculty_ids]
    
    dept_avg_sgpi = db.query(func.avg(Student.current_sgpi)).filter(
        Student.faculty_mentor_id.in_(dept_faculty_ids)
    ).scalar() or 0.0
    
    # Calculate rank
    faculty_rankings = []
    for fid in dept_faculty_ids:
        avg = db.query(func.avg(Student.current_sgpi)).filter(
            Student.faculty_mentor_id == fid
        ).scalar() or 0.0
        faculty_rankings.append((fid, avg))
    
    faculty_rankings.sort(key=lambda x: x[1], reverse=True)
    rank = next(i for i, (fid, _) in enumerate(faculty_rankings, 1) if fid == faculty_id)
    
    # Calculate percentage above average
    above_average = ((faculty_avg_sgpi - dept_avg_sgpi) / dept_avg_sgpi * 100) if dept_avg_sgpi > 0 else 0
    
    # Calculate percentile
    percentile = ((len(dept_faculty_ids) - rank + 1) / len(dept_faculty_ids)) * 100
    
    return {
        "departmentRank": rank,
        "aboveAverage": round(above_average, 1),
        "percentile": round(percentile, 0),
        "departmentAverage": round(float(dept_avg_sgpi), 2),
        "facultyAverage": round(float(faculty_avg_sgpi), 2),
        "totalFaculty": len(dept_faculty_ids)
    }

@router.post("/analytics/export")
async def export_analytics(
    faculty_id: str,
    format: str = Query("pdf", regex="^(pdf|excel|csv)$"),
    range: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Export analytics report in various formats
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Get analytics data
    analytics_data = await get_faculty_analytics(faculty_id, range, db, current_user)
    
    if format == "pdf":
        file_path = await analytics_service.generate_pdf_report(
            faculty_id, analytics_data, db
        )
    elif format == "excel":
        file_path = await analytics_service.generate_excel_report(
            faculty_id, analytics_data, db
        )
    else:  # csv
        file_path = await analytics_service.generate_csv_report(
            faculty_id, analytics_data, db
        )
    
    return {"download_url": file_path}