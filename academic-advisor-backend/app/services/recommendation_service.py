# app/services/recommendation_service.py
"""
Recommendation Service
AI-powered recommendation engine
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np
from collections import defaultdict

from app.core.firebase_admin import firebase_manager
from app.services.ml_performance_analysis import ml_analyzer
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class RecommendationService:
    """
    Service for generating personalized recommendations
    """
    
    async def get_course_recommendations(
        self,
        student_id: str,
        include_electives: bool = True,
        include_minors: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get personalized course recommendations
        """
        try:
            # Get student profile
            student = await firebase_manager.get_document(
                collection="students",
                document_id=student_id,
                subcollections=["performance", "interests"]
            )
            
            if not student:
                return []
            
            # Get available courses
            courses = await firebase_manager.get_collection(
                collection="courses",
                filters=[
                    {'field': 'department', 'operator': '==', 'value': student['department']},
                    {'field': 'semester', 'operator': '>=', 'value': student['current_semester']}
                ]
            )
            
            recommendations = []
            
            for course in courses:
                # Skip if not matching criteria
                if not include_electives and course.get('type') == 'elective':
                    continue
                if not include_minors and course.get('type') == 'minor':
                    continue
                
                # Calculate recommendation score
                score = await self._calculate_course_score(student, course)
                
                if score > 0.5:  # Threshold for recommendation
                    recommendations.append({
                        'course': course,
                        'score': score,
                        'reasons': self._get_recommendation_reasons(student, course, score),
                        'priority': 'high' if score > 0.8 else 'medium' if score > 0.6 else 'low'
                    })
            
            # Sort by score
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            
            return recommendations[:10]  # Top 10 recommendations
            
        except Exception as e:
            logger.error(f"Error getting course recommendations: {str(e)}")
            return []
    
    async def _calculate_course_score(
        self,
        student: Dict[str, Any],
        course: Dict[str, Any]
    ) -> float:
        """
        Calculate recommendation score for a course
        """
        score = 0.0
        
        # Interest alignment (40%)
        student_interests = set(student.get('interests', []))
        course_tags = set(course.get('tags', []))
        
        if student_interests and course_tags:
            overlap = len(student_interests.intersection(course_tags))
            score += (overlap / len(course_tags)) * 0.4
        
        # Performance alignment (30%)
        required_cgpa = course.get('min_cgpa', 0)
        student_cgpa = student.get('cgpa', 0)
        
        if student_cgpa >= required_cgpa:
            score += 0.3
        elif student_cgpa >= required_cgpa - 0.5:
            score += 0.15
        
        # Career alignment (20%)
        student_career = student.get('career_goal')
        course_careers = course.get('career_paths', [])
        
        if student_career and student_career in course_careers:
            score += 0.2
        
        # Skill development (10%)
        student_skills = set(student.get('skills', []))
        course_skills = set(course.get('skills_developed', []))
        
        new_skills = course_skills - student_skills
        if new_skills:
            score += min(len(new_skills) / 5, 0.1)
        
        return min(score, 1.0)
    
    def _get_recommendation_reasons(
        self,
        student: Dict[str, Any],
        course: Dict[str, Any],
        score: float
    ) -> List[str]:
        """
        Get reasons for recommendation
        """
        reasons = []
        
        if score > 0.8:
            reasons.append("Highly relevant to your profile")
        
        # Check specific alignments
        student_interests = set(student.get('interests', []))
        course_tags = set(course.get('tags', []))
        
        if student_interests.intersection(course_tags):
            reasons.append("Matches your interests")
        
        if student.get('career_goal') in course.get('career_paths', []):
            reasons.append("Aligns with career goals")
        
        if course.get('difficulty') == 'moderate':
            reasons.append("Appropriate difficulty level")
        
        return reasons
    
    async def get_career_paths(
        self,
        student_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get career path recommendations
        """
        try:
            # Get student profile
            student = await firebase_manager.get_document(
                collection="students",
                document_id=student_id
            )
            
            # Get career paths
            career_paths = await firebase_manager.get_collection(
                collection="career_paths",
                filters=[
                    {'field': 'department', 'operator': '==', 'value': student['department']}
                ]
            )
            
            recommendations = []
            
            for path in career_paths:
                # Calculate fit score
                fit_score = await self._calculate_career_fit(student, path)
                
                recommendations.append({
                    'career': path,
                    'fit_score': fit_score,
                    'requirements_met': self._check_requirements(student, path),
                    'skill_gaps': self._identify_skill_gaps(student, path),
                    'recommended_courses': path.get('recommended_courses', []),
                    'average_salary': path.get('average_salary'),
                    'growth_rate': path.get('growth_rate')
                })
            
            # Sort by fit score
            recommendations.sort(key=lambda x: x['fit_score'], reverse=True)
            
            return recommendations[:5]
            
        except Exception as e:
            logger.error(f"Error getting career paths: {str(e)}")
            return []
    
    async def _calculate_career_fit(
        self,
        student: Dict[str, Any],
        career_path: Dict[str, Any]
    ) -> float:
        """
        Calculate career fit score
        """
        score = 0.0
        
        # Skill match (40%)
        required_skills = set(career_path.get('required_skills', []))
        student_skills = set(student.get('skills', []))
        
        if required_skills:
            skill_match = len(student_skills.intersection(required_skills)) / len(required_skills)
            score += skill_match * 0.4
        
        # Academic performance (30%)
        min_cgpa = career_path.get('min_cgpa', 6.0)
        if student.get('cgpa', 0) >= min_cgpa:
            score += 0.3
        elif student.get('cgpa', 0) >= min_cgpa - 0.5:
            score += 0.15
        
        # Interest alignment (30%)
        career_interests = set(career_path.get('interests', []))
        student_interests = set(student.get('interests', []))
        
        if career_interests and student_interests:
            interest_match = len(student_interests.intersection(career_interests)) / len(career_interests)
            score += interest_match * 0.3
        
        return min(score, 1.0)
    
    def _check_requirements(
        self,
        student: Dict[str, Any],
        career_path: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Check if student meets career requirements
        """
        requirements = {}
        
        # CGPA requirement
        min_cgpa = career_path.get('min_cgpa', 6.0)
        requirements['cgpa'] = student.get('cgpa', 0) >= min_cgpa
        
        # Skill requirements
        required_skills = career_path.get('required_skills', [])
        student_skills = student.get('skills', [])
        requirements['core_skills'] = all(skill in student_skills for skill in required_skills[:3])
        
        # Course requirements
        required_courses = career_path.get('required_courses', [])
        completed_courses = student.get('completed_courses', [])
        requirements['courses'] = all(course in completed_courses for course in required_courses)
        
        return requirements
    
    def _identify_skill_gaps(
        self,
        student: Dict[str, Any],
        career_path: Dict[str, Any]
    ) -> List[str]:
        """
        Identify skill gaps for career path
        """
        required_skills = set(career_path.get('required_skills', []))
        student_skills = set(student.get('skills', []))
        
        return list(required_skills - student_skills)
    
    async def get_learning_resources(
        self,
        student_id: str,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get personalized learning resources
        """
        try:
            # Get student data
            student = await firebase_manager.get_document(
                collection="students",
                document_id=student_id,
                subcollections=["weaknesses"]
            )
            
            # Build filters
            filters = []
            
            if subject:
                filters.append({'field': 'subject', 'operator': '==', 'value': subject})
            
            if difficulty:
                filters.append({'field': 'difficulty', 'operator': '==', 'value': difficulty})
            
            # Get resources
            resources = await firebase_manager.get_collection(
                collection="learning_resources",
                filters=filters
            )
            
            # Personalize recommendations
            personalized = []
            
            for resource in resources:
                # Calculate relevance score
                relevance = await self._calculate_resource_relevance(student, resource)
                
                if relevance > 0.3:
                    personalized.append({
                        'resource': resource,
                        'relevance_score': relevance,
                        'estimated_time': resource.get('duration'),
                        'difficulty': resource.get('difficulty'),
                        'format': resource.get('format')
                    })
            
            # Sort by relevance
            personalized.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return personalized[:20]
            
        except Exception as e:
            logger.error(f"Error getting learning resources: {str(e)}")
            return []
    
    async def _calculate_resource_relevance(
        self,
        student: Dict[str, Any],
        resource: Dict[str, Any]
    ) -> float:
        """
        Calculate resource relevance for student
        """
        score = 0.5  # Base score
        
        # Check if resource addresses weaknesses
        weaknesses = student.get('weaknesses', [])
        for weakness in weaknesses:
            if weakness.get('subject') == resource.get('subject'):
                score += 0.3
                break
        
        # Difficulty matching
        student_level = student.get('current_semester', 1)
        resource_level = resource.get('recommended_semester', 1)
        
        if abs(student_level - resource_level) <= 1:
            score += 0.2
        
        return min(score, 1.0)
    
    async def get_skill_recommendations(
        self,
        student_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get skill development recommendations
        """
        try:
            # Get student profile
            student = await firebase_manager.get_document(
                collection="students",
                document_id=student_id
            )
            
            # Get industry skills
            industry_skills = await firebase_manager.get_collection(
                collection="industry_skills",
                filters=[
                    {'field': 'department', 'operator': '==', 'value': student['department']}
                ]
            )
            
            current_skills = set(student.get('skills', []))
            recommendations = []
            
            for skill in industry_skills:
                if skill['name'] not in current_skills:
                    recommendations.append({
                        'skill': skill['name'],
                        'importance': skill.get('importance', 'medium'),
                        'demand_level': skill.get('demand_level', 'moderate'),
                        'learning_resources': skill.get('resources', []),
                        'estimated_learning_time': skill.get('learning_time', '2-4 weeks'),
                        'prerequisites': skill.get('prerequisites', [])
                    })
            
            # Sort by importance and demand
            importance_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            recommendations.sort(
                key=lambda x: importance_order.get(x['importance'], 4)
            )
            
            return recommendations[:10]
            
        except Exception as e:
            logger.error(f"Error getting skill recommendations: {str(e)}")
            return []
    
    async def get_mentor_recommendations(
        self,
        student_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get mentor recommendations
        """
        try:
            # Get student profile
            student = await firebase_manager.get_document(
                collection="students",
                document_id=student_id
            )
            
            # Get available mentors
            mentors = await firebase_manager.get_collection(
                collection="mentors",
                filters=[
                    {'field': 'department', 'operator': '==', 'value': student['department']},
                    {'field': 'accepting_mentees', 'operator': '==', 'value': True}
                ]
            )
            
            recommendations = []
            
            for mentor in mentors:
                # Calculate compatibility score
                compatibility = await self._calculate_mentor_compatibility(student, mentor)
                
                recommendations.append({
                    'mentor': {
                        'id': mentor['id'],
                        'name': mentor['name'],
                        'expertise': mentor.get('expertise', []),
                        'experience_years': mentor.get('experience_years'),
                        'current_mentees': mentor.get('current_mentees', 0)
                    },
                    'compatibility_score': compatibility,
                    'shared_interests': list(
                        set(student.get('interests', [])).intersection(
                            set(mentor.get('interests', []))
                        )
                    ),
                    'availability': mentor.get('availability', 'moderate')
                })
            
            # Sort by compatibility
            recommendations.sort(key=lambda x: x['compatibility_score'], reverse=True)
            
            return recommendations[:5]
            
        except Exception as e:
            logger.error(f"Error getting mentor recommendations: {str(e)}")
            return []
    
    async def _calculate_mentor_compatibility(
        self,
        student: Dict[str, Any],
        mentor: Dict[str, Any]
    ) -> float:
        """
        Calculate student-mentor compatibility
        """
        score = 0.0
        
        # Interest alignment (40%)
        student_interests = set(student.get('interests', []))
        mentor_interests = set(mentor.get('interests', []))
        
        if student_interests and mentor_interests:
            overlap = len(student_interests.intersection(mentor_interests))
            score += (overlap / max(len(student_interests), 1)) * 0.4
        
        # Career goal alignment (30%)
        if student.get('career_goal') in mentor.get('expertise', []):
            score += 0.3
        
        # Availability (20%)
        if mentor.get('current_mentees', 0) < mentor.get('max_mentees', 5):
            score += 0.2
        
        # Rating (10%)
        rating = mentor.get('rating', 3.0)
        score += (rating / 5.0) * 0.1
        
        return min(score, 1.0)
    
    async def record_feedback(
        self,
        recommendation_id: str,
        student_id: str,
        feedback: Dict[str, Any]
    ):
        """
        Record feedback on recommendation
        """
        try:
            feedback_data = {
                'recommendation_id': recommendation_id,
                'student_id': student_id,
                'rating': feedback.get('rating'),
                'useful': feedback.get('useful'),
                'comments': feedback.get('comments'),
                'created_at': datetime.utcnow().isoformat()
            }
            
            await firebase_manager.create_document(
                collection="recommendation_feedback",
                data=feedback_data
            )
            
            # Update recommendation effectiveness metrics
            await self._update_recommendation_metrics(recommendation_id, feedback)
            
        except Exception as e:
            logger.error(f"Error recording feedback: {str(e)}")
            raise
    
    async def _update_recommendation_metrics(
        self,
        recommendation_id: str,
        feedback: Dict[str, Any]
    ):
        """
        Update recommendation effectiveness metrics
        """
        # This would update ML model training data
        pass
    
    async def generate_personalized_plan(
        self,
        student_id: str
    ) -> Dict[str, Any]:
        """
        Generate complete personalized academic plan
        """
        try:
            # Get all necessary data
            student = await firebase_manager.get_document(
                collection="students",
                document_id=student_id,
                subcollections=["performance", "weaknesses", "interests"]
            )
            
            # Generate different plan components
            plan = {
                'student_id': student_id,
                'generated_at': datetime.utcnow().isoformat(),
                'validity_period': '1 semester',
                'components': {}
            }
            
            # Course recommendations
            plan['components']['courses'] = await self.get_course_recommendations(
                student_id, True, True
            )
            
            # Skill development plan
            plan['components']['skills'] = await self.get_skill_recommendations(
                student_id
            )
            
            # Learning resources
            plan['components']['resources'] = await self.get_learning_resources(
                student_id
            )
            
            # Career guidance
            plan['components']['career_paths'] = await self.get_career_paths(
                student_id
            )
            
            # Study schedule
            plan['components']['study_schedule'] = self._generate_study_schedule(
                student
            )
            
            # Milestones
            plan['components']['milestones'] = self._generate_milestones(
                student
            )
            
            return plan
            
        except Exception as e:
            logger.error(f"Error generating personalized plan: {str(e)}")
            return {}
    
    def _generate_study_schedule(
        self,
        student: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate personalized study schedule
        """
        weaknesses = student.get('weaknesses', [])
        
        schedule = {
            'daily_hours': 3 if weaknesses else 2,
            'weekly_plan': {}
        }
        
        # Allocate time based on weaknesses
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
            schedule['weekly_plan'][day] = {
                'subjects': [],
                'hours': 2,
                'focus': 'regular_study'
            }
        
        # Weekend intensive sessions
        schedule['weekly_plan']['Saturday'] = {
            'subjects': [w['subject'] for w in weaknesses[:2]],
            'hours': 4,
            'focus': 'weakness_improvement'
        }
        
        schedule['weekly_plan']['Sunday'] = {
            'subjects': ['revision', 'practice'],
            'hours': 3,
            'focus': 'consolidation'
        }
        
        return schedule
    
    def _generate_milestones(
        self,
        student: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate academic milestones
        """
        current_cgpa = student.get('cgpa', 0)
        target_cgpa = min(current_cgpa + 0.5, 9.0)
        
        milestones = [
            {
                'title': 'Improve CGPA',
                'target': f'Achieve {target_cgpa:.1f} CGPA',
                'deadline': '1 semester',
                'progress_metric': 'cgpa'
            },
            {
                'title': 'Skill Development',
                'target': 'Learn 3 new technical skills',
                'deadline': '6 months',
                'progress_metric': 'skills_count'
            },
            {
                'title': 'Project Completion',
                'target': 'Complete 2 major projects',
                'deadline': '1 semester',
                'progress_metric': 'projects_count'
            }
        ]
        
        # Add weakness-specific milestones
        weaknesses = student.get('weaknesses', [])
        for weakness in weaknesses[:2]:
            milestones.append({
                'title': f'Improve {weakness["subject"]}',
                'target': f'Achieve 70% in {weakness["subject"]}',
                'deadline': '2 months',
                'progress_metric': 'subject_score'
            })
        
        return milestones