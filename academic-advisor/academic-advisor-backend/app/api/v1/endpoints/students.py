# app/api/v1/endpoints/students.py - COMPLETE FILE WITH ALL ENDPOINTS
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.student_profile import StudentProfile
from app.core.security import get_current_user, FirebaseUser
from pydantic import BaseModel
from app.services.weakness_analysis_service import get_weakness_analysis_service
from app.models.weakness import WeaknessAnalysisRequest, AnalysisBasis

router = APIRouter()
logger = logging.getLogger(__name__)


class PerformanceResponse(BaseModel):
    studentInfo: dict
    subjects: List[dict]
    overallCGPA: float
    semesterSGPA: float
    strongSubjects: List[str]
    weakSubjects: List[str]
    completedCredits: int
    totalCredits: int
    interests: List[str]
    careerGoals: List[str]
    skillsMatrix: dict

# Add this endpoint BEFORE the other routes (at the top after imports)
# This handles /students/me/profile which the frontend calls

@router.get("/me/profile")
async def get_my_profile(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get current student's profile for chatbot context.
    Returns basic info even if full profile doesn't exist.
    """
    try:
        student_id = current_user.uid
        logger.info(f"📱 Profile request for: {student_id[:12]}...")
        
        # Try to get full profile
        profile = await StudentProfile.find_one({"user_id": student_id})
        
        if profile:
            # Get latest semester data
            latest_semester = profile.semester_records[-1] if profile.semester_records else None
            
            # Calculate strong/weak subjects
            strong_subjects = []
            weak_subjects = []
            subjects = []
            
            if latest_semester:
                for s in latest_semester.subjects:
                    subj_data = {
                        "code": s.subject_code,
                        "name": s.subject_name,
                        "score": s.total_marks,
                        "grade": s.grade,
                        "credits": s.credits,
                    }
                    subjects.append(subj_data)
                    
                    if s.total_marks >= 75:
                        strong_subjects.append(s.subject_name)
                    elif s.total_marks < 50:
                        weak_subjects.append(s.subject_name)
            
            return {
                "user_id": student_id,
                "name": profile.name if hasattr(profile, 'name') else current_user.email.split('@')[0] if current_user.email else "Student",
                "email": current_user.email,
                "branch": profile.branch or "IT",
                "current_semester": profile.current_semester,
                "semester": profile.current_semester,
                "cgpa": profile.cgpa,
                "latest_sgpa": latest_semester.sgpa if latest_semester else None,
                "roll_number": profile.roll_number,
                "admission_year": profile.admission_year,
                "total_credits_earned": profile.total_credits_earned,
                "total_credits_required": profile.total_credits_required,
                "interests": profile.interests or [],
                "career_goals": profile.career_goals or [],
                "skills": getattr(profile, 'skills', []) or [],
                "strong_subjects": strong_subjects,
                "weak_subjects": weak_subjects,
                "subjects": subjects,
                "sgpa_trend": [
                    {"semester": i + 1, "sgpa": sem.sgpa}
                    for i, sem in enumerate(profile.semester_records or [])
                ],
                "performance_summary": {
                    "trend": "improving" if len(profile.semester_records or []) > 1 and 
                             profile.semester_records[-1].sgpa > profile.semester_records[-2].sgpa 
                             else "stable"
                },
                "_source": "database",
            }
        
        # Fallback: Return basic info from Firebase user
        # This ensures we NEVER return 404
        name = "Student"
        if current_user.email:
            name = current_user.email.split('@')[0].replace('.', ' ').title()
        
        return {
            "user_id": student_id,
            "name": name,
            "email": current_user.email,
            "branch": "IT",
            "current_semester": None,
            "semester": None,
            "cgpa": None,
            "latest_sgpa": None,
            "roll_number": None,
            "interests": [],
            "career_goals": [],
            "skills": [],
            "strong_subjects": [],
            "weak_subjects": [],
            "subjects": [],
            "sgpa_trend": [],
            "_source": "firebase_basic",
            "_partial": True,  # Flag indicating incomplete data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching profile: {e}", exc_info=True)
        # Still return something useful, never 500
        return {
            "user_id": current_user.uid if current_user else "unknown",
            "name": "Student",
            "email": current_user.email if current_user else None,
            "branch": "IT",
            "current_semester": None,
            "cgpa": None,
            "interests": [],
            "strong_subjects": [],
            "weak_subjects": [],
            "subjects": [],
            "_source": "fallback",
            "_partial": True,
            "_error": str(e),
        }


@router.get("/{student_id}/performance", response_model=PerformanceResponse)
async def get_student_performance(
    student_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get student performance metrics"""
    try:
        # Verify authorization
        if current_user.uid != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        profile = await StudentProfile.find_one(
            {"user_id": student_id}
        )

        if not profile:
            return PerformanceResponse(
                studentInfo={
                    "uid": student_id,
                    "year": "Unknown",
                    "semester": "Unknown",
                    "branch": "Unknown",
                    "roll_number": "Unknown"
                },
                subjects=[],
                overallCGPA=0.0,
                semesterSGPA=0.0,
                strongSubjects=[],
                weakSubjects=[],
                completedCredits=0,
                totalCredits=160,
                interests=[],
                careerGoals=[],
                skillsMatrix={}
            )

        latest_semester = profile.semester_records[-1] if profile.semester_records else None

        subjects = []
        if latest_semester:
            subjects = [
                {
                    "subject_code": s.subject_code,
                    "subject_name": s.subject_name,
                    "credits": s.credits,
                    "grade": s.grade,
                    "total_marks": s.total_marks,
                    "is_practical": s.is_practical
                }
                for s in latest_semester.subjects
            ]

        strong_subjects = []
        weak_subjects = []

        if latest_semester:
            for subject in latest_semester.subjects:
                if subject.total_marks >= 75:
                    strong_subjects.append(subject.subject_name)
                elif subject.total_marks < 50:
                    weak_subjects.append(subject.subject_name)

        return PerformanceResponse(
            studentInfo={
                "uid": profile.user_id,
                "year": str(profile.admission_year),
                "semester": str(profile.current_semester),
                "branch": profile.branch,
                "roll_number": profile.roll_number
            },
            subjects=subjects,
            overallCGPA=profile.cgpa,
            semesterSGPA=latest_semester.sgpa if latest_semester else 0.0,
            strongSubjects=strong_subjects,
            weakSubjects=weak_subjects,
            completedCredits=profile.total_credits_earned,
            totalCredits=profile.total_credits_required,
            interests=profile.interests or [],
            careerGoals=profile.career_goals or [],
            skillsMatrix={}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============== ELECTIVE RECOMMENDATIONS ==============

@router.get("/{student_id}/electives/recommendations")
async def get_elective_recommendations(
    student_id: str,
    semester: Optional[int] = Query(None),
    limit: int = Query(5, ge=1, le=20),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get personalized elective recommendations for a student"""
    try:
        if current_user.uid != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Get student profile
        profile = await StudentProfile.find_one(
            {"user_id": student_id}
        )

        interests = []
        if profile and profile.interests:
            interests = profile.interests

        # Generate recommendations
        recommendations = generate_elective_recommendations(interests, semester)

        return {
            "student_id": student_id,
            "recommendations": recommendations[:limit],
            "total": len(recommendations),
            "based_on": "interests" if interests else "default"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting elective recommendations: {e}")
        return {
            "student_id": student_id,
            "recommendations": get_default_elective_recommendations(),
            "total": 4,
            "based_on": "default"
        }


def generate_elective_recommendations(interests: List[str], semester: Optional[int] = None) -> List[Dict]:
    """Generate recommendations based on interests"""

    all_electives = [
        {
            "id": "ml-elective",
            "title": "Machine Learning",
            "code": "ML",
            "match": 95,
            "semester": "Semester 6",
            "reason": "Perfect match for your AI/ML interests and strong Python skills",
            "credits": 4,
            "difficulty": "Intermediate",
            "instructor": {"name": "Dr. Sharma", "rating": 4.5, "expertise": ["Deep Learning", "Neural Networks"]},
            "industryRelevance": 95,
            "jobMarketDemand": 92,
            "enrollmentCount": 120,
            "careerImpact": "Opens doors to AI/ML engineer roles with 40% higher salaries",
            "tags": ["AI", "Python", "Data Science", "Neural Networks"],
            "prerequisites": ["Python Programming", "Mathematics", "Statistics"],
            "learningOutcomes": [
                "Build and train neural networks",
                "Implement ML algorithms from scratch",
                "Work with TensorFlow and PyTorch"
            ],
            "syllabus": ["Regression", "Classification", "Clustering", "Neural Networks", "Deep Learning", "NLP Basics"]
        },
        {
            "id": "wt-elective",
            "title": "Wireless Technology",
            "code": "WT",
            "match": 78,
            "semester": "Semester 6",
            "reason": "Complements your networking knowledge and IoT interests",
            "credits": 4,
            "difficulty": "Intermediate",
            "instructor": {"name": "Dr. Patel", "rating": 4.2, "expertise": ["5G", "IoT Networks"]},
            "industryRelevance": 85,
            "jobMarketDemand": 80,
            "enrollmentCount": 85,
            "careerImpact": "Essential for IoT and telecom industry roles",
            "tags": ["IoT", "Networking", "5G", "Embedded Systems"],
            "prerequisites": ["Computer Networks", "Microprocessor"],
            "learningOutcomes": [
                "Understand wireless protocols",
                "Design IoT solutions",
                "Implement wireless security"
            ],
            "syllabus": ["Wireless Protocols", "5G Networks", "IoT Architecture", "Sensor Networks", "Security"]
        },
        {
            "id": "dwm-elective",
            "title": "Data Warehouse and Data Mining",
            "code": "DWM",
            "match": 88,
            "semester": "Semester 6",
            "reason": "Great for data science career path and analytics skills",
            "credits": 4,
            "difficulty": "Intermediate",
            "instructor": {"name": "Dr. Kumar", "rating": 4.3, "expertise": ["Big Data", "Analytics"]},
            "industryRelevance": 90,
            "jobMarketDemand": 88,
            "enrollmentCount": 95,
            "careerImpact": "Foundation for data engineering and BI roles",
            "tags": ["Data Science", "Analytics", "SQL", "ETL"],
            "prerequisites": ["DBMS", "SQL", "Statistics"],
            "learningOutcomes": [
                "Design data warehouses",
                "Implement ETL pipelines",
                "Apply data mining algorithms"
            ],
            "syllabus": ["Data Warehousing", "OLAP", "Mining Algorithms", "Pattern Recognition", "Visualization"]
        },
        {
            "id": "ccs-elective",
            "title": "Cloud Computing Services",
            "code": "CCS",
            "match": 82,
            "semester": "Semester 6",
            "reason": "High demand skill for modern software development",
            "credits": 4,
            "difficulty": "Intermediate",
            "instructor": {"name": "Dr. Singh", "rating": 4.4, "expertise": ["AWS", "DevOps"]},
            "industryRelevance": 92,
            "jobMarketDemand": 94,
            "enrollmentCount": 110,
            "careerImpact": "Essential for cloud architect and DevOps roles",
            "tags": ["Cloud", "AWS", "DevOps", "Microservices"],
            "prerequisites": ["Operating Systems", "Networking", "Linux"],
            "learningOutcomes": [
                "Deploy applications on AWS/Azure",
                "Implement containerization",
                "Design cloud architectures"
            ],
            "syllabus": ["Cloud Models", "AWS Services", "Containerization", "Kubernetes", "Serverless"]
        }
    ]

    # Score based on interests
    for elective in all_electives:
        score = 70
        for interest in interests:
            interest_lower = interest.lower()
            for keyword in elective.get("tags", []):
                if keyword.lower() in interest_lower or interest_lower in keyword.lower():
                    score += 5
        elective["match"] = min(score, 98)

    all_electives.sort(key=lambda x: x["match"], reverse=True)
    return all_electives


def get_default_elective_recommendations() -> List[Dict]:
    return generate_elective_recommendations([])


# ============== STUDY RESOURCES ==============

@router.get("/{student_id}/resources")
async def get_student_resources(
    student_id: str,
    type: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get recommended study resources for a student"""
    try:
        if current_user.uid != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Get student's weak subjects from latest analysis
        weak_subjects = []
        try:
            from app.models.weakness import WeaknessAnalysisResult
            latest_analysis = await WeaknessAnalysisResult.find_one(
                {"student_id": student_id, "is_current": True}
            )
            if latest_analysis:
                weak_subjects = latest_analysis.priority_areas or []
        except Exception as e:
            logger.warning(f"Could not get weakness analysis: {e}")

        # Generate resources
        resources = generate_study_resources(weak_subjects, subject, type)

        return {
            "student_id": student_id,
            "resources": resources[:limit],
            "total": len(resources),
            "based_on": "weakness_analysis" if weak_subjects else "general"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resources: {e}")
        return {
            "student_id": student_id,
            "resources": get_default_resources(subject, type)[:limit],
            "total": 10,
            "based_on": "default"
        }


def generate_study_resources(weak_subjects: List[str], subject: Optional[str], resource_type: Optional[str]) -> List[Dict]:
    """Generate study resources based on weak subjects"""

    all_resources = [
        {
            "id": "res-1",
            "title": "Complete Machine Learning Course",
            "type": "video",
            "url": "https://www.youtube.com/watch?v=GwIo3gDZCVQ",
            "duration": "12 hours",
            "rating": 4.8,
            "reviews": 15420,
            "difficulty": "Beginner to Intermediate",
            "language": "English",
            "examRelevance": "High",
            "completionStatus": 0,
            "tags": ["Machine Learning", "Python", "AI"],
            "provider": "freeCodeCamp",
            "platform": "YouTube",
            "lastUpdated": "2 weeks ago",
            "thumbnailUrl": None,
            "icon": "🎥",
            "aiReason": "Covers all ML fundamentals needed for your curriculum",
            "isBookmarked": False,
            "subject": "Machine Learning"
        },
        {
            "id": "res-2",
            "title": "Python for Data Science - Complete Tutorial",
            "type": "tutorial",
            "url": "https://www.kaggle.com/learn/python",
            "duration": "5 hours",
            "rating": 4.7,
            "reviews": 8500,
            "difficulty": "Beginner",
            "language": "English",
            "examRelevance": "High",
            "completionStatus": 0,
            "tags": ["Python", "Data Science", "Basics"],
            "provider": "Kaggle",
            "platform": "Kaggle Learn",
            "lastUpdated": "1 month ago",
            "thumbnailUrl": None,
            "icon": "📚",
            "aiReason": "Essential Python skills for ML and Data Science",
            "isBookmarked": False,
            "subject": "Python"
        },
        {
            "id": "res-3",
            "title": "Mathematics for Machine Learning",
            "type": "course",
            "url": "https://www.coursera.org/specializations/mathematics-machine-learning",
            "duration": "16 weeks",
            "rating": 4.6,
            "reviews": 12000,
            "difficulty": "Intermediate",
            "language": "English",
            "examRelevance": "High",
            "completionStatus": 0,
            "tags": ["Mathematics", "Linear Algebra", "Statistics", "ML"],
            "provider": "Imperial College London",
            "platform": "Coursera",
            "lastUpdated": "3 weeks ago",
            "thumbnailUrl": None,
            "icon": "🎓",
            "aiReason": "Strengthens mathematical foundation crucial for ML",
            "isBookmarked": False,
            "subject": "Mathematics"
        },
        {
            "id": "res-4",
            "title": "Statistics Practice Problems",
            "type": "practice",
            "url": "https://www.hackerrank.com/domains/statistics",
            "duration": "Self-paced",
            "rating": 4.5,
            "reviews": 5600,
            "difficulty": "Intermediate",
            "language": "English",
            "examRelevance": "Very High",
            "completionStatus": 0,
            "tags": ["Statistics", "Probability", "Practice"],
            "provider": "HackerRank",
            "platform": "HackerRank",
            "lastUpdated": "1 week ago",
            "thumbnailUrl": None,
            "icon": "🧮",
            "aiReason": "Practice problems to improve your Statistics scores",
            "isBookmarked": False,
            "subject": "Statistics"
        },
        {
            "id": "res-5",
            "title": "DBMS Complete Course",
            "type": "video",
            "url": "https://www.youtube.com/playlist?list=PLxCzCOWd7aiFAN6I8CuViBuCdJgiOkT2Y",
            "duration": "8 hours",
            "rating": 4.7,
            "reviews": 9800,
            "difficulty": "Intermediate",
            "language": "English",
            "examRelevance": "High",
            "completionStatus": 0,
            "tags": ["DBMS", "SQL", "Database"],
            "provider": "Gate Smashers",
            "platform": "YouTube",
            "lastUpdated": "1 month ago",
            "thumbnailUrl": None,
            "icon": "🗄️",
            "aiReason": "Comprehensive DBMS coverage for semester exams",
            "isBookmarked": False,
            "subject": "Database Management System"
        },
        {
            "id": "res-6",
            "title": "Data Structures & Algorithms in Python",
            "type": "course",
            "url": "https://www.geeksforgeeks.org/data-structures/",
            "duration": "20 hours",
            "rating": 4.8,
            "reviews": 22000,
            "difficulty": "Intermediate",
            "language": "English",
            "examRelevance": "Very High",
            "completionStatus": 0,
            "tags": ["DSA", "Python", "Algorithms", "Data Structures"],
            "provider": "GeeksforGeeks",
            "platform": "GeeksforGeeks",
            "lastUpdated": "2 weeks ago",
            "thumbnailUrl": None,
            "icon": "🔧",
            "aiReason": "Core DSA concepts with Python implementation",
            "isBookmarked": False,
            "subject": "Data Structures and Algorithms"
        },
        {
            "id": "res-7",
            "title": "Computer Networks - Neso Academy",
            "type": "video",
            "url": "https://www.youtube.com/playlist?list=PLBlnK6fEyqRgMCUAG0XRw78UA8qnv6jEx",
            "duration": "15 hours",
            "rating": 4.9,
            "reviews": 18000,
            "difficulty": "Beginner to Intermediate",
            "language": "English",
            "examRelevance": "High",
            "completionStatus": 0,
            "tags": ["Networking", "TCP/IP", "OSI"],
            "provider": "Neso Academy",
            "platform": "YouTube",
            "lastUpdated": "3 months ago",
            "thumbnailUrl": None,
            "icon": "🌐",
            "aiReason": "Best free resource for networking fundamentals",
            "isBookmarked": False,
            "subject": "Computer Networks"
        },
        {
            "id": "res-8",
            "title": "Operating Systems - Jenny's Lectures",
            "type": "video",
            "url": "https://www.youtube.com/playlist?list=PLdo5W4Nhv31a5ucW_S1K3-x6ztBRD-PNa",
            "duration": "18 hours",
            "rating": 4.8,
            "reviews": 14000,
            "difficulty": "Intermediate",
            "language": "English",
            "examRelevance": "High",
            "completionStatus": 0,
            "tags": ["OS", "Process", "Memory", "Scheduling"],
            "provider": "Jenny's Lectures",
            "platform": "YouTube",
            "lastUpdated": "2 months ago",
            "thumbnailUrl": None,
            "icon": "💻",
            "aiReason": "Detailed OS concepts for semester preparation",
            "isBookmarked": False,
            "subject": "Operating System"
        },
        {
            "id": "res-9",
            "title": "LeetCode - Practice DSA Problems",
            "type": "practice",
            "url": "https://leetcode.com/problemset/all/",
            "duration": "Self-paced",
            "rating": 4.9,
            "reviews": 50000,
            "difficulty": "All Levels",
            "language": "Multiple",
            "examRelevance": "Very High",
            "completionStatus": 0,
            "tags": ["DSA", "Practice", "Coding", "Interview Prep"],
            "provider": "LeetCode",
            "platform": "LeetCode",
            "lastUpdated": "Today",
            "thumbnailUrl": None,
            "icon": "⚡",
            "aiReason": "Essential for coding practice and placement preparation",
            "isBookmarked": False,
            "subject": "Data Structures and Algorithms"
        },
        {
            "id": "res-10",
            "title": "AWS Cloud Practitioner Essentials",
            "type": "course",
            "url": "https://www.aws.training/Details/Curriculum?id=27076",
            "duration": "6 hours",
            "rating": 4.7,
            "reviews": 8500,
            "difficulty": "Beginner",
            "language": "English",
            "examRelevance": "Medium",
            "completionStatus": 0,
            "tags": ["Cloud", "AWS", "DevOps"],
            "provider": "Amazon",
            "platform": "AWS Training",
            "lastUpdated": "1 month ago",
            "thumbnailUrl": None,
            "icon": "☁️",
            "aiReason": "Foundation for cloud computing elective",
            "isBookmarked": False,
            "subject": "Cloud Computing"
        }
    ]

    # Filter by type
    if resource_type:
        all_resources = [r for r in all_resources if r["type"].lower() == resource_type.lower()]

    # Filter by subject
    if subject:
        subject_lower = subject.lower()
        filtered = [r for r in all_resources if
                    subject_lower in r["subject"].lower() or
                    subject_lower in r["title"].lower() or
                    any(subject_lower in tag.lower() for tag in r["tags"])]
        if filtered:
            all_resources = filtered

    # Prioritize resources for weak subjects
    if weak_subjects:
        for resource in all_resources:
            for weak in weak_subjects:
                if weak.lower() in resource["subject"].lower() or \
                   weak.lower() in resource["title"].lower() or \
                   any(weak.lower() in tag.lower() for tag in resource["tags"]):
                    resource["aiReason"] = f"Recommended to improve your {weak} performance"
                    break

    return all_resources


def get_default_resources(subject: Optional[str], resource_type: Optional[str]) -> List[Dict]:
    return generate_study_resources([], subject, resource_type)


@router.get("/{student_id}/resources/bookmarked")
async def get_bookmarked_resources(
    student_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get bookmarked resources for student"""
    try:
        if current_user.uid != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        return {
            "student_id": student_id,
            "resources": [],
            "total": 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bookmarked resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{student_id}/resources/{resource_id}/bookmark")
async def toggle_bookmark(
    student_id: str,
    resource_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Toggle bookmark for a resource"""
    try:
        if current_user.uid != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        return {
            "status": "success",
            "resource_id": resource_id,
            "bookmarked": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling bookmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{student_id}/resources/{resource_id}/progress")
async def update_resource_progress(
    student_id: str,
    resource_id: str,
    progress: int = Query(..., ge=0, le=100),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Update progress for a resource"""
    try:
        if current_user.uid != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        return {
            "status": "success",
            "resource_id": resource_id,
            "progress": progress
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== ACTIVITY TRACKING ==============

@router.get("/{student_id}/activity")
async def get_student_activity(
    student_id: str,
    type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get student activity history"""
    try:
        if current_user.uid != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        return {
            "student_id": student_id,
            "activities": [],
            "total": 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        return {"student_id": student_id, "activities": [], "total": 0}


@router.post("/{student_id}/activity")
async def log_student_activity(
    student_id: str,
    activity: Dict[str, Any] = Body(...),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Log student activity"""
    try:
        if current_user.uid != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        logger.info(f"Activity logged for {student_id}: {activity}")

        return {
            "status": "success",
            "student_id": student_id,
            "activity": activity,
            "logged_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging activity: {e}")
        return {"status": "failed", "error": str(e)}


# ============== WEAKNESS ANALYSIS (LEGACY ENDPOINT) ==============

@router.get("/{student_id}/weaknesses")
async def get_student_weaknesses_legacy(
    student_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Legacy endpoint for weakness analysis.
    ✅ FIXED: Never returns 404. Always returns valid JSON with weakness data.
    If analysis fails, returns empty weaknesses with error message.
    """
    try:
        logger.info(f"🔍 Legacy weakness endpoint called for student: {student_id}")

        if current_user.uid != student_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this data")

        service = get_weakness_analysis_service()

        # Step 1: Check for cached analysis
        logger.info(f"📊 Checking for cached weakness analysis...")
        try:
            latest = await service.get_latest_analysis(student_id)
        except Exception as cache_err:
            logger.warning(f"⚠️ Cache lookup failed: {cache_err}")
            latest = None

        if latest and latest.weaknesses:
            logger.info(f"✅ Returning cached analysis with {len(latest.weaknesses)} weaknesses")
            return {
                "weaknesses": latest.weaknesses,
                "overall_risk_score": latest.overall_risk_score,
                "priority_areas": latest.priority_areas,
                "total_weaknesses": len(latest.weaknesses),
                "from_cache": True,
                "analysis_date": latest.analysis_date.isoformat() if latest.analysis_date else None,
                "critical_count": sum(1 for w in latest.weaknesses if isinstance(w, dict) and w.get('severity') == 'critical'),
                "high_count": sum(1 for w in latest.weaknesses if isinstance(w, dict) and w.get('severity') == 'high'),
                "medium_count": sum(1 for w in latest.weaknesses if isinstance(w, dict) and w.get('severity') == 'medium'),
                "low_count": sum(1 for w in latest.weaknesses if isinstance(w, dict) and w.get('severity') == 'low'),
                "key_insights": latest.key_insights or []
            }

        # Step 2: Run new combined analysis
        logger.info(f"🔄 No cached analysis found, running new combined analysis...")

        try:
            request = WeaknessAnalysisRequest(
                student_id=student_id,
                analysis_basis=AnalysisBasis.COMBINED,
                include_resources=True,
                include_study_plan=True
            )

            result = await service.analyze_weaknesses(request)

            logger.info(f"✅ New analysis complete: {result.total_weaknesses} weaknesses found")

            return {
                "weaknesses": [w.dict() if hasattr(w, 'dict') else w for w in result.weaknesses],
                "overall_risk_score": result.overall_risk_score,
                "priority_areas": result.priority_areas,
                "total_weaknesses": result.total_weaknesses,
                "from_cache": False,
                "critical_count": result.critical_count,
                "high_count": result.high_count,
                "medium_count": result.medium_count,
                "low_count": result.low_count,
                "key_insights": result.key_insights,
                "analysis_date": datetime.utcnow().isoformat()
            }

        except Exception as analysis_error:
            logger.error(f"❌ Analysis failed: {analysis_error}", exc_info=True)
            # ✅ FIXED: Return valid response even on error, never 404
            return {
                "weaknesses": [],
                "overall_risk_score": 0,
                "priority_areas": [],
                "total_weaknesses": 0,
                "from_cache": False,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "key_insights": [],
                "error": str(analysis_error),
                "message": "Unable to analyze weaknesses at this time. Please try again."
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in legacy weakness endpoint: {e}", exc_info=True)
        # ✅ FIXED: Return valid response, never 500 that frontend can't handle
        return {
            "weaknesses": [],
            "overall_risk_score": 0,
            "priority_areas": [],
            "total_weaknesses": 0,
            "from_cache": False,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "key_insights": [],
            "error": str(e),
            "message": "An unexpected error occurred"
        }


# ============== STUDY PLAN ==============

@router.post("/{student_id}/study-plan")
async def create_study_plan(
    student_id: str,
    body: Dict[str, Any] = Body(...),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Create study plan for a topic"""
    try:
        if current_user.uid != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        topic_id = body.get("topicId", "")

        return {
            "topicId": topic_id,
            "plan": [],
            "message": "Study plan will be generated based on your progress"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating study plan: {e}")
        return {
            "topicId": body.get("topicId", ""),
            "plan": [],
            "message": "Study plan generation failed"
        }