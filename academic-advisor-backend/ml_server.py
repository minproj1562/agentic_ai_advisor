# academic-advisor-backend/ml_server.py
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import logging
from datetime import datetime
import joblib
import json
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize models
sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

app = FastAPI(title="Academic Advisor ML Server", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================== PYDANTIC MODELS ========================

class StudentData(BaseModel):
    student_id: str
    branch: str
    current_semester: int
    current_cgpa: float
    attendance_percentage: float
    assignments_completed: int
    total_assignments: int
    study_hours_per_week: float
    extracurricular_activities: List[str]

class SubjectScore(BaseModel):
    subject_code: str
    subject_name: str
    credits: int
    internal_marks: float
    external_marks: float
    total_marks: float
    grade: str
    semester: int

class PredictionRequest(BaseModel):
    student_id: str
    academic_data: Dict[str, Any]
    historical_scores: List[Dict[str, Any]]
    current_semester: int
    subject_scores: Optional[List[SubjectScore]] = []

class WeaknessAnalysisRequest(BaseModel):
    student_id: str
    subject_scores: List[Dict[str, Any]]
    target_cgpa: float = 8.0

class CareerPredictionRequest(BaseModel):
    student_id: str
    skills: List[str]
    interests: List[str]
    cgpa: float
    projects: List[str]
    internships: List[str]

# ======================== ML MODELS ========================

class AcademicPredictor:
    def __init__(self):
        self.gpa_model = None
        self.risk_model = None
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize and train base models with synthetic data"""
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 1000
        
        # Features: prev_gpa, attendance, assignments, study_hours, activities_count
        X_train = np.column_stack([
            np.random.uniform(5.0, 10.0, n_samples),  # Previous GPA
            np.random.uniform(60, 100, n_samples),    # Attendance
            np.random.uniform(0.5, 1.0, n_samples),   # Assignment completion ratio
            np.random.uniform(10, 50, n_samples),     # Study hours per week
            np.random.randint(0, 5, n_samples)        # Number of activities
        ])
        
        # Target: Next semester GPA (influenced by features)
        y_gpa = (
            0.7 * X_train[:, 0] +  # Previous GPA weight
            0.1 * (X_train[:, 1] / 100) * 10 +  # Attendance influence
            0.1 * X_train[:, 2] * 10 +  # Assignments influence
            0.05 * np.log1p(X_train[:, 3]) +  # Study hours (diminishing returns)
            0.05 * (5 - X_train[:, 4]) / 5  # Activities (balanced is better)
        ) + np.random.normal(0, 0.3, n_samples)
        
        y_gpa = np.clip(y_gpa, 4.0, 10.0)
        
        # Fit scaler and models
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # GPA Prediction Model
        self.gpa_model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            random_state=42
        )
        self.gpa_model.fit(X_train_scaled, y_gpa)
        
        # Risk Model (binary classification: at-risk if GPA < 6.5)
        y_risk = (y_gpa < 6.5).astype(int)
        from sklearn.ensemble import RandomForestClassifier
        self.risk_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self.risk_model.fit(X_train_scaled, y_risk)
        
        # Store feature importance
        self.feature_importance = {
            'previous_gpa': 0.45,
            'attendance': 0.20,
            'assignments': 0.15,
            'study_hours': 0.12,
            'activities': 0.08
        }
    
    def predict_gpa(self, features: np.ndarray) -> Tuple[float, float]:
        """Predict next semester GPA with confidence"""
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        
        # Get prediction
        predicted_gpa = self.gpa_model.predict(features_scaled)[0]
        
        # Calculate confidence based on feature quality
        confidence = self._calculate_confidence(features)
        
        return float(np.clip(predicted_gpa, 4.0, 10.0)), confidence
    
    def assess_risk(self, features: np.ndarray) -> Dict[str, Any]:
        """Assess academic risk level"""
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        
        risk_probability = self.risk_model.predict_proba(features_scaled)[0]
        risk_level = self.risk_model.predict(features_scaled)[0]
        
        risk_factors = []
        feature_names = ['previous_gpa', 'attendance', 'assignments', 'study_hours', 'activities']
        
        for i, (name, value) in enumerate(zip(feature_names, features)):
            if name == 'previous_gpa' and value < 6.5:
                risk_factors.append(f"Low CGPA: {value:.2f}")
            elif name == 'attendance' and value < 75:
                risk_factors.append(f"Low attendance: {value:.1f}%")
            elif name == 'assignments' and value < 0.7:
                risk_factors.append(f"Incomplete assignments: {value*100:.0f}%")
        
        return {
            'risk_level': 'High' if risk_level == 1 else 'Low',
            'risk_probability': float(risk_probability[1]),
            'risk_factors': risk_factors,
            'recommendations': self._generate_risk_recommendations(features, feature_names)
        }
    
    def _calculate_confidence(self, features: np.ndarray) -> float:
        """Calculate prediction confidence based on data quality"""
        base_confidence = 0.7
        
        # Adjust based on data completeness
        if features[0] > 0:  # Has previous GPA
            base_confidence += 0.1
        if features[1] > 70:  # Good attendance
            base_confidence += 0.1
        if features[2] > 0.8:  # Good assignment completion
            base_confidence += 0.1
        
        return min(base_confidence, 0.95)
    
    def _generate_risk_recommendations(self, features: np.ndarray, feature_names: List[str]) -> List[str]:
        """Generate personalized recommendations based on risk factors"""
        recommendations = []
        
        for i, (name, value) in enumerate(zip(feature_names, features)):
            if name == 'previous_gpa' and value < 7.0:
                recommendations.append("Focus on improving core subject understanding")
                recommendations.append("Consider joining study groups or tutoring sessions")
            elif name == 'attendance' and value < 75:
                recommendations.append("Improve attendance to at least 75% to avoid grade penalties")
            elif name == 'assignments' and value < 0.8:
                recommendations.append("Complete all assignments on time for better internal marks")
            elif name == 'study_hours' and value < 20:
                recommendations.append("Increase study hours to at least 3-4 hours daily")
        
        return recommendations[:3]  # Return top 3 recommendations

class WeaknessAnalyzer:
    def __init__(self):
        self.subject_thresholds = {
            'excellent': 85,
            'good': 70,
            'average': 60,
            'poor': 50,
            'fail': 40
        }
    
    def analyze_weaknesses(self, subject_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze subject-wise weaknesses"""
        weaknesses = []
        strengths = []
        
        for subject in subject_scores:
            total_marks = subject.get('total_marks', 0)
            subject_name = subject.get('subject_name', 'Unknown')
            credits = subject.get('credits', 3)
            
            performance = self._categorize_performance(total_marks)
            
            if performance in ['poor', 'fail']:
                weakness_detail = {
                    'subject': subject_name,
                    'marks': total_marks,
                    'credits': credits,
                    'performance': performance,
                    'gap': 60 - total_marks if total_marks < 60 else 0,
                    'topics': self._identify_weak_topics(subject),
                    'improvement_strategy': self._generate_improvement_strategy(subject)
                }
                weaknesses.append(weakness_detail)
            elif performance in ['excellent', 'good']:
                strengths.append({
                    'subject': subject_name,
                    'marks': total_marks,
                    'performance': performance
                })
        
        return {
            'weaknesses': weaknesses,
            'strengths': strengths,
            'overall_performance': self._calculate_overall_performance(subject_scores),
            'priority_subjects': self._prioritize_subjects(weaknesses),
            'study_plan': self._generate_study_plan(weaknesses)
        }
    
    def _categorize_performance(self, marks: float) -> str:
        """Categorize performance based on marks"""
        for category, threshold in self.subject_thresholds.items():
            if marks >= threshold:
                return category
        return 'fail'
    
    def _identify_weak_topics(self, subject: Dict[str, Any]) -> List[str]:
        """Identify potential weak topics based on marks distribution"""
        internal = subject.get('internal_marks', 0)
        external = subject.get('external_marks', 0)
        topics = []
        
        # Analyze internal vs external performance
        if internal < 12:  # Less than 60% in internals
            topics.append("Class participation and assignments")
        if external < 48:  # Less than 60% in externals
            topics.append("Core concepts and theory")
        
        # Subject-specific analysis
        subject_name = subject.get('subject_name', '').lower()
        if 'programming' in subject_name and external < 50:
            topics.extend(["Algorithm design", "Code optimization"])
        elif 'mathematics' in subject_name and external < 50:
            topics.extend(["Problem solving", "Theoretical proofs"])
        elif 'database' in subject_name and external < 50:
            topics.extend(["Query optimization", "Normalization"])
        
        return topics
    
    def _generate_improvement_strategy(self, subject: Dict[str, Any]) -> List[str]:
        """Generate improvement strategies for weak subjects"""
        strategies = []
        total_marks = subject.get('total_marks', 0)
        
        if total_marks < 40:
            strategies.append("Seek immediate tutoring or remedial classes")
            strategies.append("Form study groups with high-performing peers")
        elif total_marks < 60:
            strategies.append("Focus on understanding fundamental concepts")
            strategies.append("Practice more problems and past papers")
        
        # Add specific strategies based on internal/external performance
        if subject.get('internal_marks', 20) < 12:
            strategies.append("Improve assignment submission and class participation")
        if subject.get('external_marks', 80) < 48:
            strategies.append("Dedicate more time to self-study and revision")
        
        return strategies[:3]
    
    def _calculate_overall_performance(self, subject_scores: List[Dict[str, Any]]) -> str:
        """Calculate overall performance category"""
        if not subject_scores:
            return "No data"
        
        avg_marks = np.mean([s.get('total_marks', 0) for s in subject_scores])
        return self._categorize_performance(avg_marks)
    
    def _prioritize_subjects(self, weaknesses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize weak subjects based on credits and performance gap"""
        if not weaknesses:
            return []
        
        # Sort by credits * gap (higher impact subjects first)
        sorted_weaknesses = sorted(
            weaknesses,
            key=lambda x: x['credits'] * x['gap'],
            reverse=True
        )
        
        return sorted_weaknesses[:3]  # Return top 3 priority subjects
    
    def _generate_study_plan(self, weaknesses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a structured study plan"""
        if not weaknesses:
            return {'message': 'No specific weaknesses identified. Maintain current performance!'}
        
        total_hours = len(weaknesses) * 10  # 10 hours per weak subject per week
        
        return {
            'weekly_hours': total_hours,
            'daily_hours': round(total_hours / 7, 1),
            'focus_distribution': {
                w['subject']: f"{(w['gap']/sum(wk['gap'] for wk in weaknesses))*100:.0f}%"
                for w in weaknesses if w['gap'] > 0
            },
            'recommended_resources': [
                "NPTEL courses for conceptual clarity",
                "Previous year question papers",
                "YouTube tutorials for practical subjects"
            ]
        }

class CareerPredictor:
    def __init__(self):
        self.career_paths = {
            'Software Developer': {
                'skills': ['programming', 'algorithms', 'data structures', 'git'],
                'min_cgpa': 7.0,
                'subjects': ['programming', 'software engineering', 'database']
            },
            'Data Scientist': {
                'skills': ['python', 'machine learning', 'statistics', 'sql'],
                'min_cgpa': 7.5,
                'subjects': ['mathematics', 'statistics', 'machine learning']
            },
            'DevOps Engineer': {
                'skills': ['linux', 'docker', 'kubernetes', 'ci/cd'],
                'min_cgpa': 7.0,
                'subjects': ['operating systems', 'networks', 'cloud computing']
            },
            'Full Stack Developer': {
                'skills': ['javascript', 'react', 'nodejs', 'databases'],
                'min_cgpa': 6.5,
                'subjects': ['web development', 'database', 'programming']
            },
            'AI/ML Engineer': {
                'skills': ['python', 'tensorflow', 'deep learning', 'mathematics'],
                'min_cgpa': 8.0,
                'subjects': ['machine learning', 'mathematics', 'artificial intelligence']
            },
            'Cybersecurity Analyst': {
                'skills': ['networking', 'security', 'cryptography', 'ethical hacking'],
                'min_cgpa': 7.0,
                'subjects': ['networks', 'cryptography', 'information security']
            }
        }
    
    def predict_career_paths(self, skills: List[str], interests: List[str], 
                            cgpa: float, projects: List[str]) -> List[Dict[str, Any]]:
        """Predict suitable career paths based on profile"""
        career_matches = []
        
        for career, requirements in self.career_paths.items():
            # Calculate match score
            skill_match = self._calculate_skill_match(skills, requirements['skills'])
            cgpa_match = 1.0 if cgpa >= requirements['min_cgpa'] else cgpa / requirements['min_cgpa']
            interest_match = self._calculate_interest_match(interests, career)
            project_relevance = self._calculate_project_relevance(projects, requirements['skills'])
            
            # Weighted score
            total_score = (
                skill_match * 0.4 +
                cgpa_match * 0.2 +
                interest_match * 0.2 +
                project_relevance * 0.2
            ) * 100
            
            if total_score > 50:  # Minimum threshold
                career_matches.append({
                    'career': career,
                    'match_score': round(total_score, 1),
                    'skill_match': round(skill_match * 100, 1),
                    'cgpa_eligible': cgpa >= requirements['min_cgpa'],
                    'missing_skills': [s for s in requirements['skills'] if s not in [sk.lower() for sk in skills]],
                    'salary_range': self._get_salary_range(career),
                    'growth_potential': self._get_growth_potential(career),
                    'preparation_path': self._generate_preparation_path(career, skills, cgpa)
                })
        
        # Sort by match score
        career_matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return career_matches[:5]  # Return top 5 matches
    
    def _calculate_skill_match(self, user_skills: List[str], required_skills: List[str]) -> float:
        """Calculate skill match percentage"""
        user_skills_lower = [s.lower() for s in user_skills]
        matched = sum(1 for skill in required_skills if skill in user_skills_lower)
        return matched / len(required_skills) if required_skills else 0
    
    def _calculate_interest_match(self, interests: List[str], career: str) -> float:
        """Calculate interest alignment with career"""
        career_keywords = career.lower().split()
        interests_lower = ' '.join(interests).lower()
        
        matches = sum(1 for keyword in career_keywords if keyword in interests_lower)
        return min(matches / len(career_keywords), 1.0)
    
    def _calculate_project_relevance(self, projects: List[str], required_skills: List[str]) -> float:
        """Calculate project relevance to required skills"""
        if not projects:
            return 0
        
        projects_text = ' '.join(projects).lower()
        skill_mentions = sum(1 for skill in required_skills if skill in projects_text)
        
        return min(skill_mentions / len(required_skills), 1.0)
    
    def _get_salary_range(self, career: str) -> str:
        """Get salary range for career path"""
        salary_ranges = {
            'Software Developer': '6-25 LPA',
            'Data Scientist': '8-30 LPA',
            'DevOps Engineer': '7-28 LPA',
            'Full Stack Developer': '5-22 LPA',
            'AI/ML Engineer': '10-35 LPA',
            'Cybersecurity Analyst': '6-25 LPA'
        }
        return salary_ranges.get(career, '5-20 LPA')
    
    def _get_growth_potential(self, career: str) -> str:
        """Get growth potential for career path"""
        growth_map = {
            'Software Developer': 'High',
            'Data Scientist': 'Very High',
            'DevOps Engineer': 'Very High',
            'Full Stack Developer': 'High',
            'AI/ML Engineer': 'Excellent',
            'Cybersecurity Analyst': 'Very High'
        }
        return growth_map.get(career, 'Moderate')
    
    def _generate_preparation_path(self, career: str, current_skills: List[str], cgpa: float) -> List[str]:
        """Generate preparation steps for career"""
        path = []
        requirements = self.career_paths.get(career, {})
        
        # CGPA improvement if needed
        if cgpa < requirements.get('min_cgpa', 7.0):
            path.append(f"Improve CGPA to at least {requirements['min_cgpa']}")
        
        # Skill gaps
        missing_skills = [s for s in requirements.get('skills', []) 
                         if s not in [sk.lower() for sk in current_skills]]
        if missing_skills:
            path.append(f"Learn: {', '.join(missing_skills[:3])}")
        
        # General recommendations
        path.extend([
            "Build 2-3 relevant projects",
            "Complete online certifications",
            "Apply for internships in the domain"
        ])
        
        return path[:4]

# ======================== ML MODEL INSTANCES ========================

predictor = AcademicPredictor()
weakness_analyzer = WeaknessAnalyzer()
career_predictor = CareerPredictor()

# ======================== API ENDPOINTS ========================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "models": {
            "sentence_transformer": "all-MiniLM-L6-v2",
            "gpa_predictor": "GradientBoostingRegressor",
            "risk_assessor": "RandomForestClassifier",
            "weakness_analyzer": "Active",
            "career_predictor": "Active"
        },
        "version": "2.0.0"
    }

