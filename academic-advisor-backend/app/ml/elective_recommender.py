# app/ml/elective_recommender.py
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class ElectiveRecommender:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.scaler = StandardScaler()
        
    def calculate_match_score(
        self,
        student_data: Dict[str, Any],
        elective: Dict[str, Any]
    ) -> Tuple[float, str]:
        """
        Calculate comprehensive match score between student and elective
        Returns: (match_score, reasoning)
        """
        scores = []
        reasons = []
        
        # 1. Skills Match (30%)
        student_skills = set(student_data.get('skills_matrix', {}).keys())
        required_skills = set(elective.get('skills_required', []))
        
        if required_skills:
            skills_match = len(student_skills & required_skills) / len(required_skills)
            scores.append(skills_match * 30)
            if skills_match > 0.7:
                reasons.append(f"Strong match with your skills in {', '.join(list(student_skills & required_skills)[:2])}")
        
        # 2. Interest Alignment (25%)
        student_interests = set(student_data.get('interests', []))
        elective_tags = set(elective.get('tags', []))
        
        if student_interests:
            interest_match = len(student_interests & elective_tags) / max(len(student_interests), 1)
            scores.append(interest_match * 25)
            if interest_match > 0.5:
                matching_interests = list(student_interests & elective_tags)[:2]
                reasons.append(f"Aligns with your interest in {', '.join(matching_interests)}")
        
        # 3. Career Goals Alignment (20%)
        career_goals = student_data.get('career_goals', [])
        career_impact = elective.get('career_impact', '').lower()
        
        career_match = 0
        for goal in career_goals:
            if goal.lower() in career_impact:
                career_match = 1.0
                reasons.append(f"Perfect fit for your {goal} career goal")
                break
        scores.append(career_match * 20)
        
        # 4. Prerequisites Met (15%)
        prerequisites = set(elective.get('prerequisites', []))
        completed_subjects = set([s['name'] for s in student_data.get('subjects', [])])
        
        if prerequisites:
            prereq_match = len(prerequisites & completed_subjects) / len(prerequisites)
            scores.append(prereq_match * 15)
            if prereq_match == 1.0:
                reasons.append("All prerequisites completed")
        else:
            scores.append(15)  # No prerequisites
        
        # 5. Performance Level Match (10%)
        avg_score = np.mean([s['score'] for s in student_data.get('subjects', [])])
        difficulty_map = {'Beginner': 60, 'Intermediate': 75, 'Advanced': 85}
        difficulty_threshold = difficulty_map.get(elective.get('difficulty', 'Intermediate'), 75)
        
        if avg_score >= difficulty_threshold:
            performance_match = 1.0
            scores.append(10)
        elif avg_score >= difficulty_threshold - 10:
            performance_match = 0.7
            scores.append(7)
        else:
            performance_match = 0.5
            scores.append(5)
        
        # Calculate final score
        final_score = sum(scores)
        
        # Generate comprehensive reasoning
        if not reasons:
            reasons.append("Good overall fit based on your academic profile")
        
        reasoning = reasons[0] if reasons else "Recommended based on your profile"
        
        return min(final_score, 100), reasoning
    
    def get_semantic_similarity(
        self,
        student_interests: List[str],
        elective_description: str
    ) -> float:
        """Calculate semantic similarity using sentence transformers"""
        if not student_interests:
            return 0.0
        
        interest_text = ' '.join(student_interests)
        
        embeddings = self.model.encode([interest_text, elective_description])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        
        return float(similarity)
    
    def recommend_electives(
        self,
        student_data: Dict[str, Any],
        available_electives: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate top-k elective recommendations for a student
        """
        recommendations = []
        
        for elective in available_electives:
            match_score, reasoning = self.calculate_match_score(student_data, elective)
            
            # Add semantic similarity bonus
            semantic_score = self.get_semantic_similarity(
                student_data.get('interests', []),
                elective.get('description', '')
            )
            
            # Adjust match score with semantic similarity (5% weight)
            final_score = match_score * 0.95 + semantic_score * 100 * 0.05
            
            recommendations.append({
                **elective,
                'match': round(final_score, 2),
                'reason': reasoning,
                'semantic_similarity': round(semantic_score, 3)
            })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x['match'], reverse=True)
        
        return recommendations[:top_k]
