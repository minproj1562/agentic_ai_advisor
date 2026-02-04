# academic-advisor/academic-advisor-backend/app/services/cv_analysis_service.py
"""
CV Analysis Service - Integrates CV parsing with profile creation
Works with AI-powered parser for intelligent extraction
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

from app.services.cv_parser_v2 import enhanced_cv_parser
from app.models.faculty import (
    Faculty,
    FacultyStatus,
    UniformFacultyProfile,
    PersonalInfo,
    AcademicQualifications,
    CurrentPosition,
    ResearchExpertise,
    TeachingInfo,
    FacultyAvailability,
    PublicationSummary,
    Degree,
    MeetingSlot
)

logger = logging.getLogger(__name__)


class CVAnalysisService:
    """
    Service for analyzing CVs and creating faculty profiles
    """

    async def analyze_cv(
        self, 
        file_content: bytes, 
        filename: str,
        user_id: str,
        user_email: str
    ) -> Tuple[Dict[str, Any], Optional[UniformFacultyProfile]]:
        """
        Analyze CV and return parsed data with suggested profile
        """
        try:
            # Parse CV using AI-powered parser
            parsed_result = await enhanced_cv_parser.parse(file_content, filename)
            
            if not parsed_result.get('extraction_success'):
                raise ValueError("Failed to extract text from CV")
            
            # Build uniform profile from parsed data
            suggested_profile = self._build_uniform_profile(
                parsed_result.get('suggested_profile', {}),
                user_email
            )
            
            return parsed_result, suggested_profile
            
        except Exception as e:
            logger.error(f"CV analysis failed for user {user_id}: {str(e)}", exc_info=True)
            raise

    def _safe_get(self, data: Any, key: str, default: Any = None) -> Any:
        """Safely get value from dict, list, or return default"""
        if data is None:
            return default
        if isinstance(data, dict):
            return data.get(key, default)
        if isinstance(data, list) and key.isdigit():
            idx = int(key)
            return data[idx] if 0 <= idx < len(data) else default
        return default

    def _ensure_list(self, data: Any) -> List:
        """Ensure data is a list"""
        if data is None:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, str):
            return [data] if data else []
        return []

    def _ensure_dict(self, data: Any) -> Dict:
        """Ensure data is a dict"""
        if isinstance(data, dict):
            return data
        return {}

    def _build_uniform_profile(
        self, 
        suggested: Dict[str, Any],
        user_email: str
    ) -> UniformFacultyProfile:
        """
        Build UniformFacultyProfile from parsed CV data with robust error handling
        """
        try:
            suggested = self._ensure_dict(suggested)
            
            # Personal Info
            pi = self._ensure_dict(self._safe_get(suggested, 'personal_info', {}))
            personal_info = PersonalInfo(
                name=self._safe_get(pi, 'name') or user_email.split('@')[0],
                email=self._safe_get(pi, 'email') or user_email,
                phone=self._safe_get(pi, 'phone'),
                photo_url=self._safe_get(pi, 'photo_url')
            )
            
            # Academic Qualifications
            aq = self._ensure_dict(self._safe_get(suggested, 'academic_qualifications', {}))
            degrees_data = self._ensure_list(self._safe_get(aq, 'all_degrees', []))
            
            all_degrees = []
            for deg in degrees_data:
                if isinstance(deg, dict):
                    all_degrees.append(Degree(
                        degree=self._safe_get(deg, 'degree', ''),
                        field=self._safe_get(deg, 'field', ''),
                        institution=self._safe_get(deg, 'institution', ''),
                        year=self._safe_get(deg, 'year'),
                        thesis_title=self._safe_get(deg, 'thesis_title')
                    ))
            
            academic_qualifications = AcademicQualifications(
                highest_degree=self._safe_get(aq, 'highest_degree', 'Unknown'),
                specialization=self._safe_get(aq, 'specialization', ''),
                university=self._safe_get(aq, 'university', ''),
                graduation_year=self._safe_get(aq, 'graduation_year'),
                all_degrees=all_degrees
            )
            
            # Current Position
            cp = self._ensure_dict(self._safe_get(suggested, 'current_position', {}))
            current_position = CurrentPosition(
                designation=self._safe_get(cp, 'designation', 'Faculty'),
                department=self._safe_get(cp, 'department', ''),
                institution=self._safe_get(cp, 'institution', ''),
                years_of_experience=self._safe_get(cp, 'years_of_experience', 0) or 0,
                joining_year=self._safe_get(cp, 'joining_year')
            )
            
            # Research Expertise
            re_data = self._ensure_dict(self._safe_get(suggested, 'research_expertise', {}))
            research_expertise = ResearchExpertise(
                primary_areas=self._ensure_list(self._safe_get(re_data, 'primary_areas', []))[:5],
                secondary_interests=self._ensure_list(self._safe_get(re_data, 'secondary_interests', [])),
                keywords=self._ensure_list(self._safe_get(re_data, 'keywords', []))
            )
            
            # Teaching Info
            ti = self._ensure_dict(self._safe_get(suggested, 'teaching', {}))
            teaching = TeachingInfo(
                current_subjects=self._ensure_list(self._safe_get(ti, 'current_subjects', [])),
                past_subjects=self._ensure_list(self._safe_get(ti, 'past_subjects', [])),
                preferred_areas=self._ensure_list(self._safe_get(ti, 'preferred_areas', []))
            )
            
            # Availability
            availability = FacultyAvailability(
                office_location="",
                office_hours="",
                available_slots=[],
                preferred_meeting_duration=30
            )
            
            # Publications
            publications = None
            pub_data = self._ensure_dict(self._safe_get(suggested, 'publications', {}))
            total_count = self._safe_get(pub_data, 'total_count', 0) or 0
            if total_count > 0:
                publications = PublicationSummary(
                    total_count=total_count,
                    journal_papers=self._safe_get(pub_data, 'journal_papers', 0) or 0,
                    conference_papers=self._safe_get(pub_data, 'conference_papers', 0) or 0,
                    notable_works=self._ensure_list(self._safe_get(pub_data, 'notable_works', []))[:5]
                )
            
            # Others
            others = self._ensure_dict(self._safe_get(suggested, 'others', {}))
            
            return UniformFacultyProfile(
                personal_info=personal_info,
                academic_qualifications=academic_qualifications,
                current_position=current_position,
                research_expertise=research_expertise,
                teaching=teaching,
                availability=availability,
                publications=publications,
                others=others,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error building uniform profile: {str(e)}", exc_info=True)
            return self._create_minimal_profile(user_email)
    
    def _create_minimal_profile(self, user_email: str) -> UniformFacultyProfile:
        """Create minimal profile on error"""
        return UniformFacultyProfile(
            personal_info=PersonalInfo(
                name=user_email.split('@')[0],
                email=user_email
            ),
            academic_qualifications=AcademicQualifications(
                highest_degree="Unknown",
                specialization="",
                university=""
            ),
            current_position=CurrentPosition(
                designation="Faculty",
                department="",
                institution=""
            ),
            research_expertise=ResearchExpertise(),
            teaching=TeachingInfo(),
            availability=FacultyAvailability(
                office_location="",
                office_hours=""
            )
        )

    async def update_faculty_from_cv(
        self,
        faculty: Faculty,
        parsed_result: Dict[str, Any],
        suggested_profile: UniformFacultyProfile,
        cv_url: Optional[str] = None,
        cv_filename: Optional[str] = None
    ) -> Faculty:
        """Update faculty document with CV analysis results"""
        try:
            if cv_url:
                faculty.cv_url = cv_url
            if cv_filename:
                faculty.cv_file_name = cv_filename
            
            faculty.cv_uploaded_at = datetime.utcnow()
            faculty.cv_parsed_data = parsed_result
            
            if not faculty.profile_setup_complete:
                faculty.uniform_profile = suggested_profile
                
                if suggested_profile.personal_info.name:
                    faculty.name = suggested_profile.personal_info.name
                if suggested_profile.current_position.department:
                    faculty.department = suggested_profile.current_position.department
                if suggested_profile.current_position.designation:
                    faculty.designation = suggested_profile.current_position.designation
                
                faculty.specializations = list(suggested_profile.research_expertise.primary_areas)
                faculty.skills = list(suggested_profile.research_expertise.keywords)
                faculty.teaching_subjects = list(suggested_profile.teaching.current_subjects)
            
            faculty.updated_at = datetime.utcnow()
            await faculty.save()
            
            return faculty
            
        except Exception as e:
            logger.error(f"Error updating faculty from CV: {str(e)}", exc_info=True)
            raise

    def calculate_extraction_confidence(self, parsed_result: Dict[str, Any]) -> float:
        """Calculate confidence score for CV extraction (0-1)"""
        return parsed_result.get('quality_score', 0) / 100.0

    def get_extraction_warnings(self, parsed_result: Dict[str, Any]) -> List[str]:
        """Get warnings for incomplete/uncertain extractions"""
        warnings = []
        
        pi = parsed_result.get('personal_info', {})
        if isinstance(pi, dict):
            if not pi.get('name'):
                warnings.append("Could not extract name - please verify")
            if not pi.get('email'):
                warnings.append("Could not extract email from CV")
        
        education = parsed_result.get('education', [])
        if not isinstance(education, list) or len(education) == 0:
            warnings.append("No education details found - please add manually")
        
        experience = parsed_result.get('experience', [])
        if not isinstance(experience, list) or len(experience) == 0:
            warnings.append("No work experience found - please add manually")
        
        research = parsed_result.get('research_interests', [])
        if not isinstance(research, list) or len(research) == 0:
            warnings.append("No research areas detected - please specify your expertise")
        
        quality = parsed_result.get('quality_score', 0)
        if quality < 50:
            warnings.append("Low extraction quality - please review all fields carefully")
        
        return warnings


# Singleton instance
cv_analysis_service = CVAnalysisService()

__all__ = ['CVAnalysisService', 'cv_analysis_service']