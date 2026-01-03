# app/api/v1/endpoints/weakness.py
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any
import logging

from app.ml.weakness_predictor import WeaknessAnalyzer
from app.models.weakness import WeaknessAnalysisResult, TopicAnalysis  # Fixed import
from app.models.student import StudentPerformance, Subject  # Fixed import path

router = APIRouter()
logger = logging.getLogger(__name__)
weakness_analyzer = WeaknessAnalyzer()

def generate_topic_scores(subject: Subject) -> Dict[str, float]:
    """Generate topic scores based on subject performance"""
    base_score = subject.score
    topics = {
        "Fundamentals": base_score * 0.9,
        "Problem Solving": base_score * 0.85,
        "Advanced Concepts": base_score * 0.75,
        "Practical Application": base_score * 0.8,
        "Theory": base_score * 0.95
    }
    return topics

def generate_exam_weights(subject: Subject) -> Dict[str, float]:
    """Generate exam weights for different topics"""
    return {
        "Fundamentals": 0.25,
        "Problem Solving": 0.3,
        "Advanced Concepts": 0.2,
        "Practical Application": 0.15,
        "Theory": 0.1
    }

@router.get("/{student_id}/weaknesses")
async def get_weakness_analysis(
    student_id: str,
    regenerate: bool = Query(False),
    current_user: Dict[str, Any] = Depends(lambda: {"uid": "test_user"})
):
    """Get AI-powered weakness analysis"""
    try:
        # Verify authorization
        if current_user["uid"] != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Check for existing analysis
        if not regenerate:
            cached_analysis = await WeaknessAnalysisResult.find(
                WeaknessAnalysisResult.student_id == student_id,
                WeaknessAnalysisResult.is_current == True
            ).to_list()
            
            if cached_analysis:
                return [analysis.dict() for analysis in cached_analysis]
        
        # Get student performance
        performance = await StudentPerformance.find_one(
            StudentPerformance.student_info.uid == student_id
        ).sort(-StudentPerformance.updated_at)
        
        if not performance:
            raise HTTPException(status_code=404, detail="Student data not found")
        
        # Analyze weaknesses for each subject
        analyses = []
        
        for subject in performance.subjects:
            if subject.score < 75:  # Only analyze subjects below threshold
                # Generate topic-wise scores and weights
                topic_scores = generate_topic_scores(subject)
                exam_weights = generate_exam_weights(subject)
                
                # Analyze weaknesses
                weakness_topics = weakness_analyzer.analyze_topic_weakness(
                    topic_scores,
                    subject.score,
                    exam_weights
                )
                
                # Generate AI analysis
                ai_analysis = weakness_analyzer.generate_ai_analysis(
                    subject.name,
                    weakness_topics,
                    performance.dict()
                )
                
                # Create analysis result
                analysis_result = WeaknessAnalysisResult(
                    student_id=student_id,
                    subject_code=subject.code,
                    subject_name=subject.name,  # Fixed field name
                    overall_score=subject.score,
                    semester=performance.student_info.semester,
                    exam_pattern=topic_scores,
                    ai_analysis=ai_analysis,
                    is_current=True
                )
                
                # Invalidate old analyses for this subject
                await WeaknessAnalysisResult.find(
                    WeaknessAnalysisResult.student_id == student_id,
                    WeaknessAnalysisResult.subject_code == subject.code
                ).update({"$set": {"is_current": False}})
                
                # Save new analysis
                await analysis_result.save()
                
                analyses.append(analysis_result)
        
        return [analysis.dict() for analysis in analyses]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing weaknesses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{student_id}/weaknesses/{subject_code}")
async def get_subject_weakness_analysis(
    student_id: str,
    subject_code: str,
    current_user: Dict[str, Any] = Depends(lambda: {"uid": "test_user"})
):
    """Get detailed weakness analysis for a specific subject"""
    try:
        if current_user["uid"] != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        analysis = await WeaknessAnalysisResult.find_one(
            WeaknessAnalysisResult.student_id == student_id,
            WeaknessAnalysisResult.subject_code == subject_code,
            WeaknessAnalysisResult.is_current == True
        )
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return analysis.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching subject weakness analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))