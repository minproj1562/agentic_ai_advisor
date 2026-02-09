# academic-advisor-backend/app/api/v1/endpoints/ml_insights.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.services.ml_service import enhanced_ml_service
from app.services.ml_performance_analysis import ml_analyzer
from app.models.student_profile import StudentProfile
from app.models.faculty import Faculty
from app.core.security import get_current_user, FirebaseUser
from app.core.curriculum import get_semester_subjects

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== REQUEST/RESPONSE MODELS ====================

class PerformancePredictionRequest(BaseModel):
    currentGrades: Dict[str, float]
    attendance: float
    projectCount: int
    studyHours: Optional[float] = None
    extracurricular: Optional[List[str]] = None


class CareerPathAnalysisRequest(BaseModel):
    skills: List[str]
    interests: List[str]
    academicPerformance: Dict[str, float]
    personalityTraits: Optional[List[str]] = None
    careerGoals: Optional[List[str]] = None


class InterestUpdateRequest(BaseModel):
    interests: List[str] = Field(..., description="List of student interests")
    career_goals: Optional[List[str]] = Field(None, description="Career goals")
    skills: Optional[List[str]] = Field(None, description="Current skills")


# ==================== COMPREHENSIVE ANALYSIS ====================

@router.get("/comprehensive-analysis")
async def get_comprehensive_analysis(
    include_trends: bool = True,
    include_comparisons: bool = True,
    include_interests: bool = True,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get comprehensive AI-powered analysis for current student
    Includes performance, interests, and curriculum recommendations
    """
    try:
        analysis = await enhanced_ml_service.generate_comprehensive_analysis(
            student_id=current_user.uid,
            include_trends=include_trends,
            include_comparisons=include_comparisons,
            include_interests=include_interests
        )
        
        return {
            "status": "success",
            "data": analysis,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Comprehensive analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ACADEMIC DATA ANALYSIS ====================

@router.get("/academic-recommendations")
async def get_academic_recommendations(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get recommendations triggered by academic data entry
    Returns elective suggestions, weakness analysis, and improvement plans
    """
    try:
        # Get student profile
        student = await StudentProfile.find_one(
            {"user_id": current_user.uid}
    )
        
        if not student:
            raise HTTPException(
                status_code=404,
                detail="Student profile not found. Please create your profile first."
            )
        
        # Get performance history
        performance_history = await enhanced_ml_service._get_performance_history(
            current_user.uid
        )
        
        # Get curriculum data
        curriculum_data = None
        try:
            available_subjects = get_semester_subjects(
                student.current_semester,
                student.admission_year
            )
            
            curriculum_data = {
                'semester': student.current_semester,
                'admission_year': student.admission_year,
                'curriculum_type': 'Pre-Autonomy' if student.admission_year < 2024 and student.current_semester <= 4 else 'Autonomy',
                'available_subjects': [
                    {
                        'code': s.subject_code,
                        'name': s.subject_name,
                        'type': s.course_type
                    }
                    for s in available_subjects
                ]
            }
        except Exception as e:
            logger.warning(f"Could not load curriculum data: {e}")
        
        # Get weakness analysis
        weaknesses = await ml_analyzer.detect_weaknesses(
            student_data={
                'id': current_user.uid,
                'cgpa': student.cgpa,
                'attendance': 85,
                'current_semester': student.current_semester,
                'branch': student.branch
            },
            performance_history=performance_history,
            assessments=[],
            curriculum_data=curriculum_data
        )
        
        # Get curriculum recommendations
        curriculum_recs = await enhanced_ml_service._get_curriculum_recommendations(
            student,
            weaknesses,
            performance_history
        )
        
        # Get interest-based recommendations
        interest_analysis = await enhanced_ml_service._analyze_interests(student)
        interest_recs = await enhanced_ml_service._recommend_electives_by_interest(
            student,
            interest_analysis
        )
        
        return {
            "status": "success",
            "data": {
                "weaknesses": weaknesses,
                "curriculum_recommendations": curriculum_recs,
                "interest_based_recommendations": interest_recs,
                "student_info": {
                    "name": student.name,
                    "branch": student.branch,
                    "semester": student.current_semester,
                    "cgpa": student.cgpa
                },
                "curriculum_info": curriculum_data
            },
            "generated_at": datetime.utcnow().isoformat(),
            "recommendation_type": "academic_data_triggered"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Academic recommendations error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INTEREST MANAGEMENT ====================

@router.get("/interests")
async def get_student_interests(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get student's current interests and recommendations"""
    try:
        student = await StudentProfile.find_one(
            {"user_id": current_user.uid}
    )
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        interest_analysis = await enhanced_ml_service._analyze_interests(student)
        
        return {
            "status": "success",
            "data": {
                "declared_interests": student.interests or [],
                "career_goals": student.career_goals or [],
                "skills": student.skills or [],
                "analysis": interest_analysis
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get interests error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interests/update")
async def update_student_interests(
    request: InterestUpdateRequest,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Update student interests manually"""
    try:
        student = await StudentProfile.find_one(
            {"user_id": current_user.uid}
        )
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Update interests
        student.interests = request.interests
        
        if request.career_goals:
            student.career_goals = request.career_goals
        
        if request.skills:
            student.skills = request.skills
        
        await student.save()
        
        # Generate updated recommendations
        interest_analysis = await enhanced_ml_service._analyze_interests(student)
        interest_recs = await enhanced_ml_service._recommend_electives_by_interest(
            student,
            interest_analysis
        )
        
        return {
            "status": "success",
            "message": "Interests updated successfully",
            "data": {
                "interests": student.interests,
                "career_goals": student.career_goals,
                "skills": student.skills,
                "updated_recommendations": interest_recs
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update interests error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/interests/profile")
async def get_interest_profile(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get student's interest profile - alias endpoint"""
    return await get_student_interests(current_user)


@router.post("/interests/update")  
async def update_interest_profile(
    request: InterestUpdateRequest,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Update student interests - alias endpoint"""
    return await update_student_interests(request, current_user)

# ==================== PERFORMANCE PREDICTION ====================

@router.post("/predict-performance")
async def predict_performance(
    data: PerformancePredictionRequest,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Predict future academic performance"""
    try:
        prediction = await enhanced_ml_service.predict_performance(
            data.currentGrades,
            data.attendance,
            data.projectCount,
            data.studyHours,
            data.extracurricular
        )
        
        return {
            "status": "success",
            "prediction": prediction,
            "confidence_score": prediction.get("confidence", 0.75)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CAREER PATH ANALYSIS ====================

@router.post("/career-path-analysis")
async def analyze_career_paths(
    data: CareerPathAnalysisRequest,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Analyze and recommend career paths"""
    try:
        career_insights = await enhanced_ml_service.analyze_career_paths(
            data.skills,
            data.interests,
            data.academicPerformance,
            data.personalityTraits,
            data.careerGoals
        )
        
        return {
            "status": "success",
            "career_insights": career_insights,
            "analysis_type": "comprehensive_career_path"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PROJECT-TRIGGERED ANALYSIS ====================

@router.post("/project-analysis-callback")
async def project_analysis_callback(
    student_id: str,
    project_data: Dict[str, Any],
    inferred_interests: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Callback endpoint for project upload analysis
    Generates academic recommendations based on project interests
    """
    try:
        # Verify user authorization
        if current_user.uid != student_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Generate project-based recommendations
        recommendations = await enhanced_ml_service.analyze_project_for_recommendations(
            student_id,
            project_data,
            inferred_interests
        )
        
        # Store recommendations for later retrieval
        # In production, store in database
        
        return {
            "status": "success",
            "message": "Project analysis completed",
            "data": {
                "inferred_interests": inferred_interests,
                "recommendations": recommendations,
                "analysis_type": "project_triggered"
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Project analysis callback error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ELECTIVE RECOMMENDATIONS ====================

@router.get("/elective-recommendations")
async def get_elective_recommendations(
    semester: Optional[int] = Query(None, description="Target semester for electives"),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get personalized elective recommendations"""
    try:
        student = await StudentProfile.find_one(
            {"user_id": current_user.uid}
    )
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        target_semester = semester or student.current_semester + 1
        
        # Get interest-based recommendations
        interest_analysis = await enhanced_ml_service._analyze_interests(student)
        interest_recs = await enhanced_ml_service._recommend_electives_by_interest(
            student,
            interest_analysis
        )
        
        # Get performance-based recommendations
        performance_history = await enhanced_ml_service._get_performance_history(
            current_user.uid
        )
        
        # Get available electives for target semester
        try:
            available_subjects = get_semester_subjects(
                target_semester,
                student.admission_year
            )
            
            available_electives = [
                {
                    'code': s.subject_code,
                    'name': s.subject_name,
                    'group': s.elective_group,
                    'credits': s.credits
                }
                for s in available_subjects
                if s.is_elective
            ]
        except Exception as e:
            logger.warning(f"Could not load available electives: {e}")
            available_electives = []
        
        return {
            "status": "success",
            "data": {
                "target_semester": target_semester,
                "interest_based_recommendations": interest_recs,
                "available_electives": available_electives,
                "student_interests": student.interests or []
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Elective recommendations error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HONOURS/MINOR RECOMMENDATIONS ====================

@router.get("/honours-minor-eligibility")
async def check_honours_minor_eligibility(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Check eligibility for Honours/Minor programs"""
    try:
        student = await StudentProfile.find_one(
            {"user_id": current_user.uid}
    )
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Check eligibility
        eligible = student.current_semester >= 4 and student.cgpa >= 7.5
        
        response = {
            "eligible": eligible,
            "current_semester": student.current_semester,
            "current_cgpa": student.cgpa,
            "required_cgpa": 7.5,
            "required_semester": 4
        }
        
        if eligible:
            # Get eligible programs
            eligible_programs = await enhanced_ml_service._get_eligible_honours_programs(student)
            
            # Get interest-based recommendations
            interest_analysis = await enhanced_ml_service._analyze_interests(student)
            student_interests = set(student.interests or [])
            
            # Rank programs by interest match
            for program in eligible_programs:
                program_keywords = set(program['program'].lower().split())
                interest_match = len(student_interests.intersection(program_keywords))
                program['interest_match_score'] = interest_match * 30
            
            eligible_programs.sort(key=lambda x: x.get('interest_match_score', 0), reverse=True)
            
            response["eligible_programs"] = eligible_programs
            response["message"] = "Congratulations! You are eligible for Honours/Minor programs"
            response["application_deadline"] = "Before Semester 5 registration"
        else:
            if student.current_semester < 4:
                response["message"] = f"You can apply after completing Semester 3"
            else:
                gap = 7.5 - student.cgpa
                response["cgpa_gap"] = gap
                response["message"] = f"Improve CGPA by {gap:.2f} to become eligible"
        
        return {
            "status": "success",
            "data": response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Honours eligibility check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HEALTH CHECK ====================

@router.get("/health")
async def ml_service_health():
    """Check ML service health"""
    try:
        health_status = {
            'status': 'healthy',
            'service': 'enhanced_ml_service',
            'available_endpoints': [
                'comprehensive-analysis',
                'academic-recommendations',
                'interests',
                'predict-performance',
                'career-path-analysis',
                'elective-recommendations',
                'honours-minor-eligibility'
            ],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return health_status
        
    except Exception as e:
        raise HTTPException(status_code=503, detail="ML service unavailable")
