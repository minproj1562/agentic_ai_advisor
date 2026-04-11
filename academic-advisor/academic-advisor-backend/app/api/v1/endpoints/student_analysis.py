# academic-advisor-backend/app/api/v1/endpoints/student_analysis.py

"""
Student Analysis Endpoints - Fetches from MongoDB student_profiles collection
Returns data in same format as admin endpoints for consistency
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import re

from app.core.security import get_current_user, FirebaseUser
from app.models.student_profile import StudentProfile
from app.models.student_projects import StudentProject

router = APIRouter()
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# HELPER FUNCTIONS (unchanged)
# ══════════════════════════════════════════════════════════

def _derive_name_from_email(email: str) -> str:
    """Extract a readable name from email address"""
    if not email:
        return "Unknown Student"
    local_part = email.split("@")[0]
    clean = re.sub(r"[0-9]+", "", local_part)
    clean = re.sub(r"[._-]", " ", clean)
    name = clean.strip().title()
    return name if name else local_part


def calculate_risk_score(profile: StudentProfile) -> tuple:
    """Calculate risk score and level based on performance"""
    risk_score = 0

    if profile.cgpa < 5.0:
        risk_score += 40
    elif profile.cgpa < 6.0:
        risk_score += 25
    elif profile.cgpa < 7.0:
        risk_score += 10

    completed_sems = len([s for s in profile.semester_records if s.is_complete])
    if completed_sems > 0:
        for sem in profile.semester_records:
            for subj in sem.subjects:
                if subj.grade == "F":
                    risk_score += 15
                elif subj.total_marks < 50:
                    risk_score += 5

    if completed_sems == 0:
        risk_score += 10

    if risk_score >= 50:
        risk_level = "high"
    elif risk_score >= 25:
        risk_level = "medium"
    else:
        risk_level = "low"

    return min(risk_score, 100), risk_level


def calculate_improvement_trend(profile: StudentProfile) -> str:
    """Calculate performance trend based on SGPA history"""
    sorted_sems = sorted(
        [s for s in profile.semester_records if s.is_complete],
        key=lambda x: x.semester_number,
    )
    if len(sorted_sems) < 2:
        return "stable"

    recent_sgpas = [s.sgpa for s in sorted_sems[-3:]]
    if len(recent_sgpas) < 2:
        return "stable"

    trend = recent_sgpas[-1] - recent_sgpas[0]
    if trend > 0.3:
        return "improving"
    elif trend < -0.3:
        return "declining"
    return "stable"


def identify_weaknesses(profile: StudentProfile) -> List[Dict[str, Any]]:
    """Identify weak subjects/areas from semester records"""
    weaknesses = []
    for sem in profile.semester_records:
        for subj in sem.subjects:
            severity = None
            gap = 0
            if subj.total_marks < 40:
                severity = "critical"
                gap = 50 - subj.total_marks
            elif subj.total_marks < 50:
                severity = "high"
                gap = 50 - subj.total_marks
            elif subj.total_marks < 60:
                severity = "medium"
                gap = 60 - subj.total_marks
            elif subj.total_marks < 70:
                severity = "low"
                gap = 70 - subj.total_marks

            if severity:
                weaknesses.append({
                    "subject": subj.subject_name,
                    "subject_code": subj.subject_code,
                    "semester": sem.semester_number,
                    "severity": severity,
                    "gap": gap,
                    "current_score": subj.total_marks,
                    "grade": subj.grade,
                    "topic": f"Overall performance in {subj.subject_name}",
                    "priority": 1 if severity == "critical" else 2 if severity == "high" else 3 if severity == "medium" else 4,
                })
    weaknesses.sort(key=lambda x: (x["priority"], -x["gap"]))
    return weaknesses


def generate_recommendations(profile: StudentProfile, weaknesses: List[Dict]) -> List[str]:
    """Generate personalized recommendations"""
    recommendations = []

    if profile.cgpa == 0:
        recommendations.append("Enter your academic data to get personalized recommendations")
    elif profile.cgpa < 5.0:
        recommendations.append("Urgent: Focus on clearing backlogs and improving core subject understanding")
        recommendations.append("Consider meeting with academic advisor immediately")
    elif profile.cgpa < 6.0:
        recommendations.append("Focus on improving core subjects to raise CGPA above 6.0")
    elif profile.cgpa < 7.5:
        recommendations.append("Good progress! Target weak subjects to push CGPA above 7.5")
    else:
        recommendations.append("Excellent performance! Consider advanced electives or research projects")

    critical_subjects = [w for w in weaknesses if w["severity"] in ["critical", "high"]]
    for subj in critical_subjects[:2]:
        recommendations.append(f"Priority: Focus on {subj['subject']} – currently at {subj['current_score']:.0f}%")

    if len(profile.interests) < 3:
        recommendations.append("Add more interests to get better elective recommendations")
    if len(profile.semester_records) == 0:
        recommendations.append("Add your semester scores to unlock AI-powered insights")

    return recommendations


def build_performance_data(profile: StudentProfile) -> Dict[str, Any]:
    """Build performance data structure for frontend charts"""
    sorted_sems = sorted(
        [s for s in profile.semester_records if s.is_complete],
        key=lambda x: x.semester_number,
    )

    sgpa_trend = []
    attendance_trend = []
    grade_distribution: Dict[str, int] = {}

    for sem in sorted_sems:
        sgpa_trend.append({
            "semester": sem.semester_number,
            "sgpa": sem.sgpa,
            "credits": sem.total_credits,
            "year": sem.academic_year,
        })
        attendance_trend.append({
            "semester": sem.semester_number,
            "attendance": 85.0,
            "assignments": len(sem.subjects),
        })
        for subj in sem.subjects:
            grade_distribution[subj.grade] = grade_distribution.get(subj.grade, 0) + 1

    sgpas = [s["sgpa"] for s in sgpa_trend]
    if sgpas:
        mean_sgpa, min_sgpa, max_sgpa = sum(sgpas) / len(sgpas), min(sgpas), max(sgpas)
    else:
        mean_sgpa = min_sgpa = max_sgpa = 0

    return {
        "sgpa_trend": sgpa_trend,
        "attendance_trend": attendance_trend,
        "grade_distribution": grade_distribution,
        "statistics": {
            "mean_sgpa": round(mean_sgpa, 2),
            "std_sgpa": 0,
            "min_sgpa": round(min_sgpa, 2),
            "max_sgpa": round(max_sgpa, 2),
            "trend_direction": calculate_improvement_trend(profile),
        },
    }


def build_predictions(profile: StudentProfile) -> Dict[str, Any]:
    """Build simple predictions based on performance history"""
    sorted_sems = sorted(
        [s for s in profile.semester_records if s.is_complete],
        key=lambda x: x.semester_number,
    )
    recent_sgpas = [s.sgpa for s in sorted_sems[-3:]]

    if recent_sgpas:
        avg_recent = sum(recent_sgpas) / len(recent_sgpas)
        trend = calculate_improvement_trend(profile)
        if trend == "improving":
            predicted_sgpa = min(avg_recent + 0.2, 10.0)
        elif trend == "declining":
            predicted_sgpa = max(avg_recent - 0.2, 0.0)
        else:
            predicted_sgpa = avg_recent
    else:
        predicted_sgpa = profile.cgpa if profile.cgpa > 0 else 7.0

    _, risk_level = calculate_risk_score(profile)

    return {
        "next_semester_sgpa": round(predicted_sgpa, 2),
        "expected_graduation_cgpa": round(profile.cgpa, 2) if profile.cgpa > 0 else round(predicted_sgpa, 2),
        "failure_risk": risk_level,
        "confidence_score": 0.75 if len(recent_sgpas) >= 2 else 0.5,
    }


def calculate_profile_completeness(profile: StudentProfile) -> int:
    """Calculate profile completeness percentage"""
    score = 0
    if profile.name: score += 15
    if profile.roll_number: score += 15
    if profile.branch: score += 10
    if len(profile.semester_records) > 0: score += 25
    if len(profile.interests) > 0: score += 15
    if len(profile.skills) > 0: score += 10
    if len(profile.career_goals) > 0: score += 10
    return min(score, 100)


def _get_display_name(profile: StudentProfile) -> str:
    """Get display name, falling back to email-derived name"""
    if profile.name and profile.name.strip():
        return profile.name
    return _derive_name_from_email(profile.email)


def _get_display_roll(profile: StudentProfile) -> str:
    """Get display roll number, falling back to email"""
    if profile.roll_number and profile.roll_number.strip():
        return profile.roll_number
    return profile.email or profile.user_id[:12]


async def _get_project_count(user_id: str) -> int:
    """Get project count for a student"""
    try:
        return await StudentProject.find(
            StudentProject.student_id == user_id
        ).count()
    except Exception:
        return 0


async def _get_projects_list(user_id: str) -> List[Dict[str, Any]]:
    """Get projects list for a student"""
    try:
        projects = await StudentProject.find(
            StudentProject.student_id == user_id
        ).to_list()
        return [
            {
                "title": p.title,
                "description": getattr(p, "description", ""),
                "technologies": getattr(p, "technologies", []),
                "github_url": getattr(p, "github_url", ""),
                "created_at": p.created_at.isoformat() if hasattr(p, "created_at") and p.created_at else None,
            }
            for p in projects
        ]
    except Exception:
        return []


# ══════════════════════════════════════════════════════════
# MAIN ENDPOINT - FIXED with proper filters
# ══════════════════════════════════════════════════════════

@router.get("/list")
async def get_students_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    department: Optional[str] = None,
    semester: Optional[int] = Query(None, ge=1, le=8),  # ✅ ADD semester filter
    batch: Optional[str] = None,  # ✅ ADD batch filter  
    search: Optional[str] = None,
    cgpa_min: Optional[float] = None,
    cgpa_max: Optional[float] = None,
    risk_level: Optional[str] = Query(None),
    current_user: FirebaseUser = Depends(get_current_user),
):
    """
    Get list of students with analysis data.
    Returns { students: [...], total: N } format matching admin pattern.
    
    ✅ FIXED: Now properly filters by semester and batch like admin endpoint
    """
    try:
        # ✅ Build MongoDB query filters (same as admin_service.py pattern)
        query_filters: Dict[str, Any] = {}
        
        if department:
            query_filters["branch"] = department
        
        # ✅ FIX: Add semester filter  
        if semester:
            query_filters["current_semester"] = semester
        
        # ✅ FIX: Add batch filter
        if batch:
            try:
                query_filters["admission_year"] = int(batch)
            except ValueError:
                logger.warning(f"Invalid batch value: {batch}")

        logger.info(f"🔍 Query filters applied: {query_filters}")

        # ✅ Build Beanie query 
        if query_filters:
            query = StudentProfile.find(query_filters)
            total_query = StudentProfile.find(query_filters)
        else:
            query = StudentProfile.find_all()
            total_query = StudentProfile.find_all()

        # Get total count first
        total = await total_query.count()
        
        # Fetch profiles with pagination
        profiles = await query.skip(skip).limit(limit).to_list()

        students = []
        filtered_count = 0  # Track how many pass post-filtering
        
        for profile in profiles:
            # Apply CGPA filters (post-query filtering)
            if cgpa_min is not None and profile.cgpa < cgpa_min:
                continue
            if cgpa_max is not None and profile.cgpa > cgpa_max:
                continue

            risk_score, r_level = calculate_risk_score(profile)

            # Apply risk filter  
            if risk_level and risk_level != "all" and r_level != risk_level:
                continue

            # Apply search filter
            display_name = _get_display_name(profile)
            display_roll = _get_display_roll(profile)
            if search:
                search_lower = search.lower()
                if (search_lower not in display_name.lower() and
                    search_lower not in display_roll.lower() and
                    search_lower not in (profile.email or "").lower()):
                    continue

            # ✅ This student passed all filters
            filtered_count += 1
            
            weaknesses = identify_weaknesses(profile)
            sorted_sems = sorted(
                [s for s in profile.semester_records if s.is_complete],
                key=lambda x: x.semester_number,
            )

            proj_count = await _get_project_count(profile.user_id)

            students.append({
                "student_id": profile.user_id,
                "id": profile.user_id,
                "uid": profile.user_id,
                "name": display_name,
                "roll_number": display_roll,
                "email": profile.email,
                "department": profile.branch,
                "branch": profile.branch,
                "batch": profile.admission_year,
                "current_semester": profile.current_semester,
                "semester": profile.current_semester,
                "cgpa": profile.cgpa,
                "overall_cgpa": profile.cgpa,
                "sgpa_trend": [s.sgpa for s in sorted_sems],
                "latest_sgpa": sorted_sems[-1].sgpa if sorted_sems else 0,
                "semester_sgpa": sorted_sems[-1].sgpa if sorted_sems else 0,
                "attendance": 85.0,
                "weaknesses": weaknesses[:5],
                "weakness_count": len(weaknesses),
                "risk_score": risk_score,
                "risk_level": r_level,
                "improvement_trend": calculate_improvement_trend(profile),
                "performance_trend": calculate_improvement_trend(profile),
                "projects_count": proj_count,
                "recommendations_pending": 0,
                "profile_completeness": calculate_profile_completeness(profile),
                "last_updated": profile.last_updated.isoformat() if profile.last_updated else datetime.now().isoformat(),
                "metadata": {
                    "total_credits": profile.total_credits_earned,
                    "has_warnings": r_level in ["medium", "high"],
                    "analysis_version": "1.0",
                },
            })

        logger.info(f"✅ Student analysis list: returning {len(students)} students (filtered from {total} total)")
        logger.info(f"📊 Filters applied - Semester: {semester}, Batch: {batch}, Department: {department}")

        return {
            "students": students,
            "total": total,  # Total matching query filters
            "filtered_total": len(students),  # Total after all filtering
            "has_more": (skip + limit) < total,
        }

    except Exception as e:
        logger.error(f"❌ Error fetching students list: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ══════════════════════════════════════════════════════════
# OTHER ENDPOINTS (unchanged)
# ══════════════════════════════════════════════════════════

@router.get("/dashboard/realtime")
async def get_realtime_dashboard(
    faculty_id: str,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get real-time dashboard for faculty"""
    try:
        profiles = await StudentProfile.find_all().to_list()
        students = []
        total_cgpa = 0.0
        at_risk_count = 0

        for profile in profiles:
            risk_score, r_level = calculate_risk_score(profile)
            weaknesses = identify_weaknesses(profile)
            sorted_sems = sorted(
                [s for s in profile.semester_records if s.is_complete],
                key=lambda x: x.semester_number,
            )

            if r_level in ["medium", "high"]:
                at_risk_count += 1
            if profile.cgpa > 0:
                total_cgpa += profile.cgpa

            students.append({
                "student_id": profile.user_id,
                "name": _get_display_name(profile),
                "department": profile.branch,
                "cgpa": profile.cgpa,
                "risk_level": r_level,
                "improvement_trend": calculate_improvement_trend(profile),
            })

        profiles_with_cgpa = [p for p in profiles if p.cgpa > 0]
        avg_cgpa = round(total_cgpa / len(profiles_with_cgpa), 2) if profiles_with_cgpa else 0

        return {
            "faculty_id": faculty_id,
            "students": students,
            "summary": {
                "total_students": len(profiles),
                "at_risk_count": at_risk_count,
                "average_cgpa": avg_cgpa,
                "last_updated": datetime.now().isoformat(),
            },
            "alerts": [],
        }

    except Exception as e:
        logger.error(f"Error getting realtime dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/analytics/batch")
