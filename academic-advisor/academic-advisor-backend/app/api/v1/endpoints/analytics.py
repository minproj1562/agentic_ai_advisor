#academic-advisor-backend/app/api/v1/endpoints/analytics.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.core.security import get_current_user, get_current_faculty
from app.services.analytics_service import AnalyticsService
from app.models.analytics import Analytics, WeaknessAnalysisResult
from app.core.exceptions import CustomException

router = APIRouter()
analytics_service = AnalyticsService()
logger = logging.getLogger(__name__)

@router.get("/performance-trends")
async def get_performance_trends(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_faculty)
):
    """
    Get performance trends for faculty's mentees
    """
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Validate date range
        if start > end:
            raise CustomException(
                status_code=400,
                detail="Start date cannot be after end date",
                code="INVALID_DATE_RANGE"
            )
        
        if (end - start).days > 365:
            raise CustomException(
                status_code=400,
                detail="Date range cannot exceed 1 year",
                code="DATE_RANGE_TOO_LARGE"
            )
        
        trends = await analytics_service.get_performance_trends(
            current_user.uid, start, end
        )
        
        return {
            "faculty_id": current_user.uid,
            "start_date": start_date,
            "end_date": end_date,
            "trends": trends,
            "summary": {
                "total_periods": len(trends),
                "avg_performance": round(
                    sum(t["avgPerformance"] for t in trends) / len(trends) if trends else 0, 
                    2
                ),
                "max_performance": max(
                    (t["avgPerformance"] for t in trends), 
                    default=0
                ),
                "min_performance": min(
                    (t["avgPerformance"] for t in trends), 
                    default=0
                )
            }
        }
        
    except ValueError as e:
        raise CustomException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD",
            code="INVALID_DATE_FORMAT"
        )
    except Exception as e:
        logger.error(f"Error fetching performance trends: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch performance trends"
        )

@router.get("/mentee-distribution")
async def get_mentee_distribution(
    current_user: dict = Depends(get_current_faculty)
):
    """
    Get mentee distribution by branch, semester, and performance
    """
    try:
        distribution = await analytics_service.get_mentee_distribution(current_user.uid)
        
        return {
            "faculty_id": current_user.uid,
            "distribution": distribution,
            "total_mentees": sum(
                branch["count"] for branch in distribution.get("byBranch", [])
            ),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching mentee distribution: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch mentee distribution"
        )

@router.get("/session-analytics")
async def get_session_analytics(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_faculty)
):
    """
    Get mentorship session analytics
    """
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Validate date range
        if start > end:
            raise CustomException(
                status_code=400,
                detail="Start date cannot be after end date",
                code="INVALID_DATE_RANGE"
            )
        
        analytics_data = await analytics_service.get_session_analytics(
            current_user.uid, start, end
        )
        
        return {
            "faculty_id": current_user.uid,
            "period": f"{start_date} to {end_date}",
            "analytics": analytics_data,
            "insights": await _generate_session_insights(analytics_data)
        }
        
    except ValueError as e:
        raise CustomException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD",
            code="INVALID_DATE_FORMAT"
        )
    except Exception as e:
        logger.error(f"Error fetching session analytics: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch session analytics"
        )

@router.get("/research-metrics")
async def get_research_metrics(
    current_user: dict = Depends(get_current_faculty)
):
    """
    Get research metrics and analytics
    """
    try:
        metrics = await analytics_service.get_research_metrics(current_user.uid)
        
        return {
            "faculty_id": current_user.uid,
            "research_metrics": metrics,
            "research_score": await _calculate_research_score(metrics),
            "comparison": await _get_research_comparison(metrics)
        }
        
    except Exception as e:
        logger.error(f"Error fetching research metrics: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch research metrics"
        )

