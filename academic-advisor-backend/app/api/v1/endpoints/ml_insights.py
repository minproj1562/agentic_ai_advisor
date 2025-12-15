# app/api/v1/endpoints/ml_insights.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import asyncio
from app.services.ml_service import EnhancedMLService
from app.models.student import Student
from app.models.faculty import Faculty
from app.core.security import get_current_user, get_current_faculty
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
ml_service = EnhancedMLService()

# Pydantic models for request/response
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

class FacultyRecommendationRequest(BaseModel):
    courseId: str
    learningStyle: str
    pastPerformance: Dict[str, float]
    preferredTeachingMethods: Optional[List[str]] = None

class CourseRecommendationRequest(BaseModel):
    studentProfile: Dict[str, Any]
    careerGoals: List[str]
    currentSemester: int
    completedCourses: Optional[List[str]] = None

class StudyPlanRequest(BaseModel):
    weakSubjects: List[str]
    availableHours: float
    examDate: str
    learningPace: Optional[str] = "moderate"

class MentorshipInsightsRequest(BaseModel):
    facultyId: str
    timeRange: Optional[str] = "last_6_months"

class StudentClusterRequest(BaseModel):
    branch: str
    semester: int
    clusteringType: str = "academic_performance"

class RiskAssessmentRequest(BaseModel):
    studentId: str
    assessmentType: str = "comprehensive"

class StudyPeerRecommendationRequest(BaseModel):
    student_id: str
    subject: str
    study_objective: str

class InterviewPreparationRequest(BaseModel):
    student_id: str
    company_type: str
    role: str

class AdaptiveLearningPathRequest(BaseModel):
    student_id: str
    learning_goals: List[str]

class BatchAnalysisRequest(BaseModel):
    student_ids: List[str]
    analysis_type: str = "comprehensive"

