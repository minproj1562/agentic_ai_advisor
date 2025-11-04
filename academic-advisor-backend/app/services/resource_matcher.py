# app/services/resource_matcher.py
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

class ResourceMatcher:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def calculate_resource_relevance(
        self,
        student_weaknesses: List[str],
        resource: Dict[str, Any]
    ) -> float:
        """Calculate relevance of resource to student weaknesses"""
        if not student_weaknesses:
            return 0.5
        
        # Get topics covered by resource
        resource_topics = resource.get('topics_covered', [])
        
        if not resource_topics:
            return 0.3
        
        # Calculate overlap
        weakness_set = set(student_weaknesses)
        topic_set = set(resource_topics)
        overlap = len(weakness_set & topic_set)
        
        if overlap == 0:
            # Use semantic similarity as fallback
            weakness_text = ' '.join(student_weaknesses)
            resource_text = ' '.join(resource_topics)
            
            embeddings = self.model.encode([weakness_text, resource_text])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(similarity)
        
        return min(overlap / len(weakness_set), 1.0)
    
    def match_resources(
        self,
        student_data: Dict[str, Any],
        resources: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Match resources to student profile"""
        
        # Extract student weaknesses
        weak_subjects = student_data.get('weak_subjects', [])
        weak_topics = []
        
        for subject in student_data.get('subjects', []):
            if subject['score'] < 70:
                weak_topics.extend(subject.get('weakness', []))
        
        all_weaknesses = weak_subjects + weak_topics
        
        # Score each resource
        scored_resources = []
        
        for resource in resources:
            # Calculate relevance score
            relevance = self.calculate_resource_relevance(all_weaknesses, resource)
            
            # Difficulty match
            student_level = self._get_student_level(student_data.get('overall_cgpa', 7.0))
            difficulty_match = self._match_difficulty(student_level, resource.get('difficulty', 'Intermediate'))
            
            # Rating weight
            rating_weight = resource.get('rating', 3.0) / 5.0
            
            # Calculate final score
            final_score = (relevance * 0.5) + (difficulty_match * 0.3) + (rating_weight * 0.2)
            
            scored_resources.append({
                **resource,
                'relevance_score': round(relevance, 2),
                'match_score': round(final_score * 100, 1),
                'match_reason': self._generate_match_reason(relevance, difficulty_match, rating_weight)
            })
        
        # Sort by match score
        scored_resources.sort(key=lambda x: x['match_score'], reverse=True)
        
        return scored_resources[:limit]
    
    def _get_student_level(self, cgpa: float) -> str:
        """Determine student level based on CGPA"""
        if cgpa >= 8.5:
            return 'Advanced'
        elif cgpa >= 7.0:
            return 'Intermediate'
        else:
            return 'Beginner'
    
    def _match_difficulty(self, student_level: str, resource_difficulty: str) -> float:
        """Match difficulty levels"""
        level_map = {'Beginner': 1, 'Intermediate': 2, 'Advanced': 3}
        
        student_val = level_map.get(student_level, 2)
        resource_val = level_map.get(resource_difficulty, 2)
        
        diff = abs(student_val - resource_val)
        
        if diff == 0:
            return 1.0
        elif diff == 1:
            return 0.7
        else:
            return 0.4
    
    def _generate_match_reason(self, relevance: float, difficulty: float, rating: float) -> str:
        """Generate reason for match"""
        reasons = []
        
        if relevance > 0.7:
            reasons.append("Highly relevant to your weak areas")
        elif relevance > 0.5:
            reasons.append("Addresses some of your weak topics")
        
        if difficulty > 0.8:
            reasons.append("Perfect difficulty level")
        
        if rating > 0.8:
            reasons.append("Highly rated by students")
        
        return " | ".join(reasons) if reasons else "Good match for your profile"