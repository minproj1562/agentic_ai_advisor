# app/core/readiness_config.py
"""
Single source of truth for all readiness engine constants.
Every constant has a documented rationale.
"""

from typing import Dict

# ══════════════════════════════════════════════════════════════
#  BLENDING WEIGHTS
# ══════════════════════════════════════════════════════════════

ACADEMIC_WEIGHT_DEFAULT: float = 0.80
EFFORT_WEIGHT_DEFAULT: float = 0.20

ACADEMIC_WEIGHT_FIRST_SEM: float = 0.90
EFFORT_WEIGHT_FIRST_SEM: float = 0.10

# ══════════════════════════════════════════════════════════════
#  ACADEMIC SCORE THRESHOLDS
# ══════════════════════════════════════════════════════════════

PASSING_SCORE: float = 40.0
MAX_SCORE_RATIO: float = 1.0

EFFORT_CAP_WITH_BACKLOG: float = 60.0

# ══════════════════════════════════════════════════════════════
#  STUDY HOURS FORMULA CONSTANTS
#
#  HOURS_PER_MARK_PER_CREDIT = 0.1
#  Derivation:
#    1 credit = 30 hrs/semester (standard academic expectation)
#    Revision = 1/10 of initial learning time
#    Per mark-point: (30 / 100) × (1/10) × credits = 0.03 × credits
#    Rounded up to 0.1 for safety margin (covers exam prep overhead)
#    Formula: hours = gap × credits × 0.1
#    Example: gap=20, credits=3 → 20 × 3 × 0.1 = 6 hours ✓
#    Example: gap=40, credits=4 → 40 × 4 × 0.1 = 16 hours ✓
# ══════════════════════════════════════════════════════════════

HOURS_PER_MARK_PER_CREDIT: float = 0.1
BACKLOG_HOURS_MULTIPLIER: float = 1.5
SENIOR_HOURS_MULTIPLIER: float = 1.2
MAX_HOURS_PER_CREDIT: float = 20.0
MIN_HOURS_PER_CREDIT: float = 1.0

# ══════════════════════════════════════════════════════════════
#  STUDY PLAN DURATION
#
#  Extra study budget per week (hours beyond normal class time).
#  Based on sustainable student capacity:
#    Light load  (< 15 credits): 20 hrs/week extra
#    Normal load (15–20 credits): 15 hrs/week extra
#    Heavy load  (> 20 credits): 10 hrs/week extra
#
#  Derivation: 2–3 hrs/day extra = 14–21 hrs/week.
#  Conservative middle values used.
# ══════════════════════════════════════════════════════════════

EXTRA_STUDY_LIGHT_LOAD: float = 20.0
EXTRA_STUDY_NORMAL_LOAD: float = 15.0
EXTRA_STUDY_HEAVY_LOAD: float = 10.0

LIGHT_LOAD_THRESHOLD: int = 15
HEAVY_LOAD_THRESHOLD: int = 20

MIN_PLAN_WEEKS: int = 2
MAX_PLAN_WEEKS: int = 16

# ══════════════════════════════════════════════════════════════
#  SEVERITY THRESHOLDS
#  Gap-based classification (importance adjusts level afterwards)
# ══════════════════════════════════════════════════════════════

GAP_SEVERITY_CRITICAL: float = 30.0
GAP_SEVERITY_HIGH: float = 20.0
GAP_SEVERITY_MEDIUM: float = 10.0

IMPORTANCE_ESCALATE_THRESHOLD: float = 0.8
IMPORTANCE_DEESCALATE_THRESHOLD: float = 0.3

# ══════════════════════════════════════════════════════════════
#  READINESS LEVEL BANDS
# ══════════════════════════════════════════════════════════════

READINESS_LEVELS: Dict[str, float] = {
    "excellent": 85.0,
    "good": 70.0,
    "moderate": 55.0,
    "low": 40.0,
    "not_ready": 0.0,
}

# ══════════════════════════════════════════════════════════════
#  SEMESTER DIFFICULTY MULTIPLIERS
# ══════════════════════════════════════════════════════════════

SEMESTER_MULTIPLIERS: Dict[int, float] = {
    1: 1.0,
    2: 1.0,
    3: 1.0,
    4: 1.0,
    5: 1.2,
    6: 1.2,
    7: 1.2,
    8: 1.2,
}

# ══════════════════════════════════════════════════════════════
#  STUDY LOAD WARNING THRESHOLDS (total hours)
# ══════════════════════════════════════════════════════════════

HEAVY_STUDY_WARNING_TOTAL: float = 100.0
MODERATE_STUDY_WARNING_TOTAL: float = 72.0

# ══════════════════════════════════════════════════════════════
#  CONFIDENCE THRESHOLDS
# ══════════════════════════════════════════════════════════════

LOW_CONFIDENCE_THRESHOLD: float = 0.7