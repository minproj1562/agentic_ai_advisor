# app/routers/academic.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel
from datetime import datetime
from app.models.student_profile import StudentProfile, SemesterRecord, SubjectScore
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/academic", tags=["Academic"])


class SubjectInput(BaseModel):
    subject_code: str
    subject_name: str
    credits: int
    internal_marks: float
    external_marks: float
    total_marks: float
    grade: str
    grade_points: float
    is_elective: bool = False
    is_practical: bool = False


class SemesterInput(BaseModel):
    semester_number: int
    academic_year: str
    subjects: List[SubjectInput]


@router.post("/scores/add")
async def add_semester_scores(
    data: SemesterInput,
    current_user: dict = Depends(get_current_user)
):
    """Add or update semester scores"""
    try:
        user_id = current_user.get("uid")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        # Find student profile
        profile = await StudentProfile.find_one(StudentProfile.user_id == user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found. Please create your profile first."
            )
        
        # Convert subjects to SubjectScore objects
        subjects = []
        total_credits = 0
        total_grade_points = 0
        credits_earned = 0
        
        for subj in data.subjects:
            subject_score = SubjectScore(
                subject_code=subj.subject_code,
                subject_name=subj.subject_name,
                credits=subj.credits,
                internal_marks=subj.internal_marks,
                external_marks=subj.external_marks,
                total_marks=subj.total_marks,
                grade=subj.grade,
                grade_points=subj.grade_points,
                is_elective=subj.is_elective,
                is_practical=subj.is_practical
            )
            subjects.append(subject_score)
            
            total_credits += subj.credits
            total_grade_points += subj.credits * subj.grade_points
            
            # Credits earned (passing grade)
            if subj.grade_points >= 4:  # P grade or above
                credits_earned += subj.credits
        
        # Calculate SGPA
        sgpa = round(total_grade_points / total_credits, 2) if total_credits > 0 else 0.0
        
        # Create semester record
        semester_record = SemesterRecord(
            semester_number=data.semester_number,
            academic_year=data.academic_year,
            subjects=subjects,
            sgpa=sgpa,
            total_credits=total_credits,
            credits_earned=credits_earned,
            is_complete=True,
            created_at=datetime.now()
        )
        
        # Check if semester already exists
        existing_index = None
        for i, record in enumerate(profile.semester_records):
            if record.semester_number == data.semester_number:
                existing_index = i
                break
        
        if existing_index is not None:
            # Update existing semester
            profile.semester_records[existing_index] = semester_record
        else:
            # Add new semester
            profile.semester_records.append(semester_record)
        
        # Sort semester records
        profile.semester_records.sort(key=lambda x: x.semester_number)
        
        # Recalculate CGPA
        total_credit_points = 0
        total_credits_all = 0
        total_credits_earned = 0
        
        for record in profile.semester_records:
            total_credit_points += record.sgpa * record.total_credits
            total_credits_all += record.total_credits
            total_credits_earned += record.credits_earned
        
        profile.cgpa = round(total_credit_points / total_credits_all, 2) if total_credits_all > 0 else 0.0
        profile.total_credits_earned = total_credits_earned
        profile.last_updated = datetime.now()
        
        # Save profile
        await profile.save()
        
        return {
            "message": "Semester data saved successfully",
            "semester_number": data.semester_number,
            "semester_sgpa": sgpa,
            "cgpa": profile.cgpa,
            "total_credits_earned": total_credits_earned,
            "subjects_count": len(subjects)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error saving semester scores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save semester scores: {str(e)}"
        )