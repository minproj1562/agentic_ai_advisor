# app/services/student_service.py
"""
Student Service
Business logic for student operations
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import io

# Optional imports - handle gracefully if not installed
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

from app.core.firebase_admin import firebase_manager
from app.services.student_analysis_service import StudentAnalysisService

logger = logging.getLogger(__name__)


class StudentService:
    """
    Service for student-related operations
    """
    
    def __init__(self):
        self.analysis_service = StudentAnalysisService()
        self._ml_analyzer = None
    
    @property
    def ml_analyzer(self):
        """Lazy load ML analyzer"""
        if self._ml_analyzer is None:
            try:
                from app.services.ml_performance_analysis import ml_analyzer
                self._ml_analyzer = ml_analyzer
            except ImportError:
                logger.warning("ML analyzer not available")
                self._ml_analyzer = None
        return self._ml_analyzer
    
    async def get_performance(
        self,
        student_id: str,
        time_range: str = "all"
    ) -> Dict[str, Any]:
        """
        Get student performance data
        """
        return await self.analysis_service.get_student_performance(
            student_id, time_range
        )
    
    async def get_student_analysis(
        self,
        student_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get full student analysis
        """
        return await self.analysis_service.get_student_by_id(student_id)
    
    async def get_recommendations(
        self,
        student_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations
        """
        try:
            # Get student data from Firebase
            student = await firebase_manager.get_document(
                collection="students",
                document_id=student_id
            )
            
            # Try users collection if not found
            if not student:
                student = await firebase_manager.get_document(
                    collection="users",
                    document_id=student_id
                )
            
            if not student:
                logger.warning(f"Student {student_id} not found")
                return []
            
            # Add student_id to the dict
            student['student_id'] = student_id
            
            # Get existing recommendations from Firebase
            try:
                recommendations = await firebase_manager.get_collection(
                    collection=f"students/{student_id}/recommendations",
                    filters=[{'field': 'is_viewed', 'operator': '==', 'value': False}],
                    order_by='priority',
                    order_direction='asc'
                )
            except Exception:
                recommendations = []
            
            # If no recommendations, generate new ones
            if not recommendations:
                # Get performance data
                performance_data = await self.analysis_service.get_student_performance(student_id)
                
                # Get ML predictions if available
                predictions = {}
                if self.ml_analyzer:
                    try:
                        predictions = await self.ml_analyzer.predict_performance(
                            student, 
                            performance_data.get('performances', [])
                        )
                    except Exception as e:
                        logger.warning(f"ML prediction failed: {e}")
                
                # Generate recommendations
                recommendations = await self.analysis_service.generate_recommendations(
                    student, 
                    performance_data.get('performances', []), 
                    predictions
                )
                
                # Store in Firebase
                for rec in recommendations:
                    try:
                        await firebase_manager.create_document(
                            collection=f"students/{student_id}/recommendations",
                            data=rec
                        )
                    except Exception as e:
                        logger.warning(f"Failed to store recommendation: {e}")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    async def analyze_cv(
        self,
        cv_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Analyze CV content
        """
        try:
            text = ""
            
            # Extract text based on file type
            if filename.endswith('.pdf'):
                text = self._extract_pdf_text(cv_content)
            elif filename.endswith('.docx'):
                text = self._extract_docx_text(cv_content)
            else:
                # Try to decode as text
                try:
                    text = cv_content.decode('utf-8')
                except:
                    text = cv_content.decode('latin-1', errors='ignore')
            
            if not text:
                return {'error': 'Could not extract text from file'}
            
            # Analyze content
            analysis = {
                'skills': self._extract_skills(text),
                'experience': self._extract_experience(text),
                'education': self._extract_education(text),
                'projects': self._extract_projects(text),
                'achievements': self._extract_achievements(text),
                'score': self._calculate_cv_score(text)
            }
            
            # Generate suggestions
            analysis['suggestions'] = self._generate_cv_suggestions(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"CV analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from PDF"""
        if PyPDF2 is None:
            logger.warning("PyPDF2 not installed")
            return ""
        
        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            return text
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return ""
    
    def _extract_docx_text(self, content: bytes) -> str:
        """Extract text from DOCX"""
        if docx is None:
            logger.warning("python-docx not installed")
            return ""
        
        try:
            doc = docx.Document(io.BytesIO(content))
            
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
            return ""
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from CV text"""
        skills = []
        
        # Common technical skills
        skill_keywords = [
            'Python', 'Java', 'JavaScript', 'C++', 'C#', 'React', 'Node.js',
            'Machine Learning', 'Deep Learning', 'Data Science', 'AI',
            'SQL', 'MongoDB', 'PostgreSQL', 'MySQL',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
            'Git', 'Linux', 'TensorFlow', 'PyTorch',
            'HTML', 'CSS', 'TypeScript', 'Angular', 'Vue',
            'REST API', 'GraphQL', 'Microservices'
        ]
        
        text_lower = text.lower()
        for skill in skill_keywords:
            if skill.lower() in text_lower:
                skills.append(skill)
        
        return list(set(skills))  # Remove duplicates
    
    def _extract_experience(self, text: str) -> List[str]:
        """Extract experience from CV"""
        experience = []
        text_lower = text.lower()
        
        if 'internship' in text_lower:
            experience.append('Has internship experience')
        if 'work experience' in text_lower or 'employment' in text_lower:
            experience.append('Has work experience')
        if 'project' in text_lower:
            experience.append('Has project experience')
        if 'research' in text_lower:
            experience.append('Has research experience')
        
        return experience
    
    def _extract_education(self, text: str) -> Dict[str, Any]:
        """Extract education details"""
        import re
        
        education = {}
        text_lower = text.lower()
        
        # Degree detection
        if any(d in text_lower for d in ['bachelor', 'b.tech', 'b.e.', 'bsc', 'ba']):
            education['degree'] = "Bachelor's"
        if any(d in text_lower for d in ['master', 'm.tech', 'm.e.', 'msc', 'ma', 'mba']):
            education['degree'] = "Master's"
        if any(d in text_lower for d in ['phd', 'doctorate', 'ph.d']):
            education['degree'] = "Doctorate"
        
        # GPA extraction
        gpa_pattern = r'(?:GPA|CGPA|CPI)[:\s]*(\d+\.?\d*)'
        gpa_match = re.search(gpa_pattern, text, re.IGNORECASE)
        if gpa_match:
            try:
                education['gpa'] = float(gpa_match.group(1))
            except ValueError:
                pass
        
        return education
    
    def _extract_projects(self, text: str) -> int:
        """Count projects mentioned"""
        project_count = text.lower().count('project')
        return min(project_count, 10)  # Cap at 10
    
    def _extract_achievements(self, text: str) -> List[str]:
        """Extract achievements"""
        achievements = []
        text_lower = text.lower()
        
        achievement_keywords = [
            ('award', 'Has awards'),
            ('winner', 'Competition winner'),
            ('rank', 'Has ranking achievements'),
            ('certificate', 'Has certifications'),
            ('hackathon', 'Hackathon participant'),
            ('scholarship', 'Has scholarship'),
            ('published', 'Has publications')
        ]
        
        for keyword, description in achievement_keywords:
            if keyword in text_lower:
                achievements.append(description)
        
        return achievements
    
    def _calculate_cv_score(self, text: str) -> int:
        """Calculate CV quality score"""
        score = 50  # Base score
        text_lower = text.lower()
        
        # Section checks
        sections = ['education', 'experience', 'skills', 'projects', 'achievements']
        for section in sections:
            if section in text_lower:
                score += 8
        
        # Length check
        word_count = len(text.split())
        if word_count > 300:
            score += 10
        
        return min(score, 100)
    
    def _generate_cv_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate CV improvement suggestions"""
        suggestions = []
        
        if len(analysis.get('skills', [])) < 5:
            suggestions.append("Add more technical skills relevant to your field")
        
        if not analysis.get('experience'):
            suggestions.append("Include internship or project experience")
        
        if analysis.get('projects', 0) < 2:
            suggestions.append("Add more project descriptions with details")
        
        if not analysis.get('achievements'):
            suggestions.append("Highlight your achievements and awards")
        
        if analysis.get('score', 0) < 70:
            suggestions.append("Add more details about your projects and achievements")
        
        if not suggestions:
            suggestions.append("Your CV looks comprehensive! Consider keeping it updated.")
        
        return suggestions
    
    async def get_elective_suggestions(
        self,
        student_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get elective course suggestions based on profile
        """
        try:
            # Get student data
            student = await firebase_manager.get_document(
                collection="students",
                document_id=student_id
            )
            
            if not student:
                student = await firebase_manager.get_document(
                    collection="users",
                    document_id=student_id
                )
            
            if not student:
                return []
            
            # Get available electives
            try:
                electives = await firebase_manager.get_collection(
                    collection="courses",
                    filters=[
                        {'field': 'type', 'operator': '==', 'value': 'elective'}
                    ]
                )
            except Exception:
                electives = []
            
            if not electives:
                # Return mock suggestions if no courses in database
                return self._get_default_elective_suggestions(student)
            
            # Score electives based on student profile
            suggestions = []
            student_interests = student.get('interests', [])
            student_semester = student.get('current_semester', student.get('semester', 1))
            
            for elective in electives:
                score = 0
                reasons = []
                
                # Check prerequisites
                prereqs = elective.get('prerequisites', [])
                if self._check_prerequisites(student, prereqs):
                    score += 20
                    reasons.append("Prerequisites met")
                
                # Check alignment with interests
                elective_tags = elective.get('tags', [])
                matching_interests = [i for i in student_interests if i in elective_tags]
                if matching_interests:
                    score += 30
                    reasons.append(f"Matches interests: {', '.join(matching_interests)}")
                
                # Check career alignment
                if elective.get('career_paths'):
                    score += 25
                    reasons.append("Aligns with career goals")
                
                # Semester suitability
                recommended_sem = elective.get('recommended_semester', 5)
                if isinstance(student_semester, str):
                    student_semester = int(student_semester) if student_semester.isdigit() else 5
                
                if student_semester >= recommended_sem:
                    score += 10
                    reasons.append("Suitable for your semester")
                
                suggestions.append({
                    'course': elective,
                    'score': score,
                    'reasons': reasons,
                    'recommended': score >= 50
                })
            
            # Sort by score
            suggestions.sort(key=lambda x: x['score'], reverse=True)
            
            return suggestions[:5]  # Return top 5
            
        except Exception as e:
            logger.error(f"Error getting elective suggestions: {e}")
            return []
    
    def _get_default_elective_suggestions(self, student: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return default elective suggestions"""
        interests = student.get('interests', [])
        
        suggestions = [
            {
                'course': {
                    'name': 'Machine Learning',
                    'code': 'CS601',
                    'credits': 4,
                    'description': 'Introduction to machine learning algorithms'
                },
                'score': 80 if 'AI' in interests or 'ML' in interests else 60,
                'reasons': ['Popular elective', 'Industry relevant'],
                'recommended': True
            },
            {
                'course': {
                    'name': 'Cloud Computing',
                    'code': 'CS602',
                    'credits': 4,
                    'description': 'Cloud platforms and distributed systems'
                },
                'score': 75 if 'Cloud' in interests else 55,
                'reasons': ['High demand skill', 'Good placement record'],
                'recommended': True
            },
            {
                'course': {
                    'name': 'Data Science',
                    'code': 'CS603',
                    'credits': 4,
                    'description': 'Data analysis and visualization'
                },
                'score': 70 if 'Data' in interests else 50,
                'reasons': ['Growing field', 'Practical applications'],
                'recommended': True
            }
        ]
        
        return suggestions
    
    def _check_prerequisites(
        self,
        student: Dict[str, Any],
        prerequisites: List[str]
    ) -> bool:
        """Check if student meets prerequisites"""
        if not prerequisites:
            return True
        
        # Get student semester
        semester = student.get('current_semester', student.get('semester', 1))
        if isinstance(semester, str):
            semester = int(semester) if semester.isdigit() else 1
        
        # Simple check: assume prerequisites met if semester >= 3
        return semester >= 3
    
    async def generate_study_plan(
        self,
        student_id: str
    ) -> Dict[str, Any]:
        """
        Generate personalized study plan
        """
        try:
            # Get student data
            student = await firebase_manager.get_document(
                collection="students",
                document_id=student_id
            )
            
            if not student:
                student = await firebase_manager.get_document(
                    collection="users",
                    document_id=student_id
                )
            
            if not student:
                return {'error': 'Student not found'}
            
            # Get weaknesses
            weaknesses = await self.analysis_service.get_weaknesses(student_id)
            
            # Create weekly plan
            now = datetime.utcnow()
            plan = {
                'student_id': student_id,
                'duration': '4 weeks',
                'start_date': now.isoformat(),
                'end_date': (now + timedelta(weeks=4)).isoformat(),
                'weeks': []
            }
            
            for week in range(1, 5):
                week_plan = {
                    'week': week,
                    'focus_areas': [],
                    'daily_schedule': {},
                    'goals': [],
                    'assessments': []
                }
                
                # Assign focus areas based on weaknesses
                if weaknesses:
                    # Prioritize by risk score
                    sorted_weaknesses = sorted(
                        weaknesses, 
                        key=lambda x: x.get('risk_score', 0), 
                        reverse=True
                    )
                    
                    week_plan['focus_areas'] = [
                        w.get('subject', 'General') 
                        for w in sorted_weaknesses[:2]
                    ]
                else:
                    week_plan['focus_areas'] = ['General Study', 'Revision']
                
                # Create daily schedule
                for day in range(1, 8):
                    is_weekend = day > 5
                    week_plan['daily_schedule'][f'day_{day}'] = {
                        'study_hours': 3 if is_weekend else 2,
                        'subjects': week_plan['focus_areas'][:2],
                        'activities': ['Theory review', 'Practice problems'] if not is_weekend else ['Project work', 'Extra practice']
                    }
                
                # Set weekly goals
                week_plan['goals'] = [
                    f"Complete week {week} materials for focus subjects",
                    "Solve at least 50 practice problems",
                    "Attend all classes and take notes",
                    "Review previous week's concepts"
                ]
                
                # Add assessment
                week_plan['assessments'].append({
                    'type': 'self_test',
                    'day': 7,
                    'subjects': week_plan['focus_areas'],
                    'duration': '1 hour'
                })
                
                plan['weeks'].append(week_plan)
            
            # Add summary
            plan['summary'] = {
                'total_study_hours': sum(
                    sum(d['study_hours'] for d in w['daily_schedule'].values())
                    for w in plan['weeks']
                ),
                'focus_subjects': list(set(
                    subject 
                    for w in plan['weeks'] 
                    for subject in w['focus_areas']
                )),
                'total_assessments': len(plan['weeks'])
            }
            
            return plan
            
        except Exception as e:
            logger.error(f"Error generating study plan: {e}")
            return {'error': str(e)}


# Create singleton instance
student_service = StudentService()