# app/services/admin_service.py
"""
Admin Service
Business logic for admin operations — queries MongoDB and Firestore.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import PydanticObjectId
from bson import ObjectId
import os

from app.models.faculty import Faculty, FacultyStatus
from app.models.elective import Elective
from app.models.meeting_request import MeetingRequest
from app.models.student_projects import StudentProject
from app.core.curriculum import (
    get_semester_subjects,
    ELECTIVE_OPTIONS,
)
from app.core.firebase_admin import firebase_manager

logger = logging.getLogger(__name__)


def _get_db():
    """Get direct MongoDB database handle"""
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DATABASE", "academic_advisor")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]


# ─────────────────────────────────────────────────────────
# Allowed‑field constants (single source of truth)
# ─────────────────────────────────────────────────────────
STUDENT_EDITABLE_FIELDS = {
    "name",
    "email",
    "roll_number",
    "branch",
    "current_semester",
    "admission_year",
    "current_academic_year",
    "cgpa",
    "interests",
    "career_goals",
    "skills",
    "total_credits_earned",
    "total_credits_required",
    "phone",
    "address",
    "date_of_birth",
    "guardian_name",
    "guardian_phone",
}

FACULTY_EDITABLE_FIELDS = {
    "name",
    "email",
    "department",
    "designation",
    "phone",
    "office_location",
    "specializations",
    "teaching_subjects",
    "max_mentees",
    "bio",
    "profile_setup_complete",
}

ELECTIVE_EDITABLE_FIELDS = {
    "name",
    "description",
    "department",
    "semester",
    "credits",
    "prerequisites",
    "topics",
    "skills_covered",
    "career_paths",
    "difficulty_level",
    "max_students",
    "is_available",
    "is_honours_track",
    "honours_track_name",
    "instructor_name",
    "instructor_email",
    "textbooks",
    "online_resources",
}

MEETING_EDITABLE_FIELDS = {
    "status",
    "scheduled_date",
    "scheduled_time",
    "meeting_link",
    "location",
    "notes",
    "admin_remarks",
    "cancel_reason",
}


class AdminService:
    """Service for admin dashboard operations"""

    # ==================== DASHBOARD STATS ====================

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        try:
            db = _get_db()

            student_count = await db.student_profiles.count_documents({})
            faculty_count = await Faculty.find().count()
            elective_count = await Elective.find(
                Elective.is_available == True
            ).count()
            project_count = await db.student_projects.count_documents({})

            try:
                meeting_count = await MeetingRequest.find().count()
                pending_meetings = await MeetingRequest.find(
                    MeetingRequest.status == "pending"
                ).count()
            except Exception:
                meeting_count = 0
                pending_meetings = 0

            try:
                active_faculty = await Faculty.find(
                    Faculty.status == FacultyStatus.ACTIVE
                ).count()
                pending_faculty = await Faculty.find(
                    Faculty.status == FacultyStatus.PENDING_SETUP
                ).count()
            except Exception:
                active_faculty = faculty_count
                pending_faculty = 0

            firestore_counts = {"students": 0, "faculty": 0, "admin": 0}
            try:
                users = await firebase_manager.get_collection("users")
                for u in users:
                    role = u.get("role", "student")
                    if role in firestore_counts:
                        firestore_counts[role] += 1
            except Exception as e:
                logger.warning(f"Firestore user count failed: {e}")

            return {
                "total_students": student_count,
                "total_faculty": faculty_count,
                "active_faculty": active_faculty,
                "pending_faculty": pending_faculty,
                "total_electives": elective_count,
                "total_meetings": meeting_count,
                "pending_meetings": pending_meetings,
                "total_projects": project_count,
                "firestore_users": firestore_counts,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Dashboard stats error: {e}")
            return {
                "total_students": 0,
                "total_faculty": 0,
                "active_faculty": 0,
                "pending_faculty": 0,
                "total_electives": 0,
                "total_meetings": 0,
                "pending_meetings": 0,
                "total_projects": 0,
                "firestore_users": {
                    "students": 0,
                    "faculty": 0,
                    "admin": 0,
                },
                "error": str(e),
            }

    # ==================== STUDENT MANAGEMENT ====================

    async def get_all_students(
        self,
        department: Optional[str] = None,
        semester: Optional[int] = None,
        batch: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 25,
    ) -> Dict[str, Any]:
        """Retrieve students from student_profiles collection"""
        try:
            db = _get_db()
            collection = db.student_profiles

            query_filter: Dict[str, Any] = {}

            if department:
                query_filter["branch"] = {
                    "$regex": department,
                    "$options": "i",
                }
            if semester:
                query_filter["current_semester"] = semester
            if batch:
                query_filter["admission_year"] = int(batch)
            if search:
                query_filter["$or"] = [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"roll_number": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}},
                ]

            total = await collection.count_documents(query_filter)

            sort_field_map = {
                "name": "name",
                "cgpa": "cgpa",
                "semester": "current_semester",
                "updated_at": "last_updated",
            }
            mongo_sort_field = sort_field_map.get(sort_by, "last_updated")
            sort_direction = -1 if sort_order == "desc" else 1

            cursor = (
                collection.find(query_filter)
                .sort(mongo_sort_field, sort_direction)
                .skip(skip)
                .limit(limit)
            )
            students_raw = await cursor.to_list(length=limit)

            students = []
            for s in students_raw:
                semester_sgpa = 0.0
                performance_trend = "stable"
                semester_records = s.get("semester_records", [])

                if semester_records:
                    sorted_records = sorted(
                        semester_records,
                        key=lambda r: r.get("semester_number", 0),
                        reverse=True,
                    )
                    semester_sgpa = sorted_records[0].get("sgpa", 0.0)

                    if len(sorted_records) >= 2:
                        latest = sorted_records[0].get("sgpa", 0)
                        previous = sorted_records[1].get("sgpa", 0)
                        if latest > previous + 0.3:
                            performance_trend = "up"
                        elif latest < previous - 0.3:
                            performance_trend = "down"

                strong_subjects: List[str] = []
                weak_subjects: List[str] = []
                if semester_records:
                    latest_record = sorted(
                        semester_records,
                        key=lambda r: r.get("semester_number", 0),
                        reverse=True,
                    )[0]
                    for subj in latest_record.get("subjects", []):
                        gp = subj.get("grade_points", 0)
                        name = subj.get("subject_name", "")
                        if gp >= 9:
                            strong_subjects.append(name)
                        elif gp <= 6:
                            weak_subjects.append(name)

                students.append(
                    {
                        "id": str(s.get("_id", "")),
                        "uid": s.get("user_id", ""),
                        "name": s.get("name", "N/A"),
                        "email": s.get("email", ""),
                        "roll_number": s.get("roll_number", ""),
                        "branch": s.get("branch", ""),
                        "semester": s.get("current_semester", ""),
                        "batch": str(s.get("admission_year", "")),
                        "year": s.get("current_academic_year", ""),
                        "overall_cgpa": s.get("cgpa", 0.0),
                        "semester_sgpa": round(semester_sgpa, 2),
                        "strong_subjects": strong_subjects[:3],
                        "weak_subjects": weak_subjects[:3],
                        "completed_credits": s.get(
                            "total_credits_earned", 0
                        ),
                        "total_credits": s.get(
                            "total_credits_required", 160
                        ),
                        "interests": s.get("interests", [])[:5],
                        "performance_trend": performance_trend,
                        "updated_at": str(s.get("last_updated", "")),
                    }
                )

            return {
                "students": students,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": (skip + limit) < total,
            }
        except Exception as e:
            logger.error(f"Error listing students: {e}", exc_info=True)
            return {
                "students": [],
                "total": 0,
                "skip": skip,
                "limit": limit,
                "has_more": False,
            }

    async def get_student_detail(
        self, uid: str
    ) -> Optional[Dict[str, Any]]:
        """Get comprehensive student data from student_profiles"""
        try:
            db = _get_db()

            student = await db.student_profiles.find_one({"user_id": uid})
            if not student:
                try:
                    student = await db.student_profiles.find_one(
                        {"_id": ObjectId(uid)}
                    )
                except Exception:
                    pass

            if not student:
                return None

            subjects_list: List[Dict[str, Any]] = []
            semester_records = student.get("semester_records", [])

            for record in semester_records:
                sem_num = record.get("semester_number", 0)
                for subj in record.get("subjects", []):
                    gp = subj.get("grade_points", 0)
                    trend = "stable"
                    if gp >= 9:
                        trend = "up"
                    elif gp <= 5:
                        trend = "down"

                    subjects_list.append(
                        {
                            "name": subj.get("subject_name", ""),
                            "code": subj.get("subject_code", ""),
                            "score": subj.get("total_marks", 0),
                            "credits": subj.get("credits", 0),
                            "trend": trend,
                            "grade": subj.get("grade", ""),
                            "grade_points": gp,
                            "semester": sem_num,
                            "internal_marks": subj.get(
                                "internal_marks", 0
                            ),
                            "external_marks": subj.get(
                                "external_marks", 0
                            ),
                        }
                    )

            strong_subjects = [
                s["name"]
                for s in subjects_list
                if s.get("grade_points", 0) >= 9
            ]
            weak_subjects = [
                s["name"]
                for s in subjects_list
                if s.get("grade_points", 0) <= 6
            ]

            semester_sgpa = 0.0
            if semester_records:
                latest = sorted(
                    semester_records,
                    key=lambda r: r.get("semester_number", 0),
                    reverse=True,
                )[0]
                semester_sgpa = latest.get("sgpa", 0.0)

            projects: List[Dict[str, Any]] = []
            try:
                project_docs = await db.student_projects.find(
                    {"student_id": uid}
                ).to_list(length=20)
                for p in project_docs:
                    projects.append(
                        {
                            "id": str(p.get("_id", "")),
                            "title": p.get("title", ""),
                            "description": p.get("description", ""),
                            "technologies": p.get("technologies", []),
                            "status": p.get("status", ""),
                            "created_at": str(p.get("created_at", "")),
                        }
                    )
            except Exception:
                pass

            weaknesses: List[Dict[str, Any]] = []
            try:
                weakness_docs = await db.weakness_analysis.find(
                    {"student_id": uid}
                ).to_list(length=20)
                for w in weakness_docs:
                    weaknesses.append(
                        {
                            "id": str(w.get("_id", "")),
                            "subject": w.get("subject_name", ""),
                            "severity": w.get("severity", ""),
                            "score": w.get("score", 0),
                        }
                    )
            except Exception:
                pass

            return {
                "uid": student.get("user_id", uid),
                "name": student.get("name", ""),
                "email": student.get("email", ""),
                "roll_number": student.get("roll_number", ""),
                "branch": student.get("branch", ""),
                "semester": student.get("current_semester", ""),
                "batch": str(student.get("admission_year", "")),
                "year": student.get("current_academic_year", ""),
                "overall_cgpa": student.get("cgpa", 0.0),
                "semester_sgpa": round(semester_sgpa, 2),
                "strong_subjects": strong_subjects[-5:],
                "weak_subjects": weak_subjects[-5:],
                "completed_credits": student.get(
                    "total_credits_earned", 0
                ),
                "total_credits": student.get(
                    "total_credits_required", 160
                ),
                "interests": student.get("interests", []),
                "career_goals": student.get("career_goals", []),
                "skills": student.get("skills", []),
                "skills_matrix": {
                    s: 80 for s in student.get("skills", [])
                },
                "performance_trend": "stable",
                "subjects": subjects_list,
                "semester_records": [
                    {
                        "semester": r.get("semester_number"),
                        "sgpa": r.get("sgpa"),
                        "credits": r.get("credits_earned"),
                        "year": r.get("academic_year"),
                    }
                    for r in semester_records
                ],
                "projects": projects,
                "weaknesses": weaknesses,
                "recommendations_count": 0,
            }
        except Exception as e:
            logger.error(
                f"Error getting student detail: {e}", exc_info=True
            )
            return None

    # ──────────── EDIT STUDENT ────────────

    async def update_student(
        self, uid: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a student profile.

        Parameters
        ----------
        uid : str
            Either the Firestore ``user_id`` **or** the Mongo ``_id``.
        update_data : dict
            Fields to patch.  Only keys listed in
            ``STUDENT_EDITABLE_FIELDS`` are applied.

        Returns
        -------
        dict  with ``updated_fields``, ``student_id``, and ``success``.

        Raises
        ------
        ValueError  – student not found or nothing to update.
        """
        db = _get_db()
        collection = db.student_profiles

        # ── locate the document ──────────────────────────────
        student = await collection.find_one({"user_id": uid})
        if not student:
            try:
                student = await collection.find_one(
                    {"_id": ObjectId(uid)}
                )
            except Exception:
                pass

        if not student:
            raise ValueError(f"Student not found: {uid}")

        doc_id = student["_id"]

        # ── build $set payload ───────────────────────────────
        set_payload: Dict[str, Any] = {}
        for field, value in update_data.items():
            if field in STUDENT_EDITABLE_FIELDS:
                set_payload[field] = value

        if not set_payload:
            raise ValueError(
                "No valid fields to update. Allowed: "
                + ", ".join(sorted(STUDENT_EDITABLE_FIELDS))
            )

        set_payload["last_updated"] = datetime.utcnow()

        result = await collection.update_one(
            {"_id": doc_id}, {"$set": set_payload}
        )

        if result.modified_count == 0 and result.matched_count == 0:
            raise ValueError("Update matched no documents")

        logger.info(
            "Student %s updated fields: %s",
            uid,
            list(set_payload.keys()),
        )

        return {
            "success": True,
            "student_id": str(doc_id),
            "uid": student.get("user_id", uid),
            "updated_fields": list(set_payload.keys()),
            "updated_at": set_payload["last_updated"].isoformat(),
        }

    async def update_student_semester_record(
        self,
        uid: str,
        semester_number: int,
        record_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Add **or** replace a single semester record inside
        ``semester_records`` for a student.

        ``record_data`` must contain at least ``sgpa``.
        ``subjects`` is an optional list of dicts.
        """
        db = _get_db()
        collection = db.student_profiles

        student = await collection.find_one({"user_id": uid})
        if not student:
            try:
                student = await collection.find_one(
                    {"_id": ObjectId(uid)}
                )
            except Exception:
                pass

        if not student:
            raise ValueError(f"Student not found: {uid}")

        doc_id = student["_id"]

        new_record = {
            "semester_number": semester_number,
            "sgpa": record_data.get("sgpa", 0.0),
            "credits_earned": record_data.get("credits_earned", 0),
            "academic_year": record_data.get("academic_year", ""),
            "subjects": record_data.get("subjects", []),
        }

        # Remove existing entry for same semester, then push new one
        await collection.update_one(
            {"_id": doc_id},
            {
                "$pull": {
                    "semester_records": {
                        "semester_number": semester_number,
                    }
                }
            },
        )
        await collection.update_one(
            {"_id": doc_id},
            {
                "$push": {"semester_records": new_record},
                "$set": {"last_updated": datetime.utcnow()},
            },
        )

        logger.info(
            "Student %s semester %d record updated", uid, semester_number
        )

        return {
            "success": True,
            "student_id": str(doc_id),
            "semester_number": semester_number,
            "updated_at": datetime.utcnow().isoformat(),
        }

    async def delete_student(self, uid: str) -> Dict[str, Any]:
        """
        Soft‑ or hard‑delete a student profile.
        Also removes related projects and weakness docs.
        """
        db = _get_db()
        collection = db.student_profiles

        student = await collection.find_one({"user_id": uid})
        if not student:
            try:
                student = await collection.find_one(
                    {"_id": ObjectId(uid)}
                )
            except Exception:
                pass

        if not student:
            raise ValueError(f"Student not found: {uid}")

        doc_id = student["_id"]
        user_id = student.get("user_id", uid)

        # Delete related documents
        del_projects = await db.student_projects.delete_many(
            {"student_id": user_id}
        )
        del_weakness = await db.weakness_analysis.delete_many(
            {"student_id": user_id}
        )

        await collection.delete_one({"_id": doc_id})

        logger.info(
            "Student %s deleted (projects=%d, weaknesses=%d)",
            uid,
            del_projects.deleted_count,
            del_weakness.deleted_count,
        )

        return {
            "success": True,
            "student_id": str(doc_id),
            "related_deleted": {
                "projects": del_projects.deleted_count,
                "weaknesses": del_weakness.deleted_count,
            },
        }

    # ==================== FACULTY MANAGEMENT ====================

    async def get_all_faculty(
        self,
        department: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 25,
    ) -> Dict[str, Any]:
        try:
            query_filter: Dict[str, Any] = {}
            if department:
                query_filter["department"] = department
            if status:
                query_filter["status"] = status

            find_query = Faculty.find(query_filter)
            total = await find_query.count()

            faculty_raw = (
                await find_query.sort([("updated_at", -1)])
                .skip(skip)
                .limit(limit)
                .to_list()
            )

            faculty_list = []
            for f in faculty_raw:
                if search:
                    search_lower = search.lower()
                    if not (
                        search_lower in (f.name or "").lower()
                        or search_lower in (f.email or "").lower()
                        or search_lower in (f.department or "").lower()
                    ):
                        continue

                profile_completeness = 0
                try:
                    if f.uniform_profile:
                        profile_completeness = (
                            f.calculate_profile_completeness()
                        )
                except Exception:
                    pass

                faculty_list.append(
                    {
                        "id": str(f.id),
                        "user_id": f.user_id,
                        "name": f.name,
                        "email": f.email,
                        "department": f.department,
                        "designation": f.designation,
                        "status": f.status,
                        "phone": f.phone,
                        "specializations": (f.specializations or [])[:5],
                        "teaching_subjects": (
                            f.teaching_subjects or []
                        )[:5],
                        "mentee_count": len(f.mentee_ids or []),
                        "max_mentees": f.max_mentees,
                        "profile_setup_complete": f.profile_setup_complete,
                        "profile_completeness": profile_completeness,
                        "cv_uploaded": f.cv_url is not None,
                        "created_at": (
                            f.created_at.isoformat()
                            if f.created_at
                            else None
                        ),
                        "updated_at": (
                            f.updated_at.isoformat()
                            if f.updated_at
                            else None
                        ),
                    }
                )

            return {
                "faculty": faculty_list,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": (skip + limit) < total,
            }
        except Exception as e:
            logger.error(f"Error listing faculty: {e}")
            return {
                "faculty": [],
                "total": 0,
                "skip": skip,
                "limit": limit,
                "has_more": False,
            }

    async def get_faculty_detail(
        self, uid: str
    ) -> Optional[Dict[str, Any]]:
        try:
            faculty = await Faculty.find_one(Faculty.user_id == uid)
            if not faculty:
                return None

            profile_completeness = 0
            student_view: Dict[str, Any] = {}
            try:
                if faculty.uniform_profile:
                    profile_completeness = (
                        faculty.calculate_profile_completeness()
                    )
                    student_view = faculty.get_student_view()
            except Exception:
                pass

            meetings: List[Any] = []
            try:
                meetings = await MeetingRequest.find(
                    MeetingRequest.faculty_id == uid
                ).to_list()
            except Exception:
                pass

            return {
                "user_id": faculty.user_id,
                "name": faculty.name,
                "email": faculty.email,
                "department": faculty.department,
                "designation": faculty.designation,
                "status": faculty.status,
                "phone": faculty.phone,
                "office_location": faculty.office_location,
                "specializations": faculty.specializations,
                "teaching_subjects": faculty.teaching_subjects,
                "qualifications": [
                    q.dict() for q in (faculty.qualifications or [])
                ],
                "publications_count": len(faculty.publications or []),
                "mentee_ids": faculty.mentee_ids,
                "mentee_count": len(faculty.mentee_ids or []),
                "cv_url": faculty.cv_url,
                "cv_uploaded_at": (
                    faculty.cv_uploaded_at.isoformat()
                    if faculty.cv_uploaded_at
                    else None
                ),
                "profile_setup_complete": faculty.profile_setup_complete,
                "profile_completeness": profile_completeness,
                "student_view": student_view,
                "meetings_count": len(meetings),
                "created_at": (
                    faculty.created_at.isoformat()
                    if faculty.created_at
                    else None
                ),
            }
        except Exception as e:
            logger.error(f"Error getting faculty detail: {e}")
            return None

    # ──────────── EDIT FACULTY ────────────

    async def update_faculty(
        self, uid: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a faculty document found by ``user_id``.

        Only fields in ``FACULTY_EDITABLE_FIELDS`` are written.
        """
        faculty = await Faculty.find_one(Faculty.user_id == uid)
        if not faculty:
            raise ValueError(f"Faculty not found: {uid}")

        applied: List[str] = []
        for field, value in update_data.items():
            if field in FACULTY_EDITABLE_FIELDS:
                setattr(faculty, field, value)
                applied.append(field)

        if not applied:
            raise ValueError(
                "No valid fields to update. Allowed: "
                + ", ".join(sorted(FACULTY_EDITABLE_FIELDS))
            )

        faculty.updated_at = datetime.utcnow()
        await faculty.save()

        logger.info("Faculty %s updated fields: %s", uid, applied)

        return {
            "success": True,
            "user_id": faculty.user_id,
            "updated_fields": applied,
            "updated_at": faculty.updated_at.isoformat(),
        }

    async def update_faculty_status(
        self,
        uid: str,
        new_status: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Change a faculty member's status
        (active / inactive / pending_setup / suspended).
        """
        faculty = await Faculty.find_one(Faculty.user_id == uid)
        if not faculty:
            raise ValueError(f"Faculty not found: {uid}")

        # Validate against the enum
        try:
            status_enum = FacultyStatus(new_status)
        except ValueError:
            valid = [s.value for s in FacultyStatus]
            raise ValueError(
                f"Invalid status '{new_status}'. Must be one of {valid}"
            )

        old_status = faculty.status
        faculty.status = status_enum
        faculty.updated_at = datetime.utcnow()
        await faculty.save()

        logger.info(
            "Faculty %s status changed %s → %s (reason=%s)",
            uid,
            old_status,
            new_status,
            reason,
        )

        return {
            "success": True,
            "user_id": uid,
            "old_status": old_status,
            "new_status": new_status,
            "reason": reason,
            "updated_at": faculty.updated_at.isoformat(),
        }

    async def add_faculty_mentee(
        self, faculty_uid: str, student_uid: str
    ) -> Dict[str, Any]:
        """Assign a student as mentee to a faculty member."""
        faculty = await Faculty.find_one(
            Faculty.user_id == faculty_uid
        )
        if not faculty:
            raise ValueError(f"Faculty not found: {faculty_uid}")

        if faculty.mentee_ids is None:
            faculty.mentee_ids = []

        if student_uid in faculty.mentee_ids:
            raise ValueError(
                f"Student {student_uid} is already a mentee"
            )

        if (
            faculty.max_mentees
            and len(faculty.mentee_ids) >= faculty.max_mentees
        ):
            raise ValueError(
                f"Faculty has reached max mentees ({faculty.max_mentees})"
            )

        faculty.mentee_ids.append(student_uid)
        faculty.updated_at = datetime.utcnow()
        await faculty.save()

        return {
            "success": True,
            "faculty_uid": faculty_uid,
            "student_uid": student_uid,
            "total_mentees": len(faculty.mentee_ids),
        }

    async def remove_faculty_mentee(
        self, faculty_uid: str, student_uid: str
    ) -> Dict[str, Any]:
        """Remove a student from a faculty member's mentee list."""
        faculty = await Faculty.find_one(
            Faculty.user_id == faculty_uid
        )
        if not faculty:
            raise ValueError(f"Faculty not found: {faculty_uid}")

        if (
            faculty.mentee_ids is None
            or student_uid not in faculty.mentee_ids
        ):
            raise ValueError(
                f"Student {student_uid} is not a mentee of {faculty_uid}"
            )

        faculty.mentee_ids.remove(student_uid)
        faculty.updated_at = datetime.utcnow()
        await faculty.save()

        return {
            "success": True,
            "faculty_uid": faculty_uid,
            "student_uid": student_uid,
            "total_mentees": len(faculty.mentee_ids),
        }

    async def delete_faculty(self, uid: str) -> Dict[str, Any]:
        """Delete a faculty profile and clean up meetings."""
        faculty = await Faculty.find_one(Faculty.user_id == uid)
        if not faculty:
            raise ValueError(f"Faculty not found: {uid}")

        # Cancel pending meetings for this faculty
        cancelled = 0
        try:
            pending = await MeetingRequest.find(
                MeetingRequest.faculty_id == uid,
                MeetingRequest.status == "pending",
            ).to_list()
            for m in pending:
                m.status = "cancelled"
                m.admin_remarks = "Faculty profile deleted by admin"
                await m.save()
                cancelled += 1
        except Exception:
            pass

        await faculty.delete()

        logger.info(
            "Faculty %s deleted, %d meetings cancelled", uid, cancelled
        )

        return {
            "success": True,
            "user_id": uid,
            "meetings_cancelled": cancelled,
        }

    # ==================== MEETING MANAGEMENT ====================

    async def get_all_meetings(
        self,
        status: Optional[str] = None,
        faculty_id: Optional[str] = None,
        student_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 25,
    ) -> Dict[str, Any]:
        """List meetings with optional filters."""
        try:
            conditions = []
            if status:
                conditions.append(MeetingRequest.status == status)
            if faculty_id:
                conditions.append(
                    MeetingRequest.faculty_id == faculty_id
                )
            if student_id:
                conditions.append(
                    MeetingRequest.student_id == student_id
                )

            query = (
                MeetingRequest.find(*conditions)
                if conditions
                else MeetingRequest.find()
            )

            total = await query.count()

            meetings_raw = (
                await query.sort([("created_at", -1)])
                .skip(skip)
                .limit(limit)
                .to_list()
            )

            meetings = []
            for m in meetings_raw:
                meetings.append(
                    {
                        "id": str(m.id),
                        "student_id": m.student_id,
                        "faculty_id": m.faculty_id,
                        "status": m.status,
                        "purpose": getattr(m, "purpose", ""),
                        "scheduled_date": (
                            m.scheduled_date.isoformat()
                            if hasattr(m, "scheduled_date")
                            and m.scheduled_date
                            else None
                        ),
                        "meeting_link": getattr(m, "meeting_link", ""),
                        "location": getattr(m, "location", ""),
                        "notes": getattr(m, "notes", ""),
                        "admin_remarks": getattr(
                            m, "admin_remarks", ""
                        ),
                        "created_at": (
                            m.created_at.isoformat()
                            if hasattr(m, "created_at") and m.created_at
                            else None
                        ),
                    }
                )

            return {
                "meetings": meetings,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": (skip + limit) < total,
            }
        except Exception as e:
            logger.error(f"Error listing meetings: {e}")
            return {
                "meetings": [],
                "total": 0,
                "skip": skip,
                "limit": limit,
                "has_more": False,
            }

    async def update_meeting(
        self, meeting_id: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a meeting request.

        Common use‑cases:
        * Approve:  ``{"status": "approved", "meeting_link": "…"}``
        * Reject:   ``{"status": "rejected", "admin_remarks": "…"}``
        * Reschedule: ``{"scheduled_date": "…", "notes": "…"}``
        """
        meeting = await MeetingRequest.get(
            PydanticObjectId(meeting_id)
        )
        if not meeting:
            raise ValueError(f"Meeting not found: {meeting_id}")

        applied: List[str] = []
        for field, value in update_data.items():
            if field in MEETING_EDITABLE_FIELDS:
                setattr(meeting, field, value)
                applied.append(field)

        if not applied:
            raise ValueError(
                "No valid fields to update. Allowed: "
                + ", ".join(sorted(MEETING_EDITABLE_FIELDS))
            )

        if hasattr(meeting, "updated_at"):
            meeting.updated_at = datetime.utcnow()
        await meeting.save()

        logger.info("Meeting %s updated fields: %s", meeting_id, applied)

        return {
            "success": True,
            "meeting_id": meeting_id,
            "updated_fields": applied,
            "current_status": meeting.status,
        }

    async def delete_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """Hard‑delete a meeting request."""
        meeting = await MeetingRequest.get(
            PydanticObjectId(meeting_id)
        )
        if not meeting:
            raise ValueError(f"Meeting not found: {meeting_id}")

        await meeting.delete()

        logger.info("Meeting %s deleted", meeting_id)
        return {"success": True, "meeting_id": meeting_id}

    # ==================== CURRICULUM / ELECTIVES ====================

    async def get_curriculum(
        self,
        semester: Optional[int] = None,
        admission_year: int = 2024,
    ) -> Dict[str, Any]:
        try:
            result: Dict[str, Any] = {}
            semesters_to_fetch = (
                [semester] if semester else list(range(1, 9))
            )

            for sem in semesters_to_fetch:
                subjects = get_semester_subjects(sem, admission_year)
                result[f"semester_{sem}"] = [
                    {
                        "subject_code": s.subject_code,
                        "subject_name": s.subject_name,
                        "credits": s.credits,
                        "course_type": s.course_type,
                        "is_elective": s.is_elective,
                        "is_practical": s.is_practical,
                        "elective_group": s.elective_group,
                        "internal_max": s.internal_max,
                        "external_max": s.external_max,
                    }
                    for s in subjects
                ]

            db_electives = await Elective.find(
                Elective.is_available == True
            ).to_list()

            return {
                "curriculum": result,
                "admission_year": admission_year,
                "curriculum_type": (
                    "pre_autonomy"
                    if admission_year <= 2024
                    else "autonomy"
                ),
                "db_electives_count": len(db_electives),
                "db_electives": [
                    {
                        "id": str(e.id),
                        "code": e.code,
                        "name": e.name,
                        "category": e.category,
                        "department": e.department,
                        "semester": e.semester,
                        "credits": e.credits,
                        "difficulty_level": e.difficulty_level,
                        "is_available": e.is_available,
                    }
                    for e in db_electives
                ],
            }
        except Exception as e:
            logger.error(f"Error fetching curriculum: {e}")
            return {"curriculum": {}, "error": str(e)}

    async def get_all_elective_options(self) -> Dict[str, Any]:
        try:
            static_options = ELECTIVE_OPTIONS
            db_electives = await Elective.find().to_list()

            return {
                "static_elective_groups": static_options,
                "db_electives": [
                    {
                        "id": str(e.id),
                        "code": e.code,
                        "name": e.name,
                        "category": (
                            e.category.value
                            if hasattr(e.category, "value")
                            else e.category
                        ),
                        "department": e.department,
                        "semester": e.semester,
                        "credits": e.credits,
                        "prerequisites": e.prerequisites,
                        "topics": e.topics,
                        "skills_covered": e.skills_covered,
                        "career_paths": e.career_paths,
                        "difficulty_level": (
                            e.difficulty_level.value
                            if hasattr(e.difficulty_level, "value")
                            else e.difficulty_level
                        ),
                        "is_available": e.is_available,
                        "is_honours_track": e.is_honours_track,
                        "honours_track_name": e.honours_track_name,
                        "max_students": e.max_students,
                        "current_enrollment": e.current_enrollment,
                    }
                    for e in db_electives
                ],
            }
        except Exception as e:
            logger.error(f"Error fetching elective options: {e}")
            return {"static_elective_groups": {}, "db_electives": []}

    async def update_elective(
        self, elective_id: str, update_data: dict
    ) -> Dict[str, Any]:
        try:
            elective = await Elective.get(
                PydanticObjectId(elective_id)
            )
            if not elective:
                raise ValueError("Elective not found")

            applied: List[str] = []
            for field in ELECTIVE_EDITABLE_FIELDS:
                if field in update_data:
                    setattr(elective, field, update_data[field])
                    applied.append(field)

            if not applied:
                raise ValueError(
                    "No valid fields to update. Allowed: "
                    + ", ".join(sorted(ELECTIVE_EDITABLE_FIELDS))
                )

            elective.updated_at = datetime.utcnow()
            await elective.save()

            return {
                "success": True,
                "id": str(elective.id),
                "code": elective.code,
                "name": elective.name,
                "updated_fields": applied,
            }
        except Exception as e:
            logger.error(f"Error updating elective: {e}")
            raise

    async def create_elective(self, data: dict) -> Dict[str, Any]:
        try:
            elective = Elective(**data)
            await elective.insert()
            return {
                "success": True,
                "id": str(elective.id),
                "code": elective.code,
                "name": elective.name,
            }
        except Exception as e:
            logger.error(f"Error creating elective: {e}")
            raise

    async def delete_elective(self, elective_id: str) -> Dict[str, Any]:
        try:
            elective = await Elective.get(
                PydanticObjectId(elective_id)
            )
            if not elective:
                raise ValueError("Elective not found")
            code = elective.code
            name = elective.name
            await elective.delete()
            return {
                "success": True,
                "id": elective_id,
                "code": code,
                "name": name,
            }
        except Exception as e:
            logger.error(f"Error deleting elective: {e}")
            raise

    # ==================== PROJECT MANAGEMENT ====================

    async def get_all_projects(
        self,
        student_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 25,
    ) -> Dict[str, Any]:
        """List student projects with optional filters."""
        try:
            db = _get_db()
            query_filter: Dict[str, Any] = {}
            if student_id:
                query_filter["student_id"] = student_id
            if status:
                query_filter["status"] = status

            total = await db.student_projects.count_documents(
                query_filter
            )

            cursor = (
                db.student_projects.find(query_filter)
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
            )
            projects_raw = await cursor.to_list(length=limit)

            projects = []
            for p in projects_raw:
                projects.append(
                    {
                        "id": str(p.get("_id", "")),
                        "student_id": p.get("student_id", ""),
                        "title": p.get("title", ""),
                        "description": p.get("description", ""),
                        "technologies": p.get("technologies", []),
                        "status": p.get("status", ""),
                        "github_url": p.get("github_url", ""),
                        "created_at": str(p.get("created_at", "")),
                        "updated_at": str(p.get("updated_at", "")),
                    }
                )

            return {
                "projects": projects,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": (skip + limit) < total,
            }
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return {
                "projects": [],
                "total": 0,
                "skip": skip,
                "limit": limit,
                "has_more": False,
            }

    async def update_project(
        self, project_id: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a student project by its Mongo ``_id``."""
        db = _get_db()

        allowed = {
            "title",
            "description",
            "technologies",
            "status",
            "github_url",
            "feedback",
            "grade",
        }

        set_payload: Dict[str, Any] = {}
        for field, value in update_data.items():
            if field in allowed:
                set_payload[field] = value

        if not set_payload:
            raise ValueError(
                "No valid fields. Allowed: " + ", ".join(sorted(allowed))
            )

        set_payload["updated_at"] = datetime.utcnow()

        result = await db.student_projects.update_one(
            {"_id": ObjectId(project_id)}, {"$set": set_payload}
        )

        if result.matched_count == 0:
            raise ValueError(f"Project not found: {project_id}")

        logger.info(
            "Project %s updated fields: %s",
            project_id,
            list(set_payload.keys()),
        )

        return {
            "success": True,
            "project_id": project_id,
            "updated_fields": list(set_payload.keys()),
        }

    async def delete_project(self, project_id: str) -> Dict[str, Any]:
        """Delete a student project."""
        db = _get_db()
        result = await db.student_projects.delete_one(
            {"_id": ObjectId(project_id)}
        )
        if result.deleted_count == 0:
            raise ValueError(f"Project not found: {project_id}")

        return {"success": True, "project_id": project_id}

    # ==================== USER / ROLE MANAGEMENT ====================

    async def get_all_firestore_users(
        self,
        role: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List users stored in Firestore ``users`` collection."""
        try:
            users = await firebase_manager.get_collection("users")

            filtered = []
            for u in users:
                if role and u.get("role") != role:
                    continue
                if search:
                    s = search.lower()
                    if not (
                        s in u.get("email", "").lower()
                        or s in u.get("displayName", "").lower()
                        or s in u.get("name", "").lower()
                        or s in u.get("uid", "").lower()
                    ):
                        continue
                filtered.append(
                    {
                        "uid": u.get("uid", u.get("id", "")),
                        "email": u.get("email", ""),
                        "name": u.get(
                            "displayName", u.get("name", "")
                        ),
                        "role": u.get("role", "student"),
                        "created_at": str(u.get("createdAt", "")),
                        "last_login": str(u.get("lastLogin", "")),
                        "disabled": u.get("disabled", False),
                    }
                )

            return {"users": filtered, "total": len(filtered)}
        except Exception as e:
            logger.error(f"Error listing Firestore users: {e}")
            return {"users": [], "total": 0, "error": str(e)}

    async def update_user_role(
        self, uid: str, new_role: str
    ) -> Dict[str, Any]:
        """
        Change a user's role in Firestore.

        Parameters
        ----------
        uid : str
            Firestore document ID (usually Firebase Auth UID).
        new_role : str
            One of ``student``, ``faculty``, ``admin``.
        """
        valid_roles = {"student", "faculty", "admin"}
        if new_role not in valid_roles:
            raise ValueError(
                f"Invalid role '{new_role}'. Must be one of {valid_roles}"
            )

        try:
            # Read current doc
            user_doc = await firebase_manager.get_document("users", uid)
            if not user_doc:
                raise ValueError(f"User not found in Firestore: {uid}")

            old_role = user_doc.get("role", "student")

            await firebase_manager.set_document(
                "users",
                uid,
                {"role": new_role, "roleUpdatedAt": datetime.utcnow()},
                merge=True,
            )

            logger.info(
                "User %s role changed %s → %s", uid, old_role, new_role
            )

            return {
                "success": True,
                "uid": uid,
                "old_role": old_role,
                "new_role": new_role,
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating user role: {e}")
            raise

    async def disable_user(
        self, uid: str, disabled: bool = True
    ) -> Dict[str, Any]:
        """
        Mark a Firestore user as disabled / enabled.
        """
        try:
            user_doc = await firebase_manager.get_document("users", uid)
            if not user_doc:
                raise ValueError(f"User not found in Firestore: {uid}")

            await firebase_manager.set_document(
                "users",
                uid,
                {
                    "disabled": disabled,
                    "disabledAt": (
                        datetime.utcnow() if disabled else None
                    ),
                },
                merge=True,
            )

            logger.info("User %s disabled=%s", uid, disabled)

            return {
                "success": True,
                "uid": uid,
                "disabled": disabled,
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error disabling user: {e}")
            raise

    # ==================== ANALYTICS ====================

    async def get_analytics_overview(self) -> Dict[str, Any]:
        try:
            db = _get_db()
            all_students = await db.student_profiles.find().to_list(
                length=1000
            )

            if not all_students:
                return {
                    "total_students": 0,
                    "average_cgpa": 0,
                    "performance_distribution": {},
                    "department_distribution": {},
                    "semester_distribution": {},
                }

            total = len(all_students)
            cgpas = [
                s.get("cgpa", 0)
                for s in all_students
                if s.get("cgpa", 0) > 0
            ]
            avg_cgpa = sum(cgpas) / len(cgpas) if cgpas else 0

            perf_dist = {
                "excellent": 0,
                "good": 0,
                "average": 0,
                "poor": 0,
            }
            for s in all_students:
                c = s.get("cgpa", 0)
                if c >= 8.5:
                    perf_dist["excellent"] += 1
                elif c >= 7.0:
                    perf_dist["good"] += 1
                elif c >= 5.5:
                    perf_dist["average"] += 1
                else:
                    perf_dist["poor"] += 1

            dept_dist: Dict[str, int] = {}
            for s in all_students:
                branch = s.get("branch", "Unknown")
                dept_dist[branch] = dept_dist.get(branch, 0) + 1

            sem_dist: Dict[str, int] = {}
            for s in all_students:
                sem = str(s.get("current_semester", "?"))
                sem_dist[sem] = sem_dist.get(sem, 0) + 1

            weak_subject_count: Dict[str, int] = {}
            for s in all_students:
                records = s.get("semester_records", [])
                if records:
                    latest = sorted(
                        records,
                        key=lambda r: r.get("semester_number", 0),
                        reverse=True,
                    )[0]
                    for subj in latest.get("subjects", []):
                        if subj.get("grade_points", 10) <= 6:
                            name = subj.get("subject_name", "")
                            weak_subject_count[name] = (
                                weak_subject_count.get(name, 0) + 1
                            )

            top_weak = sorted(
                weak_subject_count.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]

            return {
                "total_students": total,
                "average_cgpa": round(avg_cgpa, 2),
                "performance_distribution": perf_dist,
                "department_distribution": dept_dist,
                "semester_distribution": sem_dist,
                "top_weak_subjects": [
                    {"subject": name, "count": count}
                    for name, count in top_weak
                ],
            }
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {"error": str(e)}

    async def get_department_comparison(self) -> Dict[str, Any]:
        try:
            db = _get_db()
            all_students = await db.student_profiles.find().to_list(
                length=1000
            )

            dept_data: Dict[str, Dict[str, Any]] = {}
            for s in all_students:
                branch = s.get("branch", "Unknown")
                if branch not in dept_data:
                    dept_data[branch] = {"cgpas": [], "count": 0}
                dept_data[branch]["cgpas"].append(s.get("cgpa", 0))
                dept_data[branch]["count"] += 1

            comparison = []
            for dept, data in dept_data.items():
                cgpas = data["cgpas"]
                comparison.append(
                    {
                        "department": dept,
                        "student_count": data["count"],
                        "average_cgpa": (
                            round(sum(cgpas) / len(cgpas), 2)
                            if cgpas
                            else 0
                        ),
                        "max_cgpa": (
                            round(max(cgpas), 2) if cgpas else 0
                        ),
                        "min_cgpa": (
                            round(min(cgpas), 2) if cgpas else 0
                        ),
                    }
                )

            return {"departments": comparison}
        except Exception as e:
            logger.error(f"Error getting department comparison: {e}")
            return {"departments": []}

    # ==================== USER COUNTS ====================

    async def get_user_counts(self) -> Dict[str, Any]:
        try:
            users = await firebase_manager.get_collection("users")
            counts = {
                "student": 0,
                "faculty": 0,
                "admin": 0,
                "total": 0,
            }
            for u in users:
                role = u.get("role", "student")
                counts[role] = counts.get(role, 0) + 1
                counts["total"] += 1
            return counts
        except Exception as e:
            logger.error(f"Error getting user counts: {e}")
            return {
                "student": 0,
                "faculty": 0,
                "admin": 0,
                "total": 0,
            }

    # ==================== BULK OPERATIONS ====================

    async def bulk_update_students(
        self, updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Apply the same or different patches to multiple students.

        Parameters
        ----------
        updates : list[dict]
            Each dict **must** have ``"uid"`` plus any fields from
            ``STUDENT_EDITABLE_FIELDS``.

        Returns
        -------
        dict  with ``succeeded``, ``failed``, and ``errors`` lists.
        """
        succeeded: List[str] = []
        failed: List[Dict[str, str]] = []

        for entry in updates:
            uid = entry.pop("uid", None) or entry.pop("user_id", None)
            if not uid:
                failed.append(
                    {"uid": "?", "error": "Missing uid/user_id"}
                )
                continue
            try:
                await self.update_student(uid, entry)
                succeeded.append(uid)
            except Exception as e:
                failed.append({"uid": uid, "error": str(e)})

        return {
            "success": True,
            "total": len(updates),
            "succeeded": succeeded,
            "failed": failed,
        }

    async def bulk_update_faculty_status(
        self,
        uids: List[str],
        new_status: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Set the same status on several faculty members at once."""
        succeeded: List[str] = []
        failed: List[Dict[str, str]] = []

        for uid in uids:
            try:
                await self.update_faculty_status(uid, new_status, reason)
                succeeded.append(uid)
            except Exception as e:
                failed.append({"uid": uid, "error": str(e)})

        return {
            "success": True,
            "total": len(uids),
            "new_status": new_status,
            "succeeded": succeeded,
            "failed": failed,
        }