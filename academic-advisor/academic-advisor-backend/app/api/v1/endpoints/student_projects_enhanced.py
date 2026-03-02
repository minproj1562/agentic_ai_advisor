# academic-advisor/academic-advisor-backend/app/api/v1/endpoints/student_projects_enhanced.py
"""
Student Projects Enhanced Endpoint
====================================
Consolidated version:
  • Parses uploaded files (PDF, images, code)
  • Extracts skills + infers interests
  • Calls recommendation_engine for cumulative scoring
  • Persists analysis results in StudentProject document
  • Returns response compatible with frontend LegacyProjectAnalysisResult
"""

from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File, Form, Query,
)
from typing import List, Optional, Dict, Any
import json
import logging
import os
import tempfile
import shutil
from datetime import datetime

from app.models.student_profile import StudentProfile
from app.models.student_projects import StudentProject
from app.core.security import get_current_user, FirebaseUser
from app.ml.models.recommendation_engine import recommendation_engine
from app.services.recommendation_service import recommendation_service

# Local analysis engine (no DB, no auth)
from app.services.enhanced_ml_inference import (
    FCRITAcademicInferenceEngine,
    HONOURS_PROGRAMS, SEM5_ELECTIVES,
    INTEREST_PATTERNS, CAREER_MAPPING,
)

router = APIRouter()
logger = logging.getLogger(__name__)

inference_engine = FCRITAcademicInferenceEngine()


# ══════════════════════════════════════════════════════════════════
#  POST /analyze-comprehensive
# ══════════════════════════════════════════════════════════════════

