# academic-advisor-backend/app/api/v1/endpoints/student_projects_enhanced.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
import json
import logging
import os
import tempfile
from datetime import datetime
from app.ml.models.recommendation_engine import recommendation_engine
from app.services.recommendation_service import recommendation_service

# Remove the problematic ml_service import and use direct functions
from app.models.student_profile import StudentProfile
from app.core.security import get_current_user, FirebaseUser

router = APIRouter()
logger = logging.getLogger(__name__)

# Try to import the inference engine, but handle if it doesn't exist
try:
    from app.services.enhanced_ml_inference import FCRITAcademicInferenceEngine
    inference_engine = FCRITAcademicInferenceEngine()
except ImportError:
    logger.warning("FCRITAcademicInferenceEngine not available. Using mock implementation.")
    inference_engine = None
except Exception as e:
    logger.error(f"Error initializing inference engine: {e}")
    inference_engine = None

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
    Comprehensive project analysis that triggers cumulative recommendations.
    Returns: Interest inference + Elective/Honours/Career recommendations with full breakdown
    """
    try:
        data = json.loads(project_data)
        logger.info(f"Analyzing project for user: {current_user.uid}")
        
        # Get student profile
        student = await StudentProfile.find_one(
            StudentProfile.user_id == current_user.uid
        )
        
        if student:
            student_branch = student_branch or student.branch or "IT"
            student_semester = student_semester or student.current_semester or 5
        else:
            student_branch = student_branch or "IT"
            student_semester = student_semester or 5
        
        # Extract skills from the new project
        extracted_skills = _extract_skills_from_project(data)
        
        # Infer interests from project
        inferred_interests = _infer_interests_from_project(data, extracted_skills)
        
        # Update student interests if high confidence
        if student and inferred_interests:
            await _update_student_interests_from_analysis(student, inferred_interests)
        
        # ═══════════════════════════════════════════════════════════
        #  GENERATE CUMULATIVE RECOMMENDATIONS
        # ═══════════════════════════════════════════════════════════
        
        # Fetch all student data for recommendation
        student_data = await recommendation_service.get_student_data(current_user.uid)
        
        # Add the new project to the list (it might not be saved yet)
        new_project = {
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "programming_languages": data.get("programming_languages", []),
            "frameworks": data.get("frameworks", []),
            "tools": data.get("tools", []),
            "technologies": data.get("technologies", []),
            "extracted_skills": extracted_skills,
            "is_team_project": data.get("is_team_project", False),
            "complexity_score": _calculate_complexity(data),
            "github_url": data.get("github_url"),
            "demo_url": data.get("demo_url"),
        }
        student_data["projects"].append(new_project)
        
        # Merge new interests
        for interest in inferred_interests:
            if interest["confidence"] > 0.7:
                domain = interest["domain"]
                if domain not in student_data["interests"]:
                    student_data["interests"].append(domain)
        
        # Generate recommendations using the engine
        elective_recommendations = recommendation_engine.recommend_electives(
            marks=student_data["marks"],
            interests=student_data["interests"],
            projects=student_data["projects"],
            cgpa=student_data["cgpa"],
            use_ml=recommendation_engine.is_trained,
        )
        
        honours_recommendations = recommendation_engine.recommend_honours(
            marks=student_data["marks"],
            interests=student_data["interests"],
            projects=student_data["projects"],
            cgpa=student_data["cgpa"],
        )
        
        career_recommendations = recommendation_engine.recommend_careers(
            marks=student_data["marks"],
            interests=student_data["interests"],
            projects=student_data["projects"],
            cgpa=student_data["cgpa"],
        )
        
        # Build response
        return {
            "success": True,
            "project_analysis": {
                "extracted_skills": extracted_skills,
                "complexity_score": new_project["complexity_score"],
                "inferred_interests": inferred_interests,
            },
            "cumulative_recommendations": {
                "electives": elective_recommendations,
                "honours": honours_recommendations,
                "careers": career_recommendations,
            },
            "data_summary": {
                "total_marks_subjects": len(student_data["marks"]),
                "total_interests": len(student_data["interests"]),
                "total_projects": len(student_data["projects"]),
                "cgpa": student_data["cgpa"],
            },
            "model_info": {
                "is_ml_trained": recommendation_engine.is_trained,
                "models_used": ["Rule-Based", "RandomForest", "KNN"] if recommendation_engine.is_trained else ["Rule-Based"],
                "version": "2.0.0",
            },
            "student_info": {
                "branch": student_branch,
                "semester": student_semester,
                "user_id": current_user.uid,
            },
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise HTTPException(status_code=400, detail="Invalid project data format")
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _extract_skills_from_project(data: Dict[str, Any]) -> List[str]:
    """Extract skills from project data"""
    skills = set()
    
    skills.update(data.get("programming_languages", []))
    skills.update(data.get("frameworks", []))
    skills.update(data.get("tools", []))
    skills.update(data.get("technologies", []))
    
    # Extract from description using keywords
    text = f"{data.get('title', '')} {data.get('description', '')}".lower()
    
    skill_keywords = [
        "machine learning", "deep learning", "neural network", "tensorflow", "pytorch",
        "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
        "aws", "azure", "docker", "kubernetes", "ci/cd",
        "sql", "mongodb", "postgresql", "redis",
        "python", "javascript", "java", "c++", "rust", "go",
        "api", "rest", "graphql", "websocket",
        "nlp", "computer vision", "data science", "analytics",
    ]
    
    for keyword in skill_keywords:
        if keyword in text:
            skills.add(keyword.title())
    
    return list(skills)


def _infer_interests_from_project(data: Dict[str, Any], skills: List[str]) -> List[Dict[str, Any]]:
    """Infer interest domains from project"""
    text = f"{data.get('title', '')} {data.get('description', '')} {' '.join(skills)}".lower()
    
    interest_patterns = {
        "Artificial Intelligence & Machine Learning": [
            "machine learning", "deep learning", "ai", "neural", "tensorflow", 
            "pytorch", "nlp", "computer vision", "data science"
        ],
        "Web Development": [
            "web", "react", "angular", "vue", "frontend", "backend", 
            "fullstack", "html", "css", "javascript", "node"
        ],
        "Mobile & IoT Development": [
            "mobile", "android", "ios", "flutter", "react native",
            "iot", "arduino", "raspberry", "embedded", "sensor"
        ],
        "Cloud & Distributed Systems": [
            "cloud", "aws", "azure", "docker", "kubernetes", 
            "devops", "microservice", "serverless"
        ],
        "Data Science & Analytics": [
            "data analysis", "analytics", "visualization", "tableau",
            "pandas", "statistics", "bi", "dashboard"
        ],
        "Network & Wireless Systems": [
            "network", "security", "wireless", "protocol", "firewall",
            "cryptography", "cyber"
        ],
    }
    
    inferred = []
    for domain, keywords in interest_patterns.items():
        matches = [kw for kw in keywords if kw in text]
        if matches:
            confidence = min(len(matches) / 4, 1.0)
            if confidence >= 0.25:
                inferred.append({
                    "domain": domain,
                    "confidence": round(confidence, 2),
                    "matched_keywords": matches[:5],
                    "source": "project_analysis"
                })
    
    inferred.sort(key=lambda x: x["confidence"], reverse=True)
    return inferred[:3]


def _calculate_complexity(data: Dict[str, Any]) -> float:
    """Calculate project complexity score (0-1)"""
    score = 0.0
    
    # Tech stack size
    tech_count = (
        len(data.get("programming_languages", [])) +
        len(data.get("frameworks", [])) +
        len(data.get("tools", []))
    )
    score += min(tech_count * 0.08, 0.4)
    
    # Team project bonus
    if data.get("is_team_project"):
        score += 0.15
    
    # Description length (proxy for complexity)
    desc_length = len(data.get("description", ""))
    score += min(desc_length / 1000, 0.2)
    
    # External links (GitHub, demo)
    if data.get("github_url"):
        score += 0.1
    if data.get("demo_url"):
        score += 0.15
    
    return min(round(score, 2), 1.0)



async def _generate_basic_recommendations(
    student_id: str,
    project_data: Dict[str, Any],
    inferred_interests: List[Dict[str, Any]],
    student_branch: str
) -> Dict[str, Any]:
    """Generate basic recommendations when ML service is not available"""
    
    # Extract interests
    interests = [interest['domain'] for interest in inferred_interests if interest.get('confidence', 0) > 0.7]
    
    # Basic elective mapping by branch
    elective_map = {
        "IT": ["Cloud Computing", "Data Science", "AI/ML", "Cybersecurity", "IoT"],
        "CSE": ["Machine Learning", "Deep Learning", "Computer Vision", "NLP"],
        "ECE": ["Embedded Systems", "VLSI", "Communication Systems", "IoT"],
        "MECH": ["Robotics", "CAD/CAM", "Thermal Engineering", "Automotive"],
        "CIVIL": ["Structural Engineering", "Environmental Engineering", "Geotechnical"]
    }
    
    # Get electives for branch
    electives = elective_map.get(student_branch.upper(), elective_map["IT"])
    
    # Filter by interests
    recommended_electives = []
    if interests:
        for elective in electives:
            for interest in interests:
                if any(keyword in elective.lower() or keyword in interest.lower() 
                       for keyword in ["cloud", "data", "ai", "ml", "cyber", "iot", "machine", "deep"]):
                    recommended_electives.append({
                        "elective": elective,
                        "match_reason": f"Matches interest: {interest}",
                        "confidence": 0.7
                    })
    
    # If no matches, return default electives
    if not recommended_electives:
        recommended_electives = [
            {
                "elective": elective,
                "match_reason": "Based on your branch",
                "confidence": 0.6
            }
            for elective in electives[:3]
        ]
    
    return {
        "elective_recommendations": recommended_electives,
        "honours_programs": [],
        "career_paths": [],
        "notes": "Basic recommendations (ML service unavailable)"
    }


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
        # Basic honours programs structure
        honours_programs = {
            "Artificial Intelligence & Machine Learning": {
                'eligible_branches': ['IT', 'CSE', 'ECE'],
                'type': 'both',
                'courses': ['AI', 'ML', 'Deep Learning', 'NLP'],
                'career_paths': ['AI Engineer', 'ML Engineer', 'Data Scientist'],
                'skills': ['Python', 'TensorFlow', 'PyTorch'],
                'keywords': ['ai', 'machine learning', 'deep learning', 'neural networks']
            },
            "Data Science": {
                'eligible_branches': ['IT', 'CSE', 'MECH'],
                'type': 'Honours',
                'courses': ['Data Analytics', 'Big Data', 'Statistics', 'Visualization'],
                'career_paths': ['Data Scientist', 'Data Analyst', 'BI Developer'],
                'skills': ['Python', 'R', 'SQL', 'Tableau'],
                'keywords': ['data science', 'analytics', 'big data', 'statistics']
            },
            "Cyber Security": {
                'eligible_branches': ['IT', 'CSE', 'ECE'],
                'type': 'Minor',
                'courses': ['Network Security', 'Ethical Hacking', 'Cryptography'],
                'career_paths': ['Security Engineer', 'Penetration Tester'],
                'skills': ['Network Security', 'Linux', 'Python'],
                'keywords': ['cybersecurity', 'security', 'hacking', 'network']
            }
        }
        
        eligible_programs = []
        
        for program_name, info in honours_programs.items():
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
        # Basic electives structure
        sem5_electives = {
            "IT": {
                "professional": [
                    "Cloud Computing",
                    "Data Science and Analytics", 
                    "Internet of Things",
                    "Cyber Security",
                    "Software Project Management"
                ],
                "open": [
                    "Entrepreneurship Development",
                    "Technical Communication",
                    "Disaster Management"
                ]
            },
            "CSE": {
                "professional": [
                    "Machine Learning",
                    "Computer Vision",
                    "Natural Language Processing",
                    "Big Data Analytics",
                    "Software Testing"
                ],
                "open": [
                    "Entrepreneurship Development",
                    "Technical Communication",
                    "Disaster Management"
                ]
            }
        }
        
        if branch.upper() in sem5_electives and semester == 5:
            electives_data = sem5_electives[branch.upper()]
        else:
            # Return default electives structure
            electives_data = {
                "professional": ["Advanced Programming", "Database Systems", "Network Security"],
                "open": ["General Studies"],
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
            recommendations = _recommend_electives_by_interest_basic(
                student.interests,
                electives_data.get('professional', [])
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


def _recommend_electives_by_interest_basic(
    interests: List[str],
    available_electives: List[str]
) -> List[Dict[str, Any]]:
    """Basic interest-based elective recommendation"""
    recommendations = []
    
    interest_keywords = {
        "Artificial Intelligence": ["ai", "machine learning", "deep learning", "neural"],
        "Web Development": ["web", "development", "full stack", "frontend", "backend"],
        "Data Science": ["data", "analytics", "science", "big data"],
        "Cloud Computing": ["cloud", "aws", "azure", "docker", "kubernetes"],
        "Cybersecurity": ["cyber", "security", "hacking", "network security"]
    }
    
    for interest in interests[:3]:  # Consider top 3 interests
        matched_keywords = []
        for keyword_group in interest_keywords.values():
            matched_keywords.extend(keyword_group)
        
        # Find matching electives
        for elective in available_electives:
            elective_lower = elective.lower()
            for keyword in matched_keywords:
                if keyword in elective_lower:
                    recommendations.append({
                        "elective": elective,
                        "match_reason": f"Matches interest: {interest}",
                        "confidence": 0.8,
                        "interest": interest
                    })
                    break
    
    # Remove duplicates
    seen = set()
    unique_recommendations = []
    for rec in recommendations:
        if rec['elective'] not in seen:
            seen.add(rec['elective'])
            unique_recommendations.append(rec)
    
    return unique_recommendations[:5]


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
        
        # Basic career mapping
        career_map = {
            "Artificial Intelligence": ["AI Engineer", "AI Researcher", "ML Engineer"],
            "Web Development": ["Full Stack Developer", "Frontend Developer", "Backend Developer"],
            "Data Science": ["Data Scientist", "Data Analyst", "BI Developer"],
            "Cloud Computing": ["Cloud Architect", "DevOps Engineer", "SRE"],
            "Cybersecurity": ["Security Engineer", "Penetration Tester", "Security Analyst"]
        }
        
        career_paths = []
        if interests:
            for interest in interests:
                domain = interest.get('domain', '')
                for key, paths in career_map.items():
                    if key.lower() in domain.lower():
                        career_paths.append({
                            "domain": domain,
                            "career_paths": paths,
                            "confidence": interest.get('confidence', 0.8)
                        })
        
        # If no specific matches, provide general career paths
        if not career_paths:
            career_paths = [{
                "domain": "Software Engineering",
                "career_paths": ["Software Engineer", "Full Stack Developer", "Backend Developer"],
                "confidence": 0.9
            }]
        
        # Generate skill gaps
        current_skills = student.skills if student else []
        skill_analysis = _analyze_skill_gaps_basic(
            current_skills=current_skills,
            career_paths=career_paths
        )
        
        # Generate next steps
        next_steps = _generate_next_steps_basic(
            career_paths=career_paths,
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


def _analyze_skill_gaps_basic(
    current_skills: List[str],
    career_paths: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Basic skill gap analysis"""
    
    # Common required skills for tech careers
    required_skills = {
        "Programming": ["Python", "Java", "JavaScript", "C++"],
        "Web Development": ["HTML/CSS", "JavaScript", "React", "Node.js"],
        "Data Science": ["Python", "SQL", "Statistics", "Data Visualization"],
        "Cloud Computing": ["AWS", "Docker", "Linux", "Networking"],
        "AI/ML": ["Python", "TensorFlow", "PyTorch", "Mathematics"]
    }
    
    skill_gaps = []
    current_skills_lower = [skill.lower() for skill in current_skills]
    
    for career_path in career_paths[:2]:  # Analyze top 2 career paths
        domain = career_path.get('domain', '')
        
        for category, skills in required_skills.items():
            if category.lower() in domain.lower() or any(keyword in domain.lower() 
                                                         for keyword in category.lower().split()):
                missing_skills = []
                for skill in skills:
                    if skill.lower() not in current_skills_lower:
                        missing_skills.append(skill)
                
                if missing_skills:
                    skill_gaps.append({
                        "domain": domain,
                        "category": category,
                        "missing_skills": missing_skills,
                        "priority": "high" if len(missing_skills) > 2 else "medium"
                    })
    
    return skill_gaps


