# academic-advisor-backend/app/services/ml_service.py

"""
Enhanced ML Service
Comprehensive machine learning service for academic recommendations
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from app.models.student_profile import StudentProfile

# ── Resilient imports (prevent router mount failures) ──────────
try:
    from app.models.student_performance import StudentPerformance
except Exception:
    StudentPerformance = None

try:
    from app.core.curriculum import get_semester_subjects
except Exception:
    get_semester_subjects = None

try:
    from app.services.ml_performance_analysis import ml_analyzer
except Exception as e:
    ml_analyzer = None
    logging.getLogger(__name__).warning(f"ml_analyzer not available: {e}")

logger = logging.getLogger(__name__)



class EnhancedMLService:
    """Enhanced ML Service with curriculum and interest awareness"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.recommendation_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
    # ==================== ACADEMIC PERFORMANCE ANALYSIS ====================
    
    async def generate_comprehensive_analysis(
        self,
        student_id: str,
        include_trends: bool = True,
        include_comparisons: bool = True,
        include_interests: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive academic analysis including interests
        """
        try:
            # Get student profile
            student = await StudentProfile.find_one(StudentProfile.user_id == student_id)
            if not student:
                raise ValueError("Student not found")
            
            # Get performance history
            performance_history = await self._get_performance_history(student_id)
            
            # Get weakness data
            weaknesses = await ml_analyzer.detect_weaknesses(
                student_data={
                    'id': student_id,
                    'cgpa': student.cgpa,
                    'attendance': 85,  # Default or fetch from attendance system
                    'current_semester': student.current_semester,
                    'branch': student.branch
                },
                performance_history=performance_history,
                assessments=[],
                force_refresh=True
            )
            
            analysis = {
                'student_id': student_id,
                'timestamp': datetime.utcnow().isoformat(),
                'profile': {
                    'name': student.name,
                    'branch': student.branch,
                    'semester': student.current_semester,
                    'cgpa': student.cgpa,
                    'admission_year': student.admission_year
                }
            }
            
            # Performance analysis
            performance_prediction = await ml_analyzer.predict_performance(
                student_data={
                    'id': student_id,
                    'cgpa': student.cgpa,
                    'attendance': 85,
                    'current_semester': student.current_semester,
                    'total_credits': student.total_credits_earned,
                    'branch': student.branch
                },
                performance_history=performance_history
            )
            
            analysis['performance'] = {
                'current_cgpa': student.cgpa,
                'predicted_next_sgpa': performance_prediction.get('predicted_sgpa'),
                'risk_score': performance_prediction.get('risk_score'),
                'risk_level': performance_prediction.get('risk_level'),
                'success_probability': performance_prediction.get('success_probability'),
                'insights': performance_prediction.get('insights', [])
            }
            
            # Trends analysis
            if include_trends:
                trends = await self._analyze_performance_trends(performance_history)
                analysis['trends'] = trends
            
            # Weaknesses
            analysis['weaknesses'] = weaknesses
            
            # Interest-based recommendations
            if include_interests:
                interest_analysis = await self._analyze_interests(student)
                analysis['interests'] = interest_analysis
                
                # Elective recommendations based on interests
                elective_recs = await self._recommend_electives_by_interest(
                    student,
                    interest_analysis
                )
                analysis['interest_based_electives'] = elective_recs
            
            # Curriculum-specific recommendations
            curriculum_recs = await self._get_curriculum_recommendations(
                student,
                weaknesses,
                performance_history
            )
            analysis['curriculum_recommendations'] = curriculum_recs
            
            # Peer comparison (if enabled)
            if include_comparisons:
                peer_comparison = await self._compare_with_peers(
                    student,
                    performance_history
                )
                analysis['peer_comparison'] = peer_comparison
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating comprehensive analysis: {e}")
            raise
    
    async def _get_performance_history(
        self,
        student_id: str
    ) -> List[Dict[str, Any]]:
        """Get student's performance history"""
        try:
            student = await StudentProfile.find_one(StudentProfile.user_id == student_id)
            if not student:
                return []
            
            # Convert semester records to performance history
            history = []
            for sem_record in student.semester_records:
                history.append({
                    'semester': sem_record.semester_number,
                    'sgpa': sem_record.sgpa,
                    'credits_earned': sem_record.credits_earned,
                    'total_credits': sem_record.total_credits,
                    'subjects': [
                        {
                            'subject_name': s.subject_name,
                            'subject_code': s.subject_code,
                            'total_marks': s.total_marks,
                            'grade': s.grade,
                            'credits': s.credits,
                            'is_practical': s.is_practical
                        }
                        for s in sem_record.subjects
                    ]
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting performance history: {e}")
            return []
    
    async def _analyze_performance_trends(
        self,
        performance_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze performance trends"""
        if not performance_history:
            return {}
        
        sgpas = [p['sgpa'] for p in performance_history]
        
        trends = {
            'overall_trend': 'stable',
            'improvement_rate': 0.0,
            'consistency': 'variable',
            'best_semester': max(performance_history, key=lambda x: x['sgpa'])['semester'],
            'worst_semester': min(performance_history, key=lambda x: x['sgpa'])['semester']
        }
        
        # Calculate trend
        if len(sgpas) > 1:
            trend_coef = np.polyfit(range(len(sgpas)), sgpas, 1)[0]
            trends['improvement_rate'] = float(trend_coef)
            
            if trend_coef > 0.2:
                trends['overall_trend'] = 'improving'
            elif trend_coef < -0.2:
                trends['overall_trend'] = 'declining'
        
        # Calculate consistency
        if len(sgpas) > 1:
            std_dev = np.std(sgpas)
            if std_dev < 0.3:
                trends['consistency'] = 'very_consistent'
            elif std_dev < 0.6:
                trends['consistency'] = 'consistent'
            elif std_dev < 1.0:
                trends['consistency'] = 'somewhat_variable'
            else:
                trends['consistency'] = 'highly_variable'
        
        return trends
    
    # ==================== INTEREST ANALYSIS ====================
    
    async def _analyze_interests(
        self,
        student: StudentProfile
    ) -> Dict[str, Any]:
        """Analyze student interests from profile and projects"""
        
        interests = {
            'declared_interests': student.interests or [],
            'career_goals': student.career_goals or [],
            'skills': student.skills or [],
            'interest_strength': {},
            'recommended_focus_areas': []
        }
        
        # Analyze interest strength
        for interest in student.interests:
            # In a real implementation, this would analyze project history,
            # course performance in related subjects, etc.
            interests['interest_strength'][interest] = {
                'strength': 75,  # Placeholder
                'based_on': ['declared_interest'],
                'related_courses': [],
                'related_projects': []
            }
        
        # Recommend focus areas
        if student.interests:
            interests['recommended_focus_areas'] = student.interests[:3]
        else:
            # Default recommendations based on branch
            branch_defaults = {
                'IT': ['Web Development', 'Data Science', 'Cloud Computing'],
                'COMP': ['Artificial Intelligence', 'Machine Learning', 'Algorithms'],
                'EXTC': ['Signal Processing', 'Communication Systems', 'IoT'],
                'ELEC': ['Power Systems', 'Control Systems', 'Renewable Energy'],
                'MECH': ['Design', 'Manufacturing', 'Robotics']
            }
            interests['recommended_focus_areas'] = branch_defaults.get(
                student.branch, 
                ['General Engineering']
            )
        
        return interests
    
    async def _recommend_electives_by_interest(
        self,
        student: StudentProfile,
        interest_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Recommend electives based on student interests"""
        
        recommendations = []
        
        # Get available electives for student's semester
        semester = student.current_semester
        
        # Interest-to-elective mapping
        interest_elective_map = {
            'Artificial Intelligence': ['Machine Learning', 'Deep Learning', 'Natural Language Processing'],
            'Machine Learning': ['Machine Learning', 'Data Science', 'Big Data Analytics'],
            'Web Development': ['Full Stack Development', 'Cloud Computing', 'DevOps'],
            'Data Science': ['Data Warehouse and Mining', 'Big Data Analytics', 'Machine Learning'],
            'Cloud Computing': ['Cloud Computing Services', 'Distributed Systems', 'DevOps'],
            'Cybersecurity': ['Cryptography & Network Security', 'Ethical Hacking', 'Security Management'],
            'IoT': ['Internet of Things', 'Embedded Systems', 'Wireless Technologies'],
            'Mobile Development': ['Mobile App Development', 'Cross-Platform Development']
        }
        
        # Get student interests
        student_interests = interest_analysis.get('declared_interests', [])
        
        for interest in student_interests:
            related_electives = interest_elective_map.get(interest, [])
            
            for elective in related_electives:
                recommendations.append({
                    'elective_name': elective,
                    'interest': interest,
                    'match_score': 85,
                    'reason': f'Aligns with your interest in {interest}',
                    'semester_available': [5, 6, 7, 8]
                })
        
        # Remove duplicates
        seen = set()
        unique_recs = []
        for rec in recommendations:
            if rec['elective_name'] not in seen:
                seen.add(rec['elective_name'])
                unique_recs.append(rec)
        
        return unique_recs[:5]  # Top 5
    
    # ==================== CURRICULUM RECOMMENDATIONS ====================
    
    async def _get_curriculum_recommendations(
        self,
        student: StudentProfile,
        weaknesses: List[Dict[str, Any]],
        performance_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get curriculum-specific recommendations"""
        
        recommendations = {
            'immediate_actions': [],
            'elective_suggestions': [],
            'honours_minor_eligibility': {},
            'focus_areas': []
        }
        
        # Immediate actions based on weaknesses
        if weaknesses:
            critical_weaknesses = [w for w in weaknesses if w['severity'] == 'critical']
            high_weaknesses = [w for w in weaknesses if w['severity'] == 'high']
            
            if critical_weaknesses:
                recommendations['immediate_actions'].append({
                    'priority': 'critical',
                    'action': 'Schedule academic counseling session',
                    'reason': f"{len(critical_weaknesses)} critical weaknesses identified",
                    'subjects': [w['subject'] for w in critical_weaknesses]
                })
            
            if high_weaknesses:
                for weakness in high_weaknesses:
                    recommendations['immediate_actions'].append({
                        'priority': 'high',
                        'action': f"Focus on {weakness['subject']}",
                        'reason': f"Current average: {weakness['average_score']:.1f}%, Gap: {weakness['gap']:.1f}%",
                        'improvement_plan': weakness.get('improvement_plan')
                    })
        
        # Honours/Minor eligibility
        if student.current_semester >= 4:
            if student.cgpa >= 7.5:
                recommendations['honours_minor_eligibility'] = {
                    'eligible': True,
                    'cgpa': student.cgpa,
                    'message': 'Congratulations! You are eligible for Honours/Minor programs',
                    'available_programs': await self._get_eligible_honours_programs(student),
                    'application_deadline': 'Before Semester 5 registration'
                }
            else:
                gap = 7.5 - student.cgpa
                recommendations['honours_minor_eligibility'] = {
                    'eligible': False,
                    'cgpa': student.cgpa,
                    'required_cgpa': 7.5,
                    'gap': gap,
                    'message': f'Improve CGPA by {gap:.2f} to become eligible',
                    'suggestions': [
                        'Focus on upcoming semester subjects',
                        'Improve in weak areas',
                        'Maintain attendance above 85%'
                    ]
                }
        
        # Focus areas based on performance
        if performance_history:
            strong_subjects = await self._identify_strong_subjects(performance_history)
            recommendations['focus_areas'] = [
                {
                    'area': subject,
                    'reason': 'Strong performance in related subjects',
                    'average_score': score
                }
                for subject, score in strong_subjects[:3]
            ]
        
        return recommendations
    
    async def _get_eligible_honours_programs(
        self,
        student: StudentProfile
    ) -> List[Dict[str, Any]]:
        """Get honours programs eligible for student's branch"""
        
        # Honours program mapping (from curriculum)
        honours_programs = {
            'IT': [
                {
                    'program': 'AI & Machine Learning',
                    'type': 'Honours',
                    'credits': 18,
                    'duration': '4 semesters',
                    'courses': ['Knowledge Engineering', 'Foundation ML', 'Deep Learning', 'Advanced AI']
                },
                {
                    'program': 'Data Science',
                    'type': 'Minor',
                    'credits': 18,
                    'duration': '4 semesters',
                    'courses': ['Data Analytics', 'Statistical Methods', 'Big Data', 'Visualization']
                },
                {
                    'program': 'Cyber Security',
                    'type': 'Minor',
                    'credits': 18,
                    'duration': '4 semesters',
                    'courses': ['Network Security', 'Cryptography', 'Ethical Hacking', 'Security Management']
                }
            ],
            'COMP': [
                {
                    'program': 'AI & Machine Learning',
                    'type': 'Honours',
                    'credits': 18,
                    'duration': '4 semesters',
                    'courses': ['Knowledge Engineering', 'Foundation ML', 'Deep Learning', 'Advanced AI']
                }
            ],
            # Add other branches...
        }
        
        return honours_programs.get(student.branch, [])
    
    async def _identify_strong_subjects(
        self,
        performance_history: List[Dict[str, Any]]
    ) -> List[tuple]:
        """Identify subjects where student performed well"""
        
        subject_scores = {}
        
        for semester in performance_history:
            for subject in semester.get('subjects', []):
                name = subject['subject_name']
                score = subject.get('total_marks', 0)
                
                if name not in subject_scores:
                    subject_scores[name] = []
                
                subject_scores[name].append(score)
        
        # Calculate average scores
        avg_scores = [
            (subject, np.mean(scores))
            for subject, scores in subject_scores.items()
        ]
        
        # Sort by average score
        avg_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top performers (>75% average)
        return [(subj, score) for subj, score in avg_scores if score > 75]
    
    # ==================== PEER COMPARISON ====================
    
    async def _compare_with_peers(
        self,
        student: StudentProfile,
        performance_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare student with peers"""
        
        # In a real implementation, this would query database for peer data
        # For now, return mock comparison
        
        comparison = {
            'peer_group': f"{student.branch} - Semester {student.current_semester}",
            'total_peers': 60,
            'your_cgpa': student.cgpa,
            'peer_average_cgpa': 7.2,
            'your_rank': 15,
            'percentile': 75,
            'performance_category': 'Above Average'
        }
        
        if student.cgpa > 8.5:
            comparison['performance_category'] = 'Excellent'
        elif student.cgpa > 7.5:
            comparison['performance_category'] = 'Very Good'
        elif student.cgpa > 6.5:
            comparison['performance_category'] = 'Good'
        elif student.cgpa > 5.5:
            comparison['performance_category'] = 'Average'
        else:
            comparison['performance_category'] = 'Needs Improvement'
        
        return comparison
    
    # ==================== PROJECT-BASED RECOMMENDATIONS ====================
    
    async def analyze_project_for_recommendations(
        self,
        student_id: str,
        project_data: Dict[str, Any],
        inferred_interests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze project to generate academic recommendations
        This bridges project analysis with academic planning
        """
        try:
            student = await StudentProfile.find_one(StudentProfile.user_id == student_id)
            if not student:
                raise ValueError("Student not found")
            
            # Update student interests based on project
            await self._update_student_interests(student, inferred_interests)
            
            # Get performance data
            performance_history = await self._get_performance_history(student_id)
            
            # Generate integrated recommendations
            recommendations = {
                'project_aligned_electives': [],
                'skill_development_path': [],
                'career_alignment': [],
                'next_steps': []
            }
            
            # Map project interests to electives
            for interest in inferred_interests:
                domain = interest.get('domain')
                confidence = interest.get('confidence', 0)
                
                if confidence > 0.6:
                    # Get matching electives
                    matching_electives = await self._find_matching_electives(
                        domain,
                        student.branch,
                        student.current_semester
                    )
                    
                    for elective in matching_electives:
                        recommendations['project_aligned_electives'].append({
                            'elective': elective['name'],
                            'code': elective['code'],
                            'interest_domain': domain,
                            'match_score': int(confidence * 100),
                            'semester_available': elective.get('semester', 5),
                            'reason': f'Aligns with your project work in {domain}'
                        })
            
            # Skill development path
            current_skills = set(project_data.get('programmingLanguages', []) + 
                               project_data.get('frameworks', []))
            
            for interest in inferred_interests:
                related_skills = interest.get('relatedSkills', [])
                skills_to_learn = [s for s in related_skills if s not in current_skills]
                
                if skills_to_learn:
                    recommendations['skill_development_path'].append({
                        'domain': interest['domain'],
                        'current_skills': list(current_skills),
                        'skills_to_learn': skills_to_learn[:3],
                        'learning_priority': 'high' if interest['confidence'] > 0.8 else 'medium'
                    })
            
            # Career alignment
            for interest in inferred_interests:
                career_paths = interest.get('careerPaths', [])
                
                for career in career_paths:
                    recommendations['career_alignment'].append({
                        'career_path': career,
                        'alignment_score': int(interest['confidence'] * 100),
                        'domain': interest['domain'],
                        'preparation_required': await self._get_career_preparation(
                            career,
                            student,
                            current_skills
                        )
                    })
            
            # Next steps
            recommendations['next_steps'] = await self._generate_next_steps(
                student,
                inferred_interests,
                recommendations
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in project-based recommendations: {e}")
            raise
    
    async def _update_student_interests(
        self,
        student: StudentProfile,
        inferred_interests: List[Dict[str, Any]]
    ):
        """Update student's interest profile based on project analysis"""
        
        # Extract high-confidence interests
        new_interests = [
            interest['domain']
            for interest in inferred_interests
            if interest.get('confidence', 0) > 0.7
        ]
        
        # Merge with existing interests (avoid duplicates)
        existing_interests = set(student.interests or [])
        updated_interests = list(existing_interests.union(set(new_interests)))
        
        student.interests = updated_interests
        await student.save()
    
    async def _find_matching_electives(
        self,
        domain: str,
        branch: str,
        current_semester: int
    ) -> List[Dict[str, Any]]:
        """Find electives matching the interest domain"""
        
        # Domain to elective mapping
        domain_elective_map = {
            'Artificial Intelligence & Machine Learning': [
                {'name': 'Machine Learning', 'code': 'ITPEC5012', 'semester': 5},
                {'name': 'Deep Learning', 'code': 'ITPEC7031', 'semester': 7},
                {'name': 'Natural Language Processing', 'code': 'ITPEC7032', 'semester': 7}
            ],
            'Web Development': [
                {'name': 'Full Stack Development', 'code': 'ITPEC6021', 'semester': 6},
                {'name': 'Cloud Computing Services', 'code': 'ITPEC5015', 'semester': 5}
            ],
            'Data Science': [
                {'name': 'Data Warehouse and Mining', 'code': 'ITPEC5014', 'semester': 5},
                {'name': 'Big Data Analytics', 'code': 'ITPEC6024', 'semester': 6},
                {'name': 'Machine Learning', 'code': 'ITPEC5012', 'semester': 5}
            ],
            'Cloud Computing': [
                {'name': 'Cloud Computing Services', 'code': 'ITPEC5015', 'semester': 5},
                {'name': 'Distributed Systems', 'code': 'ITPEC8053', 'semester': 8}
            ],
            'Mobile Development': [
                {'name': 'Mobile App Development', 'code': 'ITPEC6025', 'semester': 6},
                {'name': 'Cross-Platform Development', 'code': 'ITPEC7042', 'semester': 7}
            ],
            'Cybersecurity': [
                {'name': 'Cryptography & Network Security', 'code': 'ITPCC611', 'semester': 6},
                {'name': 'Ethical Hacking', 'code': 'ITPEC7032', 'semester': 7}
            ]
        }
        
        return domain_elective_map.get(domain, [])
    
    async def _get_career_preparation(
        self,
        career: str,
        student: StudentProfile,
        current_skills: set
    ) -> Dict[str, Any]:
        """Get preparation requirements for a career path"""
        
        # Career requirements mapping
        career_requirements = {
            'ML Engineer': {
                'required_skills': ['Python', 'TensorFlow', 'PyTorch', 'Statistics'],
                'recommended_electives': ['Machine Learning', 'Deep Learning'],
                'recommended_honours': 'AI & Machine Learning',
                'estimated_preparation_time': '1-2 years'
            },
            'Full Stack Developer': {
                'required_skills': ['JavaScript', 'React', 'Node.js', 'Database'],
                'recommended_electives': ['Full Stack Development', 'Cloud Computing'],
                'recommended_honours': None,
                'estimated_preparation_time': '6-12 months'
            },
            'Data Scientist': {
                'required_skills': ['Python', 'R', 'SQL', 'Statistics', 'Machine Learning'],
                'recommended_electives': ['Data Warehouse and Mining', 'Machine Learning'],
                'recommended_honours': 'Data Science',
                'estimated_preparation_time': '1-2 years'
            }
        }
        
        requirements = career_requirements.get(career, {
            'required_skills': [],
            'recommended_electives': [],
            'recommended_honours': None,
            'estimated_preparation_time': '1 year'
        })
        
        # Calculate skill gap
        required_skills = set(requirements.get('required_skills', []))
        skill_gap = list(required_skills - current_skills)
        
        return {
            **requirements,
            'skill_gap': skill_gap,
            'skills_you_have': list(required_skills.intersection(current_skills)),
            'completion_percentage': int((len(required_skills.intersection(current_skills)) / len(required_skills) * 100)) if required_skills else 0
        }
    
    async def _generate_next_steps(
        self,
        student: StudentProfile,
        interests: List[Dict[str, Any]],
        recommendations: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable next steps"""
        
        next_steps = []
        
        # Elective selection
        if student.current_semester >= 4:
            electives = recommendations.get('project_aligned_electives', [])
            if electives:
                next_steps.append({
                    'priority': 'high',
                    'category': 'Academic',
                    'action': 'Select Electives for Next Semester',
                    'details': f"Choose from {len(electives)} recommended electives aligned with your projects",
                    'deadline': 'Registration period',
                    'top_recommendations': [e['elective'] for e in electives[:3]]
                })
        
        # Honours/Minor application
        if student.current_semester == 4 and student.cgpa >= 7.5:
            next_steps.append({
                'priority': 'high',
                'category': 'Academic',
                'action': 'Apply for Honours/Minor Program',
                'details': 'You are eligible! Apply before Semester 5',
                'deadline': 'Before Sem 5 registration',
                'recommended_programs': [i['domain'] for i in interests if i.get('confidence', 0) > 0.8]
            })
        
        # Skill development
        skill_paths = recommendations.get('skill_development_path', [])
        if skill_paths:
            high_priority_skills = [
                s for path in skill_paths 
                for s in path.get('skills_to_learn', [])
                if path.get('learning_priority') == 'high'
            ]
            
            if high_priority_skills:
                next_steps.append({
                    'priority': 'medium',
                    'category': 'Skill Development',
                    'action': 'Learn Key Technical Skills',
                    'details': f"Focus on: {', '.join(high_priority_skills[:3])}",
                    'deadline': 'Next 3 months',
                    'resources': 'Check recommended learning resources'
                })
        
        # Portfolio building
        next_steps.append({
            'priority': 'medium',
            'category': 'Portfolio',
            'action': 'Build Advanced Projects',
            'details': 'Create projects showcasing your specialized interests',
            'deadline': 'This semester',
            'suggestions': [i['domain'] for i in interests[:2]]
        })
        
        # Career preparation
        career_alignments = recommendations.get('career_alignment', [])
        if career_alignments:
            top_career = max(career_alignments, key=lambda x: x['alignment_score'])
            
            next_steps.append({
                'priority': 'low',
                'category': 'Career',
                'action': f"Prepare for {top_career['career_path']}",
                'details': 'Start building relevant experience',
                'deadline': 'Next 6 months',
                'preparation': top_career.get('preparation_required')
            })
        
        return next_steps
    
    # ==================== UTILITY METHODS ====================
    
    async def predict_performance(
        self,
        current_grades: Dict[str, float],
        attendance: float,
        project_count: int,
        study_hours: Optional[float] = None,
        extracurricular: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Predict academic performance"""
        
        # Simple prediction logic
        avg_grade = np.mean(list(current_grades.values())) if current_grades else 70
        
        performance_score = (avg_grade * 0.6) + (attendance * 0.3) + (project_count * 2)
        
        if study_hours:
            performance_score += min(study_hours * 0.5, 10)
        
        if extracurricular:
            performance_score += min(len(extracurricular) * 2, 10)
        
        performance_score = min(performance_score, 100)
        
        return {
            'predicted_next_semester_gpa': performance_score / 10,
            'confidence': 0.75,
            'factors': {
                'current_performance': avg_grade,
                'attendance_impact': attendance * 0.3,
                'project_contribution': project_count * 2
            }
        }
    
    async def analyze_career_paths(
        self,
        skills: List[str],
        interests: List[str],
        academic_performance: Dict[str, float],
        personality_traits: Optional[List[str]] = None,
        career_goals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze and recommend career paths"""
        
        career_insights = {
            'recommended_paths': [],
            'skill_matches': {},
            'preparation_timeline': {}
        }
        
        # Simple career matching
        career_map = {
            'Software Engineer': {'skills': ['Python', 'Java', 'JavaScript'], 'interests': ['Programming', 'Web Development']},
            'Data Scientist': {'skills': ['Python', 'R', 'Statistics'], 'interests': ['Data Science', 'Analytics']},
            'ML Engineer': {'skills': ['Python', 'TensorFlow', 'PyTorch'], 'interests': ['AI', 'Machine Learning']},
        }
        
        for career, requirements in career_map.items():
            skill_match = len(set(skills).intersection(set(requirements['skills'])))
            interest_match = len(set(interests).intersection(set(requirements['interests'])))
            
            match_score = (skill_match * 30) + (interest_match * 40) + 30
            
            if match_score > 50:
                career_insights['recommended_paths'].append({
                    'career': career,
                    'match_score': match_score,
                    'required_skills': requirements['skills'],
                    'skill_gap': list(set(requirements['skills']) - set(skills))
                })
        
        return career_insights


# Global instance
enhanced_ml_service = EnhancedMLService()