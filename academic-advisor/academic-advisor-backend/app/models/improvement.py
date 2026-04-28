# app/models/improvement.py
"""
Improvement Plan & Gamification Models
=======================================
Tracks student improvement roadmaps, XP, badges, streaks,
resource completions, and interactive learning progress.
"""

from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class RoadmapStepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class ResourceType(str, Enum):
    VIDEO = "video"
    ARTICLE = "article"
    QUIZ = "quiz"
    PROJECT = "project"
    EXERCISE = "exercise"
    GAME = "game"


class BadgeCategory(str, Enum):
    STREAK = "streak"
    COMPLETION = "completion"
    MASTERY = "mastery"
    EXPLORER = "explorer"
    SPEED = "speed"
    SOCIAL = "social"


# ── Embedded Sub-Models ──────────────────────────────────────

class RoadmapResource(BaseModel):
    """A resource linked to a roadmap step."""
    title: str
    url: Optional[str] = None
    resource_type: ResourceType = ResourceType.ARTICLE
    duration_minutes: int = 15
    is_completed: bool = False
    completed_at: Optional[datetime] = None


class RoadmapStep(BaseModel):
    """A single step in an improvement roadmap."""
    step_number: int
    title: str
    description: str
    resources: List[RoadmapResource] = Field(default_factory=list)
    status: RoadmapStepStatus = RoadmapStepStatus.PENDING
    xp_reward: int = 25
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    quiz_score: Optional[float] = None


class Badge(BaseModel):
    """A badge/achievement earned by a student."""
    badge_id: str
    name: str
    description: str
    icon: str = "🏆"
    category: BadgeCategory = BadgeCategory.COMPLETION
    earned_at: datetime = Field(default_factory=datetime.utcnow)
    xp_bonus: int = 50


class ResourceCompletion(BaseModel):
    """Tracks a completed resource."""
    resource_id: str
    resource_title: str
    resource_type: ResourceType
    subject: str = ""
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    time_spent_minutes: int = 0
    quiz_score: Optional[float] = None
    xp_earned: int = 0


class GameScore(BaseModel):
    """Tracks scores from interactive learning games."""
    game_id: str
    game_name: str
    subject: str
    score: int = 0
    max_score: int = 100
    level_reached: int = 1
    played_at: datetime = Field(default_factory=datetime.utcnow)
    time_spent_seconds: int = 0


class TopicMastery(BaseModel):
    """Tracks mastery for a specific topic within a subject."""
    subject: str
    topic: str = ""
    lane: str = "theory"  # theory, practical, coding
    mastery_pct: float = 0.0
    attempts: int = 0
    best_score: int = 0
    current_difficulty: str = "easy"  # auto-adapts: easy → medium → hard
    total_correct: int = 0
    total_questions: int = 0
    last_practiced: Optional[datetime] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)  # [{score, date, difficulty}]


class DailyStreak(BaseModel):
    """Daily activity streak tracking."""
    date: str  # YYYY-MM-DD
    activities: int = 0
    xp_earned: int = 0


# ── Documents ────────────────────────────────────────────────