@router.get("/comprehensive-analysis/{student_id}")
async def get_comprehensive_analysis(
    student_id: str,
    include_trends: bool = True,
    include_comparisons: bool = True,
    current_user: Student = Depends(get_current_user)
):
    """Get comprehensive AI-powered analysis for a student"""
    try:
        analysis = await ml_service.generate_comprehensive_analysis(
            student_id, 
            include_trends=include_trends,
            include_comparisons=include_comparisons
        )
        return {
            "status": "success",
            "data": analysis,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Comprehensive analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-performance")
async def predict_performance(
    data: PerformancePredictionRequest,
    current_user: Student = Depends(get_current_user)
):
    """Predict future academic performance with enhanced features"""
    try:
        prediction = await ml_service.predict_performance(
            data.currentGrades,
            data.attendance,
            data.projectCount,
            data.studyHours,
            data.extracurricular
        )
        return {
            "status": "success",
            "prediction": prediction,
            "confidence_score": prediction.get("confidence", 0.85)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/career-path-analysis")
async def analyze_career_paths(
    data: CareerPathAnalysisRequest,
    current_user: Student = Depends(get_current_user)
):
    """Analyze and recommend career paths with personality matching"""
    try:
        career_insights = await ml_service.analyze_career_paths(
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

@router.post("/faculty-recommendations")
async def get_faculty_recommendations(
    data: FacultyRecommendationRequest,
    current_user: Student = Depends(get_current_user)
):
    """Get AI-powered faculty recommendations with enhanced matching"""
    try:
        recommendations = await ml_service.recommend_faculty(
            data.courseId,
            data.learningStyle,
            data.pastPerformance,
            data.preferredTeachingMethods
        )
        return {
            "status": "success",
            "recommendations": recommendations,
            "matching_criteria_used": ["teaching_style", "expertise", "student_feedback"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/course-recommendations")
async def get_course_recommendations(
    data: CourseRecommendationRequest,
    current_user: Student = Depends(get_current_user)
):
    """Get personalized course recommendations with prerequisite checking"""
    try:
        recommendations = await ml_service.recommend_courses(
            data.studentProfile,
            data.careerGoals,
            data.currentSemester,
            data.completedCourses
        )
        return {
            "status": "success",
            "recommendations": recommendations,
            "semester_plan": f"Semester {data.currentSemester + 1}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/placement-readiness/{student_id}")
async def check_placement_readiness(
    student_id: str,
    target_companies: List[str] = Query(None),
    current_user: Student = Depends(get_current_user)
):
    """Check placement readiness and get preparation plan for specific companies"""
    try:
        readiness = await ml_service.assess_placement_readiness(
            student_id, 
            target_companies
        )
        return {
            "status": "success",
            "readiness_assessment": readiness,
            "improvement_areas": readiness.get("improvement_areas", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-study-plan")
async def generate_personalized_study_plan(
    data: StudyPlanRequest,
    background_tasks: BackgroundTasks,
    current_user: Student = Depends(get_current_user)
):
    """Generate personalized study plan with adaptive learning pace"""
    try:
        study_plan = await ml_service.generate_study_plan(
            data.weakSubjects,
            data.availableHours,
            data.examDate,
            data.learningPace
        )
        
        # Background task to track study plan effectiveness
        background_tasks.add_task(
            ml_service.track_study_plan_usage,
            str(current_user.id),  # Convert to string for Beanie
            study_plan.get("plan_id")
        )
        
        return {
            "status": "success",
            "study_plan": study_plan,
            "estimated_completion_time": study_plan.get("duration")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/peer-comparison/{student_id}")
async def get_peer_comparison(
    student_id: str,
    branch: str,
    semester: int,
    comparison_type: str = Query("comprehensive", regex="^(academic|skills|overall|comprehensive)$"),
    current_user: Student = Depends(get_current_user)
):
    """Compare with peers in the same branch and semester with different comparison types"""
    try:
        comparison = await ml_service.compare_with_peers(
            student_id,
            branch,
            semester,
            comparison_type
        )
        return {
            "status": "success",
            "comparison_type": comparison_type,
            "peer_comparison": comparison,
            "peer_group_size": comparison.get("peer_count", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NEW ENDPOINTS

@router.get("/faculty/mentorship-insights")
async def get_mentorship_insights(
    faculty_id: str,
    time_range: str = Query("last_6_months", regex="^(last_month|last_3_months|last_6_months|last_year)$"),
    current_faculty: Faculty = Depends(get_current_faculty)
):
    """Get AI-powered insights for faculty mentorship effectiveness"""
    try:
        insights = await ml_service.analyze_mentorship_effectiveness(
            faculty_id,
            time_range
        )
        return {
            "status": "success",
            "time_range": time_range,
            "mentorship_insights": insights,
            "recommendations": insights.get("recommendations", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/faculty/student-clustering")
async def cluster_students(
    data: StudentClusterRequest,
    current_faculty: Faculty = Depends(get_current_faculty)
):
    """Cluster students based on various criteria for targeted mentorship"""
    try:
        clusters = await ml_service.cluster_students(
            data.branch,
            data.semester,
            data.clusteringType
        )
        return {
            "status": "success",
            "clustering_type": data.clusteringType,
            "clusters": clusters,
            "total_students": sum(len(cluster["students"]) for cluster in clusters)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/risk-assessment")
async def assess_student_risk(
    data: RiskAssessmentRequest,
    current_user: Student = Depends(get_current_user)
):
    """Assess student academic and placement risk factors"""
    try:
        risk_assessment = await ml_service.assess_student_risk(
            data.studentId,
            data.assessmentType
        )
        return {
            "status": "success",
            "risk_assessment": risk_assessment,
            "intervention_priority": risk_assessment.get("priority_level", "medium")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/skill-gap-analysis/{student_id}")
async def analyze_skill_gaps(
    student_id: str,
    target_role: str = Query(None),
    industry_trends: bool = Query(True),
    current_user: Student = Depends(get_current_user)
):
    """Analyze skill gaps for specific career roles"""
    try:
        gap_analysis = await ml_service.analyze_skill_gaps(
            student_id,
            target_role,
            industry_trends
        )
        return {
            "status": "success",
            "target_role": target_role,
            "skill_gap_analysis": gap_analysis,
            "recommended_learning_path": gap_analysis.get("learning_path", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/learning-style-assessment")
async def assess_learning_style(
    responses: Dict[str, Any],
    current_user: Student = Depends(get_current_user)
):
    """Assess student learning style through AI analysis"""
    try:
        learning_style = await ml_service.assess_learning_style(responses)
        return {
            "status": "success",
            "learning_style_profile": learning_style,
            "recommended_study_techniques": learning_style.get("recommended_techniques", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/personalized-resources/{student_id}")
async def get_personalized_resources(
    student_id: str,
    resource_type: str = Query("all", regex="^(videos|books|courses|projects|all)$"),
    difficulty: str = Query("intermediate", regex="^(beginner|intermediate|advanced)$"),
    current_user: Student = Depends(get_current_user)
):
    """Get personalized learning resources based on student profile"""
    try:
        resources = await ml_service.recommend_learning_resources(
            student_id,
            resource_type,
            difficulty
        )
        return {
            "status": "success",
            "resource_type": resource_type,
            "difficulty_level": difficulty,
            "recommended_resources": resources,
            "total_resources": len(resources)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaborative-filtering/recommend-peers")
async def recommend_study_peers(
    data: StudyPeerRecommendationRequest,
    current_user: Student = Depends(get_current_user)
):
    """Recommend study peers using collaborative filtering"""
    try:
        peer_recommendations = await ml_service.recommend_study_peers(
            data.student_id,
            data.subject,
            data.study_objective
        )
        return {
            "status": "success",
            "subject": data.subject,
            "study_objective": data.study_objective,
            "recommended_peers": peer_recommendations,
            "matching_reason": "complementary_skills_and_schedule"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/progress-tracking/{student_id}")
async def track_student_progress(
    student_id: str,
    metric: str = Query("overall", regex="^(academic|skills|attendance|overall)$"),
    timeframe: str = Query("semester", regex="^(week|month|semester|year)$"),
    current_user: Student = Depends(get_current_user)
):
    """Track and analyze student progress over time"""
    try:
        progress_data = await ml_service.track_student_progress(
            student_id,
            metric,
            timeframe
        )
        return {
            "status": "success",
            "metric": metric,
            "timeframe": timeframe,
            "progress_data": progress_data,
            "trend_direction": progress_data.get("trend", "stable")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interview-preparation")
async def generate_interview_preparation(
    data: InterviewPreparationRequest,
    current_user: Student = Depends(get_current_user)
):
    """Generate personalized interview preparation plan"""
    try:
        preparation_plan = await ml_service.generate_interview_preparation(
            data.student_id,
            data.company_type,
            data.role
        )
        return {
            "status": "success",
            "company_type": data.company_type,
            "target_role": data.role,
            "preparation_plan": preparation_plan,
            "estimated_preparation_time": preparation_plan.get("duration_weeks")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/faculty/teaching-effectiveness")
async def analyze_teaching_effectiveness(
    faculty_id: str,
    course_id: str = Query(None),
    semester: str = Query(None),
    current_faculty: Faculty = Depends(get_current_faculty)
):
    """Analyze teaching effectiveness using student performance data"""
    try:
        effectiveness = await ml_service.analyze_teaching_effectiveness(
            faculty_id,
            course_id,
            semester
        )
        return {
            "status": "success",
            "teaching_effectiveness": effectiveness,
            "improvement_suggestions": effectiveness.get("suggestions", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/adaptive-learning-path")
async def generate_adaptive_learning_path(
    data: AdaptiveLearningPathRequest,
    current_user: Student = Depends(get_current_user)
):
    """Generate adaptive learning path based on continuous assessment"""
    try:
        learning_path = await ml_service.generate_adaptive_learning_path(
            data.student_id,
            data.learning_goals
        )
        return {
            "status": "success",
            "learning_goals": data.learning_goals,
            "adaptive_learning_path": learning_path,
            "estimated_completion": learning_path.get("estimated_completion")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Batch Processing Endpoints
@router.post("/batch-analysis/students")
async def batch_student_analysis(
    data: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_faculty: Faculty = Depends(get_current_faculty)
):
    """Perform batch analysis for multiple students"""
    try:
        # Start batch processing in background
        task_id = await ml_service.start_batch_analysis(
            data.student_ids,
            data.analysis_type
        )
        
        return {
            "status": "processing",
            "task_id": task_id,
            "message": "Batch analysis started",
            "total_students": len(data.student_ids),
            "estimated_completion_time": "5-10 minutes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/batch-analysis/status/{task_id}")
async def get_batch_analysis_status(
    task_id: str,
    current_faculty: Faculty = Depends(get_current_faculty)
):
    """Check status of batch analysis task"""
    try:
        status = await ml_service.get_batch_analysis_status(task_id)
        return {
            "status": "success",
            "task_status": status,
            "task_id": task_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health Check and System Status
@router.get("/health")
async def ml_service_health():
    """Check ML service health and available models"""
    try:
        health_status = await ml_service.get_service_health()
        return {
            "status": "healthy",
            "service": "enhanced_ml_service",
            "available_models": health_status.get("models", []),
            "last_training": health_status.get("last_training"),
            "model_versions": health_status.get("versions", {})
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail="ML service unavailable")

@router.get("/model-info/{model_type}")
async def get_model_info(
    model_type: str,
    current_user: Student = Depends(get_current_user)
):
    """Get information about specific ML models"""
    try:
        model_info = await ml_service.get_model_info(model_type)
        return {
            "status": "success",
            "model_type": model_type,
            "model_info": model_info,
            "accuracy_metrics": model_info.get("metrics", {})
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Model {model_type} not found")

# Additional Beanie-specific endpoints
@router.get("/student/{student_id}/academic-history")
async def get_student_academic_history(
    student_id: str,
    current_user: Student = Depends(get_current_user)
):
    """Get student academic history using Beanie ODM"""
    try:
        # Find student by ID using Beanie
        student = await Student.get(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        academic_history = {
            "student_id": str(student.id),
            "name": student.name,
            "branch": student.branch,
            "semester": student.semester,
            "grades": student.grades or {},
            "attendance": student.attendance or {},
            "projects": student.projects or []
        }
        
        return {
            "status": "success",
            "academic_history": academic_history
        }
    except Exception as e:
        logger.error(f"Error fetching academic history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/faculty/{faculty_id}/performance-snapshot")
async def get_faculty_performance_snapshot(
    faculty_id: str,
    current_faculty: Faculty = Depends(get_current_faculty)
):
    """Get faculty performance snapshot - Fix for 405 error"""
    try:
        # Find faculty by ID using Beanie
        faculty = await Faculty.get(faculty_id)
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty not found")
        
        # Generate performance snapshot
        snapshot = {
            "faculty_id": str(faculty.id),
            "name": faculty.name,
            "department": faculty.department,
            "mentorship_stats": {
                "total_mentees": len(faculty.mentees or []),
                "active_sessions": faculty.mentorship_sessions or 0,
                "completion_rate": 85,  # Mock data - replace with actual calculation
                "student_satisfaction": 4.2  # Mock data
            },
            "recent_activity": {
                "last_session": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "upcoming_sessions": 3,
                "pending_reviews": 2
            },
            "performance_metrics": {
                "engagement_score": 88,
                "response_time": "2.1 hours",
                "student_progress": "+12%"
            }
        }
        
        return {
            "status": "success",
            "data": snapshot,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Performance snapshot error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/faculty/{faculty_id}/mentorship-stats")
async def get_faculty_mentorship_stats(
    faculty_id: str,
    current_faculty: Faculty = Depends(get_current_faculty)
):
    """Get faculty mentorship statistics using Beanie ODM"""
    try:
        # Find faculty by ID using Beanie
        faculty = await Faculty.get(faculty_id)
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty not found")
        
        mentorship_stats = {
            "faculty_id": str(faculty.id),
            "name": faculty.name,
            "department": faculty.department,
            "total_mentees": len(faculty.mentees or []),
            "expertise_areas": faculty.expertise or [],
            "mentorship_sessions": faculty.mentorship_sessions or 0
        }
        
        return {
            "status": "success",
            "mentorship_stats": mentorship_stats
        }
    except Exception as e:
        logger.error(f"Error fetching mentorship stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/student/{student_id}/update-learning-preferences")
async def update_learning_preferences(
    student_id: str,
    preferences: Dict[str, Any],
    current_user: Student = Depends(get_current_user)
):
    """Update student learning preferences using Beanie"""
    try:
        student = await Student.get(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Update learning preferences
        await student.set({"learning_preferences": preferences})
        
        return {
            "status": "success",
            "message": "Learning preferences updated successfully",
            "updated_preferences": preferences
        }
    except Exception as e:
        logger.error(f"Error updating learning preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))