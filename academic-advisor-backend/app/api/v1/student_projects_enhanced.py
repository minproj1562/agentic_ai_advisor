# app/api/v1/student_projects_enhanced.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from typing import List, Optional, Dict, Any
import json
import logging
from app.services.enhanced_ml_inference import FCRITAcademicInferenceEngine
from app.core.security import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)
inference_engine = FCRITAcademicInferenceEngine()

@router.post("/analyze-comprehensive")
async def analyze_project_comprehensive(
    project_data: str = Form(...),
    student_branch: str = Form(...),
    student_semester: int = Form(...),
    files: List[UploadFile] = File(None),
    current_user = Depends(get_current_user)
):
    """
    Comprehensive project analysis including electives, honours/minor, and career mapping
    """
    try:
        # Parse project data
        data = json.loads(project_data)
        
        # Process uploaded files
        uploaded_files = []
        if files:
            for file in files:
                # Save and analyze files
                file_info = {
                    'path': f"/tmp/{file.filename}",
                    'type': file.content_type,
                    'name': file.filename
                }
                # Save file temporarily for analysis
                content = await file.read()
                with open(file_info['path'], 'wb') as f:
                    f.write(content)
                uploaded_files.append(file_info)
        
        # Perform comprehensive analysis
        analysis_result = inference_engine.analyze_project_comprehensive(
            project_data=data,
            student_branch=student_branch,
            student_semester=student_semester,
            uploaded_files=uploaded_files
        )
        
        return {
            "success": True,
            "analysis": analysis_result,
            "student_info": {
                "branch": student_branch,
                "semester": student_semester,
                "user_id": current_user.uid
            }
        }
    
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/honours-programs/{branch}")
async def get_eligible_honours_programs(
    branch: str,
    current_user = Depends(get_current_user)
):
    """Get eligible honours/minor programs for a branch"""
    eligible_programs = []
    
    for program_name, info in inference_engine.honours_programs.items():
        if branch in info['eligible_branches']:
            program_type = "Honours" if branch == info['eligible_branches'][0] else "Minor"
            eligible_programs.append({
                "program": program_name,
                "type": program_type,
                "courses": info['courses'],
                "career_paths": info['career_paths'],
                "skills": info['skills'],
                "credits": 18,
                "duration": "4 semesters"
            })
    
    return eligible_programs

@router.get("/electives/{branch}/{semester}")
async def get_available_electives(
    branch: str,
    semester: int,
    current_user = Depends(get_current_user)
):
    """Get available electives for a branch and semester"""
    if branch in inference_engine.sem5_electives and semester == 5:
        return inference_engine.sem5_electives[branch]
    
    return {"message": "Electives not configured for this branch/semester"}

@router.post("/career-guidance")
async def get_career_guidance(
    interests: List[Dict[str, Any]],
    student_branch: str = Form(...),
    current_user = Depends(get_current_user)
):
    """Get personalized career guidance based on interests"""
    try:
        # Generate career paths
        career_paths = inference_engine._map_career_paths(
            interests=interests,
            honours_recommendations=[],  # Can be populated from DB
            student_branch=student_branch
        )
        
        return {
            "career_paths": career_paths,
            "preparation_timeline": "2-3 years",
            "immediate_actions": [
                "Choose relevant electives next semester",
                "Start building projects in your interest area",
                "Apply for Honours/Minor program if eligible"
            ]
        }
    
    except Exception as e:
        logger.error(f"Error generating career guidance: {e}")
        raise HTTPException(status_code=500, detail=str(e))