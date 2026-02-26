# academic-advisor/academic-advisor-backend/app/ml/models/performance_predictor.py
"""
Performance Prediction ML Model
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import joblib
from typing import Dict, List, Any, Tuple

from app.utils.helpers import get_logger

logger = get_logger(__name__)


class PerformancePredictor:
    """
    ML model for predicting student performance
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'current_cgpa', 'attendance', 'assignment_completion',
            'previous_sgpa', 'study_hours', 'semester',
            'dept_avg', 'participation_score', 'quiz_average',
            'lab_performance', 'project_score', 'extracurricular'
        ]
        self.model_type = 'xgboost'
        
    def train(
        self,
        training_data: pd.DataFrame,
        target_column: str = 'next_sgpa'
    ) -> Dict[str, Any]:
        """
        Train the performance prediction model
        """
        try:
            # Prepare features and target
            X = training_data[self.feature_columns]
            y = training_data[target_column]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model based on type
            if self.model_type == 'xgboost':
                self.model = xgb.XGBRegressor(
                    n_estimators=200,
                    max_depth=8,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42
                )
            elif self.model_type == 'random_forest':
                self.model = RandomForestRegressor(
                    n_estimators=200,
                    max_depth=10,
                    min_samples_split=5,
                    random_state=42
                )
            else:
                self.model = GradientBoostingRegressor(
                    n_estimators=200,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=42
                )
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)
            
            # Cross-validation
            cv_scores = cross_val_score(
                self.model, X_train_scaled, y_train, cv=5
            )
            
            # Feature importance
            feature_importance = self.get_feature_importance()
            
            logger.info(f"Model trained successfully. Test R²: {test_score:.3f}")
            
            return {
                'train_score': train_score,
                'test_score': test_score,
                'cv_score_mean': cv_scores.mean(),
                'cv_score_std': cv_scores.std(),
                'feature_importance': feature_importance,
                'model_type': self.model_type
            }
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            raise
    
    def predict(
        self,
        student_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict performance for a student
        """
        try:
            if self.model is None:
                raise ValueError("Model not trained")
            
            # Prepare features
            features = []
            for col in self.feature_columns:
                features.append(student_data.get(col, 0))
            
            # Scale features
            features_scaled = self.scaler.transform([features])
            
            # Make prediction
            prediction = self.model.predict(features_scaled)[0]
            
            # Calculate confidence interval
            if hasattr(self.model, 'predict_proba'):
                confidence = self.model.predict_proba(features_scaled)[0].max()
            else:
                # Use a heuristic for confidence
                confidence = self._calculate_confidence(student_data)
            
            # Get prediction intervals
            lower_bound, upper_bound = self._get_prediction_interval(
                features_scaled, prediction
            )
            
            return {
                'predicted_sgpa': float(prediction),
                'confidence': float(confidence),
                'lower_bound': float(lower_bound),
                'upper_bound': float(upper_bound),
                'risk_category': self._categorize_risk(prediction)
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return {
                'predicted_sgpa': 0.0,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def batch_predict(
        self,
        students_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Predict for multiple students
        """
        predictions = []
        
        for student in students_data:
            pred = self.predict(student)
            pred['student_id'] = student.get('student_id')
            predictions.append(pred)
        
        return predictions
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores
        """
        if self.model is None:
            return {}
        
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            
            return {
                col: float(imp)
                for col, imp in zip(self.feature_columns, importances)
            }
        
        return {}
    
    def save_model(self, path: str):
        """
        Save model to disk
        """
        if self.model:
            joblib.dump(self.model, f"{path}_model.pkl")
            joblib.dump(self.scaler, f"{path}_scaler.pkl")
            logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """
        Load model from disk
        """
        try:
            self.model = joblib.load(f"{path}_model.pkl")
            self.scaler = joblib.load(f"{path}_scaler.pkl")
            logger.info(f"Model loaded from {path}")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
    
    def _calculate_confidence(
        self,
        student_data: Dict[str, Any]
    ) -> float:
        """
        Calculate prediction confidence
        """
        confidence = 0.5
        
        # Increase confidence based on data completeness
        complete_fields = sum(
            1 for col in self.feature_columns
            if student_data.get(col) is not None
        )
        
        confidence += (complete_fields / len(self.feature_columns)) * 0.3
        
        # Adjust based on historical performance consistency
        if 'performance_std' in student_data:
            std = student_data['performance_std']
            if std < 0.5:
                confidence += 0.2
            elif std > 1.5:
                confidence -= 0.1
        
        return min(max(confidence, 0.1), 0.95)
    
    def _get_prediction_interval(
        self,
        features: np.ndarray,
        prediction: float,
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate prediction interval
        """
        # Simple approach: use standard error
        std_error = 0.5  # This should be calculated from training residuals
        
        z_score = 1.96 if confidence_level == 0.95 else 2.58
        margin = z_score * std_error
        
        lower = max(0, prediction - margin)
        upper = min(10, prediction + margin)
        
        return lower, upper
    
    def _categorize_risk(self, predicted_sgpa: float) -> str:
        """
        Categorize risk based on predicted SGPA
        """
        if predicted_sgpa < 5.0:
            return 'high'
        elif predicted_sgpa < 6.5:
            return 'medium'
        elif predicted_sgpa < 7.5:
            return 'low'
        else:
            return 'very_low'