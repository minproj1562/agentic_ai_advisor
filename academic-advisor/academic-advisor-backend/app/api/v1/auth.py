# app/api/v1/auth.py
"""
Analytics API endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta

from app.dependencies import get_current_user, get_faculty_user
from app.services.analytics_service import AnalyticsService
from app.utils.helpers import get_logger

logger = get_logger(__name__)
router = APIRouter()

analytics_service = AnalyticsService()


@router.get("/overview")
async def get_analytics_overview(
    department: Optional[str] = None,
    time_range: str = Query("current_semester"),
    current_user: dict = Depends(get_faculty_user)
):
    """
    Get analytics overview
    """
    try:
        overview = await analytics_service.get_overview(
            department=department or current_user.get('department'),
            time_range=time_range
        )
        
        return overview
        
    except Exception as e:
        logger.error(f"Error fetching analytics overview: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch overview")


@router.get("/performance-trends")
async def get_performance_trends(
    metric: str = Query("cgpa"),
    group_by: str = Query("batch"),
    department: Optional[str] = None,
    current_user: dict = Depends(get_faculty_user)
):
    """
    Get performance trends
    """
    try:
        trends = await analytics_service.get_performance_trends(
            metric=metric,
            group_by=group_by,
            department=department or current_user.get('department')
        )
        
        return trends
        
    except Exception as e:
        logger.error(f"Error fetching trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch trends")


@router.get("/risk-distribution")
async def get_risk_distribution(
    department: Optional[str] = None,
    semester: Optional[int] = None,
    current_user: dict = Depends(get_faculty_user)
):
    """
    Get risk distribution analysis
    """
    try:
        distribution = await analytics_service.get_risk_distribution(
            department=department or current_user.get('department'),
            semester=semester
        )
        
        return distribution
        
    except Exception as e:
        logger.error(f"Error fetching risk distribution: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch distribution")


@router.get("/weakness-analysis")
async def get_weakness_analysis(
    department: Optional[str] = None,
    top_n: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_faculty_user)
):
    """
    Get common weaknesses analysis
    """
    try:
        analysis = await analytics_service.analyze_common_weaknesses(
            department=department or current_user.get('department'),
            top_n=top_n
        )
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing weaknesses: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze weaknesses")


@router.get("/prediction-accuracy")
async def get_prediction_accuracy(
    model_type: str = Query("performance"),
    time_period: int = Query(30),
    current_user: dict = Depends(get_faculty_user)
):
    """
    Get ML model prediction accuracy metrics
    """
    try:
        accuracy = await analytics_service.get_prediction_accuracy(
            model_type=model_type,
            time_period=time_period
        )
        
        return accuracy
        
    except Exception as e:
        logger.error(f"Error fetching prediction accuracy: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch accuracy")


@router.get("/comparative-analysis")
async def get_comparative_analysis(
    entity_type: str = Query("department"),
    metric: str = Query("cgpa"),
    current_user: dict = Depends(get_faculty_user)
):
    """
    Get comparative analysis between entities
    """
    try:
        analysis = await analytics_service.get_comparative_analysis(
            entity_type=entity_type,
            metric=metric
        )
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error fetching comparative analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch analysis")


@router.get("/intervention-effectiveness")
async def get_intervention_effectiveness(
    department: Optional[str] = None,
    time_period: int = Query(90),
    current_user: dict = Depends(get_faculty_user)
):
    """
    Analyze effectiveness of interventions
    """
    try:
        effectiveness = await analytics_service.analyze_intervention_effectiveness(
            department=department or current_user.get('department'),
            time_period=time_period
        )
        
        return effectiveness
        
    except Exception as e:
        logger.error(f"Error analyzing effectiveness: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze effectiveness")


@router.get("/export")
async def export_analytics(
    format: str = Query("excel"),
    report_type: str = Query("comprehensive"),
    current_user: dict = Depends(get_faculty_user)
):
    """
    Export analytics report
    """
    try:
        report = await analytics_service.generate_report(
            report_type=report_type,
            format=format,
            department=current_user.get('department')
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Error exporting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export analytics")