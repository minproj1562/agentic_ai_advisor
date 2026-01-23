# academic-advisor-backend/ml_server.py

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import numpy as np
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Academic Advisor ML Server", version="2.0.0")

# CORS middleware - MUST be added
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ======================== Request Models ========================

class PredictionRequest(BaseModel):
    student_id: str
    academic_data: Optional[Dict[str, Any]] = {}
    historical_scores: Optional[List[Dict[str, Any]]] = []
    current_semester: Optional[int] = 1


# ======================== Helper Functions ========================

def generate_predictions(student_id: str, cgpa: float = 7.0, semester: int = 1) -> Dict[str, Any]:
    """Generate predictions for a student"""
    
    predicted_gpa = min(10.0, cgpa + np.random.uniform(-0.3, 0.5))
    confidence = 0.75 + np.random.uniform(0, 0.15)
    
    if cgpa < 6.0:
        risk_level = "High"
        risk_probability = 0.7
    elif cgpa < 7.0:
        risk_level = "Medium"
        risk_probability = 0.4
    else:
        risk_level = "Low"
        risk_probability = 0.15
    
    recommendations = []
    if cgpa < 7.0:
        recommendations.extend([
            "Focus on improving core subject understanding",
            "Increase study hours by 2-3 hours daily"
        ])
    if cgpa < 8.0:
        recommendations.extend([
            "Practice more numerical problems",
            "Form study groups for difficult subjects"
        ])
    else:
        recommendations.extend([
            "Maintain current study routine",
            "Consider taking on challenging projects"
        ])
    
    return {
        "student_id": student_id,
        "predictions": {
            "next_semester_gpa": round(predicted_gpa, 2),
            "confidence_score": round(confidence, 2),
            "risk_level": risk_level,
            "risk_probability": round(risk_probability, 2),
            "expected_graduation_cgpa": round(cgpa + 0.2, 2),
            "improvement_potential": round(np.random.uniform(0.2, 0.5), 2)
        },
        "risk_factors": [
            f"Current CGPA: {cgpa}",
            f"Current semester: {semester}"
        ] if risk_level != "Low" else [],
        "recommendations": recommendations[:4],
        "trend_analysis": {
            "trend": "improving" if np.random.random() > 0.5 else "stable",
            "average_gpa": cgpa,
            "best_semester": max(1, semester - 1),
            "worst_semester": 1
        },
        "generated_at": datetime.now().isoformat()
    }


# ======================== API ENDPOINTS ========================

@app.get("/")
async def root():
    return {
        "message": "Academic Advisor ML Server",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }


# GET endpoint for predictions - THIS IS WHAT YOUR FRONTEND CALLS
@app.get("/api/v1/predictions/{student_id}")
async def get_predictions(
    student_id: str,
    cgpa: float = Query(default=7.0, ge=0, le=10),
    semester: int = Query(default=1, ge=1, le=8)
):
    """Get predictions for a student - GET method"""
    try:
        logger.info(f"GET predictions for student: {student_id}")
        return generate_predictions(student_id, cgpa, semester)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# POST endpoint for predictions
@app.post("/api/v1/predictions/{student_id}")
async def post_predictions(student_id: str, request: PredictionRequest):
    """Get predictions for a student - POST method"""
    try:
        logger.info(f"POST predictions for student: {student_id}")
        cgpa = request.academic_data.get('current_cgpa', 7.0) if request.academic_data else 7.0
        semester = request.current_semester or 1
        return generate_predictions(student_id, cgpa, semester)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET weakness analysis
@app.get("/api/v1/weakness-analysis/{student_id}")
async def get_weakness_analysis(student_id: str):
    """Get weakness analysis - GET method"""
    return {
        "student_id": student_id,
        "analysis": {
            "weaknesses": [],
            "strengths": [],
            "overall_performance": "no_data",
            "study_plan": {"weekly_hours": 20, "focus_areas": []}
        },
        "message": "Add scores to get detailed analysis",
        "generated_at": datetime.now().isoformat()
    }


# GET career prediction
@app.get("/api/v1/career-prediction/{student_id}")
async def get_career_prediction(student_id: str):
    """Get career predictions - GET method"""
    return {
        "student_id": student_id,
        "recommended_careers": [
            {"career": "Software Developer", "match_score": 85, "salary_range": "6-25 LPA"},
            {"career": "Data Scientist", "match_score": 80, "salary_range": "8-30 LPA"},
            {"career": "Full Stack Developer", "match_score": 82, "salary_range": "5-22 LPA"}
        ],
        "generated_at": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("Starting ML Server on http://localhost:5001")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="info")