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
from app.core.security import get_current_user, FirebaseUser

router = APIRouter()
logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════
#  DEPENDENCIES & HELPERS
# ════════════════════════════════════════════════════════════════


def get_service() -> WeaknessAnalysisService:
    """Dependency for getting the weakness analysis service."""
    return get_weakness_analysis_service()


def _get_recommended_action(sources: Dict[str, Any]) -> str:
    """Helper to recommend action based on sources state."""
    interest_profile = sources.get("StudentInterestProfile", {})
    student_profile = sources.get("StudentProfile", {})
    student_performance = sources.get("StudentPerformance", {})

    if interest_profile.get("interests"):
        return "All good! Interests are synced to StudentInterestProfile."
    elif student_profile.get("interests") or student_performance.get("interests"):
        return "Call GET /{student_id}/sync-interests to sync interests."
    else:
        return "No interests found. Use POST /{student_id}/interests to set interests."


# ════════════════════════════════════════════════════════════════
#  ANALYSIS ENDPOINTS
# ════════════════════════════════════════════════════════════════


@router.post("/analyze", response_model=WeaknessAnalysisResponse)
async def analyze_weaknesses(
    request: WeaknessAnalysisRequest,
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: FirebaseUser = Depends(get_current_user)
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
        logger.info(
            f"Analyzing weaknesses for student {request.student_id} "
            f"with basis {request.analysis_basis}"
        )
        result = await service.analyze_weaknesses(request)
        logger.info(f"Analysis complete: {result.total_weaknesses} weaknesses found")
        return result
    except Exception as e:
        logger.error(f"Error in weakness analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/by-interest", response_model=WeaknessAnalysisResponse)
async def get_weakness_by_interest(
    student_id: str,
    interests: Optional[str] = Query(
        None, description="Comma-separated list of interests"
    ),
    include_resources: bool = Query(True),
    include_study_plan: bool = Query(True),
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get weaknesses based on student's chosen interests.

    Analyzes which foundational subjects need improvement
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
        logger.error(f"Error analyzing by interest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/by-electives", response_model=WeaknessAnalysisResponse)
async def get_weakness_by_electives(
    student_id: str,
    electives: Optional[str] = Query(
        None, description="Comma-separated list of elective codes"
    ),
    include_resources: bool = Query(True),
    include_study_plan: bool = Query(True),
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: FirebaseUser = Depends(get_current_user)
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
        logger.error(f"Error analyzing by electives: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/by-honours", response_model=WeaknessAnalysisResponse)
async def get_weakness_by_honours(
    student_id: str,
    programmes: Optional[str] = Query(
        None, description="Comma-separated list of honours/minor programmes"
    ),
    include_resources: bool = Query(True),
    include_study_plan: bool = Query(True),
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: FirebaseUser = Depends(get_current_user)
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
        logger.error(f"Error analyzing by honours: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/by-performance", response_model=WeaknessAnalysisResponse)
async def get_weakness_by_performance(
    student_id: str,
    include_resources: bool = Query(True),
    include_study_plan: bool = Query(True),
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: FirebaseUser = Depends(get_current_user)
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
        logger.error(f"Error analyzing by performance: {e}", exc_info=True)
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
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get comprehensive weakness analysis combining all factors.

    Considers student interests, recommended electives,
    honours/minor goals, and overall academic performance.
    Weaknesses are deduplicated and prioritized.
    """
    try:
        interest_list = (
            [i.strip() for i in interests.split(",")] if interests else None
        )
        elective_list = (
            [e.strip() for e in electives.split(",")] if electives else None
        )
        honours_list = (
            [h.strip() for h in honours.split(",")] if honours else None
        )

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
        logger.error(f"Error in combined analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
#  CACHED / HISTORY ENDPOINTS
# ════════════════════════════════════════════════════════════════


@router.get("/{student_id}/latest")
async def get_latest_analysis(
    student_id: str,
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: FirebaseUser = Depends(get_current_user)
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
        logger.error(f"Error fetching latest analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/history")
async def get_analysis_history(
    student_id: str,
    limit: int = Query(10, ge=1, le=50),
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: FirebaseUser = Depends(get_current_user)
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
        logger.error(f"Error fetching analysis history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/summary")
async def get_weakness_summary(
    student_id: str,
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get a quick summary of student weaknesses.

    Lightweight endpoint for dashboard widgets.
    """
    try:
        result = await service.get_latest_analysis(student_id)

        if not result:
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
        logger.error(f"Error fetching summary: {e}", exc_info=True)
        return {
            "student_id": student_id,
            "has_analysis": False,
            "overall_risk_score": 0,
            "total_weaknesses": 0,
            "critical_count": 0,
            "high_count": 0,
            "priority_subjects": [],
            "needs_attention": False,
            "error": str(e)
        }


# ════════════════════════════════════════════════════════════════
#  INTEREST MANAGEMENT ENDPOINTS — ✅ FIXED
# ════════════════════════════════════════════════════════════════


@router.post("/{student_id}/interests")
async def save_student_interests(
    student_id: str,
    request: dict = Body(...),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Save or update student interests for weakness analysis."""
    try:
        # Extract all fields from raw dict - guaranteed to work
        interests = request.get("interests", [])
        interest_levels = request.get("interest_levels", {})
        career_goals = request.get("career_goals", [])
        skills = request.get("skills", [])
        skill_levels = request.get("skill_levels", {})
        preferred_electives = request.get("preferred_electives", [])
        honours_minors_interest = request.get("honours_minors_interest", [])

        logger.info(
            f"📥 POST /{student_id}/interests — "
            f"interests={len(interests)}, "
            f"career_goals={len(career_goals)}, "
            f"skills={len(skills)}, "
            f"preferred_electives={len(preferred_electives)}, "
            f"honours={len(honours_minors_interest)}"
        )

        if not interests:
            raise HTTPException(status_code=400, detail="interests is required and cannot be empty")

        profile = await StudentInterestProfile.find_one(
            {"user_id": student_id}
        )

        if profile:
            profile.interests = interests
            if interest_levels:
                profile.interest_levels = interest_levels
            if career_goals is not None:
                profile.career_goals = career_goals
            if skills is not None:
                profile.skills = skills
            if skill_levels:
                profile.skill_levels = skill_levels
            if preferred_electives is not None:
                profile.preferred_electives = preferred_electives
            if honours_minors_interest is not None:
                profile.honours_minors_interest = honours_minors_interest
            profile.updated_at = datetime.utcnow()
            await profile.save()
        else:
            profile = StudentInterestProfile(
                user_id=student_id,
                interests=interests,
                interest_levels=interest_levels or {},
                career_goals=career_goals or [],
                skills=skills or [],
                skill_levels=skill_levels or {},
                preferred_electives=preferred_electives or [],
                honours_minors_interest=honours_minors_interest or [],
            )
            await profile.save()

        logger.info(
            f"✅ POST saved for {student_id}: "
            f"interests={len(profile.interests)}, "
            f"career_goals={len(profile.career_goals)}, "
            f"skills={len(profile.skills)}"
        )

        return {
            "status": "success",
            "message": "Interests saved successfully",
            "interests": profile.interests,
            "career_goals": profile.career_goals,
            "skills": profile.skills,
            "preferred_electives": profile.preferred_electives,
            "honours_minors_interest": profile.honours_minors_interest,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving interests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/interests")
async def get_student_interests(
    student_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get student's saved interests."""
    try:
        profile = await StudentInterestProfile.find_one(
            {"user_id": student_id}
        )

        if not profile:
            return {
                "student_id": student_id,
                "interests": [],
                "interest_levels": {},
                "career_goals": [],
                "preferred_electives": [],
                "honours_minors_interest": [],
                "skills": [],
                "skill_levels": {}
            }

        return {
            "student_id": student_id,
            "interests": getattr(profile, 'interests', []) or [],
            "interest_levels": getattr(profile, 'interest_levels', {}) or {},
            "career_goals": getattr(profile, 'career_goals', []) or [],
            "preferred_electives": getattr(profile, 'preferred_electives', []) or [],
            "honours_minors_interest": getattr(profile, 'honours_minors_interest', []) or [],
            "skills": getattr(profile, 'skills', []) or [],
            "skill_levels": getattr(profile, 'skill_levels', {}) or {}
        }
    except Exception as e:
        logger.error(f"Error fetching interests: {e}", exc_info=True)
        return {
            "student_id": student_id,
            "interests": [],
            "interest_levels": {},
            "career_goals": [],
            "preferred_electives": [],
            "honours_minors_interest": [],
            "skills": [],
            "skill_levels": {}
        }


@router.put("/{student_id}/interests")
async def update_student_interests(
    student_id: str,
    request: dict = Body(...),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Update student interest profile with partial data."""
    try:
        logger.info(
            f"📥 PUT /{student_id}/interests — raw keys: {list(request.keys())}"
        )

        profile = await StudentInterestProfile.find_one(
            {"user_id": student_id}
        )

        if not profile:
            profile = StudentInterestProfile(user_id=student_id)

        if "interests" in request:
            profile.interests = request["interests"]
        if "interest_levels" in request:
            profile.interest_levels = request["interest_levels"]
        if "career_goals" in request:
            profile.career_goals = request["career_goals"]
        if "preferred_electives" in request:
            profile.preferred_electives = request["preferred_electives"]
        if "honours_minors_interest" in request:
            profile.honours_minors_interest = request["honours_minors_interest"]
        if "skills" in request:
            profile.skills = request["skills"]
        if "skill_levels" in request:
            profile.skill_levels = request["skill_levels"]

        profile.updated_at = datetime.utcnow()
        await profile.save()

        logger.info(
            f"✅ PUT saved for {student_id}: "
            f"interests={len(profile.interests)}, "
            f"career_goals={len(profile.career_goals)}, "
            f"skills={len(profile.skills)}"
        )

        return {
            "status": "success",
            "message": "Interest profile updated",
            "profile": {
                "interests": getattr(profile, 'interests', []) or [],
                "interest_levels": getattr(profile, 'interest_levels', {}) or {},
                "career_goals": getattr(profile, 'career_goals', []) or [],
                "skills": getattr(profile, 'skills', []) or [],
                "skill_levels": getattr(profile, 'skill_levels', {}) or {},
                "preferred_electives": getattr(profile, 'preferred_electives', []) or [],
                "honours_minors_interest": getattr(profile, 'honours_minors_interest', []) or [],
            }
        }
    except Exception as e:
        logger.error(f"Error updating interests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ════════════════════════════════════════════════════════════════
#  SYNC INTERESTS ENDPOINTS
# ════════════════════════════════════════════════════════════════


@router.get("/{student_id}/sync-interests")
async def sync_interests_from_all_sources(
    student_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Sync interests from all sources (StudentProfile, StudentPerformance, ML)
    to StudentInterestProfile for weakness analysis.
    """
    try:
        from app.models.student_profile import StudentProfile

        synced_interests: List[str] = []
        synced_career_goals: List[str] = []
        synced_skills: List[str] = []
        sources: List[str] = []

        # Check StudentProfile first
        try:
            profile = await StudentProfile.find_one({"user_id": student_id})
            if profile:
                if hasattr(profile, 'interests') and profile.interests:
                    synced_interests = profile.interests
                    sources.append("StudentProfile")
                    logger.info(
                        f"✅ Found {len(profile.interests)} interests in StudentProfile"
                    )
                if hasattr(profile, 'career_goals') and profile.career_goals:
                    synced_career_goals = profile.career_goals
                if hasattr(profile, 'skills') and profile.skills:
                    synced_skills = profile.skills
        except Exception as e:
            logger.warning(f"Could not check StudentProfile: {e}")

        # Check StudentPerformance if no interests found yet
        if not synced_interests:
            try:
                from app.models.student import StudentPerformance
                performance = await StudentPerformance.find_one(
                    {"student_info.uid": student_id}
                )
                if (
                    performance
                    and hasattr(performance, 'interests')
                    and performance.interests
                ):
                    synced_interests = performance.interests
                    sources.append("StudentPerformance (ML)")
                    logger.info(
                        f"✅ Found {len(performance.interests)} interests "
                        f"in StudentPerformance"
                    )
                    if (
                        hasattr(performance, 'career_goals')
                        and performance.career_goals
                    ):
                        synced_career_goals = performance.career_goals
                    if (
                        hasattr(performance, 'skills')
                        and performance.skills
                    ):
                        synced_skills = performance.skills
            except Exception as e:
                logger.warning(f"Could not check StudentPerformance: {e}")

        if not synced_interests:
            return {
                "status": "no_interests",
                "message": (
                    "No interests found in any source. "
                    "Please set interests first."
                ),
                "student_id": student_id,
                "interests": [],
                "career_goals": [],
                "skills": [],
                "sources": [],
                "sources_checked": ["StudentProfile", "StudentPerformance"],
                "suggestion": (
                    "Use POST /{student_id}/interests to set interests manually"
                )
            }

        # Save to StudentInterestProfile — ✅ FIXED: preserve existing fields
        action = "not_saved"
        try:
            interest_profile = await StudentInterestProfile.find_one(
                {"user_id": student_id}
            )

            if interest_profile:
                interest_profile.interests = synced_interests
                if synced_career_goals:
                    interest_profile.career_goals = synced_career_goals
                if synced_skills:
                    interest_profile.skills = synced_skills
                interest_profile.updated_at = datetime.utcnow()
                await interest_profile.save()
                action = "updated"
            else:
                interest_profile = StudentInterestProfile(
                    user_id=student_id,
                    interests=synced_interests,
                    career_goals=synced_career_goals or [],
                    skills=synced_skills or [],
                )
                await interest_profile.save()
                action = "created"
        except Exception as save_err:
            logger.error(f"Could not save interest profile: {save_err}")

        logger.info(
            f"📝 {action.title()} StudentInterestProfile "
            f"with {len(synced_interests)} interests, "
            f"{len(synced_career_goals)} career_goals, "
            f"{len(synced_skills)} skills"
        )

        return {
            "status": "success",
            "action": action,
            "interests": synced_interests,
            "career_goals": synced_career_goals,
            "skills": synced_skills,
            "sources": sources,
            "synced_at": datetime.utcnow().isoformat(),
            "message": (
                f"Successfully synced {len(synced_interests)} interests "
                f"from {', '.join(sources)}"
            )
        }
    except Exception as e:
        logger.error(f"❌ Error syncing interests: {e}", exc_info=True)
        return {
            "status": "failed",
            "message": str(e),
            "student_id": student_id,
            "interests": [],
            "career_goals": [],
            "skills": [],
            "sources": []
        }


@router.post("/{student_id}/sync-interests")
async def force_sync_interests(
    student_id: str,
    force_source: Optional[str] = Query(
        None,
        description=(
            "Force sync from specific source: "
            "'profile', 'performance', or 'all'"
        )
    ),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Force sync interests from specified source(s).

    - **profile**: Sync from StudentProfile only
    - **performance**: Sync from StudentPerformance (ML) only
    - **all**: Merge interests from all sources
    """
    try:
        from app.models.student_profile import StudentProfile

        all_interests: set = set()
        all_career_goals: set = set()
        all_skills: set = set()
        sources_used: List[str] = []

        # Get from StudentProfile
        if force_source in [None, 'profile', 'all']:
            try:
                profile = await StudentProfile.find_one(
                    {"user_id": student_id}
                )
                if (
                    profile
                    and hasattr(profile, 'interests')
                    and profile.interests
                ):
                    if force_source == 'all':
                        all_interests.update(profile.interests)
                    else:
                        all_interests = set(profile.interests)
                    if (
                        hasattr(profile, 'career_goals')
                        and profile.career_goals
                    ):
                        all_career_goals.update(profile.career_goals)
                    if (
                        hasattr(profile, 'skills')
                        and profile.skills
                    ):
                        all_skills.update(profile.skills)
                    sources_used.append("StudentProfile")
                    logger.info(
                        f"✅ Found {len(profile.interests)} interests "
                        f"in StudentProfile"
                    )
            except Exception as e:
                logger.warning(f"Could not check StudentProfile: {e}")

        # Get from StudentPerformance
        if force_source in [None, 'performance', 'all'] and (
            force_source != 'profile'
        ):
            try:
                from app.models.student import StudentPerformance
                performance = await StudentPerformance.find_one(
                    {"student_info.uid": student_id}
                )
                if (
                    performance
                    and hasattr(performance, 'interests')
                    and performance.interests
                ):
                    if force_source == 'all':
                        all_interests.update(performance.interests)
                    elif force_source == 'performance' or not all_interests:
                        all_interests = set(performance.interests)
                    if (
                        hasattr(performance, 'career_goals')
                        and performance.career_goals
                    ):
                        all_career_goals.update(performance.career_goals)
                    if (
                        hasattr(performance, 'skills')
                        and performance.skills
                    ):
                        all_skills.update(performance.skills)
                    sources_used.append("StudentPerformance")
                    logger.info(
                        f"✅ Found {len(performance.interests)} interests "
                        f"in StudentPerformance"
                    )
            except Exception as e:
                logger.warning(f"Could not check StudentPerformance: {e}")

        if not all_interests:
            return {
                "status": "no_interests",
                "message": "No interests found in specified source(s).",
                "student_id": student_id,
                "interests": [],
                "career_goals": [],
                "skills": [],
                "sources": [],
                "sources_checked": (
                    sources_used or ["None - invalid source specified"]
                ),
                "valid_sources": ["profile", "performance", "all"]
            }

        interests_list = list(all_interests)
        career_goals_list = list(all_career_goals)
        skills_list = list(all_skills)

        # Save to StudentInterestProfile — ✅ FIXED: preserve existing fields
        try:
            interest_profile = await StudentInterestProfile.find_one(
                {"user_id": student_id}
            )

            if interest_profile:
                interest_profile.interests = interests_list
                interest_profile.career_goals = career_goals_list
                if skills_list:
                    interest_profile.skills = skills_list
                interest_profile.updated_at = datetime.utcnow()
                await interest_profile.save()
                action = "updated"
            else:
                interest_profile = StudentInterestProfile(
                    user_id=student_id,
                    interests=interests_list,
                    career_goals=career_goals_list,
                    skills=skills_list,
                )
                await interest_profile.save()
                action = "created"
        except Exception as save_err:
            logger.error(f"Could not save interest profile: {save_err}")
            action = "not_saved"

        logger.info(
            f"📝 Force {action} StudentInterestProfile "
            f"with {len(interests_list)} interests, "
            f"{len(career_goals_list)} career_goals, "
            f"{len(skills_list)} skills"
        )

        return {
            "status": "success",
            "action": action,
            "force_source": force_source or "auto",
            "interests": interests_list,
            "career_goals": career_goals_list,
            "skills": skills_list,
            "sources": sources_used,
            "total_interests": len(interests_list),
            "synced_at": datetime.utcnow().isoformat(),
            "message": (
                f"Successfully force synced {len(interests_list)} interests "
                f"from {', '.join(sources_used)}"
            )
        }
    except Exception as e:
        logger.error(f"❌ Error force syncing interests: {e}", exc_info=True)
        return {
            "status": "failed",
            "message": str(e),
            "student_id": student_id,
            "interests": [],
            "career_goals": [],
            "skills": [],
            "sources": []
        }


# ════════════════════════════════════════════════════════════════
#  INTEREST SOURCES / DEBUG ENDPOINTS
# ════════════════════════════════════════════════════════════════


@router.get("/{student_id}/interests-sources")
async def check_interests_sources(
    student_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Check all sources for student interests.

    Useful for debugging when interests aren't showing up.
    Shows what's available in each data source.
    """
    try:
        from app.models.student_profile import StudentProfile

        sources: Dict[str, Any] = {}

        # Check StudentInterestProfile
        try:
            interest_profile = await StudentInterestProfile.find_one(
                {"user_id": student_id}
            )
            sources["StudentInterestProfile"] = {
                "found": interest_profile is not None,
                "interests": (
                    getattr(interest_profile, 'interests', [])
                    if interest_profile else []
                ),
                "career_goals": (
                    getattr(interest_profile, 'career_goals', [])
                    if interest_profile else []
                ),
                "skills": (
                    getattr(interest_profile, 'skills', [])
                    if interest_profile else []
                ),
                "preferred_electives": (
                    getattr(interest_profile, 'preferred_electives', [])
                    if interest_profile else []
                ),
                "honours_minors_interest": (
                    getattr(interest_profile, 'honours_minors_interest', [])
                    if interest_profile else []
                ),
                "updated_at": (
                    interest_profile.updated_at.isoformat()
                    if (
                        interest_profile
                        and hasattr(interest_profile, 'updated_at')
                        and interest_profile.updated_at
                    )
                    else None
                )
            }
        except Exception as e:
            sources["StudentInterestProfile"] = {
                "found": False, "interests": [], "error": str(e)
            }

        # Check StudentProfile
        try:
            profile = await StudentProfile.find_one({"user_id": student_id})
            sources["StudentProfile"] = {
                "found": profile is not None,
                "interests": (
                    profile.interests
                    if profile and hasattr(profile, 'interests') and profile.interests
                    else []
                ),
                "career_goals": (
                    profile.career_goals
                    if profile and hasattr(profile, 'career_goals') and profile.career_goals
                    else []
                ),
                "skills": (
                    profile.skills
                    if profile and hasattr(profile, 'skills') and profile.skills
                    else []
                ),
                "has_semester_records": (
                    len(profile.semester_records)
                    if profile and hasattr(profile, 'semester_records') and profile.semester_records
                    else 0
                )
            }
        except Exception as e:
            sources["StudentProfile"] = {
                "found": False, "interests": [], "error": str(e)
            }

        # Check StudentPerformance
        try:
            from app.models.student import StudentPerformance
            performance = await StudentPerformance.find_one(
                {"student_info.uid": student_id}
            )
            sources["StudentPerformance"] = {
                "found": performance is not None,
                "interests": (
                    performance.interests
                    if performance and hasattr(performance, 'interests') and performance.interests
                    else []
                ),
                "career_goals": (
                    performance.career_goals
                    if performance and hasattr(performance, 'career_goals') and performance.career_goals
                    else []
                ),
                "has_subjects": (
                    len(performance.subjects)
                    if performance and hasattr(performance, 'subjects') and performance.subjects
                    else 0
                )
            }
        except Exception as e:
            sources["StudentPerformance"] = {
                "found": False, "interests": [], "error": str(e)
            }

        # Summary
        all_interests: set = set()
        all_skills: set = set()
        for source_data in sources.values():
            if isinstance(source_data, dict):
                all_interests.update(source_data.get("interests", []))
                all_skills.update(source_data.get("skills", []))

        recommended_action = _get_recommended_action(sources)

        return {
            "student_id": student_id,
            "sources": sources,
            "summary": {
                "total_unique_interests": len(all_interests),
                "all_interests": list(all_interests),
                "total_unique_skills": len(all_skills),
                "all_skills": list(all_skills),
                "recommended_action": recommended_action
            }
        }
    except Exception as e:
        logger.error(f"❌ Error checking interest sources: {e}", exc_info=True)
        return {
            "student_id": student_id,
            "sources": {},
            "summary": {
                "total_unique_interests": 0,
                "all_interests": [],
                "total_unique_skills": 0,
                "all_skills": [],
                "recommended_action": "Error occurred. Please try again."
            },
            "error": str(e)
        }


@router.get("/{student_id}/debug")
async def debug_student_data(
    student_id: str,
    service: WeaknessAnalysisService = Depends(get_service),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Debug endpoint to see all data available for a student.

    Shows student data from all sources, interests, and latest analysis results.
    """
    try:
        from app.models.student_profile import StudentProfile

        debug_info: Dict[str, Any] = {
            "student_id": student_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Get student data from service
        try:
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
        except Exception as e:
            debug_info["student_data"] = {"error": str(e)}

        # Get interests from service method
        try:
            interests = await service._get_student_interests(student_id)
            debug_info["interests_from_service"] = interests
        except Exception as e:
            debug_info["interests_from_service"] = {"error": str(e)}

        # Get latest analysis
        try:
            latest_analysis = await service.get_latest_analysis(student_id)
            debug_info["latest_analysis"] = {
                "exists": latest_analysis is not None,
                "analysis_basis": (
                    latest_analysis.analysis_basis if latest_analysis else None
                ),
                "risk_score": (
                    latest_analysis.overall_risk_score if latest_analysis else None
                ),
                "weakness_count": (
                    len(latest_analysis.weaknesses) if latest_analysis else 0
                ),
                "analysis_date": (
                    latest_analysis.analysis_date.isoformat()
                    if latest_analysis else None
                )
            }
        except Exception as e:
            debug_info["latest_analysis"] = {"error": str(e)}

        # Check all interest sources — ✅ FIXED: include skills
        try:
            interest_profile = await StudentInterestProfile.find_one(
                {"user_id": student_id}
            )
            profile = await StudentProfile.find_one({"user_id": student_id})

            debug_info["interest_sources"] = {
                "StudentInterestProfile": {
                    "exists": interest_profile is not None,
                    "interests": (
                        getattr(interest_profile, 'interests', [])
                        if interest_profile else []
                    ),
                    "career_goals": (
                        getattr(interest_profile, 'career_goals', [])
                        if interest_profile else []
                    ),
                    "skills": (
                        getattr(interest_profile, 'skills', [])
                        if interest_profile else []
                    ),
                },
                "StudentProfile": {
                    "exists": profile is not None,
                    "interests": (
                        getattr(profile, 'interests', [])
                        if profile else []
                    ),
                    "career_goals": (
                        getattr(profile, 'career_goals', [])
                        if profile else []
                    ),
                    "skills": (
                        getattr(profile, 'skills', [])
                        if profile else []
                    ),
                }
            }

            try:
                from app.models.student import StudentPerformance
                performance = await StudentPerformance.find_one(
                    {"student_info.uid": student_id}
                )
                debug_info["interest_sources"]["StudentPerformance"] = {
                    "exists": performance is not None,
                    "interests": (
                        getattr(performance, 'interests', [])
                        if performance else []
                    ),
                    "career_goals": (
                        getattr(performance, 'career_goals', [])
                        if performance else []
                    ),
                }
            except Exception as e:
                debug_info["interest_sources"]["StudentPerformance"] = {
                    "error": str(e)
                }

        except Exception as e:
            debug_info["interest_sources"] = {"error": str(e)}

        return debug_info
    except Exception as e:
        logger.error(f"❌ Error in debug endpoint: {e}", exc_info=True)
        return {
            "student_id": student_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# ════════════════════════════════════════════════════════════════
#  AVAILABLE OPTIONS ENDPOINTS
# ════════════════════════════════════════════════════════════════


@router.get("/options/interests")
async def get_available_interests():
    """Get list of available interest areas for selection."""
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
    """Get list of available electives."""
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
    """Get list of available honours/minor programmes."""
    return {
        "programmes": [
            {"id": "ds_honours", "name": "Data Science Honours", "type": "honours", "min_cgpa": 7.5},
            {"id": "ai_minor", "name": "AI Minor", "type": "minor", "min_cgpa": 7.0},
            {"id": "cyber_minor", "name": "Cybersecurity Minor", "type": "minor", "min_cgpa": 7.0},
            {"id": "cloud_minor", "name": "Cloud Computing Minor", "type": "minor", "min_cgpa": 7.0}
        ]
    }