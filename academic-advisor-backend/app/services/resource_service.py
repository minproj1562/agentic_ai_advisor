# app/services/resource_service.py
"""
Resource Service
Educational resources management
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import httpx
from googleapiclient.discovery import build

from app.config import settings
from app.core.firebase_admin import firebase_manager
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class ResourceService:
    """
    Service for managing educational resources
    """
    
    def __init__(self):
        self.youtube_api_key = settings.YOUTUBE_API_KEY
        self.youtube_service = None
        if self.youtube_api_key:
            self.youtube_service = build('youtube', 'v3', developerKey=self.youtube_api_key)
    
    async def get_library_resources(
        self,
        subject: Optional[str] = None,
        resource_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get digital library resources
        """
        try:
            # Build filters
            filters = []
            
            if subject:
                filters.append({'field': 'subject', 'operator': '==', 'value': subject})
            
            if resource_type:
                filters.append({'field': 'type', 'operator': '==', 'value': resource_type})
            
            # Get resources
            resources = await firebase_manager.get_collection(
                collection="library_resources",
                filters=filters,
                order_by='rating',
                order_direction='desc',
                offset=skip,
                limit=limit
            )
            
            # Enhance with metadata
            for resource in resources:
                # Get view count
                views = await firebase_manager.get_document(
                    collection=f"resource_analytics/{resource['id']}/views",
                    document_id='count'
                )
                resource['view_count'] = views.get('total', 0) if views else 0
                
                # Get ratings
                ratings = await firebase_manager.get_collection(
                    collection=f"resources/{resource['id']}/ratings"
                )
                
                if ratings:
                    avg_rating = sum(r.get('rating', 0) for r in ratings) / len(ratings)
                    resource['average_rating'] = avg_rating
                    resource['rating_count'] = len(ratings)
            
            return resources
            
        except Exception as e:
            logger.error(f"Error getting library resources: {str(e)}")
            return []
    
    async def create_resource(
        self,
        title: str,
        description: str,
        url: str,
        resource_type: str,
        subject: str,
        uploaded_by: str,
        department: str
    ) -> str:
        """
        Create new resource
        """
        try:
            resource_data = {
                'title': title,
                'description': description,
                'url': url,
                'type': resource_type,
                'subject': subject,
                'uploaded_by': uploaded_by,
                'department': department,
                'created_at': datetime.utcnow().isoformat(),
                'is_approved': False,  # Requires approval
                'view_count': 0,
                'download_count': 0,
                'rating': 0.0
            }
            
            resource_id = await firebase_manager.create_document(
                collection="library_resources",
                data=resource_data
            )
            
            # Create analytics entry
            await firebase_manager.create_document(
                collection=f"resource_analytics/{resource_id}/views",
                document_id='count',
                data={'total': 0}
            )
            
            return resource_id
            
        except Exception as e:
            logger.error(f"Error creating resource: {str(e)}")
            raise
    
    async def search_youtube_resources(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search YouTube for educational videos
        """
        try:
            if not self.youtube_service:
                return []
            
            # Search for educational videos
            search_response = self.youtube_service.search().list(
                q=f"{query} tutorial education",
                part='id,snippet',
                maxResults=max_results,
                type='video',
                videoCategoryId='27',  # Education category
                relevanceLanguage='en',
                safeSearch='strict'
            ).execute()
            
            videos = []
            
            for item in search_response.get('items', []):
                video_id = item['id']['videoId']
                
                # Get additional video details
                video_details = self.youtube_service.videos().list(
                    part='contentDetails,statistics',
                    id=video_id
                ).execute()
                
                if video_details['items']:
                    details = video_details['items'][0]
                    
                    videos.append({
                        'video_id': video_id,
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                        'channel': item['snippet']['channelTitle'],
                        'published_at': item['snippet']['publishedAt'],
                        'duration': self._parse_duration(details['contentDetails']['duration']),
                        'view_count': details['statistics'].get('viewCount', 0),
                        'like_count': details['statistics'].get('likeCount', 0),
                        'url': f"https://www.youtube.com/watch?v={video_id}"
                    })
            
            return videos
            
        except Exception as e:
            logger.error(f"Error searching YouTube: {str(e)}")
            return []
    
    def _parse_duration(self, duration: str) -> str:
        """
        Parse YouTube duration format (PT15M33S) to readable format
        """
        import re
        
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if match:
            hours = match.group(1) or '0'
            minutes = match.group(2) or '0'
            seconds = match.group(3) or '0'
            
            if int(hours) > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m {seconds}s"
        
        return duration
    
    async def get_practice_problems(
        self,
        subject: str,
        difficulty: Optional[str] = None,
        topic: Optional[str] = None,
        student_level: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get practice problems
        """
        try:
            # Build filters
            filters = [
                {'field': 'subject', 'operator': '==', 'value': subject},
                {'field': 'level', 'operator': '<=', 'value': student_level + 1}
            ]
            
            if difficulty:
                filters.append({'field': 'difficulty', 'operator': '==', 'value': difficulty})
            
            if topic:
                filters.append({'field': 'topic', 'operator': '==', 'value': topic})
            
            # Get problems
            problems = await firebase_manager.get_collection(
                collection="practice_problems",
                filters=filters,
                limit=20
            )
            
            # Add solution hints based on difficulty
            for problem in problems:
                if problem.get('difficulty') == 'hard':
                    problem['hints_available'] = 3
                elif problem.get('difficulty') == 'medium':
                    problem['hints_available'] = 2
                else:
                    problem['hints_available'] = 1
                
                # Hide full solution initially
                problem['solution_locked'] = True
            
            return problems
            
        except Exception as e:
            logger.error(f"Error getting practice problems: {str(e)}")
            return []
    
    async def evaluate_solution(
        self,
        problem_id: str,
        student_id: str,
        solution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate student's solution to practice problem
        """
        try:
            # Get problem
            problem = await firebase_manager.get_document(
                collection="practice_problems",
                document_id=problem_id
            )
            
            if not problem:
                return {'error': 'Problem not found'}
            
            # Evaluate based on problem type
            result = {}
            
            if problem.get('type') == 'multiple_choice':
                correct_answer = problem.get('correct_answer')
                student_answer = solution.get('answer')
                
                result['correct'] = student_answer == correct_answer
                result['score'] = 100 if result['correct'] else 0
                
            elif problem.get('type') == 'coding':
                # Run test cases
                result = await self._evaluate_code(
                    problem,
                    solution.get('code')
                )
                
            elif problem.get('type') == 'numerical':
                correct_value = float(problem.get('answer'))
                student_value = float(solution.get('answer'))
                tolerance = problem.get('tolerance', 0.01)
                
                result['correct'] = abs(correct_value - student_value) <= tolerance
                result['score'] = 100 if result['correct'] else 0
            
            # Store attempt
            await firebase_manager.create_document(
                collection=f"students/{student_id}/problem_attempts",
                data={
                    'problem_id': problem_id,
                    'solution': solution,
                    'result': result,
                    'attempted_at': datetime.utcnow().isoformat()
                }
            )
            
            # Update student statistics
            await self._update_problem_statistics(student_id, problem_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating solution: {str(e)}")
            return {'error': str(e)}
    
    async def _evaluate_code(
        self,
        problem: Dict[str, Any],
        code: str
    ) -> Dict[str, Any]:
        """
        Evaluate coding solution
        """
        # This would integrate with a code execution service
        # For now, return mock result
        
        test_cases = problem.get('test_cases', [])
        passed = 0
        total = len(test_cases)
        
        # Mock evaluation
        import random
        passed = random.randint(0, total)
        
        return {
            'correct': passed == total,
            'score': (passed / total * 100) if total > 0 else 0,
            'test_results': {
                'passed': passed,
                'total': total
            }
        }
    
    async def _update_problem_statistics(
        self,
        student_id: str,
        problem_id: str,
        result: Dict[str, Any]
    ):
        """
        Update problem-solving statistics
        """
        try:
            # Update student stats
            stats = await firebase_manager.get_document(
                collection=f"students/{student_id}/statistics",
                document_id='problems'
            )
            
            if not stats:
                stats = {
                    'total_attempted': 0,
                    'total_solved': 0,
                    'by_subject': {}
                }
            
            stats['total_attempted'] += 1
            if result.get('correct'):
                stats['total_solved'] += 1
            
            await firebase_manager.update_document(
                collection=f"students/{student_id}/statistics",
                document_id='problems',
                data=stats
            )
            
        except Exception as e:
            logger.error(f"Error updating statistics: {str(e)}")
    
    async def get_course_materials(
        self,
        course_id: str,
        user_role: str
    ) -> Dict[str, Any]:
        """
        Get study materials for a course
        """
        try:
            # Get course details
            course = await firebase_manager.get_document(
                collection="courses",
                document_id=course_id
            )
            
            if not course:
                return {'error': 'Course not found'}
            
            # Get materials based on role
            materials = {
                'lectures': [],
                'assignments': [],
                'resources': [],
                'announcements': []
            }
            
            # Get lectures
            materials['lectures'] = await firebase_manager.get_collection(
                collection=f"courses/{course_id}/lectures",
                order_by='week_number',
                order_direction='asc'
            )
            
            # Get assignments
            materials['assignments'] = await firebase_manager.get_collection(
                collection=f"courses/{course_id}/assignments",
                order_by='due_date',
                order_direction='asc'
            )
            
            # Get additional resources
            materials['resources'] = await firebase_manager.get_collection(
                collection=f"courses/{course_id}/resources"
            )
            
            # Get announcements
            materials['announcements'] = await firebase_manager.get_collection(
                collection=f"courses/{course_id}/announcements",
                order_by='created_at',
                order_direction='desc',
                limit=5
            )
            
            # Add instructor materials if faculty
            if user_role in ['faculty', 'admin']:
                materials['instructor_notes'] = await firebase_manager.get_collection(
                    collection=f"courses/{course_id}/instructor_notes"
                )
            
            return materials
            
        except Exception as e:
            logger.error(f"Error getting course materials: {str(e)}")
            return {}
    
    async def get_resource_for_download(
        self,
        resource_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get resource for download
        """
        try:
            # Get resource metadata
            resource = await firebase_manager.get_document(
                collection="library_resources",
                document_id=resource_id
            )
            
            if not resource:
                raise ValueError("Resource not found")
            
            # Track download
            await firebase_manager.update_document(
                collection="library_resources",
                document_id=resource_id,
                data={'download_count': resource.get('download_count', 0) + 1}
            )
            
            # Record user download
            await firebase_manager.create_document(
                collection=f"users/{user_id}/downloads",
                data={
                    'resource_id': resource_id,
                    'downloaded_at': datetime.utcnow().isoformat()
                }
            )
            
            # Download file from storage
            file_content = await firebase_manager.download_file(
                file_path=resource['storage_path']
            )
            
            return {
                'content': file_content,
                'content_type': resource.get('content_type', 'application/octet-stream'),
                'filename': resource.get('filename', 'download')
            }
            
        except Exception as e:
            logger.error(f"Error downloading resource: {str(e)}")
            raise