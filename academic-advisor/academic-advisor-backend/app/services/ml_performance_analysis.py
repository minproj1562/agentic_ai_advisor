# academic-advisor-backend/app/services/ml_performance_analysis.py

"""
ML Performance Analysis Service
Advanced machine learning models for student performance prediction
Enhanced with curriculum awareness and FCRIT-specific features
"""

import asyncio
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import logging

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import joblib

from app.core.firebase_admin import firebase_manager
from app.core.curriculum import get_semester_subjects, ELECTIVE_OPTIONS

logger = logging.getLogger(__name__)


class MLPerformanceAnalyzer:
    """
    Enterprise ML analyzer with curriculum awareness
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.model_version = "2.0.0"
        self._load_models()
        
    def _load_models(self):
        """Load pre-trained ML models"""
        try:
            # Performance prediction model (Random Forest)
            self.models['performance'] = RandomForestRegressor(
                n_estimators=200,
                max_depth=8,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
            
            # Weakness detection model (Gradient Boosting)
            self.models['weakness'] = GradientBoostingClassifier(
                n_estimators=150,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            
            # Risk assessment model
            self.models['risk'] = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            
            # Initialize scalers
            self.scalers['features'] = StandardScaler()
            
            logger.info(f"ML models loaded successfully. Version: {self.model_version}")
            
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
    
    async def predict_performance(
        self,
        student_data: Dict[str, Any],
        performance_history: List[Dict[str, Any]],
        curriculum_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Predict student performance with curriculum awareness
        """
        try:
            # Extract enhanced features
            features = await self._extract_enhanced_features(
                student_data, 
                performance_history,
                curriculum_data
            )
            
            # Scale features
            features_scaled = self.scalers['features'].fit_transform([features])
            
            # Ensemble predictions
            predictions = {}
            
            # Predict next semester SGPA
            if len(performance_history) >= 2:
                predicted_sgpa = await self._predict_next_sgpa(performance_history)
                predictions['predicted_sgpa'] = float(predicted_sgpa)
            else:
                predictions['predicted_sgpa'] = student_data.get('cgpa', 7.0)
            
            # Risk assessment
            risk_score = await self._calculate_risk_score(student_data, performance_history)
            predictions['risk_score'] = float(risk_score)
            predictions['risk_level'] = self._classify_risk_level(risk_score)
            
            # Calculate success probability
            success_prob = await self._calculate_success_probability(
                student_data, 
                performance_history
            )
            predictions['success_probability'] = float(success_prob)
            
            # Calculate confidence
            confidence = self._calculate_confidence(performance_history)
            predictions['confidence'] = confidence
            
            # Identify patterns
            patterns = await self._identify_patterns(performance_history)
            predictions['patterns'] = patterns
            
            # Generate insights
            insights = await self._generate_performance_insights(student_data, predictions)
            predictions['insights'] = insights
            
            # Curriculum-specific recommendations
            if curriculum_data:
                curriculum_insights = await self._generate_curriculum_insights(
                    student_data,
                    predictions,
                    curriculum_data
                )
                predictions['curriculum_insights'] = curriculum_insights
            
            # Store predictions in Firebase
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
        curriculum_data: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Detect academic weaknesses with curriculum awareness
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
                # Define threshold based on curriculum type
                threshold = 60.0  # Default passing threshold
                
                if metrics['average'] < threshold:
                    # Classify severity
                    severity = await self._classify_severity(metrics)
                    
                    # Identify specific topics
                    weak_topics = await self._identify_weak_topics(
                        subject,
                        assessments,
                        student_data,
                        curriculum_data
                    )
                    
                    # Generate improvement plan
                    improvement_plan = await self._generate_improvement_plan(
                        subject,
                        severity,
                        weak_topics,
                        curriculum_data
                    )
                    
                    # Get curriculum-specific resources
                    resources = await self._get_curriculum_resources(
                        subject, 
                        severity,
                        curriculum_data
                    )
                    
                    weakness = {
                        'subject': subject,
                        'severity': severity,
                        'average_score': metrics['average'],
                        'gap': threshold - metrics['average'],
                        'trend': metrics['trend'],
                        'topics': weak_topics,
                        'improvement_plan': improvement_plan,
                        'resources': resources,
                        'confidence': metrics['confidence'],
                        'detected_at': datetime.utcnow().isoformat(),
                        'curriculum_aligned': curriculum_data is not None
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
        weaknesses: List[Dict[str, Any]],
        curriculum_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform deep analysis with curriculum integration
        """
        try:
            analysis = {
                'student_id': student_data['id'],
                'timestamp': datetime.utcnow().isoformat(),
                'curriculum_type': curriculum_data.get('curriculum_type') if curriculum_data else 'Unknown'
            }
            
            # Time series analysis
            trends = await self._analyze_time_series(performance_history)
            analysis['trends'] = trends
            
            # Correlation analysis
            correlations = await self._analyze_correlations(performance_history)
            analysis['correlations'] = correlations
            
            # Predictive modeling
            predictions = await self._generate_future_predictions(
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
            
            # Curriculum-specific analysis
            if curriculum_data:
                curriculum_analysis = await self._analyze_curriculum_progress(
                    student_data,
                    performance_history,
                    curriculum_data
                )
                analysis['curriculum_progress'] = curriculum_analysis
                
                # Elective recommendations
                elective_recs = await self._recommend_electives(
                    student_data,
                    weaknesses,
                    curriculum_data
                )
                analysis['elective_recommendations'] = elective_recs
            
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
    
    # ==================== HELPER METHODS ====================
    
    async def _extract_enhanced_features(
        self,
        student_data: Dict[str, Any],
        performance_history: List[Dict[str, Any]],
        curriculum_data: Optional[Dict[str, Any]] = None
    ) -> List[float]:
        """Extract enhanced features including curriculum data"""
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
        
        # Curriculum-specific features
        if curriculum_data:
            # Curriculum type (0 for Pre-Autonomy, 1 for Autonomy)
            features.append(1 if curriculum_data.get('curriculum_type') == 'Autonomy' else 0)
            
            # Branch encoding
            branch_encoding = {
                'IT': 0, 'COMP': 1, 'EXTC': 2, 'ELEC': 3, 'MECH': 4
            }
            features.append(branch_encoding.get(student_data.get('branch', 'IT'), 0))
        else:
            features.extend([0, 0])
        
        # Pad to expected size
        while len(features) < 50:
            features.append(0)
        
        return features[:50]
    
    async def _predict_next_sgpa(
        self,
        performance_history: List[Dict[str, Any]]
    ) -> float:
        """Predict next semester SGPA using time series"""
        sgpas = [p['sgpa'] for p in performance_history]
        
        if len(sgpas) < 2:
            return sgpas[0] if sgpas else 7.0
        
        # Polynomial regression
        x = np.arange(len(sgpas))
        degree = min(2, len(sgpas) - 1)
        coefficients = np.polyfit(x, sgpas, degree)
        poly = np.poly1d(coefficients)
        
        # Predict next value
        next_sgpa = poly(len(sgpas))
        
        # Bound between 0-10
        return max(0, min(10, float(next_sgpa)))
    
    async def _calculate_risk_score(
        self,
        student_data: Dict[str, Any],
        performance_history: List[Dict[str, Any]]
    ) -> float:
        """Calculate comprehensive risk score"""
        risk_score = 0.0
        
        # CGPA-based risk
        cgpa = student_data.get('cgpa', 0)
        if cgpa < 5.5:
            risk_score += 40
        elif cgpa < 6.5:
            risk_score += 25
        elif cgpa < 7.5:
            risk_score += 10
        
        # Attendance risk
        attendance = student_data.get('attendance', 100)
        if attendance < 70:
            risk_score += 30
        elif attendance < 80:
            risk_score += 15
        
        # Trend analysis
        if performance_history and len(performance_history) > 1:
            sgpas = [p['sgpa'] for p in performance_history]
            recent_trend = sgpas[-1] - sgpas[-2]
            
            if recent_trend < -0.5:
                risk_score += 20
            elif recent_trend < 0:
                risk_score += 10
        
        # Failure risk
        if performance_history:
            failed_subjects = sum(
                len([s for s in sem.get('subjects', []) if s.get('grade') == 'F'])
                for sem in performance_history
            )
            risk_score += min(failed_subjects * 5, 20)
        
        return min(risk_score, 100)
    
    def _classify_risk_level(self, risk_score: float) -> str:
        """Classify risk level from score"""
        if risk_score >= 70:
            return 'critical'
        elif risk_score >= 50:
            return 'high'
        elif risk_score >= 30:
            return 'medium'
        else:
            return 'low'
    
    async def _calculate_success_probability(
        self,
        student_data: Dict[str, Any],
        performance_history: List[Dict[str, Any]]
    ) -> float:
        """Calculate probability of academic success"""
        factors = []
        
        # CGPA factor
        cgpa = student_data.get('cgpa', 0)
        cgpa_factor = min(cgpa / 10.0, 1.0)
        factors.append(cgpa_factor)
        
        # Attendance factor
        attendance = student_data.get('attendance', 0)
        attendance_factor = min(attendance / 100.0, 1.0)
        factors.append(attendance_factor)
        
        # Trend factor
        if performance_history and len(performance_history) > 1:
            sgpas = [p['sgpa'] for p in performance_history]
            trend = sgpas[-1] - sgpas[0]
            trend_factor = max(0, min((trend + 2) / 4, 1.0))
            factors.append(trend_factor)
        
        # Weighted average
        if factors:
            success_prob = np.mean(factors)
            return float(success_prob)
        
        return 0.5
    
    def _calculate_confidence(
        self,
        performance_history: List[Dict[str, Any]]
    ) -> float:
        """Calculate prediction confidence"""
        if not performance_history:
            return 0.3
        
        # Base confidence on data points
        data_points = len(performance_history)
        confidence = min(0.5 + (data_points * 0.05), 0.95)
        
        # Adjust for data recency
        if performance_history:
            latest = performance_history[-1]
            if 'created_at' in latest:
                try:
                    created_at = datetime.fromisoformat(latest['created_at'].replace('Z', '+00:00'))
                    days_old = (datetime.utcnow() - created_at).days
                    
                    if days_old < 30:
                        confidence += 0.1
                    elif days_old > 180:
                        confidence -= 0.1
                except:
                    pass
        
        return min(max(confidence, 0.1), 0.95)
    
    async def _identify_patterns(
        self,
        performance_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Identify performance patterns"""
        patterns = {}
        
        if not performance_history:
            return patterns
        
        sgpas = [p['sgpa'] for p in performance_history]
        
        # Trend detection
        if len(sgpas) > 1:
            trend_coef = np.polyfit(range(len(sgpas)), sgpas, 1)[0]
            
            if trend_coef > 0.2:
                patterns['overall_trend'] = 'strongly_improving'
            elif trend_coef > 0:
                patterns['overall_trend'] = 'improving'
            elif trend_coef < -0.2:
                patterns['overall_trend'] = 'strongly_declining'
            elif trend_coef < 0:
                patterns['overall_trend'] = 'declining'
            else:
                patterns['overall_trend'] = 'stable'
        
        # Volatility
        if len(sgpas) > 1:
            volatility = np.std(sgpas)
            if volatility > 1.0:
                patterns['consistency'] = 'highly_variable'
            elif volatility > 0.5:
                patterns['consistency'] = 'somewhat_variable'
            else:
                patterns['consistency'] = 'consistent'
        
        # Recent performance
        if len(sgpas) >= 3:
            recent_avg = np.mean(sgpas[-3:])
            overall_avg = np.mean(sgpas)
            
            if recent_avg > overall_avg + 0.5:
                patterns['recent_performance'] = 'above_average'
            elif recent_avg < overall_avg - 0.5:
                patterns['recent_performance'] = 'below_average'
            else:
                patterns['recent_performance'] = 'on_par'
        
        return patterns
    
    async def _generate_performance_insights(
        self,
        student_data: Dict[str, Any],
        predictions: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable performance insights"""
        insights = []
        
        # Risk-based insights
        risk_level = predictions.get('risk_level', 'low')
        
        if risk_level == 'critical':
            insights.append("⚠️ Critical: Immediate intervention required to improve academic standing")
            insights.append("Schedule meeting with academic advisor and course coordinators")
        elif risk_level == 'high':
            insights.append("⚠️ High risk detected. Focus on weak subjects and improve attendance")
        elif risk_level == 'medium':
            insights.append("⚡ Moderate risk. Maintain consistent study habits and seek help when needed")
        else:
            insights.append("✅ Good academic standing. Continue current approach")
        
        # SGPA prediction insights
        predicted_sgpa = predictions.get('predicted_sgpa', 0)
        current_cgpa = student_data.get('cgpa', 0)
        
        if predicted_sgpa > current_cgpa + 0.5:
            insights.append(f"📈 Predicted improvement: Next semester SGPA likely {predicted_sgpa:.2f}")
        elif predicted_sgpa < current_cgpa - 0.5:
            insights.append(f"📉 Warning: Predicted decline to {predicted_sgpa:.2f}. Take corrective action")
        
        # Pattern-based insights
        patterns = predictions.get('patterns', {})
        
        if patterns.get('overall_trend') == 'improving':
            insights.append("🎯 Excellent progress! Maintain your current study strategy")
        elif patterns.get('overall_trend') == 'declining':
            insights.append("⚠️ Declining trend detected. Review study methods and seek guidance")
        
        if patterns.get('consistency') == 'highly_variable':
            insights.append("📊 Performance is inconsistent. Work on establishing regular study habits")
        
        return insights
    
    async def _analyze_subjects(
        self,
        performance_history: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze subject-wise performance"""
        subject_data = {}
        
        for perf in performance_history:
            for subject in perf.get('subjects', []):
                subject_name = subject.get('subject_name') or subject.get('name')
                score = subject.get('total_marks') or subject.get('score', 0)
                
                if subject_name not in subject_data:
                    subject_data[subject_name] = {
                        'scores': [],
                        'credits': subject.get('credits', 3),
                        'grades': []
                    }
                
                subject_data[subject_name]['scores'].append(score)
                subject_data[subject_name]['grades'].append(subject.get('grade', ''))
        
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
                'credits': data['credits'],
                'failure_count': data['grades'].count('F')
            }
        
        return analysis
    
    async def _classify_severity(
        self,
        metrics: Dict[str, Any]
    ) -> str:
        """Classify weakness severity"""
        avg = metrics['average']
        failure_count = metrics.get('failure_count', 0)
        
        if avg < 35 or failure_count >= 2:
            return 'critical'
        elif avg < 50 or failure_count >= 1:
            return 'high'
        elif avg < 60:
            return 'medium'
        else:
            return 'low'
    
    async def _identify_weak_topics(
        self,
        subject: str,
        assessments: List[Dict[str, Any]],
        student_data: Dict[str, Any],
        curriculum_data: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Identify specific weak topics"""
        weak_topics = []
        
        # Analyze assessments for topic-level performance
        for assessment in assessments:
            if assessment.get('subject') == subject:
                for topic in assessment.get('topics', []):
                    if topic.get('score', 0) < 50:
                        weak_topics.append(topic.get('name'))
        
        # If no specific data, use curriculum-based topics
        if not weak_topics and curriculum_data:
            # Map common subjects to key topics
            topic_map = {
                'Mathematics': ['Calculus', 'Linear Algebra', 'Probability'],
                'Programming': ['Data Structures', 'Algorithms', 'OOP'],
                'Physics': ['Mechanics', 'Thermodynamics', 'Electromagnetics'],
                'Data Structures': ['Trees', 'Graphs', 'Hashing'],
                'DBMS': ['Normalization', 'SQL', 'Transactions'],
                'Operating System': ['Process Management', 'Memory Management', 'File Systems']
            }
            
            for key, topics in topic_map.items():
                if key.lower() in subject.lower():
                    weak_topics = topics[:2]
                    break
        
        return weak_topics[:5]  # Return top 5
    
    async def _generate_improvement_plan(
        self,
        subject: str,
        severity: str,
        weak_topics: List[str],
        curriculum_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate personalized improvement plan"""
        
        # Duration based on severity
        duration_map = {
            'critical': '6 weeks',
            'high': '4 weeks',
            'medium': '3 weeks',
            'low': '2 weeks'
        }
        
        # Daily hours based on severity
        hours_map = {
            'critical': 3,
            'high': 2,
            'medium': 1.5,
            'low': 1
        }
        
        duration = duration_map.get(severity, '4 weeks')
        daily_hours = hours_map.get(severity, 2)
        weeks = int(duration.split()[0])
        
        plan = {
            'duration': duration,
            'daily_hours': daily_hours,
            'focus_areas': weak_topics,
            'milestones': [],
            'recommended_approach': []
        }
        
        # Create weekly milestones
        for week in range(1, weeks + 1):
            milestone = {
                'week': week,
                'goals': [
                    f"Complete {subject} chapter {week}",
                    f"Solve {20 + (week * 5)} practice problems",
                    "Take mock assessment" if week == weeks else "Complete weekly quiz"
                ],
                'target_improvement': 10 * week,
                'focus_topics': weak_topics[:2] if weak_topics else []
            }
            plan['milestones'].append(milestone)
        
        # Recommended approach
        if severity in ['critical', 'high']:
            plan['recommended_approach'] = [
                "Attend all lectures and take detailed notes",
                "Schedule one-on-one sessions with professor",
                "Form study group with high-performing peers",
                "Use online resources and video tutorials",
                "Practice daily for at least 2 hours"
            ]
        else:
            plan['recommended_approach'] = [
                "Review lecture notes regularly",
                "Complete all practice problems",
                "Attend doubt-clearing sessions",
                "Use reference books for deeper understanding"
            ]
        
        return plan
    
    async def _get_curriculum_resources(
        self,
        subject: str,
        severity: str,
        curriculum_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get curriculum-aligned learning resources"""
        resources = []
        
        # YouTube videos
        resources.append({
            'type': 'video',
            'platform': 'YouTube',
            'title': f'{subject} Complete Course',
            'url': f'https://youtube.com/results?search_query={subject.replace(" ", "+")}+tutorial',
            'duration': '10-15 hours',
            'priority': 'high' if severity in ['critical', 'high'] else 'medium'
        })
        
        # NPTEL courses (India-specific)
        resources.append({
            'type': 'course',
            'platform': 'NPTEL',
            'title': f'{subject} - IIT Course',
            'url': f'https://nptel.ac.in/courses',
            'duration': '8 weeks',
            'priority': 'high'
        })
        
        # Practice platforms
        if any(term in subject.lower() for term in ['programming', 'data structures', 'algorithms']):
            resources.append({
                'type': 'practice',
                'platform': 'LeetCode',
                'title': f'{subject} Practice Problems',
                'url': 'https://leetcode.com/problemset/all/',
                'priority': 'critical' if severity == 'critical' else 'high'
            })
            
            resources.append({
                'type': 'practice',
                'platform': 'HackerRank',
                'title': f'{subject} Challenges',
                'url': 'https://www.hackerrank.com/',
                'priority': 'medium'
            })
        
        # Textbooks
        resources.append({
            'type': 'book',
            'platform': 'Reference',
            'title': f'Standard textbook for {subject}',
            'url': 'Library/Online',
            'priority': 'medium'
        })
        
        return resources
    
    async def _generate_curriculum_insights(
        self,
        student_data: Dict[str, Any],
        predictions: Dict[str, Any],
        curriculum_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate curriculum-specific insights"""
        insights = {
            'curriculum_type': curriculum_data.get('curriculum_type', 'Unknown'),
            'semester': curriculum_data.get('semester', student_data.get('current_semester', 1)),
            'recommendations': []
        }
        
        # Elective recommendations
        if curriculum_data.get('elective_groups'):
            insights['elective_available'] = True
            insights['recommendations'].append(
                "Elective selection available. Choose based on career goals and strengths"
            )
        
        # Honours/Minor eligibility
        current_semester = student_data.get('current_semester', 1)
        cgpa = student_data.get('cgpa', 0)
        
        if current_semester >= 4 and cgpa >= 7.5:
            insights['honours_eligible'] = True
            insights['recommendations'].append(
                "✨ Eligible for Honours/Minor programs! Apply before semester 5 registration"
            )
        elif current_semester >= 4:
            gap = 7.5 - cgpa
            insights['recommendations'].append(
                f"Improve CGPA by {gap:.2f} to become eligible for Honours/Minor programs"
            )
        
        return insights
    
    async def _analyze_curriculum_progress(
        self,
        student_data: Dict[str, Any],
        performance_history: List[Dict[str, Any]],
        curriculum_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze progress through curriculum"""
        
        completed_credits = sum(
            sem.get('credits_earned', 0) 
            for sem in performance_history
        )
        
        total_required = 160  # Standard B.Tech credits
        
        progress = {
            'completed_credits': completed_credits,
            'total_required': total_required,
            'percentage': (completed_credits / total_required) * 100,
            'on_track': True,
            'projected_graduation': None
        }
        
        # Calculate if on track
        current_semester = student_data.get('current_semester', 1)
        expected_credits = (current_semester - 1) * 20  # ~20 credits per semester
        
        if completed_credits < expected_credits * 0.9:
            progress['on_track'] = False
            progress['credit_deficit'] = expected_credits - completed_credits
        
        # Project graduation semester
        if completed_credits > 0:
            avg_credits_per_sem = completed_credits / current_semester
            remaining_credits = total_required - completed_credits
            semesters_remaining = np.ceil(remaining_credits / avg_credits_per_sem)
            
            progress['projected_graduation_semester'] = int(current_semester + semesters_remaining)
        
        return progress
    
    async def _recommend_electives(
        self,
        student_data: Dict[str, Any],
        weaknesses: List[Dict[str, Any]],
        curriculum_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Recommend electives based on performance and career goals"""
        
        recommendations = []
        
        # Get available electives from curriculum
        branch = student_data.get('branch', 'IT')
        semester = student_data.get('current_semester', 5)
        
        # Get elective options
        elective_groups = curriculum_data.get('elective_groups', {})
        
        for group_name, group_data in elective_groups.items():
            options = group_data.get('options', [])
            
            for option in options:
                # Calculate match score based on weaknesses and strengths
                match_score = 70  # Base score
                
                # Adjust based on related subjects
                # This would need more sophisticated logic in production
                
                recommendation = {
                    'elective_code': option['code'],
                    'elective_name': option['name'],
                    'group': group_name,
                    'match_score': match_score,
                    'reasons': [
                        "Aligns with your strengths",
                        "High industry demand",
                        "Builds on previous coursework"
                    ],
                    'career_relevance': "High"
                }
                
                recommendations.append(recommendation)
        
        # Sort by match score
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        return recommendations[:3]  # Top 3 recommendations
    
    def _is_cache_valid(
        self,
        cached_data: Dict[str, Any]
    ) -> bool:
        """Check if cached data is still valid"""
        if 'expires_at' in cached_data:
            try:
                expiry = datetime.fromisoformat(cached_data['expires_at'].replace('Z', '+00:00'))
                return datetime.utcnow() < expiry
            except:
                return False
        return False
    
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
            'moving_average': [float(x) if not np.isnan(x) else 0 for x in moving_avg],
            'volatility': float(np.std(sgpas)) if len(sgpas) > 1 else 0,
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
        
        for perf in performance_history:
            sgpas.append(perf.get('sgpa', 0))
            attendance.append(perf.get('attendance', 0))
        
        correlations = {}
        
        # Calculate correlations
        if len(set(attendance)) > 1:  # Check for variance
            try:
                corr = np.corrcoef(attendance, sgpas)[0, 1]
                correlations['attendance_sgpa'] = float(corr) if not np.isnan(corr) else 0.0
            except:
                correlations['attendance_sgpa'] = 0.0
        
        return correlations
    
    async def _generate_future_predictions(
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
        degree = min(2, len(sgpas) - 1)
        coefficients = np.polyfit(x, sgpas, degree)
        poly = np.poly1d(coefficients)
        
        # Predict next semester
        next_sem_prediction = poly(len(sgpas))
        next_sem_prediction = max(0, min(10, float(next_sem_prediction)))
        
        predictions['next_semester_sgpa'] = next_sem_prediction
        
        # Graduation CGPA prediction
        remaining_semesters = 8 - student_data.get('current_semester', 1)
        if remaining_semesters > 0:
            future_predictions = []
            for i in range(remaining_semesters):
                pred = poly(len(sgpas) + i)
                pred = max(0, min(10, float(pred)))
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
                        'sgpa': float(sgpa),
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
                is_practical = subject.get('is_practical', False)
                score = subject.get('total_marks') or subject.get('score', 0)
                
                if is_practical:
                    practical_scores.append(score)
                else:
                    theory_scores.append(score)
        
        if theory_scores and practical_scores:
            theory_avg = np.mean(theory_scores)
            practical_avg = np.mean(practical_scores)
            
            if practical_avg > theory_avg + 10:
                style['type'] = 'practical_learner'
                style['strengths'] = ['hands-on learning', 'project work', 'laboratory experiments']
            elif theory_avg > practical_avg + 10:
                style['type'] = 'theoretical_learner'
                style['strengths'] = ['conceptual understanding', 'analytical thinking', 'problem-solving']
            else:
                style['type'] = 'balanced_learner'
                style['strengths'] = ['versatile', 'adaptable', 'comprehensive understanding']
        
        # Add preferences based on performance
        attendance = student_data.get('attendance', 0)
        if attendance > 90:
            style['preferences'].append('regular_classes')
        
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
        report_parts.append(f"Curriculum Type: {analysis.get('curriculum_type', 'Unknown')}")
        report_parts.append("")
        
        # Trends
        if 'trends' in analysis:
            report_parts.append("### Performance Trends")
            report_parts.append(f"- Overall trend: {analysis['trends'].get('trend', 'N/A')}")
            report_parts.append(f"- Volatility: {analysis['trends'].get('volatility', 0):.2f}")
            report_parts.append(f"- Current position: {analysis['trends'].get('current_position', 'N/A')}")
            report_parts.append("")
        
        # Predictions
        if 'predictions' in analysis:
            report_parts.append("### Future Predictions")
            pred = analysis['predictions']
            if 'next_semester_sgpa' in pred:
                report_parts.append(f"- Next semester SGPA: {pred['next_semester_sgpa']:.2f}")
            if 'expected_graduation_cgpa' in pred:
                report_parts.append(f"- Expected graduation CGPA: {pred['expected_graduation_cgpa']:.2f}")
            if 'failure_risk_percentage' in pred:
                report_parts.append(f"- Failure risk: {pred['failure_risk_percentage']:.0f}%")
            report_parts.append("")
        
        # Curriculum progress
        if 'curriculum_progress' in analysis:
            progress = analysis['curriculum_progress']
            report_parts.append("### Curriculum Progress")
            report_parts.append(f"- Completed credits: {progress.get('completed_credits', 0)}/{progress.get('total_required', 160)}")
            report_parts.append(f"- Progress: {progress.get('percentage', 0):.1f}%")
            report_parts.append(f"- On track: {'Yes' if progress.get('on_track', False) else 'No'}")
            report_parts.append("")
        
        # Anomalies
        if 'anomalies' in analysis and analysis['anomalies']:
            report_parts.append("### Detected Anomalies")
            for anomaly in analysis['anomalies']:
                report_parts.append(f"- Semester {anomaly['semester']}: {anomaly['type']} (Severity: {anomaly['severity']})")
            report_parts.append("")
        
        # Learning style
        if 'learning_style' in analysis:
            style = analysis['learning_style']
            report_parts.append("### Learning Style Analysis")
            report_parts.append(f"- Type: {style.get('type', 'Unknown')}")
            if style.get('strengths'):
                report_parts.append(f"- Strengths: {', '.join(style['strengths'])}")
            report_parts.append("")
        
        # Elective recommendations
        if 'elective_recommendations' in analysis and analysis['elective_recommendations']:
            report_parts.append("### Recommended Electives")
            for rec in analysis['elective_recommendations'][:3]:
                report_parts.append(f"- {rec['elective_name']} (Match: {rec['match_score']}%)")
            report_parts.append("")
        
        return "\n".join(report_parts)
    
    # ==================== UTILITY METHODS ====================
    
    async def quick_predict(
        self,
        student_data: Dict[str, Any],
        performance_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Quick prediction for bulk processing"""
        try:
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


# Global instance
ml_analyzer = MLPerformanceAnalyzer()


# Module-level functions
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