@app.post("/api/v1/predictions/{student_id}")
async def get_predictions(student_id: str, request: PredictionRequest):
    """Get comprehensive ML predictions for student performance"""
    try:
        # Extract features from request
        academic_data = request.academic_data
        
        features = np.array([
            academic_data.get('current_cgpa', 7.0),
            academic_data.get('attendance_percentage', 75),
            academic_data.get('assignment_completion_ratio', 0.8),
            academic_data.get('study_hours_per_week', 25),
            len(academic_data.get('extracurricular_activities', []))
        ])
        
        # Get predictions
        predicted_gpa, confidence = predictor.predict_gpa(features)
        risk_assessment = predictor.assess_risk(features)
        
        # Analyze historical data for trends
        trend_analysis = analyze_performance_trend(request.historical_scores)
        
        # Generate comprehensive recommendations
        recommendations = generate_personalized_recommendations(
            predicted_gpa=predicted_gpa,
            risk_assessment=risk_assessment,
            trend_analysis=trend_analysis,
            academic_data=academic_data
        )
        
        return {
            "student_id": student_id,
            "predictions": {
                "next_semester_gpa": round(predicted_gpa, 2),
                "confidence_score": round(confidence, 2),
                "risk_level": risk_assessment['risk_level'],
                "risk_probability": round(risk_assessment['risk_probability'], 2),
                "expected_graduation_cgpa": calculate_expected_graduation_cgpa(
                    current_cgpa=academic_data.get('current_cgpa', 7.0),
                    predicted_gpa=predicted_gpa,
                    current_semester=request.current_semester
                ),
                "improvement_potential": calculate_improvement_potential(features)
            },
            "risk_factors": risk_assessment['risk_factors'],
            "recommendations": recommendations,
            "trend_analysis": trend_analysis,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Prediction error for {student_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/weakness-analysis")
async def analyze_weaknesses(request: WeaknessAnalysisRequest):
    """Analyze subject-wise weaknesses and generate improvement strategies"""
    try:
        analysis = weakness_analyzer.analyze_weaknesses(request.subject_scores)
        
        # Add personalized study recommendations
        cgpa_gap = request.target_cgpa - sum(s.get('total_marks', 0) for s in request.subject_scores) / (len(request.subject_scores) * 10)
        
        analysis['cgpa_improvement_needed'] = max(0, cgpa_gap)
        analysis['estimated_effort_hours'] = calculate_effort_hours(analysis['weaknesses'])
        analysis['success_probability'] = calculate_success_probability(
            weaknesses=analysis['weaknesses'],
            current_performance=analysis['overall_performance']
        )
        
        return {
            "student_id": request.student_id,
            "analysis": analysis,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Weakness analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/career-prediction")
async def predict_career(request: CareerPredictionRequest):
    """Predict suitable career paths based on student profile"""
    try:
        career_paths = career_predictor.predict_career_paths(
            skills=request.skills,
            interests=request.interests,
            cgpa=request.cgpa,
            projects=request.projects
        )
        
        # Add industry insights
        for career in career_paths:
            career['industry_demand'] = get_industry_demand(career['career'])
            career['required_certifications'] = get_certifications(career['career'])
            career['top_companies'] = get_top_companies(career['career'])
        
        return {
            "student_id": request.student_id,
            "recommended_careers": career_paths,
            "skill_development_priority": identify_priority_skills(
                career_paths, request.skills
            ),
            "internship_recommendations": generate_internship_recommendations(
                career_paths[:3], request.cgpa
            ),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Career prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/embeddings")
async def get_embeddings(texts: List[str]):
    """Get text embeddings using SentenceTransformer"""
    try:
        embeddings = sentence_model.encode(texts)
        
        return {
            "embeddings": embeddings.tolist(),
            "shape": embeddings.shape,
            "model": "all-MiniLM-L6-v2"
        }
        
    except Exception as e:
        logger.error(f"Embedding error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/similarity")
async def calculate_similarity(texts: List[str]):
    """Calculate semantic similarity between texts"""
    try:
        embeddings = sentence_model.encode(texts)
        
        # Calculate cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarity_matrix = cosine_similarity(embeddings)
        
        # Find most similar pairs
        similar_pairs = []
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                similar_pairs.append({
                    'text1': texts[i][:50] + '...' if len(texts[i]) > 50 else texts[i],
                    'text2': texts[j][:50] + '...' if len(texts[j]) > 50 else texts[j],
                    'similarity': float(similarity_matrix[i][j])
                })
        
        similar_pairs.sort(key=lambda x: x['similarity'], reverse=True)
        
        return {
            "similarity_matrix": similarity_matrix.tolist(),
            "most_similar_pairs": similar_pairs[:5],
            "average_similarity": float(np.mean(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)]))
        }
        
    except Exception as e:
        logger.error(f"Similarity calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ======================== HELPER FUNCTIONS ========================

def analyze_performance_trend(historical_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze performance trends from historical data"""
    if not historical_scores:
        return {"trend": "insufficient_data"}
    
    gpas = [score.get('gpa', 0) for score in historical_scores]
    
    if len(gpas) < 2:
        return {"trend": "insufficient_data", "gpas": gpas}
    
    # Calculate trend
    trend_coefficient = np.polyfit(range(len(gpas)), gpas, 1)[0]
    
    return {
        "trend": "improving" if trend_coefficient > 0.1 else "declining" if trend_coefficient < -0.1 else "stable",
        "trend_coefficient": float(trend_coefficient),
        "average_gpa": float(np.mean(gpas)),
        "gpa_variance": float(np.var(gpas)),
        "best_semester": int(np.argmax(gpas) + 1),
        "worst_semester": int(np.argmin(gpas) + 1)
    }

def generate_personalized_recommendations(predicted_gpa: float, risk_assessment: Dict[str, Any],
                                         trend_analysis: Dict[str, Any], 
                                         academic_data: Dict[str, Any]) -> List[str]:
    """Generate personalized recommendations based on comprehensive analysis"""
    recommendations = []
    
    # GPA-based recommendations
    if predicted_gpa < 6.5:
        recommendations.append("🎯 Focus on core subjects to improve fundamental understanding")
        recommendations.append("📚 Attend extra tutoring sessions for difficult subjects")
    elif predicted_gpa < 7.5:
        recommendations.append("📈 Maintain consistency and aim for higher grades in electives")
    else:
        recommendations.append("🌟 Excellent performance! Consider advanced courses or research projects")
    
    # Risk-based recommendations
    recommendations.extend(risk_assessment.get('recommendations', []))
    
    # Trend-based recommendations
    if trend_analysis.get('trend') == 'declining':
        recommendations.append("⚠️ Address the declining trend by reviewing study methods")
    elif trend_analysis.get('trend') == 'improving':
        recommendations.append("✅ Great improvement! Keep up the current study approach")
    
    # Activity-based recommendations
    activities = len(academic_data.get('extracurricular_activities', []))
    if activities == 0:
        recommendations.append("🎭 Join at least one extracurricular activity for holistic development")
    elif activities > 3:
        recommendations.append("⚖️ Consider balancing extracurricular activities with academics")
    
    return recommendations[:5]  # Return top 5 recommendations

def calculate_expected_graduation_cgpa(current_cgpa: float, predicted_gpa: float, 
                                      current_semester: int) -> float:
    """Calculate expected CGPA at graduation"""
    remaining_semesters = 8 - current_semester
    if remaining_semesters <= 0:
        return current_cgpa
    
    # Weighted calculation
    total_weight = current_semester + remaining_semesters
    expected_cgpa = (current_cgpa * current_semester + predicted_gpa * remaining_semesters) / total_weight
    
    return round(min(10.0, max(4.0, expected_cgpa)), 2)

def calculate_improvement_potential(features: np.ndarray) -> float:
    """Calculate potential for improvement based on current performance"""
    current_gpa = features[0]
    attendance = features[1]
    assignments = features[2]
    
    # Calculate potential based on gaps
    gpa_potential = (10 - current_gpa) / 10
    attendance_potential = (100 - attendance) / 100
    assignment_potential = (1 - assignments)
    
    # Weighted potential
    potential = (gpa_potential * 0.5 + attendance_potential * 0.3 + assignment_potential * 0.2)
    
    return round(min(1.0, max(0.0, potential)), 2)

def calculate_effort_hours(weaknesses: List[Dict[str, Any]]) -> int:
    """Calculate estimated effort hours needed for improvement"""
    if not weaknesses:
        return 0
    
    total_hours = 0
    for weakness in weaknesses:
        gap = weakness.get('gap', 0)
        credits = weakness.get('credits', 3)
        
        # Estimate hours based on gap and credits
        hours_needed = (gap / 10) * credits * 5  # 5 hours per credit per 10% gap
        total_hours += hours_needed
    
    return int(total_hours)

def calculate_success_probability(weaknesses: List[Dict[str, Any]], 
                                 current_performance: str) -> float:
    """Calculate probability of achieving target performance"""
    base_probability = {
        'excellent': 0.9,
        'good': 0.75,
        'average': 0.6,
        'poor': 0.4,
        'fail': 0.25
    }.get(current_performance, 0.5)
    
    # Adjust based on number of weaknesses
    weakness_penalty = len(weaknesses) * 0.05
    
    return round(max(0.1, min(0.95, base_probability - weakness_penalty)), 2)

def get_industry_demand(career: str) -> str:
    """Get current industry demand for career path"""
    demand_map = {
        'Software Developer': 'Very High',
        'Data Scientist': 'High',
        'DevOps Engineer': 'Very High',
        'Full Stack Developer': 'High',
        'AI/ML Engineer': 'Very High',
        'Cybersecurity Analyst': 'High'
    }
    return demand_map.get(career, 'Moderate')

def get_certifications(career: str) -> List[str]:
    """Get recommended certifications for career path"""
    cert_map = {
        'Software Developer': ['AWS Developer', 'Microsoft Azure', 'Google Cloud'],
        'Data Scientist': ['TensorFlow Certificate', 'AWS ML Specialty', 'DataCamp'],
        'DevOps Engineer': ['Docker Certified', 'Kubernetes CKA', 'Jenkins CI/CD'],
        'Full Stack Developer': ['Meta Front-End', 'Meta Back-End', 'MongoDB Certified'],
        'AI/ML Engineer': ['Deep Learning Specialization', 'TensorFlow Developer', 'PyTorch'],
        'Cybersecurity Analyst': ['CEH', 'CompTIA Security+', 'CISSP Associate']
    }
    return cert_map.get(career, ['Industry Certifications'])

def get_top_companies(career: str) -> List[str]:
    """Get top hiring companies for career path"""
    company_map = {
        'Software Developer': ['Microsoft', 'Google', 'Amazon', 'Apple', 'Meta'],
        'Data Scientist': ['Google', 'Amazon', 'Microsoft', 'IBM', 'Netflix'],
        'DevOps Engineer': ['Amazon', 'Google', 'Microsoft', 'RedHat', 'HashiCorp'],
        'Full Stack Developer': ['Meta', 'Airbnb', 'Uber', 'Netflix', 'Spotify'],
        'AI/ML Engineer': ['OpenAI', 'Google DeepMind', 'Microsoft', 'Tesla', 'NVIDIA'],
        'Cybersecurity Analyst': ['Palo Alto', 'CrowdStrike', 'FireEye', 'IBM', 'Cisco']
    }
    return company_map.get(career, ['Top Tech Companies'])[:3]

def identify_priority_skills(career_paths: List[Dict[str, Any]], 
                            current_skills: List[str]) -> List[str]:
    """Identify priority skills to develop based on career matches"""
    all_missing_skills = []
    for career in career_paths[:3]:  # Top 3 careers
        all_missing_skills.extend(career.get('missing_skills', []))
    
    # Count frequency and prioritize
    from collections import Counter
    skill_counts = Counter(all_missing_skills)
    
    return [skill for skill, _ in skill_counts.most_common(5)]

def generate_internship_recommendations(top_careers: List[Dict[str, Any]], 
                                       cgpa: float) -> List[Dict[str, str]]:
    """Generate internship recommendations based on career paths"""
    recommendations = []
    
    for career in top_careers:
        career_name = career['career']
        recommendations.append({
            'role': f"{career_name} Intern",
            'duration': '3-6 months',
            'skills_to_gain': career.get('missing_skills', [])[:3],
            'min_cgpa_required': '7.0' if cgpa >= 7.0 else '6.5',
            'application_tip': f"Highlight projects related to {career_name.lower()}"
        })
    
    return recommendations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "ml_server:app",
        host="0.0.0.0",
        port=5001,
        reload=True,
        log_level="info"
    )