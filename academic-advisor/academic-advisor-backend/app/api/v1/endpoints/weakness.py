# app/api/v1/endpoints/weakness.py
"""
Weakness Analysis API Endpoints
Provides endpoints for analyzing student weaknesses based on:
- Student-selected interests
- Recommended electives and honours/minors
- Academic performance
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.models.weakness import (
    WeaknessAnalysisRequest,
    WeaknessAnalysisResponse,
    WeaknessAnalysisResult,
    AnalysisBasis,
    SeverityLevel,
    StudentInterestProfile
)
from app.services.weakness_analysis_service import (
    WeaknessAnalysisService,
    get_weakness_analysis_service
)
from app.core.security import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# Dependency for getting the service
def get_service() -> WeaknessAnalysisService:
    return get_weakness_analysis_service()


# Mock auth dependency for development
async def get_current_user_dev(
    authorization: Optional[str] = None
) -> Dict[str, Any]:
    """Development auth - replace with real auth in production"""
    return {"uid": "test_user", "email": "test@example.com"}


@router.post("/analyze", response_model=WeaknessAnalysisResponse)
async def analyze_weaknesses(
    request: WeaknessAnalysisRequest,
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Perform comprehensive weakness analysis.
    
    Analysis can be based on:
    - **interest**: Weaknesses related to student's chosen interests
    - **electives**: Weaknesses for recommended elective prerequisites
    - **honours_minors**: Weaknesses for honours/minor program requirements
    - **performance**: Pure academic performance analysis
    - **combined**: All of the above combined
    
    Returns detailed weakness areas with severity, suggestions, and resources.
    """
    try:
        logger.info(f"Analyzing weaknesses for student {request.student_id} with basis {request.analysis_basis}")
        
        # Validate that student can access this analysis
        if current_user["uid"] != request.student_id and current_user["uid"] != "test_user":
            # Allow if faculty or admin - add role check here
            pass
        
        result = await service.analyze_weaknesses(request)
        
        logger.info(f"Analysis complete: {result.total_weaknesses} weaknesses found")
        return result
        
    except Exception as e:
        logger.error(f"Error in weakness analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/by-interest", response_model=WeaknessAnalysisResponse)
