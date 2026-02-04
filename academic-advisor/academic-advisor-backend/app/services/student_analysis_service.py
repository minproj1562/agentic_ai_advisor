# app/services/student_analysis_service.py
"""
Student Analysis Service Layer - MongoDB/Beanie Version
Business logic for processing student data and generating insights
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict
import logging

# Beanie/MongoDB models - use the one from student.py
from app.models.student import StudentPerformance as StudentPerformanceModel, TrendEnum
from app.models.weakness import WeaknessAnalysisResult
from app.core.firebase_admin import firebase_manager

logger = logging.getLogger(__name__)


class StudentAnalysisService:
    """
    Service for student analysis operations using MongoDB/Beanie
    """
    
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    # ==================== Main Analysis Methods ====================
    
    async def get_students_analysis(
        self,
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = 'overall_cgpa',
        sort_order: str = 'desc'
    ) -> List[Dict[str, Any]]:
        """
        Get comprehensive analysis for multiple students
        """
        try:
            filters = filters or {}
            
            # Build Beanie query conditions
            query_conditions = {}
            
            if filters.get('department'):
                query_conditions['student_info.branch'] = filters['department']
            
            if filters.get('semester'):
                query_conditions['student_info.semester'] = str(filters['semester'])
            
            if filters.get('batch'):
                query_conditions['student_info.batch'] = str(filters['batch'])
            
            # Build and execute query
            if query_conditions:
                query = StudentPerformanceModel.find(query_conditions)
            else:
                query = StudentPerformanceModel.find_all()
            
            # Apply sorting
            sort_field = f"-{sort_by}" if sort_order == 'desc' else sort_by
            query = query.sort(sort_field).skip(skip).limit(limit)
            
            performances = await query.to_list()
            
            # Process each student
            results = []
            for perf in performances:
                try:
                    analysis = await self._process_student_performance(perf)
                    if analysis:
                        results.append(analysis)
                except Exception as e:
                    logger.warning(f"Failed to process student: {e}")
                    continue
            
            # Apply post-processing
            results = self._apply_post_processing(results)
            
            logger.info(f"Processed analysis for {len(results)} students")
            return results
            
        except Exception as e:
            logger.error(f"Error in get_students_analysis: {str(e)}")
            return []
    
    async def _process_student_performance(
        self,
        performance: StudentPerformanceModel
    ) -> Optional[Dict[str, Any]]:
        """
        Process individual student performance data
        """
        try:
            student_info = performance.student_info
            
            # Get all performances for trend analysis
            all_performances = await StudentPerformanceModel.find(
                StudentPerformanceModel.student_info.uid == student_info.uid
            ).sort("-updated_at").to_list()
            
            # Calculate SGPA trend
            sgpa_trend = [p.semester_sgpa for p in all_performances]
            
            # Get weaknesses
            weaknesses = await self._get_student_weaknesses(student_info.uid)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(performance, all_performances, weaknesses)
            
            # Determine risk level
            risk_level = 'high' if risk_score >= 70 else 'medium' if risk_score >= 40 else 'low'
            
            # Calculate improvement trend
            improvement_trend = self._calculate_improvement_trend(sgpa_trend)
            
            # Get weakness data
            weakness_data = []
            for subject in performance.weak_subjects[:5]:
                subject_detail = next(
                    (s for s in performance.subjects if s.name == subject or s.code == subject),
                    None
                )
                if subject_detail:
                    weakness_data.append({
                        'subject': subject_detail.name,
                        'code': subject_detail.code,
                        'score': subject_detail.score,
                        'weaknesses': subject_detail.weakness,
                        'trend': subject_detail.trend.value if subject_detail.trend else 'stable'
                    })
            
            return {
                'student_id': student_info.uid,
                'name': student_info.name,
                'email': student_info.email,
                'department': student_info.branch,
                'batch': student_info.batch,
                'current_semester': int(student_info.semester) if student_info.semester.isdigit() else 1,
                'roll_number': student_info.rollNumber,
                'cgpa': float(performance.overall_cgpa),
                'sgpa_trend': sgpa_trend,
                'latest_sgpa': float(performance.semester_sgpa),
                'attendance': float(performance.attendance_average),
                'assignment_completion': float(performance.assignment_completion_rate),
                'weaknesses': weakness_data,
                'weak_subjects': performance.weak_subjects,
                'strong_subjects': performance.strong_subjects,
                'weakness_count': len(performance.weak_subjects),
                'risk_score': risk_score,
                'risk_level': risk_level,
                'improvement_trend': improvement_trend,
                'performance_trend': performance.performance_trend.value if performance.performance_trend else 'stable',
                'predicted_next_sgpa': performance.predicted_next_sgpa,
                'completed_credits': performance.completed_credits,
                'total_credits': performance.total_credits,
                'interests': performance.interests,
                'career_goals': performance.career_goals,
                'skills_matrix': performance.skills_matrix,
                'recommendations_pending': 0,
                'updated_at': performance.updated_at.isoformat() if performance.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Error processing student performance: {str(e)}")
            return None
    
    async def _get_student_weaknesses(self, student_id: str) -> List[Dict[str, Any]]:
        """Get weaknesses for a student"""
        try:
            weaknesses = await WeaknessAnalysisResult.find(
                WeaknessAnalysisResult.student_id == student_id
            ).to_list()
            
            return [
                {
                    'subject': getattr(w, 'subject_name', 'Unknown'),
                    'topic': '',
                    'severity': 'medium',
                    'gap': getattr(w, 'overall_risk_score', 0)
                }
                for w in weaknesses
            ]
        except Exception as e:
            logger.debug(f"Could not fetch weaknesses: {e}")
            return []
    
    def _calculate_risk_score(
        self,
        performance: StudentPerformanceModel,
        all_performances: List[StudentPerformanceModel],
        weaknesses: List[Dict]
    ) -> float:
        """Calculate risk score"""
        risk_score = 0.0
        
        # CGPA component (30%)
        if performance.overall_cgpa < 5.0:
            risk_score += 30
        elif performance.overall_cgpa < 6.0:
            risk_score += 20
        elif performance.overall_cgpa < 7.0:
            risk_score += 10
        
        # Attendance component (20%)
        if performance.attendance_average < 65:
            risk_score += 20
        elif performance.attendance_average < 75:
            risk_score += 10
        
        # Performance trend component (25%)
        if len(all_performances) >= 2:
            trend = all_performances[0].semester_sgpa - all_performances[1].semester_sgpa
            if trend < -0.5:
                risk_score += 25
            elif trend < 0:
                risk_score += 15
        
        # Weak subjects component (25%)
        weak_count = len(performance.weak_subjects)
        if weak_count >= 4:
            risk_score += 25
        elif weak_count >= 2:
            risk_score += 15
        elif weak_count >= 1:
            risk_score += 5
        
        return min(risk_score, 100.0)
    
    def _calculate_improvement_trend(self, sgpa_trend: List[float]) -> str:
        """Calculate improvement trend"""
        if len(sgpa_trend) < 2:
            return 'stable'
        
        diff = sgpa_trend[0] - sgpa_trend[1]
        if diff > 0.3:
            return 'improving'
        elif diff < -0.3:
            return 'declining'
        return 'stable'
    
    def _apply_post_processing(self, results: List[Dict]) -> List[Dict]:
        """Apply post-processing to results"""
        if not results:
            return results
        
        cgpas = [r['cgpa'] for r in results if r['cgpa'] > 0]
        
        if cgpas:
            try:
                percentiles = [
                    float(np.percentile(cgpas, 25)),
                    float(np.percentile(cgpas, 50)),
                    float(np.percentile(cgpas, 75))
                ]
                
                for result in results:
                    # Performance category
                    if result['cgpa'] >= 8.5:
                        result['performance_category'] = 'excellent'
                    elif result['cgpa'] >= 7.0:
                        result['performance_category'] = 'good'
                    elif result['cgpa'] >= 5.5:
                        result['performance_category'] = 'average'
                    else:
                        result['performance_category'] = 'needs_improvement'
                    
                    # Percentile rank
                    if result['cgpa'] <= percentiles[0]:
                        result['cgpa_percentile'] = 'bottom_25'
                    elif result['cgpa'] <= percentiles[1]:
                        result['cgpa_percentile'] = 'lower_middle'
                    elif result['cgpa'] <= percentiles[2]:
                        result['cgpa_percentile'] = 'upper_middle'
                    else:
                        result['cgpa_percentile'] = 'top_25'
            except Exception as e:
                logger.warning(f"Post-processing error: {e}")
        
        return results
    
    # ==================== Student Performance Methods ====================
    
    async def get_student_performance(
        self,
        student_id: str,
        time_range: str = 'all'
    ) -> Dict[str, Any]:
        """
        Get student performance - called by StudentService
        Alias for get_performance_data
        """
        return await self.get_performance_data(student_id, time_range)
    
    async def get_performance_data(
        self,
        student_id: str,
        time_range: str = 'all'
    ) -> Dict[str, Any]:
        """
        Get comprehensive performance data for a student
        """
        try:
            # Get all performances for this student
            query = StudentPerformanceModel.find(
                StudentPerformanceModel.student_info.uid == student_id
            ).sort("-updated_at")
            
            if time_range == 'current':
                query = query.limit(1)
            elif time_range == 'last_year':
                query = query.limit(2)
            
            performances = await query.to_list()
            
            if not performances:
                return {
                    'sgpa_trend': [],
                    'attendance_trend': [],
                    'statistics': {},
                    'subjects': [],
                    'strong_subjects': [],
                    'weak_subjects': []
                }
            
            # Process performance data
            sgpa_trend = []
            attendance_trend = []
            all_subjects = []
            
            for perf in performances:
                semester = perf.student_info.semester
                
                sgpa_trend.append({
                    'semester': semester,
                    'sgpa': perf.semester_sgpa,
                    'cgpa': perf.overall_cgpa,
                    'credits': perf.completed_credits
                })
                
                attendance_trend.append({
                    'semester': semester,
                    'attendance': perf.attendance_average,
                    'assignment_rate': perf.assignment_completion_rate
                })
                
                for subject in perf.subjects:
                    all_subjects.append({
                        'name': subject.name,
                        'code': subject.code,
                        'score': subject.score,
                        'grade': subject.grade,
                        'credits': subject.credits,
                        'semester': semester,
                        'trend': subject.trend.value if subject.trend else 'stable'
                    })
            
            # Calculate statistics
            sgpa_values = [p.semester_sgpa for p in performances]
            statistics = {
                'average_sgpa': float(np.mean(sgpa_values)) if sgpa_values else 0,
                'max_sgpa': float(np.max(sgpa_values)) if sgpa_values else 0,
                'min_sgpa': float(np.min(sgpa_values)) if sgpa_values else 0,
                'total_semesters': len(performances),
                'current_cgpa': performances[0].overall_cgpa if performances else 0
            }
            
            return {
                'sgpa_trend': sgpa_trend,
                'attendance_trend': attendance_trend,
                'statistics': statistics,
                'subjects': all_subjects,
                'strong_subjects': performances[0].strong_subjects if performances else [],
                'weak_subjects': performances[0].weak_subjects if performances else [],
                'skills_matrix': performances[0].skills_matrix if performances else {},
                'interests': performances[0].interests if performances else [],
                'career_goals': performances[0].career_goals if performances else []
            }
            
        except Exception as e:
            logger.error(f"Error getting performance data: {str(e)}")
            return {
                'sgpa_trend': [],
                'attendance_trend': [],
                'statistics': {},
                'subjects': [],
                'error': str(e)
            }
    
    async def get_student_by_id(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get student by ID"""
        try:
            performance = await StudentPerformanceModel.find_one(
                StudentPerformanceModel.student_info.uid == student_id
            )
            
            if performance:
                return await self._process_student_performance(performance)
            
            # Fallback to Firebase
            user_data = await firebase_manager.get_document("users", student_id)
            if user_data:
                return {
                    'student_id': student_id,
                    'name': user_data.get('name', user_data.get('displayName', '')),
                    'email': user_data.get('email', ''),
                    'department': user_data.get('department', ''),
                    'role': user_data.get('role', 'student')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting student {student_id}: {e}")
            return None
    
    # ==================== Recommendations ====================
    
    async def generate_recommendations(
        self,
        student: Dict[str, Any],
        performances: List[Any] = None,
        predictions: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendations
        Called by StudentService with student dict, performances list, and predictions
        """
        recommendations = []
        
        try:
            student_id = student.get('id') or student.get('uid') or student.get('student_id')
            
            # Get performance data if not provided
            if not performances:
                perf_data = await self.get_performance_data(student_id) if student_id else {}
            else:
                perf_data = {'performances': performances}
            
            cgpa = student.get('cgpa', student.get('overall_cgpa', 0))
            attendance = student.get('attendance', student.get('attendance_percentage', 75))
            weak_subjects = student.get('weak_subjects', student.get('weaknesses', []))
            
            # CGPA-based recommendations
            if cgpa < 6.0:
                recommendations.append({
                    'type': 'academic',
                    'priority': 1,
                    'title': 'Improve Core Subjects',
                    'description': 'Your CGPA is below 6.0. Focus on improving core subjects.',
                    'actions': [
                        'Join study groups',
                        'Seek faculty mentorship',
                        'Attend extra tutorials'
                    ],
                    'is_viewed': False,
                    'created_at': datetime.utcnow().isoformat()
                })
            elif cgpa < 7.5:
                recommendations.append({
                    'type': 'academic',
                    'priority': 2,
                    'title': 'Target Weak Areas',
                    'description': 'Good progress! Push your CGPA above 7.5 by targeting weak areas.',
                    'actions': [
                        'Identify and focus on weak subjects',
                        'Practice more problems',
                        'Review previous exam papers'
                    ],
                    'is_viewed': False,
                    'created_at': datetime.utcnow().isoformat()
                })
            elif cgpa >= 8.5:
                recommendations.append({
                    'type': 'career',
                    'priority': 3,
                    'title': 'Explore Advanced Opportunities',
                    'description': 'Excellent performance! Consider research or advanced electives.',
                    'actions': [
                        'Apply for research projects',
                        'Consider honors programs',
                        'Explore internship opportunities'
                    ],
                    'is_viewed': False,
                    'created_at': datetime.utcnow().isoformat()
                })
            
            # Attendance recommendations
            if attendance < 75:
                recommendations.append({
                    'type': 'attendance',
                    'priority': 1,
                    'title': 'Improve Attendance',
                    'description': f'Your attendance ({attendance:.1f}%) is below 75%. This may affect your eligibility.',
                    'actions': [
                        'Attend all classes regularly',
                        'Set reminders for classes',
                        'Avoid skipping morning classes'
                    ],
                    'is_viewed': False,
                    'created_at': datetime.utcnow().isoformat()
                })
            
            # Subject-specific recommendations
            if isinstance(weak_subjects, list):
                for subject in weak_subjects[:3]:
                    subject_name = subject if isinstance(subject, str) else subject.get('subject', 'Subject')
                    recommendations.append({
                        'type': 'subject_improvement',
                        'priority': 2,
                        'title': f'Improve {subject_name}',
                        'description': f'Focus on improving your performance in {subject_name}.',
                        'actions': [
                            'Review fundamentals',
                            'Practice more problems',
                            'Seek help from faculty or peers'
                        ],
                        'is_viewed': False,
                        'created_at': datetime.utcnow().isoformat()
                    })
            
            # Prediction-based recommendations
            if predictions:
                risk_score = predictions.get('risk_score', 0)
                if risk_score > 70:
                    recommendations.insert(0, {
                        'type': 'academic',
                        'priority': 0,
                        'title': 'Urgent Attention Required',
                        'description': 'High risk detected. Immediate action recommended.',
                        'actions': [
                            'Meet with academic advisor immediately',
                            'Create a recovery study plan',
                            'Consider tutoring services'
                        ],
                        'is_viewed': False,
                        'created_at': datetime.utcnow().isoformat()
                    })
            
            if not recommendations:
                recommendations.append({
                    'type': 'general',
                    'priority': 3,
                    'title': 'Keep Up The Good Work',
                    'description': 'You are doing well! Consider exploring new opportunities.',
                    'actions': [
                        'Explore advanced topics',
                        'Consider research opportunities',
                        'Build your portfolio'
                    ],
                    'is_viewed': False,
                    'created_at': datetime.utcnow().isoformat()
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return [{
                'type': 'general',
                'priority': 3,
                'title': 'Unable to Generate Recommendations',
                'description': 'Please try again later or contact support.',
                'actions': [],
                'is_viewed': False,
                'created_at': datetime.utcnow().isoformat()
            }]
    
    # ==================== Department Analytics ====================
    
    async def get_department_analytics(
        self,
        department: str,
        semester: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get department-level analytics"""
        try:
            query_conditions = {'student_info.branch': department}
            
            if semester:
                query_conditions['student_info.semester'] = str(semester)
            
            performances = await StudentPerformanceModel.find(query_conditions).to_list()
            
            if not performances:
                return {
                    'department': department,
                    'error': 'No students found',
                    'total_students': 0
                }
            
            cgpas = [p.overall_cgpa for p in performances]
            sgpas = [p.semester_sgpa for p in performances]
            attendances = [p.attendance_average for p in performances]
            
            return {
                'department': department,
                'total_students': len(performances),
                'average_cgpa': float(np.mean(cgpas)),
                'average_sgpa': float(np.mean(sgpas)),
                'average_attendance': float(np.mean(attendances)) if attendances else 0,
                'cgpa_distribution': {
                    'excellent': len([c for c in cgpas if c >= 8.5]),
                    'good': len([c for c in cgpas if 7.0 <= c < 8.5]),
                    'average': len([c for c in cgpas if 5.5 <= c < 7.0]),
                    'poor': len([c for c in cgpas if c < 5.5])
                },
                'at_risk_count': len([c for c in cgpas if c < 6.0]),
                'top_performers': len([c for c in cgpas if c >= 8.5])
            }
            
        except Exception as e:
            logger.error(f"Error getting department analytics: {e}")
            return {'department': department, 'error': str(e)}
    
    # ==================== Weaknesses ====================
    
    async def get_weaknesses(self, student_id: str) -> List[Dict[str, Any]]:
        """Get student weaknesses"""
        try:
            weaknesses = await WeaknessAnalysisResult.find(
                WeaknessAnalysisResult.student_id == student_id
            ).to_list()
            
            return [
                {
                    'id': str(w.id),
                    'subject': w.subject_name or 'Unknown',
                    'subject_code': w.subject_code,
                    'overall_score': w.overall_score,
                    'risk_score': w.overall_risk_score,
                    'priority_areas': w.priority_areas,
                    'key_insights': w.key_insights,
                    'recommended_resources': w.recommended_resources,
                    'study_plan': w.study_plan,
                    'analysis_date': w.analysis_date.isoformat() if w.analysis_date else None
                }
                for w in weaknesses
            ]
            
        except Exception as e:
            logger.error(f"Error getting weaknesses: {e}")
            return []


# Create singleton instance
student_analysis_service = StudentAnalysisService()