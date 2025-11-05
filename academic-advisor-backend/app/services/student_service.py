# app/services/student_service.py
"""
Student Service
Business logic for student operations
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import PyPDF2
import docx

from app.core.firebase_admin import firebase_manager
from app.services.ml_performance_analysis import ml_analyzer
from app.services.student_analysis_service import StudentAnalysisService
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class StudentService:
    """
    Service for student-related operations
    """
    
    def __init__(self):
        self.analysis_service = StudentAnalysisService()
    
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
    
    async def get_recommendations(
        self,
        student_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations
        """
        # Get student data
        student = await firebase_manager.get_document(
            collection="students",
            document_id=student_id,
            subcollections=["performance", "weaknesses"]
        )
        
        if not student:
            return []
        
        # Get existing recommendations
        recommendations = await firebase_manager.get_collection(
            collection=f"students/{student_id}/recommendations",
            filters=[{'field': 'is_viewed', 'operator': '==', 'value': False}],
            order_by='priority',
            order_direction='asc'
        )
        
        # If no recommendations, generate new ones
        if not recommendations:
            # Get ML predictions
            predictions = await ml_analyzer.predict_performance(
                student, student.get('performance', [])
            )
            
            # Generate recommendations
            recommendations = await self.analysis_service.generate_recommendations(
                student, student.get('performance', []), predictions
            )
            
            # Store in Firebase
            for rec in recommendations:
                await firebase_manager.create_document(
                    collection=f"students/{student_id}/recommendations",
                    data=rec
                )
        
        return recommendations
    
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
        try:
            import io
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            return text
        except:
            return ""
    
    def _extract_docx_text(self, content: bytes) -> str:
        """Extract text from DOCX"""
        try:
            import io
            doc = docx.Document(io.BytesIO(content))
            
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text
        except:
            return ""
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from CV text"""
        skills = []
        
        # Common technical skills to look for
        skill_keywords = [
            'Python', 'Java', 'JavaScript', 'C++', 'React', 'Node.js',
            'Machine Learning', 'Data Science', 'SQL', 'MongoDB',
            'AWS', 'Docker', 'Kubernetes', 'Git', 'Linux'
        ]
        
        text_lower = text.lower()
        for skill in skill_keywords:
            if skill.lower() in text_lower:
                skills.append(skill)
        
        return skills
    
    def _extract_experience(self, text: str) -> List[str]:
        """Extract experience from CV"""
        experience = []
        
        # Look for internship/job indicators
        if 'internship' in text.lower():
            experience.append('Has internship experience')
        if 'work experience' in text.lower():
            experience.append('Has work experience')
        
        return experience
    
    def _extract_education(self, text: str) -> Dict[str, Any]:
        """Extract education details"""
        education = {}
        
        # Look for degree information
        if 'bachelor' in text.lower() or 'b.tech' in text.lower():
            education['degree'] = 'Bachelor\'s'
        if 'master' in text.lower() or 'm.tech' in text.lower():
            education['degree'] = 'Master\'s'
        
        # Look for GPA/CGPA
        import re
        gpa_pattern = r'(?:GPA|CGPA)[:\s]*(\d+\.?\d*)'
        gpa_match = re.search(gpa_pattern, text, re.IGNORECASE)
        if gpa_match:
            education['gpa'] = float(gpa_match.group(1))
        
        return education
    
    def _extract_projects(self, text: str) -> int:
        """Count projects mentioned"""
        project_count = text.lower().count('project')
        return min(project_count, 10)  # Cap at 10
    
    def _extract_achievements(self, text: str) -> List[str]:
        """Extract achievements"""
        achievements = []
        
        achievement_keywords = ['award', 'winner', 'rank', 'certificate', 'hackathon']
        
        for keyword in achievement_keywords:
            if keyword in text.lower():
                achievements.append(f"Has {keyword} mentioned")
        
        return achievements
    
    def _calculate_cv_score(self, text: str) -> int:
        """Calculate CV quality score"""
        score = 50  # Base score
        
        # Check for key sections
        if 'education' in text.lower():
            score += 10
        if 'experience' in text.lower():
            score += 10
        if 'skills' in text.lower():
            score += 10
        if 'projects' in text.lower():
            score += 10
        if 'achievements' in text.lower():
            score += 10
        
        return min(score, 100)
    
    def _generate_cv_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate CV improvement suggestions"""
        suggestions = []
        
        if len(analysis.get('skills', [])) < 5:
            suggestions.append("Add more technical skills relevant to your field")
        
        if not analysis.get('experience'):
            suggestions.append("Include internship or project experience")
        
        if analysis.get('score', 0) < 70:
            suggestions.append("Add more details about your projects and achievements")
        
        return suggestions
    
    async def get_elective_suggestions(
        self,
        student_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get elective course suggestions based on profile
        """
        # Get student data
        student = await firebase_manager.get_document(
            collection="students",
            document_id=student_id
        )
        
        if not student:
            return []
        
        # Get available electives
        electives = await firebase_manager.get_collection(
            collection="courses",
            filters=[
                {'field': 'type', 'operator': '==', 'value': 'elective'},
                {'field': 'department', 'operator': '==', 'value': student['department']}
            ]
        )
        
        # Score electives based on student profile
        suggestions = []
        
        for elective in electives:
            score = 0
            reasons = []
            
            # Check prerequisites
            prereqs = elective.get('prerequisites', [])
            if self._check_prerequisites(student, prereqs):
                score += 20
                reasons.append("Prerequisites met")
            
            # Check alignment with interests
            if any(interest in elective.get('tags', []) for interest in student.get('interests', [])):
                score += 30
                reasons.append("Matches your interests")
            
            # Check career alignment
            if elective.get('career_paths'):
                score += 25
                reasons.append("Aligns with career goals")
            
            suggestions.append({
                'course': elective,
                'score': score,
                'reasons': reasons,
                'recommended': score >= 50
            })
        
        # Sort by score
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        
        return suggestions[:5]  # Return top 5
    
    def _check_prerequisites(
        self,
        student: Dict[str, Any],
        prerequisites: List[str]
    ) -> bool:
        """Check if student meets prerequisites"""
        # Simplified check - in reality would check completed courses
        return len(prerequisites) == 0 or student.get('current_semester', 1) >= 3
    
    async def generate_study_plan(
        self,
        student_id: str
    ) -> Dict[str, Any]:
        """
        Generate personalized study plan
        """
        # Get student data
        student = await firebase_manager.get_document(
            collection="students",
            document_id=student_id,
            subcollections=["performance", "weaknesses"]
        )
        
        if not student:
            return {}
        
        # Get weaknesses
        weaknesses = student.get('weaknesses', [])
        
        # Create weekly plan
        plan = {
            'duration': '4 weeks',
            'start_date': datetime.utcnow().isoformat(),
            'end_date': (datetime.utcnow() + timedelta(weeks=4)).isoformat(),
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
                # Focus on most critical weaknesses first
                critical = [w for w in weaknesses if w['severity'] == 'critical']
                high = [w for w in weaknesses if w['severity'] == 'high']
                
                if week <= 2 and critical:
                    week_plan['focus_areas'] = [w['subject'] for w in critical[:2]]
                elif high:
                    week_plan['focus_areas'] = [w['subject'] for w in high[:2]]
            
            # Create daily schedule
            for day in range(1, 8):
                week_plan['daily_schedule'][f'day_{day}'] = {
                    'study_hours': 2 if day <= 5 else 3,  # More on weekends
                    'subjects': week_plan['focus_areas'][:2] if week_plan['focus_areas'] else ['General']
                }
            
            # Set weekly goals
            week_plan['goals'] = [
                f"Complete chapter {week} materials",
                "Solve 50 practice problems",
                "Attend all classes"
            ]
            
            # Add assessment
            week_plan['assessments'].append({
                'type': 'self_test',
                'day': 7,
                'subjects': week_plan['focus_areas']
            })
            
            plan['weeks'].append(week_plan)
        
        return plan