# app/api/v1/analytics.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import numpy as np

from app.core.security import get_current_user
from app.models.analytics import AnalyticsSnapshot, PerformanceMetric, SessionMetric
from app.models.student import Student
from app.models.faculty import Faculty
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

    # Get all mentees (students with this faculty as mentor)
    mentees = await Student.find(Student.faculty_mentor_id == faculty_id).to_list()
    total_mentees = len(mentees)
    active_mentees = len([m for m in mentees if m.is_active])

    # Calculate average SGPI
    if total_mentees > 0:
        avg_sgpi = sum(s.current_sgpi or 0 for s in mentees) / total_mentees
        prev_avg = sum(s.previous_sgpi or 0 for s in mentees) / total_mentees
    else:
        avg_sgpi = 0.0
        prev_avg = 0.0

    performance_change = ((avg_sgpi - prev_avg) / prev_avg * 100) if prev_avg > 0 else 0

    # Session analytics (filtered by date range)
    sessions = await MentorshipSession.find(
        MentorshipSession.faculty_id == faculty_id,
        MentorshipSession.date >= start_date,
        MentorshipSession.date <= end_date
    ).to_list()

    completed_sessions = len([s for s in sessions if s.status == 'completed'])
    avg_session_rating = np.mean([s.rating for s in sessions if s.rating]) if sessions else 0

    # Research papers
    papers = await ResearchPaper.find(ResearchPaper.faculty_id == faculty_id).to_list()
    total_citations = sum(p.citations or 0 for p in papers)

    # Performance trends
    performance_trends = await analytics_service.get_performance_trends(
        faculty_id, start_date, end_date
    )

    # Mentee distribution (e.g., by year, performance bucket)
    mentee_distribution = await analytics_service.get_mentee_distribution(faculty_id)

    # Session analytics details (average duration, satisfaction, etc.)
    session_analytics = await analytics_service.get_session_analytics(
        faculty_id, start_date, end_date
    )

    # Research metrics (e.g., publications per year, citation growth)
    research_metrics = await analytics_service.get_research_metrics(faculty_id)

    # Engagement metrics (e.g., response time, meeting frequency)
    engagement_metrics = await analytics_service.get_engagement_metrics(
        faculty_id, start_date, end_date
    )

    analytics_data = {
        "overview": {
            "totalMentees": total_mentees,
            "activeMentees": active_mentees,
            "avgPerformance": round(avg_sgpi, 2),
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
    current_user: dict = Depends(get_current_user)
):
    """
    Get ML-based predictions for performance and outcomes
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    cache_key = f"predictions:{faculty_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    # Get historical data for all mentees
    mentees = await Student.find(Student.faculty_mentor_id == faculty_id).to_list()

    # Prepare features for ML model
    features = []
    for mentee in mentees:
        # Convert to dict with numeric values
        features.append({
            'current_sgpi': mentee.current_sgpi or 0,
            'previous_sgpi': mentee.previous_sgpi or 0,
            'attendance': mentee.attendance_percentage or 0,
            'assignment_completion': mentee.assignment_completion_rate or 0,
            'sessions_attended': mentee.sessions_attended or 0,
            'days_since_last_session': (
                (datetime.utcnow() - mentee.last_session_date).days
                if mentee.last_session_date else 30
            )
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
    recommendations = await ml_service.generate_recommendations(faculty_id, features)

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
    current_user: dict = Depends(get_current_user)
):
    """
    Get comparative analytics against department averages
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Get faculty's department
    faculty = await Faculty.find_one(Faculty.id == faculty_id)
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")

    # Find all faculty in same department
    dept_faculty = await Faculty.find(Faculty.department == faculty.department).to_list()
    dept_faculty_ids = [f.id for f in dept_faculty]

    # Compute faculty's average student SGPI
    faculty_mentees = await Student.find(
        Student.faculty_mentor_id == faculty_id
    ).to_list()
    faculty_avg_sgpi = (
        sum(s.current_sgpi or 0 for s in faculty_mentees) / len(faculty_mentees)
        if faculty_mentees else 0.0
    )

    # Compute department average SGPI across all faculty
    all_mentees = await Student.find(
        Student.faculty_mentor_id.in_(dept_faculty_ids)
    ).to_list()
    dept_avg_sgpi = (
        sum(s.current_sgpi or 0 for s in all_mentees) / len(all_mentees)
        if all_mentees else 0.0
    )

    # Compute rank based on average SGPI
    faculty_averages = {}
    for fid in dept_faculty_ids:
        mentees = await Student.find(Student.faculty_mentor_id == fid).to_list()
        avg = sum(s.current_sgpi or 0 for s in mentees) / len(mentees) if mentees else 0.0
        faculty_averages[fid] = avg

    # Sort by average descending
    sorted_faculty = sorted(faculty_averages.items(), key=lambda x: x[1], reverse=True)
    rank = next(
        (i for i, (fid, _) in enumerate(sorted_faculty, 1) if fid == faculty_id),
        len(dept_faculty_ids)
    )

    # Calculate percentage above average
    above_average = (
        ((faculty_avg_sgpi - dept_avg_sgpi) / dept_avg_sgpi * 100)
        if dept_avg_sgpi > 0 else 0
    )

    # Calculate percentile
    percentile = ((len(dept_faculty_ids) - rank + 1) / len(dept_faculty_ids)) * 100

    return {
        "departmentRank": rank,
        "aboveAverage": round(above_average, 1),
        "percentile": round(percentile, 0),
        "departmentAverage": round(dept_avg_sgpi, 2),
        "facultyAverage": round(faculty_avg_sgpi, 2),
        "totalFaculty": len(dept_faculty_ids)
    }


@router.post("/analytics/export")
async def export_analytics(
    faculty_id: str,
    format: str = Query("pdf", regex="^(pdf|excel|csv)$"),
    range: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Export analytics report in various formats
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Get analytics data
    analytics_data = await get_faculty_analytics(faculty_id, range, current_user)

    # Generate report based on format
    if format == "pdf":
        file_path = await analytics_service.generate_pdf_report(
            faculty_id, analytics_data
        )
    elif format == "excel":
        file_path = await analytics_service.generate_excel_report(
            faculty_id, analytics_data
        )
    else:  # csv
        file_path = await analytics_service.generate_csv_report(
            faculty_id, analytics_data
        )

    return {"download_url": file_path}