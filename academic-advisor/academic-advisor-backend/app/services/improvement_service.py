# app/services/improvement_service.py
"""
Improvement & Gamification Service
====================================
Generates roadmaps, tracks progress, awards XP/badges,
and provides data for the interactive learning hub.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.models.improvement import (
    ImprovementPlan, StudentProgress, RoadmapStep, RoadmapResource,
    Badge, ResourceCompletion, GameScore, DailyStreak, TopicMastery,
    RoadmapStepStatus, ResourceType, BADGE_DEFINITIONS,
)
from app.models.student_profile import StudentProfile

logger = logging.getLogger(__name__)


# ── Roadmap Templates ────────────────────────────────────────

SUBJECT_RESOURCES = {
    "Engineering Mathematics-III": [
        {"title": "Linear Algebra Crash Course", "url": "https://www.khanacademy.org/math/linear-algebra", "type": "video", "duration": 30},
        {"title": "Laplace Transform Practice", "url": "https://www.mathsisfun.com/calculus/laplace-transform.html", "type": "article", "duration": 20},
        {"title": "Probability & Statistics Fundamentals", "url": "https://www.khanacademy.org/math/statistics-probability", "type": "video", "duration": 25},
    ],
    "Data Structures and Algorithms": [
        {"title": "Visualgo - Algorithm Visualization", "url": "https://visualgo.net/", "type": "game", "duration": 20},
        {"title": "LeetCode Easy Problems", "url": "https://leetcode.com/problemset/?difficulty=EASY", "type": "exercise", "duration": 45},
        {"title": "Abdul Bari DSA Course", "url": "https://www.youtube.com/playlist?list=PLDN4rrl48XKpZkf03iYFl-O29szjTrs_O", "type": "video", "duration": 30},
    ],
    "Database Management Systems": [
        {"title": "SQL Practice - SQLBolt", "url": "https://sqlbolt.com/", "type": "game", "duration": 20},
        {"title": "Normalization Tutorial", "url": "https://www.studytonight.com/dbms/database-normalization.php", "type": "article", "duration": 15},
        {"title": "ER Diagram Builder", "url": "https://www.lucidchart.com/pages/er-diagrams", "type": "exercise", "duration": 25},
    ],
    "Operating Systems": [
        {"title": "OS Concepts - Neso Academy", "url": "https://www.youtube.com/playlist?list=PLBlnK6fEyqRiVhbXDGLXDk_OQAdc0cPiS", "type": "video", "duration": 30},
        {"title": "Process Scheduling Simulator", "url": "https://os-sim.netlify.app/", "type": "game", "duration": 20},
        {"title": "Memory Management Quiz", "url": "#quiz-memory-management", "type": "quiz", "duration": 15},
    ],
    "Computer Networks": [
        {"title": "Networking Fundamentals", "url": "https://www.youtube.com/watch?v=qiQR5rTSshw", "type": "video", "duration": 25},
        {"title": "Subnetting Practice", "url": "https://subnettingpractice.com/", "type": "game", "duration": 20},
        {"title": "Protocol Layers Quiz", "url": "#quiz-protocol-layers", "type": "quiz", "duration": 15},
    ],
    "Artificial Intelligence": [
        {"title": "AI Fundamentals - Google", "url": "https://ai.google/education/", "type": "video", "duration": 30},
        {"title": "Search Algorithm Visualizer", "url": "https://qiao.github.io/PathFinding.js/visual/", "type": "game", "duration": 20},
        {"title": "ML Playground - TensorFlow", "url": "https://playground.tensorflow.org/", "type": "game", "duration": 25},
    ],
    "Software Engineering": [
        {"title": "Design Patterns Illustrated", "url": "https://refactoring.guru/design-patterns", "type": "article", "duration": 30},
        {"title": "UML Diagram Practice", "url": "https://www.lucidchart.com/pages/uml-diagram", "type": "exercise", "duration": 25},
        {"title": "Agile & Scrum Overview", "url": "https://www.atlassian.com/agile", "type": "article", "duration": 15},
    ],
}

DEFAULT_RESOURCES = [
    {"title": "Review Lecture Notes", "url": "", "type": "article", "duration": 30},
    {"title": "Practice Problems Set", "url": "", "type": "exercise", "duration": 45},
    {"title": "Subject Quiz", "url": "", "type": "quiz", "duration": 15},
]


class ImprovementService:

    async def generate_roadmap(
        self, student_id: str, target_type: str, target_name: str
    ) -> Dict[str, Any]:
        """Generate an improvement roadmap for a student."""

        # Get student profile for weak subject detection
        profile = await StudentProfile.find_one(StudentProfile.user_id == student_id)
        weak_subjects = []

        if profile:
            for sem in (profile.semester_records or []):
                for subj in (sem.subjects or []):
                    if subj.total_marks < 50:
                        weak_subjects.append(subj.subject_name)

        # Build roadmap steps
        steps = []
        step_num = 1

        for subj in weak_subjects[:5]:  # Max 5 weak subjects
            resources_data = SUBJECT_RESOURCES.get(subj, DEFAULT_RESOURCES)
            resources = [
                RoadmapResource(
                    title=r["title"],
                    url=r.get("url", ""),
                    resource_type=ResourceType(r.get("type", "article")),
                    duration_minutes=r.get("duration", 15),
                )
                for r in resources_data
            ]

            steps.append(RoadmapStep(
                step_number=step_num,
                title=f"Improve: {subj}",
                description=f"Work through these resources to strengthen your understanding of {subj}",
                resources=resources,
                xp_reward=50,
            ))
            step_num += 1

        # Add target-specific steps
        if target_type == "career":
            steps.append(RoadmapStep(
                step_number=step_num,
                title=f"Career Prep: {target_name}",
                description=f"Build a project relevant to {target_name} career path",
                resources=[RoadmapResource(title="Build a Portfolio Project", resource_type=ResourceType.PROJECT, duration_minutes=120)],
                xp_reward=100,
            ))
        elif target_type == "elective":
            steps.append(RoadmapStep(
                step_number=step_num,
                title=f"Elective Readiness: {target_name}",
                description=f"Review prerequisites for {target_name}",
                resources=[RoadmapResource(title="Prerequisite Review", resource_type=ResourceType.ARTICLE, duration_minutes=60)],
                xp_reward=75,
            ))

        # Create plan
        plan = ImprovementPlan(
            student_id=student_id,
            target_type=target_type,
            target_name=target_name,
            weak_subjects=weak_subjects,
            roadmap_steps=steps,
        )
        await plan.insert()

        return {
            "plan_id": str(plan.id),
            "target": target_name,
            "steps": len(steps),
            "total_xp": sum(s.xp_reward for s in steps),
            "roadmap": plan.dict(),
        }

    async def complete_step(
        self, student_id: str, plan_id: str, step_number: int
    ) -> Dict[str, Any]:
        """Mark a roadmap step as completed and award XP."""
        plan = await ImprovementPlan.get(plan_id)
        if not plan or plan.student_id != student_id:
            return {"error": "Plan not found"}

        step = None
        for s in plan.roadmap_steps:
            if s.step_number == step_number:
                step = s
                break

        if not step:
            return {"error": "Step not found"}

        if step.status == RoadmapStepStatus.COMPLETED:
            return {"error": "Step already completed"}

        step.status = RoadmapStepStatus.COMPLETED
        step.completed_at = datetime.utcnow()
        plan.total_xp += step.xp_reward
        plan.recalculate_progress()
        await plan.save()

        # Award XP to student progress
        progress = await self._get_or_create_progress(student_id)
        progress.add_xp(step.xp_reward, f"roadmap:{plan_id}")
        await self._update_streak(progress)
        await self._check_badges(progress, plan)
        await progress.save()

        return {
            "xp_earned": step.xp_reward,
            "total_xp": progress.total_xp,
            "level": progress.level,
            "plan_progress": plan.progress_pct,
            "new_badges": [b.dict() for b in progress.badges[-3:]],
        }

    async def track_resource(
        self, student_id: str, resource_id: str, resource_title: str,
        resource_type: str, subject: str = "", time_spent: int = 0,
        quiz_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Track resource completion and award XP."""
        progress = await self._get_or_create_progress(student_id)

        xp = 15  # base XP for resource
        if quiz_score and quiz_score >= 80:
            xp += 10
        if time_spent > 30:
            xp += 5

        completion = ResourceCompletion(
            resource_id=resource_id,
            resource_title=resource_title,
            resource_type=ResourceType(resource_type),
            subject=subject,
            time_spent_minutes=time_spent,
            quiz_score=quiz_score,
            xp_earned=xp,
        )
        progress.resource_completions.append(completion)
        progress.total_study_minutes += time_spent
        if quiz_score is not None:
            progress.quizzes_taken += 1
            if quiz_score >= 60:
                progress.quizzes_passed += 1
        progress.add_xp(xp)
        await self._update_streak(progress)
        await progress.save()

        return {"xp_earned": xp, "total_xp": progress.total_xp, "level": progress.level}

    async def record_game_score(
        self, student_id: str, game_id: str, game_name: str,
        subject: str, score: int, max_score: int = 100,
        level_reached: int = 1, time_spent: int = 0,
    ) -> Dict[str, Any]:
        """Record a learning game score and award XP."""
        progress = await self._get_or_create_progress(student_id)

        game = GameScore(
            game_id=game_id, game_name=game_name, subject=subject,
            score=score, max_score=max_score, level_reached=level_reached,
            time_spent_seconds=time_spent,
        )
        progress.game_scores.append(game)
        progress.games_played += 1

        xp = int((score / max_score) * 30) + 5
        progress.add_xp(xp)
        await self._update_streak(progress)
        await self._check_badges(progress)
        await progress.save()

        return {"xp_earned": xp, "total_xp": progress.total_xp, "level": progress.level, "score": score}

    async def get_progress(self, student_id: str) -> Dict[str, Any]:
        """Get full gamification dashboard data."""
        progress = await self._get_or_create_progress(student_id)
        plans = await ImprovementPlan.find(
            ImprovementPlan.student_id == student_id,
            ImprovementPlan.status == "active",
        ).to_list()

        return {
            "total_xp": progress.total_xp,
            "level": progress.level,
            "xp_to_next_level": progress.get_xp_to_next_level(),
            "level_progress_pct": progress.get_level_progress_pct(),
            "current_streak": progress.current_streak,
            "longest_streak": progress.longest_streak,
            "badges": [b.dict() for b in progress.badges],
            "badge_count": len(progress.badges),
            "games_played": progress.games_played,
            "quizzes_taken": progress.quizzes_taken,
            "quizzes_passed": progress.quizzes_passed,
            "total_study_minutes": progress.total_study_minutes,
            "recent_completions": [c.dict() for c in progress.resource_completions[-5:]],
            "recent_games": [g.dict() for g in progress.game_scores[-5:]],
            "active_plans": [
                {
                    "id": str(p.id),
                    "target": p.target_name,
                    "type": p.target_type,
                    "progress": p.progress_pct,
                    "steps_total": len(p.roadmap_steps),
                    "steps_done": sum(1 for s in p.roadmap_steps if s.status == RoadmapStepStatus.COMPLETED),
                }
                for p in plans
            ],
        }

    async def get_roadmap(self, plan_id: str) -> Optional[Dict]:
        """Get a specific roadmap plan."""
        plan = await ImprovementPlan.get(plan_id)
        return plan.dict() if plan else None

    # ── Private Helpers ────────────────────────────────────────

    async def _get_or_create_progress(self, student_id: str) -> StudentProgress:
        progress = await StudentProgress.find_one(StudentProgress.student_id == student_id)
        if not progress:
            progress = StudentProgress(student_id=student_id)
            await progress.insert()
        return progress

    async def _update_streak(self, progress: StudentProgress):
        today = datetime.utcnow().strftime("%Y-%m-%d")
        existing = next((d for d in progress.daily_streaks if d.date == today), None)
        if existing:
            existing.activities += 1
        else:
            progress.daily_streaks.append(DailyStreak(date=today, activities=1))
            # Check if yesterday had activity
            yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            had_yesterday = any(d.date == yesterday for d in progress.daily_streaks)
            if had_yesterday:
                progress.current_streak += 1
            else:
                progress.current_streak = 1
            progress.longest_streak = max(progress.longest_streak, progress.current_streak)

    async def _check_badges(self, progress: StudentProgress, plan: ImprovementPlan = None):
        earned_ids = {b.badge_id for b in progress.badges}

        # First step badge
        if "first_step" not in earned_ids and len(progress.resource_completions) >= 1:
            badge = BADGE_DEFINITIONS["first_step"].model_copy()
            badge.earned_at = datetime.utcnow()
            progress.badges.append(badge)
            progress.add_xp(badge.xp_bonus)

        # Streak badges
        for streak_key, streak_val in [("streak_3", 3), ("streak_7", 7), ("streak_30", 30)]:
            if streak_key not in earned_ids and progress.current_streak >= streak_val:
                badge = BADGE_DEFINITIONS[streak_key].model_copy()
                badge.earned_at = datetime.utcnow()
                progress.badges.append(badge)
                progress.add_xp(badge.xp_bonus)

        # Roadmap complete
        if plan and "roadmap_complete" not in earned_ids and plan.status == "completed":
            badge = BADGE_DEFINITIONS["roadmap_complete"].model_copy()
            badge.earned_at = datetime.utcnow()
            progress.badges.append(badge)
            progress.add_xp(badge.xp_bonus)

        # Explorer badge
        if "explorer" not in earned_ids:
            unique_games = len(set(g.game_id for g in progress.game_scores))
            if unique_games >= 3:
                badge = BADGE_DEFINITIONS["explorer"].model_copy()
                badge.earned_at = datetime.utcnow()
                progress.badges.append(badge)
                progress.add_xp(badge.xp_bonus)

        # Lane-specific badges
        if "debug_hunter" not in earned_ids:
            bug_games = [g for g in progress.game_scores if "code_debug" in g.game_id or "bug" in g.game_id.lower()]
            if len(bug_games) >= 10:
                badge = BADGE_DEFINITIONS["debug_hunter"].model_copy()
                badge.earned_at = datetime.utcnow()
                progress.badges.append(badge)
                progress.add_xp(badge.xp_bonus)

        if "theory_climber" not in earned_ids:
            theory_games = [g for g in progress.game_scores if "mcq" in g.game_id or "fill" in g.game_id]
            if len(theory_games) >= 20:
                badge = BADGE_DEFINITIONS["theory_climber"].model_copy()
                badge.earned_at = datetime.utcnow()
                progress.badges.append(badge)
                progress.add_xp(badge.xp_bonus)

    # ── Mastery Tracking ──────────────────────────────────────

    async def update_mastery(
        self, student_id: str, subject: str, lane: str,
        score: int, total_questions: int, correct: int,
    ) -> Dict[str, Any]:
        """Update topic mastery with adaptive difficulty."""
        progress = await self._get_or_create_progress(student_id)

        # Find or create mastery entry
        mastery = None
        for m in progress.topic_masteries:
            if m.subject == subject and m.lane == lane:
                mastery = m
                break

        if not mastery:
            mastery = TopicMastery(subject=subject, lane=lane)
            progress.topic_masteries.append(mastery)

        # Update stats
        old_mastery = mastery.mastery_pct
        mastery.attempts += 1
        mastery.total_correct += correct
        mastery.total_questions += total_questions
        mastery.best_score = max(mastery.best_score, score)
        mastery.last_practiced = datetime.utcnow()

        # Calculate mastery % (weighted: recent scores count more)
        if mastery.total_questions > 0:
            mastery.mastery_pct = round((mastery.total_correct / mastery.total_questions) * 100, 1)

        # Store history
        mastery.history.append({
            "score": score, "difficulty": mastery.current_difficulty,
            "date": datetime.utcnow().isoformat(), "correct": correct, "total": total_questions,
        })
        # Keep only last 20 entries
        mastery.history = mastery.history[-20:]

        # Adaptive difficulty
        recent = mastery.history[-3:]  # last 3 attempts
        if len(recent) >= 2:
            avg_recent = sum(h["score"] for h in recent) / len(recent)
            if avg_recent >= 80 and mastery.current_difficulty == "easy":
                mastery.current_difficulty = "medium"
            elif avg_recent >= 80 and mastery.current_difficulty == "medium":
                mastery.current_difficulty = "hard"
            elif avg_recent < 40 and mastery.current_difficulty == "hard":
                mastery.current_difficulty = "medium"
            elif avg_recent < 40 and mastery.current_difficulty == "medium":
                mastery.current_difficulty = "easy"

        # Check improvement badge
        improvement = mastery.mastery_pct - old_mastery
        earned_ids = {b.badge_id for b in progress.badges}
        if "improvement_star" not in earned_ids and improvement >= 25:
            badge = BADGE_DEFINITIONS["improvement_star"].model_copy()
            badge.earned_at = datetime.utcnow()
            progress.badges.append(badge)
            progress.add_xp(badge.xp_bonus)

        await progress.save()

        return {
            "subject": subject,
            "lane": lane,
            "mastery_pct": mastery.mastery_pct,
            "difficulty": mastery.current_difficulty,
            "attempts": mastery.attempts,
            "best_score": mastery.best_score,
            "improvement": round(improvement, 1),
        }

    async def get_mastery_summary(self, student_id: str) -> Dict[str, Any]:
        """Get per-subject mastery overview."""
        progress = await self._get_or_create_progress(student_id)
        subjects: Dict[str, Any] = {}

        for m in progress.topic_masteries:
            if m.subject not in subjects:
                subjects[m.subject] = {"subject": m.subject, "lanes": {}, "overall_mastery": 0}
            subjects[m.subject]["lanes"][m.lane] = {
                "mastery_pct": m.mastery_pct,
                "attempts": m.attempts,
                "best_score": m.best_score,
                "difficulty": m.current_difficulty,
                "last_practiced": m.last_practiced.isoformat() if m.last_practiced else None,
            }

        # Calculate overall per subject
        for subj_data in subjects.values():
            lanes = subj_data["lanes"]
            if lanes:
                subj_data["overall_mastery"] = round(sum(l["mastery_pct"] for l in lanes.values()) / len(lanes), 1)

        return {
            "subjects": list(subjects.values()),
            "total_practiced": len(subjects),
        }

    # ── Quiz Generation ───────────────────────────────────────

    async def get_weak_subjects(self, student_id: str) -> Dict[str, Any]:
        """Auto-detect weak subjects from student marks."""
        profile = await StudentProfile.find_one(StudentProfile.user_id == student_id)
        weak = []
        all_subjects = []

        if profile:
            for sem in (profile.semester_records or []):
                for subj in (sem.subjects or []):
                    entry = {
                        "name": subj.subject_name,
                        "marks": subj.total_marks,
                        "semester": sem.semester,
                        "max_marks": 100,
                    }
                    all_subjects.append(entry)
                    if subj.total_marks < 60:
                        entry["severity"] = "critical" if subj.total_marks < 40 else "warning"
                        weak.append(entry)

        # Sort: worst first
        weak.sort(key=lambda x: x["marks"])
        return {
            "weak_subjects": weak,
            "total_subjects": len(all_subjects),
            "weak_count": len(weak),
        }

    async def generate_quiz(
        self, student_id: str, subject: str, topic: str = "",
        difficulty: str = "medium", count: int = 5, quiz_type: str = "mcq",
    ) -> Dict[str, Any]:
        """Generate quiz questions using LLM."""
        try:
            from app.services.chatbot.llm_service import llm_service
        except Exception:
            # Fallback if LLM unavailable
            return self._fallback_quiz(subject, quiz_type, count, difficulty)

        difficulty_desc = {
            "easy": "basic recall and definition questions suitable for beginners",
            "medium": "application-level questions requiring understanding of concepts",
            "hard": "analysis-level questions involving problem-solving and code tracing",
        }.get(difficulty, "medium-difficulty")

        topic_clause = f" focusing on the topic: {topic}" if topic else ""

        if quiz_type == "code_debug":
            prompt = f"""Generate exactly {count} code debugging questions for the subject "{subject}"{topic_clause}.
Difficulty: {difficulty_desc}.
Each question should show a short code snippet (Python/C/Java) with a bug, and 4 options for what the fix is.

Return ONLY a JSON array (no markdown, no explanation) in this exact format:
[{{"question": "What is wrong with this code?\\n```python\\ndef add(a, b):\\n    return a - b\\n```", "options": ["Change - to +", "Add return type", "Use print instead", "Add parentheses"], "correct": 0, "explanation": "The function should add, not subtract"}}]"""
        elif quiz_type == "fill_blank":
            prompt = f"""Generate exactly {count} fill-in-the-blank questions for the subject "{subject}"{topic_clause}.
Difficulty: {difficulty_desc}.
Each question should have a sentence with a blank (shown as ___) and 4 options.

Return ONLY a JSON array (no markdown, no explanation) in this exact format:
[{{"question": "In DBMS, ___ is the process of organizing data to reduce redundancy.", "options": ["Normalization", "Indexing", "Hashing", "Sorting"], "correct": 0, "explanation": "Normalization reduces data redundancy by organizing tables"}}]"""
        else:  # mcq (default)
            prompt = f"""Generate exactly {count} multiple-choice questions for the subject "{subject}"{topic_clause}.
Difficulty: {difficulty_desc}.
Questions should test real understanding from theory to practical application.

Return ONLY a JSON array (no markdown, no explanation) in this exact format:
[{{"question": "Which scheduling algorithm may cause starvation?", "options": ["FCFS", "SJF", "Round Robin", "FIFO"], "correct": 1, "explanation": "SJF can cause starvation for longer processes"}}]"""

        try:
            raw = await llm_service.generate_response(prompt, context_type="quiz_generation")
            if not raw:
                return self._fallback_quiz(subject, quiz_type, count, difficulty)

            # Parse JSON from response
            import json, re
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', raw, re.DOTALL)
            if json_match:
                questions = json.loads(json_match.group())
            else:
                return self._fallback_quiz(subject, quiz_type, count, difficulty)

            return {
                "subject": subject,
                "topic": topic,
                "difficulty": difficulty,
                "quiz_type": quiz_type,
                "questions": questions[:count],
                "generated": True,
            }
        except Exception as e:
            logger.warning(f"LLM quiz generation failed: {e}")
            return self._fallback_quiz(subject, quiz_type, count, difficulty)

    def _fallback_quiz(self, subject: str, quiz_type: str, count: int, difficulty: str) -> Dict:
        """Hardcoded fallback quizzes when LLM is unavailable."""
        FALLBACK_BANKS = {
            "Operating Systems": [
                {"question": "Which of the following is NOT a process state?", "options": ["Running", "Ready", "Blocked", "Compiled"], "correct": 3, "explanation": "Compiled is not a valid process state. The standard states are New, Ready, Running, Blocked/Waiting, and Terminated."},
                {"question": "What is a deadlock?", "options": ["A process that runs forever", "A situation where processes wait for each other indefinitely", "A crashed process", "A memory overflow"], "correct": 1, "explanation": "Deadlock occurs when two or more processes are waiting for resources held by each other, creating a circular dependency."},
                {"question": "Which scheduling algorithm gives minimum average waiting time?", "options": ["FCFS", "SJF", "Round Robin", "Priority"], "correct": 1, "explanation": "Shortest Job First (SJF) provides the minimum average waiting time among non-preemptive algorithms."},
                {"question": "What does the fork() system call do?", "options": ["Terminates a process", "Creates a new process", "Suspends a process", "Resumes a process"], "correct": 1, "explanation": "fork() creates a new child process that is a copy of the parent process."},
                {"question": "Which page replacement algorithm is optimal?", "options": ["FIFO", "LRU", "OPT/Belady's", "Clock"], "correct": 2, "explanation": "OPT (Belady's algorithm) replaces the page that won't be used for the longest time, giving the lowest page fault rate."},
            ],
            "Database Management Systems": [
                {"question": "What is the highest normal form that eliminates all partial dependencies?", "options": ["1NF", "2NF", "3NF", "BCNF"], "correct": 1, "explanation": "2NF eliminates partial dependencies — where a non-key attribute depends on only part of a composite primary key."},
                {"question": "Which SQL clause is used to filter groups?", "options": ["WHERE", "HAVING", "GROUP BY", "ORDER BY"], "correct": 1, "explanation": "HAVING filters groups after GROUP BY, while WHERE filters individual rows before grouping."},
                {"question": "What does ACID stand for in database transactions?", "options": ["Atomicity, Consistency, Isolation, Durability", "Access, Control, Identity, Data", "Automatic, Concurrent, Isolated, Distributed", "None of the above"], "correct": 0, "explanation": "ACID properties ensure reliable transaction processing in databases."},
                {"question": "Which join returns all rows from both tables?", "options": ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL OUTER JOIN"], "correct": 3, "explanation": "FULL OUTER JOIN returns all rows from both tables, with NULLs where there's no match."},
                {"question": "What is a candidate key?", "options": ["A foreign key", "A minimal superkey", "An alternate primary key", "Both B and C"], "correct": 3, "explanation": "A candidate key is a minimal superkey (no redundant attributes) and any candidate key can serve as the primary key."},
            ],
            "Data Structures and Algorithms": [
                {"question": "What is the time complexity of binary search?", "options": ["O(n)", "O(log n)", "O(n²)", "O(1)"], "correct": 1, "explanation": "Binary search halves the search space each time, giving O(log n) time complexity."},
                {"question": "Which data structure uses LIFO ordering?", "options": ["Queue", "Stack", "Array", "Linked List"], "correct": 1, "explanation": "Stack follows Last-In-First-Out (LIFO) — the last element pushed is the first one popped."},
                {"question": "What is the worst-case time complexity of quicksort?", "options": ["O(n log n)", "O(n²)", "O(n)", "O(log n)"], "correct": 1, "explanation": "Quicksort degrades to O(n²) when the pivot selection is poor (e.g., already sorted array with first element as pivot)."},
                {"question": "Which traversal of BST gives sorted output?", "options": ["Preorder", "Inorder", "Postorder", "Level order"], "correct": 1, "explanation": "Inorder traversal (Left-Root-Right) of a BST visits nodes in ascending sorted order."},
                {"question": "What is the space complexity of BFS?", "options": ["O(1)", "O(V)", "O(E)", "O(V+E)"], "correct": 1, "explanation": "BFS uses a queue that can hold up to O(V) vertices in the worst case."},
            ],
            "Computer Networks": [
                {"question": "Which layer of the OSI model handles routing?", "options": ["Data Link", "Network", "Transport", "Session"], "correct": 1, "explanation": "The Network layer (Layer 3) is responsible for logical addressing and routing packets between networks."},
                {"question": "What protocol does HTTP use at the transport layer?", "options": ["UDP", "TCP", "ICMP", "ARP"], "correct": 1, "explanation": "HTTP uses TCP at the transport layer to ensure reliable, ordered delivery of web data."},
                {"question": "What is the purpose of ARP?", "options": ["Route packets", "Resolve IP to MAC address", "Encrypt data", "Assign IP addresses"], "correct": 1, "explanation": "ARP (Address Resolution Protocol) maps a known IP address to a MAC address on the local network."},
                {"question": "Which topology has a single point of failure at the center?", "options": ["Ring", "Bus", "Star", "Mesh"], "correct": 2, "explanation": "In a Star topology, all nodes connect through a central hub — if the hub fails, the entire network goes down."},
                {"question": "What is the default subnet mask for a Class C network?", "options": ["255.0.0.0", "255.255.0.0", "255.255.255.0", "255.255.255.255"], "correct": 2, "explanation": "Class C networks use 255.255.255.0 (/24), providing 254 usable host addresses."},
            ],
            "Artificial Intelligence": [
                {"question": "Which search algorithm is both complete and optimal?", "options": ["DFS", "BFS", "A*", "Greedy Best-First"], "correct": 2, "explanation": "A* is both complete and optimal when using an admissible heuristic (never overestimates the cost)."},
                {"question": "What is the Turing Test?", "options": ["A test for program correctness", "A test for machine intelligence", "A sorting algorithm test", "A network speed test"], "correct": 1, "explanation": "The Turing Test evaluates whether a machine can exhibit intelligent behavior indistinguishable from a human."},
                {"question": "Which activation function outputs values between 0 and 1?", "options": ["ReLU", "Sigmoid", "Tanh", "Linear"], "correct": 1, "explanation": "The Sigmoid function maps any input to a value between 0 and 1, making it useful for probability outputs."},
                {"question": "What is overfitting in machine learning?", "options": ["Model performs well on all data", "Model memorizes training data", "Model is too simple", "Model has no bias"], "correct": 1, "explanation": "Overfitting occurs when a model learns noise and details in training data, performing poorly on unseen data."},
                {"question": "What does CNN stand for in deep learning?", "options": ["Computer Neural Network", "Convolutional Neural Network", "Connected Node Network", "Clustered Neuron Network"], "correct": 1, "explanation": "CNN (Convolutional Neural Network) uses convolutional layers to detect patterns in image and spatial data."},
            ],
        }

        questions = FALLBACK_BANKS.get(subject, [
            {"question": f"Sample question about {subject}", "options": ["Option A", "Option B", "Option C", "Option D"], "correct": 0, "explanation": f"This is a sample question. LLM was unavailable for {subject}."},
        ])

        return {
            "subject": subject,
            "topic": "",
            "difficulty": difficulty,
            "quiz_type": quiz_type,
            "questions": questions[:count],
            "generated": False,
        }


improvement_service = ImprovementService()