def _generate_next_steps_basic(
    career_paths: List[Dict[str, Any]],
    skill_gaps: List[Dict[str, Any]],
    student_semester: int
) -> List[Dict[str, Any]]:
    """Generate basic next steps"""
    
    next_steps = []
    
    # Add steps based on career paths
    for career_path in career_paths[:2]:
        domain = career_path.get('domain', '')
        next_steps.append({
            "action": f"Start a project in {domain}",
            "timeline": "This semester",
            "priority": "high",
            "category": "project"
        })
    
    # Add steps based on skill gaps
    for gap in skill_gaps[:2]:
        missing_skills = gap.get('missing_skills', [])
        if missing_skills:
            next_steps.append({
                "action": f"Learn {missing_skills[0]}",
                "timeline": "Next 3 months",
                "priority": gap.get('priority', 'medium'),
                "category": "skill"
            })
    
    # Add general steps based on semester
    if student_semester <= 4:
        next_steps.append({
            "action": "Build strong fundamentals in core subjects",
            "timeline": "Current semester",
            "priority": "high",
            "category": "academic"
        })
    
    return next_steps


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
        
        # Get basic recommendations
        recommendations = {
            "electives": [],
            "honours_programs": [],
            "career_paths": []
        }
        
        if interests:
            # Get elective recommendations
            recommendations["electives"] = _recommend_electives_by_interest_basic(
                interests,
                ["Cloud Computing", "Data Science", "AI/ML", "Cybersecurity"]  # Default electives
            )
            
            # Basic honours programs structure
            honours_programs = {
                "Artificial Intelligence & Machine Learning": {
                    'eligible_branches': ['IT', 'CSE', 'ECE'],
                    'type': 'both',
                    'keywords': ['ai', 'machine learning', 'deep learning']
                },
                "Data Science": {
                    'eligible_branches': ['IT', 'CSE', 'MECH'],
                    'type': 'Honours',
                    'keywords': ['data science', 'analytics', 'big data']
                }
            }
            
            # Check honours programs
            if student.branch:
                for program_name, info in honours_programs.items():
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