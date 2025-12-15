# app/ml/weakness_predictor.py
from typing import List, Dict, Any, Tuple
import logging
from app.models.weakness import TopicAnalysis  # Fixed import

logger = logging.getLogger(__name__)

class WeaknessAnalyzer:
    def __init__(self):
        self.logger = logger
        self.weakness_thresholds = {
            'critical': 40,
            'high': 55,
            'medium': 65,
            'low': 75
        }

    def analyze_topic_weakness(
        self, 
        topic_scores: Dict[str, float], 
        overall_score: float,
        exam_weights: Dict[str, float]
    ) -> List[TopicAnalysis]:
        """Analyze topic-level weaknesses for a subject"""
        weaknesses = []
        
        for topic, score in topic_scores.items():
            weight = exam_weights.get(topic, 0.1)
            weakness_level = self._calculate_weakness_level(score, weight)
            
            if weakness_level != 'low':
                analysis = TopicAnalysis(
                    topic_name=topic,
                    score=score,
                    weight=weight,
                    weakness_level=weakness_level,
                    improvement_suggestions=self._generate_suggestions(topic, weakness_level),
                    recommended_resources=self._suggest_resources(topic, weakness_level),
                    practice_exercises=self._generate_practice_exercises(topic, weakness_level)  # Added this method
                )
                weaknesses.append(analysis)
        
        return weaknesses

    def _calculate_weakness_level(self, score: float, weight: float) -> str:
        """Calculate weakness level based on score and exam weight"""
        weighted_score = score * weight
        
        if weighted_score <= self.weakness_thresholds['critical']:
            return 'critical'
        elif weighted_score <= self.weakness_thresholds['high']:
            return 'high'
        elif weighted_score <= self.weakness_thresholds['medium']:
            return 'medium'
        else:
            return 'low'

    def _generate_suggestions(self, topic: str, level: str) -> List[str]:
        """Generate improvement suggestions based on topic and weakness level"""
        suggestions = {
            'critical': [
                f"Focus on fundamental concepts of {topic}",
                "Practice basic problems daily",
                "Seek help from instructor or tutor",
                "Review prerequisite knowledge"
            ],
            'high': [
                f"Practice medium-difficulty problems in {topic}",
                "Review solved examples thoroughly",
                "Create summary notes for key concepts",
                "Join study group for collaborative learning"
            ],
            'medium': [
                f"Solve advanced problems in {topic}",
                "Focus on application-based questions",
                "Practice time-bound tests",
                "Teach concepts to peers to reinforce understanding"
            ]
        }
        
        return suggestions.get(level, ["Maintain current practice routine"])

    def _suggest_resources(self, topic: str, level: str) -> List[str]:
        """Suggest learning resources based on topic and weakness level"""
        resources = {
            'critical': [
                f"Beginner's guide to {topic}",
                "Fundamental concept videos",
                "Basic practice problems set",
                "Step-by-step tutorial series"
            ],
            'high': [
                f"Intermediate {topic} course",
                "Practice problem collections",
                "Concept explanation videos",
                "Solved examples compilation"
            ],
            'medium': [
                f"Advanced {topic} tutorials",
                "Competitive programming problems",
                "Real-world application examples",
                "Previous year question papers"
            ]
        }
        
        return resources.get(level, ["General practice materials"])

    def _generate_practice_exercises(self, topic: str, level: str) -> List[str]:
        """Generate practice exercises based on topic and weakness level"""
        exercises = {
            'critical': [
                f"Basic {topic} definition questions",
                "Simple multiple choice questions",
                "Step-by-step guided problems",
                "Concept mapping exercises"
            ],
            'high': [
                f"Medium difficulty {topic} problems",
                "Application-based questions",
                "Previous year basic questions",
                "Time-bound practice sets"
            ],
            'medium': [
                f"Advanced {topic} challenges",
                "Complex problem-solving exercises",
                "Competitive exam questions",
                "Real-world scenario problems"
            ]
        }
        
        return exercises.get(level, ["General practice problems"])

    def generate_ai_analysis(
        self, 
        subject: str, 
        weakness_topics: List[TopicAnalysis],
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered analysis and recommendations"""
        
        # Calculate overall weakness score
        total_weakness_score = sum(
            topic.score * topic.weight 
            for topic in weakness_topics 
            if topic.weakness_level in ['critical', 'high']
        )
        
        # Generate personalized insights
        insights = self._generate_insights(subject, weakness_topics, performance_data)
        
        # Create study plan
        study_plan = self._create_study_plan(weakness_topics, performance_data)
        
        return {
            "overall_weakness_score": round(total_weakness_score, 2),
            "critical_weaknesses": len([t for t in weakness_topics if t.weakness_level == 'critical']),
            "high_weaknesses": len([t for t in weakness_topics if t.weakness_level == 'high']),
            "insights": insights,
            "study_plan": study_plan,
            "predicted_improvement": self._predict_improvement(weakness_topics, performance_data),
            "priority_order": self._get_priority_order(weakness_topics)
        }

    def _generate_insights(
        self, 
        subject: str, 
        weakness_topics: List[TopicAnalysis],
        performance_data: Dict[str, Any]
    ) -> List[str]:
        """Generate personalized insights"""
        insights = []
        
        critical_topics = [t for t in weakness_topics if t.weakness_level == 'critical']
        high_topics = [t for t in weakness_topics if t.weakness_level == 'high']
        
        if critical_topics:
            insights.append(
                f"Critical weaknesses detected in {len(critical_topics)} key areas of {subject}. "
                "Immediate attention required to prevent impact on overall performance."
            )
        
        if high_topics:
            insights.append(
                f"Significant improvement opportunities in {len(high_topics)} important topics. "
                "Focus on these areas to boost your overall score."
            )
        
        # Add performance trend insights
        cgpa = performance_data.get('overall_cgpa', 0)  # Fixed field name
        if cgpa < 7.0:
            insights.append(
                "Your current CGPA indicates need for consistent improvement across subjects. "
                "Focus on strengthening fundamentals first."
            )
        elif cgpa > 8.5:
            insights.append(
                "Strong academic foundation detected. Focus on advanced topics and "
                "practical applications to excel further."
            )
        
        return insights

    def _create_study_plan(
        self, 
        weakness_topics: List[TopicAnalysis],
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create personalized study plan"""
        # Sort topics by severity and exam weight
        priority_topics = sorted(
            weakness_topics,
            key=lambda x: (
                0 if x.weakness_level == 'critical' else 
                1 if x.weakness_level == 'high' else 
                2 if x.weakness_level == 'medium' else 3,
                -x.weight
            )
        )
        
        study_plan = {
            "weekly_schedule": [],
            "daily_time_commitment": "2-3 hours",
            "focus_areas": [],
            "milestones": []
        }
        
        for i, topic in enumerate(priority_topics[:5]):  # Top 5 priority topics
            study_plan["focus_areas"].append({
                "topic": topic.topic_name,
                "priority": i + 1,
                "time_allocation": f"{2 + i * 0.5} hours weekly",
                "target_score": min(85, topic.score + 20)  # Realistic improvement target
            })
        
        # Add milestones
        study_plan["milestones"] = [
            "Week 1-2: Master fundamental concepts",
            "Week 3-4: Practice application problems", 
            "Week 5-6: Solve advanced and timed tests",
            "Week 7-8: Revision and mock tests"
        ]
        
        return study_plan

    def _predict_improvement(
        self, 
        weakness_topics: List[TopicAnalysis],
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict potential improvement with focused study"""
        current_score = performance_data.get('overall_cgpa', 7.0) * 10  # Convert to percentage scale
        
        # Calculate improvement potential
        improvement_potential = sum(
            (85 - topic.score) * topic.weight * 0.6  # 60% of gap can be closed
            for topic in weakness_topics 
            if topic.weakness_level in ['critical', 'high']
        )
        
        predicted_score = min(95, current_score + improvement_potential)
        
        return {
            "current_score": round(current_score, 1),
            "predicted_score": round(predicted_score, 1),
            "improvement_potential": round(improvement_potential, 1),
            "time_required": "6-8 weeks with consistent effort",
            "confidence_level": "high" if improvement_potential > 10 else "medium"
        }

    def _get_priority_order(self, weakness_topics: List[TopicAnalysis]) -> List[str]:
        """Get priority order for addressing weaknesses"""
        return [topic.topic_name for topic in sorted(
            weakness_topics,
            key=lambda x: (
                0 if x.weakness_level == 'critical' else 
                1 if x.weakness_level == 'high' else 
                2 if x.weakness_level == 'medium' else 3,
                -x.weight
            )
        )]