@router.get("/engagement-metrics")
async def get_engagement_metrics(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_faculty)
):
    """
    Get faculty engagement metrics
    """
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        metrics = await analytics_service.get_engagement_metrics(
            current_user.uid, start, end
        )
        
        return {
            "faculty_id": current_user.uid,
            "period": f"{start_date} to {end_date}",
            "engagement_metrics": metrics,
            "engagement_level": _assess_engagement_level(metrics)
        }
        
    except ValueError as e:
        raise CustomException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD",
            code="INVALID_DATE_FORMAT"
        )
    except Exception as e:
        logger.error(f"Error fetching engagement metrics: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch engagement metrics"
        )

@router.get("/weakness-analysis")
async def get_weakness_analytics(
    student_id: Optional[str] = Query(None, description="Specific student ID"),
    subject_code: Optional[str] = Query(None, description="Specific subject code"),
    current_user: dict = Depends(get_current_faculty)
):
    """
    Get weakness analysis for mentees
    """
    try:
        # Build query based on parameters
        query = {}
        
        if student_id:
            query["student_id"] = student_id
        
        if subject_code:
            query["subject_code"] = subject_code
        
        # Only show current analyses by default
        query["is_current"] = True
        
        analyses = await WeaknessAnalysisResult.find(query).to_list()
        
        # Filter to only include the faculty's mentees
        # This would require joining with student profiles
        # For now, return all analyses (in production, implement proper filtering)
        
        return {
            "faculty_id": current_user.uid,
            "filters": {
                "student_id": student_id,
                "subject_code": subject_code
            },
            "total_analyses": len(analyses),
            "weakness_analyses": [
                {
                    "id": analysis.id,
                    "student_id": analysis.student_id,
                    "subject_name": analysis.subject_name,
                    "overall_score": analysis.overall_score,
                    "semester": analysis.semester,
                    "analysis_date": analysis.analysis_date,
                    "key_weaknesses": list(analysis.ai_analysis.get("weaknesses", {}).keys())[:3]
                }
                for analysis in analyses
            ],
            "summary": await _generate_weakness_summary(analyses)
        }
        
    except Exception as e:
        logger.error(f"Error fetching weakness analytics: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch weakness analytics"
        )

@router.get("/dashboard-overview")
async def get_dashboard_overview(
    current_user: dict = Depends(get_current_faculty)
):
    """
    Get comprehensive dashboard overview for faculty
    """
    try:
        # Get data for last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        # Fetch all analytics data in parallel
        performance_trends = await analytics_service.get_performance_trends(
            current_user.uid, start_date, end_date
        )
        mentee_distribution = await analytics_service.get_mentee_distribution(current_user.uid)
        session_analytics = await analytics_service.get_session_analytics(
            current_user.uid, start_date, end_date
        )
        research_metrics = await analytics_service.get_research_metrics(current_user.uid)
        engagement_metrics = await analytics_service.get_engagement_metrics(
            current_user.uid, start_date, end_date
        )
        
        # Calculate overall faculty score
        overall_score = await _calculate_faculty_score(
            performance_trends,
            session_analytics,
            research_metrics,
            engagement_metrics
        )
        
        return {
            "faculty_id": current_user.uid,
            "period": "Last 30 days",
            "overview": {
                "overall_score": overall_score,
                "performance_level": _get_performance_level(overall_score),
                "key_metrics": {
                    "total_mentees": sum(
                        branch["count"] for branch in mentee_distribution.get("byBranch", [])
                    ),
                    "active_sessions": session_analytics.get("completedSessions", 0),
                    "research_publications": research_metrics.get("totalPapers", 0),
                    "engagement_rate": engagement_metrics.get("engagementScore", 0)
                }
            },
            "quick_stats": {
                "avg_student_performance": _get_avg_performance(performance_trends),
                "session_completion_rate": session_analytics.get("completionRate", 0),
                "research_impact": research_metrics.get("hIndex", 0),
                "student_satisfaction": engagement_metrics.get("studentSatisfaction", 0)
            },
            "recent_activity": engagement_metrics.get("recentActivities", []),
            "alerts": await _generate_alerts(
                performance_trends,
                session_analytics,
                mentee_distribution
            )
        }
        
    except Exception as e:
        logger.error(f"Error fetching dashboard overview: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch dashboard overview"
        )

