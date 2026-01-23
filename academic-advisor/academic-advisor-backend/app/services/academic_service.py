# academic-advisor-backend/app/services/academic_service.py

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.student_profile import StudentProfile, SemesterRecord, SubjectScore
from app.core.security import FirebaseUser
from app.core.curriculum import get_semester_subjects, get_elective_options

logger = logging.getLogger(__name__)


class AcademicService:
    """Academic Service with curriculum-aware subject handling"""
    
    def _calculate_current_semester(self, admission_year: int) -> tuple:
        """Calculate current semester and academic year"""
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        
        if current_month >= 7:  # July-December (Odd semester)
            academic_year = f"{current_year}-{str(current_year + 1)[2:]}"
            semester = (current_year - admission_year) * 2 + 1
        else:  # January-June (Even semester)
            academic_year = f"{current_year - 1}-{str(current_year)[2:]}"
            semester = (current_year - admission_year) * 2
        
        semester = max(1, min(semester, 8))
        return semester, academic_year
    
    def _calculate_grade(self, total_marks: float) -> Dict[str, Any]:
        """Calculate grade from total marks"""
        if total_marks >= 90:
            return {"grade": "O", "points": 10.0}
        elif total_marks >= 80:
            return {"grade": "A+", "points": 9.0}
        elif total_marks >= 70:
            return {"grade": "A", "points": 8.0}
        elif total_marks >= 60:
            return {"grade": "B+", "points": 7.0}
        elif total_marks >= 50:
            return {"grade": "B", "points": 6.0}
        elif total_marks >= 45:
            return {"grade": "C", "points": 5.0}
        elif total_marks >= 40:
            return {"grade": "P", "points": 4.0}
        else:
            return {"grade": "F", "points": 0.0}
    
    async def get_student_profile(self, user: FirebaseUser) -> Optional[StudentProfile]:
        """Get student profile"""
        return await StudentProfile.find_one(StudentProfile.user_id == user.uid)
    
    async def get_available_subjects(self, user: FirebaseUser, semester: int) -> Dict[str, Any]:
        """Get available subjects for a semester based on student's admission year"""
        profile = await self.get_student_profile(user)
        
        if not profile:
            raise ValueError("Student profile not found")
        
        subjects = get_semester_subjects(semester, profile.admission_year)
        
        # Group subjects by type
        theory_subjects = []
        lab_subjects = []
        project_subjects = []
        elective_groups = {}
        
        for subject in subjects:
            subject_dict = {
                "subject_code": subject.subject_code,
                "subject_name": subject.subject_name,
                "credits": subject.credits,
                "course_type": subject.course_type,
                "internal_max": subject.internal_max,
                "external_max": subject.external_max,
                "is_elective": subject.is_elective,
                "is_practical": subject.is_practical
            }
            
            if subject.is_elective and subject.elective_group:
                if subject.elective_group not in elective_groups:
                    elective_groups[subject.elective_group] = {
                        "group_name": subject.elective_group,
                        "subject_template": subject_dict,
                        "options": get_elective_options(subject.elective_group)
                    }
            elif subject.is_practical or subject.course_type in ["LBC", "SBL"]:
                lab_subjects.append(subject_dict)
            elif subject.course_type in ["MNP", "MJP", "INT"]:
                project_subjects.append(subject_dict)
            else:
                theory_subjects.append(subject_dict)
        
        return {
            "semester": semester,
            "admission_year": profile.admission_year,
            "curriculum_type": "Pre-Autonomy" if profile.admission_year < 2024 and semester <= 4 else "Autonomy",
            "theory_subjects": theory_subjects,
            "lab_subjects": lab_subjects,
            "project_subjects": project_subjects,
            "elective_groups": elective_groups
        }
    
    async def create_or_update_profile(
        self, 
        user: FirebaseUser, 
        profile_data: Dict[str, Any]
    ) -> StudentProfile:
        """Create or update student profile"""
        user_id = user.uid
        user_email = user.email or ""
        
        logger.info(f"Creating/updating profile for user: {user_id}")
        
        admission_year = profile_data.get("admission_year", datetime.now().year)
        current_semester, academic_year = self._calculate_current_semester(admission_year)
        
        existing_profile = await StudentProfile.find_one(StudentProfile.user_id == user_id)
        
        if existing_profile:
            existing_profile.name = profile_data.get("name", existing_profile.name)
            existing_profile.roll_number = profile_data.get("roll_number", existing_profile.roll_number)
            existing_profile.branch = profile_data.get("branch", existing_profile.branch)
            existing_profile.admission_year = admission_year
            existing_profile.email = profile_data.get("email", user_email)
            existing_profile.current_semester = current_semester
            existing_profile.current_academic_year = academic_year
            existing_profile.last_updated = datetime.now()
            
            await existing_profile.save()
            logger.info(f"Updated profile for user: {user_id}")
            return existing_profile
        
        new_profile = StudentProfile(
            user_id=user_id,
            name=profile_data.get("name", ""),
            roll_number=profile_data.get("roll_number", ""),
            branch=profile_data.get("branch", "IT"),
            admission_year=admission_year,
            email=profile_data.get("email", user_email),
            current_semester=current_semester,
            current_academic_year=academic_year,
            cgpa=0.0,
            total_credits_earned=0,
            total_credits_required=160,
            semester_records=[],
            skills=[],
            interests=[],
            career_goals=[],
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        await new_profile.insert()
        logger.info(f"Created profile for user: {user_id}")
        return new_profile
    
    async def add_semester_scores(
        self,
        user: FirebaseUser,
        semester_number: int,
        academic_year: str,
        subjects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Add subject scores for a semester"""
        user_id = user.uid
        logger.info(f"Adding scores for user: {user_id}, semester: {semester_number}")
        
        profile = await StudentProfile.find_one(StudentProfile.user_id == user_id)
        
        if not profile:
            raise ValueError("Student profile not found. Please create your profile first.")
        
        processed_subjects = []
        total_grade_points = 0.0
        total_credits = 0
        credits_earned = 0
        
        for subject_data in subjects:
            internal_marks = float(subject_data.get("internal_marks", 0))
            external_marks = float(subject_data.get("external_marks", 0))
            total_marks = internal_marks + external_marks
            
            grade_info = self._calculate_grade(total_marks)
            credits = int(subject_data.get("credits", 3))
            
            subject_score = SubjectScore(
                subject_code=subject_data.get("subject_code", ""),
                subject_name=subject_data.get("subject_name", ""),
                credits=credits,
                internal_marks=internal_marks,
                external_marks=external_marks,
                total_marks=total_marks,
                grade=grade_info["grade"],
                grade_points=grade_info["points"],
                is_elective=bool(subject_data.get("is_elective", False)),
                is_practical=bool(subject_data.get("is_practical", False))
            )
            
            processed_subjects.append(subject_score)
            
            total_credits += credits
            if grade_info["grade"] != "F":
                total_grade_points += grade_info["points"] * credits
                credits_earned += credits
        
        sgpa = round(total_grade_points / total_credits, 2) if total_credits > 0 else 0.0
        
        semester_record = SemesterRecord(
            semester_number=semester_number,
            academic_year=academic_year,
            subjects=processed_subjects,
            sgpa=sgpa,
            total_credits=total_credits,
            credits_earned=credits_earned,
            is_complete=True,
            created_at=datetime.now()
        )
        
        existing_index = None
        for i, existing_sem in enumerate(profile.semester_records):
            if existing_sem.semester_number == semester_number:
                existing_index = i
                break
        
        if existing_index is not None:
            profile.semester_records[existing_index] = semester_record
        else:
            profile.semester_records.append(semester_record)
            profile.semester_records.sort(key=lambda x: x.semester_number)
        
        # Recalculate CGPA
        all_grade_points = 0.0
        all_credits = 0
        all_credits_earned = 0
        
        for sem in profile.semester_records:
            if sem.is_complete and sem.total_credits > 0:
                all_grade_points += sem.sgpa * sem.total_credits
                all_credits += sem.total_credits
                all_credits_earned += sem.credits_earned
        
        profile.cgpa = round(all_grade_points / all_credits, 2) if all_credits > 0 else 0.0
        profile.total_credits_earned = all_credits_earned
        profile.last_updated = datetime.now()
        
        await profile.save()
        
        return {
            "semester_number": semester_number,
            "academic_year": academic_year,
            "semester_sgpa": sgpa,
            "credits_earned": credits_earned,
            "total_credits": total_credits,
            "subjects_added": len(processed_subjects),
            "updated_cgpa": profile.cgpa,
            "total_credits_earned": profile.total_credits_earned
        }
    
    async def get_semester_scores(
        self, 
        user: FirebaseUser, 
        semester_number: Optional[int] = None
    ) -> List[SubjectScore]:
        """Get subject scores"""
        profile = await self.get_student_profile(user)
        
        if not profile:
            return []
        
        if semester_number is not None:
            for sem in profile.semester_records:
                if sem.semester_number == semester_number:
                    return sem.subjects
            return []
        
        all_subjects = []
        for sem in profile.semester_records:
            all_subjects.extend(sem.subjects)
        
        return all_subjects
    
    async def get_semester_records(self, user: FirebaseUser) -> List[SemesterRecord]:
        """Get all semester records"""
        profile = await self.get_student_profile(user)
        
        if not profile:
            return []
        
        return profile.semester_records