class ImprovementPlan(Document):
    """
    An improvement plan for a student targeting a specific goal
    (elective readiness, career prep, or weak subject remediation).
    """
    student_id: Indexed(str)
    target_type: str  # "elective", "career", "subject", "honours"
    target_name: str  # e.g., "Machine Learning", "Data Scientist"
    weak_subjects: List[str] = Field(default_factory=list)
    roadmap_steps: List[RoadmapStep] = Field(default_factory=list)
    total_xp: int = 0
    progress_pct: float = 0.0
    status: str = "active"  # active, completed, abandoned
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Settings:
        name = "improvement_plans"
        indexes = [
            "student_id",
            [("student_id", 1), ("status", 1)],
            [("student_id", 1), ("target_type", 1)],
        ]

    def recalculate_progress(self):
        """Recalculate progress percentage based on completed steps."""
        if not self.roadmap_steps:
            self.progress_pct = 0.0
            return
        completed = sum(1 for s in self.roadmap_steps if s.status == RoadmapStepStatus.COMPLETED)
        self.progress_pct = round((completed / len(self.roadmap_steps)) * 100, 1)
        if self.progress_pct >= 100:
            self.status = "completed"
            self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class StudentProgress(Document):
    """
    Overall gamification progress for a student.
    Tracks XP, level, badges, streaks, game scores, etc.
    """
    student_id: Indexed(str, unique=True)
    total_xp: int = 0
    level: int = 1
    badges: List[Badge] = Field(default_factory=list)
    resource_completions: List[ResourceCompletion] = Field(default_factory=list)
    game_scores: List[GameScore] = Field(default_factory=list)
    daily_streaks: List[DailyStreak] = Field(default_factory=list)
    current_streak: int = 0
    longest_streak: int = 0
    quizzes_taken: int = 0
    quizzes_passed: int = 0
    games_played: int = 0
    total_study_minutes: int = 0
    topic_masteries: List[TopicMastery] = Field(default_factory=list)
    last_activity_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "student_progress"
        indexes = ["student_id"]

    def add_xp(self, amount: int, source: str = ""):
        """Add XP and auto-level-up."""
        self.total_xp += amount
        # Level formula: every 500 XP = 1 level
        self.level = max(1, (self.total_xp // 500) + 1)
        self.last_activity_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def get_xp_to_next_level(self) -> int:
        """XP needed for next level."""
        next_level_xp = self.level * 500
        return max(0, next_level_xp - self.total_xp)

    def get_level_progress_pct(self) -> float:
        """Progress percentage within current level."""
        level_start = (self.level - 1) * 500
        level_end = self.level * 500
        progress = self.total_xp - level_start
        return round((progress / 500) * 100, 1)


# ── Badge Definitions ────────────────────────────────────────

BADGE_DEFINITIONS = {
    "first_step": Badge(badge_id="first_step", name="First Step", description="Complete your first activity", icon="👣", category=BadgeCategory.COMPLETION, xp_bonus=25),
    "streak_3": Badge(badge_id="streak_3", name="Consistent Learner", description="3-day learning streak", icon="🔥", category=BadgeCategory.STREAK, xp_bonus=50),
    "streak_7": Badge(badge_id="streak_7", name="Week Warrior", description="7-day learning streak", icon="⚡", category=BadgeCategory.STREAK, xp_bonus=100),
    "streak_30": Badge(badge_id="streak_30", name="Monthly Master", description="30-day learning streak", icon="🌟", category=BadgeCategory.STREAK, xp_bonus=500),
    "quiz_ace": Badge(badge_id="quiz_ace", name="Quiz Ace", description="Score 90%+ on 5 quizzes", icon="🎯", category=BadgeCategory.MASTERY, xp_bonus=100),
    "roadmap_complete": Badge(badge_id="roadmap_complete", name="Roadmap Champion", description="Complete an entire improvement roadmap", icon="🏆", category=BadgeCategory.COMPLETION, xp_bonus=200),
    "explorer": Badge(badge_id="explorer", name="Explorer", description="Try 3 different learning games", icon="🗺️", category=BadgeCategory.EXPLORER, xp_bonus=75),
    "speed_learner": Badge(badge_id="speed_learner", name="Speed Learner", description="Complete 5 resources in one day", icon="⚡", category=BadgeCategory.SPEED, xp_bonus=100),
    "subject_master": Badge(badge_id="subject_master", name="Subject Master", description="Reach 80%+ mastery in any subject", icon="📚", category=BadgeCategory.MASTERY, xp_bonus=150),
    "game_champion": Badge(badge_id="game_champion", name="Game Champion", description="Score 80%+ on 10 learning games", icon="🎮", category=BadgeCategory.MASTERY, xp_bonus=200),
    # Lane-specific badges
    "debug_hunter": Badge(badge_id="debug_hunter", name="Debug Hunter", description="Fix 10 bugs in Bug Hunter", icon="🐛", category=BadgeCategory.MASTERY, xp_bonus=100),
    "theory_climber": Badge(badge_id="theory_climber", name="Theory Climber", description="Complete 20 theory quizzes", icon="📖", category=BadgeCategory.MASTERY, xp_bonus=100),
    "code_tracer": Badge(badge_id="code_tracer", name="Code Tracer", description="Correctly trace 15 code snippets", icon="🔍", category=BadgeCategory.MASTERY, xp_bonus=100),
    "practical_pro": Badge(badge_id="practical_pro", name="Practical Pro", description="Complete 15 practical challenges", icon="🔧", category=BadgeCategory.MASTERY, xp_bonus=100),
    "boss_slayer": Badge(badge_id="boss_slayer", name="Boss Slayer", description="Pass 3 boss battles", icon="🐉", category=BadgeCategory.MASTERY, xp_bonus=200),
    "improvement_star": Badge(badge_id="improvement_star", name="Improvement Star", description="Improve mastery by 25%+ in any subject", icon="📈", category=BadgeCategory.MASTERY, xp_bonus=150),
}
