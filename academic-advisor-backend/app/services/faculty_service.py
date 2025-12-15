# app/services/faculty_service.py
"""
Faculty Service
Business logic for faculty operations
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio

from app.core.firebase_admin import firebase_manager
from app.services.notification_service import NotificationService
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class FacultyService:
    """
    Service for faculty-related operations
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    async def get_dashboard_data(
        self,
        faculty_id: str,
        department: str
    ) -> Dict[str, Any]:
        """
        Get faculty dashboard data
        """
        try:
            # Get assigned students
            students = await firebase_manager.get_collection(
                collection="students",
                filters=[
                    {'field': 'department', 'operator': '==', 'value': department},
                    {'field': 'faculty_advisor', 'operator': '==', 'value': faculty_id}
                ]
            )
            
            # Calculate statistics
            total_students = len(students)
            at_risk_count = sum(1 for s in students if s.get('risk_level') == 'high')
            avg_cgpa = sum(s.get('cgpa', 0) for s in students) / total_students if students else 0
            
            # Get recent activities
            activities = await firebase_manager.get_collection(
                collection="faculty_activities",
                filters=[{'field': 'faculty_id', 'operator': '==', 'value': faculty_id}],
                order_by='created_at',
                order_direction='desc',
                limit=10
            )
            
            # Get pending tasks
            tasks = await firebase_manager.get_collection(
                collection="faculty_tasks",
                filters=[
                    {'field': 'faculty_id', 'operator': '==', 'value': faculty_id},
                    {'field': 'status', 'operator': '==', 'value': 'pending'}
                ]
            )
            
            return {
                'statistics': {
                    'total_students': total_students,
                    'at_risk_students': at_risk_count,
                    'average_cgpa': round(avg_cgpa, 2),
                    'department': department
                },
                'recent_activities': activities,
                'pending_tasks': tasks,
                'students_summary': [
                    {
                        'id': s['id'],
                        'name': s.get('name'),
                        'cgpa': s.get('cgpa'),
                        'risk_level': s.get('risk_level'),
                        'attendance': s.get('attendance')
                    }
                    for s in students[:10]  # Top 10 for summary
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            return {}
    
    async def get_assigned_students(
        self,
        faculty_id: str,
        department: str,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get students assigned to faculty
        """
        try:
            # Build query filters
            query_filters = [
                {'field': 'department', 'operator': '==', 'value': department}
            ]
            
            # Add additional filters
            if filters.get('risk_level'):
                query_filters.append({
                    'field': 'risk_level',
                    'operator': '==',
                    'value': filters['risk_level']
                })
            
            # Get students
            students = await firebase_manager.get_collection(
                collection="students",
                filters=query_filters,
                offset=skip,
                limit=limit
            )
            
            # Enhance with latest performance
            for student in students:
                # Get latest performance
                performance = await firebase_manager.get_collection(
                    collection=f"students/{student['id']}/performance",
                    order_by='semester',
                    order_direction='desc',
                    limit=1
                )
                
                if performance:
                    student['latest_sgpa'] = performance[0].get('sgpa')
                
                # Get weakness count
                weaknesses = await firebase_manager.get_collection(
                    collection=f"students/{student['id']}/weaknesses",
                    filters=[{'field': 'status', 'operator': '==', 'value': 'active'}]
                )
                
                student['weakness_count'] = len(weaknesses)
            
            return students
            
        except Exception as e:
            logger.error(f"Error getting assigned students: {str(e)}")
            return []
    
    async def verify_student_access(
        self,
        faculty_id: str,
        student_id: str
    ) -> bool:
        """
        Verify if faculty has access to student
        """
        try:
            # Get faculty details
            faculty = await firebase_manager.get_document(
                collection="faculty",
                document_id=faculty_id
            )
            
            # Get student details
            student = await firebase_manager.get_document(
                collection="students",
                document_id=student_id
            )
            
            if not faculty or not student:
                return False
            
            # Check if same department
            if faculty.get('department') != student.get('department'):
                return False
            
            # Check if faculty is advisor
            if student.get('faculty_advisor') == faculty_id:
                return True
            
            # Check if faculty has general access to department students
            if faculty.get('role') in ['hod', 'coordinator']:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying access: {str(e)}")
            return False
    
    async def get_student_analysis(
        self,
        student_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed student analysis for faculty view
        """
        try:
            # Get student data
            student = await firebase_manager.get_document(
                collection="students",
                document_id=student_id,
                subcollections=['performance', 'weaknesses', 'recommendations']
            )
            
            if not student:
                return {}
            
            # Get attendance records
            attendance = await firebase_manager.get_collection(
                collection=f"students/{student_id}/attendance",
                order_by='date',
                order_direction='desc',
                limit=30
            )
            
            # Get assignment submissions
            assignments = await firebase_manager.get_collection(
                collection=f"students/{student_id}/assignments"
            )
            
            # Calculate metrics
            attendance_rate = sum(1 for a in attendance if a.get('present')) / len(attendance) * 100 if attendance else 0
            assignment_completion = sum(1 for a in assignments if a.get('submitted')) / len(assignments) * 100 if assignments else 0
            
            return {
                'student': student,
                'metrics': {
                    'attendance_rate': attendance_rate,
                    'assignment_completion': assignment_completion,
                    'cgpa': student.get('cgpa'),
                    'risk_score': student.get('risk_score')
                },
                'recent_attendance': attendance[:7],  # Last week
                'pending_assignments': [a for a in assignments if not a.get('submitted')]
            }
            
        except Exception as e:
            logger.error(f"Error getting student analysis: {str(e)}")
            return {}
    
    async def create_intervention(
        self,
        faculty_id: str,
        student_id: str,
        intervention_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create intervention for student
        """
        try:
            intervention = {
                'faculty_id': faculty_id,
                'student_id': student_id,
                'type': intervention_data.get('type'),
                'description': intervention_data.get('description'),
                'actions': intervention_data.get('actions', []),
                'target_date': intervention_data.get('target_date'),
                'status': 'active',
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Store intervention
            intervention_id = await firebase_manager.create_document(
                collection="interventions",
                data=intervention
            )
            
            intervention['id'] = intervention_id
            
            # Update student record
            await firebase_manager.update_document(
                collection="students",
                document_id=student_id,
                data={'has_intervention': True}
            )
            
            return intervention
            
        except Exception as e:
            logger.error(f"Error creating intervention: {str(e)}")
            raise
    
    async def notify_student_intervention(
        self,
        student_id: str,
        intervention: Dict[str, Any]
    ):
        """
        Notify student about intervention
        """
        try:
            await self.notification_service.send_notification(
                user_id=student_id,
                notification_type='intervention',
                title='Academic Intervention',
                message=f"Your faculty has created an intervention plan: {intervention.get('description')}",
                data=intervention,
                channels=['database', 'email', 'realtime']
            )
        except Exception as e:
            logger.error(f"Error notifying student: {str(e)}")
    
    async def get_department_analytics(
        self,
        department: str,
        time_range: str
    ) -> Dict[str, Any]:
        """
        Get department-level analytics
        """
        try:
            # Get all students in department
            students = await firebase_manager.get_collection(
                collection="students",
                filters=[{'field': 'department', 'operator': '==', 'value': department}]
            )
            
            # Calculate metrics
            total = len(students)
            
            if total == 0:
                return {'error': 'No students found'}
            
            # Performance distribution
            performance_dist = {
                'excellent': sum(1 for s in students if s.get('cgpa', 0) >= 8.5),
                'good': sum(1 for s in students if 7.0 <= s.get('cgpa', 0) < 8.5),
                'average': sum(1 for s in students if 5.5 <= s.get('cgpa', 0) < 7.0),
                'poor': sum(1 for s in students if s.get('cgpa', 0) < 5.5)
            }
            
            # Risk distribution
            risk_dist = {
                'high': sum(1 for s in students if s.get('risk_level') == 'high'),
                'medium': sum(1 for s in students if s.get('risk_level') == 'medium'),
                'low': sum(1 for s in students if s.get('risk_level') == 'low')
            }
            
            # Batch-wise performance
            batch_performance = {}
            for student in students:
                batch = student.get('batch')
                if batch not in batch_performance:
                    batch_performance[batch] = []
                batch_performance[batch].append(student.get('cgpa', 0))
            
            batch_avg = {
                batch: sum(cgpas) / len(cgpas)
                for batch, cgpas in batch_performance.items()
            }
            
            return {
                'total_students': total,
                'average_cgpa': sum(s.get('cgpa', 0) for s in students) / total,
                'performance_distribution': performance_dist,
                'risk_distribution': risk_dist,
                'batch_performance': batch_avg,
                'attendance_average': sum(s.get('attendance', 0) for s in students) / total
            }
            
        except Exception as e:
            logger.error(f"Error getting department analytics: {str(e)}")
            return {}
    
    async def broadcast_announcement(
        self,
        announcement_id: str,
        department: str
    ):
        """
        Broadcast announcement to department students
        """
        try:
            # Get announcement
            announcement = await firebase_manager.get_document(
                collection="announcements",
                document_id=announcement_id
            )
            
            # Get department students
            students = await firebase_manager.get_collection(
                collection="students",
                filters=[{'field': 'department', 'operator': '==', 'value': department}]
            )
            
            # Send notifications
            student_ids = [s['id'] for s in students]
            
            await self.notification_service.send_bulk_notifications(
                user_ids=student_ids,
                notification_type='announcement',
                title=announcement.get('title'),
                message=announcement.get('content'),
                data={'announcement_id': announcement_id}
            )
            
        except Exception as e:
            logger.error(f"Error broadcasting announcement: {str(e)}")
    
    async def get_schedule(
        self,
        faculty_id: str
    ) -> Dict[str, Any]:
        """
        Get faculty schedule
        """
        try:
            # Get appointments
            appointments = await firebase_manager.get_collection(
                collection="appointments",
                filters=[
                    {'field': 'faculty_id', 'operator': '==', 'value': faculty_id},
                    {'field': 'date', 'operator': '>=', 'value': datetime.utcnow().isoformat()}
                ],
                order_by='date',
                order_direction='asc'
            )
            
            # Get classes
            classes = await firebase_manager.get_collection(
                collection="classes",
                filters=[{'field': 'faculty_id', 'operator': '==', 'value': faculty_id}]
            )
            
            return {
                'appointments': appointments,
                'classes': classes,
                'office_hours': {
                    'monday': '10:00 AM - 12:00 PM',
                    'wednesday': '2:00 PM - 4:00 PM',
                    'friday': '10:00 AM - 12:00 PM'
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting schedule: {str(e)}")
            return {}
    
    async def submit_feedback(
        self,
        faculty_id: str,
        student_id: str,
        feedback: Dict[str, Any]
    ) -> str:
        """
        Submit feedback for student
        """
        try:
            feedback_data = {
                'faculty_id': faculty_id,
                'student_id': student_id,
                'type': feedback.get('type'),
                'rating': feedback.get('rating'),
                'comments': feedback.get('comments'),
                'areas_of_improvement': feedback.get('areas_of_improvement', []),
                'strengths': feedback.get('strengths', []),
                'created_at': datetime.utcnow().isoformat()
            }
            
            feedback_id = await firebase_manager.create_document(
                collection=f"students/{student_id}/feedback",
                data=feedback_data
            )
            
            return feedback_id
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            raise