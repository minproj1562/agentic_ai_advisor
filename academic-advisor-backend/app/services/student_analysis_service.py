"""
Student Analysis Service Layer
Business logic for processing student data and generating insights
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc, asc
import pandas as pd
import numpy as np
from collections import defaultdict
import json
import redis
from concurrent.futures import ThreadPoolExecutor
import logging

from app.models.student_analysis import Student, Performance, Weakness, Recommendation, AnalysisHistory
from app.services.ml_performance_analysis import MLPerformanceAnalyzer
from app.core.cache import CacheManager
from app.core.exceptions import ServiceException, DataNotFoundException
from app.core.metrics import track_service_call
from app.utils.data_validator import DataValidator
from app.utils.formatters import DataFormatter

logger = logging.getLogger(__name__)

class StudentAnalysisService:
    """
    Enterprise-level service for student analysis operations
    """
    
    def __init__(self):
        self.ml_analyzer = MLPerformanceAnalyzer()
        self.cache_manager = CacheManager()
        self.data_validator = DataValidator()
        self.formatter = DataFormatter()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
    @track_service_call
    async def get_students_analysis(
        self,
        db: Session,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort_by: str = 'cgpa',
        sort_order: str = 'desc'
    ) -> List[Dict[str, Any]]:
        """
        Get comprehensive analysis for multiple students with filtering and sorting
        """
        try:
            # Build query
            query = db.query(Student).filter(Student.is_active == True)
            
            # Apply filters
            if filters.get('department'):
                query = query.filter(Student.department == filters['department'])
            
            if filters.get('cgpa_min') is not None:
                query = query.filter(Student.cgpa >= filters['cgpa_min'])
            
            if filters.get('cgpa_max') is not None:
                query = query.filter(Student.cgpa <= filters['cgpa_max'])
            
            # Apply sorting
            if sort_order == 'desc':
                query = query.order_by(desc(getattr(Student, sort_by)))
            else:
                query = query.order_by(asc(getattr(Student, sort_by)))
            
            # Execute query with pagination
            students = query.offset(skip).limit(limit).all()
            
            # Process students in parallel
            tasks = []
            for student in students:
                tasks.append(self._process_student_analysis(db, student, filters.get('weakness_threshold', 0.6)))
            
            # Gather results
            results = await asyncio.gather(*tasks)
            
            # Filter out None results
            results = [r for r in results if r is not None]
            
            # Apply post-processing
            results = self._apply_post_processing(results)
            
            logger.info(f"Processed analysis for {len(results)} students")
            return results
            
        except Exception as e:
            logger.error(f"Error in get_students_analysis: {str(e)}")
            raise ServiceException(f"Failed to fetch student analysis: {str(e)}")
    
    async def _process_student_analysis(
        self,
        db: Session,
        student: Student,
        weakness_threshold: float
    ) -> Dict[str, Any]:
        """
        Process individual student analysis
        """
        try:
            # Get latest performance
            latest_performance = db.query(Performance)\
                .filter(Performance.student_id == student.id)\
                .order_by(desc(Performance.semester))\
                .first()
            
            # Get SGPA trend
            performances = db.query(Performance)\
                .filter(Performance.student_id == student.id)\
                .order_by(Performance.semester)\
                .all()
            
            sgpa_trend = [p.sgpa for p in performances]
            
            # Get weaknesses
            weaknesses = db.query(Weakness)\
                .filter(
                    and_(
                        Weakness.student_id == student.id,
                        Weakness.status == 'active'
                    )
                )\
                .order_by(desc(Weakness.priority))\
                .limit(5)\
                .all()
            
            # Calculate risk score
            risk_score = await self._calculate_risk_score(student, performances, weaknesses)
            
            # Get recommendations count
            recommendations_count = db.query(func.count(Recommendation.id))\
                .filter(
                    and_(
                        Recommendation.student_id == student.id,
                        Recommendation.is_viewed == False
                    )
                )\
                .scalar()
            
            # Format weakness data
            weakness_data = []
            for w in weaknesses:
                if w.gap_percentage and w.gap_percentage > weakness_threshold * 100:
                    weakness_data.append({
                        'subject': w.subject,
                        'topic': w.topic,
                        'severity': w.severity,
                        'gap': w.gap_percentage,
                        'priority': w.priority
                    })
            
            # Calculate improvement trend
            improvement_trend = self._calculate_improvement_trend(performances)
            
            # Prepare response
            analysis = {
                'student_id': student.student_id,
                'name': student.name,
                'department': student.department,
                'batch': student.batch,
                'current_semester': student.current_semester,
                'cgpa': float(student.cgpa),
                'sgpa_trend': sgpa_trend,
                'latest_sgpa': latest_performance.sgpa if latest_performance else 0.0,
                'attendance': float(student.attendance_percentage),
                'weaknesses': weakness_data,
                'weakness_count': len(weakness_data),
                'risk_score': risk_score,
                'risk_level': student.risk_level,
                'improvement_trend': improvement_trend,
                'recommendations_pending': recommendations_count,
                'profile_completeness': student.full_profile_score,
                'last_updated': student.updated_at.isoformat() if student.updated_at else None,
                'metadata': {
                    'total_credits': student.total_credits,
                    'has_warnings': student.has_warnings,
                    'analysis_version': '2.0'
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error processing student {student.id}: {str(e)}")
            return None
    
    async def _calculate_risk_score(
        self,
        student: Student,
        performances: List[Performance],
        weaknesses: List[Weakness]
    ) -> float:
        """
        Calculate comprehensive risk score for a student
        """
        risk_score = 0.0
        
        # CGPA component (30%)
        if student.cgpa < 5.0:
            risk_score += 30
        elif student.cgpa < 6.0:
            risk_score += 20
        elif student.cgpa < 7.0:
            risk_score += 10
        
        # Attendance component (20%)
        if student.attendance_percentage < 65:
            risk_score += 20
        elif student.attendance_percentage < 75:
            risk_score += 10
        
        # Performance trend component (25%)
        if len(performances) >= 2:
            recent_trend = performances[-1].sgpa - performances[-2].sgpa
            if recent_trend < -0.5:
                risk_score += 25
            elif recent_trend < 0:
                risk_score += 15
        
        # Weakness severity component (25%)
        critical_weaknesses = sum(1 for w in weaknesses if w.severity == 'critical')
        high_weaknesses = sum(1 for w in weaknesses if w.severity == 'high')
        
        risk_score += min(critical_weaknesses * 10, 15)
        risk_score += min(high_weaknesses * 5, 10)
        
        return min(risk_score, 100.0)
    
    def _calculate_improvement_trend(self, performances: List[Performance]) -> str:
        """
        Calculate improvement trend from performance history
        """
        if len(performances) < 2:
            return 'stable'
        
        sgpas = [p.sgpa for p in performances]
        
        # Calculate linear regression slope
        x = np.arange(len(sgpas))
        slope = np.polyfit(x, sgpas, 1)[0]
        
        if slope > 0.1:
            return 'improving'
        elif slope < -0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _apply_post_processing(self, results: List[Dict]) -> List[Dict]:
        """
        Apply post-processing to analysis results
        """
        # Calculate percentiles for relative ranking
        if results:
            cgpas = [r['cgpa'] for r in results]
            risk_scores = [r['risk_score'] for r in results]
            
            cgpa_percentiles = np.percentile(cgpas, [25, 50, 75])
            risk_percentiles = np.percentile(risk_scores, [25, 50, 75])
            
            for result in results:
                # Add percentile ranks
                result['cgpa_percentile'] = self._get_percentile_rank(result['cgpa'], cgpa_percentiles)
                result['risk_percentile'] = self._get_percentile_rank(result['risk_score'], risk_percentiles)
                
                # Add performance category
                if result['cgpa'] >= 8.5:
                    result['performance_category'] = 'excellent'
                elif result['cgpa'] >= 7.0:
                    result['performance_category'] = 'good'
                elif result['cgpa'] >= 5.5:
                    result['performance_category'] = 'average'
                else:
                    result['performance_category'] = 'needs_improvement'
        
        return results
    
    def _get_percentile_rank(self, value: float, percentiles: List[float]) -> str:
        """
        Get percentile rank category
        """
        if value <= percentiles[0]:
            return 'bottom_25'
        elif value <= percentiles[1]:
            return 'lower_middle'
        elif value <= percentiles[2]:
            return 'upper_middle'
        else:
            return 'top_25'
    
    @track_service_call
    async def get_student_by_id(self, db: Session, student_id: str) -> Student:
        """
        Get student by ID with caching
        """
        # Check cache first
        cache_key = f"student:{student_id}"
        cached_data = self.cache_manager.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Query database
        student = db.query(Student)\
            .filter(Student.student_id == student_id)\
            .options(
                joinedload(Student.performances),
                joinedload(Student.weaknesses),
                joinedload(Student.recommendations)
            )\
            .first()
        
        if not student:
            raise DataNotFoundException(f"Student {student_id} not found")
        
        # Cache for 5 minutes
        self.cache_manager.set(cache_key, student, ttl=300)
        
        return student
    
    @track_service_call
    async def get_performance_data(
        self,
        db: Session,
        student_id: str,
        time_range: str = 'all'
    ) -> Dict[str, Any]:
        """
        Get comprehensive performance data for a student
        """
        try:
            # Get student
            student = await self.get_student_by_id(db, student_id)
            
            # Build performance query
            query = db.query(Performance).filter(Performance.student_id == student.id)
            
            # Apply time range filter
            if time_range == 'current':
                query = query.filter(Performance.semester == student.current_semester)
            elif time_range == 'last_year':
                one_year_ago = datetime.utcnow() - timedelta(days=365)
                query = query.filter(Performance.created_at >= one_year_ago)
            
            performances = query.order_by(Performance.semester).all()
            
            if not performances:
                return {
                    'sgpa_trend': [],
                    'subject_performance': {},
                    'attendance_trend': [],
                    'grade_distribution': {}
                }
            
            # Process performance data
            sgpa_trend = []
            attendance_trend = []
            all_grades = defaultdict(int)
            subject_scores = defaultdict(list)
            
            for perf in performances:
                sgpa_trend.append({
                    'semester': perf.semester,
                    'sgpa': perf.sgpa,
                    'credits': perf.credits_earned,
                    'year': perf.academic_year
                })
                
                attendance_trend.append({
                    'semester': perf.semester,
                    'attendance': perf.attendance_percentage,
                    'assignments': perf.completion_rate
                })
                
                # Process grades
                for grade in perf.grades.values():
                    all_grades[grade] += 1
                
                # Process subject scores
                for subject_data in perf.subjects:
                    subject_scores[subject_data['code']].append({
                        'semester': perf.semester,
                        'score': subject_data.get('score', 0),
                        'grade': subject_data.get('grade', 'NA')
                    })
            
            # Calculate statistics
            sgpa_values = [p.sgpa for p in performances]
            statistics = {
                'mean_sgpa': np.mean(sgpa_values),
                'std_sgpa': np.std(sgpa_values),
                'min_sgpa': np.min(sgpa_values),
                'max_sgpa': np.max(sgpa_values),
                'trend_direction': 'up' if len(sgpa_values) > 1 and sgpa_values[-1] > sgpa_values[-2] else 'down'
            }
            
            # Identify consistent performers
            consistent_subjects = []
            weak_subjects = []
            
            for subject, scores in subject_scores.items():
                avg_score = np.mean([s['score'] for s in scores])
                if avg_score >= 80:
                    consistent_subjects.append({
                        'subject': subject,
                        'average': avg_score,
                        'category': 'strength'
                    })
                elif avg_score < 60:
                    weak_subjects.append({
                        'subject': subject,
                        'average': avg_score,
                        'category': 'weakness'
                    })
            
            return {
                'sgpa_trend': sgpa_trend,
                'attendance_trend': attendance_trend,
                'grade_distribution': dict(all_grades),
                'subject_performance': dict(subject_scores),
                'statistics': statistics,
                'consistent_subjects': consistent_subjects,
                'weak_subjects': weak_subjects,
                'total_semesters': len(performances),
                'latest_semester': performances[-1].semester if performances else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting performance data: {str(e)}")
            raise ServiceException(f"Failed to get performance data: {str(e)}")
    
    @track_service_call
    async def generate_recommendations(
        self,
        student: Student,
        performance_data: Dict[str, Any],
        predictions: Dict[str, Any]
    ) -> List[str]:
        """
        Generate personalized recommendations based on analysis
        """
        recommendations = []
        
        try:
            # Academic performance recommendations
            if student.cgpa < 6.0:
                recommendations.append(
                    "Focus on improving core subjects. Consider joining study groups or seeking faculty mentorship."
                )
            
            # Attendance recommendations
            if student.attendance_percentage < 75:
                recommendations.append(
                    f"Your attendance is {student.attendance_percentage}%. Aim for at least 75% to avoid academic penalties."
                )
            
            # Subject-specific recommendations
            weak_subjects = performance_data.get('weak_subjects', [])
            for subject in weak_subjects[:3]:  # Top 3 weak subjects
                recommendations.append(
                    f"Strengthen your understanding in {subject['subject']} (Avg: {subject['average']:.1f}%). "
                    f"Consider additional tutorials or online resources."
                )
            
            # Trend-based recommendations
            if performance_data.get('statistics', {}).get('trend_direction') == 'down':
                recommendations.append(
                    "Your performance shows a declining trend. Schedule a meeting with your academic advisor."
                )
            
            # ML-based recommendations
            if predictions:
                risk_score = predictions.get('risk_score', 0)
                if risk_score > 70:
                    recommendations.append(
                        "High risk detected. Immediate intervention recommended. Contact student counseling services."
                    )
                
                # Weakness-specific recommendations
                for weakness in predictions.get('weaknesses', [])[:2]:
                    recommendations.append(
                        f"Work on {weakness['subject']} - {weakness.get('topic', 'General concepts')}. "
                        f"Recommended resources: {', '.join(weakness.get('resources', ['Textbook', 'Online tutorials']))}"
                    )
            
            # Career-oriented recommendations
            if student.current_semester >= 5:
                recommendations.append(
                    "Start building your professional profile. Update your LinkedIn and work on internship applications."
                )
            
            # Skill recommendations based on interests
            if student.interests:
                recommendations.append(
                    f"Based on your interests in {', '.join(student.interests[:2])}, "
                    f"consider taking relevant electives or online certifications."
                )
            
            # Store recommendations in database
            await self._store_recommendations(student.id, recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Unable to generate specific recommendations at this time. Please consult your advisor."]
    
    async def _store_recommendations(self, student_id: str, recommendations: List[str]):
        """
        Store generated recommendations in database
        """
        # Implementation for storing recommendations
        pass
    
    @track_service_call
    async def get_department_trends(
        self,
        db: Session,
        department: str,
        semester: Optional[int],
        metric: str
    ) -> Dict[str, Any]:
        """
        Get aggregated trends for a department
        """
        try:
            # Base query
            query = db.query(Student).filter(Student.department == department)
            
            if semester:
                query = query.filter(Student.current_semester == semester)
            
            students = query.all()
            
            if not students:
                return {'error': 'No students found for the specified criteria'}
            
            # Calculate metrics based on type
            if metric == 'cgpa':
                data = self._calculate_cgpa_trends(students, db)
            elif metric == 'attendance':
                data = self._calculate_attendance_trends(students)
            elif metric == 'assignments':
                data = self._calculate_assignment_trends(students, db)
            else:
                data = {}
            
            # Add statistical analysis
            values = [d['value'] for d in data.get('trend', []) if 'value' in d]
            
            if values:
                data['statistics'] = {
                    'mean': np.mean(values),
                    'median': np.median(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'q1': np.percentile(values, 25),
                    'q3': np.percentile(values, 75)
                }
            
            # Add comparison with other departments
            data['comparison'] = await self._get_department_comparison(db, department, metric)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting department trends: {str(e)}")
            raise ServiceException(f"Failed to get department trends: {str(e)}")
    
    def _calculate_cgpa_trends(self, students: List[Student], db: Session) -> Dict[str, Any]:
        """
        Calculate CGPA trends for students
        """
        # Group by batch
        batch_wise = defaultdict(list)
        for student in students:
            batch_wise[student.batch].append(student.cgpa)
        
        trend = []
        for batch, cgpas in sorted(batch_wise.items()):
            trend.append({
                'batch': batch,
                'value': np.mean(cgpas),
                'count': len(cgpas),
                'min': np.min(cgpas),
                'max': np.max(cgpas)
            })
        
        # Calculate semester-wise progression
        semester_progression = []
        for sem in range(1, 9):
            performances = db.query(Performance)\
                .join(Student)\
                .filter(
                    and_(
                        Student.department == students[0].department,
                        Performance.semester == sem
                    )
                )\
                .all()
            
            if performances:
                sgpas = [p.sgpa for p in performances]
                semester_progression.append({
                    'semester': sem,
                    'average_sgpa': np.mean(sgpas),
                    'student_count': len(sgpas)
                })
        
        return {
            'trend': trend,
            'semester_progression': semester_progression,
            'current_average': np.mean([s.cgpa for s in students]),
            'top_performers': len([s for s in students if s.cgpa >= 8.5]),
            'at_risk': len([s for s in students if s.cgpa < 6.0])
        }
    
    def _calculate_attendance_trends(self, students: List[Student]) -> Dict[str, Any]:
        """
        Calculate attendance trends
        """
        attendance_ranges = {
            '90-100': 0,
            '75-89': 0,
            '65-74': 0,
            'Below 65': 0
        }
        
        for student in students:
            att = student.attendance_percentage
            if att >= 90:
                attendance_ranges['90-100'] += 1
            elif att >= 75:
                attendance_ranges['75-89'] += 1
            elif att >= 65:
                attendance_ranges['65-74'] += 1
            else:
                attendance_ranges['Below 65'] += 1
        
        trend = [
            {'range': range_name, 'value': count}
            for range_name, count in attendance_ranges.items()
        ]
        
        return {
            'trend': trend,
            'average_attendance': np.mean([s.attendance_percentage for s in students]),
            'below_threshold': len([s for s in students if s.attendance_percentage < 75])
        }
    
    def _calculate_assignment_trends(self, students: List[Student], db: Session) -> Dict[str, Any]:
        """
        Calculate assignment completion trends
        """
        # Get latest performance for each student
        completion_rates = []
        
        for student in students:
            latest_perf = db.query(Performance)\
                .filter(Performance.student_id == student.id)\
                .order_by(desc(Performance.semester))\
                .first()
            
            if latest_perf and latest_perf.assignments_total > 0:
                completion_rate = (latest_perf.assignments_completed / latest_perf.assignments_total) * 100
                completion_rates.append(completion_rate)
        
        if not completion_rates:
            return {'trend': [], 'average_completion': 0}
        
        # Group into ranges
        ranges = {
            '90-100%': len([r for r in completion_rates if r >= 90]),
            '70-89%': len([r for r in completion_rates if 70 <= r < 90]),
            '50-69%': len([r for r in completion_rates if 50 <= r < 70]),
            'Below 50%': len([r for r in completion_rates if r < 50])
        }
        
        trend = [
            {'range': range_name, 'value': count}
            for range_name, count in ranges.items()
        ]
        
        return {
            'trend': trend,
            'average_completion': np.mean(completion_rates),
            'high_performers': len([r for r in completion_rates if r >= 90])
        }
    
    async def _get_department_comparison(
        self,
        db: Session,
        department: str,
        metric: str
    ) -> Dict[str, Any]:
        """
        Compare department with others
        """
        all_departments = ['CS', 'ECE', 'MECH', 'CIVIL', 'EEE']
        comparison = {}
        
        for dept in all_departments:
            students = db.query(Student).filter(Student.department == dept).all()
            
            if students:
                if metric == 'cgpa':
                    value = np.mean([s.cgpa for s in students])
                elif metric == 'attendance':
                    value = np.mean([s.attendance_percentage for s in students])
                else:
                    value = 0
                
                comparison[dept] = {
                    'value': value,
                    'student_count': len(students),
                    'is_current': dept == department
                }
        
        return comparison
    
    @track_service_call
    async def bulk_analyze_students(
        self,
        db: Session,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform bulk analysis on multiple students
        """
        try:
            start_time = datetime.utcnow()
            
            # Get students based on criteria
            query = db.query(Student)
            
            if request.get('department'):
                query = query.filter(Student.department == request['department'])
            
            if request.get('semester'):
                query = query.filter(Student.current_semester == request['semester'])
            
            students = query.all()
            total_students = len(students)
            
            # Process in batches
            batch_size = 50
            analyzed_students = []
            failed_students = []
            
            for i in range(0, total_students, batch_size):
                batch = students[i:i+batch_size]
                
                # Process batch in parallel
                tasks = []
                for student in batch:
                    tasks.append(self._analyze_single_student(db, student))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for student, result in zip(batch, results):
                    if isinstance(result, Exception):
                        failed_students.append({
                            'student_id': student.student_id,
                            'error': str(result)
                        })
                    else:
                        analyzed_students.append(result)
                
                # Update progress
                progress = ((i + len(batch)) / total_students) * 100
                self.redis_client.set(f"bulk_progress:{request.get('job_id')}", progress)
            
            # Calculate aggregated metrics
            aggregated_metrics = self._calculate_aggregated_metrics(analyzed_students)
            
            # Generate insights
            insights = await self._generate_bulk_insights(aggregated_metrics)
            
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            return {
                'total_students': total_students,
                'analyzed_count': len(analyzed_students),
                'failed_count': len(failed_students),
                'execution_time': execution_time,
                'aggregated_metrics': aggregated_metrics,
                'insights': insights,
                'failed_students': failed_students[:10],  # Return first 10 failures
                'timestamp': end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Bulk analysis failed: {str(e)}")
            raise ServiceException(f"Bulk analysis failed: {str(e)}")
    
    async def _analyze_single_student(
        self,
        db: Session,
        student: Student
    ) -> Dict[str, Any]:
        """
        Analyze a single student for bulk processing
        """
        try:
            # Get performance data
            performances = db.query(Performance)\
                .filter(Performance.student_id == student.id)\
                .all()
            
            # Get weaknesses
            weaknesses = db.query(Weakness)\
                .filter(Weakness.student_id == student.id)\
                .all()
            
            # Run ML analysis
            ml_predictions = await self.ml_analyzer.quick_predict(student, performances)
            
            # Store analysis history
            history = AnalysisHistory(
                student_id=student.id,
                analysis_type='bulk',
                results=ml_predictions,
                model_name='XGBoost',
                model_version=self.ml_analyzer.model_version,
                status='completed'
            )
            db.add(history)
            db.commit()
            
            return {
                'student_id': student.student_id,
                'cgpa': student.cgpa,
                'risk_score': ml_predictions.get('risk_score', 0),
                'weaknesses_count': len(weaknesses),
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze student {student.id}: {str(e)}")
            raise
    
    def _calculate_aggregated_metrics(
        self,
        analyzed_students: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate aggregated metrics from analyzed students
        """
        if not analyzed_students:
            return {}
        
        cgpas = [s['cgpa'] for s in analyzed_students]
        risk_scores = [s['risk_score'] for s in analyzed_students]
        
        return {
            'cgpa': {
                'mean': np.mean(cgpas),
                'median': np.median(cgpas),
                'std': np.std(cgpas),
                'min': np.min(cgpas),
                'max': np.max(cgpas)
            },
            'risk': {
                'mean': np.mean(risk_scores),
                'high_risk_count': len([r for r in risk_scores if r > 70]),
                'medium_risk_count': len([r for r in risk_scores if 40 <= r <= 70]),
                'low_risk_count': len([r for r in risk_scores if r < 40])
            },
            'distribution': {
                'excellent': len([c for c in cgpas if c >= 8.5]),
                'good': len([c for c in cgpas if 7.0 <= c < 8.5]),
                'average': len([c for c in cgpas if 5.5 <= c < 7.0]),
                'poor': len([c for c in cgpas if c < 5.5])
            }
        }
    
    async def _generate_bulk_insights(
        self,
        metrics: Dict[str, Any]
    ) -> List[str]:
        """
        Generate insights from bulk analysis
        """
        insights = []
        
        if metrics.get('cgpa'):
            avg_cgpa = metrics['cgpa']['mean']
            insights.append(f"Average CGPA: {avg_cgpa:.2f}")
            
            if avg_cgpa < 6.0:
                insights.append("Department average is below acceptable threshold. Intervention needed.")
        
        if metrics.get('risk'):
            high_risk = metrics['risk']['high_risk_count']
            if high_risk > 0:
                insights.append(f"{high_risk} students at high risk. Immediate attention required.")
        
        if metrics.get('distribution'):
            poor_performers = metrics['distribution']['poor']
            total = sum(metrics['distribution'].values())
            if poor_performers / total > 0.3:
                insights.append("Over 30% students performing poorly. Review teaching methods.")
        
        return insights
    
    @track_service_call
    async def export_analysis_data(
        self,
        db: Session,
        department: Optional[str],
        format: str
    ):
        """
        Export analysis data in various formats
        """
        try:
            # Get data
            query = db.query(Student)
            if department:
                query = query.filter(Student.department == department)
            
            students = query.all()
            
            # Prepare data for export
            export_data = []
            for student in students:
                # Get latest performance
                latest_perf = db.query(Performance)\
                    .filter(Performance.student_id == student.id)\
                    .order_by(desc(Performance.semester))\
                    .first()
                
                export_data.append({
                    'Student ID': student.student_id,
                    'Name': student.name,
                    'Department': student.department,
                    'Batch': student.batch,
                    'CGPA': student.cgpa,
                    'Current Semester': student.current_semester,
                    'Attendance %': student.attendance_percentage,
                    'Latest SGPA': latest_perf.sgpa if latest_perf else 'N/A',
                    'Risk Level': student.risk_level,
                    'Last Updated': student.updated_at.isoformat() if student.updated_at else ''
                })
            
            # Convert to requested format
            if format == 'csv':
                import csv
                import io
                
                output = io.StringIO()
                if export_data:
                    writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
                    writer.writeheader()
                    writer.writerows(export_data)
                
                output.seek(0)
                return output
                
            elif format == 'excel':
                import io
                df = pd.DataFrame(export_data)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Student Analysis', index=False)
                output.seek(0)
                return output
                
            else:  # JSON
                return export_data
                
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            raise ServiceException(f"Export failed: {str(e)}")
    
    async def get_real_time_metrics(
        self,
        db: Session,
        student_id: str
    ) -> Dict[str, Any]:
        """
        Get real-time metrics for WebSocket updates
        """
        try:
            student = await self.get_student_by_id(db, student_id)
            
            # Get latest metrics
            latest_analysis = db.query(AnalysisHistory)\
                .filter(AnalysisHistory.student_id == student.id)\
                .order_by(desc(AnalysisHistory.analysis_date))\
                .first()
            
            return {
                'student_id': student_id,
                'current_cgpa': student.cgpa,
                'attendance': student.attendance_percentage,
                'risk_level': student.risk_level,
                'last_analysis': latest_analysis.analysis_date.isoformat() if latest_analysis else None,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {str(e)}")
            return {'error': str(e)}