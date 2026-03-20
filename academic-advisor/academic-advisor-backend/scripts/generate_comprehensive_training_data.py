# academic-advisor/academic-advisor-backend/scripts/generate_comprehensive_training_data.py
"""
Comprehensive Training Data Generator for Performance Predictor & Weakness Detector
====================================================================================
Generates realistic FCRIT IT student data with diverse score distributions:
  - Toppers, average, below-average, failing, improving, inconsistent students
  - Scores from 5 to 100 (not just 65-98)
  - Realistic correlations between attendance, scores, CGPA
  - Curriculum-aligned subjects with proper difficulty factors

Usage:
    python -m scripts.generate_comprehensive_training_data
    python -m scripts.generate_comprehensive_training_data --students 15000
    python -m scripts.generate_comprehensive_training_data --output-dir scripts/training_data
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

np.random.seed(42)

# ═══════════════════════════════════════════════════════════════════
#  CURRICULUM-ALIGNED SUBJECT DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

SUBJECTS_BY_SEMESTER: Dict[int, List[Dict[str, Any]]] = {
    3: [
        {"name": "Engineering Mathematics-III", "code": "MATH301", "credits": 4, "difficulty": 0.82, "is_practical": False, "category": "math"},
        {"name": "Data Structures and Algorithms", "code": "DSA301", "credits": 4, "difficulty": 0.68, "is_practical": False, "category": "core_cs"},
        {"name": "Database Management Systems", "code": "DBMS301", "credits": 4, "difficulty": 0.58, "is_practical": False, "category": "core_cs"},
        {"name": "Digital Logic & Design", "code": "DLDA301", "credits": 4, "difficulty": 0.65, "is_practical": False, "category": "hardware"},
        {"name": "Python Programming", "code": "PYTHON301", "credits": 2, "difficulty": 0.38, "is_practical": True, "category": "programming"},
        {"name": "DSA Laboratory", "code": "DSAL301", "credits": 1, "difficulty": 0.42, "is_practical": True, "category": "lab"},
    ],
    4: [
        {"name": "Engineering Mathematics-IV", "code": "MATH401", "credits": 4, "difficulty": 0.78, "is_practical": False, "category": "math"},
        {"name": "Operating Systems", "code": "OS401", "credits": 4, "difficulty": 0.72, "is_practical": False, "category": "core_cs"},
        {"name": "Computer Networks", "code": "CN401", "credits": 4, "difficulty": 0.67, "is_practical": False, "category": "core_cs"},
        {"name": "Software Engineering", "code": "SE401", "credits": 4, "difficulty": 0.50, "is_practical": False, "category": "core_cs"},
        {"name": "Microcontroller & Embedded Systems", "code": "MES401", "credits": 4, "difficulty": 0.75, "is_practical": False, "category": "hardware"},
        {"name": "Microcontroller Lab", "code": "MESL401", "credits": 1, "difficulty": 0.48, "is_practical": True, "category": "lab"},
        {"name": "Computer Networks Lab", "code": "CNL401", "credits": 1, "difficulty": 0.43, "is_practical": True, "category": "lab"},
    ],
    5: [
        {"name": "Automata Theory", "code": "ITPCC509", "credits": 4, "difficulty": 0.85, "is_practical": False, "category": "theory"},
        {"name": "Design & Analysis of Algorithms", "code": "ITPCC501", "credits": 3, "difficulty": 0.78, "is_practical": False, "category": "core_cs"},
        {"name": "Cloud Computing Laboratory", "code": "ITLBC506", "credits": 1, "difficulty": 0.44, "is_practical": True, "category": "lab"},
        {"name": "Mobile App Development Lab", "code": "ITLBC507", "credits": 1, "difficulty": 0.46, "is_practical": True, "category": "lab"},
    ],
    6: [
        {"name": "Cryptography & Network Security", "code": "ITPCC611", "credits": 4, "difficulty": 0.80, "is_practical": False, "category": "core_cs"},
        {"name": "Cryptography Lab", "code": "ITLBC608", "credits": 1, "difficulty": 0.48, "is_practical": True, "category": "lab"},
        {"name": "Data Science Laboratory", "code": "ITLBC609", "credits": 1, "difficulty": 0.40, "is_practical": True, "category": "lab"},
        {"name": "DevOps Laboratory", "code": "ITSBL603", "credits": 2, "difficulty": 0.46, "is_practical": True, "category": "lab"},
    ],
    7: [
        {"name": "Artificial Intelligence", "code": "ITPCC710", "credits": 4, "difficulty": 0.70, "is_practical": False, "category": "core_cs"},
        {"name": "AI Laboratory", "code": "ITLBC711", "credits": 1, "difficulty": 0.42, "is_practical": True, "category": "lab"},
        {"name": "Data Analytics Lab", "code": "ITLBC712", "credits": 1, "difficulty": 0.38, "is_practical": True, "category": "lab"},
    ],
}

# Prerequisite chains (subject → prerequisite subject category)
PREREQUISITE_MAP = {
    "Engineering Mathematics-IV": "Engineering Mathematics-III",
    "Design & Analysis of Algorithms": "Data Structures and Algorithms",
    "Cryptography & Network Security": "Computer Networks",
    "Artificial Intelligence": "Engineering Mathematics-III",
    "Automata Theory": "Engineering Mathematics-III",
}

# ═══════════════════════════════════════════════════════════════════
#  STUDENT ARCHETYPES
# ═══════════════════════════════════════════════════════════════════

ARCHETYPES = {
    "topper":       {"pct": 0.10, "ability": (82, 97), "attend": (90, 100), "assign": (88, 100), "study": (8, 14), "consistency": 0.90},
    "strong":       {"pct": 0.18, "ability": (68, 83), "attend": (80, 96),  "assign": (75, 95),  "study": (5, 10), "consistency": 0.80},
    "above_avg":    {"pct": 0.15, "ability": (58, 70), "attend": (72, 88),  "assign": (60, 85),  "study": (4, 8),  "consistency": 0.72},
    "average":      {"pct": 0.22, "ability": (45, 60), "attend": (62, 82),  "assign": (48, 75),  "study": (2, 6),  "consistency": 0.65},
    "below_avg":    {"pct": 0.15, "ability": (32, 48), "attend": (48, 70),  "assign": (30, 60),  "study": (1, 4),  "consistency": 0.55},
    "struggling":   {"pct": 0.10, "ability": (18, 35), "attend": (30, 58),  "assign": (12, 42),  "study": (0, 3),  "consistency": 0.45},
    "failing":      {"pct": 0.04, "ability": (5, 22),  "attend": (10, 40),  "assign": (5, 25),   "study": (0, 2),  "consistency": 0.35},
    "improving":    {"pct": 0.03, "ability": (50, 68), "attend": (72, 92),  "assign": (65, 88),  "study": (5, 10), "consistency": 0.60},
    "inconsistent": {"pct": 0.03, "ability": (40, 75), "attend": (45, 90),  "assign": (30, 90),  "study": (1, 10), "consistency": 0.30},
}


# ═══════════════════════════════════════════════════════════════════
#  SCORE GENERATION HELPERS
# ═══════════════════════════════════════════════════════════════════

def _sample_uniform(low: float, high: float) -> float:
    return np.random.uniform(low, high)


def _sample_clipped_normal(mean: float, std: float, low: float = 0, high: float = 100) -> float:
    return float(np.clip(np.random.normal(mean, std), low, high))


def generate_subject_score(
    base_ability: float,
    difficulty: float,
    is_practical: bool,
    consistency: float = 0.7,
) -> float:
    """
    Generate a realistic subject score.
    
    - Hard subjects with low ability → very low scores
    - Practical subjects are generally easier
    - Consistency affects noise level
    """
    # Difficulty effect: harder subjects pull score down more for weaker students
    difficulty_penalty = difficulty * (100 - base_ability) * 0.4
    
    # Practical subjects get a boost
    practical_bonus = 8 if is_practical else 0
    
    # Base score
    mean_score = base_ability - difficulty_penalty + practical_bonus
    
    # Noise inversely proportional to consistency
    noise_std = (1 - consistency) * 18 + 5
    
    score = _sample_clipped_normal(mean_score, noise_std, 2, 100)
    return round(score, 1)


def marks_to_grade_points(marks: float) -> float:
    """Convert marks (0-100) to grade points (0-10) per Mumbai University system."""
    if marks >= 80: return 10.0
    elif marks >= 75: return 9.0
    elif marks >= 70: return 8.0
    elif marks >= 60: return 7.0
    elif marks >= 50: return 6.0
    elif marks >= 45: return 5.0
    elif marks >= 40: return 4.0
    else: return 0.0  # Fail


def calculate_sgpa(scores: List[float], credits: List[int]) -> float:
    """Calculate SGPA from marks and credit weights."""
    total_credit_points = 0.0
    total_credits = 0
    for score, credit in zip(scores, credits):
        gp = marks_to_grade_points(score)
        total_credit_points += gp * credit
        total_credits += credit
    if total_credits == 0:
        return 0.0
    return round(total_credit_points / total_credits, 2)


def determine_severity(
    score: float,
    attendance: float,
    assignment: float,
    quiz_avg: float,
    difficulty: float,
) -> Tuple[int, bool]:
    """
    Determine weakness severity with realistic noise.
    
    Returns (severity_int, needs_intervention)
    severity: 0=none, 1=low, 2=medium, 3=high, 4=critical
    """
    # Composite risk score (0-100, higher = more risk)
    risk = 0.0
    
    # Score is primary factor (50% weight)
    if score < 25:
        risk += 50
    elif score < 35:
        risk += 42
    elif score < 45:
        risk += 33
    elif score < 55:
        risk += 24
    elif score < 65:
        risk += 15
    elif score < 75:
        risk += 7
    else:
        risk += 2
    
    # Attendance (20% weight)
    if attendance < 40:
        risk += 20
    elif attendance < 55:
        risk += 15
    elif attendance < 65:
        risk += 10
    elif attendance < 75:
        risk += 5
    else:
        risk += 1
    
    # Assignment completion (15% weight)
    if assignment < 30:
        risk += 15
    elif assignment < 50:
        risk += 10
    elif assignment < 70:
        risk += 5
    else:
        risk += 1
    
    # Quiz average (10% weight)
    if quiz_avg < 35:
        risk += 10
    elif quiz_avg < 50:
        risk += 6
    elif quiz_avg < 65:
        risk += 3
    else:
        risk += 1
    
    # Difficulty modulator (5% weight) — harder subjects are more likely to be a weakness
    risk += difficulty * 5
    
    # Add noise (±8 points)
    risk += np.random.normal(0, 4)
    risk = np.clip(risk, 0, 100)
    
    # Map to severity
    if risk >= 72:
        severity = 4  # critical
    elif risk >= 55:
        severity = 3  # high
    elif risk >= 38:
        severity = 2  # medium
    elif risk >= 22:
        severity = 1  # low
    else:
        severity = 0  # none
    
    # Needs intervention: critical/high always, medium sometimes
    needs_intervention = (severity >= 3) or (severity == 2 and np.random.random() < 0.3)
    
    return severity, needs_intervention


# ═══════════════════════════════════════════════════════════════════
#  MAIN DATA GENERATORS
# ═══════════════════════════════════════════════════════════════════

def generate_performance_dataset(n_students: int = 12000) -> pd.DataFrame:
    """
    Generate performance prediction training data.
    Each row = one student snapshot with current features → next_sgpa target.
    """
    records = []
    archetype_names = list(ARCHETYPES.keys())
    archetype_probs = [ARCHETYPES[a]["pct"] for a in archetype_names]
    # Normalize
    total = sum(archetype_probs)
    archetype_probs = [p / total for p in archetype_probs]
    
    semesters = [3, 4, 5, 6, 7]
    sem_weights = [0.28, 0.28, 0.22, 0.12, 0.10]
    
    for sid in range(n_students):
        archetype = np.random.choice(archetype_names, p=archetype_probs)
        cfg = ARCHETYPES[archetype]
        
        base_ability = _sample_uniform(*cfg["ability"])
        consistency = cfg["consistency"] + np.random.uniform(-0.1, 0.1)
        consistency = np.clip(consistency, 0.15, 0.95)
        
        semester = int(np.random.choice(semesters, p=sem_weights))
        subjects = SUBJECTS_BY_SEMESTER[semester]
        
        # Generate attendance and other metrics
        attend_mean = _sample_uniform(*cfg["attend"])
        assign_mean = _sample_uniform(*cfg["assign"])
        study_hrs = _sample_uniform(*cfg["study"])
        
        # Per-subject scores
        scores = []
        attendances = []
        assignments = []
        quizzes = []
        is_practicals = []
        
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
        
        # Generate previous semester data
        prev_sem = semester - 1
        if prev_sem in SUBJECTS_BY_SEMESTER:
            prev_subjects = SUBJECTS_BY_SEMESTER[prev_sem]
        else:
            prev_subjects = subjects  # fallback
        
        if archetype == "improving":
            prev_ability = base_ability - np.random.uniform(12, 22)
        elif archetype == "inconsistent":
            prev_ability = base_ability + np.random.uniform(-20, 20)
        else:
            prev_ability = base_ability + np.random.normal(0, 5)
        prev_ability = np.clip(prev_ability, 5, 100)
        
        prev_scores = [
            generate_subject_score(prev_ability, s["difficulty"], s["is_practical"], consistency)
            for s in prev_subjects
        ]
        prev_credits = [s["credits"] for s in prev_subjects]
        prev_sgpa = calculate_sgpa(prev_scores, prev_credits)
        
        # Current CGPA (weighted average of current and prev semesters roughly)
        if archetype == "improving":
            cgpa_weight = 0.4  # past pulls it down
            cgpa = prev_sgpa * cgpa_weight + current_sgpa * (1 - cgpa_weight) + np.random.normal(0, 0.2)
        else:
            cgpa = (prev_sgpa + current_sgpa) / 2 + np.random.normal(0, 0.3)
        cgpa = np.clip(cgpa, 0, 10)
        
        # ──────── Generate NEXT semester SGPA (TARGET) ────────
        next_sem = semester + 1
        if next_sem in SUBJECTS_BY_SEMESTER:
            next_subjects = SUBJECTS_BY_SEMESTER[next_sem]
        else:
            next_subjects = subjects
        
        # Next ability is influenced by current performance + trend + effort
        sgpa_trend = current_sgpa - prev_sgpa
        
        if archetype == "improving":
            next_ability = base_ability + np.random.uniform(3, 10)
        elif archetype == "failing":
            next_ability = base_ability + np.random.normal(-2, 5)
        elif archetype == "inconsistent":
            next_ability = base_ability + np.random.uniform(-15, 15)
        else:
            effort_factor = (study_hrs / 14) * 5  # studying more → slight improvement
            attend_factor = (np.mean(attendances) - 70) / 30 * 3  # good attendance → slight boost
            next_ability = base_ability + sgpa_trend * 2 + effort_factor + attend_factor + np.random.normal(0, 4)
        
        next_ability = np.clip(next_ability, 5, 100)
        
        next_scores = [
            generate_subject_score(next_ability, s["difficulty"], s["is_practical"], consistency)
            for s in next_subjects
        ]
        next_credits = [s["credits"] for s in next_subjects]
        next_sgpa = calculate_sgpa(next_scores, next_credits)
        
        # Aggregated features
        scores_arr = np.array(scores)
        attend_arr = np.array(attendances)
        assign_arr = np.array(assignments)
        quiz_arr = np.array(quizzes)
        practical_mask = np.array(is_practicals)
        
        num_backlogs = int(np.sum(scores_arr < 40))
        num_strong = int(np.sum(scores_arr >= 70))
        num_weak = int(np.sum(scores_arr < 50))
        
        practical_avg = float(np.mean(scores_arr[practical_mask])) if practical_mask.any() else 0
        theory_avg = float(np.mean(scores_arr[~practical_mask])) if (~practical_mask).any() else 0
        
        dept_avg = _sample_clipped_normal(6.2, 0.8, 4.0, 8.5)
        participation = _sample_clipped_normal(base_ability * 0.7 + 15, 15, 0, 100)
        extracurricular = _sample_clipped_normal(base_ability * 0.4 + 10, 20, 0, 100)
        lab_perf = _sample_clipped_normal(practical_avg + 5, 10, 0, 100) if practical_mask.any() else _sample_clipped_normal(base_ability * 0.8, 12, 0, 100)
        project_score = _sample_clipped_normal(base_ability * 0.8 + 10, 12, 0, 100)
        
        records.append({
            "student_id": f"STU_{sid:05d}",
            "archetype": archetype,
            "semester": semester,
            # ── Core features ──
            "current_cgpa": round(cgpa, 2),
            "current_sgpa": round(current_sgpa, 2),
            "previous_sgpa": round(prev_sgpa, 2),
            "sgpa_trend": round(sgpa_trend, 2),
            "attendance": round(float(np.mean(attend_arr)), 1),
            "assignment_completion": round(float(np.mean(assign_arr)), 1),
            "quiz_average": round(float(np.mean(quiz_arr)), 1),
            "lab_performance": round(lab_perf, 1),
            "project_score": round(project_score, 1),
            "study_hours": round(study_hrs, 1),
            "participation_score": round(participation, 1),
            "extracurricular": round(extracurricular, 1),
            "dept_avg": round(dept_avg, 2),
            # ── Aggregated subject features ──
            "num_subjects": len(subjects),
            "num_backlogs": num_backlogs,
            "num_strong_subjects": num_strong,
            "num_weak_subjects": num_weak,
            "avg_subject_score": round(float(np.mean(scores_arr)), 1),
            "min_subject_score": round(float(np.min(scores_arr)), 1),
            "max_subject_score": round(float(np.max(scores_arr)), 1),
            "std_subject_score": round(float(np.std(scores_arr)), 1),
            "practical_avg": round(practical_avg, 1),
            "theory_avg": round(theory_avg, 1),
            "credits_completed_ratio": round((semester - 1) * 20 / 160, 2),
            # ── TARGET ──
            "next_sgpa": round(next_sgpa, 2),
        })
    
    return pd.DataFrame(records)


def generate_weakness_dataset(n_students: int = 10000) -> pd.DataFrame:
    """
    Generate weakness detection training data.
    Each row = one student-subject pair with features → severity + intervention targets.
    """
    records = []
    archetype_names = list(ARCHETYPES.keys())
    archetype_probs = [ARCHETYPES[a]["pct"] for a in archetype_names]
    total = sum(archetype_probs)
    archetype_probs = [p / total for p in archetype_probs]
    
    semesters = [3, 4, 5, 6, 7]
    sem_weights = [0.28, 0.28, 0.22, 0.12, 0.10]
    
    for sid in range(n_students):
        archetype = np.random.choice(archetype_names, p=archetype_probs)
        cfg = ARCHETYPES[archetype]
        
        base_ability = _sample_uniform(*cfg["ability"])
        consistency = cfg["consistency"] + np.random.uniform(-0.1, 0.1)
        consistency = np.clip(consistency, 0.15, 0.95)
        
        semester = int(np.random.choice(semesters, p=sem_weights))
        subjects = SUBJECTS_BY_SEMESTER[semester]
        
        attend_mean = _sample_uniform(*cfg["attend"])
        assign_mean = _sample_uniform(*cfg["assign"])
        study_hrs = _sample_uniform(*cfg["study"])
        
        # Overall CGPA for this student
        cgpa = _sample_clipped_normal(base_ability / 10, 0.8, 0, 10)
        
        # Class average for normalization
        class_avg = _sample_clipped_normal(55, 8, 30, 80)
        
        # Generate previous semester scores for prerequisite lookup
        prev_sem = semester - 1
        prev_subjects = SUBJECTS_BY_SEMESTER.get(prev_sem, [])
        prev_scores_map = {}
        for ps in prev_subjects:
            prev_ability = base_ability + np.random.normal(0, 6)
            prev_scores_map[ps["name"]] = generate_subject_score(
                np.clip(prev_ability, 5, 100), ps["difficulty"], ps["is_practical"], consistency
            )
        
        for subj in subjects:
            score = generate_subject_score(base_ability, subj["difficulty"], subj["is_practical"], consistency)
            attend = _sample_clipped_normal(attend_mean, 8, 5, 100)
            assign = _sample_clipped_normal(assign_mean, 10, 0, 100)
            quiz = _sample_clipped_normal(score + np.random.normal(0, 10), 10, 0, 100)
            lab_perf = _sample_clipped_normal(score + 8, 12, 0, 100) if subj["is_practical"] else _sample_clipped_normal(score - 5, 15, 0, 100)
            
            # Previous related score
            prereq_name = PREREQUISITE_MAP.get(subj["name"], "")
            prev_score = prev_scores_map.get(prereq_name, _sample_clipped_normal(base_ability * 0.9, 12, 5, 100))
            
            # Subject-specific study hours
            subj_study = _sample_clipped_normal(study_hrs * subj["credits"] / 3, 1.5, 0, 15)
            
            # Score vs class average
            score_vs_avg = score - class_avg
            
            # Trend indicator: -1 declining, 0 stable, 1 improving
            if archetype == "improving":
                trend = 1
            elif archetype in ("failing", "struggling"):
                trend = -1 if np.random.random() < 0.6 else 0
            elif archetype == "inconsistent":
                trend = np.random.choice([-1, 0, 1])
            else:
                trend = np.random.choice([-1, 0, 1], p=[0.15, 0.55, 0.30])
            
            # ── Derive targets ──
            severity, needs_intervention = determine_severity(
                score, attend, assign, quiz, subj["difficulty"]
            )
            
            records.append({
                "student_id": f"STU_{sid:05d}",
                "subject_name": subj["name"],
                "subject_code": subj["code"],
                "semester": semester,
                "archetype": archetype,
                # ── Features ──
                "subject_score": round(score, 1),
                "attendance": round(attend, 1),
                "assignment_score": round(assign, 1),
                "quiz_average": round(quiz, 1),
                "lab_performance": round(lab_perf, 1),
                "previous_related_score": round(prev_score, 1),
                "study_hours": round(subj_study, 1),
                "difficulty_factor": subj["difficulty"],
                "cgpa": round(cgpa, 2),
                "credits": subj["credits"],
                "is_practical": int(subj["is_practical"]),
                "class_avg_score": round(class_avg, 1),
                "score_vs_class_avg": round(score_vs_avg, 1),
                "trend_indicator": trend,
                # ── Targets ──
                "weakness_severity": severity,
                "needs_intervention": int(needs_intervention),
            })
    
    return pd.DataFrame(records)


def print_dataset_stats(df: pd.DataFrame, name: str):
    """Print comprehensive statistics about generated dataset."""
    print(f"\n{'═' * 60}")
    print(f"  📊 {name} Dataset Statistics")
    print(f"{'═' * 60}")
    print(f"  Total records:   {len(df):,}")
    print(f"  Columns:         {len(df.columns)}")
    
    if "archetype" in df.columns:
        print(f"\n  Archetype Distribution:")
        for arch, count in df["archetype"].value_counts().items():
            pct = count / len(df) * 100
            bar = "█" * int(pct / 2)
            print(f"    {arch:<14} {count:>6,} ({pct:5.1f}%) {bar}")
    
    if "next_sgpa" in df.columns:
        print(f"\n  Target (next_sgpa) Distribution:")
        print(f"    Mean: {df['next_sgpa'].mean():.2f}  Std: {df['next_sgpa'].std():.2f}")
        print(f"    Min:  {df['next_sgpa'].min():.2f}  Max: {df['next_sgpa'].max():.2f}")
        bins = [(0, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10.01)]
        for lo, hi in bins:
            count = ((df["next_sgpa"] >= lo) & (df["next_sgpa"] < hi)).sum()
            pct = count / len(df) * 100
            bar = "█" * int(pct / 2)
            print(f"    SGPA {lo:.0f}-{hi:.0f}: {count:>5,} ({pct:5.1f}%) {bar}")
    
    if "weakness_severity" in df.columns:
        print(f"\n  Severity Distribution:")
        sev_names = {0: "none", 1: "low", 2: "medium", 3: "high", 4: "critical"}
        for sev_int, sev_name in sev_names.items():
            count = (df["weakness_severity"] == sev_int).sum()
            pct = count / len(df) * 100
            bar = "█" * int(pct / 2)
            print(f"    {sev_name:<10} {count:>6,} ({pct:5.1f}%) {bar}")
    
    if "subject_score" in df.columns:
        print(f"\n  Score Distribution:")
        print(f"    Mean: {df['subject_score'].mean():.1f}  Std: {df['subject_score'].std():.1f}")
        bins = [(0, 25), (25, 40), (40, 50), (50, 60), (60, 70), (70, 85), (85, 101)]
        for lo, hi in bins:
            count = ((df["subject_score"] >= lo) & (df["subject_score"] < hi)).sum()
            pct = count / len(df) * 100
            bar = "█" * int(pct)
            print(f"    {lo:>3}-{hi-1:>3}: {count:>6,} ({pct:5.1f}%) {bar}")
    
    print(f"{'═' * 60}\n")


def main():
    parser = argparse.ArgumentParser(description="Generate training data")
    parser.add_argument("--students", type=int, default=12000, help="Number of students for performance data")
    parser.add_argument("--weakness-students", type=int, default=10000, help="Number of students for weakness data")
    parser.add_argument("--output-dir", type=str, default="scripts/training_data", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    np.random.seed(args.seed)
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("🎓 Generating Comprehensive Training Data for Academic Advisor")
    print(f"   Output directory: {args.output_dir}")
    
    # Generate performance data
    print(f"\n📈 Generating performance prediction data ({args.students:,} students)...")
    perf_df = generate_performance_dataset(args.students)
    perf_path = os.path.join(args.output_dir, "performance_training_data.csv")
    perf_df.to_csv(perf_path, index=False)
    print(f"   ✅ Saved to {perf_path}")
    print_dataset_stats(perf_df, "Performance Prediction")
    
    # Generate weakness data
    print(f"🔍 Generating weakness detection data ({args.weakness_students:,} students)...")
    weak_df = generate_weakness_dataset(args.weakness_students)
    weak_path = os.path.join(args.output_dir, "weakness_training_data.csv")
    weak_df.to_csv(weak_path, index=False)
    print(f"   ✅ Saved to {weak_path}")
    print_dataset_stats(weak_df, "Weakness Detection")
    
    # Save metadata
    meta = {
        "performance_records": len(perf_df),
        "weakness_records": len(weak_df),
        "seed": args.seed,
        "archetypes": list(ARCHETYPES.keys()),
        "semesters": [3, 4, 5, 6, 7],
        "performance_features": [c for c in perf_df.columns if c not in ("student_id", "archetype", "next_sgpa")],
        "weakness_features": [c for c in weak_df.columns if c not in ("student_id", "subject_name", "subject_code", "archetype", "weakness_severity", "needs_intervention")],
    }
    meta_path = os.path.join(args.output_dir, "data_generation_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"📋 Metadata saved to {meta_path}")
    print("\n✅ Data generation complete!")

        # ═══════════════════════════════════════════════════════════════
    # ELECTIVE RECOMMENDATION DATA
    # ═══════════════════════════════════════════════════════════════
    print(f"\n🎯 Generating elective recommendation data (4 × {args.students // 4} per class)...")

    from app.ml.utils.training import generate_training_dataset, generate_training_csv

    elective_data = generate_training_dataset(
        n_samples_per_class=max(args.students // 4, 1500),
        include_hard_samples=True,
    )

    # Save as CSV for review
    elective_csv_path = os.path.join(args.output_dir, "elective_training_data.csv")
    generate_training_csv(elective_data, elective_csv_path)

    # Save as JSON for direct model consumption
    elective_json_path = os.path.join(args.output_dir, "elective_training_data.json")

    # Clean internal keys before saving
    clean_data = []
    for sample in elective_data:
        clean_data.append({
            "marks": sample["marks"],
            "interests": sample["interests"],
            "projects": sample["projects"],
            "label": sample["label"],
        })

    with open(elective_json_path, "w") as f:
        json.dump(clean_data, f, indent=2)
    print(f"   ✅ Saved to {elective_json_path}")

    # Print elective data stats
    from collections import Counter
    label_counts = Counter(d["label"] for d in elective_data)
    all_scores = [s for d in elective_data for s in d["marks"].values()]

    print(f"\n{'═' * 60}")
    print(f"  📊 Elective Training Data Statistics")
    print(f"{'═' * 60}")
    print(f"  Total samples: {len(elective_data):,}")
    print(f"  Labels: {dict(label_counts)}")
    print(f"  Score range: {min(all_scores):.1f} – {max(all_scores):.1f}")
    print(f"  Score mean: {np.mean(all_scores):.1f} ± {np.std(all_scores):.1f}")

    # Score distribution
    bins = [(0, 25), (25, 40), (40, 50), (50, 60), (60, 75), (75, 90), (90, 101)]
    for lo, hi in bins:
        count = sum(1 for s in all_scores if lo <= s < hi)
        pct = count / len(all_scores) * 100
        bar = "█" * int(pct)
        print(f"    {lo:>3}-{hi-1:>3}: {count:>6} ({pct:5.1f}%) {bar}")
    print(f"{'═' * 60}")

    # Update metadata
    meta["elective_records"] = len(elective_data)
    meta["elective_labels"] = list(label_counts.keys())
    meta["elective_score_range"] = [round(min(all_scores), 1), round(max(all_scores), 1)]
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)


if __name__ == "__main__":
    main()