@router.get("/reports/generate")
async def generate_analytics_report(
    report_type: str = Query(..., description="Report type: pdf, excel, csv"),
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_faculty)
):
    """
    Generate analytics report in various formats
    """
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Collect all analytics data
        analytics_data = {
            "performance_trends": await analytics_service.get_performance_trends(
                current_user.uid, start, end
            ),
            "mentee_distribution": await analytics_service.get_mentee_distribution(current_user.uid),
            "session_analytics": await analytics_service.get_session_analytics(
                current_user.uid, start, end
            ),
            "research_metrics": await analytics_service.get_research_metrics(current_user.uid),
            "engagement_metrics": await analytics_service.get_engagement_metrics(
                current_user.uid, start, end
            ),
            "report_metadata": {
                "faculty_id": current_user.uid,
                "period": f"{start_date} to {end_date}",
                "generated_at": datetime.utcnow().isoformat(),
                "report_type": report_type
            }
        }
        
        # Generate report based on type
        if report_type == "pdf":
            report_url = await analytics_service.generate_pdf_report(
                current_user.uid, analytics_data
            )
        elif report_type == "excel":
            report_url = await analytics_service.generate_excel_report(
                current_user.uid, analytics_data
            )
        elif report_type == "csv":
            report_url = await analytics_service.generate_csv_report(
                current_user.uid, analytics_data
            )
        else:
            raise CustomException(
                status_code=400,
                detail="Invalid report type. Use: pdf, excel, csv",
                code="INVALID_REPORT_TYPE"
            )
        
        return {
            "faculty_id": current_user.uid,
            "report_type": report_type,
            "report_url": report_url,
            "generated_at": datetime.utcnow().isoformat(),
            "period": f"{start_date} to {end_date}"
        }
        
    except ValueError as e:
        raise CustomException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD",
            code="INVALID_DATE_FORMAT"
        )
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to generate analytics report"
        )

# Helper functions
async def _generate_session_insights(analytics_data: Dict[str, Any]) -> List[str]:
    """Generate insights from session analytics"""
    insights = []
    
    completion_rate = analytics_data.get("completionRate", 0)
    if completion_rate < 70:
        insights.append("Low session completion rate. Consider following up with students.")
    
    avg_rating = analytics_data.get("avgRating", 0)
    if avg_rating < 4.0:
        insights.append("Session ratings below average. Review session content and delivery.")
    
    day_dist = analytics_data.get("dayDistribution", [])
    if day_dist:
        busiest_day = max(day_dist, key=lambda x: x["count"])
        insights.append(f"Most sessions occur on {busiest_day['day']}. Consider scheduling accordingly.")
    
    return insights

async def _calculate_research_score(metrics: Dict[str, Any]) -> float:
    """Calculate overall research score"""
    total_papers = metrics.get("totalPapers", 0)
    h_index = metrics.get("hIndex", 0)
    avg_citations = metrics.get("avgCitations", 0)
    
    if total_papers == 0:
        return 0
    
    # Weighted score calculation
    paper_score = min(total_papers * 2, 40)  # Max 40 points for papers
    citation_score = min(avg_citations, 30)  # Max 30 points for citations
    h_index_score = min(h_index * 3, 30)  # Max 30 points for h-index
    
    return paper_score + citation_score + h_index_score

