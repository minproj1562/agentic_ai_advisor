#academic-advisor-backend/app/ml/ml_service.py
from typing import List, Dict, Any, Optional
import logging
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pandas as pd

logger = logging.getLogger(__name__)

class MLPredictionService:
    def __init__(self):
        self.logger = logger
        self.performance_model = RandomForestRegressor()
        self.risk_model = RandomForestRegressor()
        self.scaler = StandardScaler()
        self.models_trained = False

    async def predict_average_performance(self, features: List[Dict[str, Any]]) -> float:
        """Predict next month's average performance"""
        try:
            if not features:
                return 7.0  # Default average
            
            # Convert features to DataFrame
            df = pd.DataFrame(features)
            
            # Simple prediction logic (replace with trained model)
            current_avg = df['current_sgpi'].mean()
            previous_avg = df['previous_sgpi'].mean()
            
            # Simple trend-based prediction
            trend = current_avg - previous_avg
            predicted = current_avg + (trend * 0.1)  # Small adjustment based on trend
            
            return max(0, min(10, predicted))  # Ensure within valid range
            
        except Exception as e:
            self.logger.error(f"Error predicting performance: {e}")
            return 7.0  # Fallback value

    async def predict_at_risk_students(self, features: List[Dict[str, Any]]) -> List[float]:
        """Predict at-risk probability for each student"""
        try:
            if not features:
                return []
            
            risk_scores = []
            for feature_set in features:
                # Simple risk calculation
                risk_score = 0.0
                
                # Low SGPI
                if feature_set.get('current_sgpi', 0) < 6.0:
                    risk_score += 0.4
                
                # Declining performance
                current = feature_set.get('current_sgpi', 0)
                previous = feature_set.get('previous_sgpi', 0)
                if current < previous:
                    risk_score += 0.3
                
                # Poor attendance
                if feature_set.get('attendance', 100) < 75:
                    risk_score += 0.2
                
                # Low assignment completion
                if feature_set.get('assignment_completion', 100) < 70:
                    risk_score += 0.1
                
                risk_scores.append(min(1.0, risk_score))
            
            return risk_scores
            
        except Exception as e:
            self.logger.error(f"Error predicting at-risk students: {e}")
            return [0.0] * len(features)

    async def calculate_success_probability(
        self, 
        features: List[Dict[str, Any]], 
        target_sgpi: float = 7.5
    ) -> float:
        """Calculate probability of meeting target SGPI"""
        try:
            if not features:
                return 0.5  # Default probability
            
            # Simple success probability calculation
            current_avg = np.mean([f.get('current_sgpi', 0) for f in features])
            above_target = len([f for f in features if f.get('current_sgpi', 0) >= target_sgpi])
            
            base_probability = above_target / len(features) if features else 0
            
            # Adjust based on trends
            improving_trends = len([
                f for f in features 
                if f.get('current_sgpi', 0) > f.get('previous_sgpi', 0)
            ])
            
            trend_adjustment = (improving_trends / len(features)) * 0.2 if features else 0
            
            final_probability = base_probability + trend_adjustment
            return min(1.0, max(0.0, final_probability))
            
        except Exception as e:
            self.logger.error(f"Error calculating success probability: {e}")
            return 0.5

    async def generate_recommendations(
        self, 
        faculty_id: str, 
        features: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate AI-powered recommendations"""
        recommendations = []
        
        # Analyze features to generate recommendations
        avg_sgpi = np.mean([f.get('current_sgpi', 0) for f in features]) if features else 0
        at_risk_count = len([f for f in features if f.get('current_sgpi', 0) < 6.0])
        
        if avg_sgpi < 7.0:
            recommendations.append(
                "Focus on foundational concepts and regular practice sessions for struggling students"
            )
        
        if at_risk_count > len(features) * 0.3:  # More than 30% at risk
            recommendations.append(
                "Consider implementing additional support programs or tutoring for at-risk students"
            )
        
        # Check attendance patterns
        low_attendance = len([f for f in features if f.get('attendance', 100) < 75])
        if low_attendance > 0:
            recommendations.append(
                "Address attendance issues through personalized counseling and engagement strategies"
            )
        
        # Add general best practices
        recommendations.extend([
            "Schedule regular progress review meetings with each mentee",
            "Encourage participation in academic support programs",
            "Provide timely feedback on assignments and projects"
        ])
        
        return recommendations[:5]  # Return top 5 recommendations