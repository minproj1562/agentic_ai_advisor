#academic-advisor-backend/app/services/recommendation_engine.py
from typing import List, Dict, Any, Optional
from app.models.student_performance import StudentPerformance
from app.models.elective import Elective
from app.models.resource import StudyResource
import logging

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self):
        self.logger = logger

    async def get_elective_recommendations(self, student_id: str, limit: int = 10) -> List[Elective]:
        """Get personalized elective recommendations for a student"""
        try:
            # Get student performance data
            performance = await StudentPerformance.find_one(
                StudentPerformance.student_info.uid == student_id
            ).sort(-StudentPerformance.updated_at)
            
            if not performance:
                return []

            # Get student's branch and interests
            branch = performance.student_info.branch
            interests = performance.interests
            strong_subjects = performance.strong_subjects
            weak_subjects = performance.weak_subjects

            # Build query filters
            query_filters = {
                "department": branch,
                "is_active": True
            }

            # Get electives matching student's branch
            electives = await Elective.find(query_filters).to_list(limit * 2)

            # Simple matching algorithm (can be enhanced with ML)
            scored_electives = []
            for elective in electives:
                score = 0.0
                
                # Match by interests
                for interest in interests:
                    if interest.lower() in elective.description.lower():
                        score += 2.0
                    if any(tag.lower() == interest.lower() for tag in elective.tags):
                        score += 1.5
                
                # Match by strong subjects (prerequisites)
                for subject in strong_subjects:
                    if any(prereq.lower() in subject.lower() for prereq in elective.prerequisites):
                        score += 1.0
                
                # Match by career goals
                if any(goal.lower() in elective.career_impact.lower() for goal in performance.career_goals):
                    score += 1.5
                
                # Consider difficulty level
                if performance.overall_cgpa >= 8.0 and elective.difficulty == "Advanced":
                    score += 1.0
                elif performance.overall_cgpa >= 7.0 and elective.difficulty == "Intermediate":
                    score += 1.0
                elif elective.difficulty == "Beginner":
                    score += 0.5
                
                # Consider popularity and rating
                score += (elective.average_rating / 10) * 0.5
                score += (elective.enrollment_count / 100) * 0.1
                
                scored_electives.append((elective, score))
            
            # Sort by score and return top recommendations
            scored_electives.sort(key=lambda x: x[1], reverse=True)
            return [elective for elective, score in scored_electives[:limit]]
            
        except Exception as e:
            self.logger.error(f"Error generating elective recommendations: {e}")
            return []

    async def get_study_resource_recommendations(
        self, 
        student_id: str, 
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 10
    ) -> List[StudyResource]:
        """Get personalized study resource recommendations"""
        try:
            # Get student performance data
            performance = await StudentPerformance.find_one(
                StudentPerformance.student_info.uid == student_id
            ).sort(-StudentPerformance.updated_at)
            
            if not performance:
                return []

            # Build query filters
            query_filters = {"is_active": True}
            
            if subject:
                query_filters["tags"] = {"$in": [subject]}
            if topic:
                query_filters["topics_covered"] = {"$in": [topic]}
            if difficulty:
                query_filters["difficulty"] = difficulty
            if resource_type:
                query_filters["type"] = resource_type

            # Get resources
            resources = await StudyResource.find(query_filters).to_list(limit * 2)

            # Simple matching algorithm
            scored_resources = []
            for resource in resources:
                score = 0.0
                
                # Match with weak subjects
                for weak_subject in performance.weak_subjects:
                    if weak_subject.lower() in resource.description.lower():
                        score += 2.0
                    if any(tag.lower() == weak_subject.lower() for tag in resource.tags):
                        score += 1.5
                
                # Match with interests
                for interest in performance.interests:
                    if interest.lower() in resource.description.lower():
                        score += 1.0
                
                # Consider resource quality
                score += resource.rating * 0.2
                score += resource.effectiveness_score * 0.3
                
                # Consider completion rate
                score += resource.completion_rate * 0.1
                
                # Consider exam relevance
                if resource.exam_relevance == "High":
                    score += 1.0
                elif resource.exam_relevance == "Medium":
                    score += 0.5
                
                scored_resources.append((resource, score))
            
            # Sort by score and return top recommendations
            scored_resources.sort(key=lambda x: x[1], reverse=True)
            return [resource for resource, score in scored_resources[:limit]]
            
        except Exception as e:
            self.logger.error(f"Error generating resource recommendations: {e}")
            return []

    async def generate_career_path_recommendations(self, student_id: str) -> List[Dict[str, Any]]:
        """Generate career path recommendations based on student profile"""
        try:
            performance = await StudentPerformance.find_one(
                StudentPerformance.student_info.uid == student_id
            ).sort(-StudentPerformance.updated_at)
            
            if not performance:
                return []

            career_paths = []
            
            # Analyze skills and interests to suggest career paths
            skills = performance.skills_matrix
            interests = performance.interests
            cgpa = performance.overall_cgpa
            branch = performance.student_info.branch
            
            # Software Engineering Path
            if any(interest in interests for interest in ['Web Development', 'Mobile Development', 'Software Engineering']):
                career_paths.append({
                    "title": "Software Engineer",
                    "match_score": 0.85,
                    "skills_required": ["Programming", "Algorithms", "System Design"],
                    "skills_matched": list(set(skills.keys()) & {"Programming", "Algorithms", "System Design"}),
                    "growth_prospects": "High",
                    "average_salary": "₹8-15 LPA",
                    "recommended_courses": ["Advanced Algorithms", "System Design", "Cloud Computing"]
                })
            
            # Data Science Path
            if any(interest in interests for interest in ['Data Science', 'AI/ML', 'Analytics']):
                career_paths.append({
                    "title": "Data Scientist",
                    "match_score": 0.78,
                    "skills_required": ["Statistics", "Machine Learning", "Python"],
                    "skills_matched": list(set(skills.keys()) & {"Statistics", "Machine Learning", "Python"}),
                    "growth_prospects": "Very High",
                    "average_salary": "₹10-20 LPA",
                    "recommended_courses": ["Machine Learning", "Deep Learning", "Big Data Analytics"]
                })
            
            # Cloud/DevOps Path
            if any(interest in interests for interest in ['Cloud Computing', 'DevOps', 'Infrastructure']):
                career_paths.append({
                    "title": "Cloud Engineer",
                    "match_score": 0.72,
                    "skills_required": ["Cloud Platforms", "Networking", "Linux"],
                    "skills_matched": list(set(skills.keys()) & {"Cloud Platforms", "Networking", "Linux"}),
                    "growth_prospects": "High",
                    "average_salary": "₹9-16 LPA",
                    "recommended_courses": ["Cloud Architecture", "Containerization", "Networking"]
                })
            
            return sorted(career_paths, key=lambda x: x["match_score"], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error generating career path recommendations: {e}")
            return []