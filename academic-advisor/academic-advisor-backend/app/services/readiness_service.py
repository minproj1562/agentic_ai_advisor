# app/services/readiness_service.py
"""
Academic Readiness Engine — Corrected 8-Step Pipeline
Uses actual field names confirmed from student_profile.py:
  SubjectScore.total_marks, SubjectScore.credits,
  SubjectScore.subject_name, SubjectScore.subject_code
  SemesterRecord.subjects, StudentProfile.semester_records
  StudentProfile.current_semester, StudentProfile.cgpa
"""

import re
import logging
import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.models.readiness import (
    SubjectRequirementMap,
    RequiredSubject,
    ReadinessResult,
    MatchedSubject,
    WeaknessEntry,
    ReadinessResponse,
    ReadinessSummaryResponse,
    ElectiveReadinessResponse,
    HonoursReadinessResponse,
    PrerequisiteDetail,
    EffortReadinessResult,
)
from app.models.student_profile import StudentProfile
from app.models.weakness import StudentInterestProfile
from app.models.recommendation import RecommendationRecord
from app.services.effort_calculator import get_effort_calculator
from app.core.readiness_config import (
    PASSING_SCORE,
    MAX_SCORE_RATIO,
    READINESS_LEVELS,
    GAP_SEVERITY_CRITICAL,
    GAP_SEVERITY_HIGH,
    GAP_SEVERITY_MEDIUM,
    IMPORTANCE_ESCALATE_THRESHOLD,
    IMPORTANCE_DEESCALATE_THRESHOLD,
    HOURS_PER_MARK_PER_CREDIT,
    BACKLOG_HOURS_MULTIPLIER,
    MAX_HOURS_PER_CREDIT,
    MIN_HOURS_PER_CREDIT,
    EXTRA_STUDY_LIGHT_LOAD,
    EXTRA_STUDY_NORMAL_LOAD,
    EXTRA_STUDY_HEAVY_LOAD,
    LIGHT_LOAD_THRESHOLD,
    HEAVY_LOAD_THRESHOLD,
    MIN_PLAN_WEEKS,
    MAX_PLAN_WEEKS,
    SEMESTER_MULTIPLIERS,
    LOW_CONFIDENCE_THRESHOLD,
)

logger = logging.getLogger(__name__)


