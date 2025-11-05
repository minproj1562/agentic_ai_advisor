# app/ml/models/weakness_detector.py
"""
Weakness Detection ML Model
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
import lightgbm as lgb
from typing import Dict, List, Any

from app.utils.helpers import get_logger

logger = get_logger(__name__)


class WeaknessDetector:
    """
    ML model for detecting academic weaknesses
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.subjects = [
            'Mathematics', 'Programming', 'Data Structures',
            'Algorithms', 'Database', 'Networks', 'Operating Systems'
        ]
        self.severity_levels = ['none', 'low', 'medium', 'high', 'critical']
        
    def train(
        self,
        training_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Train weakness detection model
        """
        try:
            # Prepare features
            feature_columns = [
                'subject_score', 'attendance', 'assignment_score',
                'quiz_average', 'lab_performance', 'previous_score',
                'study_hours', 'difficulty_rating'
            ]
            
            X = training_data[feature_columns]
            
            # Prepare targets (multi-label classification)
            y = training_data[['weakness_severity', 'needs_intervention']]
            
            # Encode labels
            for col in y.columns:
                le = LabelEncoder()
                y[col] = le.fit_transform(y[col])
                self.label_encoders[col] = le
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Create and train model
            base_model = lgb.LGBMClassifier(
                n_estimators=150,
                max_depth=6,
                learning_rate=0.1,
                num_leaves=31,
                random_state=42
            )
            
            self.model = MultiOutputClassifier(base_model)
            self.model.fit(X_scaled, y)
            
            # Evaluate
            train_score = self.model.score(X_scaled, y)
            
            logger.info(f"Weakness detector trained. Accuracy: {train_score:.3f}")
            
            return {
                'accuracy': train_score,
                'subjects_covered': len(self.subjects),
                'severity_levels': self.severity_levels
            }
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            raise
    
    def detect_weaknesses(
        self,
        student_performance: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect weaknesses for a student
        """
        try:
            weaknesses = []
            
            for subject in self.subjects:
                # Get subject data
                subject_data = student_performance.get(subject, {})
                
                if not subject_data:
                    continue
                
                # Check for weakness indicators
                weakness = self._analyze_subject(subject, subject_data)
                
                if weakness['severity'] != 'none':
                    weaknesses.append(weakness)
            
            # Sort by severity and confidence
            weaknesses.sort(
                key=lambda x: (
                    self.severity_levels.index(x['severity']),
                    -x['confidence']
                ),
                reverse=True
            )
            
            return weaknesses
            
        except Exception as e:
            logger.error(f"Weakness detection failed: {str(e)}")
            return []
    
    def _analyze_subject(
        self,
        subject: str,
        subject_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a specific subject for weaknesses
        """
        score = subject_data.get('score', 0)
        attendance = subject_data.get('attendance', 0)
        assignments = subject_data.get('assignment_completion', 0)
        
        # Determine severity
        severity = 'none'
        confidence = 0.0
        
        if score < 35:
            severity = 'critical'
            confidence = 0.95
        elif score < 50:
            severity = 'high'
            confidence = 0.85
        elif score < 60:
            severity = 'medium'
            confidence = 0.75
        elif score < 70:
            severity = 'low'
            confidence = 0.65
        
        # Adjust based on other factors
        if attendance < 60:
            if severity == 'none':
                severity = 'low'
            confidence = min(confidence + 0.1, 0.95)
        
        if assignments < 50:
            if severity in ['none', 'low']:
                severity = 'medium'
            confidence = min(confidence + 0.05, 0.95)
        
        # Identify specific weak topics
        weak_topics = self._identify_weak_topics(subject, subject_data)
        
        # Generate improvement suggestions
        suggestions = self._generate_suggestions(subject, severity, weak_topics)
        
        return {
            'subject': subject,
            'severity': severity,
            'score': score,
            'gap': max(0, 60 - score),  # Gap from passing score
            'confidence': confidence,
            'weak_topics': weak_topics,
            'suggestions': suggestions,
            'factors': {
                'low_score': score < 60,
                'poor_attendance': attendance < 75,
                'incomplete_assignments': assignments < 80
            }
        }
    
    def _identify_weak_topics(
        self,
        subject: str,
        subject_data: Dict[str, Any]
    ) -> List[str]:
        """
        Identify specific weak topics within a subject
        """
        weak_topics = []
        
        # Get topic scores if available
        topic_scores = subject_data.get('topic_scores', {})
        
        for topic, score in topic_scores.items():
            if score < 50:
                weak_topics.append(topic)
        
        # If no specific data, use general topics
        if not weak_topics:
            topic_map = {
                'Mathematics': ['Calculus', 'Linear Algebra', 'Statistics'],
                'Programming': ['Syntax', 'Logic Building', 'Problem Solving'],
                'Data Structures': ['Arrays', 'Linked Lists', 'Trees', 'Graphs'],
                'Algorithms': ['Sorting', 'Searching', 'Dynamic Programming'],
                'Database': ['SQL', 'Normalization', 'Transactions'],
                'Networks': ['TCP/IP', 'Routing', 'Security'],
                'Operating Systems': ['Process Management', 'Memory', 'File Systems']
            }
            
            if subject in topic_map and subject_data.get('score', 100) < 60:
                weak_topics = topic_map[subject][:2]
        
        return weak_topics
    
    def _generate_suggestions(
        self,
        subject: str,
        severity: str,
        weak_topics: List[str]
    ) -> List[str]:
        """
        Generate improvement suggestions
        """
        suggestions = []
        
        # Severity-based suggestions
        if severity == 'critical':
            suggestions.extend([
                f"Urgent: Schedule immediate consultation with {subject} faculty",
                "Join intensive tutoring sessions",
                "Dedicate minimum 3 hours daily for this subject"
            ])
        elif severity == 'high':
            suggestions.extend([
                f"Priority: Focus on {subject} improvement",
                "Form or join a study group",
                "Complete all practice problems"
            ])
        elif severity == 'medium':
            suggestions.extend([
                "Review fundamental concepts",
                "Solve previous year papers",
                "Attend all classes without fail"
            ])
        else:
            suggestions.extend([
                "Maintain consistent practice",
                "Aim for higher scores"
            ])
        
        # Topic-specific suggestions
        if weak_topics:
            suggestions.append(
                f"Focus on: {', '.join(weak_topics[:3])}"
            )
        
        return suggestions
    
    def get_intervention_recommendations(
        self,
        weaknesses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Get intervention recommendations based on weaknesses
        """
        interventions = []
        
        # Count severity levels
        severity_counts = defaultdict(int)
        for w in weaknesses:
            severity_counts[w['severity']] += 1
        
        # Critical interventions
        if severity_counts['critical'] > 0:
            interventions.append({
                'type': 'urgent',
                'action': 'Immediate faculty intervention required',
                'subjects': [w['subject'] for w in weaknesses if w['severity'] == 'critical'],
                'timeline': 'within 24 hours'
            })
        
        # High severity interventions
        if severity_counts['high'] > 1:
            interventions.append({
                'type': 'high_priority',
                'action': 'Enrollment in remedial classes recommended',
                'subjects': [w['subject'] for w in weaknesses if w['severity'] == 'high'],
                'timeline': 'within 1 week'
            })
        
        # General interventions
        if len(weaknesses) > 3:
            interventions.append({
                'type': 'comprehensive',
                'action': 'Complete academic performance review needed',
                'timeline': 'within 2 weeks'
            })
        
        return interventions