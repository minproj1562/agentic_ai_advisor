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


class AdminService:
    """Service for admin dashboard operations"""

    # ==================== DASHBOARD STATS ====================

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        try:
            db = _get_db()

            # Direct MongoDB counts
            student_count = await db.student_profiles.count_documents({})
            faculty_count = await Faculty.find().count()
            elective_count = await Elective.find(Elective.is_available == True).count()
            project_count = await db.student_projects.count_documents({})

            # Meeting counts
            try:
                meeting_count = await MeetingRequest.find().count()
                pending_meetings = await MeetingRequest.find(
                    MeetingRequest.status == "pending"
                ).count()
            except Exception:
                meeting_count = 0
                pending_meetings = 0

            # Faculty status breakdown
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

            # Firestore user counts
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
                "firestore_users": {"students": 0, "faculty": 0, "admin": 0},
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

            # Build query filter
            query_filter: Dict[str, Any] = {}

            if department:
                query_filter["branch"] = {"$regex": department, "$options": "i"}
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

            # Count total
            total = await collection.count_documents(query_filter)

            # Sort mapping
            sort_field_map = {
                "name": "name",
                "cgpa": "cgpa",
                "semester": "current_semester",
                "updated_at": "last_updated",
            }
            mongo_sort_field = sort_field_map.get(sort_by, "last_updated")
            sort_direction = -1 if sort_order == "desc" else 1

            # Fetch with pagination
            cursor = (
                collection
                .find(query_filter)
                .sort(mongo_sort_field, sort_direction)
                .skip(skip)
                .limit(limit)
            )
            students_raw = await cursor.to_list(length=limit)

            # Build response
            students = []
            for s in students_raw:
                # Get latest semester SGPA
                semester_sgpa = 0.0
                performance_trend = "stable"
                semester_records = s.get("semester_records", [])

                if semester_records:
                    # Sort by semester number to get latest
                    sorted_records = sorted(
                        semester_records,
                        key=lambda r: r.get("semester_number", 0),
                        reverse=True,
                    )
                    semester_sgpa = sorted_records[0].get("sgpa", 0.0)

                    # Calculate trend from last 2 semesters
                    if len(sorted_records) >= 2:
                        latest = sorted_records[0].get("sgpa", 0)
                        previous = sorted_records[1].get("sgpa", 0)
                        if latest > previous + 0.3:
                            performance_trend = "up"
                        elif latest < previous - 0.3:
                            performance_trend = "down"
                        else:
                            performance_trend = "stable"

                # Calculate weak/strong subjects from latest semester
                strong_subjects = []
                weak_subjects = []
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

                students.append({
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
                    "completed_credits": s.get("total_credits_earned", 0),
                    "total_credits": s.get("total_credits_required", 160),
                    "interests": s.get("interests", [])[:5],
                    "performance_trend": performance_trend,
                    "updated_at": str(s.get("last_updated", "")),
                })

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

    async def get_student_detail(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive student data from student_profiles"""
        try:
            db = _get_db()

            # Find by user_id
            student = await db.student_profiles.find_one({"user_id": uid})
            if not student:
                # Try by _id
                try:
                    from bson import ObjectId
                    student = await db.student_profiles.find_one(
                        {"_id": ObjectId(uid)}
                    )
                except Exception:
                    pass

            if not student:
                return None

            # Build subjects list from all semester records
            subjects_list = []
            semester_records = student.get("semester_records", [])

            for record in semester_records:
                sem_num = record.get("semester_number", 0)
                for subj in record.get("subjects", []):
                    gp = subj.get("grade_points", 0)
                    # Determine trend based on grade
                    trend = "stable"
                    if gp >= 9:
                        trend = "up"
                    elif gp <= 5:
                        trend = "down"

                    subjects_list.append({
                        "name": subj.get("subject_name", ""),
                        "code": subj.get("subject_code", ""),
                        "score": subj.get("total_marks", 0),
                        "credits": subj.get("credits", 0),
                        "trend": trend,
                        "grade": subj.get("grade", ""),
                        "grade_points": gp,
                        "semester": sem_num,
                        "internal_marks": subj.get("internal_marks", 0),
                        "external_marks": subj.get("external_marks", 0),
                    })

            # Calculate strong/weak subjects
            strong_subjects = [
                s["name"] for s in subjects_list if s.get("grade_points", 0) >= 9
            ]
            weak_subjects = [
                s["name"] for s in subjects_list if s.get("grade_points", 0) <= 6
            ]

            # Get latest SGPA
            semester_sgpa = 0.0
            if semester_records:
                latest = sorted(
                    semester_records,
                    key=lambda r: r.get("semester_number", 0),
                    reverse=True,
                )[0]
                semester_sgpa = latest.get("sgpa", 0.0)

            # Get projects
            projects = []
            try:
                project_docs = await db.student_projects.find(
                    {"student_id": uid}
                ).to_list(length=20)
                for p in project_docs:
                    projects.append({
                        "id": str(p.get("_id", "")),
                        "title": p.get("title", ""),
                        "description": p.get("description", ""),
                        "technologies": p.get("technologies", []),
                        "status": p.get("status", ""),
                        "created_at": str(p.get("created_at", "")),
                    })
            except Exception:
                pass

            # Get weaknesses
            weaknesses = []
            try:
                weakness_docs = await db.weakness_analysis.find(
                    {"student_id": uid}
                ).to_list(length=20)
                for w in weakness_docs:
                    weaknesses.append({
                        "id": str(w.get("_id", "")),
                        "subject": w.get("subject_name", ""),
                        "severity": w.get("severity", ""),
                        "score": w.get("score", 0),
                    })
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
                "completed_credits": student.get("total_credits_earned", 0),
                "total_credits": student.get("total_credits_required", 160),
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
            logger.error(f"Error getting student detail: {e}", exc_info=True)
            return None

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
            query_filter = {}
            if department:
                query_filter["department"] = department
            if status:
                query_filter["status"] = status

            find_query = Faculty.find(query_filter)
            total = await find_query.count()

            faculty_raw = (
                await find_query
                .sort([("updated_at", -1)])
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
                        profile_completeness = f.calculate_profile_completeness()
                except Exception:
                    pass

                faculty_list.append({
                    "id": str(f.id),
                    "user_id": f.user_id,
                    "name": f.name,
                    "email": f.email,
                    "department": f.department,
                    "designation": f.designation,
                    "status": f.status,
                    "phone": f.phone,
                    "specializations": (f.specializations or [])[:5],
                    "teaching_subjects": (f.teaching_subjects or [])[:5],
                    "mentee_count": len(f.mentee_ids or []),
                    "max_mentees": f.max_mentees,
                    "profile_setup_complete": f.profile_setup_complete,
                    "profile_completeness": profile_completeness,
                    "cv_uploaded": f.cv_url is not None,
                    "created_at": f.created_at.isoformat()
                    if f.created_at
                    else None,
                    "updated_at": f.updated_at.isoformat()
                    if f.updated_at
                    else None,
                })

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

    async def get_faculty_detail(self, uid: str) -> Optional[Dict[str, Any]]:
        try:
            faculty = await Faculty.find_one(Faculty.user_id == uid)
            if not faculty:
                return None

            profile_completeness = 0
            student_view = {}
            try:
                if faculty.uniform_profile:
                    profile_completeness = faculty.calculate_profile_completeness()
                    student_view = faculty.get_student_view()
            except Exception:
                pass

            meetings = []
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
                "cv_uploaded_at": faculty.cv_uploaded_at.isoformat()
                if faculty.cv_uploaded_at
                else None,
                "profile_setup_complete": faculty.profile_setup_complete,
                "profile_completeness": profile_completeness,
                "student_view": student_view,
                "meetings_count": len(meetings),
                "created_at": faculty.created_at.isoformat()
                if faculty.created_at
                else None,
            }
        except Exception as e:
            logger.error(f"Error getting faculty detail: {e}")
            return None

    # ==================== CURRICULUM ====================

    async def get_curriculum(
        self,
        semester: Optional[int] = None,
        admission_year: int = 2024,
    ) -> Dict[str, Any]:
        try:
            result = {}
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
            elective = await Elective.get(PydanticObjectId(elective_id))
            if not elective:
                raise Exception("Elective not found")

            allowed_fields = [
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
            ]

            for field in allowed_fields:
                if field in update_data:
                    setattr(elective, field, update_data[field])

            elective.updated_at = datetime.utcnow()
            await elective.save()

            return {
                "id": str(elective.id),
                "code": elective.code,
                "name": elective.name,
            }
        except Exception as e:
            logger.error(f"Error updating elective: {e}")
            raise

    async def create_elective(self, data: dict) -> Dict[str, Any]:
        try:
            elective = Elective(**data)
            await elective.insert()
            return {
                "id": str(elective.id),
                "code": elective.code,
                "name": elective.name,
            }
        except Exception as e:
            logger.error(f"Error creating elective: {e}")
            raise

    async def delete_elective(self, elective_id: str):
        try:
            elective = await Elective.get(PydanticObjectId(elective_id))
            if not elective:
                raise Exception("Elective not found")
            await elective.delete()
        except Exception as e:
            logger.error(f"Error deleting elective: {e}")
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

            # Top weak subjects
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
                comparison.append({
                    "department": dept,
                    "student_count": data["count"],
                    "average_cgpa": (
                        round(sum(cgpas) / len(cgpas), 2) if cgpas else 0
                    ),
                    "max_cgpa": round(max(cgpas), 2) if cgpas else 0,
                    "min_cgpa": round(min(cgpas), 2) if cgpas else 0,
                })

            return {"departments": comparison}
        except Exception as e:
            logger.error(f"Error getting department comparison: {e}")
            return {"departments": []}

    # ==================== USER COUNTS ====================

    async def get_user_counts(self) -> Dict[str, Any]:
        try:
            users = await firebase_manager.get_collection("users")
            counts = {"student": 0, "faculty": 0, "admin": 0, "total": 0}
            for u in users:
                role = u.get("role", "student")
                counts[role] = counts.get(role, 0) + 1
                counts["total"] += 1
            return counts
        except Exception as e:
            logger.error(f"Error getting user counts: {e}")
            return {"student": 0, "faculty": 0, "admin": 0, "total": 0}