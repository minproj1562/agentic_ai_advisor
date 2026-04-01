# academic-advisor-backend/app/services/readiness_service.py
"""
Academic Readiness Engine — 8-Step Pipeline
============================================
Every threshold, weight, and subject mapping is read from MongoDB at runtime.
"""

import re
import logging
import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.models.readiness import (
    SubjectRequirementMap, RequiredSubject,
    ReadinessResult, MatchedSubject, WeaknessEntry,
    ReadinessResponse, ReadinessSummaryResponse,
    ElectiveReadinessResponse, HonoursReadinessResponse,
)
from app.models.student_profile import StudentProfile
from app.models.weakness import StudentInterestProfile
from app.models.recommendation import RecommendationRecord

logger = logging.getLogger(__name__)


class ReadinessService:
    _seeded: bool = False

    # ════════════════════════════════════════════════════════════════
    #  AUTO-SEED
    # ════════════════════════════════════════════════════════════════

    async def _ensure_seeded(self) -> None:
        if ReadinessService._seeded:
            return
        count = await SubjectRequirementMap.count()
        if count == 0:
            logger.info("📦 SubjectRequirementMap collection empty — seeding …")
            await self._seed_default_maps()
        ReadinessService._seeded = True

    async def _seed_default_maps(self) -> None:
        from app.services._seed_readiness_data import build_seed_documents
        docs = build_seed_documents()
        for doc in docs:
            await doc.insert()
        logger.info(f"✅ Seeded {len(docs)} requirement maps")

    # ════════════════════════════════════════════════════════════════
    #  MAIN PIPELINE
    # ════════════════════════════════════════════════════════════════

    async def calculate_readiness(
        self,
        student_id: str,
        interests: Optional[List[str]] = None,
        electives: Optional[List[str]] = None,
        honours: Optional[List[str]] = None,
    ) -> ReadinessResponse:
        await self._ensure_seeded()

        interests, electives, honours = await self._resolve_goals(
            student_id, interests, electives, honours
        )

        if not interests and not electives and not honours:
            return ReadinessResponse(
                student_id=student_id,
                primary_recommendation=(
                    "No interests, electives, or honours selected. "
                    "Please set your academic goals first."
                ),
            )

        target_profile = await self._build_target_profile(
            interests, electives, honours
        )

        student_data = await self._load_student_scores(student_id)
        is_first_sem = student_data["is_first_semester"]
        matched = self._match_performance(target_profile, student_data)
        matched = self._identify_weaknesses(matched, is_first_sem)
        matched = self._assign_severity(matched)

        overall, cat_scores, breakdowns = self._calculate_readiness_scores(
            matched, is_first_sem, interests, electives, honours
        )

        weakness_entries = self._prioritise_weaknesses(matched)
        study_plan = self._generate_study_plan(weakness_entries, overall)

        level, rec_type, primary_rec, detail_recs = (
            self._generate_recommendation(overall, weakness_entries, is_first_sem)
        )

        has_critical = any(w.severity == "critical" for w in weakness_entries)
        has_blockers = has_critical or overall < 30
        focus_subjects = [w.subject for w in weakness_entries[:5]]
        prep_time = self._estimate_preparation_time(weakness_entries)

        resp = ReadinessResponse(
            student_id=student_id,
            overall_readiness_score=round(overall, 1),
            readiness_level=level,
            recommendation_type=rec_type,
            primary_recommendation=primary_rec,
            interest_readiness=round(cat_scores.get("interest", 0), 1),
            elective_readiness=round(cat_scores.get("elective", 0), 1),
            honours_readiness=round(cat_scores.get("honours", 0), 1),
            interest_breakdown=breakdowns.get("interest", {}),
            elective_breakdown=breakdowns.get("elective", {}),
            honours_breakdown=breakdowns.get("honours", {}),
            has_critical_weakness=has_critical,
            has_blockers=has_blockers,
            is_first_semester=is_first_sem,
            subjects_to_focus=focus_subjects,
            estimated_preparation_time=prep_time,
            detailed_recommendations=detail_recs,
            weaknesses=[w.dict() for w in weakness_entries],
            study_plan=study_plan,
            analysis_timestamp=datetime.utcnow().isoformat(),
        )

        await self._save_result(resp, interests, electives, honours)
        return resp

    # ════════════════════════════════════════════════════════════════
    #  SINGLE-TARGET HELPERS
    # ════════════════════════════════════════════════════════════════

    # ════════════════════════════════════════════════════════════════
    #  REPLACE check_elective_readiness with this enhanced version
    # ════════════════════════════════════════════════════════════════

    async def check_elective_readiness(
        self, student_id: str, elective_code: str
    ) -> ElectiveReadinessResponse:
        """
        Detailed readiness check for a specific elective.
        Returns per-prerequisite scores, strengths, gaps, and preparation plan.
        Uses ONLY data already in the student's profile (no manual input).
        """
        from app.models.readiness import PrerequisiteDetail

        await self._ensure_seeded()
        req_map = await self._find_map("elective", elective_code)
        if not req_map:
            return ElectiveReadinessResponse(
                student_id=student_id,
                elective=elective_code,
                recommendation=(
                    f"No requirement map found for '{elective_code}'. "
                    "Ask your faculty to add it, or try the full name."
                ),
            )

        student = await self._load_student_scores(student_id)
        subjects = student["subjects"]
        is_first = student["is_first_semester"]

        matched = self._match_performance(
            self._convert_map_to_target(req_map, "elective"), student
        )
        matched = self._identify_weaknesses(matched, is_first)
        matched = self._assign_severity(matched)

        score = self._readiness_from_matched(matched, is_first)

        # ── Build detailed prerequisite breakdown ──
        prerequisites: list = []
        strengths: list = []
        gaps: list = []
        prep_plan: list = []

        for m in matched:
            current = m.student_score if m.student_score is not None else 0

            if m.is_taken and current >= m.min_score + 10:
                status = "strong"
                strengths.append(f"{m.subject_name} ({current:.0f}%)")
            elif m.is_taken and current >= m.min_score:
                status = "adequate"
                strengths.append(f"{m.subject_name} ({current:.0f}%)")
            elif m.is_taken:
                status = "weak"
                gap_val = m.min_score - current
                gaps.append(
                    f"{m.subject_name}: need {m.min_score:.0f}%, "
                    f"have {current:.0f}% (gap: {gap_val:.0f})"
                )
                prep_plan.append(
                    f"📚 Revise {m.subject_name} — improve by "
                    f"{gap_val:.0f} marks ({m.importance_label} priority)"
                )
            else:
                status = "missing"
                gaps.append(f"{m.subject_name}: not yet taken/recorded")
                if not is_first:
                    prep_plan.append(
                        f"⚠️ {m.subject_name} not found in your records "
                        f"— ensure marks are uploaded"
                    )

            prerequisites.append(PrerequisiteDetail(
                subject_name=m.subject_name,
                subject_code=m.subject_code,
                current_score=round(current, 1),
                required_score=m.min_score,
                gap=round(max(0, m.min_score - current), 1),
                importance=m.importance,
                importance_label=m.importance_label,
                status=status,
                is_taken=m.is_taken,
                confidence=m.confidence,
            ))

        # ── Determine readiness level ──
        if score >= 80:
            level = "ready"
            rec = (
                f"You're well-prepared for {req_map.target_name}! "
                "Your prerequisites are strong."
            )
            weeks = 0
        elif score >= 65:
            level = "mostly_ready"
            rec = (
                f"Mostly ready for {req_map.target_name}. "
                f"Minor revision in {len(gaps)} area(s) will help."
            )
            weeks = 2
        elif score >= 40:
            level = "needs_work"
            rec = (
                f"You can consider {req_map.target_name}, but "
                "significant preparation is recommended first."
            )
            weeks = 6
        else:
            level = "not_ready"
            rec = (
                f"Prerequisites for {req_map.target_name} need "
                "substantial work. Strengthen fundamentals first."
            )
            weeks = 10

        if is_first:
            rec += (
                " (Note: As a first-semester student, some subjects "
                "haven't been taken yet — this is expected.)"
            )

        weak_subj = [m.subject_name for m in matched if m.is_weakness]
        prep_time = self._estimate_preparation_time(
            self._prioritise_weaknesses(matched)
        )

        return ElectiveReadinessResponse(
            student_id=student_id,
            elective=req_map.target_name,
            elective_code=req_map.target_code,
            readiness_score=round(score, 1),
            readiness_level=level,
            is_ready=score >= 65,
            recommendation=rec,
            prerequisites=prerequisites,
            strengths=strengths,
            gaps=gaps,
            subjects_to_focus=weak_subj[:5],
            preparation_plan=prep_plan[:5],
            preparation_time=prep_time,
            estimated_preparation_weeks=weeks,
        )

    async def check_honours_readiness(
        self, student_id: str, programme: str
    ) -> HonoursReadinessResponse:
        await self._ensure_seeded()
        req_map = await self._find_map("honours", programme)
        if not req_map:
            return HonoursReadinessResponse(
                student_id=student_id,
                programme=programme,
                recommendation=f"No requirement map found for '{programme}'.",
            )

        student = await self._load_student_scores(student_id)
        cgpa = student.get("cgpa", 0)
        min_cgpa = req_map.min_cgpa or 0

        matched = self._match_performance(
            self._convert_map_to_target(req_map, "honours"), student
        )
        matched = self._identify_weaknesses(matched, student["is_first_semester"])
        matched = self._assign_severity(matched)

        score = self._readiness_from_matched(matched, student["is_first_semester"])
        is_eligible = cgpa >= min_cgpa

        blockers: List[str] = []
        if not is_eligible:
            blockers.append(f"CGPA {cgpa:.2f} is below required {min_cgpa:.1f}")
        for m in matched:
            if m.severity == "critical":
                blockers.append(f"{m.subject_name} score is critically low")

        steps = self._honours_steps(matched, is_eligible, min_cgpa, cgpa)
        weak_subj = [m.subject_name for m in matched if m.is_weakness]
        prep = self._estimate_preparation_time(self._prioritise_weaknesses(matched))

        return HonoursReadinessResponse(
            student_id=student_id,
            programme=req_map.target_name,
            readiness_score=round(score, 1),
            is_eligible=is_eligible and score >= 60,
            recommendation=self._honours_rec_text(score, is_eligible),
            blockers=blockers,
            preparation_time=prep,
            detailed_steps=steps,
        )

    async def get_summary(self, student_id: str) -> ReadinessSummaryResponse:
        latest = await ReadinessResult.find_one(
            {"student_id": student_id, "is_current": True}
        )
        if not latest:
            return ReadinessSummaryResponse(
                student_id=student_id,
                primary_action="Run a readiness analysis first.",
                timestamp=datetime.utcnow().isoformat(),
            )
        ts = latest.analysis_timestamp
        if hasattr(ts, 'isoformat'):
            ts = ts.isoformat()
        else:
            ts = str(ts)
        return ReadinessSummaryResponse(
            student_id=student_id,
            overall_readiness=latest.overall_readiness_score,
            level=latest.readiness_level,
            can_proceed=latest.recommendation_type in ("proceed", "proceed_with_caution"),
            critical_issues=latest.has_critical_weakness,
            primary_action=latest.primary_recommendation,
            timestamp=ts,
        )

    # ════════════════════════════════════════════════════════════════
    #  STEP 1 — BUILD TARGET PROFILE
    # ════════════════════════════════════════════════════════════════

    async def _build_target_profile(
        self,
        interests: List[str],
        electives: List[str],
        honours: List[str],
    ) -> List[MatchedSubject]:
        merged: Dict[str, MatchedSubject] = {}

        async def _merge(goal_type: str, names: List[str]):
            for name in names:
                req_map = await self._find_map(goal_type, name)
                if not req_map:
                    logger.warning(f"No map for {goal_type}='{name}'")
                    continue
                for rs in req_map.required_subjects:
                    key = rs.subject_name.lower()
                    if key in merged:
                        existing = merged[key]
                        if rs.importance > existing.importance:
                            existing.importance = rs.importance
                            existing.importance_label = rs.importance_label
                        existing.min_score = max(existing.min_score, rs.min_score)
                        existing.weight = max(existing.weight, rs.weight)
                        if name not in existing.linked_goals:
                            existing.linked_goals.append(name)
                        if goal_type not in existing.goal_types:
                            existing.goal_types.append(goal_type)
                    else:
                        merged[key] = MatchedSubject(
                            subject_name=rs.subject_name,
                            subject_code=rs.subject_code,
                            importance=rs.importance,
                            importance_label=rs.importance_label,
                            min_score=rs.min_score,
                            weight=rs.weight,
                            linked_goals=[name],
                            goal_types=[goal_type],
                        )

        await _merge("interest", interests)
        await _merge("elective", electives)
        await _merge("honours", honours)

        return list(merged.values())

    async def _find_map(
        self, target_type: str, name: str
    ) -> Optional[SubjectRequirementMap]:
        """Flexible look-up: exact → case-insensitive → alias."""
        # 1. Exact match
        result = await SubjectRequirementMap.find_one(
            {"target_type": target_type, "target_name": name, "is_active": True}
        )
        if result:
            return result

        # 2. Case-insensitive match
        regex = re.compile(f"^{re.escape(name)}$", re.IGNORECASE)
        result = await SubjectRequirementMap.find_one(
            {"target_type": target_type, "target_name": {"$regex": regex}, "is_active": True}
        )
        if result:
            return result

        # 3. Alias match
        result = await SubjectRequirementMap.find_one(
            {"target_type": target_type, "target_aliases": {"$regex": regex}, "is_active": True}
        )
        return result

    # ════════════════════════════════════════════════════════════════
    #  STEP 2 — MATCH STUDENT PERFORMANCE
    # ════════════════════════════════════════════════════════════════

    async def _load_student_scores(self, student_id: str) -> Dict[str, Any]:
        """Load student's subject scores from their profile."""
        profile = await StudentProfile.find_one({"user_id": student_id})
        
        if not profile:
            logger.warning(f"No profile found for student {student_id}")
            return {
                "subjects": {},
                "cgpa": 0,
                "semester": 1,
                "is_first_semester": True,
            }

        subjects: Dict[str, Dict[str, Any]] = {}
        
        for sem in profile.semester_records:
            for subj in sem.subjects:
                key = subj.subject_name
                
                # Use total_marks directly - AcademicDataEntry stores 
                # internal_marks + external_marks in total_marks
                score = subj.total_marks
                
                # Safety: normalize if > 100 (shouldn't happen with proper entry)
                if score > 100:
                    internal_max = getattr(subj, 'internal_max', 20)
                    external_max = getattr(subj, 'external_max', 80)
                    max_marks = internal_max + external_max
                    if max_marks > 0:
                        score = (score / max_marks) * 100
                    else:
                        score = min(score, 100)

                existing = subjects.get(key)
                if not existing or score > existing["score"]:
                    subjects[key] = {
                        "score": round(score, 1),
                        "code": subj.subject_code,
                        "credits": subj.credits,
                        "grade": subj.grade,
                    }

        completed = len(profile.semester_records)
        
        return {
            "subjects": subjects,
            "cgpa": profile.cgpa,
            "semester": profile.current_semester,
            "is_first_semester": completed <= 1,
        }

    def _match_performance(
        self, target_profile: List[MatchedSubject], student_data: Dict[str, Any],
    ) -> List[MatchedSubject]:
        """Match student scores against required subjects."""
        subjects = student_data["subjects"]
        is_first = student_data["is_first_semester"]

        for entry in target_profile:
            score, confidence = self._find_score(subjects, entry)
            if score is not None:
                entry.student_score = score
                entry.is_taken = True
                entry.confidence = confidence
            else:
                entry.student_score = None
                entry.is_taken = False
                entry.confidence = 0.3 if is_first else 0.6

        return target_profile

    def _find_score(
        self, subjects: Dict[str, Dict[str, Any]], entry: MatchedSubject,
    ) -> Tuple[Optional[float], float]:
        """Find the student's score for a required subject."""
        target = entry.subject_name.lower()

        # Exact match
        for name, data in subjects.items():
            if name.lower() == target:
                return data["score"], 1.0

        # Code match
        if entry.subject_code:
            for name, data in subjects.items():
                if (data.get("code") or "").upper() == entry.subject_code.upper():
                    return data["score"], 1.0

        # Partial match
        for name, data in subjects.items():
            nl = name.lower()
            if target in nl or nl in target:
                return data["score"], 0.9

        # Word overlap
        tw = set(target.split())
        for name, data in subjects.items():
            nw = set(name.lower().split())
            common = tw & nw
            if len(common) >= 2 or (len(common) >= 1 and len(tw) == 1):
                return data["score"], 0.8

        return None, 0.0

    # ════════════════════════════════════════════════════════════════
    #  STEP 3 — IDENTIFY WEAKNESSES
    # ════════════════════════════════════════════════════════════════

    def _identify_weaknesses(
        self, matched: List[MatchedSubject], is_first_semester: bool
    ) -> List[MatchedSubject]:
        """Identify which subjects are weaknesses based on gap analysis."""
        for m in matched:
            if m.is_taken:
                if m.student_score is not None and m.student_score < m.min_score:
                    m.gap = m.min_score - m.student_score
                    m.is_weakness = True
                else:
                    m.gap = 0
                    m.is_weakness = False
            else:
                # Subject not taken yet
                if is_first_semester:
                    m.gap = m.min_score * 0.3
                    m.is_weakness = m.importance >= 0.7
                else:
                    m.gap = m.min_score
                    m.is_weakness = True
        return matched

    # ════════════════════════════════════════════════════════════════
    #  STEP 4 — ASSIGN SEVERITY
    # ════════════════════════════════════════════════════════════════

    def _assign_severity(self, matched: List[MatchedSubject]) -> List[MatchedSubject]:
        """Assign severity levels to weaknesses."""
        for m in matched:
            if not m.is_weakness:
                m.severity = "none"
                continue
            effective_gap = m.gap * m.importance * m.confidence
            if effective_gap >= 30:
                m.severity = "critical"
            elif effective_gap >= 20:
                m.severity = "high"
            elif effective_gap >= 10:
                m.severity = "medium"
            else:
                m.severity = "low"
        return matched

    # ════════════════════════════════════════════════════════════════
    #  STEP 5 — CALCULATE READINESS SCORES
    # ════════════════════════════════════════════════════════════════

    def _calculate_readiness_scores(
        self, matched: List[MatchedSubject], is_first_sem: bool,
        interests: List[str], electives: List[str], honours: List[str],
    ) -> Tuple[float, Dict[str, float], Dict[str, Dict[str, float]]]:
        """Calculate overall and per-category readiness scores."""
        overall = self._readiness_from_matched(matched, is_first_sem)
        cat_scores: Dict[str, float] = {}
        breakdowns: Dict[str, Dict[str, float]] = {"interest": {}, "elective": {}, "honours": {}}

        for cat, names in [("interest", interests), ("elective", electives), ("honours", honours)]:
            cat_entries = [m for m in matched if cat in m.goal_types]
            cat_scores[cat] = self._readiness_from_matched(cat_entries, is_first_sem) if cat_entries else 0
            for name in names:
                entries = [m for m in matched if name in m.linked_goals]
                if entries:
                    breakdowns[cat][name] = round(self._readiness_from_matched(entries, is_first_sem), 1)

        return overall, cat_scores, breakdowns

    def _readiness_from_matched(
        self, entries: List[MatchedSubject], is_first_sem: bool
    ) -> float:
        """Calculate readiness score from matched subjects."""
        if not entries:
            return 0.0
        total_max = 0.0
        total_achieved = 0.0
        for m in entries:
            w = m.weight * m.importance
            total_max += w
            if m.is_taken and m.student_score is not None:
                ratio = min(m.student_score / m.min_score, 1.2)
                total_achieved += ratio * w * m.confidence
            else:
                total_achieved += (0.35 if is_first_sem else 0.10) * w
        if total_max == 0:
            return 0.0
        return max(0, min(100, (total_achieved / total_max) * 100))

    # ════════════════════════════════════════════════════════════════
    #  STEP 6 — PRIORITISE WEAKNESSES
    # ════════════════════════════════════════════════════════════════

    def _prioritise_weaknesses(self, matched: List[MatchedSubject]) -> List[WeaknessEntry]:
        """Prioritize and format weakness entries."""
        weak = [m for m in matched if m.is_weakness]
        sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}
        weak.sort(key=lambda m: (sev_order.get(m.severity, 4), -m.importance, -len(m.linked_goals)))

        entries: List[WeaknessEntry] = []
        for rank, m in enumerate(weak, 1):
            entries.append(WeaknessEntry(
                subject=m.subject_name,
                current_score=m.student_score or 0,
                target_score=m.min_score,
                gap=round(m.gap, 1),
                severity=m.severity,
                importance=m.importance,
                importance_label=m.importance_label,
                confidence=m.confidence,
                linked_goals=m.linked_goals,
                goal_types=m.goal_types,
                suggestions=self._suggestions(m),
                resources=self._resources(m.subject_name),
                estimated_hours=self._est_hours(m.gap, m.importance),
                priority_rank=rank,
            ))
        return entries

    # ════════════════════════════════════════════════════════════════
    #  STEP 7 — STUDY PLAN
    # ════════════════════════════════════════════════════════════════

    def _generate_study_plan(
        self, weaknesses: List[WeaknessEntry], readiness: float
    ) -> Dict[str, Any]:
        """Generate a study plan based on weaknesses."""
        if not weaknesses:
            return {
                "duration_weeks": 0,
                "weekly_hours": 0,
                "message": "No weaknesses detected — no study plan needed."
            }

        total_hours = sum(w.estimated_hours for w in weaknesses[:6])
        weeks = max(6, min(8, math.ceil(total_hours / 12)))
        weekly = round(total_hours / weeks, 1)

        focus_areas = [{
            "subject": w.subject,
            "priority": w.priority_rank,
            "current_score": w.current_score,
            "target_score": w.target_score,
            "weekly_hours": round(w.estimated_hours / weeks, 1),
            "severity": w.severity,
        } for w in weaknesses[:6]]

        critical_high = [w.subject for w in weaknesses if w.severity in ("critical", "high")][:3]
        
        phases = [
            {
                "name": "Foundation Building",
                "weeks": "1–2",
                "focus": critical_high or [weaknesses[0].subject],
                "goals": ["Review fundamentals", "Complete basic exercises"]
            },
            {
                "name": "Active Practice",
                "weeks": f"3–{weeks - 2}",
                "focus": [w.subject for w in weaknesses[:4]],
                "goals": ["Solve practice problems", "Timed quizzes"]
            },
            {
                "name": "Mastery & Revision",
                "weeks": f"{weeks - 1}–{weeks}",
                "focus": [w.subject for w in weaknesses[:5]],
                "goals": ["Mock tests", "Target-score verification"]
            },
        ]

        milestones = [
            {"week": 2, "target": "Complete fundamentals review"},
            {"week": max(3, weeks // 2), "target": "Score ≥60% in practice tests"},
            {"week": weeks - 1, "target": "Score ≥70% in practice tests"},
            {"week": weeks, "target": "Achieve target proficiency"},
        ]

        return {
            "duration_weeks": weeks,
            "weekly_hours": weekly,
            "weekly_commitment": f"{weekly} hours / week",
            "focus_areas": focus_areas,
            "phases": phases,
            "milestones": milestones,
            "current_readiness": round(readiness, 1),
            "target_readiness": 80,
            "recommendation": "Follow this plan consistently to raise readiness above 80%.",
        }

    # ════════════════════════════════════════════════════════════════
    #  STEP 8 — SAFE RECOMMENDATION
    # ════════════════════════════════════════════════════════════════

    def _generate_recommendation(
        self, readiness: float, weaknesses: List[WeaknessEntry], is_first_sem: bool,
    ) -> Tuple[str, str, str, List[str]]:
        """Generate safe recommendation based on analysis."""
        critical = [w for w in weaknesses if w.severity == "critical"]
        high = [w for w in weaknesses if w.severity == "high"]

        # Determine level
        if readiness >= 85:
            level = "excellent"
        elif readiness >= 70:
            level = "good"
        elif readiness >= 55:
            level = "moderate"
        elif readiness >= 40:
            level = "low"
        else:
            level = "not_ready"

        # Determine recommendation type
        if readiness >= 75 and not critical:
            rec_type = "proceed"
        elif readiness >= 60 and not critical:
            rec_type = "proceed_with_caution"
        elif readiness >= 35 or (critical and readiness >= 40):
            rec_type = "improve_first"
        else:
            rec_type = "do_not_proceed"

        texts = {
            "proceed": "You are academically prepared. Proceed with confidence.",
            "proceed_with_caution": "You meet most requirements. Proceed but improve weak areas in parallel.",
            "improve_first": "Critical gaps detected. Improve the listed subjects before committing to these choices.",
            "do_not_proceed": "Significant foundational gaps exist. Focus on strengthening these areas before selecting advanced electives or honours.",
        }
        primary = texts[rec_type]

        detail: List[str] = []
        if critical:
            detail.append(f"🔴 Critical: Improve {', '.join(w.subject for w in critical[:3])} immediately.")
        if high:
            detail.append(f"🟠 High priority: Strengthen {', '.join(w.subject for w in high[:3])}.")
        if is_first_sem:
            detail.append("ℹ️ As a first-semester student, some subjects haven't been taken yet — this is expected.")
        if rec_type in ("improve_first", "do_not_proceed"):
            detail.append("⏸️ Consider delaying elective / honours selection until you have improved the flagged subjects.")
        if rec_type == "proceed":
            detail.append("✅ Your profile aligns well — good to go!")

        return level, rec_type, primary, detail

    # ════════════════════════════════════════════════════════════════
    #  RESOLVE GOALS FROM DB
    # ════════════════════════════════════════════════════════════════

    async def _resolve_goals(
        self, student_id: str,
        interests: Optional[List[str]],
        electives: Optional[List[str]],
        honours: Optional[List[str]],
    ) -> Tuple[List[str], List[str], List[str]]:
        """Resolve goals from request params or database."""
        if interests and electives and honours:
            return interests, electives, honours

        try:
            ip = await StudentInterestProfile.find_one({"user_id": student_id})
            if ip:
                interests = interests or getattr(ip, 'interests', None) or []
                honours = honours or getattr(ip, 'honours_minors_interest', None) or []
                electives = electives or getattr(ip, 'preferred_electives', None) or []
        except Exception as e:
            logger.warning(f"Could not fetch StudentInterestProfile: {e}")

        if not interests:
            try:
                sp = await StudentProfile.find_one({"user_id": student_id})
                if sp:
                    interests = interests or getattr(sp, 'interests', None) or []
            except Exception as e:
                logger.warning(f"Could not fetch StudentProfile: {e}")

        if not electives:
            try:
                rec = await RecommendationRecord.find_one(
                    {"student_id": student_id, "is_active": True}
                )
                if rec and hasattr(rec, 'electives') and rec.electives:
                    electives = [e.elective_name for e in rec.electives[:4]]
            except Exception as e:
                logger.warning(f"Could not fetch RecommendationRecord: {e}")

        return interests or [], electives or [], honours or []

    # ════════════════════════════════════════════════════════════════
    #  SMALL HELPERS
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def _convert_map_to_target(
        req_map: SubjectRequirementMap, goal_type: str
    ) -> List[MatchedSubject]:
        """Convert a requirement map to a list of MatchedSubject."""
        return [
            MatchedSubject(
                subject_name=rs.subject_name,
                subject_code=rs.subject_code,
                importance=rs.importance,
                importance_label=rs.importance_label,
                min_score=rs.min_score,
                weight=rs.weight,
                linked_goals=[req_map.target_name],
                goal_types=[goal_type],
            )
            for rs in req_map.required_subjects
        ]

    @staticmethod
    def _suggestions(m: MatchedSubject) -> List[str]:
        """Generate improvement suggestions for a subject."""
        s = []
        if m.severity == "critical":
            s += [
                f"Seek immediate tutoring for {m.subject_name}",
                "Schedule daily 2-hour study sessions",
                "Meet with subject professor"
            ]
        elif m.severity == "high":
            s += [
                f"Dedicate extra time to {m.subject_name} weekly",
                "Practice with previous-year papers"
            ]
        elif m.severity == "medium":
            s += [
                f"Regular revision of {m.subject_name}",
                "Solve additional practice problems"
            ]
        else:
            s += [f"Maintain current effort in {m.subject_name}"]
        if not m.is_taken:
            s.insert(0, f"Enrol in or study {m.subject_name} as soon as possible")
        return s

    @staticmethod
    def _resources(subject: str) -> List[Dict[str, Any]]:
        """Generate resource links for a subject."""
        q = subject.replace(" ", "+")
        return [
            {
                "type": "course",
                "platform": "Coursera",
                "title": f"{subject} Fundamentals",
                "url": f"https://coursera.org/search?query={q}"
            },
            {
                "type": "video",
                "platform": "YouTube",
                "title": f"Learn {subject}",
                "url": f"https://youtube.com/results?search_query={q}+tutorial"
            },
            {
                "type": "practice",
                "platform": "GeeksforGeeks",
                "title": f"{subject} Practice",
                "url": f"https://geeksforgeeks.org/search?q={q}"
            },
        ]

    @staticmethod
    def _est_hours(gap: float, importance: float) -> int:
        """Estimate hours needed to close a gap."""
        return max(5, int(gap * 0.4 * (1 + importance)))

    @staticmethod
    def _estimate_preparation_time(weaknesses: List[WeaknessEntry]) -> str:
        """Estimate total preparation time."""
        if not weaknesses:
            return "0 weeks"
        total = sum(w.estimated_hours for w in weaknesses)
        if total < 20:
            return "1–2 weeks"
        elif total < 50:
            return "3–4 weeks"
        elif total < 100:
            return "6–8 weeks"
        return "2–3 months"

    @staticmethod
    def _elective_rec_text(score: float, weak: List[str]) -> str:
        """Generate elective recommendation text."""
        if score >= 80:
            return "You are well prepared for this elective."
        if score >= 65:
            return f"Mostly ready. Strengthen {', '.join(weak[:2])} to excel."
        if score >= 45:
            return "Significant preparation needed before enrolling."
        return "Not recommended at this time. Build prerequisites first."

    @staticmethod
    def _honours_rec_text(score: float, eligible: bool) -> str:
        """Generate honours recommendation text."""
        if not eligible:
            return "CGPA below the minimum requirement. Raise CGPA first."
        if score >= 75:
            return "Strong candidate. You may proceed."
        if score >= 55:
            return "Eligible but weak in some areas. Improve before committing."
        return "Eligibility met but academic readiness is low. Delay recommended."

    @staticmethod
    def _honours_steps(matched, eligible, min_cgpa, cgpa) -> List[str]:
        """Generate detailed steps for honours preparation."""
        steps = []
        if not eligible:
            steps.append(f"Raise CGPA from {cgpa:.2f} to at least {min_cgpa:.1f}")
        for m in matched:
            if m.is_weakness:
                if not m.is_taken:
                    steps.append(f"Complete the subject: {m.subject_name}")
                else:
                    steps.append(
                        f"Improve {m.subject_name} from {m.student_score:.0f}% to ≥{m.min_score:.0f}%"
                    )
        return steps or ["All requirements met — proceed with the application."]

    # ════════════════════════════════════════════════════════════════
    #  PERSIST RESULT
    # ════════════════════════════════════════════════════════════════

    async def _save_result(
        self, resp: ReadinessResponse,
        interests: List[str], electives: List[str], honours: List[str],
    ) -> None:
        """Save the readiness result to the database."""
        try:
            # Mark previous results as not current
            await ReadinessResult.find(
                {"student_id": resp.student_id, "is_current": True}
            ).update({"$set": {"is_current": False}})

            doc = ReadinessResult(
                student_id=resp.student_id,
                overall_readiness_score=resp.overall_readiness_score,
                readiness_level=resp.readiness_level,
                recommendation_type=resp.recommendation_type,
                primary_recommendation=resp.primary_recommendation,
                interest_readiness=resp.interest_readiness,
                elective_readiness=resp.elective_readiness,
                honours_readiness=resp.honours_readiness,
                interest_breakdown=resp.interest_breakdown,
                elective_breakdown=resp.elective_breakdown,
                honours_breakdown=resp.honours_breakdown,
                weaknesses=resp.weaknesses,
                study_plan=resp.study_plan,
                has_critical_weakness=resp.has_critical_weakness,
                has_blockers=resp.has_blockers,
                is_first_semester=resp.is_first_semester,
                subjects_to_focus=resp.subjects_to_focus,
                estimated_preparation_time=resp.estimated_preparation_time,
                detailed_recommendations=resp.detailed_recommendations,
                interests_analyzed=interests,
                electives_analyzed=electives,
                honours_analyzed=honours,
            )
            await doc.insert()
        except Exception as e:
            logger.error(f"Failed to persist readiness result: {e}")


# ── Singleton ──────────────────────────────────────────────────

_instance: Optional[ReadinessService] = None


def get_readiness_service() -> ReadinessService:
    global _instance
    if _instance is None:
        _instance = ReadinessService()
    return _instance