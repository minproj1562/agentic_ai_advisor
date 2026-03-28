# app/services/pending_marks_service.py

from typing import Optional, List
import logging
from datetime import datetime
from app.models.pending_marks import PendingStudentMarks
from app.models.student_profile import StudentProfile, SemesterRecord

logger = logging.getLogger(__name__)

class PendingMarksService:
    
    async def link_pending_marks_to_student(
        self, 
        student_profile: StudentProfile
    ) -> int:
        """
        Link any pending marks to a newly registered student profile.
        Returns number of semesters linked.
        """
        try:
            # FIX: Search by both roll_number AND seat_number
            query_conditions = [
                {"roll_number": student_profile.roll_number, "linked_to_profile": False}
            ]
            
            if student_profile.current_seat_number:
                query_conditions.append({
                    "seat_number": student_profile.current_seat_number,
                    "linked_to_profile": False
                })
            
            for seat_rec in student_profile.seat_number_history:
                query_conditions.append({
                    "seat_number": seat_rec.seat_number,
                    "linked_to_profile": False
                })
            
            pending_marks = await PendingStudentMarks.find({
                "$or": query_conditions
            }).to_list()
            
            if not pending_marks:
                logger.info(f"No pending marks found for {student_profile.roll_number}")
                return 0
            
            logger.info(f"Found {len(pending_marks)} pending marks entries for {student_profile.roll_number}")
            
            linked_count = 0
            
            for pending in pending_marks:
                # Create semester record from pending marks
                sem_rec = SemesterRecord(
                    semester_number=pending.semester_number,
                    academic_year=pending.academic_year,
                    subjects=pending.subjects,
                    sgpa=pending.sgpa,
                    total_credits=pending.total_credits,
                    credits_earned=pending.credits_earned,
                    is_complete=True,
                    created_at=pending.upload_timestamp
                )
                
                # Check if semester already exists
                idx = next(
                    (i for i, sr in enumerate(student_profile.semester_records)
                     if sr.semester_number == pending.semester_number),
                    None
                )
                
                if idx is not None:
                    student_profile.semester_records[idx] = sem_rec
                else:
                    student_profile.semester_records.append(sem_rec)
                
                # Mark pending marks as linked
                pending.linked_to_profile = True
                pending.linked_user_id = student_profile.user_id
                await pending.replace()  # FIX: was .save()
                
                linked_count += 1
            
            # Sort semester records
            student_profile.semester_records.sort(key=lambda x: x.semester_number)
            
            # Recalculate CGPA
            agp = ac = ace = 0.0
            for sr in student_profile.semester_records:
                if sr.is_complete and sr.total_credits > 0:
                    agp += sr.sgpa * sr.total_credits
                    ac += sr.total_credits
                    ace += sr.credits_earned
            
            student_profile.cgpa = round(agp / ac, 2) if ac > 0 else 0.0
            student_profile.total_credits_earned = int(ace)
            student_profile.marks_synced_at = datetime.now()
            student_profile.last_updated = datetime.now()
            
            # FIX: Use replace() for nested document changes
            await student_profile.replace()
            
            logger.info(f"Successfully linked {linked_count} semesters for {student_profile.roll_number}")
            return linked_count
            
        except Exception as e:
            logger.error(f"Error linking pending marks: {e}", exc_info=True)
            return 0
    
    async def get_pending_marks_summary(self, branch: Optional[str] = None) -> dict:
        """Get summary of all pending marks"""
        query = {"linked_to_profile": False}
        if branch:
            query["branch"] = branch
        
        pending = await PendingStudentMarks.find(query).to_list()
        
        # Group by roll number
        by_student = {}
        for p in pending:
            if p.roll_number not in by_student:
                by_student[p.roll_number] = {
                    "roll_number": p.roll_number,
                    "student_name": p.student_name,
                    "branch": p.branch,
                    "semesters": []
                }
            by_student[p.roll_number]["semesters"].append({
                "semester": p.semester_number,
                "sgpa": p.sgpa,
                "credits": p.credits_earned,
                "uploaded_at": p.upload_timestamp
            })
        
        return {
            "total_students": len(by_student),
            "total_records": len(pending),
            "students": list(by_student.values())
        }

pending_marks_service = PendingMarksService()