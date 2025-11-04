# app/ml/weakness_predictor.py
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.cluster import KMeans
import numpy as np
from typing import List, Dict, Any

class WeaknessAnalyzer:
    def __init__(self):
        self.severity_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.improvement_predictor = GradientBoostingRegressor(n_estimators=100, random_state=42)
        
    def analyze_topic_weakness(
        self,
        topic_scores: Dict[str, float],
        overall_score: float,
        exam_weights: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Analyze weaknesses in specific topics
        """
        weaknesses = []
        
        for topic, score in topic_scores.items():
            severity = self._calculate_severity(score, overall_score, exam_weights.get(topic, 0.1))
            
            if severity in ['high', 'medium']:
                improvement_potential = self._calculate_improvement_potential(
                    score,
                    overall_score,
                    exam_weights.get(topic, 0.1)
                )
                
                weakness = {
                    'name': topic,
                    'severity': severity,
                    'current_score': score,
                    'target_score': min(score + improvement_potential, 100),
                    'improvement': f'+{int(improvement_potential)} points',
                    'exam_weight': f"{int(exam_weights.get(topic, 0.1) * 100)}%",
                    'time_estimate': self._estimate_time_to_improve(improvement_potential),
                    'resources': self._count_available_resources(topic)
                }
                
                weaknesses.append(weakness)
        
        return sorted(weaknesses, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x['severity']], reverse=True)
    
    def _calculate_severity(self, score: float, overall: float, weight: float) -> str:
        """Calculate severity level of weakness"""
        gap = overall - score
        weighted_impact = gap * weight
        
        if score < 50 or weighted_impact > 15:
            return 'high'
        elif score < 70 or weighted_impact > 8:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_improvement_potential(
        self,
        current_score: float,
        overall_score: float,
        weight: float
    ) -> float:
        """Calculate realistic improvement potential"""
        gap_to_overall = overall_score - current_score
        
        if gap_to_overall < 0:
            return min(25, (85 - current_score) * 0.6)
        else:
            return min(30, max(15, gap_to_overall * 1.5))
    
    def _estimate_time_to_improve(self, improvement_points: float) -> str:
        """Estimate time needed to achieve improvement"""
        days = int(improvement_points * 0.5)  # Roughly 0.5 days per point
        
        if days < 7:
            return f"{days} days"
        elif days < 21:
            return f"{days // 7} week{'s' if days // 7 > 1 else ''}"
        else:
            return f"{days // 7} weeks"
    
    def _count_available_resources(self, topic: str) -> int:
        """Count available resources for a topic (would query DB in production)"""
        return np.random.randint(2, 8)  # Placeholder
    
    def generate_ai_analysis(
        self,
        subject_name: str,
        weaknesses: List[Dict[str, Any]],
        student_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered analysis and recommendations"""
        
        # Identify root cause
        root_causes = []
        if len(weaknesses) > 3:
            root_causes.append("Multiple topic gaps indicating foundational concept issues")
        if any(w['severity'] == 'high' for w in weaknesses):
            high_severity_topics = [w['name'] for w in weaknesses if w['severity'] == 'high']
            root_causes.append(f"Critical gaps in {', '.join(high_severity_topics[:2])}")
        
        root_cause = root_causes[0] if root_causes else "Some topics need focused attention"
        
        # Generate study strategy
        strategies = []
        if len(weaknesses) > 2:
            strategies.append("Focus on one topic at a time, starting with highest exam weight")
            strategies.append("Build strong foundation before moving to advanced concepts")
        else:
            strategies.append("Targeted practice on identified weak areas")
        
        strategies.append("Utilize video tutorials for visual understanding")
        strategies.append("Practice problems daily for 30-45 minutes")
        strategies.append("Join study groups for collaborative learning")
        
        # Generate recommendations
        recommendations = []
        for weakness in weaknesses[:3]:
            recommendations.append(
                f"Master {weakness['name']} through structured learning path with daily practice"
            )
        
        # Estimate improvement time
        total_improvement = sum(
            float(w['improvement'].replace('+', '').replace(' points', ''))
            for w in weaknesses
        )
        weeks = max(2, int(total_improvement * 0.5 / 7))
        
        return {
            'root_cause': root_cause,
            'recommendations': recommendations,
            'study_strategy': ' | '.join(strategies[:3]),
            'estimated_improvement_time': f"{weeks} weeks with consistent effort"
        }