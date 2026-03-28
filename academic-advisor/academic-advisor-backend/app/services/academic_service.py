# app/services/academic_service.py
"""
Academic Service with curriculum-aware subject handling
FIXED: pending_marks_checked flag, .replace() usage, re-upload support
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.student_profile import (
    StudentProfile, SemesterRecord, SubjectScore, SeatNumberRecord
)
from app.models.pending_marks import PendingStudentMarks
from app.core.security import FirebaseUser
from app.core.curriculum import get_semester_subjects, get_elective_options
from app.services.pending_marks_service import pending_marks_service

logger = logging.getLogger(__name__)


class AcademicService:
    """Academic Service with curriculum-aware subject handling"""

    def _calculate_current_semester(self, admission_year: int) -> tuple:
        """Calculate current semester and academic year"""
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month

        if current_month >= 7:
            academic_year = f"{current_year}-{str(current_year + 1)[2:]}"
            year_diff = current_year - admission_year
            semester = (year_diff * 2) + 1
        else:
            academic_year = f"{current_year - 1}-{str(current_year)[2:]}"
            year_diff = current_year - admission_year
            semester = year_diff * 2

        semester = max(1, min(semester, 8))

        logger.info(
            f"Calculated semester: {semester} for admission year: "
            f"{admission_year}, current month: {current_month}"
        )
        return semester, academic_year

    def _calculate_grade(
        self, total_marks: float, max_marks: float = 100.0
    ) -> Dict[str, Any]:
        """Calculate grade from total marks using percentage"""
        if max_marks <= 0:
            max_marks = 100.0
        percentage = (total_marks / max_marks) * 100.0

        if percentage >= 90:
            return {"grade": "O", "points": 10.0}
        elif percentage >= 80:
            return {"grade": "A+", "points": 9.0}
        elif percentage >= 70:
            return {"grade": "A", "points": 8.0}
        elif percentage >= 60:
            return {"grade": "B+", "points": 7.0}
        elif percentage >= 50:
            return {"grade": "B", "points": 6.0}
        elif percentage >= 45:
            return {"grade": "C", "points": 5.0}
        elif percentage >= 40:
            return {"grade": "P", "points": 4.0}
        else:
            return {"grade": "F", "points": 0.0}

    async def get_student_profile(
        self, user: FirebaseUser
    ) -> Optional[StudentProfile]:
        """
        Get student profile and auto-fetch pending marks.
        FIXED: Always re-check if pending_marks_checked is False,
        or if marks_synced_at is None (first time).
        """
        profile = await StudentProfile.find_one(
            StudentProfile.user_id == user.uid
        )

        if not profile:
            return None
        # ═══════════════════════════════════════════
        # FIX: Re-check pending marks if flag is False
        # The flag is reset by admin re-uploads and by
        # the save() method in bulk_marks_service.
        # ═══════════════════════════════════════════
        should_check = (
            not profile.pending_marks_checked
            or profile.marks_synced_at is None
        )

        if should_check:
            linked = await self._auto_fetch_pending_marks(profile)
            if linked > 0:
                profile = await StudentProfile.find_one(
                    StudentProfile.user_id == user.uid
                )

        return profile


    async def get_available_subjects(
        self, user: FirebaseUser, semester: int
    ) -> Dict[str, Any]:
        """Get available subjects for a semester"""
        profile = await self.get_student_profile(user)

        if not profile:
            raise ValueError(
                "Student profile not found. Please create your profile first."
            )

        subjects = get_semester_subjects(semester, profile.admission_year)

        if not subjects:
            logger.warning(
                f"No subjects found for semester {semester}, "
                f"admission_year {profile.admission_year}"
            )

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
                "is_practical": subject.is_practical,
                "elective_group": subject.elective_group,
            }

            if subject.is_elective and subject.elective_group:
                if subject.elective_group not in elective_groups:
                    elective_groups[subject.elective_group] = {
                        "group_name": subject.elective_group,
                        "subject_template": subject_dict,
                        "options": get_elective_options(
                            subject.elective_group
                        ),
                    }
            elif subject.is_practical or subject.course_type in [
                "LBC", "SBL"
            ]:
                lab_subjects.append(subject_dict)
            elif subject.course_type in ["MNP", "MJP", "INT"]:
                project_subjects.append(subject_dict)
            else:
                theory_subjects.append(subject_dict)

        if profile.admission_year <= 2024 and semester <= 4:
            curriculum_type = "Pre-Autonomy"
        else:
            curriculum_type = "Autonomy"

        return {
            "semester": semester,
            "admission_year": profile.admission_year,
            "curriculum_type": curriculum_type,
            "theory_subjects": theory_subjects,
            "lab_subjects": lab_subjects,
            "project_subjects": project_subjects,
            "elective_groups": elective_groups,
        }

# ═══════════════════════════════════════════════════════════
# In academic_service.py — REPLACE create_or_update_profile with this:
# ═══════════════════════════════════════════════════════════

    async def create_or_update_profile(
        self,
        user: FirebaseUser,
        profile_data: Dict[str, Any],
    ) -> StudentProfile:
        """
        Create or update student profile.
        FIXED: Merges with placeholder profiles from add_students_batch.
        """
        user_id = user.uid
        user_email = user.email or ""

        logger.info(f"Creating/updating profile for user: {user_id}")

        admission_year = profile_data.get(
            "admission_year", datetime.now().year
        )
        current_semester, academic_year = self._calculate_current_semester(
            admission_year
        )

        # ── Check for existing profile by Firebase UID ──
        existing_profile = await StudentProfile.find_one(
            StudentProfile.user_id == user_id
        )

        seat_number = profile_data.get("seat_number")
        if seat_number and not (
            len(str(seat_number)) == 5 and str(seat_number).isdigit()
        ):
            seat_number = None

        if existing_profile:
            # Update existing profile
            existing_profile.name = profile_data.get("name", existing_profile.name)
            existing_profile.roll_number = profile_data.get(
                "roll_number", existing_profile.roll_number
            )
            existing_profile.branch = profile_data.get("branch", existing_profile.branch)
            existing_profile.admission_year = admission_year
            existing_profile.email = profile_data.get("email", user_email)
            existing_profile.current_semester = current_semester
            existing_profile.current_academic_year = academic_year
            existing_profile.last_updated = datetime.now()

            if seat_number and seat_number != existing_profile.current_seat_number:
                existing_profile.current_seat_number = seat_number
                existing_profile.seat_number_history.append(
                    SeatNumberRecord(
                        seat_number=seat_number,
                        semester=current_semester,
                        academic_year=academic_year,
                    )
                )

            existing_profile.pending_marks_checked = False  # Reset to re-check
            await existing_profile.replace()
            await self._auto_fetch_pending_marks(existing_profile)
            return await StudentProfile.find_one(StudentProfile.user_id == user_id)

        # ═══════════════════════════════════════════
        # FIX: Check for placeholder profile with same
        # roll_number (from add_students_batch) and MERGE
        # ═══════════════════════════════════════════
        roll_number = profile_data.get("roll_number", "").strip()
        if roll_number:
            placeholder = await StudentProfile.find_one({
                "roll_number": roll_number,
                "user_id": {"$regex": "^pending_"}
            })

            if placeholder:
                logger.info(
                    f"Merging placeholder profile for {roll_number} "
                    f"with real user {user_id}"
                )
                # Take over the placeholder — keep any existing semester_records
                placeholder.user_id = user_id
                placeholder.name = profile_data.get("name", placeholder.name)
                placeholder.email = profile_data.get("email", user_email)
                placeholder.branch = profile_data.get("branch", placeholder.branch)
                placeholder.admission_year = admission_year
                placeholder.current_semester = current_semester
                placeholder.current_academic_year = academic_year
                placeholder.last_updated = datetime.now()
                placeholder.pending_marks_checked = False

                if seat_number:
                    placeholder.current_seat_number = seat_number
                    placeholder.seat_number_history.append(
                        SeatNumberRecord(
                            seat_number=seat_number,
                            semester=current_semester,
                            academic_year=academic_year,
                        )
                    )

                await placeholder.replace()
                await self._auto_fetch_pending_marks(placeholder)
                logger.info(
                    f"Merged placeholder → real profile: {roll_number}, "
                    f"semesters: {len(placeholder.semester_records)}"
                )
                return await StudentProfile.find_one(
                    StudentProfile.user_id == user_id
                )

        # ── Create brand new profile ──
        new_profile = StudentProfile(
            user_id=user_id,
            name=profile_data.get("name", ""),
            roll_number=roll_number,
            current_seat_number=seat_number,
            seat_number_history=[
                SeatNumberRecord(
                    seat_number=seat_number,
                    semester=current_semester,
                    academic_year=academic_year,
                )
            ] if seat_number else [],
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
            pending_marks_checked=False,  # Will check on first load
            created_at=datetime.now(),
            last_updated=datetime.now(),
        )

        await new_profile.insert()
        await self._auto_fetch_pending_marks(new_profile)
        return await StudentProfile.find_one(StudentProfile.user_id == user_id)

    async def update_seat_number(
        self,
        user: FirebaseUser,
        seat_number: str,
        semester: Optional[int] = None,
    ) -> StudentProfile:
        """Update student's seat number and check for pending marks"""
        profile = await StudentProfile.find_one(
            StudentProfile.user_id == user.uid
        )

        if not profile:
            raise ValueError(
                "Student profile not found. Please create your profile first."
            )

        # Validate 5 digits
        if not (len(seat_number) == 5 and seat_number.isdigit()):
            raise ValueError("Seat number must be exactly 5 digits")

        if semester is None:
            semester = profile.current_semester

        profile.current_seat_number = seat_number

        existing_record = next(
            (
                sr
                for sr in profile.seat_number_history
                if sr.seat_number == seat_number and sr.semester == semester
            ),
            None,
        )

        if not existing_record:
            seat_record = SeatNumberRecord(
                seat_number=seat_number,
                semester=semester,
                academic_year=profile.current_academic_year,
            )
            profile.seat_number_history.append(seat_record)

        profile.last_updated = datetime.now()
        # ═══════════════════════════════════════════
        # FIX: Reset flag to re-check pending marks
        # ═══════════════════════════════════════════
        profile.pending_marks_checked = True
        await profile.replace()

        marks_found = await self._auto_fetch_pending_marks(profile)

        # Re-fetch to get latest state
        profile = await StudentProfile.find_one(
            StudentProfile.user_id == user.uid
        )

        logger.info(
            f"Updated seat number for user {user.uid}: "
            f"{seat_number}, marks found: {marks_found}"
        )
        return profile

    async def add_semester_scores(
        self,
        user: FirebaseUser,
        semester_number: int,
        academic_year: str,
        subjects: List[Dict[str, Any]],
        study_hours: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Add subject scores for a semester"""
        user_id = user.uid
        logger.info(
            f"Adding scores for user: {user_id}, semester: {semester_number}"
        )

        profile = await StudentProfile.find_one(
            StudentProfile.user_id == user_id
        )

        if not profile:
            raise ValueError(
                "Student profile not found. Please create your profile first."
            )

        processed_subjects = []
        total_grade_points = 0.0
        total_credits = 0
        credits_earned = 0

        for subject_data in subjects:
            internal_marks = float(subject_data.get("internal_marks", 0))
            external_marks = float(subject_data.get("external_marks", 0))
            total_marks = internal_marks + external_marks

            internal_max = float(subject_data.get("internal_max", 20))
            external_max = float(subject_data.get("external_max", 80))
            max_marks = internal_max + external_max

            grade_info = self._calculate_grade(total_marks, max_marks)
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
                is_practical=bool(subject_data.get("is_practical", False)),
            )

            processed_subjects.append(subject_score)
            total_credits += credits
            if grade_info["grade"] != "F":
                total_grade_points += grade_info["points"] * credits
                credits_earned += credits

        sgpa = (
            round(total_grade_points / total_credits, 2)
            if total_credits > 0
            else 0.0
        )

        semester_record = SemesterRecord(
            semester_number=semester_number,
            academic_year=academic_year,
            subjects=processed_subjects,
            sgpa=sgpa,
            total_credits=total_credits,
            credits_earned=credits_earned,
            is_complete=True,
            created_at=datetime.now(),
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

        all_grade_points = 0.0
        all_credits = 0
        all_credits_earned = 0

        for sem in profile.semester_records:
            if sem.is_complete and sem.total_credits > 0:
                all_grade_points += sem.sgpa * sem.total_credits
                all_credits += sem.total_credits
                all_credits_earned += sem.credits_earned

        profile.cgpa = (
            round(all_grade_points / all_credits, 2) if all_credits > 0 else 0.0
        )
        profile.total_credits_earned = all_credits_earned
        profile.last_updated = datetime.now()

        # ═══════════════════════════════════════════
        # FIX: Use replace() for nested doc changes
        # ═══════════════════════════════════════════
        await profile.replace()

        return {
            "semester_number": semester_number,
            "academic_year": academic_year,
            "semester_sgpa": sgpa,
            "credits_earned": credits_earned,
            "total_credits": total_credits,
            "subjects_added": len(processed_subjects),
            "updated_cgpa": profile.cgpa,
            "total_credits_earned": profile.total_credits_earned,
        }

    async def get_semester_scores(
        self,
        user: FirebaseUser,
        semester_number: Optional[int] = None,
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

    async def get_semester_records(
        self, user: FirebaseUser
    ) -> List[SemesterRecord]:
        """Get all semester records"""
        profile = await self.get_student_profile(user)

        if not profile:
            return []

        return profile.semester_records

    async def _auto_fetch_pending_marks(
        self, profile: StudentProfile
    ) -> int:
        """
        Automatically fetch and link pending marks based on
        roll number or seat number.

        FIXED:
        - pending_marks_checked set to True after completion
        - Uses .replace() for all document saves
        - Also resets linked_to_profile=False entries when
          re-uploaded by admin
        """
        try:
            query_conditions = []

            if profile.roll_number:
                query_conditions.append(
                    {"roll_number": profile.roll_number}
                )
                # Case-insensitive match
                query_conditions.append(
                    {
                        "roll_number": {
                            "$regex": f"^{profile.roll_number}$",
                            "$options": "i",
                        }
                    }
                )

            if profile.current_seat_number:
                query_conditions.append(
                    {"seat_number": profile.current_seat_number}
                )

            for seat_record in profile.seat_number_history:
                query_conditions.append(
                    {"seat_number": seat_record.seat_number}
                )

            if not query_conditions:
                logger.warning(
                    f"No identifiers to match for user {profile.user_id}"
                )
                profile.pending_marks_checked = True
                await profile.replace()
                return 0

            # ═══════════════════════════════════════════
            # FIX: Find ALL unlinked pending marks
            # ═══════════════════════════════════════════
            pending_marks = await PendingStudentMarks.find(
                {
                    "$or": query_conditions,
                    "linked_to_profile": False,
                }
            ).to_list()

            if not pending_marks:
                logger.info(
                    f"No pending marks found for user {profile.user_id}"
                )
                profile.pending_marks_checked = True
                await profile.replace()
                return 0

            logger.info(
                f"Found {len(pending_marks)} pending marks entries "
                f"for user {profile.user_id}"
            )

            linked_count = 0

            for pending in pending_marks:
                idx = next(
                    (
                        i
                        for i, sr in enumerate(profile.semester_records)
                        if sr.semester_number == pending.semester_number
                    ),
                    None,
                )

                sem_rec = SemesterRecord(
                    semester_number=pending.semester_number,
                    academic_year=pending.academic_year,
                    subjects=pending.subjects,
                    sgpa=pending.sgpa,
                    total_credits=pending.total_credits,
                    credits_earned=pending.credits_earned,
                    is_complete=True,
                    created_at=pending.upload_timestamp,
                )

                if idx is not None:
                    logger.info(
                        f"Updating existing semester "
                        f"{pending.semester_number}"
                    )
                    profile.semester_records[idx] = sem_rec
                else:
                    logger.info(
                        f"Adding new semester {pending.semester_number}"
                    )
                    profile.semester_records.append(sem_rec)

                # Mark pending marks as linked
                pending.linked_to_profile = True
                pending.linked_user_id = profile.user_id
                await pending.replace()

                linked_count += 1

            profile.semester_records.sort(
                key=lambda x: x.semester_number
            )

            # Recalculate CGPA
            all_grade_points = 0.0
            all_credits = 0
            all_credits_earned = 0

            for sem in profile.semester_records:
                if sem.is_complete and sem.total_credits > 0:
                    all_grade_points += sem.sgpa * sem.total_credits
                    all_credits += sem.total_credits
                    all_credits_earned += sem.credits_earned

            profile.cgpa = (
                round(all_grade_points / all_credits, 2)
                if all_credits > 0
                else 0.0
            )
            profile.total_credits_earned = all_credits_earned
            profile.marks_synced_at = datetime.now()
            # ═══════════════════════════════════════════
            # FIX: Set to True (was False — caused
            # infinite loop of re-checking)
            # ═══════════════════════════════════════════
            profile.pending_marks_checked = True
            profile.last_updated = datetime.now()

            await profile.replace()

            logger.info(
                f"Successfully linked {linked_count} semesters "
                f"for user {profile.user_id}"
            )
            return linked_count

        except Exception as e:
            logger.error(
                f"Error auto-fetching marks for user "
                f"{profile.user_id}: {e}",
                exc_info=True,
            )
            return 0