async def get_weakness_by_interest(
    student_id: str,
    interests: Optional[str] = Query(None, description="Comma-separated list of interests"),
    include_resources: bool = Query(True),
    include_study_plan: bool = Query(True),
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Get weaknesses based on student's chosen interests.
    
    This analyzes which foundational subjects need improvement
    to excel in the chosen interest areas.
    
    Example interests: Machine Learning, Web Development, Cloud Computing
    """
    try:
        interest_list = None
        if interests:
            interest_list = [i.strip() for i in interests.split(",")]
        
        request = WeaknessAnalysisRequest(
            student_id=student_id,
            analysis_basis=AnalysisBasis.INTEREST,
            interests=interest_list,
            include_resources=include_resources,
            include_study_plan=include_study_plan
        )
        
        return await service.analyze_weaknesses(request)
        
    except Exception as e:
        logger.error(f"Error analyzing by interest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/by-electives", response_model=WeaknessAnalysisResponse)
async def get_weakness_by_electives(
    student_id: str,
    electives: Optional[str] = Query(None, description="Comma-separated list of elective codes"),
    include_resources: bool = Query(True),
    include_study_plan: bool = Query(True),
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Get weaknesses based on recommended electives.
    
    Analyzes prerequisite subjects needed for the electives.
    If no electives provided, uses AI-recommended electives.
    
    Example electives: ML, WT, DWM, CCS
    """
    try:
        elective_list = None
        if electives:
            elective_list = [e.strip() for e in electives.split(",")]
        
        request = WeaknessAnalysisRequest(
            student_id=student_id,
            analysis_basis=AnalysisBasis.ELECTIVES,
            recommended_electives=elective_list,
            include_resources=include_resources,
            include_study_plan=include_study_plan
        )
        
        return await service.analyze_weaknesses(request)
        
    except Exception as e:
        logger.error(f"Error analyzing by electives: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/by-honours", response_model=WeaknessAnalysisResponse)
async def get_weakness_by_honours(
    student_id: str,
    programmes: Optional[str] = Query(None, description="Comma-separated list of honours/minor programmes"),
    include_resources: bool = Query(True),
    include_study_plan: bool = Query(True),
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Get weaknesses based on honours/minor programmes.
    
    Analyzes subjects needed for eligibility and success in
    honours or minor programmes.
    
    Example programmes: Data Science Honours, AI Minor, Cybersecurity Minor
    """
    try:
        programme_list = None
        if programmes:
            programme_list = [p.strip() for p in programmes.split(",")]
        
        request = WeaknessAnalysisRequest(
            student_id=student_id,
            analysis_basis=AnalysisBasis.HONOURS_MINORS,
            honours_minors=programme_list,
            include_resources=include_resources,
            include_study_plan=include_study_plan
        )
        
        return await service.analyze_weaknesses(request)
        
    except Exception as e:
        logger.error(f"Error analyzing by honours: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/by-performance", response_model=WeaknessAnalysisResponse)
async def get_weakness_by_performance(
    student_id: str,
    include_resources: bool = Query(True),
    include_study_plan: bool = Query(True),
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Get weaknesses based on pure academic performance.
    
    Analyzes all subjects where performance is below expected levels,
    regardless of interests or elective choices.
    """
    try:
        request = WeaknessAnalysisRequest(
            student_id=student_id,
            analysis_basis=AnalysisBasis.PERFORMANCE,
            include_resources=include_resources,
            include_study_plan=include_study_plan
        )
        
        return await service.analyze_weaknesses(request)
        
    except Exception as e:
        logger.error(f"Error analyzing by performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/combined", response_model=WeaknessAnalysisResponse)
async def get_combined_weakness_analysis(
    student_id: str,
    interests: Optional[str] = Query(None),
    electives: Optional[str] = Query(None),
    honours: Optional[str] = Query(None),
    include_resources: bool = Query(True),
    include_study_plan: bool = Query(True),
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Get comprehensive weakness analysis combining all factors.
    
    This is the most complete analysis that considers:
    - Student interests
    - Recommended electives
    - Honours/minor goals
    - Overall academic performance
    
    Weaknesses are deduplicated and prioritized.
    """
    try:
        interest_list = [i.strip() for i in interests.split(",")] if interests else None
        elective_list = [e.strip() for e in electives.split(",")] if electives else None
        honours_list = [h.strip() for h in honours.split(",")] if honours else None
        
        request = WeaknessAnalysisRequest(
            student_id=student_id,
            analysis_basis=AnalysisBasis.COMBINED,
            interests=interest_list,
            recommended_electives=elective_list,
            honours_minors=honours_list,
            include_resources=include_resources,
            include_study_plan=include_study_plan
        )
        
        return await service.analyze_weaknesses(request)
        
    except Exception as e:
        logger.error(f"Error in combined analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/latest")
async def get_latest_analysis(
    student_id: str,
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Get the most recent weakness analysis for a student.
    
    Returns cached analysis if available, avoiding recomputation.
    """
    try:
        result = await service.get_latest_analysis(student_id)
        
        if not result:
            raise HTTPException(
                status_code=404, 
                detail="No analysis found. Run analysis first."
            )
        
        return {
            "student_id": result.student_id,
            "analysis_basis": result.analysis_basis,
            "overall_risk_score": result.overall_risk_score,
            "weaknesses": result.weaknesses,
            "priority_areas": result.priority_areas,
            "key_insights": result.key_insights,
            "study_plan": result.study_plan,
            "recommended_resources": result.recommended_resources,
            "analysis_date": result.analysis_date.isoformat(),
            "related_interests": result.related_interests,
            "related_electives": result.related_electives,
            "related_honours": result.related_honours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/history")
async def get_analysis_history(
    student_id: str,
    limit: int = Query(10, ge=1, le=50),
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Get weakness analysis history for a student.
    
    Useful for tracking improvement over time.
    """
    try:
        results = await service.get_analysis_history(student_id, limit)
        
        return {
            "student_id": student_id,
            "total_analyses": len(results),
            "history": [
                {
                    "id": str(r.id) if hasattr(r, 'id') else None,
                    "analysis_basis": r.analysis_basis,
                    "overall_risk_score": r.overall_risk_score,
                    "weakness_count": len(r.weaknesses),
                    "priority_areas": r.priority_areas[:3],
                    "analysis_date": r.analysis_date.isoformat(),
                    "is_current": r.is_current
                }
                for r in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching analysis history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/summary")
async def get_weakness_summary(
    student_id: str,
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Get a quick summary of student weaknesses.
    
    Lightweight endpoint for dashboard widgets.
    """
    try:
        result = await service.get_latest_analysis(student_id)
        
        if not result:
            # Return empty summary if no analysis exists
            return {
                "student_id": student_id,
                "has_analysis": False,
                "overall_risk_score": 0,
                "total_weaknesses": 0,
                "critical_count": 0,
                "high_count": 0,
                "priority_subjects": [],
                "needs_attention": False
            }
        
        ai_analysis = result.ai_analysis or {}
        
        return {
            "student_id": student_id,
            "has_analysis": True,
            "overall_risk_score": result.overall_risk_score,
            "total_weaknesses": len(result.weaknesses),
            "critical_count": ai_analysis.get("critical_count", 0),
            "high_count": ai_analysis.get("high_count", 0),
            "priority_subjects": result.priority_areas[:3],
            "needs_attention": result.overall_risk_score > 50,
            "last_analyzed": result.analysis_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Interest Management Endpoints ==============

@router.post("/{student_id}/interests")
async def save_student_interests(
    student_id: str,
    interests: List[str] = Body(..., embed=True),
    interest_levels: Optional[Dict[str, int]] = Body(None, embed=True),
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Save or update student interests for weakness analysis.
    """
    try:
        # Find existing profile or create new
        profile = await StudentInterestProfile.find_one(
            StudentInterestProfile.user_id == student_id
        )
        
        if profile:
            profile.interests = interests
            if interest_levels:
                profile.interest_levels = interest_levels
            profile.updated_at = datetime.utcnow()
            await profile.save()
        else:
            profile = StudentInterestProfile(
                user_id=student_id,
                interests=interests,
                interest_levels=interest_levels or {}
            )
            await profile.save()
        
        return {
            "status": "success",
            "message": "Interests saved successfully",
            "interests": interests
        }
        
    except Exception as e:
        logger.error(f"Error saving interests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/interests")
async def get_student_interests(
    student_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Get student's saved interests.
    """
    try:
        profile = await StudentInterestProfile.find_one(
            StudentInterestProfile.user_id == student_id
        )
        
        if not profile:
            return {
                "student_id": student_id,
                "interests": [],
                "interest_levels": {},
                "career_goals": [],
                "skills": []
            }
        
        return {
            "student_id": student_id,
            "interests": profile.interests,
            "interest_levels": profile.interest_levels,
            "career_goals": profile.career_goals,
            "preferred_electives": profile.preferred_electives,
            "honours_minors_interest": profile.honours_minors_interest,
            "skills": profile.skills,
            "skill_levels": profile.skill_levels
        }
        
    except Exception as e:
        logger.error(f"Error fetching interests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{student_id}/interests")
async def update_student_interests(
    student_id: str,
    interests: Optional[List[str]] = Body(None),
    interest_levels: Optional[Dict[str, int]] = Body(None),
    career_goals: Optional[List[str]] = Body(None),
    preferred_electives: Optional[List[str]] = Body(None),
    honours_minors_interest: Optional[List[str]] = Body(None),
    skills: Optional[List[str]] = Body(None),
    skill_levels: Optional[Dict[str, int]] = Body(None),
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Update student interest profile with partial data.
    """
    try:
        profile = await StudentInterestProfile.find_one(
            StudentInterestProfile.user_id == student_id
        )
        
        if not profile:
            profile = StudentInterestProfile(user_id=student_id)
        
        if interests is not None:
            profile.interests = interests
        if interest_levels is not None:
            profile.interest_levels = interest_levels
        if career_goals is not None:
            profile.career_goals = career_goals
        if preferred_electives is not None:
            profile.preferred_electives = preferred_electives
        if honours_minors_interest is not None:
            profile.honours_minors_interest = honours_minors_interest
        if skills is not None:
            profile.skills = skills
        if skill_levels is not None:
            profile.skill_levels = skill_levels
        
        profile.updated_at = datetime.utcnow()
        await profile.save()
        
        return {
            "status": "success",
            "message": "Interest profile updated",
            "profile": {
                "interests": profile.interests,
                "career_goals": profile.career_goals,
                "preferred_electives": profile.preferred_electives
            }
        }
        
    except Exception as e:
        logger.error(f"Error updating interests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Sync Interests Endpoint ==============

@router.get("/{student_id}/sync-interests")
async def sync_interests_from_all_sources(
    student_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Manually sync interests from all sources (StudentProfile, StudentPerformance, ML)
    to StudentInterestProfile for weakness analysis.
    Use this if interests aren't showing up in weakness analysis.
    """
    try:
        from app.models.student import StudentPerformance
        from app.models.student_profile import StudentProfile
        
        synced_interests = []
        synced_career_goals = []
        sources = []
        
        # Check StudentProfile first
        profile = await StudentProfile.find_one(
            StudentProfile.user_id == student_id
        )
        if profile and profile.interests:
            synced_interests = profile.interests
            if profile.career_goals:
                synced_career_goals = profile.career_goals
            sources.append("StudentProfile")
            logger.info(f"✅ Found {len(profile.interests)} interests in StudentProfile")
        
        # Check StudentPerformance (ML service) if no interests found yet
        if not synced_interests:
            performance = await StudentPerformance.find_one(
                StudentPerformance.student_info.uid == student_id
            )
            if performance and performance.interests:
                synced_interests = performance.interests
                if hasattr(performance, 'career_goals') and performance.career_goals:
                    synced_career_goals = performance.career_goals
                sources.append("StudentPerformance (ML)")
                logger.info(f"✅ Found {len(performance.interests)} interests in StudentPerformance")
        
        if not synced_interests:
            return {
                "status": "no_interests",
                "message": "No interests found in any source. Please set interests first.",
                "student_id": student_id,
                "sources_checked": ["StudentProfile", "StudentPerformance"],
                "suggestion": "Use POST /{student_id}/interests to set interests manually"
            }
        
        # Save to StudentInterestProfile for weakness analysis
        interest_profile = await StudentInterestProfile.find_one(
            StudentInterestProfile.user_id == student_id
        )
        
        if interest_profile:
            # Update existing profile
            interest_profile.interests = synced_interests
            if synced_career_goals:
                interest_profile.career_goals = synced_career_goals
            interest_profile.updated_at = datetime.utcnow()
            await interest_profile.save()
            action = "updated"
        else:
            # Create new profile
            interest_profile = StudentInterestProfile(
                user_id=student_id,
                interests=synced_interests,
                career_goals=synced_career_goals if synced_career_goals else []
            )
            await interest_profile.save()
            action = "created"
        
        logger.info(f"📝 {action.title()} StudentInterestProfile with {len(synced_interests)} interests")
        
        return {
            "status": "success",
            "action": action,
            "interests": synced_interests,
            "career_goals": synced_career_goals,
            "sources": sources,
            "synced_at": datetime.utcnow().isoformat(),
            "message": f"Successfully synced {len(synced_interests)} interests from {', '.join(sources)}"
        }
        
    except Exception as e:
        logger.error(f"❌ Error syncing interests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{student_id}/sync-interests")
async def force_sync_interests(
    student_id: str,
    force_source: Optional[str] = Query(
        None, 
        description="Force sync from specific source: 'profile', 'performance', or 'all'"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Force sync interests from specified source(s).
    
    Use this when you want to override existing interests with data from a specific source.
    
    - **profile**: Sync from StudentProfile only
    - **performance**: Sync from StudentPerformance (ML) only
    - **all**: Merge interests from all sources
    """
    try:
        from app.models.student import StudentPerformance
        from app.models.student_profile import StudentProfile
        
        all_interests = set()
        all_career_goals = set()
        sources_used = []
        
        # Get from StudentProfile
        if force_source in [None, 'profile', 'all']:
            profile = await StudentProfile.find_one(
                StudentProfile.user_id == student_id
            )
            if profile and profile.interests:
                if force_source == 'all':
                    all_interests.update(profile.interests)
                else:
                    all_interests = set(profile.interests)
                if profile.career_goals:
                    all_career_goals.update(profile.career_goals)
                sources_used.append("StudentProfile")
                logger.info(f"✅ Found {len(profile.interests)} interests in StudentProfile")
        
        # Get from StudentPerformance
        if force_source in [None, 'performance', 'all'] and (force_source != 'profile'):
            performance = await StudentPerformance.find_one(
                StudentPerformance.student_info.uid == student_id
            )
            if performance and performance.interests:
                if force_source == 'all':
                    all_interests.update(performance.interests)
                elif force_source == 'performance' or not all_interests:
                    all_interests = set(performance.interests)
                if hasattr(performance, 'career_goals') and performance.career_goals:
                    all_career_goals.update(performance.career_goals)
                sources_used.append("StudentPerformance")
                logger.info(f"✅ Found {len(performance.interests)} interests in StudentPerformance")
        
        if not all_interests:
            return {
                "status": "no_interests",
                "message": "No interests found in specified source(s).",
                "student_id": student_id,
                "sources_checked": sources_used or ["None - invalid source specified"],
                "valid_sources": ["profile", "performance", "all"]
            }
        
        # Convert sets to lists
        interests_list = list(all_interests)
        career_goals_list = list(all_career_goals)
        
        # Save to StudentInterestProfile
        interest_profile = await StudentInterestProfile.find_one(
            StudentInterestProfile.user_id == student_id
        )
        
        if interest_profile:
            interest_profile.interests = interests_list
            interest_profile.career_goals = career_goals_list
            interest_profile.updated_at = datetime.utcnow()
            await interest_profile.save()
            action = "updated"
        else:
            interest_profile = StudentInterestProfile(
                user_id=student_id,
                interests=interests_list,
                career_goals=career_goals_list
            )
            await interest_profile.save()
            action = "created"
        
        logger.info(f"📝 Force {action} StudentInterestProfile with {len(interests_list)} interests")
        
        return {
            "status": "success",
            "action": action,
            "force_source": force_source or "auto",
            "interests": interests_list,
            "career_goals": career_goals_list,
            "sources": sources_used,
            "total_interests": len(interests_list),
            "synced_at": datetime.utcnow().isoformat(),
            "message": f"Successfully force synced {len(interests_list)} interests from {', '.join(sources_used)}"
        }
        
    except Exception as e:
        logger.error(f"❌ Error force syncing interests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/interests-sources")
async def check_interests_sources(
    student_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Check all sources for student interests.
    
    Useful for debugging when interests aren't showing up.
    Shows what's available in each data source.
    """
    try:
        from app.models.student import StudentPerformance
        from app.models.student_profile import StudentProfile
        
        sources = {}
        
        # Check StudentInterestProfile
        interest_profile = await StudentInterestProfile.find_one(
            StudentInterestProfile.user_id == student_id
        )
        sources["StudentInterestProfile"] = {
            "found": interest_profile is not None,
            "interests": interest_profile.interests if interest_profile else [],
            "career_goals": interest_profile.career_goals if interest_profile else [],
            "updated_at": interest_profile.updated_at.isoformat() if interest_profile and interest_profile.updated_at else None
        }
        
        # Check StudentProfile
        profile = await StudentProfile.find_one(
            StudentProfile.user_id == student_id
        )
        sources["StudentProfile"] = {
            "found": profile is not None,
            "interests": profile.interests if profile and profile.interests else [],
            "career_goals": profile.career_goals if profile and profile.career_goals else [],
            "has_semester_records": len(profile.semester_records) if profile and profile.semester_records else 0
        }
        
        # Check StudentPerformance
        performance = await StudentPerformance.find_one(
            StudentPerformance.student_info.uid == student_id
        )
        sources["StudentPerformance"] = {
            "found": performance is not None,
            "interests": performance.interests if performance and performance.interests else [],
            "career_goals": performance.career_goals if performance and hasattr(performance, 'career_goals') and performance.career_goals else [],
            "has_subjects": len(performance.subjects) if performance and performance.subjects else 0
        }
        
        # Summary
        all_interests = set()
        for source_data in sources.values():
            all_interests.update(source_data.get("interests", []))
        
        return {
            "student_id": student_id,
            "sources": sources,
            "summary": {
                "total_unique_interests": len(all_interests),
                "all_interests": list(all_interests),
                "recommended_action": self._get_recommended_action(sources)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking interest sources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _get_recommended_action(sources: Dict[str, Any]) -> str:
    """Helper to recommend action based on sources state"""
    interest_profile = sources.get("StudentInterestProfile", {})
    student_profile = sources.get("StudentProfile", {})
    student_performance = sources.get("StudentPerformance", {})
    
    if interest_profile.get("interests"):
        return "All good! Interests are synced to StudentInterestProfile."
    elif student_profile.get("interests") or student_performance.get("interests"):
        return "Call GET /{student_id}/sync-interests to sync interests."
    else:
        return "No interests found. Use POST /{student_id}/interests to set interests."


# ============== Available Options Endpoints ==============

@router.get("/options/interests")
async def get_available_interests():
    """
    Get list of available interest areas for selection.
    """
    return {
        "interests": [
            {"id": "ml", "name": "Machine Learning", "category": "AI/ML"},
            {"id": "ai", "name": "Artificial Intelligence", "category": "AI/ML"},
            {"id": "ds", "name": "Data Science", "category": "Data"},
            {"id": "web", "name": "Web Development", "category": "Development"},
            {"id": "mobile", "name": "Mobile Development", "category": "Development"},
            {"id": "cloud", "name": "Cloud Computing", "category": "Infrastructure"},
            {"id": "devops", "name": "DevOps", "category": "Infrastructure"},
            {"id": "security", "name": "Cybersecurity", "category": "Security"},
            {"id": "iot", "name": "IoT", "category": "Embedded"},
            {"id": "blockchain", "name": "Blockchain", "category": "Emerging Tech"}
        ]
    }


@router.get("/options/electives")
async def get_available_electives():
    """
    Get list of available electives.
    """
    return {
        "electives": [
            {"code": "ML", "name": "Machine Learning", "credits": 4, "pair": 1},
            {"code": "WT", "name": "Wireless Technology", "credits": 4, "pair": 1},
            {"code": "DWM", "name": "Data Warehouse and Data Mining", "credits": 4, "pair": 2},
            {"code": "CCS", "name": "Cloud Computing Services", "credits": 4, "pair": 2},
            {"code": "NLP", "name": "Natural Language Processing", "credits": 3, "pair": 3},
            {"code": "CV", "name": "Computer Vision", "credits": 3, "pair": 3}
        ]
    }


@router.get("/options/honours")
async def get_available_honours():
    """
    Get list of available honours/minor programmes.
    """
    return {
        "programmes": [
            {"id": "ds_honours", "name": "Data Science Honours", "type": "honours", "min_cgpa": 7.5},
            {"id": "ai_minor", "name": "AI Minor", "type": "minor", "min_cgpa": 7.0},
            {"id": "cyber_minor", "name": "Cybersecurity Minor", "type": "minor", "min_cgpa": 7.0},
            {"id": "cloud_minor", "name": "Cloud Computing Minor", "type": "minor", "min_cgpa": 7.0}
        ]
    }


# ============== Diagnostic Endpoints ==============

@router.get("/{student_id}/debug")
async def debug_student_data(
    student_id: str,
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: Dict[str, Any] = Depends(get_current_user_dev)
):
    """
    Debug endpoint to see all data available for a student.
    
    Shows:
    - Student data from all sources
    - Interests from all sources
    - Latest analysis results
    """
    try:
        from app.models.student import StudentPerformance
        from app.models.student_profile import StudentProfile
        
        debug_info = {
            "student_id": student_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Get student data from service
        student_data = await service._get_student_data(student_id)
        debug_info["student_data"] = {
            "cgpa": student_data.get("cgpa"),
            "sgpa": student_data.get("sgpa"),
            "semester": student_data.get("semester"),
            "branch": student_data.get("branch"),
            "subjects_count": len(student_data.get("subjects", {})),
            "subjects": list(student_data.get("subjects", {}).keys()),
            "strong_subjects": student_data.get("strong_subjects", []),
            "weak_subjects": student_data.get("weak_subjects", []),
            "interests_in_data": student_data.get("interests", []),
            "career_goals_in_data": student_data.get("career_goals", [])
        }
        
        # Get interests from service method
        interests = await service._get_student_interests(student_id)
        debug_info["interests_from_service"] = interests
        
        # Get latest analysis
        latest_analysis = await service.get_latest_analysis(student_id)
        debug_info["latest_analysis"] = {
            "exists": latest_analysis is not None,
            "analysis_basis": latest_analysis.analysis_basis if latest_analysis else None,
            "risk_score": latest_analysis.overall_risk_score if latest_analysis else None,
            "weakness_count": len(latest_analysis.weaknesses) if latest_analysis else 0,
            "analysis_date": latest_analysis.analysis_date.isoformat() if latest_analysis else None
        }
        
        # Check all interest sources
        interest_profile = await StudentInterestProfile.find_one(
            StudentInterestProfile.user_id == student_id
        )
        profile = await StudentProfile.find_one(
            StudentProfile.user_id == student_id
        )
        performance = await StudentPerformance.find_one(
            StudentPerformance.student_info.uid == student_id
        )
        
        debug_info["interest_sources"] = {
            "StudentInterestProfile": {
                "exists": interest_profile is not None,
                "interests": interest_profile.interests if interest_profile else []
            },
            "StudentProfile": {
                "exists": profile is not None,
                "interests": profile.interests if profile else []
            },
            "StudentPerformance": {
                "exists": performance is not None,
                "interests": performance.interests if performance else []
            }
        }
        
        return debug_info
        
    except Exception as e:
        logger.error(f"❌ Error in debug endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))