class ReadinessService:
    _seeded: bool = False

    # ════════════════════════════════════════════════════════════
    #  AUTO-SEED
    # ════════════════════════════════════════════════════════════

    async def _ensure_seeded(self) -> None:
        if ReadinessService._seeded:
            return
        count = await SubjectRequirementMap.count()
        if count == 0:
            logger.info("SubjectRequirementMap empty — seeding …")
            await self._seed_default_maps()
        ReadinessService._seeded = True

    async def _seed_default_maps(self) -> None:
        from app.services._seed_readiness_data import build_seed_documents
        docs = build_seed_documents()
        for doc in docs:
            await doc.insert()
        logger.info(f"Seeded {len(docs)} requirement maps")

    # ════════════════════════════════════════════════════════════
    #  MAIN PIPELINE
    # ════════════════════════════════════════════════════════════

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

        # Step 1: Build target profile from requirement maps
        target_profile = await self._build_target_profile(
            interests, electives, honours
        )

        # Step 2: Load student data
        # Uses confirmed field names from student_profile.py:
        #   SubjectScore.total_marks, SubjectScore.credits
        student_data = await self._load_student_scores(student_id)
        is_first_sem = student_data["is_first_semester"]
        semester = student_data.get("semester", 1)

        # Steps 2–4: Match → Weaknesses → Severity
        matched = self._match_performance(target_profile, student_data)
        matched = self._identify_weaknesses(matched, is_first_sem)
        matched = self._assign_severity(matched)

        # Step 5a: Academic readiness (marks vs requirements)
        academic_readiness, cat_scores, breakdowns = (
            self._calculate_readiness_scores(
                matched, is_first_sem, interests, electives, honours
            )
        )

        # Step 5b: Effort readiness (coverage ratio from credits+marks)
        effort_calc = get_effort_calculator()
        required_for_effort = [
            {
                "subject_name": m.subject_name,
                "subject_code": m.subject_code,
                "min_score": m.min_score,
                "importance": m.importance,
            }
            for m in matched
        ]

        effort_result: EffortReadinessResult = effort_calc.compute(
            subject_scores=student_data["subjects"],
            required_subjects=required_for_effort,
            semester=semester,
            is_first_semester=is_first_sem,
        )

        # Step 5c: Blend academic + effort
        overall = effort_calc.blend_scores(
            academic_readiness=academic_readiness,
            effort_readiness=effort_result.effort_readiness_score,
            is_first_semester=is_first_sem,
        )

        # Steps 6–7: Prioritise weaknesses + generate study plan
        weakness_entries = self._prioritise_weaknesses(matched, semester)
        total_gap_hours = round(
            sum(w.estimated_hours for w in weakness_entries), 1
        )
        study_plan = self._generate_study_plan(
            weakness_entries, overall, student_data, semester
        )

        # Step 8: Safe recommendation
        level, rec_type, primary_rec, detail_recs = (
            self._generate_recommendation(
                overall, weakness_entries, is_first_sem
            )
        )

        has_critical = any(
            w.severity == "critical" for w in weakness_entries
        )
        has_blockers = has_critical or overall < 30
        focus_subjects = [w.subject for w in weakness_entries[:5]]
        prep_time = self._estimate_preparation_time(total_gap_hours)

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
            effort_readiness_score=round(
                effort_result.effort_readiness_score, 1
            ),
            total_gap_hours=total_gap_hours,
            study_load_warning=effort_result.study_load_warning,
            effort_detail=effort_result.dict(),
            analysis_timestamp=datetime.utcnow().isoformat(),
        )

        await self._save_result(resp, interests, electives, honours)
        return resp

    # ════════════════════════════════════════════════════════════
    #  SINGLE-TARGET HELPERS
    # ════════════════════════════════════════════════════════════

    async def check_elective_readiness(
        self, student_id: str, elective_code: str
    ) -> ElectiveReadinessResponse:
        await self._ensure_seeded()
        req_map = await self._find_map("elective", elective_code)

        if not req_map:
            return ElectiveReadinessResponse(
                student_id=student_id,
                elective=elective_code,
                recommendation=(
                    f"No requirement map found for '{elective_code}'. "
                    "Try the full elective name or ask faculty to add it."
                ),
            )

        student = await self._load_student_scores(student_id)
        is_first = student["is_first_semester"]
        semester = student.get("semester", 1)

        matched = self._match_performance(
            self._convert_map_to_target(req_map, "elective"), student
        )
        matched = self._identify_weaknesses(matched, is_first)
        matched = self._assign_severity(matched)
        score = self._readiness_from_matched(matched, is_first)

        prerequisites: List[PrerequisiteDetail] = []
        strengths: List[str] = []
        gaps: List[str] = []
        prep_plan: List[str] = []

        for m in matched:
            current = (
                m.student_score if m.student_score is not None else 0.0
            )
            coverage = (
                min(current / m.min_score, 1.0)
                if m.min_score > 0
                else 0.0
            )

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
                    f"Revise {m.subject_name} — close "
                    f"{gap_val:.0f}-mark gap "
                    f"({m.importance_label} priority)"
                )
            else:
                status = "missing"
                gaps.append(
                    f"{m.subject_name}: not yet taken/recorded"
                )
                if not is_first:
                    prep_plan.append(
                        f"{m.subject_name} not found in your records "
                        "— ensure marks are uploaded"
                    )

            prerequisites.append(PrerequisiteDetail(
                subject_name=m.subject_name,
                subject_code=m.subject_code,
                current_score=round(current, 1),
                required_score=m.min_score,
                gap=round(max(0.0, m.min_score - current), 1),
                coverage_ratio=round(coverage, 3),
                importance=m.importance,
                importance_label=m.importance_label,
                status=status,
                is_taken=m.is_taken,
                confidence=m.confidence,
                low_confidence_flag=m.low_confidence_flag,
            ))

        if score >= 80:
            level, weeks = "ready", 0
            rec = (
                f"You are well-prepared for {req_map.target_name}!"
            )
        elif score >= 65:
            level, weeks = "mostly_ready", 2
            rec = (
                f"Mostly ready for {req_map.target_name}. "
                f"Minor revision in {len(gaps)} area(s) recommended."
            )
        elif score >= 40:
            level, weeks = "needs_work", 6
            rec = (
                f"You can consider {req_map.target_name} but "
                "significant preparation is needed first."
            )
        else:
            level, weeks = "not_ready", 10
            rec = (
                f"Prerequisites for {req_map.target_name} need "
                "substantial work. Strengthen fundamentals first."
            )

        if is_first:
            rec += (
                " (First-semester: untaken subjects are excluded "
                "from scoring as expected.)"
            )

        weak_subj = [m.subject_name for m in matched if m.is_weakness]
        total_hours = sum(
            self._est_hours(
                m.gap,
                m.credits,
                (
                    m.student_score is not None
                    and m.student_score < PASSING_SCORE
                ),
                semester,
            )
            for m in matched
            if m.is_weakness
        )
        prep_time = self._estimate_preparation_time(total_hours)

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
                recommendation=f"No map found for '{programme}'.",
            )

        student = await self._load_student_scores(student_id)
        cgpa = student.get("cgpa", 0.0)
        min_cgpa = req_map.min_cgpa or 0.0
        semester = student.get("semester", 1)

        matched = self._match_performance(
            self._convert_map_to_target(req_map, "honours"), student
        )
        matched = self._identify_weaknesses(
            matched, student["is_first_semester"]
        )
        matched = self._assign_severity(matched)

        score = self._readiness_from_matched(
            matched, student["is_first_semester"]
        )
        is_eligible = cgpa >= min_cgpa

        blockers: List[str] = []
        if not is_eligible:
            blockers.append(
                f"CGPA {cgpa:.2f} is below required {min_cgpa:.1f}"
            )
        for m in matched:
            if m.severity == "critical":
                blockers.append(
                    f"{m.subject_name} score is critically low"
                )

        total_hours = sum(
            self._est_hours(
                m.gap,
                m.credits,
                (
                    m.student_score is not None
                    and m.student_score < PASSING_SCORE
                ),
                semester,
            )
            for m in matched
            if m.is_weakness
        )

        return HonoursReadinessResponse(
            student_id=student_id,
            programme=req_map.target_name,
            readiness_score=round(score, 1),
            is_eligible=is_eligible and score >= 60,
            recommendation=self._honours_rec_text(score, is_eligible),
            blockers=blockers,
            preparation_time=self._estimate_preparation_time(total_hours),
            detailed_steps=self._honours_steps(
                matched, is_eligible, min_cgpa, cgpa
            ),
        )

    async def get_summary(
        self, student_id: str
    ) -> ReadinessSummaryResponse:
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
        timestamp_str = (
            ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
        )

        return ReadinessSummaryResponse(
            student_id=student_id,
            overall_readiness=latest.overall_readiness_score,
            level=latest.readiness_level,
            can_proceed=latest.recommendation_type in (
                "proceed", "proceed_with_caution"
            ),
            critical_issues=latest.has_critical_weakness,
            primary_action=latest.primary_recommendation,
            timestamp=timestamp_str,
        )

    # ════════════════════════════════════════════════════════════
    #  STEP 1 — BUILD TARGET PROFILE
    # ════════════════════════════════════════════════════════════

    async def _build_target_profile(
        self,
        interests: List[str],
        electives: List[str],
        honours: List[str],
    ) -> List[MatchedSubject]:
        """
        Merge requirements from all goals into a deduplicated list.
        When the same subject appears in multiple goals:
          - importance: keep the highest
          - min_score: keep the highest
          - weight: keep the highest
          - linked_goals: append
          - goal_types: append
        """
        merged: Dict[str, MatchedSubject] = {}

        async def _merge(goal_type: str, names: List[str]) -> None:
            for name in names:
                req_map = await self._find_map(goal_type, name)
                if not req_map:
                    logger.warning(
                        f"No requirement map for {goal_type}='{name}'"
                    )
                    continue
                for rs in req_map.required_subjects:
                    key = rs.subject_name.lower()
                    if key in merged:
                        ex = merged[key]
                        if rs.importance > ex.importance:
                            ex.importance = rs.importance
                            ex.importance_label = rs.importance_label
                        ex.min_score = max(ex.min_score, rs.min_score)
                        ex.weight = max(ex.weight, rs.weight)
                        if name not in ex.linked_goals:
                            ex.linked_goals.append(name)
                        if goal_type not in ex.goal_types:
                            ex.goal_types.append(goal_type)
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
        result = await SubjectRequirementMap.find_one(
            {
                "target_type": target_type,
                "target_name": name,
                "is_active": True,
            }
        )
        if result:
            return result

        regex = re.compile(f"^{re.escape(name)}$", re.IGNORECASE)
        result = await SubjectRequirementMap.find_one(
            {
                "target_type": target_type,
                "target_name": {"$regex": regex},
                "is_active": True,
            }
        )
        if result:
            return result

        result = await SubjectRequirementMap.find_one(
            {
                "target_type": target_type,
                "target_aliases": {"$regex": regex},
                "is_active": True,
            }
        )
        return result

    # ════════════════════════════════════════════════════════════
    #  STEP 2 — LOAD STUDENT DATA
    # ════════════════════════════════════════════════════════════

    async def _load_student_scores(
        self, student_id: str
    ) -> Dict[str, Any]:
        """
        Load student subject scores from StudentProfile.

        Confirmed field names from student_profile.py:
          StudentProfile.semester_records    → List[SemesterRecord]
          SemesterRecord.subjects            → List[SubjectScore]
          SubjectScore.subject_name          → str
          SubjectScore.subject_code          → str
          SubjectScore.total_marks           → float  (0–100)
          SubjectScore.credits               → int
          SubjectScore.grade                 → str
          StudentProfile.current_semester    → int
          StudentProfile.cgpa                → float
        """
        profile = await StudentProfile.find_one({"user_id": student_id})

        if not profile:
            logger.warning(f"No StudentProfile for user_id={student_id}")
            return {
                "subjects": {},
                "cgpa": 0.0,
                "semester": 1,
                "is_first_semester": True,
            }

        subjects: Dict[str, Dict[str, Any]] = {}

        for sem in profile.semester_records:
            for subj in sem.subjects:
                # total_marks is confirmed present on SubjectScore
                score = subj.total_marks

                # Normalise if somehow stored out of range
                # (should not happen with proper AcademicDataEntry)
                if score > 100:
                    logger.warning(
                        f"Score > 100 for {subj.subject_name}: "
                        f"{score} — normalising"
                    )
                    score = min(score, 100.0)

                # credits confirmed present on SubjectScore, default 3
                credits = int(subj.credits) if subj.credits else 3

                existing = subjects.get(subj.subject_name)
                if not existing or score > existing["score"]:
                    subjects[subj.subject_name] = {
                        "score": round(score, 1),
                        "credits": credits,
                        "code": subj.subject_code,
                        "grade": subj.grade,
                    }

        completed_semesters = len(profile.semester_records)

        return {
            "subjects": subjects,
            "cgpa": profile.cgpa,
            "semester": profile.current_semester,
            "is_first_semester": completed_semesters <= 1,
        }

    # ════════════════════════════════════════════════════════════
    #  STEP 2 — MATCH PERFORMANCE
    # ════════════════════════════════════════════════════════════

    def _match_performance(
        self,
        target_profile: List[MatchedSubject],
        student_data: Dict[str, Any],
    ) -> List[MatchedSubject]:
        """
        Match each required subject against student's actual scores.
        Sets: student_score, is_taken, confidence, credits,
              low_confidence_flag.
        """
        subjects = student_data["subjects"]
        is_first = student_data["is_first_semester"]

        for entry in target_profile:
            score, confidence, credits = self._find_score_and_credits(
                subjects, entry
            )
            if score is not None:
                entry.student_score = score
                entry.is_taken = True
                entry.confidence = confidence
                entry.credits = credits
                entry.low_confidence_flag = (
                    confidence < LOW_CONFIDENCE_THRESHOLD
                )
            else:
                entry.student_score = None
                entry.is_taken = False
                entry.confidence = 0.4 if is_first else 0.6
                entry.credits = 3
                entry.low_confidence_flag = True

        return target_profile

    def _find_score_and_credits(
        self,
        subjects: Dict[str, Dict[str, Any]],
        entry: MatchedSubject,
    ) -> Tuple[Optional[float], float, int]:
        """
        Find score, confidence, and credits for a required subject.

        Returns: (score, confidence, credits)
          score      → None if not found
          confidence → 1.0 exact, 0.9 substring, 0.8 word-overlap
          credits    → from student record or default 3
        """
        target = entry.subject_name.lower().strip()
        target_words = set(target.split())

        # Pass 1: exact name
        for name, data in subjects.items():
            if name.lower().strip() == target:
                return (
                    data["score"],
                    1.0,
                    int(data.get("credits", 3) or 3),
                )

        # Pass 2: subject code
        if entry.subject_code:
            for name, data in subjects.items():
                stored_code = (data.get("code") or "").strip().upper()
                if stored_code and stored_code == entry.subject_code.upper():
                    return (
                        data["score"],
                        1.0,
                        int(data.get("credits", 3) or 3),
                    )

        # Pass 3: substring
        for name, data in subjects.items():
            nl = name.lower().strip()
            if target in nl or nl in target:
                return (
                    data["score"],
                    0.9,
                    int(data.get("credits", 3) or 3),
                )

        # Pass 4: word overlap
        for name, data in subjects.items():
            nw = set(name.lower().split())
            common = target_words & nw
            if len(common) >= 2 or (
                len(common) >= 1 and len(target_words) == 1
            ):
                return (
                    data["score"],
                    0.8,
                    int(data.get("credits", 3) or 3),
                )

        return None, 0.0, 3

    # ════════════════════════════════════════════════════════════
    #  STEP 3 — IDENTIFY WEAKNESSES
    # ════════════════════════════════════════════════════════════

    def _identify_weaknesses(
        self,
        matched: List[MatchedSubject],
        is_first_semester: bool,
    ) -> List[MatchedSubject]:
        """
        Determine weakness status and compute gap for each subject.

        Rules:
          Taken AND score < min_score      → weakness, gap = difference
          Taken AND score >= min_score     → not a weakness, gap = 0
          Not taken, first semester        → NOT a weakness
                                             (student hasn't had chance)
          Not taken, later semester        → weakness, gap = full min_score
        """
        for m in matched:
            if m.is_taken and m.student_score is not None:
                if m.student_score < m.min_score:
                    m.gap = round(m.min_score - m.student_score, 1)
                    m.is_weakness = True
                else:
                    m.gap = 0.0
                    m.is_weakness = False
            elif not m.is_taken and is_first_semester:
                m.gap = 0.0
                m.is_weakness = False
            else:
                # Not taken in later semesters
                m.gap = m.min_score
                m.is_weakness = True

        return matched

    # ════════════════════════════════════════════════════════════
    #  STEP 4 — ASSIGN SEVERITY
    # ════════════════════════════════════════════════════════════

    def _assign_severity(
        self, matched: List[MatchedSubject]
    ) -> List[MatchedSubject]:
        """
        Assign severity based on gap size + importance adjustment.
        Confidence affects low_confidence_flag only, NOT severity.

        Algorithm:
          1. Classify gap into base severity (critical/high/medium/low)
          2. If importance >= 0.8: escalate one level
          3. If importance <= 0.3: de-escalate one level
          4. Set low_confidence_flag separately
        """
        severity_order = ["low", "medium", "high", "critical"]

        for m in matched:
            if not m.is_weakness:
                m.severity = "none"
                continue

            # Step 1: base severity from gap size
            if m.gap >= GAP_SEVERITY_CRITICAL:
                base = "critical"
            elif m.gap >= GAP_SEVERITY_HIGH:
                base = "high"
            elif m.gap >= GAP_SEVERITY_MEDIUM:
                base = "medium"
            else:
                base = "low"

            # Step 2: importance adjustment
            idx = severity_order.index(base)

            if m.importance >= IMPORTANCE_ESCALATE_THRESHOLD:
                idx = min(idx + 1, len(severity_order) - 1)
            elif m.importance <= IMPORTANCE_DEESCALATE_THRESHOLD:
                idx = max(idx - 1, 0)

            m.severity = severity_order[idx]

        return matched

    # ════════════════════════════════════════════════════════════
    #  STEP 5a — ACADEMIC READINESS
    # ════════════════════════════════════════════════════════════

    def _calculate_readiness_scores(
        self,
        matched: List[MatchedSubject],
        is_first_sem: bool,
        interests: List[str],
        electives: List[str],
        honours: List[str],
    ) -> Tuple[float, Dict[str, float], Dict[str, Dict[str, float]]]:
        overall = self._readiness_from_matched(matched, is_first_sem)

        cat_scores: Dict[str, float] = {}
        breakdowns: Dict[str, Dict[str, float]] = {
            "interest": {},
            "elective": {},
            "honours": {},
        }

        for cat, names in [
            ("interest", interests),
            ("elective", electives),
            ("honours", honours),
        ]:
            entries = [m for m in matched if cat in m.goal_types]
            cat_scores[cat] = (
                self._readiness_from_matched(entries, is_first_sem)
                if entries
                else 0.0
            )
            for name in names:
                name_entries = [
                    m for m in matched if name in m.linked_goals
                ]
                if name_entries:
                    breakdowns[cat][name] = round(
                        self._readiness_from_matched(
                            name_entries, is_first_sem
                        ),
                        1,
                    )

        return overall, cat_scores, breakdowns

    def _readiness_from_matched(
        self,
        entries: List[MatchedSubject],
        is_first_sem: bool,
    ) -> float:
        """
        Academic readiness: importance-and-weight-weighted coverage.

        Formula (per subject):
          score_ratio = min(student_score / min_score, MAX_SCORE_RATIO)
                      = min(score/min, 1.0)
                        ← capped at 1.0 (no bonus for exceeding minimum)

          weighted_contribution = score_ratio × importance × weight
          denominator           = importance × weight

        For NOT TAKEN subjects:
          first semester → EXCLUDE (student hasn't had opportunity)
          later semester → score_ratio = 0.0 (full penalty)

        overall = Σ(contribution) / Σ(denominator) × 100
        Result clamped to [0, 100].
        """
        if not entries:
            return 0.0

        numerator = 0.0
        denominator = 0.0

        for m in entries:
            if not m.is_taken and is_first_sem:
                # Exclude first-semester untaken subjects
                continue

            w = m.importance * m.weight
            denominator += w

            if (
                m.is_taken
                and m.student_score is not None
                and m.min_score > 0
            ):
                ratio = min(
                    m.student_score / m.min_score, MAX_SCORE_RATIO
                )
            else:
                ratio = 0.0

            numerator += ratio * w

        if denominator == 0:
            # All excluded (pure first-semester case) → no data, return 100
            return 100.0

        raw = (numerator / denominator) * 100.0
        return round(max(0.0, min(100.0, raw)), 1)

    # ════════════════════════════════════════════════════════════
    #  STEP 6 — PRIORITISE WEAKNESSES
    # ════════════════════════════════════════════════════════════

    def _prioritise_weaknesses(
        self,
        matched: List[MatchedSubject],
        semester: int,
    ) -> List[WeaknessEntry]:
        """
        Filter, sort, and build WeaknessEntry objects.

        Sort order (most critical first):
          1. Severity (critical > high > medium > low)
          2. Importance (higher first)
          3. Number of linked goals (higher = more impact)
          4. Gap size (larger first)
        """
        weak = [m for m in matched if m.is_weakness]

        sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        weak.sort(key=lambda m: (
            sev_order.get(m.severity, 4),
            -m.importance,
            -len(m.linked_goals),
            -m.gap,
        ))

        entries: List[WeaknessEntry] = []
        for rank, m in enumerate(weak, 1):
            credits = m.credits or 3
            is_backlog = (
                m.student_score is not None
                and m.student_score < PASSING_SCORE
            )
            hours = self._est_hours(
                gap=m.gap,
                credits=credits,
                is_backlog=is_backlog,
                semester=semester,
            )

            entries.append(WeaknessEntry(
                subject=m.subject_name,
                current_score=m.student_score or 0.0,
                target_score=m.min_score,
                gap=round(m.gap, 1),
                severity=m.severity,
                importance=m.importance,
                importance_label=m.importance_label,
                confidence=m.confidence,
                low_confidence_flag=m.low_confidence_flag,
                credits=credits,
                linked_goals=m.linked_goals,
                goal_types=m.goal_types,
                suggestions=self._suggestions(m),
                resources=self._resources(m.subject_name),
                estimated_hours=round(hours, 1),
                priority_rank=rank,
            ))

        return entries

    # ════════════════════════════════════════════════════════════
    #  STEP 7 — STUDY PLAN
    # ════════════════════════════════════════════════════════════

    def _generate_study_plan(
        self,
        weaknesses: List[WeaknessEntry],
        readiness: float,
        student_data: Dict[str, Any],
        semester: int,
    ) -> Dict[str, Any]:
        """
        Generate a structured, credit-aware study plan.

        Duration formula:
          total_credits = Σ(credits from student profile)
          extra_budget/week:
            credits < 15  → 20 hrs/week
            credits 15–20 → 15 hrs/week
            credits > 20  → 10 hrs/week
          duration_weeks = clamp(⌈total_gap_hours / budget⌉, 2, 16)
          weekly_commitment = total_gap_hours / duration_weeks

          Consistency check: if weekly_commitment > budget + 2,
          extend duration_weeks by 1 to keep plan achievable.
        """
        if not weaknesses:
            return {
                "duration_weeks": 0,
                "weekly_hours": 0,
                "message": "No weaknesses detected — no study plan needed.",
            }

        subjects = student_data.get("subjects", {})
        total_credits = sum(
            int(d.get("credits", 3) or 3)
            for d in subjects.values()
        )
        if total_credits == 0:
            total_credits = 18

        if total_credits < LIGHT_LOAD_THRESHOLD:
            extra_budget = EXTRA_STUDY_LIGHT_LOAD
        elif total_credits > HEAVY_LOAD_THRESHOLD:
            extra_budget = EXTRA_STUDY_HEAVY_LOAD
        else:
            extra_budget = EXTRA_STUDY_NORMAL_LOAD

        top_weaknesses = weaknesses[:6]
        total_gap_hours = sum(w.estimated_hours for w in top_weaknesses)

        raw_weeks = (
            math.ceil(total_gap_hours / extra_budget)
            if extra_budget > 0
            else MAX_PLAN_WEEKS
        )
        duration_weeks = max(
            MIN_PLAN_WEEKS, min(MAX_PLAN_WEEKS, raw_weeks)
        )

        weekly_commitment = (
            total_gap_hours / duration_weeks
            if duration_weeks > 0
            else 0.0
        )

        # Consistency check
        if weekly_commitment > extra_budget + 2:
            duration_weeks = min(MAX_PLAN_WEEKS, duration_weeks + 1)
            weekly_commitment = total_gap_hours / duration_weeks

        focus_areas = [
            {
                "subject": w.subject,
                "priority": w.priority_rank,
                "current_score": w.current_score,
                "target_score": w.target_score,
                "total_hours": w.estimated_hours,
                "weekly_hours": round(
                    w.estimated_hours / duration_weeks, 1
                ),
                "severity": w.severity,
                "credits": w.credits,
            }
            for w in top_weaknesses
        ]

        critical_high = [
            w.subject
            for w in weaknesses
            if w.severity in ("critical", "high")
        ][:3]

        mid_week = max(3, duration_weeks // 2)

        phases = [
            {
                "name": "Foundation Building",
                "weeks": "1–2",
                "focus": critical_high or [weaknesses[0].subject],
                "goals": [
                    "Review lecture notes and fundamentals",
                    "Complete basic practice exercises",
                ],
            },
            {
                "name": "Active Practice",
                "weeks": f"3–{max(3, duration_weeks - 2)}",
                "focus": [w.subject for w in weaknesses[:4]],
                "goals": [
                    "Solve past exam questions",
                    "Timed topic quizzes",
                ],
            },
            {
                "name": "Mastery & Revision",
                "weeks": f"{max(2, duration_weeks - 1)}–{duration_weeks}",
                "focus": [w.subject for w in weaknesses[:5]],
                "goals": [
                    "Full mock tests",
                    "Verify target scores achieved",
                ],
            },
        ]

        milestones = [
            {"week": 2, "target": "Complete fundamentals review"},
            {
                "week": mid_week,
                "target": "Score ≥60% in practice tests",
            },
            {
                "week": max(2, duration_weeks - 1),
                "target": "Score ≥70% in practice tests",
            },
            {
                "week": duration_weeks,
                "target": "Achieve target proficiency",
            },
        ]

        return {
            "duration_weeks": duration_weeks,
            "weekly_hours": round(weekly_commitment, 1),
            "weekly_commitment": f"{weekly_commitment:.1f} hours / week",
            "total_gap_hours": round(total_gap_hours, 1),
            "extra_budget_per_week": extra_budget,
            "focus_areas": focus_areas,
            "phases": phases,
            "milestones": milestones,
            "current_readiness": round(readiness, 1),
            "target_readiness": 80,
            "total_credits_registered": total_credits,
            "recommendation": (
                "Follow this plan to raise readiness above 80%."
            ),
        }

    # ════════════════════════════════════════════════════════════
    #  STEP 8 — RECOMMENDATION
    # ════════════════════════════════════════════════════════════

    def _generate_recommendation(
        self,
        readiness: float,
        weaknesses: List[WeaknessEntry],
        is_first_sem: bool,
    ) -> Tuple[str, str, str, List[str]]:
        critical = [w for w in weaknesses if w.severity == "critical"]
        high = [w for w in weaknesses if w.severity == "high"]

        if readiness >= READINESS_LEVELS["excellent"]:
            level = "excellent"
        elif readiness >= READINESS_LEVELS["good"]:
            level = "good"
        elif readiness >= READINESS_LEVELS["moderate"]:
            level = "moderate"
        elif readiness >= READINESS_LEVELS["low"]:
            level = "low"
        else:
            level = "not_ready"

        if readiness >= 75 and not critical:
            rec_type = "proceed"
        elif readiness >= 60 and not critical:
            rec_type = "proceed_with_caution"
        elif readiness >= 35 or (critical and readiness >= 40):
            rec_type = "improve_first"
        else:
            rec_type = "do_not_proceed"

        texts = {
            "proceed": (
                "You are academically prepared. Proceed with confidence."
            ),
            "proceed_with_caution": (
                "You meet most requirements. Proceed but improve "
                "weak areas in parallel."
            ),
            "improve_first": (
                "Significant gaps detected. Improve the listed subjects "
                "before committing to these choices."
            ),
            "do_not_proceed": (
                "Foundational gaps exist. Strengthen these areas before "
                "selecting advanced electives or honours."
            ),
        }
        primary = texts[rec_type]

        detail: List[str] = []
        if critical:
            detail.append(
                f"Critical: Improve "
                f"{', '.join(w.subject for w in critical[:3])} "
                "immediately."
            )
        if high:
            detail.append(
                f"High priority: Strengthen "
                f"{', '.join(w.subject for w in high[:3])}."
            )
        if is_first_sem:
            detail.append(
                "As a first-semester student, not all subjects "
                "have been taken yet — this is expected and accounted for."
            )
        if rec_type in ("improve_first", "do_not_proceed"):
            detail.append(
                "Consider delaying elective or honours selection "
                "until flagged subjects are improved."
            )
        if rec_type == "proceed":
            detail.append("Your profile aligns well — good to go!")

        return level, rec_type, primary, detail

    # ════════════════════════════════════════════════════════════
    #  RESOLVE GOALS FROM DATABASE
    # ════════════════════════════════════════════════════════════

    async def _resolve_goals(
        self,
        student_id: str,
        interests: Optional[List[str]],
        electives: Optional[List[str]],
        honours: Optional[List[str]],
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Resolve goals from request params or pull from database.

        Priority:
          1. Use explicitly passed params if all three provided
          2. Fill gaps from StudentInterestProfile
             (confirmed field names: interests, preferred_electives,
              honours_minors_interest)
          3. Fill interests from StudentProfile.interests
          4. Fill electives from RecommendationRecord.electives
        """
        if interests is not None and electives is not None \
                and honours is not None:
            return interests, electives, honours

        try:
            ip = await StudentInterestProfile.find_one(
                {"user_id": student_id}
            )
            if ip:
                # Field names confirmed from weakness.py
                if interests is None:
                    interests = ip.interests or []
                if honours is None:
                    honours = ip.honours_minors_interest or []
                if electives is None:
                    electives = ip.preferred_electives or []
        except Exception as e:
            logger.warning(f"StudentInterestProfile fetch failed: {e}")

        if not interests:
            try:
                sp = await StudentProfile.find_one(
                    {"user_id": student_id}
                )
                if sp:
                    interests = sp.interests or []
            except Exception as e:
                logger.warning(f"StudentProfile interests fetch failed: {e}")

        if not electives:
            try:
                rec = await RecommendationRecord.find_one(
                    {"student_id": student_id, "is_active": True}
                )
                if rec and rec.electives:
                    # ElectiveDetail.elective_name confirmed from recommendation.py
                    electives = [
                        e.elective_name for e in rec.electives[:4]
                    ]
            except Exception as e:
                logger.warning(
                    f"RecommendationRecord fetch failed: {e}"
                )

        return interests or [], electives or [], honours or []

    # ════════════════════════════════════════════════════════════
    #  STATIC HELPERS
    # ════════════════════════════════════════════════════════════

    @staticmethod
    def _convert_map_to_target(
        req_map: SubjectRequirementMap, goal_type: str
    ) -> List[MatchedSubject]:
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
    def _est_hours(
        gap: float,
        credits: int,
        is_backlog: bool,
        semester: int,
    ) -> float:
        """
        Estimate total hours to close a score gap.

        Formula: gap × credits × 0.1 × multipliers
        Bounds:  [credits × 1, credits × 20]
        """
        if gap <= 0:
            return 0.0

        base = gap * credits * HOURS_PER_MARK_PER_CREDIT
        multiplier = 1.0
        if is_backlog:
            multiplier *= BACKLOG_HOURS_MULTIPLIER
        multiplier *= SEMESTER_MULTIPLIERS.get(semester, 1.0)

        hours = base * multiplier
        return max(
            float(credits * MIN_HOURS_PER_CREDIT),
            min(float(credits * MAX_HOURS_PER_CREDIT), hours),
        )

    @staticmethod
    def _estimate_preparation_time(total_hours: float) -> str:
        if total_hours <= 0:
            return "No preparation needed"
        if total_hours < 15:
            return "1–2 weeks"
        elif total_hours < 40:
            return "3–4 weeks"
        elif total_hours < 80:
            return "6–8 weeks"
        elif total_hours < 150:
            return "2–3 months"
        else:
            return "3–4 months"

    @staticmethod
    def _suggestions(m: MatchedSubject) -> List[str]:
        s: List[str] = []
        if not m.is_taken:
            s.append(
                f"Enrol in or study {m.subject_name} as soon as possible"
            )
        if m.severity == "critical":
            s += [
                f"Seek immediate tutoring for {m.subject_name}",
                "Schedule daily 2-hour study sessions",
                "Consult your subject professor",
            ]
        elif m.severity == "high":
            s += [
                f"Dedicate extra weekly time to {m.subject_name}",
                "Practice with previous exam papers",
            ]
        elif m.severity == "medium":
            s += [
                f"Regular weekly revision of {m.subject_name}",
                "Solve additional practice problems",
            ]
        else:
            s.append(f"Maintain current effort in {m.subject_name}")

        if m.low_confidence_flag:
            s.append(
                "Ensure your marks for this subject are uploaded "
                "to the system for a more accurate assessment."
            )
        return s

    @staticmethod
    def _resources(subject: str) -> List[Dict[str, Any]]:
        q = subject.replace(" ", "+")
        return [
            {
                "type": "course",
                "platform": "Coursera",
                "title": f"{subject} Fundamentals",
                "url": f"https://coursera.org/search?query={q}",
            },
            {
                "type": "video",
                "platform": "YouTube",
                "title": f"Learn {subject}",
                "url": (
                    f"https://youtube.com/results?search_query="
                    f"{q}+tutorial"
                ),
            },
            {
                "type": "practice",
                "platform": "GeeksforGeeks",
                "title": f"{subject} Practice",
                "url": f"https://geeksforgeeks.org/search?q={q}",
            },
        ]

    @staticmethod
    def _honours_rec_text(score: float, eligible: bool) -> str:
        if not eligible:
            return "CGPA below minimum requirement. Raise CGPA first."
        if score >= 75:
            return "Strong candidate. You may proceed."
        if score >= 55:
            return "Eligible but gaps exist. Improve before committing."
        return "Eligibility met but readiness is low. Delay recommended."

    @staticmethod
    def _honours_steps(
        matched: List[MatchedSubject],
        eligible: bool,
        min_cgpa: float,
        cgpa: float,
    ) -> List[str]:
        steps: List[str] = []
        if not eligible:
            steps.append(
                f"Raise CGPA from {cgpa:.2f} to at least {min_cgpa:.1f}"
            )
        for m in matched:
            if m.is_weakness:
                if not m.is_taken:
                    steps.append(
                        f"Complete subject: {m.subject_name}"
                    )
                else:
                    steps.append(
                        f"Improve {m.subject_name} from "
                        f"{(m.student_score or 0):.0f}% "
                        f"to ≥{m.min_score:.0f}%"
                    )
        return steps or [
            "All requirements met — proceed with application."
        ]

    # ════════════════════════════════════════════════════════════
    #  PERSIST RESULT
    # ════════════════════════════════════════════════════════════

    async def _save_result(
        self,
        resp: ReadinessResponse,
        interests: List[str],
        electives: List[str],
        honours: List[str],
    ) -> None:
        try:
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
                effort_readiness_score=resp.effort_readiness_score,
                total_gap_hours=resp.total_gap_hours,
                study_load_warning=resp.study_load_warning,
            )
            await doc.insert()
        except Exception as e:
            logger.error(f"Failed to persist readiness result: {e}")


# ════════════════════════════════════════════════════════════════
#  SINGLETON
# ════════════════════════════════════════════════════════════════

_instance: Optional[ReadinessService] = None


def get_readiness_service() -> ReadinessService:
    global _instance
    if _instance is None:
        _instance = ReadinessService()
    return _instance