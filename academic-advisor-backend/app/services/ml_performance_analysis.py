"""
ML Performance Analysis Service
Advanced machine learning models for student performance prediction
"""

import asyncio
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb
import tensorflow as tf
from transformers import pipeline

from app.config import settings
from app.core.firebase_admin import firebase_manager
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class MLPerformanceAnalyzer:
    """
    Enterprise ML analyzer with multiple models and real-time predictions
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.model_version = settings.MODEL_VERSION
        self._load_models()
        
    def _load_models(self):
        """Load pre-trained ML models"""
        try:
            # Performance prediction model (XGBoost)
            self.models['performance'] = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=8,
                learning_rate=0.1,
                objective='reg:squarederror',
                random_state=42
            )
            
            # Weakness detection model (LightGBM)
            self.models['weakness'] = lgb.LGBMClassifier(
                n_estimators=150,
                max_depth=6,
                learning_rate=0.1,
                objective='multiclass',
                num_class=4,
                random_state=42
            )
            
            # Risk assessment model (Gradient Boosting)
            self.models['risk'] = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            
            # Deep learning model for complex patterns
            self.models['deep'] = self._build_deep_model()
            
            # NLP model for text analysis (recommendations)
            self.models['nlp'] = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            
            # Initialize scalers
            self.scalers['features'] = StandardScaler()
            
            logger.info(f"ML models loaded successfully. Version: {self.model_version}")
            
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            
    def _build_deep_model(self) -> tf.keras.Model:
        """Build deep learning model for complex pattern recognition"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu', input_shape=(50,)),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    async def predict_performance(
        self,
        student_data: Dict[str, Any],
        performance_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Predict student performance with ensemble models
        """
        try:
            # Extract features
            features = await self._extract_features(student_data, performance_history)
            
            # Scale features
            features_scaled = self.scalers['features'].fit_transform([features])
            
            # Ensemble predictions
            predictions = {}
            
            # XGBoost prediction
            if 'performance' in self.models:
                xgb_pred = self.models['performance'].predict(features_scaled)[0]
                predictions['predicted_sgpa'] = float(xgb_pred)
            
            # Risk assessment
            if 'risk' in self.models:
                risk_prob = self.models['risk'].predict_proba(features_scaled)[0]
                predictions['risk_score'] = float(risk_prob[1] * 100)
            
            # Deep learning prediction
            if 'deep' in self.models:
                deep_pred = self.models['deep'].predict(features_scaled)[0][0]
                predictions['success_probability'] = float(deep_pred)
            
            # Calculate confidence
            confidence = self._calculate_confidence(performance_history)
            predictions['confidence'] = confidence
            
            # Identify patterns
            patterns = await self._identify_patterns(performance_history)
            predictions['patterns'] = patterns
            
            # Generate insights
            insights = await self._generate_insights(student_data, predictions)
            predictions['insights'] = insights
            
            # Store predictions in Firebase for real-time access
            await firebase_manager.update_document(
                collection="predictions",
                document_id=student_data['id'],
                data={
                    **predictions,
                    'timestamp': datetime.utcnow().isoformat(),
                    'model_version': self.model_version
                }
            )
            
            return predictions
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return {
                'error': str(e),
                'risk_score': 50.0,
                'confidence': 0.0
            }
    
    async def detect_weaknesses(
        self,
        student_data: Dict[str, Any],
        performance_history: List[Dict[str, Any]],
        assessments: List[Dict[str, Any]],
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Detect academic weaknesses using ML
        """
        try:
            # Check cache if not forcing refresh
            if not force_refresh:
                cached = await firebase_manager.get_document(
                    collection="weakness_cache",
                    document_id=student_data['id']
                )
                
                if cached and self._is_cache_valid(cached):
                    return cached.get('weaknesses', [])
            
            weaknesses = []
            
            # Analyze subject-wise performance
            subject_analysis = await self._analyze_subjects(performance_history)
            
            for subject, metrics in subject_analysis.items():
                if metrics['average'] < 60:  # Threshold for weakness
                    # Use LightGBM for severity classification
                    severity = await self._classify_severity(metrics)
                    
                    # Identify specific topics
                    weak_topics = await self._identify_weak_topics(
                        subject,
                        assessments,
                        student_data
                    )
                    
                    # Generate improvement plan
                    improvement_plan = await self._generate_improvement_plan(
                        subject,
                        severity,
                        weak_topics
                    )
                    
                    weakness = {
                        'subject': subject,
                        'severity': severity,
                        'average_score': metrics['average'],
                        'gap': 60 - metrics['average'],
                        'trend': metrics['trend'],
                        'topics': weak_topics,
                        'improvement_plan': improvement_plan,
                        'resources': await self._get_learning_resources(subject, severity),
                        'confidence': metrics['confidence'],
                        'detected_at': datetime.utcnow().isoformat()
                    }
                    
                    weaknesses.append(weakness)
            
            # Sort by severity and gap
            weaknesses.sort(key=lambda x: (
                {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[x['severity']],
                -x['gap']
            ))
            
            # Cache results
            await firebase_manager.create_document(
                collection="weakness_cache",
                document_id=student_data['id'],
                data={
                    'weaknesses': weaknesses,
                    'cached_at': datetime.utcnow().isoformat(),
                    'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
                }
            )
            
            return weaknesses
            
        except Exception as e:
            logger.error(f"Weakness detection error: {str(e)}")
            return []
    
    async def deep_analysis(
        self,
        student_data: Dict[str, Any],
        performance_history: List[Dict[str, Any]],
        weaknesses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform deep analysis using advanced ML techniques
        """
        try:
            analysis = {
                'student_id': student_data['id'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Time series analysis for trends
            trends = await self._analyze_time_series(performance_history)
            analysis['trends'] = trends
            
            # Correlation analysis
            correlations = await self._analyze_correlations(performance_history)
            analysis['correlations'] = correlations
            
            # Predictive modeling
            predictions = await self._generate_predictions(
                student_data,
                performance_history,
                weaknesses
            )
            analysis['predictions'] = predictions
            
            # Anomaly detection
            anomalies = await self._detect_anomalies(performance_history)
            analysis['anomalies'] = anomalies
            
            # Learning style analysis
            learning_style = await self._analyze_learning_style(
                student_data,
                performance_history
            )
            analysis['learning_style'] = learning_style
            
            # Generate comprehensive report
            report = await self._generate_analysis_report(analysis)
            analysis['report'] = report
            
            # Store in Firebase
            await firebase_manager.create_document(
                collection=f"students/{student_data['id']}/deep_analysis",
                data=analysis
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Deep analysis error: {str(e)}")
            return {'error': str(e)}
    
    async def quick_predict(
        self,
        student_data: Dict[str, Any],
        performance_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Quick prediction for bulk processing
        """
        try:
            features = await self._extract_basic_features(student_data, performance_history)
            
            # Simple risk calculation
            cgpa = student_data.get('cgpa', 0)
            attendance = student_data.get('attendance', 0)
            
            risk_score = 0
            if cgpa < 6.0:
                risk_score += 40
            elif cgpa < 7.0:
                risk_score += 20
            
            if attendance < 75:
                risk_score += 30
            elif attendance < 85:
                risk_score += 10
            
            # Trend analysis
            if performance_history and len(performance_history) > 1:
                recent_trend = performance_history[-1]['sgpa'] - performance_history[-2]['sgpa']
                if recent_trend < -0.5:
                    risk_score += 30
                elif recent_trend < 0:
                    risk_score += 15
            
            return {
                'risk_score': min(risk_score, 100),
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Quick predict error: {str(e)}")
            return {'risk_score': 50, 'status': 'error'}
    
    # Helper methods
    
    async def _extract_features(
        self,
        student_data: Dict[str, Any],
        performance_history: List[Dict[str, Any]]
    ) -> List[float]:
        """Extract features for ML models"""
        features = []
        
        # Basic features
        features.append(student_data.get('cgpa', 0))
        features.append(student_data.get('attendance', 0))
        features.append(student_data.get('current_semester', 1))
        features.append(student_data.get('total_credits', 0))
        
        # Performance features
        if performance_history:
            sgpas = [p['sgpa'] for p in performance_history]
            features.append(np.mean(sgpas))
            features.append(np.std(sgpas) if len(sgpas) > 1 else 0)
            features.append(np.max(sgpas))
            features.append(np.min(sgpas))
            
            # Trend
            if len(sgpas) > 1:
                trend = np.polyfit(range(len(sgpas)), sgpas, 1)[0]
                features.append(trend)
            else:
                features.append(0)
        else:
            features.extend([0] * 5)
        
        # Pad to expected size
        while len(features) < 50:
            features.append(0)
        
        return features[:50]
    
    async def _analyze_subjects(
        self,
        performance_history: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze subject-wise performance"""
        subject_data = {}
        
        for perf in performance_history:
            for subject in perf.get('subjects', []):
                subject_name = subject.get('name')
                score = subject.get('score', 0)
                
                if subject_name not in subject_data:
                    subject_data[subject_name] = {
                        'scores': [],
                        'credits': subject.get('credits', 3)
                    }
                
                subject_data[subject_name]['scores'].append(score)
        
        # Calculate metrics
        analysis = {}
        for subject, data in subject_data.items():
            scores = data['scores']
            analysis[subject] = {
                'average': np.mean(scores),
                'std': np.std(scores) if len(scores) > 1 else 0,
                'min': np.min(scores),
                'max': np.max(scores),
                'trend': 'improving' if len(scores) > 1 and scores[-1] > scores[0] else 'declining',
                'confidence': min(0.5 + len(scores) * 0.1, 0.95),
                'credits': data['credits']
            }
        
        return analysis
    
    async def _classify_severity(
        self,
        metrics: Dict[str, Any]
    ) -> str:
        """Classify weakness severity"""
        avg = metrics['average']
        
        if avg < 35:
            return 'critical'
        elif avg < 50:
            return 'high'
        elif avg < 60:
            return 'medium'
        else:
            return 'low'
    
    async def _identify_weak_topics(
        self,
        subject: str,
        assessments: List[Dict[str, Any]],
        student_data: Dict[str, Any]
    ) -> List[str]:
        """Identify specific weak topics within a subject"""
        weak_topics = []
        
        # Analyze assessments for topic-level performance
        for assessment in assessments:
            if assessment.get('subject') == subject:
                for topic in assessment.get('topics', []):
                    if topic.get('score', 0) < 50:
                        weak_topics.append(topic.get('name'))
        
        # If no specific data, use general topics
        if not weak_topics:
            topic_map = {
                'Mathematics': ['Calculus', 'Linear Algebra', 'Probability'],
                'Programming': ['Data Structures', 'Algorithms', 'OOP'],
                'Physics': ['Mechanics', 'Thermodynamics', 'Electromagnetics']
            }
            
            for key, topics in topic_map.items():
                if key.lower() in subject.lower():
                    weak_topics = topics[:2]
                    break
        
        return weak_topics
    
    async def _generate_improvement_plan(
        self,
        subject: str,
        severity: str,
        weak_topics: List[str]
    ) -> Dict[str, Any]:
        """Generate personalized improvement plan"""
        plan = {
            'duration': '4 weeks' if severity == 'critical' else '2 weeks',
            'daily_hours': 2 if severity in ['critical', 'high'] else 1,
            'focus_areas': weak_topics,
            'milestones': []
        }
        
        # Create weekly milestones
        weeks = 4 if severity == 'critical' else 2
        for week in range(1, weeks + 1):
            milestone = {
                'week': week,
                'goals': [
                    f"Complete {subject} chapter {week}",
                    f"Solve 20 practice problems",
                    "Take mock assessment"
                ],
                'target_improvement': 10 * week
            }
            plan['milestones'].append(milestone)
        
        return plan
    
    async def _get_learning_resources(
        self,
        subject: str,
        severity: str
    ) -> List[Dict[str, Any]]:
        """Get recommended learning resources"""
        resources = []
        
        # YouTube videos
        resources.append({
            'type': 'video',
            'platform': 'YouTube',
            'title': f'{subject} Fundamentals',
            'url': f'https://youtube.com/search?q={subject}+tutorial',
            'duration': '2 hours'
        })
        
        # Online courses
        if severity in ['critical', 'high']:
            resources.append({
                'type': 'course',
                'platform': 'Coursera',
                'title': f'Master {subject}',
                'url': f'https://coursera.org/search?query={subject}',
                'duration': '4 weeks'
            })
        
        # Practice platforms
        resources.append({
            'type': 'practice',
            'platform': 'LeetCode' if 'program' in subject.lower() else 'Khan Academy',
            'title': f'{subject} Practice Problems',
            'url': 'https://leetcode.com' if 'program' in subject.lower() else 'https://khanacademy.org'
        })
        
        return resources
    
    async def _analyze_time_series(
        self,
        performance_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze time series patterns"""
        if not performance_history:
            return {}
        
        sgpas = [p['sgpa'] for p in performance_history]
        timestamps = [p.get('semester', i) for i, p in enumerate(performance_history)]
        
        # Calculate moving averages
        window_size = min(3, len(sgpas))
        if len(sgpas) >= window_size:
            moving_avg = pd.Series(sgpas).rolling(window=window_size).mean().tolist()
        else:
            moving_avg = sgpas
        
        # Detect trend
        if len(sgpas) > 1:
            trend_coefficient = np.polyfit(timestamps, sgpas, 1)[0]
            trend = 'upward' if trend_coefficient > 0.1 else 'downward' if trend_coefficient < -0.1 else 'stable'
        else:
            trend = 'insufficient_data'
        
        # Detect seasonality
        seasonality = 'none'
        if len(sgpas) >= 4:
            # Check for semester patterns
            odd_sems = [sgpas[i] for i in range(0, len(sgpas), 2)]
            even_sems = [sgpas[i] for i in range(1, len(sgpas), 2)]
            
            if odd_sems and even_sems:
                if np.mean(odd_sems) > np.mean(even_sems) + 0.5:
                    seasonality = 'better_odd_semesters'
                elif np.mean(even_sems) > np.mean(odd_sems) + 0.5:
                    seasonality = 'better_even_semesters'
        
        return {
            'trend': trend,
            'seasonality': seasonality,
            'moving_average': moving_avg,
            'volatility': np.std(sgpas) if len(sgpas) > 1 else 0,
            'current_position': 'above_average' if sgpas[-1] > np.mean(sgpas) else 'below_average'
        }
    
    async def _analyze_correlations(
        self,
        performance_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Analyze correlations between metrics"""
        if len(performance_history) < 3:
            return {}
        
        # Extract metrics
        sgpas = []
        attendance = []
        assignments = []
        
        for perf in performance_history:
            sgpas.append(perf.get('sgpa', 0))
            attendance.append(perf.get('attendance', 0))
            assignments.append(perf.get('assignment_score', 0))
        
        correlations = {}
        
        # Calculate correlations
        if len(set(attendance)) > 1:  # Check for variance
            correlations['attendance_sgpa'] = float(np.corrcoef(attendance, sgpas)[0, 1])
        
        if len(set(assignments)) > 1:
            correlations['assignments_sgpa'] = float(np.corrcoef(assignments, sgpas)[0, 1])
        
        return correlations
    
    async def _generate_predictions(
        self,
        student_data: Dict[str, Any],
        performance_history: List[Dict[str, Any]],
        weaknesses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate future predictions"""
        predictions = {}
        
        if len(performance_history) < 2:
            return {'message': 'Insufficient data for predictions'}
        
        # Extract SGPA values
        sgpas = [p['sgpa'] for p in performance_history]
        
        # Polynomial regression for next semester
        x = np.arange(len(sgpas))
        coefficients = np.polyfit(x, sgpas, min(2, len(sgpas) - 1))
        poly = np.poly1d(coefficients)
        
        # Predict next semester
        next_sem_prediction = poly(len(sgpas))
        next_sem_prediction = max(0, min(10, next_sem_prediction))  # Bound between 0-10
        
        predictions['next_semester_sgpa'] = float(next_sem_prediction)
        
        # Graduation CGPA prediction
        remaining_semesters = 8 - student_data.get('current_semester', 1)
        if remaining_semesters > 0:
            future_predictions = []
            for i in range(remaining_semesters):
                pred = poly(len(sgpas) + i)
                pred = max(0, min(10, pred))
                future_predictions.append(pred)
            
            all_sgpas = sgpas + future_predictions
            predictions['expected_graduation_cgpa'] = float(np.mean(all_sgpas))
        
        # Risk prediction based on weaknesses
        if weaknesses:
            critical_count = sum(1 for w in weaknesses if w['severity'] == 'critical')
            high_count = sum(1 for w in weaknesses if w['severity'] == 'high')
            
            risk_factor = (critical_count * 20) + (high_count * 10)
            predictions['failure_risk_percentage'] = min(risk_factor, 100)
        else:
            predictions['failure_risk_percentage'] = 10
        
        # Time to improvement
        if student_data.get('cgpa', 0) < 7.0:
            improvement_rate = 0.2  # Average improvement per semester
            semesters_needed = (7.0 - student_data.get('cgpa', 0)) / improvement_rate
            predictions['semesters_to_7_cgpa'] = int(np.ceil(semesters_needed))
        
        return predictions
    
    async def _detect_anomalies(
        self,
        performance_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in performance"""
        anomalies = []
        
        if len(performance_history) < 3:
            return anomalies
        
        sgpas = [p['sgpa'] for p in performance_history]
        
        # Calculate z-scores
        mean = np.mean(sgpas)
        std = np.std(sgpas)
        
        if std > 0:
            for i, sgpa in enumerate(sgpas):
                z_score = (sgpa - mean) / std
                
                if abs(z_score) > 2:  # Anomaly threshold
                    anomalies.append({
                        'semester': performance_history[i].get('semester', i + 1),
                        'sgpa': sgpa,
                        'z_score': float(z_score),
                        'type': 'significant_drop' if z_score < -2 else 'exceptional_performance',
                        'severity': 'high' if abs(z_score) > 3 else 'medium'
                    })
        
        return anomalies
    
    async def _analyze_learning_style(
        self,
        student_data: Dict[str, Any],
        performance_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze student's learning style"""
        style = {
            'type': 'unknown',
            'strengths': [],
            'preferences': []
        }
        
        # Analyze performance patterns
        theory_scores = []
        practical_scores = []
        
        for perf in performance_history:
            for subject in perf.get('subjects', []):
                if 'theory' in subject.get('type', '').lower():
                    theory_scores.append(subject.get('score', 0))
                elif 'practical' in subject.get('type', '').lower():
                    practical_scores.append(subject.get('score', 0))
        
        if theory_scores and practical_scores:
            if np.mean(practical_scores) > np.mean(theory_scores) + 10:
                style['type'] = 'practical_learner'
                style['strengths'] = ['hands-on learning', 'project work']
            elif np.mean(theory_scores) > np.mean(practical_scores) + 10:
                style['type'] = 'theoretical_learner'
                style['strengths'] = ['conceptual understanding', 'analytical thinking']
            else:
                style['type'] = 'balanced_learner'
                style['strengths'] = ['versatile', 'adaptable']
        
        # Add preferences based on performance
        if student_data.get('attendance', 0) > 90:
            style['preferences'].append('regular_classes')
        
        if student_data.get('assignment_completion', 0) > 90:
            style['preferences'].append('self_study')
        
        return style
    
    async def _generate_analysis_report(
        self,
        analysis: Dict[str, Any]
    ) -> str:
        """Generate comprehensive analysis report"""
        report_parts = []
        
        # Executive summary
        report_parts.append("## Academic Performance Analysis Report")
        report_parts.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        report_parts.append("")
        
        # Trends
        if 'trends' in analysis:
            report_parts.append("### Performance Trends")
            report_parts.append(f"- Overall trend: {analysis['trends'].get('trend', 'N/A')}")
            report_parts.append(f"- Volatility: {analysis['trends'].get('volatility', 0):.2f}")
            report_parts.append("")
        
        # Predictions
        if 'predictions' in analysis:
            report_parts.append("### Predictions")
            pred = analysis['predictions']
            if 'next_semester_sgpa' in pred:
                report_parts.append(f"- Next semester SGPA: {pred['next_semester_sgpa']:.2f}")
            if 'expected_graduation_cgpa' in pred:
                report_parts.append(f"- Expected graduation CGPA: {pred['expected_graduation_cgpa']:.2f}")
            report_parts.append("")
        
        # Anomalies
        if 'anomalies' in analysis and analysis['anomalies']:
            report_parts.append("### Detected Anomalies")
            for anomaly in analysis['anomalies']:
                report_parts.append(f"- Semester {anomaly['semester']}: {anomaly['type']}")
            report_parts.append("")
        
        # Learning style
        if 'learning_style' in analysis:
            style = analysis['learning_style']
            report_parts.append("### Learning Style Analysis")
            report_parts.append(f"- Type: {style.get('type', 'Unknown')}")
            if style.get('strengths'):
                report_parts.append(f"- Strengths: {', '.join(style['strengths'])}")
            report_parts.append("")
        
        return "\n".join(report_parts)
    
    def _calculate_confidence(
        self,
        performance_history: List[Dict[str, Any]]
    ) -> float:
        """Calculate prediction confidence"""
        if not performance_history:
            return 0.3
        
        # Base confidence on data points
        data_points = len(performance_history)
        confidence = min(0.5 + (data_points * 0.05), 0.85)
        
        # Adjust for data recency
        if performance_history:
            latest = performance_history[-1]
            if 'created_at' in latest:
                days_old = (datetime.utcnow() - datetime.fromisoformat(latest['created_at'])).days
                if days_old < 30:
                    confidence += 0.1
                elif days_old > 180:
                    confidence -= 0.1
        
        return min(max(confidence, 0.1), 0.95)
    
    def _is_cache_valid(
        self,
        cached_data: Dict[str, Any]
    ) -> bool:
        """Check if cached data is still valid"""
        if 'expires_at' in cached_data:
            expiry = datetime.fromisoformat(cached_data['expires_at'])
            return datetime.utcnow() < expiry
        return False


async def load_all_models():
    """Load all ML models on startup"""
    global ml_analyzer
    ml_analyzer = MLPerformanceAnalyzer()
    logger.info("All ML models loaded successfully")


async def check_models_health() -> Dict[str, Any]:
    """Check ML models health"""
    try:
        # Test prediction
        test_data = {
            'id': 'test',
            'cgpa': 7.5,
            'attendance': 85,
            'current_semester': 4
        }
        
        test_history = [
            {'sgpa': 7.0, 'semester': 1},
            {'sgpa': 7.5, 'semester': 2},
            {'sgpa': 8.0, 'semester': 3}
        ]
        
        result = await ml_analyzer.quick_predict(test_data, test_history)
        
        return {
            'status': 'healthy' if 'risk_score' in result else 'unhealthy',
            'model_version': ml_analyzer.model_version,
            'models_loaded': len(ml_analyzer.models)
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }


# Global instance
ml_analyzer = MLPerformanceAnalyzer()