async def record_analytics_batch(
    events: Dict[str, Any],
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Record analytics events (batch)"""
    event_count = len(events.get("events", []))
    return {"status": "success", "events_recorded": event_count}


@router.get("/{student_id}")
async def get_student_details(
    student_id: str,
    include_predictions: bool = True,
    include_recommendations: bool = True,
    time_range: str = "all",
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get detailed student analysis"""
    try:
        if current_user.role == "student" and current_user.uid != student_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own data")

        profile = await StudentProfile.find_one(StudentProfile.user_id == student_id)
        if not profile:
            return _empty_student_response(student_id)

        risk_score, risk_level = calculate_risk_score(profile)
        weaknesses = identify_weaknesses(profile)
        recommendations = generate_recommendations(profile, weaknesses)
        performance_data = build_performance_data(profile)
        predictions = build_predictions(profile) if include_predictions else {}
        sorted_sems = sorted([s for s in profile.semester_records if s.is_complete], key=lambda x: x.semester_number)

        return {
            "student_id": profile.user_id,
            "name": _get_display_name(profile),
            "roll_number": _get_display_roll(profile),
            "email": profile.email,
            "department": profile.branch,
            "batch": profile.admission_year,
            "current_semester": profile.current_semester,
            "cgpa": profile.cgpa,
            "sgpa_trend": [s.sgpa for s in sorted_sems],
            "latest_sgpa": sorted_sems[-1].sgpa if sorted_sems else 0,
            "attendance": 85.0,
            "weaknesses": weaknesses,
            "weakness_count": len(weaknesses),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "improvement_trend": calculate_improvement_trend(profile),
            "recommendations_pending": len(recommendations),
            "profile_completeness": calculate_profile_completeness(profile),
            "last_updated": profile.last_updated.isoformat() if profile.last_updated else datetime.now().isoformat(),
            "metadata": {"total_credits": profile.total_credits_earned, "has_warnings": risk_level in ["medium", "high"], "analysis_version": "1.0"},
            "performance_data": performance_data,
            "predictions": predictions,
            "recommendations": recommendations if include_recommendations else [],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student details: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{student_id}/dashboard-view")
async def get_student_dashboard_view(
    student_id: str,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """
    Faculty read-only view of student's full dashboard.
    Returns everything needed for charts, stats, weaknesses, predictions.
    """
    try:
        profile = await StudentProfile.find_one(StudentProfile.user_id == student_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

        risk_score, risk_level = calculate_risk_score(profile)
        weaknesses = identify_weaknesses(profile)
        recommendations = generate_recommendations(profile, weaknesses)
        performance_data = build_performance_data(profile)
        predictions = build_predictions(profile)
        sorted_sems = sorted([s for s in profile.semester_records if s.is_complete], key=lambda x: x.semester_number)

        projects_list = await _get_projects_list(student_id)

        subjects_by_semester = []
        for sem in sorted_sems:
            subjects_by_semester.append({
                "semester": sem.semester_number,
                "sgpa": sem.sgpa,
                "credits": sem.total_credits,
                "academic_year": sem.academic_year,
                "subjects": [
                    {
                        "name": subj.subject_name,
                        "code": subj.subject_code,
                        "credits": subj.credits,
                        "internal_marks": subj.internal_marks,
                        "external_marks": subj.external_marks,
                        "total_marks": subj.total_marks,
                        "grade": subj.grade,
                        "grade_points": subj.grade_points,
                    }
                    for subj in sem.subjects
                ],
            })

        return {
            "student_id": profile.user_id,
            "name": _get_display_name(profile),
            "roll_number": _get_display_roll(profile),
            "email": profile.email,
            "department": profile.branch,
            "batch": profile.admission_year,
            "current_semester": profile.current_semester,
            "cgpa": profile.cgpa,
            "sgpa_trend": [s.sgpa for s in sorted_sems],
            "latest_sgpa": sorted_sems[-1].sgpa if sorted_sems else 0,
            "total_credits_earned": profile.total_credits_earned,
            "total_credits_required": profile.total_credits_required,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "improvement_trend": calculate_improvement_trend(profile),
            "profile_completeness": calculate_profile_completeness(profile),
            "performance_data": performance_data,
            "subjects_by_semester": subjects_by_semester,
            "weaknesses": weaknesses,
            "weakness_count": len(weaknesses),
            "predictions": predictions,
            "recommendations": recommendations,
            "projects": projects_list,
            "projects_count": len(projects_list),
            "interests": profile.interests,
            "skills": profile.skills,
            "career_goals": profile.career_goals,
            "last_updated": profile.last_updated.isoformat() if profile.last_updated else datetime.now().isoformat(),
            "view_mode": "readonly",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in dashboard-view for {student_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{student_id}/predictions")
async def get_student_predictions(
    student_id: str,
    include_confidence: bool = True,
    time_horizon: str = "next_semester",
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get ML predictions for a student"""
    try:
        profile = await StudentProfile.find_one(StudentProfile.user_id == student_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

        predictions = build_predictions(profile)
        weaknesses = identify_weaknesses(profile)

        return {
            "prediction_id": f"pred_{student_id}_{int(datetime.now().timestamp())}",
            "student_id": student_id,
            "predictions": {
                "next_semester_sgpa": predictions["next_semester_sgpa"],
                "expected_graduation_cgpa": predictions["expected_graduation_cgpa"],
                "failure_risk": predictions["failure_risk"],
                "confidence_interval": [max(0, predictions["next_semester_sgpa"] - 0.5), min(10, predictions["next_semester_sgpa"] + 0.5)] if include_confidence else None,
                "key_factors": ["previous_performance", "attendance", "subject_difficulty"],
                "improvement_recommendations": generate_recommendations(profile, weaknesses),
            },
            "model_metadata": {"model_version": "1.0.0", "training_date": "2024-01-01", "accuracy": 0.85, "features_used": ["sgpa_history", "attendance", "credits"]},
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting predictions: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{student_id}/weakness-analysis")
async def trigger_weakness_analysis(
    student_id: str,
    force_refresh: bool = False,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Trigger weakness analysis for a student"""
    try:
        profile = await StudentProfile.find_one(StudentProfile.user_id == student_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

        weaknesses = identify_weaknesses(profile)
        risk_score, risk_level = calculate_risk_score(profile)

        return {
            "status": "completed",
            "job_id": f"wa_{student_id}_{int(datetime.now().timestamp())}",
            "weaknesses": weaknesses,
            "overall_risk_score": risk_score,
            "risk_level": risk_level,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in weakness analysis: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{student_id}/analysis-status")
async def get_analysis_status(
    student_id: str,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get analysis status for a student"""
    try:
        profile = await StudentProfile.find_one(StudentProfile.user_id == student_id)
        has_data = profile is not None and len(profile.semester_records) > 0
        return {
            "status": "completed" if has_data else "pending",
            "progress": 100 if has_data else 0,
            "message": "Analysis complete" if has_data else "Add academic data to generate analysis",
        }
    except Exception as e:
        return {"status": "error", "progress": 0, "message": str(e)}


def _empty_student_response(student_id: str) -> Dict[str, Any]:
    return {
        "student_id": student_id, "name": "", "roll_number": "", "department": "",
        "batch": 0, "current_semester": 1, "cgpa": 0, "sgpa_trend": [], "latest_sgpa": 0,
        "attendance": 0, "weaknesses": [], "weakness_count": 0, "risk_score": 0,
        "risk_level": "low", "improvement_trend": "stable", "recommendations_pending": 0,
        "profile_completeness": 0, "last_updated": datetime.now().isoformat(),
        "metadata": {"total_credits": 0, "has_warnings": False, "analysis_version": "1.0"},
        "performance_data": {"sgpa_trend": [], "attendance_trend": [], "grade_distribution": {}, "statistics": {"mean_sgpa": 0, "std_sgpa": 0, "min_sgpa": 0, "max_sgpa": 0, "trend_direction": "stable"}},
        "predictions": {"next_semester_sgpa": 0, "expected_graduation_cgpa": 0, "failure_risk": "unknown"},
        "recommendations": ["Create your profile and add academic data to get personalized insights"],
    }