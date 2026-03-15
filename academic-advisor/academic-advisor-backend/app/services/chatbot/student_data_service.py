# app/services/chatbot/student_data_service.py
"""
Consolidated Student Data Service
Single source of truth for student academic data
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Try importing models (may not be available during startup)
_models_available = False
try:
    from app.models.student_profile import StudentProfile
    _models_available = True
except ImportError:
    StudentProfile = None
    logger.info("StudentProfile model not available")

try:
    from app.models.student import StudentPerformance
except ImportError:
    StudentPerformance = None


class StudentDataService:
    """
    Unified service for fetching and formatting student data.
    Combines data from multiple sources into a single interface.
    """
    
    def __init__(self):
        self._cache = {}  # Simple in-memory cache
        self._cache_ttl = 300  # 5 minutes
    
    async def get_student_data(self, user_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        # NEVER CACHE FAILED LOOKUPS. EVER.
        if not force_refresh and user_id in self._cache:
            entry = self._cache[user_id]
            if (datetime.utcnow() - entry["timestamp"]).seconds < 300:
                return entry["data"]
        
        data = await self._fetch_from_db(user_id)
        
        # Only cache successful results
        if data and not data.get("_partial"):
            self._cache[user_id] = {
                "data": data,
                "timestamp": datetime.utcnow()
            }
        
        return data
    
    async def _fetch_from_db(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch student data from MongoDB.
        Tries multiple lookup strategies since user_id might be:
          - Firebase UID (real login)
          - Synthetic ID (seeded data)
          - Email-based match
        """
        if not _models_available or StudentProfile is None:
            logger.debug("StudentProfile model not available")
            return None

        try:
            profile = None

            # ── Strategy 1: Direct user_id match ──
            profile = await StudentProfile.find_one({"user_id": user_id})
            if profile:
                logger.debug(f"Found student by user_id: {profile.name}")
                return self._build_student_context(profile)

            # ── Strategy 2: Check if field named firebase_uid exists ──
            profile = await StudentProfile.find_one({"firebase_uid": user_id})
            if profile:
                logger.debug(f"Found student by firebase_uid: {profile.name}")
                # Update user_id for future lookups
                profile.user_id = user_id
                await profile.save()
                return self._build_student_context(profile)

            # ── Strategy 3: Get email from Firebase Auth, match by email ──
            email = None
            display_name = None
            try:
                from firebase_admin import auth as fb_auth
                fb_user = fb_auth.get_user(user_id)
                if fb_user:
                    email = fb_user.email
                    display_name = fb_user.display_name
            except Exception as e:
                logger.debug(f"Firebase user lookup failed: {e}")

            if email:
                profile = await StudentProfile.find_one({"email": email})
                if profile:
                    logger.info(f"✅ Found student by email {email}: {profile.name}")
                    # Link for future fast lookups
                    profile.user_id = user_id
                    if display_name and (not profile.name or profile.name.startswith("student")):
                        profile.name = display_name
                    await profile.save()

                    # Also update StudentPerformance references
                    await self._update_performance_uid(profile.roll_number, user_id)
                    return self._build_student_context(profile)

            # ── Strategy 4: Check Firestore users collection for email ──
            if not email:
                try:
                    from firebase_admin import firestore
                    fs_db = firestore.client()
                    user_doc = fs_db.collection('users').document(user_id).get()
                    if user_doc.exists:
                        user_data = user_doc.to_dict()
                        email = user_data.get('email', '')
                        display_name = user_data.get('name', '')
                        if email:
                            profile = await StudentProfile.find_one({"email": email})
                            if profile:
                                profile.user_id = user_id
                                if display_name:
                                    profile.name = display_name
                                await profile.save()
                                logger.info(f"✅ Linked via Firestore: {profile.name}")
                                return self._build_student_context(profile)
                except Exception as e:
                    logger.debug(f"Firestore lookup failed: {e}")

            # ── Strategy 5: Return basic info even without profile ──
            # So the chatbot at least knows the student's name
            if display_name or email:
                logger.info(f"No StudentProfile for {display_name or email}, returning basic context")
                return {
                    "name": display_name or "",
                    "email": email or "",
                    "branch": "",
                    "semester": None,
                    "cgpa": None,  # None, not 0 — so chatbot knows data is missing
                    "subjects": [],
                    "weak_subjects": [],
                    "strong_subjects": [],
                    "sgpa_trend": [],
                    "latest_sgpa": None,
                    "skills": [],
                    "interests": [],
                    "career_goals": [],
                    "performance_summary": {"level": "unknown", "trend": "unknown"},
                    "_partial": True,  # Flag: only basic info available
                }

            logger.debug(f"No student data found for user_id={user_id[:12]}...")
            return None

        except Exception as e:
            logger.error(f"Student data fetch error: {e}", exc_info=True)
            return None

    async def _update_performance_uid(self, roll_number: str, new_uid: str):
        """Update StudentPerformance/StudentInfo when we link a profile."""
        try:
            from app.database.connection import get_mongo_database
            db = get_mongo_database()
            if db and roll_number:
                # Update StudentInfo
                await db["student_info"].update_many(
                    {"roll_number": roll_number},
                    {"$set": {"uid": new_uid}}
                )
                logger.debug(f"Updated StudentInfo for roll {roll_number}")
        except Exception as e:
            logger.debug(f"Performance UID update failed: {e}")
    
    def _build_student_context(self, profile) -> Dict[str, Any]:
        """Build student context from profile."""
        # Basic info
        data = {
            "name": getattr(profile, 'name', ''),
            "branch": getattr(profile, 'branch', 'IT'),
            "semester": getattr(profile, 'current_semester', 1),
            "roll_number": getattr(profile, 'roll_number', ''),
            "email": getattr(profile, 'email', ''),
            "cgpa": getattr(profile, 'cgpa', 0.0),
            "admission_year": getattr(profile, 'admission_year', 0),
        }
        
        # Process semester records
        semester_records = getattr(profile, 'semester_records', []) or []
        subjects = []
        weak_subjects = []
        strong_subjects = []
        sgpa_trend = []
        
        for sem in semester_records:
            sem_num = getattr(sem, 'semester_number', 0)
            sgpa = getattr(sem, 'sgpa', 0.0)
            
            sgpa_trend.append({
                "semester": sem_num,
                "sgpa": sgpa,
                "credits": getattr(sem, 'credits_earned', 0),
            })
            
            # Process subjects
            sem_subjects = getattr(sem, 'subjects', []) or []
            for subj in sem_subjects:
                score = (
                    getattr(subj, 'total_marks', 0) or 
                    getattr(subj, 'marks_obtained', 0) or 
                    0
                )
                subject_name = getattr(subj, 'subject_name', '')
                
                subjects.append({
                    "name": subject_name,
                    "code": getattr(subj, 'subject_code', ''),
                    "score": score,
                    "grade": getattr(subj, 'grade', ''),
                    "credits": getattr(subj, 'credits', 3),
                    "semester": sem_num,
                })
                
                # Categorize as weak/strong
                if score < 50:
                    weak_subjects.append(subject_name)
                elif score >= 75:
                    strong_subjects.append(subject_name)
        
        # Add processed data
        data.update({
            "subjects": subjects,
            "weak_subjects": list(set(weak_subjects)),
            "strong_subjects": list(set(strong_subjects)),
            "sgpa_trend": sorted(sgpa_trend, key=lambda x: x["semester"]),
            "latest_sgpa": sgpa_trend[-1]["sgpa"] if sgpa_trend else 0.0,
            "total_credits_earned": getattr(profile, 'total_credits_earned', 0),
            "total_credits_required": getattr(profile, 'total_credits_required', 160),
        })
        
        # Additional profile data
        data.update({
            "interests": getattr(profile, 'interests', []) or [],
            "career_goals": getattr(profile, 'career_goals', []) or [],
            "skills": getattr(profile, 'skills', []) or [],
        })
        
        # Calculate performance metrics
        data["performance_summary"] = self._calculate_performance_summary(data)
        
        return data
    
    def _calculate_performance_summary(self, data: Dict) -> Dict[str, Any]:
        """Calculate performance summary metrics."""
        cgpa = data.get("cgpa", 0)
        weak_count = len(data.get("weak_subjects", []))
        strong_count = len(data.get("strong_subjects", []))
        sgpa_trend = data.get("sgpa_trend", [])
        
        # Determine trend
        trend = "stable"
        if len(sgpa_trend) >= 2:
            recent = sgpa_trend[-1]["sgpa"]
            previous = sgpa_trend[-2]["sgpa"]
            if recent > previous + 0.2:
                trend = "improving"
            elif recent < previous - 0.2:
                trend = "declining"
        
        # Performance level
        if cgpa >= 8.5:
            level = "excellent"
        elif cgpa >= 7.5:
            level = "good"
        elif cgpa >= 6.0:
            level = "average"
        else:
            level = "needs_improvement"
        
        return {
            "trend": trend,
            "level": level,
            "weak_subject_count": weak_count,
            "strong_subject_count": strong_count,
            "needs_attention": weak_count > 2 or cgpa < 6.0,
        }
    
    def _get_from_cache(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get from in-memory cache."""
        if user_id not in self._cache:
            return None
        
        entry = self._cache[user_id]
        if (datetime.utcnow() - entry["timestamp"]).seconds > self._cache_ttl:
            del self._cache[user_id]
            return None
        
        return entry["data"]
    
    def _set_cache(self, user_id: str, data: Dict[str, Any]):
        """Set in-memory cache."""
        self._cache[user_id] = {
            "data": data,
            "timestamp": datetime.utcnow(),
        }
        
        # Clean old entries
        if len(self._cache) > 100:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest_key]
    
    def invalidate_cache(self, user_id: str):
        """Invalidate cache for a user."""
        if user_id in self._cache:
            del self._cache[user_id]
    
    async def get_performance_for_analysis(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get performance data formatted for analysis responses."""
        data = await self.get_student_data(user_id)
        if not data:
            return None
        
        # Format for performance analysis response
        return {
            "profile": {
                "name": data.get("name", "Student"),
                "branch": data.get("branch"),
                "semester": data.get("semester"),
                "cgpa": data.get("cgpa"),
            },
            "current_cgpa": data.get("cgpa"),
            "latest_sgpa": data.get("latest_sgpa"),
            "sgpa_trend": data.get("sgpa_trend", []),
            "trend_direction": data.get("performance_summary", {}).get("trend", "stable"),
            "weak_subjects": data.get("weak_subjects", []),
            "strong_subjects": data.get("strong_subjects", []),
            "subject_analysis": self._build_subject_analysis(data.get("subjects", [])),
        }
    
    def _build_subject_analysis(self, subjects: List[Dict]) -> List[Dict]:
        """Build subject analysis for response."""
        analysis = []
        for subj in subjects[-10:]:  # Last 10 subjects
            score = subj.get("score", 0)
            if score < 50:
                status = "weak"
            elif score >= 75:
                status = "strong"
            else:
                status = "average"
            
            analysis.append({
                "subject": subj.get("name"),
                "score": score,
                "grade": subj.get("grade", ""),
                "status": status,
            })
        
        return analysis


# Singleton instance
_student_data_service = None


def get_student_data_service() -> StudentDataService:
    """Get or create student data service singleton."""
    global _student_data_service
    if _student_data_service is None:
        _student_data_service = StudentDataService()
    return _student_data_service