# app/ml/weakness_predictor.py
"""
Enhanced Weakness Predictor with ML capabilities
Integrates with interests, electives, and academic performance
"""

from typing import List, Dict, Any, Tuple, Optional
import logging
import numpy as np
from datetime import datetime

from app.models.weakness import (
    WeaknessArea,
    SeverityLevel,
    AnalysisBasis
)

logger = logging.getLogger(__name__)


class WeaknessAnalyzer:
    """
    ML-powered weakness analysis engine.
    Combines rule-based logic with statistical analysis.
    """
    
    def __init__(self):
        self.logger = logger
        
        # Thresholds for weakness detection
        self.weakness_thresholds = {
            'critical': 40,
            'high': 55,
            'medium': 65,
            'low': 75
        }
        
        # Subject difficulty weights (higher = harder)
        self.subject_difficulty = {
            'Mathematics': 0.9,
            'Linear Algebra': 0.85,
            'Calculus': 0.85,
            'Statistics': 0.8,
            'Probability': 0.8,
            'Data Structures': 0.75,
            'Algorithms': 0.8,
            'Operating System': 0.7,
            'Database Management': 0.65,
            'Computer Networks': 0.7,
            'Python': 0.5,
            'Java': 0.6,
            'C Programming': 0.6,
            'Web Development': 0.55,
            'Machine Learning': 0.85,
            'Artificial Intelligence': 0.85,
            'Cryptography': 0.8,
            'Distributed Systems': 0.75
        }
        
        # Interest to subject relevance mapping with weights
        self.interest_subject_weights = {
            'Machine Learning': {
                'Mathematics': 1.0,
                'Statistics': 0.95,
                'Python': 0.9,
                'Linear Algebra': 0.85,
                'Calculus': 0.7,
                'Data Structures': 0.75
            },
            'Data Science': {
                'Statistics': 1.0,
                'Python': 0.95,
                'Database Management': 0.85,
                'Mathematics': 0.8
            },
            'Web Development': {
                'JavaScript': 0.95,
                'Database Management': 0.8,
                'Python': 0.7,
                'HTML/CSS': 0.9
            },
            'Cloud Computing': {
                'Operating System': 0.9,
                'Computer Networks': 0.95,
                'Linux': 0.85,
                'Database Management': 0.7
            },
            'Cybersecurity': {
                'Computer Networks': 1.0,
                'Operating System': 0.9,
                'Cryptography': 0.95,
                'Linux': 0.8
            }
        }

    def analyze_topic_weakness(
        self, 
        topic_scores: Dict[str, float], 
        overall_score: float,
        exam_weights: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Analyze topic-level weaknesses for a subject.
        
        Args:
            topic_scores: Dictionary of topic names to scores
            overall_score: Overall subject score
            exam_weights: Weight of each topic in exam
            
        Returns:
            List of weakness dictionaries
        """
        weaknesses = []
        
        for topic, score in topic_scores.items():
            weight = exam_weights.get(topic, 0.1)
            weighted_score = score * weight
            
            # Calculate weakness level
            if weighted_score < self.weakness_thresholds['critical']:
                level = 'critical'
            elif weighted_score < self.weakness_thresholds['high']:
                level = 'high'
            elif weighted_score < self.weakness_thresholds['medium']:
                level = 'medium'
            elif weighted_score < self.weakness_thresholds['low']:
                level = 'low'
            else:
                continue  # Not a weakness
            
            weakness = {
                'topic_name': topic,
                'score': score,
                'weight': weight,
                'weighted_score': weighted_score,
                'weakness_level': level,
                'improvement_suggestions': self._generate_suggestions(topic, level),
                'recommended_resources': self._suggest_resources(topic, level),
                'practice_exercises': self._generate_practice_exercises(topic, level),
                'estimated_hours': self._estimate_study_hours(score, weight)
            }
            weaknesses.append(weakness)
        
        # Sort by severity (critical first)
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        weaknesses.sort(key=lambda x: severity_order.get(x['weakness_level'], 4))
        
        return weaknesses

    def analyze_interest_gap(
        self,
        student_scores: Dict[str, float],
        interests: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Analyze gaps between student's interests and their performance
        in relevant subjects.
        
        Args:
            student_scores: Dictionary of subject names to scores
            interests: List of student interests
            
        Returns:
            List of gap analysis results
        """
        gaps = []
        
        for interest in interests:
            if interest not in self.interest_subject_weights:
                continue
            
            required_subjects = self.interest_subject_weights[interest]
            interest_gaps = []
            
            for subject, importance in required_subjects.items():
                student_score = self._find_matching_score(student_scores, subject)
                
                if student_score is None:
                    # Subject not taken
                    interest_gaps.append({
                        'subject': subject,
                        'importance': importance,
                        'current_score': 0,
                        'target_score': 70,
                        'gap': 70,
                        'status': 'not_taken',
                        'impact': 'high' if importance >= 0.8 else 'medium'
                    })
                elif student_score < 60:
                    # Significant weakness
                    target = 75 if importance >= 0.8 else 65
                    interest_gaps.append({
                        'subject': subject,
                        'importance': importance,
                        'current_score': student_score,
                        'target_score': target,
                        'gap': target - student_score,
                        'status': 'weak',
                        'impact': 'high' if importance >= 0.8 else 'medium'
                    })
                elif student_score < 75 and importance >= 0.8:
                    # Moderate gap in important subject
                    interest_gaps.append({
                        'subject': subject,
                        'importance': importance,
                        'current_score': student_score,
                        'target_score': 80,
                        'gap': 80 - student_score,
                        'status': 'needs_improvement',
                        'impact': 'medium'
                    })
            
            if interest_gaps:
                # Calculate overall readiness for this interest
                readiness = self._calculate_interest_readiness(
                    interest_gaps, 
                    required_subjects
                )
                
                gaps.append({
                    'interest': interest,
                    'subject_gaps': interest_gaps,
                    'total_gaps': len(interest_gaps),
                    'readiness_score': readiness,
                    'recommendation': self._get_interest_recommendation(readiness, interest)
                })
        
        return gaps

    def analyze_elective_readiness(
        self,
        student_scores: Dict[str, float],
        elective: str,
        prerequisites: Dict[str, Tuple[float, str]]
    ) -> Dict[str, Any]:
        """
        Analyze student's readiness for a specific elective.
        
        Args:
            student_scores: Dictionary of subject names to scores
            elective: Name of the elective
            prerequisites: Dict of prereq subject to (weight, importance)
            
        Returns:
            Readiness analysis dictionary
        """
        gaps = []
        ready_subjects = []
        total_weight = 0
        achieved_weight = 0
        
        for prereq, (weight, importance) in prerequisites.items():
            student_score = self._find_matching_score(student_scores, prereq)
            threshold = 70 if importance == "Critical" else 60 if importance == "High" else 50
            
            total_weight += weight
            
            if student_score is None:
                gaps.append({
                    'subject': prereq,
                    'importance': importance,
                    'weight': weight,
                    'current_score': 0,
                    'required_score': threshold,
                    'gap': threshold,
                    'status': 'not_taken'
                })
            elif student_score < threshold:
                achieved_weight += (student_score / threshold) * weight
                gaps.append({
                    'subject': prereq,
                    'importance': importance,
                    'weight': weight,
                    'current_score': student_score,
                    'required_score': threshold,
                    'gap': threshold - student_score,
                    'status': 'below_threshold'
                })
            else:
                achieved_weight += weight
                ready_subjects.append({
                    'subject': prereq,
                    'score': student_score,
                    'status': 'ready'
                })
        
        readiness_percentage = (achieved_weight / total_weight * 100) if total_weight > 0 else 0
        
        return {
            'elective': elective,
            'readiness_percentage': round(readiness_percentage, 1),
            'is_ready': readiness_percentage >= 70,
            'gaps': gaps,
            'ready_subjects': ready_subjects,
            'recommendation': self._get_elective_recommendation(readiness_percentage, gaps),
            'estimated_prep_time': self._estimate_prep_time(gaps)
        }

    def predict_weakness_impact(
        self,
        weaknesses: List[Dict[str, Any]],
        target_cgpa: float,
        current_cgpa: float
    ) -> Dict[str, Any]:
        """
        Predict the impact of weaknesses on academic goals.
        
        Args:
            weaknesses: List of weakness dictionaries
            target_cgpa: Student's target CGPA
            current_cgpa: Current CGPA
            
        Returns:
            Impact prediction dictionary
        """
        # Calculate total weakness impact
        total_impact = 0
        critical_subjects = []
        
        for w in weaknesses:
            severity_impact = {
                'critical': 0.4,
                'high': 0.25,
                'medium': 0.15,
                'low': 0.05
            }
            
            level = w.get('weakness_level', w.get('severity', 'medium'))
            impact = severity_impact.get(level, 0.1)
            weight = w.get('weight', 0.5)
            
            total_impact += impact * weight
            
            if level in ['critical', 'high']:
                critical_subjects.append(w.get('topic_name', w.get('subject', 'Unknown')))
        
        # Normalize impact
        normalized_impact = min(total_impact, 1.0)
        
        # Predict CGPA impact
        cgpa_gap = target_cgpa - current_cgpa
        predicted_achievement = current_cgpa + (cgpa_gap * (1 - normalized_impact * 0.5))
        
        # Calculate probability of reaching target
        if normalized_impact < 0.2:
            probability = 0.85
        elif normalized_impact < 0.4:
            probability = 0.65
        elif normalized_impact < 0.6:
            probability = 0.45
        else:
            probability = 0.25
        
        return {
            'current_cgpa': current_cgpa,
            'target_cgpa': target_cgpa,
            'predicted_cgpa': round(predicted_achievement, 2),
            'weakness_impact_score': round(normalized_impact * 100, 1),
            'probability_of_target': round(probability * 100, 1),
            'critical_subjects': critical_subjects,
            'risk_level': 'high' if normalized_impact > 0.5 else 'medium' if normalized_impact > 0.25 else 'low',
            'recommendation': self._get_impact_recommendation(normalized_impact, critical_subjects)
        }

    def generate_ai_analysis(
        self, 
        subject: str, 
        weakness_topics: List[Any],
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive AI-powered analysis.
        
        Args:
            subject: Subject name
            weakness_topics: List of weak topics
            performance_data: Student's performance data
            
        Returns:
            AI analysis dictionary
        """
        # Handle both dict and object types
        topics_list = []
        for topic in weakness_topics:
            if hasattr(topic, 'dict'):
                topics_list.append(topic.dict())
            elif isinstance(topic, dict):
                topics_list.append(topic)
            else:
                topics_list.append({
                    'topic_name': str(topic),
                    'weakness_level': 'medium',
                    'score': 50,
                    'weight': 0.5
                })
        
        # Calculate severity counts
        critical_count = sum(1 for t in topics_list if t.get('weakness_level') == 'critical')
        high_count = sum(1 for t in topics_list if t.get('weakness_level') == 'high')
        
        # Calculate overall weakness score
        total_score = sum(
            t.get('score', 50) * t.get('weight', 0.5)
            for t in topics_list
            if t.get('weakness_level') in ['critical', 'high']
        )
        
        # Generate insights
        insights = self._generate_insights(subject, topics_list, performance_data)
        
        # Create study plan
        study_plan = self._create_study_plan(topics_list, performance_data)
        
        # Predict improvement
        improvement = self._predict_improvement(topics_list, performance_data)
        
        # Get priority order
        priority_order = self._get_priority_order(topics_list)
        
        return {
            "subject": subject,
            "overall_weakness_score": round(total_score, 2),
            "critical_weaknesses": critical_count,
            "high_weaknesses": high_count,
            "total_weak_topics": len(topics_list),
            "insights": insights,
            "study_plan": study_plan,
            "predicted_improvement": improvement,
            "priority_order": priority_order,
            "confidence": 0.85,
            "generated_at": datetime.utcnow().isoformat()
        }

    # ============== Helper Methods ==============

    def _find_matching_score(
        self, 
        scores: Dict[str, float], 
        target: str
    ) -> Optional[float]:
        """Find score for a subject using fuzzy matching."""
        target_lower = target.lower()
        
        for subject, score in scores.items():
            subject_lower = subject.lower()
            if target_lower in subject_lower or subject_lower in target_lower:
                if isinstance(score, dict):
                    return score.get('score', 0)
                return score
        
        return None

    def _calculate_interest_readiness(
        self,
        gaps: List[Dict[str, Any]],
        required_subjects: Dict[str, float]
    ) -> float:
        """Calculate overall readiness for an interest area."""
        if not required_subjects:
            return 100.0
        
        total_weight = sum(required_subjects.values())
        achieved = 0
        
        gap_subjects = {g['subject'].lower(): g for g in gaps}
        
        for subject, weight in required_subjects.items():
            subject_lower = subject.lower()
            if subject_lower in gap_subjects:
                gap = gap_subjects[subject_lower]
                score = gap.get('current_score', 0)
                target = gap.get('target_score', 70)
                achieved += (score / target) * weight if target > 0 else 0
            else:
                # Subject not in gaps means student is ready
                achieved += weight
        
        return round((achieved / total_weight) * 100, 1) if total_weight > 0 else 0

    def _get_interest_recommendation(self, readiness: float, interest: str) -> str:
        """Get recommendation based on interest readiness."""
        if readiness >= 80:
            return f"Excellent! You're well-prepared to pursue {interest}."
        elif readiness >= 60:
            return f"Good foundation for {interest}. Focus on weak areas to excel."
        elif readiness >= 40:
            return f"Need significant improvement before pursuing {interest}."
        else:
            return f"Consider building foundational skills before focusing on {interest}."

    def _get_elective_recommendation(
        self, 
        readiness: float, 
        gaps: List[Dict[str, Any]]
    ) -> str:
        """Get recommendation for elective readiness."""
        critical_gaps = [g for g in gaps if g.get('importance') == 'Critical']
        
        if readiness >= 80:
            return "You're ready to take this elective."
        elif readiness >= 60:
            if critical_gaps:
                subjects = ", ".join([g['subject'] for g in critical_gaps[:2]])
                return f"Focus on {subjects} before enrolling."
            return "Minor preparation needed. You can proceed with extra effort."
        else:
            return "Significant preparation required. Consider next semester."

    def _estimate_prep_time(self, gaps: List[Dict[str, Any]]) -> str:
        """Estimate preparation time for gaps."""
        total_hours = 0
        
        for gap in gaps:
            gap_size = gap.get('gap', 0)
            importance = gap.get('importance', 'Medium')
            
            base_hours = gap_size * 0.5  # 0.5 hours per percentage point
            if importance == 'Critical':
                base_hours *= 1.5
            
            total_hours += base_hours
        
        if total_hours < 20:
            return "1-2 weeks"
        elif total_hours < 50:
            return "3-4 weeks"
        elif total_hours < 100:
            return "6-8 weeks"
        else:
            return "2-3 months"

    def _get_impact_recommendation(
        self, 
        impact: float, 
        critical_subjects: List[str]
    ) -> str:
        """Get recommendation based on weakness impact."""
        if impact < 0.2:
            return "Minor weaknesses. Maintain current study habits with slight adjustments."
        elif impact < 0.4:
            subjects = ", ".join(critical_subjects[:2]) if critical_subjects else "weak areas"
            return f"Moderate impact. Prioritize {subjects} for improvement."
        else:
            return "Significant impact on goals. Consider intensive remediation or tutoring."

    def _generate_suggestions(self, topic: str, level: str) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = {
            'critical': [
                f"Immediate focus required on {topic} fundamentals",
                "Schedule daily practice sessions (minimum 1 hour)",
                "Seek help from professor or tutor immediately",
                "Review all basic concepts before advancing"
            ],
            'high': [
                f"Dedicate extra study time to {topic}",
                "Practice more problems from this area",
                "Join study groups for collaborative learning",
                "Use video tutorials for concept clarity"
            ],
            'medium': [
                f"Regular revision of {topic} concepts",
                "Solve practice problems weekly",
                "Focus on understanding, not memorization"
            ],
            'low': [
                "Maintain current effort level",
                "Focus on advanced applications"
            ]
        }
        return suggestions.get(level, suggestions['medium'])

    def _suggest_resources(self, topic: str, level: str) -> List[Dict[str, str]]:
        """Suggest learning resources."""
        resources = []
        
        if level in ['critical', 'high']:
            resources.extend([
                {"type": "video", "title": f"{topic} Crash Course", "platform": "YouTube"},
                {"type": "course", "title": f"{topic} Fundamentals", "platform": "Coursera"},
                {"type": "practice", "title": f"{topic} Problem Set", "platform": "HackerRank"}
            ])
        else:
            resources.extend([
                {"type": "article", "title": f"Advanced {topic}", "platform": "Medium"},
                {"type": "practice", "title": f"{topic} Challenges", "platform": "LeetCode"}
            ])
        
        return resources

    def _generate_practice_exercises(self, topic: str, level: str) -> List[str]:
        """Generate practice exercise suggestions."""
        exercises = {
            'critical': [
                f"Basic {topic} concept questions",
                "Step-by-step guided problems",
                "Multiple choice practice tests"
            ],
            'high': [
                f"Intermediate {topic} problems",
                "Previous exam questions",
                "Timed practice sets"
            ],
            'medium': [
                f"Advanced {topic} challenges",
                "Real-world application problems"
            ],
            'low': [
                "Competitive-level problems"
            ]
        }
        return exercises.get(level, exercises['medium'])

    def _estimate_study_hours(self, score: float, weight: float) -> int:
        """Estimate hours needed to improve."""
        gap = max(0, 75 - score)
        base_hours = gap * 0.3  # 0.3 hours per point
        weighted_hours = base_hours * (1 + weight)
        return max(5, int(weighted_hours))

    def _generate_insights(
        self,
        subject: str,
        topics: List[Dict[str, Any]],
        performance_data: Dict[str, Any]
    ) -> List[str]:
        """Generate personalized insights."""
        insights = []
        
        critical = [t for t in topics if t.get('weakness_level') == 'critical']
        high = [t for t in topics if t.get('weakness_level') == 'high']
        
        if critical:
            topics_str = ", ".join([t.get('topic_name', 'topic') for t in critical[:2]])
            insights.append(
                f"Critical attention needed in {subject}: {topics_str}. "
                "Immediate action recommended."
            )
        
        if high:
            insights.append(
                f"{len(high)} high-priority areas identified in {subject}. "
                "Focused improvement can significantly boost performance."
            )
        
        cgpa = performance_data.get('overall_cgpa', performance_data.get('cgpa', 7.0))
        if cgpa < 7.0:
            insights.append(
                "Current CGPA suggests need for consistent improvement. "
                "Focus on strengthening fundamentals."
            )
        elif cgpa > 8.5:
            insights.append(
                "Strong academic foundation. Focus on advanced topics "
                "and practical applications."
            )
        
        if not insights:
            insights.append(f"Good performance in {subject}. Maintain current effort.")
        
        return insights

    def _create_study_plan(
        self,
        topics: List[Dict[str, Any]],
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create personalized study plan."""
        # Sort by priority
        sorted_topics = sorted(
            topics,
            key=lambda x: (
                0 if x.get('weakness_level') == 'critical' else
                1 if x.get('weakness_level') == 'high' else
                2 if x.get('weakness_level') == 'medium' else 3,
                -x.get('weight', 0.5)
            )
        )
        
        focus_areas = []
        for i, topic in enumerate(sorted_topics[:5]):
            focus_areas.append({
                "topic": topic.get('topic_name', 'Unknown'),
                "priority": i + 1,
                "current_score": topic.get('score', 50),
                "target_score": min(85, topic.get('score', 50) + 20),
                "weekly_hours": 3 if topic.get('weakness_level') in ['critical', 'high'] else 2
            })
        
        return {
            "duration": "8 weeks",
            "weekly_commitment": "15-20 hours",
            "focus_areas": focus_areas,
            "phases": [
                {"week": "1-2", "focus": "Fundamental concepts"},
                {"week": "3-5", "focus": "Practice and application"},
                {"week": "6-8", "focus": "Advanced problems and revision"}
            ],
            "milestones": [
                {"week": 2, "target": "Complete basics review"},
                {"week": 4, "target": "Score 60%+ in practice"},
                {"week": 6, "target": "Score 70%+ in practice"},
                {"week": 8, "target": "Achieve target proficiency"}
            ]
        }

    def _predict_improvement(
        self,
        topics: List[Dict[str, Any]],
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict potential improvement."""
        current_avg = np.mean([t.get('score', 50) for t in topics]) if topics else 70
        
        # Calculate improvement potential
        improvement_points = 0
        for topic in topics:
            score = topic.get('score', 50)
            weight = topic.get('weight', 0.5)
            potential = min(85, score + 20) - score
            improvement_points += potential * weight * 0.6  # 60% achievable
        
        predicted_score = min(95, current_avg + improvement_points)
        
        return {
            "current_average": round(current_avg, 1),
            "predicted_average": round(predicted_score, 1),
            "improvement_potential": round(predicted_score - current_avg, 1),
            "confidence": "high" if improvement_points > 10 else "medium",
            "timeline": "6-8 weeks with consistent effort",
            "success_probability": 0.75 if improvement_points > 15 else 0.6
        }

    def _get_priority_order(self, topics: List[Dict[str, Any]]) -> List[str]:
        """Get topics in priority order."""
        sorted_topics = sorted(
            topics,
            key=lambda x: (
                0 if x.get('weakness_level') == 'critical' else
                1 if x.get('weakness_level') == 'high' else
                2 if x.get('weakness_level') == 'medium' else 3,
                -x.get('weight', 0.5)
            )
        )
        return [t.get('topic_name', 'Unknown') for t in sorted_topics]


# Singleton instance
_weakness_analyzer: Optional[WeaknessAnalyzer] = None

def get_weakness_analyzer() -> WeaknessAnalyzer:
    """Get singleton instance of WeaknessAnalyzer."""
    global _weakness_analyzer
    if _weakness_analyzer is None:
        _weakness_analyzer = WeaknessAnalyzer()
    return _weakness_analyzer