@router.post("/analyze-comprehensive")
async def analyze_project_comprehensive(
    project_data: str = Form(...),
    student_branch: str = Form(None),
    student_semester: int = Form(None),
    files: List[UploadFile] = File(None),
    current_user: FirebaseUser = Depends(get_current_user),
):
    """
    Upload-triggered analysis pipeline:

    1. Parse uploaded files (PDF / image / code)
    2. Extract skills from form data + parsed files
    3. Infer interest domains
    4. Fetch all existing student data (marks, projects, interests)
    5. Merge new project into data snapshot
    6. Run recommendation_engine for electives / honours / careers
    7. Persist analysis on the StudentProject document
    8. Return full response (compatible with frontend LegacyProjectAnalysisResult)
    """
    temp_dirs: List[str] = []
    try:
        data = json.loads(project_data)
        logger.info(f"📊 Comprehensive project analysis for user {current_user.uid}")

        # ── 0. Student profile ────────────────────────────────────
        student = await StudentProfile.find_one(
            StudentProfile.user_id == current_user.uid
        )
        student_branch = student_branch or (student.branch if student else "IT")
        student_semester = student_semester or (student.current_semester if student else 5)

        # ── 1. Save uploaded files to temp dir ────────────────────
        uploaded_files: List[Dict[str, Any]] = []
        if files:
            for f in files:
                if not f.filename:
                    continue
                try:
                    td = tempfile.mkdtemp()
                    temp_dirs.append(td)
                    path = os.path.join(td, f.filename)
                    content = await f.read()
                    with open(path, "wb") as fh:
                        fh.write(content)
                    uploaded_files.append({
                        "path": path,
                        "type": f.content_type,
                        "name": f.filename,
                        "size": len(content),
                    })
                except Exception as e:
                    logger.warning(f"File save error ({f.filename}): {e}")

        # ── 2. Run analysis engine (skills + interests + complexity)
        analysis = inference_engine.analyze_project_comprehensive(
            project_data=data,
            student_branch=student_branch,
            student_semester=student_semester,
            uploaded_files=uploaded_files,
        )

        extracted_skills: List[str] = analysis["extracted_skills"]
        inferred_interests: List[Dict] = analysis["inferred_interests"]
        complexity_score: float = analysis["complexity_score"]

        # ── 3. Update student interests (high confidence) ─────────
        if student and inferred_interests:
            high = [i["domain"] for i in inferred_interests if i.get("confidence", 0) > 0.6]
            if high:
                existing = set(student.interests or [])
                student.interests = list(existing | set(high))[:12]
                student.last_updated = datetime.utcnow()
                await student.save()
                logger.info(f"✅ Updated interests: +{high}")

        # ── 4. Fetch cumulative student data ──────────────────────
        student_data = await recommendation_service.get_student_data(current_user.uid)

        # ── 5. Append new project to snapshot ─────────────────────
        new_proj = {
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "programming_languages": data.get("programmingLanguages", data.get("programming_languages", [])),
            "frameworks": data.get("frameworks", []),
            "tools": data.get("tools", []),
            "technologies": data.get("technologies", []),
            "extracted_skills": extracted_skills,
            "is_team_project": data.get("isTeamProject", data.get("is_team_project", False)),
            "complexity_score": complexity_score,
            "github_url": data.get("githubUrl", data.get("github_url")),
            "demo_url": data.get("demoUrl", data.get("demo_url")),
        }
        student_data["projects"].append(new_proj)

        # Merge inferred interests
        for interest in inferred_interests:
            if interest["confidence"] > 0.5:
                domain = interest["domain"]
                if domain not in student_data["interests"]:
                    student_data["interests"].append(domain)

        # ── 6. Run recommendation engine ──────────────────────────
        elective_recs = recommendation_engine.recommend_electives(
            marks=student_data["marks"],
            interests=student_data["interests"],
            projects=student_data["projects"],
            cgpa=student_data["cgpa"],
            use_ml=recommendation_engine.is_trained,
        )
        honours_recs = recommendation_engine.recommend_honours(
            marks=student_data["marks"],
            interests=student_data["interests"],
            projects=student_data["projects"],
            cgpa=student_data["cgpa"],
        )
        career_recs = recommendation_engine.recommend_careers(
            marks=student_data["marks"],
            interests=student_data["interests"],
            projects=student_data["projects"],
            cgpa=student_data["cgpa"],
        )

        # ── 7. Persist project + analysis to MongoDB ──────────
        try:
            from app.models.student_projects import (
                StudentProject, ProjectType, InferredInterest as InferredInterestModel
            )
            from datetime import datetime as dt

            # Build inferred interest models
            interest_models = []
            for i in inferred_interests:
                interest_models.append(InferredInterestModel(
                    domain=i["domain"],
                    confidence=i["confidence"],
                    keywords=i.get("matched_keywords", []),
                    related_skills=i.get("relatedSkills", []),
                    career_paths=i.get("careerPaths", []),
                    industry_relevance=i.get("industryRelevance", 0),
                    reasoning=f"Detected from project analysis ({len(i.get('matched_keywords', []))} keyword matches)",
                    evidence=i.get("matched_keywords", [])[:5],
                ))

            # Try to find existing project with same title by this student
            existing = await StudentProject.find_one(
                StudentProject.student_id == current_user.uid,
                StudentProject.title == data.get("title", ""),
            )

            if existing:
                # Update existing project's analysis
                existing.extracted_skills = extracted_skills
                existing.complexity_score = complexity_score
                existing.inferred_interests = interest_models
                existing.programming_languages = data.get("programmingLanguages", data.get("programming_languages", []))
                existing.frameworks = data.get("frameworks", [])
                existing.tools = data.get("tools", [])
                existing.technologies = data.get("technologies", [])
                existing.description = data.get("description", existing.description)
                existing.detailed_description = data.get("detailedDescription", data.get("detailed_description", ""))
                existing.github_url = data.get("githubUrl", data.get("github_url"))
                existing.demo_url = data.get("demoUrl", data.get("demo_url"))
                existing.is_team_project = data.get("isTeamProject", data.get("is_team_project", False))
                existing.team_size = data.get("teamSize", data.get("team_size", 1))
                existing.key_achievements = data.get("keyAchievements", data.get("key_achievements", []))
                existing.challenges_faced = data.get("challengesFaced", data.get("challenges_faced", []))
                existing.learnings = data.get("learnings", [])
                existing.updated_at = dt.utcnow()
                await existing.save()
                logger.info(f"✅ Updated existing project in MongoDB: {existing.title}")
            else:
                # CREATE new project in MongoDB so recommendation engine can find it
                project_type_str = data.get("projectType", data.get("project_type", "personal"))
                try:
                    project_type = ProjectType(project_type_str)
                except ValueError:
                    project_type = ProjectType.PERSONAL

                start_date_str = data.get("startDate", data.get("start_date"))
                end_date_str = data.get("endDate", data.get("end_date"))

                try:
                    start_date = dt.fromisoformat(start_date_str.replace("Z", "+00:00")) if start_date_str else dt.utcnow()
                except Exception:
                    start_date = dt.utcnow()

                end_date = None
                if end_date_str:
                    try:
                        end_date = dt.fromisoformat(end_date_str.replace("Z", "+00:00"))
                    except Exception:
                        pass

                new_project = StudentProject(
                    student_id=current_user.uid,
                    title=data.get("title", "Untitled Project"),
                    description=data.get("description", ""),
                    detailed_description=data.get("detailedDescription", data.get("detailed_description", "")),
                    project_type=project_type,
                    start_date=start_date,
                    end_date=end_date,
                    programming_languages=data.get("programmingLanguages", data.get("programming_languages", [])),
                    frameworks=data.get("frameworks", []),
                    tools=data.get("tools", []),
                    technologies=data.get("technologies", []),
                    github_url=data.get("githubUrl", data.get("github_url")),
                    demo_url=data.get("demoUrl", data.get("demo_url")),
                    is_team_project=data.get("isTeamProject", data.get("is_team_project", False)),
                    team_size=data.get("teamSize", data.get("team_size", 1)),
                    key_achievements=data.get("keyAchievements", data.get("key_achievements", [])),
                    challenges_faced=data.get("challengesFaced", data.get("challenges_faced", [])),
                    learnings=data.get("learnings", []),
                    extracted_skills=extracted_skills,
                    complexity_score=complexity_score,
                    inferred_interests=interest_models,
                )
                await new_project.insert()
                logger.info(f"✅ Created new project in MongoDB: {new_project.title}")

        except Exception as e:
            logger.warning(f"Could not persist project to MongoDB: {e}")

        # ── 7b. Invalidate recommendation cache ──────────────
        try:
            await recommendation_service.invalidate_cache(current_user.uid)
            logger.info("♻️ Recommendation cache invalidated after project analysis")
        except Exception as e:
            logger.warning(f"Cache invalidation failed (non-critical): {e}")

        # ── 7c. Create training data point from this analysis ─
        try:
            top_elective = elective_recs[0].get("elective_name", "ML") if elective_recs else "ML"
            name_to_code = {
                "Machine Learning": "ML",
                "Wireless Technology": "WT",
                "Data Warehouse and Mining": "DWM",
                "Cloud Computing Services": "CCS",
            }
            label = name_to_code.get(top_elective, "ML")
            await recommendation_service.create_training_data_from_project(
                student_id=current_user.uid,
                student_data=student_data,
                top_elective=label,
            )
        except Exception as e:
            logger.warning(f"Training data creation failed (non-critical): {e}")

        # ── 8. Build legacy-compatible response ───────────────────
        response = _build_legacy_response(
            inferred_interests=inferred_interests,
            extracted_skills=extracted_skills,
            complexity_score=complexity_score,
            elective_recs=elective_recs,
            honours_recs=honours_recs,
            career_recs=career_recs,
            student_data=student_data,
            student_branch=student_branch,
            student_semester=student_semester,
            analysis=analysis,
        )

        return response

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid project_data JSON")
    except Exception as e:
        logger.error(f"Comprehensive analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for td in temp_dirs:
            shutil.rmtree(td, ignore_errors=True)


def _build_legacy_response(
    *,
    inferred_interests: List[Dict],
    extracted_skills: List[str],
    complexity_score: float,
    elective_recs: List[Dict],
    honours_recs: List[Dict],
    career_recs: List[Dict],
    student_data: Dict,
    student_branch: str,
    student_semester: int,
    analysis: Dict,
) -> Dict[str, Any]:
    """
    Build a response that the frontend can consume directly as
    LegacyProjectAnalysisResult (via student_projects_cloudinary.service).
    """
    # Inferred interests (legacy shape)
    legacy_interests = []
    for i in inferred_interests:
        legacy_interests.append({
            "domain": i["domain"],
            "confidence": i["confidence"],
            "keywords": i.get("matched_keywords", []),
            "relatedSkills": i.get("relatedSkills", []),
            "careerPaths": i.get("careerPaths", []),
            "industryRelevance": i.get("industryRelevance", i["confidence"] * 0.9),
        })

    # Elective recommendations (legacy shape)
    legacy_electives = []
    for e in elective_recs:
        legacy_electives.append({
            "elective": e.get("elective_name", ""),
            "code": e.get("elective_code", ""),
            "match_score": e.get("match_score", 0),
            "reasons": [e.get("match_explanation", "Based on your profile")],
            "skills_to_gain": e.get("skill_alignment", []),
            "career_relevance": ", ".join(e.get("career_relevance", [])),
            "difficulty_level": "Intermediate",
        })

    # Honours/Minor (legacy shape)
    legacy_honours = []
    for h in honours_recs:
        legacy_honours.append({
            "program": h.get("program", ""),
            "type": h.get("type", "Honours"),
            "match_score": h.get("match_score", 0),
            "courses": h.get("skills_gained", []),
            "career_paths": h.get("career_paths", []),
            "credits": 18,
            "semester_commitment": "4 semesters (Sem V-VIII)",
            "reasons": [h.get("explanation", "Based on your profile")],
        })

    # Career paths (legacy shape)
    legacy_careers = []
    for c in career_recs:
        legacy_careers.append({
            "title": c.get("career", ""),
            "match_score": c.get("match_score", 0),
            "salary_range": c.get("salary_range", ""),
            "market_demand": "Very High" if c.get("growth_potential") == "Very High" else "High",
            "growth_potential": c.get("growth_potential", "High"),
            "required_skills": c.get("missing_skills", []),
            "companies_hiring": c.get("top_companies", []),
            "preparation_path": c.get("preparation_path", []),
            "honours_program": None,
        })

    # Skill gaps
    all_project_skills_lower = {s.lower() for s in extracted_skills}
    top_elective_skills = elective_recs[0].get("skill_alignment", []) if elective_recs else []
    skill_gaps = [s for s in top_elective_skills if s.lower() not in all_project_skills_lower]
    top_elective_gap_items = elective_recs[0].get("skill_gaps", []) if elective_recs else []

    # Next steps
    next_steps = []
    if legacy_electives:
        next_steps.append({
            "action": f"Consider choosing '{legacy_electives[0]['elective']}' as your elective",
            "category": "Academic",
            "priority": "high",
            "deadline": "Next registration",
            "details": legacy_electives[0]["reasons"][0] if legacy_electives[0]["reasons"] else "",
        })
    if skill_gaps:
        next_steps.append({
            "action": f"Learn {', '.join(skill_gaps[:3])}",
            "category": "Skills",
            "priority": "high",
            "deadline": "Next 3 months",
            "details": "These skills will strengthen your elective and career alignment.",
        })
    if legacy_careers:
        next_steps.append({
            "action": f"Explore career path: {legacy_careers[0]['title']}",
            "category": "Career",
            "priority": "medium",
            "deadline": "This semester",
            "details": f"Salary range: {legacy_careers[0]['salary_range']}",
        })
    next_steps.append({
        "action": "Upload more projects for better recommendations",
        "category": "Portfolio",
        "priority": "medium",
        "deadline": "Ongoing",
        "details": "Each project improves AI accuracy by ~10-15%.",
    })

    confidence_overall = 0.5
    if student_data:
        factors = 0
        if len(student_data.get("marks", {})) > 3: factors += 0.35
        elif student_data.get("marks"): factors += 0.15
        if len(student_data.get("interests", [])) > 1: factors += 0.25
        elif student_data.get("interests"): factors += 0.1
        if len(student_data.get("projects", [])) > 1: factors += 0.25
        elif student_data.get("projects"): factors += 0.1
        confidence_overall = min(factors + 0.15, 0.95)

    return {
        # ── LegacyProjectAnalysisResult fields ────────────────
        "inferred_interests": legacy_interests,
        "elective_recommendations": legacy_electives,
        "honours_minor_recommendations": legacy_honours,
        "career_paths": legacy_careers,
        "skill_gap_analysis": {
            "current_skills": extracted_skills,
            "skill_gaps": skill_gaps,
            "priority_skills": skill_gaps[:3],
            "learning_resources": {},
            "completeness_percentage": min(
                int((len(extracted_skills) / max(len(extracted_skills) + len(skill_gaps), 1)) * 100),
                95,
            ),
            "estimated_learning_time": "2-3 months",
        },
        "next_steps": next_steps,
        "metadata": {
            "analysis_date": datetime.utcnow().isoformat(),
            "confidence_score": round(confidence_overall, 2),
            "model_version": "2.0.0",
            "data_sources": ["marks", "interests", "projects", "files"],
            "ml_model_used": recommendation_engine.is_trained,
            "files_parsed": analysis.get("file_analysis", {}).get("successfully_parsed", 0),
        },
        # ── Extra: structured recommendations (new frontend) ──
        "cumulative_recommendations": {
            "electives": elective_recs,
            "honours": honours_recs,
            "careers": career_recs,
        },
        "data_summary": {
            "total_marks_subjects": len(student_data.get("marks", {})),
            "total_interests": len(student_data.get("interests", [])),
            "total_projects": len(student_data.get("projects", [])),
            "cgpa": student_data.get("cgpa", 0),
        },
        "student_info": {
            "branch": student_branch,
            "semester": student_semester,
        },
    }


# ══════════════════════════════════════════════════════════════════
#  OTHER ENDPOINTS (kept from original)
# ══════════════════════════════════════════════════════════════════

@router.get("/analysis/{project_id}")
async def get_project_analysis(
    project_id: str,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get stored analysis for a specific project."""
    try:
        project = await StudentProject.find_one(
            StudentProject.id == project_id,
            StudentProject.student_id == current_user.uid,
        )
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return {
            "success": True,
            "project_id": project_id,
            "title": project.title,
            "extracted_skills": project.extracted_skills,
            "inferred_interests": [
                {
                    "domain": i.domain,
                    "confidence": i.confidence,
                    "keywords": i.keywords,
                    "relatedSkills": i.related_skills,
                    "careerPaths": i.career_paths,
                }
                for i in (project.inferred_interests or [])
            ],
            "complexity_score": project.complexity_score,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/honours-programs/{branch}")
async def get_eligible_honours_programs(
    branch: str,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get eligible honours/minor programs for a branch."""
    eligible = []
    for name, info in HONOURS_PROGRAMS.items():
        if branch.upper() not in info["eligible_branches"]:
            continue
        ptype = info.get("type", "Honours")
        if branch.upper() != info["eligible_branches"][0] and ptype == "both":
            ptype = "Minor"
        eligible.append({
            "program": name, "type": ptype,
            "courses": info.get("courses", []),
            "career_paths": info.get("career_paths", []),
            "skills": info.get("skills", []),
            "keywords": info.get("keywords", [])[:5],
            "credits": 18, "duration": "4 semesters (Sem V-VIII)",
            "eligibility": {"min_cgpa": 7.5, "min_semester": 4,
                            "eligible_branches": info["eligible_branches"]},
        })

    student = await StudentProfile.find_one(StudentProfile.user_id == current_user.uid)
    if student and student.interests:
        si = {i.lower() for i in student.interests}
        for p in eligible:
            pk = {k.lower() for k in p.get("keywords", [])}
            p["interest_match_score"] = min(len(si & pk) * 25, 100)
        eligible.sort(key=lambda x: x.get("interest_match_score", 0), reverse=True)

    return {"success": True, "branch": branch,
            "eligible_programs": eligible, "total_count": len(eligible)}


@router.get("/electives/{branch}/{semester}")
async def get_available_electives(
    branch: str, semester: int,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get available electives with personalized recommendations."""
    electives = SEM5_ELECTIVES.get(branch.upper(), {}) if semester == 5 else {}
    if not electives:
        electives = {"message": f"Electives for {branch} Sem {semester}", "available": True}

    student = await StudentProfile.find_one(StudentProfile.user_id == current_user.uid)
    recs: List[Dict] = []
    if student and student.interests:
        for interest in student.interests[:3]:
            low = interest.lower()
            for el in (electives.get("professional", []) if isinstance(electives, dict) else []):
                if any(kw in el.lower() for kw in low.split()):
                    recs.append({"elective": el, "match_reason": f"Matches: {interest}",
                                 "confidence": 0.8})

    return {"success": True, "branch": branch, "semester": semester,
            "electives": electives, "personalized_recommendations": recs,
            "student_interests": student.interests if student else []}


@router.get("/interest-profile")
async def get_interest_profile(
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get student's complete interest profile based on all projects."""
    student = await StudentProfile.find_one(StudentProfile.user_id == current_user.uid)
    if not student:
        return {"success": True, "interests": [], "topDomains": []}

    # Aggregate from projects
    projects = await StudentProject.find(
        StudentProject.student_id == current_user.uid
    ).to_list()

    domain_scores: Dict[str, float] = {}
    domain_project_counts: Dict[str, int] = {}
    for p in projects:
        for ii in (p.inferred_interests or []):
            d = ii.domain if hasattr(ii, "domain") else ii.get("domain", "")
            c = ii.confidence if hasattr(ii, "confidence") else ii.get("confidence", 0)
            domain_scores[d] = domain_scores.get(d, 0) + c
            domain_project_counts[d] = domain_project_counts.get(d, 0) + 1

    # Merge with declared interests
    for i in (student.interests or []):
        if i not in domain_scores:
            domain_scores[i] = 0.5
            domain_project_counts[i] = 0

    top_domains = []
    for domain in sorted(domain_scores, key=domain_scores.get, reverse=True)[:5]:
        info = INTEREST_PATTERNS.get(domain, {})
        strength = min(int(domain_scores[domain] * 50) + 40, 98)
        top_domains.append({
            "name": domain, "strength": strength,
            "projectCount": domain_project_counts.get(domain, 0),
            "relatedSkills": info.get("related_skills", []),
            "careerPaths": info.get("career_paths", []),
        })

    return {
        "success": True,
        "interests": student.interests or [],
        "skills": student.skills or [],
        "career_goals": student.career_goals or [],
        "topDomains": top_domains,
        "profile_completeness": _calc_completeness(student),
    }


@router.post("/quick-analyze")
async def quick_analyze_project(
    title: str = Form(...),
    description: str = Form(...),
    technologies: str = Form(""),
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Quick lightweight analysis without file uploads."""
    tech_list = [t.strip() for t in technologies.split(",") if t.strip()]
    text = f"{title} {description} {' '.join(tech_list)}".lower()

    detected = []
    for domain, info in INTEREST_PATTERNS.items():
        matches = [kw for kw in info["keywords"] if kw in text]
        if matches:
            conf = min(len(matches) / 4.0, 1.0)
            if conf > 0.2:
                detected.append({"domain": domain, "confidence": round(conf, 2),
                                 "matched_keywords": matches[:5]})
    detected.sort(key=lambda x: x["confidence"], reverse=True)

    return {"success": True, "quick_analysis": {
        "detected_interests": detected[:3],
        "technologies_detected": tech_list,
        "suggestions": (["Add more details for better analysis"]
                        if len(detected) < 2 else []),
    }}

@router.delete("/project/{project_id}")
async def delete_project_from_mongodb(
    project_id: str,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Delete a project from MongoDB (called when Firestore project is deleted)."""
    try:
        # Try finding by id field
        project = await StudentProject.find_one(
            StudentProject.student_id == current_user.uid,
            StudentProject.id == project_id,
        )

        if not project:
            # Try by document _id
            from beanie import PydanticObjectId
            try:
                project = await StudentProject.get(project_id)
                if project and project.student_id != current_user.uid:
                    raise HTTPException(status_code=403, detail="Not your project")
            except Exception:
                pass

        if not project:
            # Not found in MongoDB — that's OK, it may have only been in Firestore
            return {"success": True, "message": "Project not found in MongoDB (may only exist in Firestore)"}

        await project.delete()
        logger.info(f"🗑️ Deleted project from MongoDB: {project_id}")

        # Invalidate recommendation cache
        try:
            await recommendation_service.invalidate_cache(current_user.uid)
        except Exception:
            pass

        return {"success": True, "message": "Project deleted from MongoDB"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _calc_completeness(s: StudentProfile) -> int:
    c = 0
    if s.name: c += 15
    if s.email: c += 10
    if s.branch: c += 10
    if s.admission_year: c += 10
    if s.interests and len(s.interests) >= 3: c += 20
    elif s.interests: c += 10
    if s.skills and len(s.skills) >= 3: c += 20
    elif s.skills: c += 10
    if s.career_goals: c += 15
    return min(c, 100)