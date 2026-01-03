#academic-advisor-backend/app/services/academic_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.student_profile import StudentProfile, SemesterRecord, SubjectScore, Branch, Grade
from app.core.security import FirebaseUser
import logging

logger = logging.getLogger(__name__)

class AcademicService:
    
    async def create_or_update_profile(
        self, 
        user: FirebaseUser, 
        profile_data: dict
    ) -> StudentProfile:
        """Create or update student profile"""
        
        # Calculate current semester and academic year
        current_semester, academic_year = self._calculate_current_semester(
            profile_data["admission_year"]
        )
        
        # Check if profile exists
        existing_profile = await StudentProfile.find_one(
            StudentProfile.user_id == user.uid
        )
        
        if existing_profile:
            # Update existing profile
            for field, value in profile_data.items():
                if hasattr(existing_profile, field):
                    setattr(existing_profile, field, value)
            
            existing_profile.current_semester = current_semester
            existing_profile.current_academic_year = academic_year
            existing_profile.last_updated = datetime.now()
            await existing_profile.save()
            return existing_profile
        else:
            # Create new profile
            profile = StudentProfile(
                user_id=user.uid,
                current_semester=current_semester,
                current_academic_year=academic_year,
                **profile_data
            )
            await profile.insert()
            return profile
    
    async def get_student_profile(self, user: FirebaseUser) -> Optional[StudentProfile]:
        """Get student profile"""
        return await StudentProfile.find_one(StudentProfile.user_id == user.uid)
    
    async def add_semester_scores(
        self,
        user: FirebaseUser,
        semester_number: int,
        academic_year: str,
        subjects: List[dict]
    ) -> Dict[str, Any]:
        """Add subject scores for a semester"""
        
        # Get or create semester record
        semester_record = await SemesterRecord.find_one({
            "student_id": user.uid,
            "semester_number": semester_number
        })
        
        if not semester_record:
            semester_record = SemesterRecord(
                student_id=user.uid,
                semester_number=semester_number,
                academic_year=academic_year,
                is_completed=True
            )
            await semester_record.insert()
        
        # Process subjects
        subject_scores = []
        total_grade_points = 0
        total_credits = 0
        passed_subjects = 0
        failed_subjects = 0
        
        for subject_data in subjects:
            # Calculate total marks and grade
            total_marks = subject_data["internal_marks"] + subject_data["external_marks"]
            grade_info = self._calculate_grade(total_marks)
            
            # Create subject score
            subject_score = SubjectScore(
                student_id=user.uid,
                semester_id=str(semester_record.id),
                semester_number=semester_number,
                subject_code=subject_data["subject_code"],
                subject_name=subject_data["subject_name"],
                credits=subject_data["credits"],
                internal_marks=subject_data["internal_marks"],
                external_marks=subject_data["external_marks"],
                total_marks=total_marks,
                grade=grade_info["grade"],
                grade_points=grade_info["points"],
                is_elective=subject_data.get("is_elective", False),
                is_practical=subject_data.get("is_practical", False),
                is_backlog=grade_info["grade"] == Grade.F,
                attempt_number=1
            )
            
            await subject_score.insert()
            subject_scores.append(subject_score)
            
            # Update semester statistics
            if grade_info["grade"] != Grade.F:
                total_grade_points += grade_info["points"] * subject_data["credits"]
                total_credits += subject_data["credits"]
                passed_subjects += 1
            else:
                failed_subjects += 1
        
        # Calculate SGPA
        sgpa = total_grade_points / total_credits if total_credits > 0 else 0
        
        # Update semester record
        semester_record.sgpa = round(sgpa, 2)
        semester_record.credits_earned = total_credits
        semester_record.total_subjects = len(subjects)
        semester_record.passed_subjects = passed_subjects
        semester_record.failed_subjects = failed_subjects
        await semester_record.save()
        
        # Update overall CGPA
        await self._update_cgpa(user.uid)
        
        return {
            "semester_sgpa": round(sgpa, 2),
            "credits_earned": total_credits,
            "subjects_added": len(subjects),
            "passed_subjects": passed_subjects,
            "failed_subjects": failed_subjects
        }
    
    async def get_semester_scores(
        self, 
        user: FirebaseUser, 
        semester_number: Optional[int] = None
    ) -> List[SubjectScore]:
        """Get subject scores for a semester"""
        query = {"student_id": user.uid}
        if semester_number:
            query["semester_number"] = semester_number
        
        return await SubjectScore.find(query).to_list()
    
    async def get_semester_records(self, user: FirebaseUser) -> List[SemesterRecord]:
        """Get all semester records for a student"""
        return await SemesterRecord.find(
            SemesterRecord.student_id == user.uid
        ).sort("semester_number").to_list()
    
    def _calculate_current_semester(self, admission_year: int) -> tuple[int, str]:
        """Calculate current semester and academic year"""
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        
        if current_month >= 7:  # July-December (Odd semester)
            academic_year = f"{current_year}-{current_year + 1}"
            semester = (current_year - admission_year) * 2 + 1
        else:  # January-June (Even semester)
            academic_year = f"{current_year - 1}-{current_year}"
            semester = (current_year - admission_year) * 2
        
        # Cap at 8 semesters
        semester = max(1, min(semester, 8))
        
        return semester, academic_year
    
    def _calculate_grade(self, total_marks: float) -> Dict[str, Any]:
        """Calculate grade from total marks"""
        if total_marks >= 90:
            return {"grade": Grade.O, "points": 10}
        elif total_marks >= 80:
            return {"grade": Grade.A_PLUS, "points": 9}
        elif total_marks >= 70:
            return {"grade": Grade.A, "points": 8}
        elif total_marks >= 60:
            return {"grade": Grade.B_PLUS, "points": 7}
        elif total_marks >= 50:
            return {"grade": Grade.B, "points": 6}
        elif total_marks >= 45:
            return {"grade": Grade.C, "points": 5}
        elif total_marks >= 40:
            return {"grade": Grade.P, "points": 4}
        else:
            return {"grade": Grade.F, "points": 0}
    
    async def _update_cgpa(self, user_id: str):
        """Update overall CGPA"""
        # Get all completed semesters
        semesters = await SemesterRecord.find({
            "student_id": user_id,
            "is_completed": True
        }).to_list()
        
        if not semesters:
            return
        
        total_grade_points = 0
        total_credits = 0
        
        for semester in semesters:
            # Get all subject scores for this semester
            subject_scores = await SubjectScore.find({
                "student_id": user_id,
                "semester_number": semester.semester_number,
                "is_backlog": False
            }).to_list()
            
            for subject in subject_scores:
                if subject.grade_points and subject.grade != Grade.F:
                    total_grade_points += subject.grade_points * subject.credits
                    total_credits += subject.credits
        
        # Calculate CGPA
        cgpa = total_grade_points / total_credits if total_credits > 0 else 0
        
        # Update profile
        profile = await StudentProfile.find_one(StudentProfile.user_id == user_id)
        if profile:
            profile.cgpa = round(cgpa, 2)
            profile.total_credits_earned = total_credits
            profile.last_updated = datetime.now()
            await profile.save()