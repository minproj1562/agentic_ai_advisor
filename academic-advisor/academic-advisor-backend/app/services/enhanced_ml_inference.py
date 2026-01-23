# academic-advisor-backend/app/api/v1/endpoints/student_projects_enhanced.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
import json
import logging
import os
import tempfile
from datetime import datetime

from app.services.enhanced_ml_inference import FCRITAcademicInferenceEngine
from app.services.ml_service import enhanced_ml_service
from app.models.student_profile import StudentProfile
from app.core.security import get_current_user, FirebaseUser

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize inference engine
inference_engine = FCRITAcademicInferenceEngine()


# ==================== REQUEST/RESPONSE MODELS ====================

class ProjectAnalysisResponse:
    """Response model for project analysis"""
    def __init__(
        self,
        success: bool,
        analysis: Dict[str, Any],
        student_info: Dict[str, Any],
        recommendations: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.analysis = analysis
        self.student_info = student_info
        self.recommendations = recommendations


# ==================== COMPREHENSIVE PROJECT ANALYSIS ====================

@router.post("/analyze-comprehensive")
async def analyze_project_comprehensive(
    project_data: str = Form(...),
    student_branch: str = Form(None),
    student_semester: int = Form(None),
    files: List[UploadFile] = File(None),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Comprehensive project analysis including:
    - Interest inference
    - Elective recommendations
    - Honours/Minor recommendations
    - Career path mapping
    - Skill gap analysis
    
    This is triggered when a student uploads a project.
    """
    try:
        # Parse project data
        data = json.loads(project_data)
        logger.info(f"Analyzing project for user: {current_user.uid}")
        
        # Get student profile for branch/semester if not provided
        student = await StudentProfile.find_one(
            StudentProfile.user_id == current_user.uid
        )
        
        if student:
            if not student_branch:
                student_branch = student.branch or "IT"
            if not student_semester:
                student_semester = student.current_semester or 5
        else:
            student_branch = student_branch or "IT"
            student_semester = student_semester or 5
        
        # Process uploaded files
        uploaded_files = []
        if files:
            for file in files:
                if file.filename:  # Check if file is not empty
                    try:
                        # Create temp file
                        temp_dir = tempfile.mkdtemp()
                        file_path = os.path.join(temp_dir, file.filename)
                        
                        content = await file.read()
                        with open(file_path, 'wb') as f:
                            f.write(content)
                        
                        uploaded_files.append({
                            'path': file_path,
                            'type': file.content_type,
                            'name': file.filename,
                            'size': len(content)
                        })
                    except Exception as e:
                        logger.warning(f"Error processing file {file.filename}: {e}")
        
        # Perform comprehensive analysis
        analysis_result = inference_engine.analyze_project_comprehensive(
            project_data=data,
            student_branch=student_branch,
            student_semester=student_semester,
            uploaded_files=uploaded_files
        )
        
        # Update student interests based on analysis (if high confidence)
        if student and analysis_result.get('inferred_interests'):
            await _update_student_interests_from_analysis(
                student,
                analysis_result['inferred_interests']
            )
        
        # Generate academic recommendations
        academic_recommendations = None
        if student:
            try:
                academic_recommendations = await enhanced_ml_service.analyze_project_for_recommendations(
                    student_id=current_user.uid,
                    project_data=data,
                    inferred_interests=analysis_result.get('inferred_interests', [])
                )
            except Exception as e:
                logger.warning(f"Could not generate academic recommendations: {e}")
        
        # Cleanup temp files
        for file_info in uploaded_files:
            try:
                if os.path.exists(file_info['path']):
                    os.remove(file_info['path'])
            except:
                pass
        
        return {
            "success": True,
            "analysis": analysis_result,
            "academic_recommendations": academic_recommendations,
            "student_info": {
                "branch": student_branch,
                "semester": student_semester,
                "user_id": current_user.uid,
                "interests_updated": bool(analysis_result.get('inferred_interests'))
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise HTTPException(status_code=400, detail="Invalid project data format")
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _update_student_interests_from_analysis(
    student: StudentProfile,
    inferred_interests: List[Dict[str, Any]]
):
    """Update student interests from project analysis"""
    try:
        # Extract high-confidence interests
        high_confidence_interests = [
            interest['domain']
            for interest in inferred_interests
            if interest.get('confidence', 0) > 0.7
        ]
        
        if not high_confidence_interests:
            return
        
        # Merge with existing interests
        existing_interests = set(student.interests or [])
        updated_interests = list(existing_interests.union(set(high_confidence_interests)))
        
        # Limit to top 10 interests
        student.interests = updated_interests[:10]
        student.last_updated = datetime.now()
        await student.save()
        
        logger.info(f"Updated interests for student {student.user_id}: {high_confidence_interests}")
        
    except Exception as e:
        logger.warning(f"Could not update student interests: {e}")


# ==================== GET STORED PROJECT ANALYSIS ====================

@router.get("/analysis/{project_id}")
async def get_project_analysis(
    project_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get stored analysis for a specific project
    Shows the full analysis that was generated when project was uploaded
    """
    try:
        # In production, fetch from database
        # For now, return structure
        
        # This would typically query a ProjectAnalysis collection
        # analysis = await ProjectAnalysis.find_one(project_id=project_id, user_id=current_user.uid)
        
        return {
            "success": True,
            "project_id": project_id,
            "message": "Fetch analysis from stored projects",
            "note": "Analysis is generated at upload time and stored with the project"
        }
        
    except Exception as e:
        logger.error(f"Error fetching project analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HONOURS PROGRAMS ====================

@router.get("/honours-programs/{branch}")
async def get_eligible_honours_programs(
    branch: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get eligible honours/minor programs for a branch"""
    try:
        eligible_programs = []
        
        for program_name, info in inference_engine.honours_programs.items():
            if branch.upper() in info['eligible_branches']:
                # Determine type based on branch position
                if branch.upper() == info['eligible_branches'][0]:
                    program_type = info.get('type', 'Honours')
                else:
                    program_type = 'Minor' if info.get('type') == 'both' else info.get('type', 'Minor')
                
                eligible_programs.append({
                    "program": program_name,
                    "type": program_type,
                    "courses": info.get('courses', []),
                    "career_paths": info.get('career_paths', []),
                    "skills": info.get('skills', []),
                    "keywords": info.get('keywords', [])[:5],
                    "credits": 18,
                    "duration": "4 semesters (Sem V-VIII)",
                    "eligibility": {
                        "min_cgpa": 7.5,
                        "min_semester": 4,
                        "eligible_branches": info['eligible_branches']
                    }
                })
        
        # Get student's interest match (if logged in)
        student = await StudentProfile.find_one(
            StudentProfile.user_id == current_user.uid
        )
        
        if student and student.interests:
            student_interests = set(interest.lower() for interest in student.interests)
            
            for program in eligible_programs:
                program_keywords = set(kw.lower() for kw in program.get('keywords', []))
                match_score = len(student_interests.intersection(program_keywords))
                program['interest_match_score'] = min(match_score * 25, 100)
            
            # Sort by match score
            eligible_programs.sort(key=lambda x: x.get('interest_match_score', 0), reverse=True)
        
        return {
            "success": True,
            "branch": branch,
            "eligible_programs": eligible_programs,
            "total_count": len(eligible_programs)
        }
    
    except Exception as e:
        logger.error(f"Error getting honours programs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ELECTIVES ====================

@router.get("/electives/{branch}/{semester}")
async def get_available_electives(
    branch: str,
    semester: int,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get available electives for a branch and semester with recommendations"""
    try:
        electives_data = {}
        
        # Get branch-specific electives
        if branch.upper() in inference_engine.sem5_electives and semester == 5:
            electives_data = inference_engine.sem5_electives[branch.upper()]
        else:
            # Return default electives structure
            electives_data = {
                "message": f"Electives for {branch} Semester {semester}",
                "available": True
            }
        
        # Get student's interests for personalized recommendations
        student = await StudentProfile.find_one(
            StudentProfile.user_id == current_user.uid
        )
        
        recommendations = []
        if student and student.interests:
            # Generate interest-based elective recommendations
            interest_analysis = await enhanced_ml_service._analyze_interests(student)
            recommendations = await enhanced_ml_service._recommend_electives_by_interest(
                student,
                interest_analysis
            )
        
        return {
            "success": True,
            "branch": branch,
            "semester": semester,
            "electives": electives_data,
            "personalized_recommendations": recommendations,
            "student_interests": student.interests if student else []
        }
    
    except Exception as e:
        logger.error(f"Error getting electives: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CAREER GUIDANCE ====================

@router.post("/career-guidance")
async def get_career_guidance(
    interests: List[Dict[str, Any]] = None,
    student_branch: str = Form(None),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get personalized career guidance based on interests and projects"""
    try:
        # Get student profile
        student = await StudentProfile.find_one(
            StudentProfile.user_id == current_user.uid
        )
        
        if not student_branch:
            student_branch = student.branch if student else "IT"
        
        # Use provided interests or student's stored interests
        if not interests and student:
            # Convert stored interests to inference format
            interests = [
                {
                    "domain": interest,
                    "confidence": 0.8,
                    "relatedSkills": [],
                    "careerPaths": []
                }
                for interest in (student.interests or [])
            ]
        
        # Get honours recommendations
        honours_recommendations = []
        if student_branch:
            for program_name, info in inference_engine.honours_programs.items():
                if student_branch.upper() in info['eligible_branches']:
                    honours_recommendations.append({
                        "program": program_name,
                        "type": info.get('type', 'Honours'),
                        "career_paths": info.get('career_paths', []),
                        "skills": info.get('skills', [])
                    })
        
        # Generate career paths
        career_paths = inference_engine._map_career_paths(
            interests=interests or [],
            honours_recommendations=honours_recommendations,
            student_branch=student_branch
        )
        
        # Generate skill gaps
        current_skills = student.skills if student else []
        skill_analysis = inference_engine._analyze_skill_gaps(
            current_skills=current_skills,
            career_paths=career_paths,
            interests=interests or []
        )
        
        # Generate next steps
        next_steps = inference_engine._generate_next_steps(
            interests=interests or [],
            elective_recommendations=[],
            skill_gaps=skill_analysis,
            student_semester=student.current_semester if student else 5
        )
        
        return {
            "success": True,
            "career_paths": career_paths,
            "skill_analysis": skill_analysis,
            "next_steps": next_steps,
            "honours_recommendations": honours_recommendations[:3],
            "preparation_timeline": "2-3 years",
            "immediate_actions": [
                "Choose relevant electives next semester",
                "Start building projects in your interest area",
                "Apply for Honours/Minor program if eligible",
                "Build a strong portfolio on GitHub",
                "Network with professionals in target fields"
            ],
            "student_info": {
                "branch": student_branch,
                "semester": student.current_semester if student else None,
                "cgpa": student.cgpa if student else None,
                "interests": student.interests if student else []
            }
        }
    
    except Exception as e:
        logger.error(f"Error generating career guidance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INTEREST PROFILE ====================

@router.get("/interest-profile")
async def get_interest_profile(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """Get student's complete interest profile based on all projects"""
    try:
        student = await StudentProfile.find_one(
            StudentProfile.user_id == current_user.uid
        )
        
        if not student:
            return {
                "success": True,
                "message": "No profile found",
                "interests": [],
                "topDomains": []
            }
        
        # Build interest profile
        interests = student.interests or []
        skills = student.skills or []
        career_goals = student.career_goals or []
        
        # Create domain strength mapping
        top_domains = []
        for i, interest in enumerate(interests[:5]):
            # In production, calculate actual strength from project history
            strength = max(90 - (i * 10), 50)
            
            top_domains.append({
                "name": interest,
                "strength": strength,
                "projectCount": 1,  # Would be calculated from project history
                "relatedSkills": _get_related_skills(interest),
                "careerPaths": _get_career_paths_for_interest(interest)
            })
        
        # Get recommendations
        recommendations = {
            "electives": [],
            "honours_programs": [],
            "career_paths": []
        }
        
        if interests:
            # Get elective recommendations
            interest_analysis = await enhanced_ml_service._analyze_interests(student)
            recommendations["electives"] = await enhanced_ml_service._recommend_electives_by_interest(
                student,
                interest_analysis
            )
            
            # Get honours recommendations
            for program_name, info in inference_engine.honours_programs.items():
                if student.branch.upper() in info['eligible_branches']:
                    # Check interest alignment
                    program_keywords = set(kw.lower() for kw in info.get('keywords', []))
                    student_interests_lower = set(i.lower() for i in interests)
                    
                    if program_keywords.intersection(student_interests_lower):
                        recommendations["honours_programs"].append({
                            "program": program_name,
                            "type": info.get('type', 'Honours'),
                            "match_reason": "Aligns with your interests"
                        })
        
        return {
            "success": True,
            "interests": interests,
            "skills": skills,
            "career_goals": career_goals,
            "topDomains": top_domains,
            "recommendations": recommendations,
            "profile_completeness": _calculate_profile_completeness(student)
        }
    
    except Exception as e:
        logger.error(f"Error getting interest profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_related_skills(interest: str) -> List[str]:
    """Get related skills for an interest domain"""
    skill_map = {
        "Artificial Intelligence": ["Python", "TensorFlow", "PyTorch", "NumPy"],
        "Machine Learning": ["Python", "Scikit-learn", "Pandas", "Statistics"],
        "Web Development": ["JavaScript", "React", "Node.js", "HTML/CSS"],
        "Data Science": ["Python", "R", "SQL", "Tableau"],
        "Cloud Computing": ["AWS", "Docker", "Kubernetes", "Linux"],
        "Mobile Development": ["Flutter", "React Native", "Swift", "Kotlin"],
        "Cybersecurity": ["Network Security", "Cryptography", "Linux", "Python"],
        "DevOps": ["Docker", "Kubernetes", "Jenkins", "Git"]
    }
    
    # Find matching interest
    for key, skills in skill_map.items():
        if key.lower() in interest.lower() or interest.lower() in key.lower():
            return skills
    
    return ["Programming", "Problem Solving", "Analytical Thinking"]


def _get_career_paths_for_interest(interest: str) -> List[str]:
    """Get career paths for an interest"""
    career_map = {
        "Artificial Intelligence": ["AI Engineer", "AI Researcher", "ML Engineer"],
        "Machine Learning": ["ML Engineer", "Data Scientist", "AI Developer"],
        "Web Development": ["Full Stack Developer", "Frontend Developer", "Backend Developer"],
        "Data Science": ["Data Scientist", "Data Analyst", "BI Developer"],
        "Cloud Computing": ["Cloud Architect", "DevOps Engineer", "SRE"],
        "Mobile Development": ["Mobile Developer", "iOS Developer", "Android Developer"],
        "Cybersecurity": ["Security Engineer", "Penetration Tester", "Security Analyst"]
    }
    
    for key, careers in career_map.items():
        if key.lower() in interest.lower() or interest.lower() in key.lower():
            return careers
    
    return ["Software Engineer", "Technical Specialist"]


def _calculate_profile_completeness(student: StudentProfile) -> int:
    """Calculate profile completeness percentage"""
    completeness = 0
    
    if student.name:
        completeness += 15
    if student.email:
        completeness += 10
    if student.branch:
        completeness += 10
    if student.admission_year:
        completeness += 10
    if student.interests and len(student.interests) >= 3:
        completeness += 20
    elif student.interests:
        completeness += 10
    if student.skills and len(student.skills) >= 3:
        completeness += 20
    elif student.skills:
        completeness += 10
    if student.career_goals:
        completeness += 15
    
    return min(completeness, 100)


# ==================== QUICK ANALYSIS (LIGHTWEIGHT) ====================

@router.post("/quick-analyze")
async def quick_analyze_project(
    title: str = Form(...),
    description: str = Form(...),
    technologies: str = Form(""),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Quick lightweight analysis without file uploads
    Useful for real-time suggestions during project creation
    """
    try:
        # Parse technologies
        tech_list = [t.strip() for t in technologies.split(",") if t.strip()]
        
        # Simple keyword-based analysis
        text = f"{title} {description} {' '.join(tech_list)}".lower()
        
        # Detect interests
        detected_interests = []
        
        interest_keywords = {
            "Artificial Intelligence & Machine Learning": [
                "machine learning", "ai", "neural", "deep learning", "tensorflow", "pytorch"
            ],
            "Web Development": [
                "web", "react", "angular", "vue", "frontend", "backend", "fullstack"
            ],
            "Data Science": [
                "data analysis", "pandas", "visualization", "analytics", "statistics"
            ],
            "Cloud Computing": [
                "cloud", "aws", "azure", "docker", "kubernetes", "serverless"
            ],
            "Mobile Development": [
                "mobile", "android", "ios", "flutter", "react native"
            ]
        }
        
        for domain, keywords in interest_keywords.items():
            matches = [kw for kw in keywords if kw in text]
            if matches:
                confidence = min(len(matches) / len(keywords) * 2, 1.0)
                if confidence > 0.3:
                    detected_interests.append({
                        "domain": domain,
                        "confidence": confidence,
                        "matched_keywords": matches
                    })
        
        # Sort by confidence
        detected_interests.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            "success": True,
            "quick_analysis": {
                "detected_interests": detected_interests[:3],
                "technologies_detected": tech_list,
                "suggestions": [
                    "Add more details for better analysis",
                    "Upload project files for comprehensive insights"
                ] if len(detected_interests) < 2 else []
            }
        }
    
    except Exception as e:
        logger.error(f"Quick analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))