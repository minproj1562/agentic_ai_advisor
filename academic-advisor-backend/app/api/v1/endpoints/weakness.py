# app/api/v1/endpoints/weaknesses.py
from app.ml.weakness_predictor import WeaknessAnalyzer
from app.models.analytics import WeaknessAnalysisResult

router = APIRouter()
weakness_analyzer = WeaknessAnalyzer()

@router.get("/{student_id}/weaknesses")
async def get_weakness_analysis(
    student_id: str,
    regenerate: bool = Query(False),
    current_user = Depends(get_current_user)
):
    """Get AI-powered weakness analysis"""
    try:
        # Verify authorization
        if current_user.uid != student_id and current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Check for existing analysis
        if not regenerate:
            cached_analysis = await WeaknessAnalysisResult.find(
                WeaknessAnalysisResult.student_id == student_id,
                WeaknessAnalysisResult.is_current == True
            ).to_list()
            
            if cached_analysis:
                return [a.dict() for a in cached_analysis]
        
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
                # Simulate topic-wise scores (in production, fetch from DB)
                topic_scores = generate_topic_scores(subject)
                exam_weights = generate_exam_weights(subject)
                
                # Analyze weaknesses
                weakness_topics = weakness_analyzer.analyze_topic_weakness(
                    topic_scores,
                    subject.score,
                    exam_weights
                    # app/api/v1/endpoints/weaknesses.py (continued)
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
                    subject=subject.name,
                    overall_score=subject.score,
                    semester=performance.student_info.semester,
                    topics=weakness_topics,
                    ai_analysis=ai_analysis,
                    is_current=True
                )
                
                # Invalidate old analyses
                await WeaknessAnalysisResult.find(
                    WeaknessAnalysisResult.student_id == student_id,
                    WeaknessAnalysisResult.subject_code == subject.code
                ).update({"$set": {"is_current": False}})
                
                # Save new analysis
                await analysis_result.save()
                
                analyses.append(analysis_result.dict())
        
        return analyses
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing weaknesses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_topic_scores(subject: Subject) -> Dict[str, float]:
    """Generate topic scores (placeholder - fetch from DB in production)"""
    topics = {
        "Fundamentals": subject.score * 0.9,
        "Problem Solving": subject.score * 0.85,
        "Advanced Concepts": subject.score * 0.75,
        "Practical Application": subject.score * 0.8,
        "Theory": subject.score * 0.95
    }
    return topics

def generate_exam_weights(subject: Subject) -> Dict[str, float]:
    """Generate exam weights (placeholder - fetch from DB in production)"""
    return {
        "Fundamentals": 0.25,
        "Problem Solving": 0.3,
        "Advanced Concepts": 0.2,
        "Practical Application": 0.15,
        "Theory": 0.1
    }
