# scripts/generate_training_data_v2.py
"""
Optimized Training Data Generator v2 (Self-Contained)
======================================================
Generates ALL training data:
  - Program Elective (PEC) recommendations
  - Open Elective (OEC) recommendations  
  - Performance Predictor (SGPA prediction)
  - Weakness Detector (severity classification)

Usage:
    python -m scripts.generate_training_data_v2
    python -m scripts.generate_training_data_v2 --pec 800 --oec 600
    python -m scripts.generate_training_data_v2 --skip-electives
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

np.random.seed(42)

# ═══════════════════════════════════════════════════════════════════
#  SHARED CONSTANTS
# ═══════════════════════════════════════════════════════════════════

CANONICAL_SUBJECTS = [
    "Engineering Mathematics-III", "Engineering Mathematics-IV",
    "Data Structures and Algorithms", "Database Management Systems",
    "Digital Logic & Design", "Operating Systems", "Computer Networks",
    "Microcontroller & Embedded Systems", "Software Engineering",
    "Python", "C++", "Java", "Automata Theory", "Design & Analysis of Algorithms",
    "Artificial Intelligence", "Cryptography & Network Security",
    "Full Stack Development", "IoT",
]

INTEREST_AREAS = [
    "Artificial Intelligence & Machine Learning",
    "Mobile & IoT Development",
    "Web Development",
    "Data Science & Analytics",
    "Cloud & Distributed Systems",
    "Network & Wireless Systems",
]

PEC_LABELS = ["ML", "WT", "DWM", "CCS"]
OEC_LABELS = ["RE", "OR", "CSL", "DBM", "EAM"]

# ═══════════════════════════════════════════════════════════════════
#  STUDENT ARCHETYPES (shared across all generators)
# ═══════════════════════════════════════════════════════════════════

ARCHETYPES = {
    "topper":       {"pct": 0.08, "ability": (78, 95), "attend": (90, 100), "assign": (88, 100), "study": (8, 14), "consistency": 0.88},
    "strong":       {"pct": 0.15, "ability": (65, 80), "attend": (80, 96),  "assign": (75, 95),  "study": (5, 10), "consistency": 0.78},
    "above_avg":    {"pct": 0.18, "ability": (55, 68), "attend": (72, 88),  "assign": (60, 85),  "study": (4, 8),  "consistency": 0.70},
    "average":      {"pct": 0.25, "ability": (42, 58), "attend": (62, 82),  "assign": (48, 75),  "study": (2, 6),  "consistency": 0.62},
    "below_avg":    {"pct": 0.18, "ability": (30, 45), "attend": (48, 70),  "assign": (30, 60),  "study": (1, 4),  "consistency": 0.52},
    "struggling":   {"pct": 0.10, "ability": (18, 33), "attend": (30, 58),  "assign": (12, 42),  "study": (0, 3),  "consistency": 0.42},
    "failing":      {"pct": 0.03, "ability": (5, 22),  "attend": (10, 40),  "assign": (5, 25),   "study": (0, 2),  "consistency": 0.32},
    "improving":    {"pct": 0.02, "ability": (48, 68), "attend": (72, 92),  "assign": (65, 88),  "study": (5, 10), "consistency": 0.55},
    "inconsistent": {"pct": 0.01, "ability": (35, 75), "attend": (45, 90),  "assign": (30, 90),  "study": (1, 10), "consistency": 0.25},
}

# ═══════════════════════════════════════════════════════════════════
#  ELECTIVE AFFINITY MAPS (with realistic overlap)
# ═══════════════════════════════════════════════════════════════════

PEC_AFFINITY = {
    "ML": {
        "boost": {
            "Python": (3, 12), "Artificial Intelligence": (5, 15),
            "Engineering Mathematics-III": (2, 8), "Data Structures and Algorithms": (2, 8),
            "Database Management Systems": (0, 5),
        },
        "penalize": {
            "Microcontroller & Embedded Systems": (-3, -10), "IoT": (-3, -12),
            "Digital Logic & Design": (-2, -6),
        },
    },
    "WT": {
        "boost": {
            "Computer Networks": (5, 12), "Microcontroller & Embedded Systems": (5, 12),
            "IoT": (5, 15), "Digital Logic & Design": (3, 8), "Operating Systems": (2, 6),
        },
        "penalize": {
            "Python": (-2, -6), "Artificial Intelligence": (-3, -10),
            "Full Stack Development": (-2, -8),
        },
    },
    "DWM": {
        "boost": {
            "Database Management Systems": (5, 15), "Data Structures and Algorithms": (3, 10),
            "Python": (2, 8), "Engineering Mathematics-IV": (2, 6),
        },
        "penalize": {
            "Microcontroller & Embedded Systems": (-3, -10), "IoT": (-3, -10),
            "Digital Logic & Design": (-2, -6),
        },
    },
    "CCS": {
        "boost": {
            "Full Stack Development": (5, 15), "Computer Networks": (3, 10),
            "Operating Systems": (3, 8), "Software Engineering": (2, 8),
            "Database Management Systems": (2, 6),
        },
        "penalize": {
            "Microcontroller & Embedded Systems": (-2, -8), "IoT": (-2, -8),
            "Artificial Intelligence": (-2, -6),
        },
    },
}

OEC_AFFINITY = {
    "RE": {
        "boost": {
            "Engineering Mathematics-III": (5, 12), "Engineering Mathematics-IV": (4, 10),
            "Software Engineering": (2, 6), "Operating Systems": (1, 5),
        },
        "penalize": {"Full Stack Development": (-2, -8), "Python": (-1, -4)},
    },
    "OR": {
        "boost": {
            "Engineering Mathematics-III": (5, 12), "Engineering Mathematics-IV": (5, 12),
            "Design & Analysis of Algorithms": (3, 8), "Data Structures and Algorithms": (2, 6),
        },
        "penalize": {"IoT": (-2, -6), "Full Stack Development": (-1, -5)},
    },
    "CSL": {
        "boost": {
            "Computer Networks": (5, 15), "Cryptography & Network Security": (5, 15),
            "Operating Systems": (3, 8),
        },
        "penalize": {"Engineering Mathematics-III": (-1, -5), "IoT": (-1, -5)},
    },
    "DBM": {
        "boost": {
            "Database Management Systems": (4, 12), "Software Engineering": (4, 10),
            "Full Stack Development": (4, 12), "Python": (2, 6),
        },
        "penalize": {"Microcontroller & Embedded Systems": (-2, -8), "Digital Logic & Design": (-2, -6)},
    },
    "EAM": {
        "boost": {
            "Microcontroller & Embedded Systems": (4, 12), "IoT": (4, 12),
            "Engineering Mathematics-III": (2, 6),
        },
        "penalize": {"Full Stack Development": (-2, -8), "Artificial Intelligence": (-2, -6)},
    },
}

# Interest patterns
PEC_INTEREST_PATTERNS = {
    "ML": {"primary": ["Artificial Intelligence & Machine Learning", "Data Science & Analytics"], "secondary": ["Web Development", "Cloud & Distributed Systems"], "rare": ["Network & Wireless Systems"]},
    "WT": {"primary": ["Network & Wireless Systems", "Mobile & IoT Development"], "secondary": ["Cloud & Distributed Systems"], "rare": ["Data Science & Analytics"]},
    "DWM": {"primary": ["Data Science & Analytics"], "secondary": ["Artificial Intelligence & Machine Learning", "Web Development"], "rare": ["Cloud & Distributed Systems"]},
    "CCS": {"primary": ["Cloud & Distributed Systems", "Web Development"], "secondary": ["Network & Wireless Systems", "Data Science & Analytics"], "rare": ["Artificial Intelligence & Machine Learning"]},
}

OEC_INTEREST_PATTERNS = {
    "RE": {"primary": ["Network & Wireless Systems"], "secondary": ["Cloud & Distributed Systems"], "rare": ["Data Science & Analytics"]},
    "OR": {"primary": ["Data Science & Analytics"], "secondary": ["Artificial Intelligence & Machine Learning"], "rare": ["Web Development"]},
    "CSL": {"primary": ["Network & Wireless Systems"], "secondary": ["Cloud & Distributed Systems"], "rare": ["Web Development"]},
    "DBM": {"primary": ["Web Development", "Data Science & Analytics"], "secondary": ["Cloud & Distributed Systems"], "rare": ["Mobile & IoT Development"]},
    "EAM": {"primary": ["Mobile & IoT Development"], "secondary": ["Network & Wireless Systems"], "rare": ["Cloud & Distributed Systems"]},
}

# Project skill pools
PEC_PROJECT_SKILLS = {
    "ML": ["python", "tensorflow", "pytorch", "sklearn", "pandas", "numpy", "machine learning", "deep learning", "nlp", "neural network", "keras", "classification", "regression"],
    "WT": ["arduino", "raspberry pi", "iot", "embedded", "sensor", "wireless", "mqtt", "microcontroller", "esp32", "bluetooth", "gpio"],
    "DWM": ["sql", "mongodb", "data warehouse", "etl", "analytics", "tableau", "power bi", "data mining", "postgresql", "dashboard"],
    "CCS": ["aws", "azure", "docker", "kubernetes", "cloud", "devops", "terraform", "serverless", "react", "node", "fullstack", "ci/cd"],
}

OEC_PROJECT_SKILLS = {
    "RE": ["probability", "statistics", "reliability", "fmea", "fault tree", "weibull", "simulation", "quality", "testing", "risk"],
    "OR": ["optimization", "linear programming", "simulation", "queuing", "scheduling", "inventory", "supply chain", "simplex", "scipy"],
    "CSL": ["security", "cyber", "firewall", "encryption", "phishing", "vulnerability", "authentication", "network security", "forensics"],
    "DBM": ["digital marketing", "seo", "analytics", "ecommerce", "crm", "dashboard", "kpi", "agile", "web", "react"],
    "EAM": ["energy", "audit", "solar", "renewable", "power", "hvac", "iot", "monitoring", "sensor", "efficiency"],
}


# ═══════════════════════════════════════════════════════════════════
#  PERFORMANCE & WEAKNESS — SUBJECT DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

SUBJECTS_BY_SEMESTER: Dict[int, List[Dict[str, Any]]] = {
    3: [
        {"name": "Engineering Mathematics-III", "code": "MATH301", "credits": 4, "difficulty": 0.82, "is_practical": False},
        {"name": "Data Structures and Algorithms", "code": "DSA301", "credits": 4, "difficulty": 0.68, "is_practical": False},
        {"name": "Database Management Systems", "code": "DBMS301", "credits": 4, "difficulty": 0.58, "is_practical": False},
        {"name": "Digital Logic & Design", "code": "DLDA301", "credits": 4, "difficulty": 0.65, "is_practical": False},
        {"name": "Python Programming", "code": "PYTHON301", "credits": 2, "difficulty": 0.38, "is_practical": True},
        {"name": "DSA Laboratory", "code": "DSAL301", "credits": 1, "difficulty": 0.42, "is_practical": True},
    ],
    4: [
        {"name": "Engineering Mathematics-IV", "code": "MATH401", "credits": 4, "difficulty": 0.78, "is_practical": False},
        {"name": "Operating Systems", "code": "OS401", "credits": 4, "difficulty": 0.72, "is_practical": False},
        {"name": "Computer Networks", "code": "CN401", "credits": 4, "difficulty": 0.67, "is_practical": False},
        {"name": "Software Engineering", "code": "SE401", "credits": 4, "difficulty": 0.50, "is_practical": False},
        {"name": "Microcontroller & Embedded Systems", "code": "MES401", "credits": 4, "difficulty": 0.75, "is_practical": False},
        {"name": "Microcontroller Lab", "code": "MESL401", "credits": 1, "difficulty": 0.48, "is_practical": True},
        {"name": "Computer Networks Lab", "code": "CNL401", "credits": 1, "difficulty": 0.43, "is_practical": True},
    ],
    5: [
        {"name": "Automata Theory", "code": "ITPCC509", "credits": 4, "difficulty": 0.85, "is_practical": False},
        {"name": "Design & Analysis of Algorithms", "code": "ITPCC501", "credits": 3, "difficulty": 0.78, "is_practical": False},
        {"name": "Cloud Computing Laboratory", "code": "ITLBC506", "credits": 1, "difficulty": 0.44, "is_practical": True},
        {"name": "Mobile App Development Lab", "code": "ITLBC507", "credits": 1, "difficulty": 0.46, "is_practical": True},
    ],
    6: [
        {"name": "Cryptography & Network Security", "code": "ITPCC611", "credits": 4, "difficulty": 0.80, "is_practical": False},
        {"name": "Cryptography Lab", "code": "ITLBC608", "credits": 1, "difficulty": 0.48, "is_practical": True},
        {"name": "Data Science Laboratory", "code": "ITLBC609", "credits": 1, "difficulty": 0.40, "is_practical": True},
        {"name": "DevOps Laboratory", "code": "ITSBL603", "credits": 2, "difficulty": 0.46, "is_practical": True},
    ],
    7: [
        {"name": "Artificial Intelligence", "code": "ITPCC710", "credits": 4, "difficulty": 0.70, "is_practical": False},
        {"name": "AI Laboratory", "code": "ITLBC711", "credits": 1, "difficulty": 0.42, "is_practical": True},
        {"name": "Data Analytics Lab", "code": "ITLBC712", "credits": 1, "difficulty": 0.38, "is_practical": True},
    ],
}

PREREQUISITE_MAP = {
    "Engineering Mathematics-IV": "Engineering Mathematics-III",
    "Design & Analysis of Algorithms": "Data Structures and Algorithms",
    "Cryptography & Network Security": "Computer Networks",
    "Artificial Intelligence": "Engineering Mathematics-III",
    "Automata Theory": "Engineering Mathematics-III",
}


# ═══════════════════════════════════════════════════════════════════
#  SHARED HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def _clip(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return float(np.clip(val, lo, hi))


def _sample_uniform(low: float, high: float) -> float:
    return np.random.uniform(low, high)


def _sample_clipped_normal(mean: float, std: float, low: float = 0, high: float = 100) -> float:
    return float(np.clip(np.random.normal(mean, std), low, high))


def _sample_archetype() -> Tuple[str, dict]:
    names = list(ARCHETYPES.keys())
    probs = [ARCHETYPES[a]["pct"] for a in names]
    probs = [p / sum(probs) for p in probs]
    name = np.random.choice(names, p=probs)
    return name, ARCHETYPES[name]


# ═══════════════════════════════════════════════════════════════════
#  ELECTIVE DATA HELPERS
# ═══════════════════════════════════════════════════════════════════

def _generate_elective_marks(
    label: str,
    base_ability: float,
    consistency: float,
    affinity_map: Dict,
) -> Dict[str, float]:
    affinity = affinity_map.get(label, {"boost": {}, "penalize": {}})
    boost_map = affinity.get("boost", {})
    penalty_map = affinity.get("penalize", {})
    noise_std = (1 - consistency) * 15 + 5
    marks = {}

    for subj in CANONICAL_SUBJECTS:
        score = base_ability + np.random.normal(0, noise_std)
        if subj in boost_map:
            lo, hi = boost_map[subj]
            score += np.random.uniform(lo, hi)
        elif subj in penalty_map:
            lo, hi = penalty_map[subj]
            score += np.random.uniform(hi, lo)
        else:
            score += np.random.uniform(-8, 8)
        marks[subj] = round(_clip(score, 5, 100), 1)

    # Cross-contamination: 25% chance to boost subjects from OTHER class
    if np.random.random() < 0.25:
        other_labels = [l for l in affinity_map.keys() if l != label]
        if other_labels:
            other = np.random.choice(other_labels)
            other_boost = affinity_map[other].get("boost", {})
            for subj in list(other_boost.keys())[:2]:
                if subj in marks:
                    marks[subj] = min(marks[subj] + np.random.uniform(5, 15), 100)

    return marks


def _generate_interests(label: str, pattern_map: Dict) -> List[str]:
    pattern = pattern_map.get(label, {"primary": [], "secondary": [], "rare": []})
    interests = []

    if pattern["primary"]:
        interests.append(np.random.choice(pattern["primary"]))

    if len(pattern["primary"]) > 1 and np.random.random() < 0.6:
        remaining = [p for p in pattern["primary"] if p not in interests]
        if remaining:
            interests.append(np.random.choice(remaining))

    if pattern["secondary"] and np.random.random() < 0.4:
        sec = np.random.choice(pattern["secondary"])
        if sec not in interests:
            interests.append(sec)

    if pattern.get("rare") and np.random.random() < 0.15:
        rare = np.random.choice(pattern["rare"])
        if rare not in interests:
            interests.append(rare)

    return interests


def _generate_projects(
    label: str,
    base_ability: float,
    skill_pool_map: Dict,
    all_labels: List[str],
    n_projects: int = None,
) -> List[Dict[str, Any]]:
    pool = skill_pool_map.get(label, [])

    if n_projects is None:
        n_projects = np.random.choice([0, 1, 2, 3, 4], p=[0.05, 0.25, 0.35, 0.25, 0.10])

    if n_projects == 0:
        return []

    projects = []
    for _ in range(n_projects):
        n_skills = np.random.randint(2, min(7, len(pool) + 1))
        skills = list(np.random.choice(pool, size=min(n_skills, len(pool)), replace=False))

        # 30% chance to add cross-class skills
        if np.random.random() < 0.30:
            other_labels = [l for l in all_labels if l != label]
            if other_labels:
                other = np.random.choice(other_labels)
                other_pool = skill_pool_map.get(other, [])
                if other_pool:
                    cross_skill = np.random.choice(other_pool)
                    if cross_skill not in skills:
                        skills.append(cross_skill)

        complexity = _clip(base_ability / 100 * 0.5 + np.random.uniform(0.1, 0.5), 0.1, 1.0)

        projects.append({
            "title": f"Project {len(projects) + 1}",
            "description": f"A project using {', '.join(skills[:3])}",
            "extracted_skills": skills,
            "programming_languages": [],
            "frameworks": [],
            "tools": [],
            "technologies": [],
            "key_achievements": [],
            "learnings": [],
            "complexity_score": round(complexity, 2),
            "is_team_project": np.random.random() < 0.4,
            "github_url": "https://github.com/x/y" if np.random.random() < 0.3 else "",
            "demo_url": "" if np.random.random() > 0.15 else "https://demo.com",
        })

    return projects


# ═══════════════════════════════════════════════════════════════════
#  ELECTIVE DATASET GENERATORS
# ═══════════════════════════════════════════════════════════════════

def generate_pec_dataset(n_per_class: int = 600) -> List[Dict[str, Any]]:
    """Generate Program Elective training data."""
    dataset = []

    for label in PEC_LABELS:
        for _ in range(n_per_class):
            arch_name, arch_cfg = _sample_archetype()
            base_ability = np.random.uniform(*arch_cfg["ability"])
            consistency = arch_cfg["consistency"] + np.random.uniform(-0.1, 0.1)
            consistency = np.clip(consistency, 0.15, 0.95)

            marks = _generate_elective_marks(label, base_ability, consistency, PEC_AFFINITY)
            interests = _generate_interests(label, PEC_INTEREST_PATTERNS)
            projects = _generate_projects(label, base_ability, PEC_PROJECT_SKILLS, PEC_LABELS)

            dataset.append({
                "marks": marks, "interests": interests,
                "projects": projects, "label": label,
            })

    # Add hard/ambiguous samples (12%)
    n_hard = int(n_per_class * 0.12)
    for label in PEC_LABELS:
        for _ in range(n_hard):
            base_ability = np.random.uniform(40, 65)
            consistency = 0.35 + np.random.uniform(0, 0.25)

            marks = _generate_elective_marks(label, base_ability, consistency, PEC_AFFINITY)
            other_label = np.random.choice([l for l in PEC_LABELS if l != label])
            other_marks = _generate_elective_marks(other_label, base_ability, consistency, PEC_AFFINITY)

            for subj in marks:
                if np.random.random() < 0.3:
                    marks[subj] = round((marks[subj] * 0.6 + other_marks[subj] * 0.4), 1)

            interests = _generate_interests(label, PEC_INTEREST_PATTERNS)
            other_interests = _generate_interests(other_label, PEC_INTEREST_PATTERNS)
            if other_interests and np.random.random() < 0.5:
                interests = list(set(interests + other_interests[:1]))

            projects = _generate_projects(label, base_ability, PEC_PROJECT_SKILLS, PEC_LABELS,
                                          n_projects=np.random.randint(1, 3))

            dataset.append({
                "marks": marks, "interests": interests,
                "projects": projects, "label": label,
            })

    np.random.shuffle(dataset)
    return dataset


def generate_oec_dataset(n_per_class: int = 500) -> List[Dict[str, Any]]:
    """Generate Open Elective training data."""
    dataset = []

    for label in OEC_LABELS:
        for _ in range(n_per_class):
            arch_name, arch_cfg = _sample_archetype()
            base_ability = np.random.uniform(*arch_cfg["ability"])
            consistency = arch_cfg["consistency"] + np.random.uniform(-0.1, 0.1)
            consistency = np.clip(consistency, 0.15, 0.95)

            marks = _generate_elective_marks(label, base_ability, consistency, OEC_AFFINITY)
            interests = _generate_interests(label, OEC_INTEREST_PATTERNS)
            projects = _generate_projects(label, base_ability, OEC_PROJECT_SKILLS, OEC_LABELS)

            dataset.append({
                "marks": marks, "interests": interests,
                "projects": projects, "label": label,
            })

    # Hard samples (10%)
    n_hard = int(n_per_class * 0.10)
    for label in OEC_LABELS:
        for _ in range(n_hard):
            base_ability = np.random.uniform(40, 65)
            consistency = 0.35 + np.random.uniform(0, 0.25)

            marks = _generate_elective_marks(label, base_ability, consistency, OEC_AFFINITY)
            other_label = np.random.choice([l for l in OEC_LABELS if l != label])
            other_marks = _generate_elective_marks(other_label, base_ability, consistency, OEC_AFFINITY)

            for subj in marks:
                if np.random.random() < 0.3:
                    marks[subj] = round((marks[subj] * 0.6 + other_marks[subj] * 0.4), 1)

            interests = _generate_interests(label, OEC_INTEREST_PATTERNS)
            projects = _generate_projects(label, base_ability, OEC_PROJECT_SKILLS, OEC_LABELS,
                                          n_projects=np.random.randint(0, 2))

            dataset.append({
                "marks": marks, "interests": interests,
                "projects": projects, "label": label,
            })

    np.random.shuffle(dataset)
    return dataset


# ═══════════════════════════════════════════════════════════════════
#  PERFORMANCE PREDICTOR DATA
# ═══════════════════════════════════════════════════════════════════

def generate_subject_score(
    base_ability: float, difficulty: float,
    is_practical: bool, consistency: float = 0.7,
) -> float:
    difficulty_penalty = difficulty * (100 - base_ability) * 0.4
    practical_bonus = 8 if is_practical else 0
    mean_score = base_ability - difficulty_penalty + practical_bonus
    noise_std = (1 - consistency) * 18 + 5
    return round(_sample_clipped_normal(mean_score, noise_std, 2, 100), 1)


def marks_to_grade_points(marks: float) -> float:
    if marks >= 80: return 10.0
    elif marks >= 75: return 9.0
    elif marks >= 70: return 8.0
    elif marks >= 60: return 7.0
    elif marks >= 50: return 6.0
    elif marks >= 45: return 5.0
    elif marks >= 40: return 4.0
    else: return 0.0


def calculate_sgpa(scores: List[float], credits: List[int]) -> float:
    total_cp = sum(marks_to_grade_points(s) * c for s, c in zip(scores, credits))
    total_c = sum(credits)
    return round(total_cp / total_c, 2) if total_c > 0 else 0.0


def generate_performance_dataset(n_students: int = 6000) -> pd.DataFrame:
    """Generate performance prediction training data."""
    records = []
    semesters = [3, 4, 5, 6, 7]
    sem_weights = [0.28, 0.28, 0.22, 0.12, 0.10]

    for sid in range(n_students):
        arch_name, cfg = _sample_archetype()
        base_ability = _sample_uniform(*cfg["ability"])
        consistency = cfg["consistency"] + np.random.uniform(-0.1, 0.1)
        consistency = np.clip(consistency, 0.15, 0.95)

        semester = int(np.random.choice(semesters, p=sem_weights))
        subjects = SUBJECTS_BY_SEMESTER[semester]

        attend_mean = _sample_uniform(*cfg["attend"])
        assign_mean = _sample_uniform(*cfg["assign"])
        study_hrs = _sample_uniform(*cfg["study"])

        scores, attendances, assignments, quizzes, is_practicals = [], [], [], [], []

        for subj in subjects:
            score = generate_subject_score(base_ability, subj["difficulty"], subj["is_practical"], consistency)
            attend = _sample_clipped_normal(attend_mean, 8, 5, 100)
            assign = _sample_clipped_normal(assign_mean, 10, 0, 100)
            quiz = _sample_clipped_normal(score + np.random.normal(0, 8), 10, 0, 100)

            scores.append(score)
            attendances.append(attend)
            assignments.append(assign)
            quizzes.append(quiz)
            is_practicals.append(subj["is_practical"])

        credits = [s["credits"] for s in subjects]
        current_sgpa = calculate_sgpa(scores, credits)

        # Previous semester
        prev_sem = semester - 1
        prev_subjects = SUBJECTS_BY_SEMESTER.get(prev_sem, subjects)

        if arch_name == "improving":
            prev_ability = base_ability - np.random.uniform(12, 22)
        elif arch_name == "inconsistent":
            prev_ability = base_ability + np.random.uniform(-20, 20)
        else:
            prev_ability = base_ability + np.random.normal(0, 5)
        prev_ability = np.clip(prev_ability, 5, 100)

        prev_scores = [generate_subject_score(prev_ability, s["difficulty"], s["is_practical"], consistency)
                       for s in prev_subjects]
        prev_credits = [s["credits"] for s in prev_subjects]
        prev_sgpa = calculate_sgpa(prev_scores, prev_credits)

        # CGPA
        if arch_name == "improving":
            cgpa = prev_sgpa * 0.4 + current_sgpa * 0.6 + np.random.normal(0, 0.2)
        else:
            cgpa = (prev_sgpa + current_sgpa) / 2 + np.random.normal(0, 0.3)
        cgpa = np.clip(cgpa, 0, 10)

        # Next semester (TARGET)
        sgpa_trend = current_sgpa - prev_sgpa
        next_subjects = SUBJECTS_BY_SEMESTER.get(semester + 1, subjects)

        if arch_name == "improving":
            next_ability = base_ability + np.random.uniform(3, 10)
        elif arch_name == "failing":
            next_ability = base_ability + np.random.normal(-2, 5)
        elif arch_name == "inconsistent":
            next_ability = base_ability + np.random.uniform(-15, 15)
        else:
            effort = (study_hrs / 14) * 5
            attend_factor = (np.mean(attendances) - 70) / 30 * 3
            next_ability = base_ability + sgpa_trend * 2 + effort + attend_factor + np.random.normal(0, 4)
        next_ability = np.clip(next_ability, 5, 100)

        next_scores = [generate_subject_score(next_ability, s["difficulty"], s["is_practical"], consistency)
                       for s in next_subjects]
        next_credits = [s["credits"] for s in next_subjects]
        next_sgpa = calculate_sgpa(next_scores, next_credits)

        # Aggregated features
        scores_arr = np.array(scores)
        practical_mask = np.array(is_practicals)
        practical_avg = float(np.mean(scores_arr[practical_mask])) if practical_mask.any() else 0
        theory_avg = float(np.mean(scores_arr[~practical_mask])) if (~practical_mask).any() else 0

        lab_perf = _sample_clipped_normal(practical_avg + 5, 10, 0, 100) if practical_mask.any() else _sample_clipped_normal(base_ability * 0.8, 12, 0, 100)
        project_score = _sample_clipped_normal(base_ability * 0.8 + 10, 12, 0, 100)

        records.append({
            "student_id": f"STU_{sid:05d}", "archetype": arch_name, "semester": semester,
            "current_cgpa": round(cgpa, 2), "current_sgpa": round(current_sgpa, 2),
            "previous_sgpa": round(prev_sgpa, 2), "sgpa_trend": round(sgpa_trend, 2),
            "attendance": round(float(np.mean(attendances)), 1),
           # "assignment_completion": round(float(np.mean(assignments)), 1),
           # "quiz_average": round(float(np.mean(quizzes)), 1),
            "lab_performance": round(lab_perf, 1),
            "project_score": round(project_score, 1),
           # "study_hours": round(study_hrs, 1),
            "participation_score": round(_sample_clipped_normal(base_ability * 0.7 + 15, 15, 0, 100), 1),
            "extracurricular": round(_sample_clipped_normal(base_ability * 0.4 + 10, 20, 0, 100), 1),
            "dept_avg": round(_sample_clipped_normal(6.2, 0.8, 4.0, 8.5), 2),
            "num_subjects": len(subjects),
            "num_backlogs": int(np.sum(scores_arr < 40)),
            "num_strong_subjects": int(np.sum(scores_arr >= 70)),
            "num_weak_subjects": int(np.sum(scores_arr < 50)),
            "avg_subject_score": round(float(np.mean(scores_arr)), 1),
            "min_subject_score": round(float(np.min(scores_arr)), 1),
            "max_subject_score": round(float(np.max(scores_arr)), 1),
            "std_subject_score": round(float(np.std(scores_arr)), 1),
            "practical_avg": round(practical_avg, 1), "theory_avg": round(theory_avg, 1),
            "credits_completed_ratio": round((semester - 1) * 20 / 160, 2),
            "next_sgpa": round(next_sgpa, 2),
        })

    return pd.DataFrame(records)


# ═══════════════════════════════════════════════════════════════════
#  WEAKNESS DETECTOR DATA
# ═══════════════════════════════════════════════════════════════════

def determine_severity(score, attendance, assignment, quiz_avg, difficulty):
    risk = 0.0
    if score < 25: risk += 50
    elif score < 35: risk += 42
    elif score < 45: risk += 33
    elif score < 55: risk += 24
    elif score < 65: risk += 15
    elif score < 75: risk += 7
    else: risk += 2

    if attendance < 40: risk += 20
    elif attendance < 55: risk += 15
    elif attendance < 65: risk += 10
    elif attendance < 75: risk += 5
    else: risk += 1

    if assignment < 30: risk += 15
    elif assignment < 50: risk += 10
    elif assignment < 70: risk += 5
    else: risk += 1

    if quiz_avg < 35: risk += 10
    elif quiz_avg < 50: risk += 6
    elif quiz_avg < 65: risk += 3
    else: risk += 1

    risk += difficulty * 5 + np.random.normal(0, 4)
    risk = np.clip(risk, 0, 100)

    if risk >= 72: severity = 4
    elif risk >= 55: severity = 3
    elif risk >= 38: severity = 2
    elif risk >= 22: severity = 1
    else: severity = 0

    needs_intervention = (severity >= 3) or (severity == 2 and np.random.random() < 0.3)
    return severity, needs_intervention


def generate_weakness_dataset(n_students: int = 4000) -> pd.DataFrame:
    """Generate weakness detection training data."""
    records = []
    semesters = [3, 4, 5, 6, 7]
    sem_weights = [0.28, 0.28, 0.22, 0.12, 0.10]

    for sid in range(n_students):
        arch_name, cfg = _sample_archetype()
        base_ability = _sample_uniform(*cfg["ability"])
        consistency = cfg["consistency"] + np.random.uniform(-0.1, 0.1)
        consistency = np.clip(consistency, 0.15, 0.95)

        semester = int(np.random.choice(semesters, p=sem_weights))
        subjects = SUBJECTS_BY_SEMESTER[semester]
        attend_mean = _sample_uniform(*cfg["attend"])
        assign_mean = _sample_uniform(*cfg["assign"])
        study_hrs = _sample_uniform(*cfg["study"])
        cgpa = _sample_clipped_normal(base_ability / 10, 0.8, 0, 10)
        class_avg = _sample_clipped_normal(55, 8, 30, 80)

        prev_subjects = SUBJECTS_BY_SEMESTER.get(semester - 1, [])
        prev_scores_map = {}
        for ps in prev_subjects:
            pa = np.clip(base_ability + np.random.normal(0, 6), 5, 100)
            prev_scores_map[ps["name"]] = generate_subject_score(pa, ps["difficulty"], ps["is_practical"], consistency)

        for subj in subjects:
            score = generate_subject_score(base_ability, subj["difficulty"], subj["is_practical"], consistency)
            attend = _sample_clipped_normal(attend_mean, 8, 5, 100)
            assign = _sample_clipped_normal(assign_mean, 10, 0, 100)
            quiz = _sample_clipped_normal(score + np.random.normal(0, 10), 10, 0, 100)
            lab_perf = _sample_clipped_normal(score + 8, 12, 0, 100) if subj["is_practical"] else _sample_clipped_normal(score - 5, 15, 0, 100)

            prereq_name = PREREQUISITE_MAP.get(subj["name"], "")
            prev_score = prev_scores_map.get(prereq_name, _sample_clipped_normal(base_ability * 0.9, 12, 5, 100))
            subj_study = _sample_clipped_normal(study_hrs * subj["credits"] / 3, 1.5, 0, 15)

            if arch_name == "improving": trend = 1
            elif arch_name in ("failing", "struggling"): trend = -1 if np.random.random() < 0.6 else 0
            elif arch_name == "inconsistent": trend = np.random.choice([-1, 0, 1])
            else: trend = np.random.choice([-1, 0, 1], p=[0.15, 0.55, 0.30])

            severity, needs_intervention = determine_severity(score, attend, assign, quiz, subj["difficulty"])

            records.append({
                "student_id": f"STU_{sid:05d}", "subject_name": subj["name"],
                "subject_code": subj["code"], "semester": semester, "archetype": arch_name,
                "subject_score": round(score, 1), "attendance": round(attend, 1),
                # "assignment_score": round(assign, 1), "quiz_average": round(quiz, 1),
                "lab_performance": round(lab_perf, 1),
                "previous_related_score": round(prev_score, 1),
                # "study_hours": round(subj_study, 1), "difficulty_factor": subj["difficulty"],
                "cgpa": round(cgpa, 2), "credits": subj["credits"],
                "is_practical": int(subj["is_practical"]),
                "class_avg_score": round(class_avg, 1),
                # "score_vs_class_avg": round(score - class_avg, 1),
                "trend_indicator": trend,
                "weakness_severity": severity,
                "needs_intervention": int(needs_intervention),
            })

    return pd.DataFrame(records)


# ═══════════════════════════════════════════════════════════════════
#  EXPORT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def save_elective_data(data: List[Dict], output_dir: str, prefix: str):
    """Save elective data as JSON and CSV."""
    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, f"{prefix}_training_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    csv_path = os.path.join(output_dir, f"{prefix}_training_data.csv")
    rows = []
    for sample in data:
        marks = sample["marks"]
        sorted_subj = sorted(marks.items(), key=lambda x: x[1], reverse=True)[:5]
        row = {
            "label": sample["label"],
            "n_interests": len(sample["interests"]),
            "n_projects": len(sample["projects"]),
            "interests": "|".join(sample["interests"]),
        }
        for i, (subj, score) in enumerate(sorted_subj):
            row[f"subj_{i+1}_name"] = subj
            row[f"subj_{i+1}_score"] = score
        if sample["projects"]:
            all_skills = []
            for p in sample["projects"]:
                all_skills.extend(p.get("extracted_skills", []))
            row["project_skills"] = "|".join(list(set(all_skills))[:10])
        else:
            row["project_skills"] = ""
        rows.append(row)

    pd.DataFrame(rows).to_csv(csv_path, index=False, encoding="utf-8")
    print(f"  Saved {len(data)} samples to {json_path}")


def print_dataset_stats(data, name: str):
    print(f"\n{'=' * 50}")
    print(f"  {name} Statistics")
    print(f"{'=' * 50}")
    if isinstance(data, list):
        print(f"  Total samples: {len(data)}")
        label_counts = Counter(d["label"] for d in data)
        print(f"  Labels: {dict(label_counts)}")
        all_scores = [s for d in data for s in d["marks"].values()]
        print(f"  Score range: {min(all_scores):.1f} - {max(all_scores):.1f}")
        print(f"  Score mean: {np.mean(all_scores):.1f} +/- {np.std(all_scores):.1f}")
    elif isinstance(data, pd.DataFrame):
        print(f"  Total records: {len(data):,}")
        if "archetype" in data.columns:
            print(f"  Archetypes: {dict(data['archetype'].value_counts())}")
    print(f"{'=' * 50}")


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Generate optimized training data")
    parser.add_argument("--pec", type=int, default=600, help="Samples per PEC class (default: 600)")
    parser.add_argument("--oec", type=int, default=500, help="Samples per OEC class (default: 500)")
    parser.add_argument("--perf", type=int, default=6000, help="Performance predictor samples (default: 6000)")
    parser.add_argument("--weak", type=int, default=4000, help="Weakness detector students (default: 4000)")
    parser.add_argument("--output-dir", type=str, default="scripts/training_data", help="Output directory")
    parser.add_argument("--skip-electives", action="store_true", help="Skip elective data generation")
    parser.add_argument("--skip-perf-weak", action="store_true", help="Skip performance/weakness data")
    args = parser.parse_args()

    print("Generating Optimized Training Data v2")
    print(f"  Output: {args.output_dir}")
    os.makedirs(args.output_dir, exist_ok=True)

    if not args.skip_electives:
        print(f"\n  PEC: {args.pec} x 4 = {args.pec * 4} samples")
        pec_data = generate_pec_dataset(args.pec)
        save_elective_data(pec_data, args.output_dir, "elective")
        print_dataset_stats(pec_data, "PEC")

        print(f"\n  OEC: {args.oec} x 5 = {args.oec * 5} samples")
        oec_data = generate_oec_dataset(args.oec)
        save_elective_data(oec_data, args.output_dir, "oe")
        print_dataset_stats(oec_data, "OEC")

    if not args.skip_perf_weak:
        print(f"\n  Performance: {args.perf} samples")
        perf_df = generate_performance_dataset(args.perf)
        perf_path = os.path.join(args.output_dir, "performance_training_data.csv")
        perf_df.to_csv(perf_path, index=False)
        print(f"  Saved {len(perf_df)} records to {perf_path}")
        print_dataset_stats(perf_df, "Performance")

        print(f"\n  Weakness: {args.weak} students")
        weak_df = generate_weakness_dataset(args.weak)
        weak_path = os.path.join(args.output_dir, "weakness_training_data.csv")
        weak_df.to_csv(weak_path, index=False)
        print(f"  Saved {len(weak_df)} records to {weak_path}")
        print_dataset_stats(weak_df, "Weakness")

    meta = {
        "generated_at": datetime.utcnow().isoformat(),
        "version": "2.0",
        "pec_per_class": args.pec,
        "oec_per_class": args.oec,
        "perf_samples": args.perf,
        "weak_students": args.weak,
    }
    with open(os.path.join(args.output_dir, "data_generation_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print("\nDone!")


if __name__ == "__main__":
    main()