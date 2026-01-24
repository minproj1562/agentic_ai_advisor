# app/services/weakness_analysis_service.py
"""
Central Weakness Analysis Service
Integrates student performance, interests, and elective recommendations
to generate comprehensive weakness analysis
"""

import logging
import traceback
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np

from app.models.weakness import (
    WeaknessArea,
    WeaknessAnalysisRequest,
    WeaknessAnalysisResponse,
    WeaknessAnalysisResult,
    StudentInterestProfile,
    AnalysisBasis,
    SeverityLevel
)

logger = logging.getLogger(__name__)


class WeaknessAnalysisService:
    """
    Main service for analyzing student weaknesses based on:
    1. Student-selected interests
    2. Recommended electives and honours/minors
    3. Academic performance (grades, scores, history)
    """
    
    # Mapping of interests to required foundational subjects with weights
    INTEREST_SUBJECT_MAP: Dict[str, Dict[str, float]] = {
        "Machine Learning": {
            "Mathematics": 1.0,
            "Statistics": 0.9,
            "Python Programming": 0.95,
            "Linear Algebra": 0.85,
            "Data Structures": 0.8,
            "Algorithms": 0.75,
            "Probability": 0.85,
            "Calculus": 0.7
        },
        "Artificial Intelligence": {
            "Mathematics": 0.95,
            "Python Programming": 0.9,
            "Statistics": 0.85,
            "Algorithms": 0.9,
            "Data Structures": 0.85,
            "Logic": 0.8,
            "Discrete Mathematics": 0.75
        },
        "Data Science": {
            "Statistics": 1.0,
            "Python Programming": 0.95,
            "Database Management": 0.85,
            "Mathematics": 0.8,
            "Data Visualization": 0.75,
            "Machine Learning Basics": 0.7
        },
        "Web Development": {
            "HTML/CSS": 0.9,
            "JavaScript": 0.95,
            "Database Management": 0.85,
            "Backend Programming": 0.9,
            "React/Angular": 0.8,
            "Node.js": 0.75
        },
        "Cloud Computing": {
            "Networking": 0.95,
            "Operating Systems": 0.9,
            "Linux": 0.85,
            "Security": 0.8,
            "Virtualization": 0.85,
            "Database Management": 0.7
        },
        "Cybersecurity": {
            "Networking": 1.0,
            "Operating Systems": 0.9,
            "Cryptography": 0.95,
            "Security Fundamentals": 0.9,
            "Linux": 0.8,
            "Programming": 0.75
        },
        "Mobile Development": {
            "Java": 0.9,
            "Kotlin": 0.85,
            "Swift": 0.85,
            "UI/UX Design": 0.8,
            "Database Management": 0.75,
            "API Development": 0.7
        },
        "IoT": {
            "Embedded Systems": 0.95,
            "Networking": 0.9,
            "Electronics": 0.85,
            "Python Programming": 0.8,
            "C Programming": 0.85,
            "Sensors": 0.75
        },
        "Blockchain": {
            "Cryptography": 0.95,
            "Distributed Systems": 0.9,
            "Data Structures": 0.85,
            "Networking": 0.8,
            "Smart Contracts": 0.85
        },
        "DevOps": {
            "Linux": 0.95,
            "Networking": 0.85,
            "Scripting": 0.9,
            "Cloud Platforms": 0.9,
            "Docker/Kubernetes": 0.85,
            "CI/CD": 0.8
        }
    }
    
    # Mapping of electives to prerequisites with importance weights
    ELECTIVE_PREREQUISITES: Dict[str, Dict[str, Tuple[float, str]]] = {
        "Machine Learning": {
            "Python": (0.95, "Critical"),
            "Mathematics": (0.9, "Critical"),
            "Statistics": (0.85, "High"),
            "Linear Algebra": (0.8, "High"),
            "Data Structures": (0.7, "Medium")
        },
        "ML": {
            "Python": (0.95, "Critical"),
            "Data Structures and Algorithms": (0.9, "High"),
            "Artificial Intelligence": (0.85, "High"),
            "Database Management System": (0.7, "Medium")
        },
        "Wireless Technology": {
            "Computer Networks": (0.95, "Critical"),
            "Microprocessor and Embedded Systems": (0.9, "High"),
            "Internet of Things (IoT)": (0.85, "High"),
            "C": (0.7, "Medium")
        },
        "WT": {
            "Computer Networks": (0.95, "Critical"),
            "Microprocessor and Embedded Systems": (0.9, "High"),
            "Internet of Things (IoT)": (0.85, "High"),
            "C": (0.7, "Medium")
        },
        "Data Warehouse and Data Mining": {
            "Database Management System": (0.95, "Critical"),
            "Data Structures and Algorithms": (0.85, "High"),
            "Python": (0.8, "Medium"),
            "Artificial Intelligence": (0.75, "Medium")
        },
        "DWM": {
            "Database Management System": (0.95, "Critical"),
            "Data Structures and Algorithms": (0.85, "High"),
            "Python": (0.8, "Medium")
        },
        "Cloud Computing Services": {
            "Computer Networks": (0.9, "High"),
            "Operating System": (0.85, "High"),
            "Database Management System": (0.8, "Medium"),
            "Full Stack Development (FSDL)": (0.85, "High")
        },
        "CCS": {
            "Computer Networks": (0.9, "High"),
            "Operating System": (0.85, "High"),
            "Database Management System": (0.8, "Medium")
        },
        "Big Data Analytics": {
            "Database Management": (0.95, "Critical"),
            "Distributed Systems": (0.85, "High"),
            "Statistics": (0.8, "High"),
            "Python": (0.75, "Medium")
        },
        "Natural Language Processing": {
            "Machine Learning": (0.9, "Critical"),
            "Python": (0.9, "Critical"),
            "Linguistics": (0.7, "Medium"),
            "Statistics": (0.75, "Medium")
        },
        "Computer Vision": {
            "Image Processing": (0.9, "Critical"),
            "Machine Learning": (0.85, "High"),
            "Linear Algebra": (0.8, "High"),
            "Python": (0.85, "High")
        }
    }
    
    # Mapping of honours/minors to required subjects
    HONOURS_PREREQUISITES: Dict[str, Dict[str, Tuple[float, str]]] = {
        "Data Science Honours": {
            "Statistics": (1.0, "Critical"),
            "Machine Learning": (0.95, "Critical"),
            "Big Data": (0.85, "High"),
            "Data Visualization": (0.8, "High"),
            "Python": (0.9, "Critical")
        },
        "AI Minor": {
            "Machine Learning": (0.95, "Critical"),
            "Deep Learning": (0.9, "High"),
            "Mathematics": (0.85, "High"),
            "Neural Networks": (0.85, "High"),
            "Python": (0.9, "Critical")
        },
        "Cybersecurity Minor": {
            "Networking": (0.95, "Critical"),
            "Cryptography": (0.9, "Critical"),
            "Security": (0.9, "Critical"),
            "Ethical Hacking": (0.85, "High"),
            "Operating Systems": (0.8, "High")
        },
        "Cloud Computing Minor": {
            "Cloud Platforms": (0.95, "Critical"),
            "Networking": (0.9, "High"),
            "Linux": (0.85, "High"),
            "Virtualization": (0.8, "High"),
            "DevOps": (0.75, "Medium")
        }
    }
    
    def __init__(self):
        self.logger = logger
    
    async def analyze_weaknesses(
        self,
        request: WeaknessAnalysisRequest
    ) -> WeaknessAnalysisResponse:
        """
        Main method to analyze student weaknesses based on the specified basis
        """
        try:
            student_id = request.student_id
            
            # Get student academic data
            student_data = await self._get_student_data(student_id)
            
            # Get student interests if analyzing by interest
            interests = request.interests
            if not interests and request.analysis_basis in [AnalysisBasis.INTEREST, AnalysisBasis.COMBINED]:
                interests = await self._get_student_interests(student_id)
            
            # Get recommended electives if analyzing by electives
            electives = request.recommended_electives
            if not electives and request.analysis_basis in [AnalysisBasis.ELECTIVES, AnalysisBasis.COMBINED]:
                electives = await self._get_recommended_electives(student_id, student_data)
            
            # Get honours/minors if analyzing by honours
            honours_minors = request.honours_minors
            if not honours_minors and request.analysis_basis in [AnalysisBasis.HONOURS_MINORS, AnalysisBasis.COMBINED]:
                honours_minors = await self._get_recommended_honours(student_id, student_data)
            
            # Perform analysis based on the specified basis
            if request.analysis_basis == AnalysisBasis.INTEREST:
                weaknesses = await self._analyze_by_interests(student_data, interests or [])
            elif request.analysis_basis == AnalysisBasis.ELECTIVES:
                weaknesses = await self._analyze_by_electives(student_data, electives or [])
            elif request.analysis_basis == AnalysisBasis.HONOURS_MINORS:
                weaknesses = await self._analyze_by_honours(student_data, honours_minors or [])
            elif request.analysis_basis == AnalysisBasis.PERFORMANCE:
                weaknesses = await self._analyze_by_performance(student_data)
            else:  # COMBINED
                weaknesses = await self._analyze_combined(
                    student_data,
                    interests or [],
                    electives or [],
                    honours_minors or []
                )
            
            # Calculate overall metrics
            response = self._build_response(
                student_id=student_id,
                analysis_basis=request.analysis_basis,
                weaknesses=weaknesses,
                include_resources=request.include_resources,
                include_study_plan=request.include_study_plan
            )
            
            # Save analysis to database
            await self._save_analysis_result(response, interests, electives, honours_minors)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error analyzing weaknesses: {e}")
            raise
    
    async def _get_student_data(self, student_id: str) -> Dict[str, Any]:
        """Fetch student academic data from database"""
        try:
            # Import here to avoid circular imports
            from app.models.student import StudentPerformance
            from app.models.student_profile import StudentProfile
            
            # Try to get from StudentPerformance collection
            performance = await StudentPerformance.find_one(
                StudentPerformance.student_info.uid == student_id
            )
            
            if performance:
                # Convert subjects to score dictionary
                subject_scores = {}
                for subject in performance.subjects:
                    subject_scores[subject.name] = {
                        'score': subject.score,
                        'credits': subject.credits,
                        'trend': subject.trend.value if hasattr(subject.trend, 'value') else subject.trend,
                        'weakness': subject.weakness,
                        'strength': subject.strength
                    }
                
                return {
                    'student_id': student_id,
                    'cgpa': performance.overall_cgpa,
                    'sgpa': performance.semester_sgpa,
                    'semester': performance.student_info.semester,
                    'branch': performance.student_info.branch,
                    'subjects': subject_scores,
                    'strong_subjects': performance.strong_subjects,
                    'weak_subjects': performance.weak_subjects,
                    'interests': performance.interests,
                    'career_goals': performance.career_goals,
                    'skills_matrix': performance.skills_matrix
                }
            
            # Try StudentProfile as fallback
            profile = await StudentProfile.find_one(
                StudentProfile.user_id == student_id
            )
            
            if profile:
                subject_scores = {}
                for semester in profile.semester_records:
                    for subject in semester.subjects:
                        # Convert grade to score
                        score = self._grade_to_score(subject.grade)
                        subject_scores[subject.subject_name] = {
                            'score': score,
                            'credits': subject.credits,
                            'grade': subject.grade,
                            'trend': 'stable'
                        }
                
                return {
                    'student_id': student_id,
                    'cgpa': profile.cgpa,
                    'sgpa': profile.semester_records[-1].sgpa if profile.semester_records else 0,
                    'semester': profile.current_semester,
                    'branch': profile.branch,
                    'subjects': subject_scores,
                    'strong_subjects': [],
                    'weak_subjects': [],
                    'interests': profile.interests,
                    'career_goals': profile.career_goals,
                    'skills_matrix': {}
                }
            
            # Return default data if nothing found
            return self._get_default_student_data(student_id)
            
        except Exception as e:
            self.logger.error(f"Error fetching student data: {e}")
            return self._get_default_student_data(student_id)
    
    def _get_default_student_data(self, student_id: str) -> Dict[str, Any]:
        """Return default student data structure"""
        return {
            'student_id': student_id,
            'cgpa': 7.5,
            'sgpa': 7.8,
            'semester': '5',
            'branch': 'IT',
            'subjects': {
                'Data Structures and Algorithms': {'score': 75, 'credits': 4, 'trend': 'up'},
                'Database Management System': {'score': 68, 'credits': 4, 'trend': 'stable'},
                'Computer Networks': {'score': 72, 'credits': 3, 'trend': 'up'},
                'Operating System': {'score': 70, 'credits': 4, 'trend': 'stable'},
                'Python': {'score': 82, 'credits': 3, 'trend': 'up'},
                'Mathematics': {'score': 65, 'credits': 4, 'trend': 'down'},
                'Statistics': {'score': 60, 'credits': 3, 'trend': 'stable'},
            },
            'strong_subjects': ['Python', 'Data Structures and Algorithms'],
            'weak_subjects': ['Mathematics', 'Statistics'],
            'interests': ['Machine Learning', 'Web Development'],
            'career_goals': ['Software Engineer'],
            'skills_matrix': {'Python': 0.8, 'JavaScript': 0.6, 'SQL': 0.7}
        }
    
    def _grade_to_score(self, grade: str) -> float:
        """Convert grade to numerical score"""
        grade_map = {
            'O': 95, 'A+': 85, 'A': 75, 'B+': 65,
            'B': 55, 'C': 45, 'P': 40, 'F': 30
        }
        return grade_map.get(grade, 50)
    
    async def _get_student_interests(self, student_id: str) -> List[str]:
        """Fetch student interests from database (checks multiple sources)"""
        try:
            # Try StudentInterestProfile first (weakness analysis storage)
            interest_profile = await StudentInterestProfile.find_one(
                StudentInterestProfile.user_id == student_id
            )
            if interest_profile and interest_profile.interests:
                self.logger.info(f"✅ Found {len(interest_profile.interests)} interests in StudentInterestProfile")
                return interest_profile.interests
            
            # Fallback: Try StudentProfile (where student profile saves interests)
            from app.models.student_profile import StudentProfile
            profile = await StudentProfile.find_one(
                StudentProfile.user_id == student_id
            )
            if profile and profile.interests:
                self.logger.info(f"✅ Found {len(profile.interests)} interests in StudentProfile")
                
                # Sync to StudentInterestProfile for future use
                interest_profile = StudentInterestProfile(
                    user_id=student_id,
                    interests=profile.interests,
                    career_goals=profile.career_goals if profile.career_goals else []
                )
                await interest_profile.save()
                self.logger.info(f"📝 Synced interests to StudentInterestProfile")
                
                return profile.interests
            
            # Also try StudentPerformance (where ML service saves interests)
            from app.models.student import StudentPerformance
            performance = await StudentPerformance.find_one(
                StudentPerformance.student_info.uid == student_id
            )
            if performance and performance.interests:
                self.logger.info(f"✅ Found {len(performance.interests)} interests in StudentPerformance (ML)")
                
                # Sync to StudentInterestProfile
                interest_profile = StudentInterestProfile(
                    user_id=student_id,
                    interests=performance.interests,
                    career_goals=performance.career_goals if hasattr(performance, 'career_goals') else []
                )
                await interest_profile.save()
                self.logger.info(f"📝 Synced ML interests to StudentInterestProfile")
                
                return performance.interests
            
            self.logger.warning(f"⚠️ No interests found for student {student_id}")
            return []
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching interests: {e}")
            traceback.print_exc()
            return []
    
    async def _get_recommended_electives(
        self, 
        student_id: str, 
        student_data: Dict[str, Any]
    ) -> List[str]:
        """Get recommended electives based on student performance"""
        # This would typically call ElectiveRecommendationService
        # For now, return based on branch and interests
        interests = student_data.get('interests', [])
        
        elective_suggestions = []
        if 'Machine Learning' in interests or 'AI' in interests:
            elective_suggestions.append('ML')
        if 'IoT' in interests or 'Embedded Systems' in interests:
            elective_suggestions.append('WT')
        if 'Data Science' in interests or 'Analytics' in interests:
            elective_suggestions.append('DWM')
        if 'Cloud' in interests or 'DevOps' in interests:
            elective_suggestions.append('CCS')
        
        # Default to ML if no matches
        if not elective_suggestions:
            elective_suggestions = ['ML', 'CCS']
        
        return elective_suggestions
    
    async def _get_recommended_honours(
        self, 
        student_id: str, 
        student_data: Dict[str, Any]
    ) -> List[str]:
        """Get recommended honours/minors based on student profile"""
        cgpa = student_data.get('cgpa', 0)
        interests = student_data.get('interests', [])
        
        recommendations = []
        
        # Only recommend honours for students with good CGPA
        if cgpa >= 7.5:
            if any(i in interests for i in ['Machine Learning', 'AI', 'Data Science']):
                recommendations.append('Data Science Honours')
                recommendations.append('AI Minor')
            if any(i in interests for i in ['Security', 'Cybersecurity', 'Networking']):
                recommendations.append('Cybersecurity Minor')
            if any(i in interests for i in ['Cloud', 'DevOps']):
                recommendations.append('Cloud Computing Minor')
        
        return recommendations[:2]  # Return top 2
    
    async def _analyze_by_interests(
        self,
        student_data: Dict[str, Any],
        interests: List[str]
    ) -> List[WeaknessArea]:
        """Analyze weaknesses based on chosen interests"""
        weaknesses = []
        subjects = student_data.get('subjects', {})
        
        for interest in interests:
            if interest not in self.INTEREST_SUBJECT_MAP:
                continue
            
            required_subjects = self.INTEREST_SUBJECT_MAP[interest]
            
            for req_subject, weight in required_subjects.items():
                # Find matching subject in student data
                student_score = self._find_subject_score(subjects, req_subject)
                
                if student_score is None:
                    # Subject not taken yet - flag as potential weakness
                    weaknesses.append(self._create_weakness_area(
                        subject=req_subject,
                        current_score=0,
                        related_to=f"{interest} interest",
                        analysis_basis=AnalysisBasis.INTEREST,
                        topic=f"Prerequisite for {interest}",
                        severity=SeverityLevel.MEDIUM,
                        confidence=0.7,
                        impact_on_interest=f"Required foundation for {interest}"
                    ))
                elif student_score < 60:
                    # Low score - definite weakness
                    severity = self._calculate_severity(student_score, weight)
                    weaknesses.append(self._create_weakness_area(
                        subject=req_subject,
                        current_score=student_score,
                        related_to=f"{interest} interest",
                        analysis_basis=AnalysisBasis.INTEREST,
                        topic=f"Foundation for {interest}",
                        severity=severity,
                        confidence=0.85 * weight,
                        impact_on_interest=f"Will affect ability to excel in {interest}"
                    ))
                elif student_score < 75 and weight >= 0.8:
                    # Moderate score in high-weight subject
                    weaknesses.append(self._create_weakness_area(
                        subject=req_subject,
                        current_score=student_score,
                        related_to=f"{interest} interest",
                        analysis_basis=AnalysisBasis.INTEREST,
                        topic=f"Important for {interest}",
                        severity=SeverityLevel.LOW,
                        confidence=0.75,
                        impact_on_interest=f"Improvement recommended for {interest}"
                    ))
        
        return weaknesses
    
    async def _analyze_by_electives(
        self,
        student_data: Dict[str, Any],
        electives: List[str]
    ) -> List[WeaknessArea]:
        """Analyze weaknesses based on recommended electives"""
        weaknesses = []
        subjects = student_data.get('subjects', {})
        
        for elective in electives:
            if elective not in self.ELECTIVE_PREREQUISITES:
                continue
            
            prerequisites = self.ELECTIVE_PREREQUISITES[elective]
            
            for prereq, (weight, importance) in prerequisites.items():
                student_score = self._find_subject_score(subjects, prereq)
                
                threshold = 70 if importance == "Critical" else 60 if importance == "High" else 50
                
                if student_score is None:
                    weaknesses.append(self._create_weakness_area(
                        subject=prereq,
                        current_score=0,
                        related_to=f"{elective} elective",
                        analysis_basis=AnalysisBasis.ELECTIVES,
                        topic=f"Prerequisite for {elective}",
                        severity=SeverityLevel.HIGH if importance == "Critical" else SeverityLevel.MEDIUM,
                        confidence=0.8,
                        impact_on_elective=f"Required before taking {elective}"
                    ))
                elif student_score < threshold:
                    severity = SeverityLevel.CRITICAL if importance == "Critical" and student_score < 50 else \
                               SeverityLevel.HIGH if importance == "Critical" else \
                               SeverityLevel.MEDIUM if importance == "High" else SeverityLevel.LOW
                    
                    weaknesses.append(self._create_weakness_area(
                        subject=prereq,
                        current_score=student_score,
                        related_to=f"{elective} elective",
                        analysis_basis=AnalysisBasis.ELECTIVES,
                        topic=f"Prerequisite for {elective}",
                        severity=severity,
                        confidence=0.85 * weight,
                        impact_on_elective=f"May struggle with {elective} if not improved"
                    ))
        
        return weaknesses
    
    async def _analyze_by_honours(
        self,
        student_data: Dict[str, Any],
        honours_minors: List[str]
    ) -> List[WeaknessArea]:
        """Analyze weaknesses based on honours/minors programs"""
        weaknesses = []
        subjects = student_data.get('subjects', {})
        
        for program in honours_minors:
            if program not in self.HONOURS_PREREQUISITES:
                continue
            
            prerequisites = self.HONOURS_PREREQUISITES[program]
            
            for prereq, (weight, importance) in prerequisites.items():
                student_score = self._find_subject_score(subjects, prereq)
                
                # Honours require higher scores
                threshold = 75 if importance == "Critical" else 65
                
                if student_score is None:
                    weaknesses.append(self._create_weakness_area(
                        subject=prereq,
                        current_score=0,
                        related_to=f"{program}",
                        analysis_basis=AnalysisBasis.HONOURS_MINORS,
                        topic=f"Required for {program}",
                        severity=SeverityLevel.HIGH,
                        confidence=0.85,
                        impact_on_career=f"Essential for {program} eligibility"
                    ))
                elif student_score < threshold:
                    severity = SeverityLevel.CRITICAL if student_score < 50 else \
                               SeverityLevel.HIGH if student_score < 60 else SeverityLevel.MEDIUM
                    
                    weaknesses.append(self._create_weakness_area(
                        subject=prereq,
                        current_score=student_score,
                        related_to=f"{program}",
                        analysis_basis=AnalysisBasis.HONOURS_MINORS,
                        topic=f"Required for {program}",
                        severity=severity,
                        confidence=0.9 * weight,
                        impact_on_career=f"Must improve to {threshold}% for {program}"
                    ))
        
        return weaknesses
    
    async def _analyze_by_performance(
        self,
        student_data: Dict[str, Any]
    ) -> List[WeaknessArea]:
        """Analyze weaknesses based on pure academic performance"""
        weaknesses = []
        subjects = student_data.get('subjects', {})
        
        for subject_name, data in subjects.items():
            score = data.get('score', 0)
            trend = data.get('trend', 'stable')
            
            if score < 60:
                severity = SeverityLevel.CRITICAL if score < 40 else \
                           SeverityLevel.HIGH if score < 50 else SeverityLevel.MEDIUM
                
                weaknesses.append(self._create_weakness_area(
                    subject=subject_name,
                    current_score=score,
                    related_to="Academic performance",
                    analysis_basis=AnalysisBasis.PERFORMANCE,
                    topic="Overall subject performance",
                    severity=severity,
                    confidence=0.9
                ))
            elif score < 70 and trend == 'down':
                weaknesses.append(self._create_weakness_area(
                    subject=subject_name,
                    current_score=score,
                    related_to="Declining performance",
                    analysis_basis=AnalysisBasis.PERFORMANCE,
                    topic="Performance trending downward",
                    severity=SeverityLevel.MEDIUM,
                    confidence=0.8
                ))
        
        return weaknesses
    
    async def _analyze_combined(
        self,
        student_data: Dict[str, Any],
        interests: List[str],
        electives: List[str],
        honours_minors: List[str]
    ) -> List[WeaknessArea]:
        """Combined analysis from all sources"""
        all_weaknesses = []
        
        # Gather weaknesses from all sources
        if interests:
            interest_weaknesses = await self._analyze_by_interests(student_data, interests)
            all_weaknesses.extend(interest_weaknesses)
        
        if electives:
            elective_weaknesses = await self._analyze_by_electives(student_data, electives)
            all_weaknesses.extend(elective_weaknesses)
        
        if honours_minors:
            honours_weaknesses = await self._analyze_by_honours(student_data, honours_minors)
            all_weaknesses.extend(honours_weaknesses)
        
        # Always include performance-based analysis
        performance_weaknesses = await self._analyze_by_performance(student_data)
        all_weaknesses.extend(performance_weaknesses)
        
        # Deduplicate and merge weaknesses
        merged = self._merge_weaknesses(all_weaknesses)
        
        return merged
    
    def _find_subject_score(
        self, 
        subjects: Dict[str, Any], 
        target_subject: str
    ) -> Optional[float]:
        """Find subject score using fuzzy matching"""
        target_lower = target_subject.lower()
        
        for subject_name, data in subjects.items():
            if target_lower in subject_name.lower() or subject_name.lower() in target_lower:
                return data.get('score', 0)
        
        # Try partial matching
        for subject_name, data in subjects.items():
            # Split and check words
            target_words = set(target_lower.split())
            subject_words = set(subject_name.lower().split())
            if target_words & subject_words:  # Any common words
                return data.get('score', 0)
        
        return None
    
    def _calculate_severity(self, score: float, weight: float = 1.0) -> SeverityLevel:
        """Calculate severity based on score and weight"""
        weighted_score = score * weight
        
        if weighted_score < 35:
            return SeverityLevel.CRITICAL
        elif weighted_score < 50:
            return SeverityLevel.HIGH
        elif weighted_score < 65:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _create_weakness_area(
        self,
        subject: str,
        current_score: float,
        related_to: str,
        analysis_basis: AnalysisBasis,
        topic: Optional[str] = None,
        severity: SeverityLevel = SeverityLevel.MEDIUM,
        confidence: float = 0.8,
        impact_on_interest: Optional[str] = None,
        impact_on_elective: Optional[str] = None,
        impact_on_career: Optional[str] = None
    ) -> WeaknessArea:
        """Create a WeaknessArea object with all details"""
        target_score = 75 if severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH] else 70
        gap = max(0, target_score - current_score)
        
        return WeaknessArea(
            subject=subject,
            topic=topic,
            current_score=current_score,
            target_score=target_score,
            gap_percentage=gap,
            severity=severity,
            confidence=confidence,
            related_to=related_to,
            analysis_basis=analysis_basis,
            improvement_suggestions=self._get_improvement_suggestions(subject, severity),
            recommended_resources=self._get_resources(subject, severity),
            estimated_improvement_time=self._estimate_improvement_time(gap, severity),
            priority=self._severity_to_priority(severity),
            impact_on_interest=impact_on_interest,
            impact_on_elective=impact_on_elective,
            impact_on_career=impact_on_career
        )
    
    def _merge_weaknesses(self, weaknesses: List[WeaknessArea]) -> List[WeaknessArea]:
        """Merge duplicate weaknesses and combine related_to fields"""
        merged: Dict[str, WeaknessArea] = {}
        
        for w in weaknesses:
            key = w.subject.lower()
            
            if key in merged:
                existing = merged[key]
                # Keep higher severity
                if self._severity_to_priority(w.severity) > self._severity_to_priority(existing.severity):
                    existing.severity = w.severity
                    existing.priority = w.priority
                # Combine related_to
                if w.related_to not in existing.related_to:
                    existing.related_to = f"{existing.related_to}, {w.related_to}"
                # Keep lower score (worse performance)
                if w.current_score < existing.current_score:
                    existing.current_score = w.current_score
                    existing.gap_percentage = max(existing.gap_percentage, w.gap_percentage)
                # Combine impacts
                if w.impact_on_interest and not existing.impact_on_interest:
                    existing.impact_on_interest = w.impact_on_interest
                if w.impact_on_elective and not existing.impact_on_elective:
                    existing.impact_on_elective = w.impact_on_elective
                if w.impact_on_career and not existing.impact_on_career:
                    existing.impact_on_career = w.impact_on_career
            else:
                merged[key] = w
        
        return list(merged.values())
    
    def _severity_to_priority(self, severity: SeverityLevel) -> int:
        """Convert severity to priority number"""
        priority_map = {
            SeverityLevel.CRITICAL: 5,
            SeverityLevel.HIGH: 4,
            SeverityLevel.MEDIUM: 3,
            SeverityLevel.LOW: 2
        }
        return priority_map.get(severity, 1)
    
    def _get_improvement_suggestions(self, subject: str, severity: SeverityLevel) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = {
            SeverityLevel.CRITICAL: [
                f"Seek immediate tutoring for {subject}",
                f"Schedule daily 2-hour study sessions for {subject}",
                f"Meet with {subject} professor during office hours",
                "Join or form a study group",
                "Complete all practice problems from textbook"
            ],
            SeverityLevel.HIGH: [
                f"Dedicate extra time to {subject} each week",
                f"Review {subject} fundamentals thoroughly",
                "Practice with previous year question papers",
                "Use online resources like Coursera/edX"
            ],
            SeverityLevel.MEDIUM: [
                f"Regular revision of {subject} concepts",
                "Solve additional practice problems",
                "Watch tutorial videos for difficult topics",
                "Discuss concepts with classmates"
            ],
            SeverityLevel.LOW: [
                f"Maintain current study pace for {subject}",
                "Focus on advanced topics",
                "Practice competitive problems"
            ]
        }
        return suggestions.get(severity, suggestions[SeverityLevel.MEDIUM])
    
    def _get_resources(self, subject: str, severity: SeverityLevel) -> List[Dict[str, Any]]:
        """Get recommended resources for a subject"""
        return [
            {
                "type": "course",
                "platform": "Coursera",
                "title": f"{subject} Fundamentals",
                "url": f"https://coursera.org/search?query={subject.replace(' ', '+')}"
            },
            {
                "type": "video",
                "platform": "YouTube",
                "title": f"Learn {subject}",
                "url": f"https://youtube.com/results?search_query={subject.replace(' ', '+')}+tutorial"
            },
            {
                "type": "practice",
                "platform": "LeetCode/HackerRank",
                "title": f"{subject} Practice Problems",
                "url": f"https://leetcode.com/problemset/all/?search={subject.replace(' ', '+')}"
            }
        ]
    
    def _estimate_improvement_time(self, gap: float, severity: SeverityLevel) -> str:
        """Estimate time needed to improve"""
        if severity == SeverityLevel.CRITICAL:
            return "8-12 weeks of intensive study"
        elif severity == SeverityLevel.HIGH:
            return "6-8 weeks with consistent effort"
        elif severity == SeverityLevel.MEDIUM:
            return "4-6 weeks with regular practice"
        else:
            return "2-4 weeks with focused revision"
    
    def _build_response(
        self,
        student_id: str,
        analysis_basis: AnalysisBasis,
        weaknesses: List[WeaknessArea],
        include_resources: bool,
        include_study_plan: bool
    ) -> WeaknessAnalysisResponse:
        """Build the final response object"""
        # Sort weaknesses by priority
        sorted_weaknesses = sorted(weaknesses, key=lambda x: x.priority, reverse=True)
        
        # Calculate counts
        critical_count = sum(1 for w in weaknesses if w.severity == SeverityLevel.CRITICAL)
        high_count = sum(1 for w in weaknesses if w.severity == SeverityLevel.HIGH)
        medium_count = sum(1 for w in weaknesses if w.severity == SeverityLevel.MEDIUM)
        low_count = sum(1 for w in weaknesses if w.severity == SeverityLevel.LOW)
        
        # Calculate overall risk score
        if weaknesses:
            severity_scores = [self._severity_to_priority(w.severity) for w in weaknesses]
            risk_score = (sum(severity_scores) / (len(severity_scores) * 5)) * 100
        else:
            risk_score = 0
        
        # Get priority areas
        priority_areas = [w.subject for w in sorted_weaknesses if w.priority >= 4][:5]
        
        # Generate key insights
        key_insights = self._generate_insights(weaknesses, analysis_basis)
        
        # Calculate improvement potential
        if weaknesses:
            avg_gap = np.mean([w.gap_percentage for w in weaknesses])
            improvement_potential = min(avg_gap * 0.7, 100)  # 70% of gap can be closed
        else:
            improvement_potential = 0
        
        # Collect all resources
        all_resources = []
        if include_resources:
            for w in sorted_weaknesses[:5]:
                all_resources.extend(w.recommended_resources)
        
        # Generate study plan
        study_plan = None
        if include_study_plan:
            study_plan = self._generate_study_plan(sorted_weaknesses[:5])
        
        return WeaknessAnalysisResponse(
            student_id=student_id,
            analysis_basis=analysis_basis,
            weaknesses=sorted_weaknesses,
            overall_risk_score=round(risk_score, 2),
            priority_areas=priority_areas,
            recommended_resources=all_resources[:10],
            study_plan=study_plan,
            total_weaknesses=len(weaknesses),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            key_insights=key_insights,
            improvement_potential=round(improvement_potential, 2)
        )
    
    def _generate_insights(
        self, 
        weaknesses: List[WeaknessArea],
        analysis_basis: AnalysisBasis
    ) -> List[str]:
        """Generate key insights from weaknesses"""
        insights = []
        
        critical_subjects = [w.subject for w in weaknesses if w.severity == SeverityLevel.CRITICAL]
        if critical_subjects:
            insights.append(
                f"Critical attention needed for: {', '.join(critical_subjects[:3])}"
            )
        
        if analysis_basis == AnalysisBasis.INTEREST:
            interest_gaps = [w for w in weaknesses if w.impact_on_interest]
            if interest_gaps:
                insights.append(
                    f"Your chosen interests require strengthening {len(interest_gaps)} foundational areas"
                )
        
        if analysis_basis == AnalysisBasis.ELECTIVES:
            elective_gaps = [w for w in weaknesses if w.impact_on_elective]
            if elective_gaps:
                insights.append(
                    f"Recommended electives need {len(elective_gaps)} prerequisites to be improved"
                )
        
        if len(weaknesses) == 0:
            insights.append("Excellent! No significant weaknesses detected based on analysis")
        elif len(weaknesses) <= 2:
            insights.append("Good overall performance with minor areas for improvement")
        elif len(weaknesses) <= 5:
            insights.append("Moderate improvement opportunities exist - focus on priority areas")
        else:
            insights.append("Multiple areas need attention - consider structured improvement plan")
        
        return insights
    
    def _generate_study_plan(self, priority_weaknesses: List[WeaknessArea]) -> Dict[str, Any]:
        """Generate a weekly study plan"""
        plan = {
            "duration": "8 weeks",
            "weekly_hours": 15,
            "phases": [],
            "milestones": []
        }
        
        # Phase 1: Foundations (Week 1-2)
        phase1_subjects = [w.subject for w in priority_weaknesses if w.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]][:2]
        plan["phases"].append({
            "name": "Foundation Building",
            "weeks": "1-2",
            "focus": phase1_subjects or ["Core concepts review"],
            "goals": ["Master fundamentals", "Complete basic exercises"]
        })
        
        # Phase 2: Practice (Week 3-5)
        plan["phases"].append({
            "name": "Active Practice",
            "weeks": "3-5",
            "focus": [w.subject for w in priority_weaknesses[:3]],
            "goals": ["Solve practice problems", "Work on assignments", "Peer learning"]
        })
        
        # Phase 3: Mastery (Week 6-8)
        plan["phases"].append({
            "name": "Mastery & Review",
            "weeks": "6-8",
            "focus": [w.subject for w in priority_weaknesses],
            "goals": ["Mock tests", "Advanced problems", "Final revision"]
        })
        
        # Milestones
        plan["milestones"] = [
            {"week": 2, "target": "Complete fundamentals review"},
            {"week": 4, "target": "Score 60%+ in practice tests"},
            {"week": 6, "target": "Score 70%+ in practice tests"},
            {"week": 8, "target": "Achieve target proficiency"}
        ]
        
        return plan
    
    async def _save_analysis_result(
        self,
        response: WeaknessAnalysisResponse,
        interests: Optional[List[str]],
        electives: Optional[List[str]],
        honours_minors: Optional[List[str]]
    ) -> None:
        """Save analysis result to database"""
        try:
            # Mark old analyses as not current
            await WeaknessAnalysisResult.find(
                WeaknessAnalysisResult.student_id == response.student_id,
                WeaknessAnalysisResult.is_current == True
            ).update({"$set": {"is_current": False}})
            
            # Create new analysis record
            result = WeaknessAnalysisResult(
                student_id=response.student_id,
                analysis_basis=response.analysis_basis.value,
                overall_score=100 - response.overall_risk_score,
                overall_risk_score=response.overall_risk_score,
                weaknesses=[w.dict() for w in response.weaknesses],
                priority_areas=response.priority_areas,
                ai_analysis={
                    "total_weaknesses": response.total_weaknesses,
                    "critical_count": response.critical_count,
                    "high_count": response.high_count,
                    "medium_count": response.medium_count,
                    "low_count": response.low_count
                },
                study_plan=response.study_plan or {},
                key_insights=response.key_insights,
                recommended_resources=response.recommended_resources,
                related_interests=interests or [],
                related_electives=electives or [],
                related_honours=honours_minors or [],
                is_current=True
            )
            
            await result.save()
            self.logger.info(f"Saved weakness analysis for student {response.student_id}")
            
        except Exception as e:
            self.logger.error(f"Error saving analysis result: {e}")
    
    async def get_latest_analysis(
        self, 
        student_id: str
    ) -> Optional[WeaknessAnalysisResult]:
        """Get the latest analysis for a student"""
        try:
            return await WeaknessAnalysisResult.find_one(
                WeaknessAnalysisResult.student_id == student_id,
                WeaknessAnalysisResult.is_current == True
            )
        except Exception as e:
            self.logger.error(f"Error fetching latest analysis: {e}")
            return None
    
    async def get_analysis_history(
        self,
        student_id: str,
        limit: int = 10
    ) -> List[WeaknessAnalysisResult]:
        """Get analysis history for a student"""
        try:
            return await WeaknessAnalysisResult.find(
                WeaknessAnalysisResult.student_id == student_id
            ).sort(-WeaknessAnalysisResult.analysis_date).limit(limit).to_list()
        except Exception as e:
            self.logger.error(f"Error fetching analysis history: {e}")
            return []
    
    async def sync_interests_from_all_sources(self, student_id: str) -> Dict[str, Any]:
        """
        Utility method to sync interests from all sources to StudentInterestProfile.
        Returns summary of what was found and synced.
        """
        result = {
            "student_id": student_id,
            "sources_checked": [],
            "interests_found": [],
            "synced": False,
            "source": None
        }
        
        try:
            from app.models.student_profile import StudentProfile
            from app.models.student import StudentPerformance
            
            # Check StudentInterestProfile
            interest_profile = await StudentInterestProfile.find_one(
                StudentInterestProfile.user_id == student_id
            )
            result["sources_checked"].append("StudentInterestProfile")
            
            if interest_profile and interest_profile.interests:
                result["interests_found"] = interest_profile.interests
                result["source"] = "StudentInterestProfile"
                return result
            
            # Check StudentProfile
            profile = await StudentProfile.find_one(
                StudentProfile.user_id == student_id
            )
            result["sources_checked"].append("StudentProfile")
            
            if profile and profile.interests:
                # Sync to StudentInterestProfile
                new_profile = StudentInterestProfile(
                    user_id=student_id,
                    interests=profile.interests,
                    career_goals=profile.career_goals if profile.career_goals else []
                )
                await new_profile.save()
                
                result["interests_found"] = profile.interests
                result["source"] = "StudentProfile"
                result["synced"] = True
                return result
            
            # Check StudentPerformance
            performance = await StudentPerformance.find_one(
                StudentPerformance.student_info.uid == student_id
            )
            result["sources_checked"].append("StudentPerformance")
            
            if performance and performance.interests:
                # Sync to StudentInterestProfile
                new_profile = StudentInterestProfile(
                    user_id=student_id,
                    interests=performance.interests,
                    career_goals=performance.career_goals if hasattr(performance, 'career_goals') else []
                )
                await new_profile.save()
                
                result["interests_found"] = performance.interests
                result["source"] = "StudentPerformance"
                result["synced"] = True
                return result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error syncing interests: {e}")
            result["error"] = str(e)
            return result


# Singleton instance
_weakness_service: Optional[WeaknessAnalysisService] = None


def get_weakness_analysis_service() -> WeaknessAnalysisService:
    """Get singleton instance of WeaknessAnalysisService"""
    global _weakness_service
    if _weakness_service is None:
        _weakness_service = WeaknessAnalysisService()
    return _weakness_service