async def _get_research_comparison(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Get research comparison data (mock for now)"""
    return {
        "department_avg": {
            "papers": 15,
            "citations": 120,
            "h_index": 8
        },
        "institution_avg": {
            "papers": 25,
            "citations": 200,
            "h_index": 12
        },
        "your_metrics": {
            "papers": metrics.get("totalPapers", 0),
            "citations": metrics.get("totalCitations", 0),
            "h_index": metrics.get("hIndex", 0)
        }
    }

def _assess_engagement_level(metrics: Dict[str, Any]) -> str:
    """Assess engagement level based on metrics"""
    engagement_score = metrics.get("engagementScore", 0)
    
    if engagement_score >= 90:
        return "excellent"
    elif engagement_score >= 75:
        return "good"
    elif engagement_score >= 60:
        return "average"
    else:
        return "needs_improvement"

async def _generate_weakness_summary(analyses: List[WeaknessAnalysisResult]) -> Dict[str, Any]:
    """Generate summary of weakness analyses"""
    if not analyses:
        return {}
    
    total_analyses = len(analyses)
    avg_score = sum(analysis.overall_score for analysis in analyses) / total_analyses
    
    # Count weak subjects (score < 60)
    weak_subjects = len([a for a in analyses if a.overall_score < 60])
    
    # Common weaknesses
    all_weaknesses = []
    for analysis in analyses:
        weaknesses = analysis.ai_analysis.get("weaknesses", {})
        all_weaknesses.extend(weaknesses.keys())
    
    from collections import Counter
    common_weaknesses = Counter(all_weaknesses).most_common(5)
    
    return {
        "total_analyses": total_analyses,
        "average_score": round(avg_score, 2),
        "weak_subjects_count": weak_subjects,
        "weak_subjects_percentage": round((weak_subjects / total_analyses) * 100, 1),
        "common_weaknesses": [
            {"topic": topic, "frequency": count}
            for topic, count in common_weaknesses
        ]
    }

async def _calculate_faculty_score(
    performance_trends: List[Dict],
    session_analytics: Dict[str, Any],
    research_metrics: Dict[str, Any],
    engagement_metrics: Dict[str, Any]
) -> float:
    """Calculate overall faculty performance score"""
    # Performance component (40%)
    performance_avg = sum(t["avgPerformance"] for t in performance_trends) / len(performance_trends) if performance_trends else 0
    performance_score = (performance_avg / 10) * 40  # Convert 0-10 scale to 0-40
    
    # Session component (25%)
    completion_rate = session_analytics.get("completionRate", 0)
    avg_rating = session_analytics.get("avgRating", 0)
    session_score = (completion_rate * 0.15) + (avg_rating * 2)  # 15% completion, 10% rating
    
    # Research component (20%)
    research_score = await _calculate_research_score(research_metrics)
    research_score_normalized = (research_score / 100) * 20
    
    # Engagement component (15%)
    engagement_score = engagement_metrics.get("engagementScore", 0)
    engagement_score_normalized = (engagement_score / 100) * 15
    
    return round(
        performance_score + session_score + research_score_normalized + engagement_score_normalized, 
        2
    )

def _get_performance_level(score: float) -> str:
    """Get performance level based on score"""
    if score >= 90:
        return "excellent"
    elif score >= 75:
        return "good"
    elif score >= 60:
        return "satisfactory"
    else:
        return "needs_improvement"

def _get_avg_performance(performance_trends: List[Dict]) -> float:
    """Calculate average performance from trends"""
    if not performance_trends:
        return 0
    return round(sum(t["avgPerformance"] for t in performance_trends) / len(performance_trends), 2)

async def _generate_alerts(
    performance_trends: List[Dict],
    session_analytics: Dict[str, Any],
    mentee_distribution: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate alerts based on analytics data"""
    alerts = []
    
    # Performance alerts
    if performance_trends:
        recent_performance = performance_trends[-1]["avgPerformance"] if performance_trends else 0
        if recent_performance < 6.0:
            alerts.append({
                "type": "warning",
                "title": "Low Average Performance",
                "message": f"Recent average performance is {recent_performance:.2f}",
                "priority": "high"
            })
    
    # Session alerts
    completion_rate = session_analytics.get("completionRate", 0)
    if completion_rate < 70:
        alerts.append({
            "type": "warning",
            "title": "Low Session Completion",
            "message": f"Session completion rate is {completion_rate:.1f}%",
            "priority": "medium"
        })
    
    # Mentee distribution alerts
    performance_dist = mentee_distribution.get("byPerformance", {})
    needs_improvement = performance_dist.get("needs_improvement", 0)
    if needs_improvement > 5:
        alerts.append({
            "type": "info",
            "title": "Multiple Students Need Support",
            "message": f"{needs_improvement} students are performing below expectations",
            "priority": "medium"
        })
    
    return alerts