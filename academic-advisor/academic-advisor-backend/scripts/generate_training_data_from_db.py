# academic-advisor-backend/scripts/generate_training_data_from_db.py
"""
Generate ML Training Data from Real Student Marks (MongoDB)
===========================================================
Replaces synthetic data in performance_training_data.csv and
weakness_training_data.csv with data derived from real uploaded marks.

Elective training data remains synthetic because we have no ground-truth
labels for which elective a student "should" choose.

Usage:
    python -m scripts.generate_training_data_from_db
    python -m scripts.generate_training_data_from_db --min-students 50
    python -m scripts.generate_training_data_from_db --blend 0.4
"""

import asyncio
import argparse
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training_data")

# ══════════════════════════════════════════════════════════════
# FEATURE DEFINITIONS
# Must match EXACTLY what train_performance_weakness_models.py uses
# ══════════════════════════════════════════════════════════════

PERFORMANCE_FEATURES = [
    "current_cgpa", "current_sgpa", "previous_sgpa", "sgpa_trend",
    "attendance",
    "lab_performance", "project_score",
    "participation_score", "extracurricular", "dept_avg",
    "num_subjects", "num_backlogs", "num_strong_subjects", "num_weak_subjects",
    "avg_subject_score", "min_subject_score", "max_subject_score", "std_subject_score",
    "practical_avg", "theory_avg", "credits_completed_ratio", "semester",
]

WEAKNESS_FEATURES = [
    "subject_score", "attendance",
    "lab_performance", "previous_related_score",
    "cgpa", "credits", "is_practical",
    "class_avg_score", "trend_indicator", "semester",
]

# Subjects considered "related" for prerequisite chain
PREREQUISITE_MAP = {
    "Engineering Mathematics-IV": "Engineering Mathematics-III",
    "Design & Analysis of Algorithms": "Data Structures and Algorithms",
    "Cryptography & Network Security": "Computer Networks",
    "Artificial Intelligence": "Engineering Mathematics-III",
    "Automata Theory / Theory of Computer Science": "Engineering Mathematics-III",
    "Automata Theory": "Engineering Mathematics-III",
    "Operating Systems": "Computer Networks",
    "Software Engineering": "Data Structures and Algorithms",
    "Microcontroller & Embedded Systems": "Digital Logic & Design",
    "Digital Logic & Computer Architecture": "Digital Logic & Design",
}

# Practical subject keywords
PRACTICAL_KEYWORDS = {
    "laboratory", "lab", "lab", "practical", "project",
    "internship", "mini project", "major project", "sbl",
}


def _is_practical_subject(name: str, code: str, is_practical: bool) -> bool:
    if is_practical:
        return True
    lower = name.lower() + " " + code.lower()
    return any(kw in lower for kw in PRACTICAL_KEYWORDS)


# ══════════════════════════════════════════════════════════════
# MARK PERCENTAGE CALCULATION
# ══════════════════════════════════════════════════════════════

def _subject_percentage(subj) -> float:
    """
    Calculate percentage from a SubjectScore.
    Handles zero max_marks gracefully.
    """
    # SubjectScore stores internal_marks + external_marks = total_marks
    # We need to know the max to calculate percentage
    # Try to get it from curriculum, else estimate from grade
    grade = getattr(subj, "grade", "FF")
    total = getattr(subj, "total_marks", 0.0)

    # Grade-based percentage estimation as fallback
    GRADE_PCT = {
        "AA": 87.5, "AB": 82.5, "BB": 77.5, "BC": 70.0,
        "CC": 60.0, "CD": 50.0, "PP": 42.0, "FF": 20.0, "LL": 0.0,
        "O": 92.5, "A+": 84.0, "A": 75.0, "B+": 65.0,
        "B": 57.5, "C": 50.0, "P": 42.0, "F": 20.0,
    }

    if total > 0:
        # Estimate max from grade and total
        # If grade is CC (55-65%) and total = 60, max ≈ 100
        # This is approximate — use grade midpoint
        pct = GRADE_PCT.get(grade.upper(), 50.0)
        if pct > 0:
            estimated_max = total / (pct / 100.0)
            # Snap to common max values
            for std_max in [50, 75, 100, 125]:
                if abs(estimated_max - std_max) < std_max * 0.15:
                    return (total / std_max) * 100.0
        # Fallback: assume max 100
        return min(total, 100.0)

    return GRADE_PCT.get(grade.upper(), 0.0)


def _grade_to_severity(pct: float, class_avg: float) -> Tuple[int, bool]:
    """
    Determine weakness severity and intervention need from percentage.
    Mirrors the logic in generate_training_data_v2.py::determine_severity()
    """
    risk = 0.0

    if pct < 25:   risk += 50
    elif pct < 35: risk += 42
    elif pct < 45: risk += 33
    elif pct < 55: risk += 24
    elif pct < 65: risk += 15
    elif pct < 75: risk += 7
    else:          risk += 2

    # Class average factor
    if pct < class_avg - 15: risk += 10
    elif pct < class_avg - 5: risk += 5

    if risk >= 72:   severity = 4
    elif risk >= 55: severity = 3
    elif risk >= 38: severity = 2
    elif risk >= 22: severity = 1
    else:            severity = 0

    needs_intervention = (severity >= 3) or (severity == 2 and pct < class_avg - 10)
    return severity, needs_intervention


# ══════════════════════════════════════════════════════════════
# DATABASE EXTRACTION
# ══════════════════════════════════════════════════════════════

async def init_db():
    from motor.motor_asyncio import AsyncIOMotorClient
    from beanie import init_beanie
    from app.core.config import settings
    from app.models.student_profile import StudentProfile, SemesterRecord, SubjectScore

    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    await init_beanie(database=db, document_models=[StudentProfile])
    logger.info("✅ Database connected")
    return client


async def extract_performance_records() -> pd.DataFrame:
    """
    Extract PERFORMANCE PREDICTOR training data from real StudentProfiles.

    For each student with ≥2 semesters of marks, create one training
    record per consecutive semester pair (sem_n → predict sem_n+1).

    Features are derived from sem_n; label is sem_n+1 SGPA.
    """
    from app.models.student_profile import StudentProfile

    students = await StudentProfile.find({}).to_list()
    logger.info(f"Found {len(students)} student profiles")

    records = []

    for student in students:
        srs = [sr for sr in student.semester_records if sr.is_complete and len(sr.subjects) > 0]
        srs.sort(key=lambda x: x.semester_number)

        if len(srs) < 2:
            continue  # Need at least 2 semesters

        cgpa_running = 0.0
        total_credits_running = 0

        for i in range(len(srs) - 1):
            current_sr = srs[i]
            next_sr    = srs[i + 1]

            # Skip if next semester has no valid SGPA
            if next_sr.sgpa <= 0:
                continue

            # ── Subject score arrays ──
            scores:   List[float] = []
            prac_sc:  List[float] = []
            theory_sc:List[float] = []
            n_backlogs = 0
            n_strong   = 0
            n_weak     = 0

            for subj in current_sr.subjects:
                pct = _subject_percentage(subj)
                scores.append(pct)

                is_prac = _is_practical_subject(
                    subj.subject_name, subj.subject_code, subj.is_practical
                )
                if is_prac:
                    prac_sc.append(pct)
                else:
                    theory_sc.append(pct)

                if pct < 40:  n_backlogs += 1
                if pct >= 70: n_strong   += 1
                if pct < 50:  n_weak     += 1

            if not scores:
                continue

            # Previous semester
            prev_sgpa = srs[i - 1].sgpa if i > 0 else current_sr.sgpa

            # Running CGPA up to and including current semester
            cgpa_running = student.cgpa  # use profile's CGPA as approximation
            # More accurate: compute from srs[0..i]
            agp = ac = 0.0
            for sr in srs[:i + 1]:
                if sr.total_credits > 0:
                    agp += sr.sgpa * sr.total_credits
                    ac  += sr.total_credits
            cgpa_approx = round(agp / ac, 2) if ac > 0 else current_sr.sgpa

            # Dept average (approximated from class — we don't store it,
            # so use a realistic constant per archetype of performance)
            dept_avg = 6.2  # approximate for MU IT dept

            # Credits completed ratio
            total_sem_credits_possible = 160  # 8 semesters × 20 credits
            credits_so_far = sum(sr.total_credits for sr in srs[:i + 1])
            credits_ratio = min(credits_so_far / total_sem_credits_possible, 1.0)

            # Lab performance: mean of practical subject percentages
            lab_perf = float(np.mean(prac_sc)) if prac_sc else float(np.mean(scores))

            # Practical avg / theory avg
            practical_avg = float(np.mean(prac_sc))  if prac_sc  else 0.0
            theory_avg    = float(np.mean(theory_sc)) if theory_sc else 0.0

            # Determine archetype from performance pattern
            avg_score = float(np.mean(scores))
            if avg_score >= 78:    archetype = "topper"
            elif avg_score >= 65:  archetype = "strong"
            elif avg_score >= 55:  archetype = "above_avg"
            elif avg_score >= 42:  archetype = "average"
            elif avg_score >= 30:  archetype = "below_avg"
            else:                  archetype = "failing"

            record = {
                "student_id":             student.user_id[:12] + f"_s{current_sr.semester_number}",
                "archetype":              archetype,
                "semester":               current_sr.semester_number,
                "current_cgpa":           round(cgpa_approx, 2),
                "current_sgpa":           round(current_sr.sgpa, 2),
                "previous_sgpa":          round(prev_sgpa, 2),
                "sgpa_trend":             round(current_sr.sgpa - prev_sgpa, 2),
                # attendance: not stored per-semester in StudentProfile
                # Use heuristic based on performance level
                "attendance":             round(min(95, 60 + avg_score * 0.35 + np.random.normal(0, 5)), 1),
                "lab_performance":        round(lab_perf, 1),
                "project_score":          round(min(100, avg_score * 0.9 + np.random.normal(5, 8)), 1),
                "participation_score":    round(min(100, avg_score * 0.7 + np.random.normal(10, 12)), 1),
                "extracurricular":        round(min(100, avg_score * 0.4 + np.random.normal(10, 18)), 1),
                "dept_avg":               dept_avg,
                "num_subjects":           len(current_sr.subjects),
                "num_backlogs":           n_backlogs,
                "num_strong_subjects":    n_strong,
                "num_weak_subjects":      n_weak,
                "avg_subject_score":      round(float(np.mean(scores)), 1),
                "min_subject_score":      round(float(np.min(scores)), 1),
                "max_subject_score":      round(float(np.max(scores)), 1),
                "std_subject_score":      round(float(np.std(scores)), 1),
                "practical_avg":          round(practical_avg, 1),
                "theory_avg":             round(theory_avg, 1),
                "credits_completed_ratio": round(credits_ratio, 2),
                "next_sgpa":              round(next_sr.sgpa, 2),   # ← TARGET
            }

            records.append(record)

    logger.info(f"Extracted {len(records)} performance training records from real data")
    return pd.DataFrame(records) if records else pd.DataFrame(columns=PERFORMANCE_FEATURES + ["next_sgpa", "student_id", "archetype"])


async def extract_weakness_records() -> pd.DataFrame:
    """
    Extract WEAKNESS DETECTOR training data from real StudentProfiles.

    For each subject in each semester, create one training record.
    """
    from app.models.student_profile import StudentProfile

    students = await StudentProfile.find({}).to_list()
    records  = []

    # Build class averages per semester per subject (approximate)
    # We compute them from the data itself
    all_subject_scores: Dict[Tuple[int, str], List[float]] = {}

    # First pass: collect all scores
    for student in students:
        for sr in student.semester_records:
            if not sr.is_complete:
                continue
            for subj in sr.subjects:
                key = (sr.semester_number, subj.subject_name.strip().lower())
                pct = _subject_percentage(subj)
                all_subject_scores.setdefault(key, []).append(pct)

    # Compute class averages
    class_averages: Dict[Tuple[int, str], float] = {
        k: float(np.mean(v)) for k, v in all_subject_scores.items()
    }

    # Second pass: build records
    for student in students:
        srs = sorted(
            [sr for sr in student.semester_records if sr.is_complete],
            key=lambda x: x.semester_number,
        )

        # Build previous semester subject map for prerequisite scores
        prev_subject_map: Dict[str, float] = {}

        cgpa = student.cgpa if student.cgpa > 0 else 5.0

        for sr in srs:
            for subj in sr.subjects:
                pct = _subject_percentage(subj)
                subj_name_lower = subj.subject_name.strip().lower()
                class_avg = class_averages.get(
                    (sr.semester_number, subj_name_lower), 55.0
                )

                # Previous related score (prerequisite)
                prereq_name = PREREQUISITE_MAP.get(subj.subject_name, "")
                prev_score  = prev_subject_map.get(
                    prereq_name.lower(),
                    pct + np.random.normal(0, 8),  # fallback: noisy version of current
                )
                prev_score = float(np.clip(prev_score, 5, 100))

                # Lab performance
                is_prac = _is_practical_subject(
                    subj.subject_name, subj.subject_code, subj.is_practical
                )
                lab_perf = pct + np.random.normal(5, 8) if is_prac else pct - 5 + np.random.normal(0, 10)
                lab_perf = float(np.clip(lab_perf, 0, 100))

                # Trend indicator
                prev_same = prev_subject_map.get(subj_name_lower, None)
                if prev_same is None:
                    trend = 0
                elif pct > prev_same + 5:
                    trend = 1
                elif pct < prev_same - 5:
                    trend = -1
                else:
                    trend = 0

                # Attendance (heuristic)
                all_scores_this_sem = [_subject_percentage(s) for s in sr.subjects]
                avg_sem_score = float(np.mean(all_scores_this_sem)) if all_scores_this_sem else pct
                attendance = float(np.clip(60 + avg_sem_score * 0.35 + np.random.normal(0, 5), 5, 100))

                severity, needs_intervention = _grade_to_severity(pct, class_avg)

                # Archetype from cgpa
                if cgpa >= 8.0:    archetype = "topper"
                elif cgpa >= 7.0:  archetype = "strong"
                elif cgpa >= 6.0:  archetype = "above_avg"
                elif cgpa >= 5.0:  archetype = "average"
                elif cgpa >= 4.0:  archetype = "below_avg"
                else:              archetype = "failing"

                records.append({
                    "student_id":            student.user_id[:12] + f"_s{sr.semester_number}",
                    "subject_name":          subj.subject_name,
                    "subject_code":          subj.subject_code,
                    "semester":              sr.semester_number,
                    "archetype":             archetype,
                    "subject_score":         round(pct, 1),
                    "attendance":            round(attendance, 1),
                    "lab_performance":       round(lab_perf, 1),
                    "previous_related_score":round(prev_score, 1),
                    "cgpa":                  round(cgpa, 2),
                    "credits":               subj.credits,
                    "is_practical":          int(is_prac),
                    "class_avg_score":       round(class_avg, 1),
                    "trend_indicator":       trend,
                    "weakness_severity":     severity,
                    "needs_intervention":    int(needs_intervention),
                })

                # Update previous map
                prev_subject_map[subj_name_lower] = pct

    logger.info(f"Extracted {len(records)} weakness training records from real data")
    return pd.DataFrame(records) if records else pd.DataFrame(
        columns=WEAKNESS_FEATURES + ["weakness_severity", "needs_intervention", "student_id", "archetype", "subject_name", "subject_code"]
    )


# ══════════════════════════════════════════════════════════════
# BLENDING (real + synthetic)
# ══════════════════════════════════════════════════════════════

def blend_with_synthetic(
    real_df: pd.DataFrame,
    synthetic_path: str,
    real_ratio: float,
    target_col: str,
    feature_cols: List[str],
) -> pd.DataFrame:
    """
    Blend real data with existing synthetic data.

    real_ratio: 0.0 = all synthetic, 1.0 = all real
    """
    if not os.path.exists(synthetic_path):
        logger.warning(f"Synthetic data not found at {synthetic_path} — using real only")
        return real_df

    synth_df = pd.read_csv(synthetic_path)

    # Keep only feature + target columns
    keep_cols = [c for c in feature_cols + [target_col, "archetype"] if c in synth_df.columns]
    synth_df  = synth_df[keep_cols].copy()

    if real_df.empty:
        logger.warning("No real data — using synthetic only")
        return synth_df

    n_real  = len(real_df)
    n_synth = len(synth_df)
    target_total = max(n_real, n_synth)

    n_real_target  = int(target_total * real_ratio)
    n_synth_target = target_total - n_real_target

    # Sample / upsample
    if n_real > n_real_target:
        real_sample = real_df.sample(n=n_real_target, random_state=42)
    else:
        # Upsample real data with small noise for regularisation
        repeats = (n_real_target // n_real) + 1
        real_sample = pd.concat([real_df] * repeats, ignore_index=True)
        numeric_cols = real_sample.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in feature_cols:
                std = real_sample[col].std() * 0.02  # 2% noise
                real_sample[col] = (real_sample[col] + np.random.normal(0, std, len(real_sample))).clip(
                    real_sample[col].min(), real_sample[col].max()
                )
        real_sample = real_sample.sample(n=n_real_target, random_state=42)

    if n_synth > n_synth_target:
        synth_sample = synth_df.sample(n=n_synth_target, random_state=42)
    else:
        synth_sample = synth_df

    blended = pd.concat([real_sample, synth_sample], ignore_index=True)
    blended = blended.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle

    logger.info(
        f"Blended: {len(real_sample)} real + {len(synth_sample)} synthetic "
        f"= {len(blended)} total (real_ratio={real_ratio:.0%})"
    )

    return blended


# ══════════════════════════════════════════════════════════════
# DATA VALIDATION
# ══════════════════════════════════════════════════════════════

def validate_performance_df(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean performance training DataFrame."""
    if df.empty:
        return df

    # Ensure all feature columns exist
    for col in PERFORMANCE_FEATURES + ["next_sgpa"]:
        if col not in df.columns:
            logger.warning(f"Missing column '{col}' — filling with 0")
            df[col] = 0.0

    # Clip to valid ranges
    df["current_sgpa"]  = df["current_sgpa"].clip(0, 10)
    df["previous_sgpa"] = df["previous_sgpa"].clip(0, 10)
    df["next_sgpa"]     = df["next_sgpa"].clip(0, 10)
    df["current_cgpa"]  = df["current_cgpa"].clip(0, 10)
    df["attendance"]    = df["attendance"].clip(0, 100)
    df["lab_performance"]= df["lab_performance"].clip(0, 100)
    df["project_score"] = df["project_score"].clip(0, 100)
    df["participation_score"] = df["participation_score"].clip(0, 100)
    df["extracurricular"]     = df["extracurricular"].clip(0, 100)
    df["dept_avg"]      = df["dept_avg"].clip(0, 10)
    df["avg_subject_score"]   = df["avg_subject_score"].clip(0, 100)
    df["min_subject_score"]   = df["min_subject_score"].clip(0, 100)
    df["max_subject_score"]   = df["max_subject_score"].clip(0, 100)
    df["std_subject_score"]   = df["std_subject_score"].clip(0, 50)
    df["practical_avg"] = df["practical_avg"].clip(0, 100)
    df["theory_avg"]    = df["theory_avg"].clip(0, 100)
    df["credits_completed_ratio"] = df["credits_completed_ratio"].clip(0, 1)
    df["sgpa_trend"]    = df["sgpa_trend"].clip(-10, 10)
    df["num_backlogs"]  = df["num_backlogs"].clip(0, 20).astype(int)
    df["num_subjects"]  = df["num_subjects"].clip(1, 15).astype(int)
    df["semester"]      = df["semester"].clip(1, 8).astype(int)

    # Drop rows with NaN in critical columns
    critical = ["current_sgpa", "next_sgpa", "semester"]
    df = df.dropna(subset=critical)

    return df


def validate_weakness_df(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean weakness training DataFrame."""
    if df.empty:
        return df

    for col in WEAKNESS_FEATURES + ["weakness_severity", "needs_intervention"]:
        if col not in df.columns:
            logger.warning(f"Missing column '{col}' — filling with 0")
            df[col] = 0

    df["subject_score"]          = df["subject_score"].clip(0, 100)
    df["attendance"]             = df["attendance"].clip(0, 100)
    df["lab_performance"]        = df["lab_performance"].clip(0, 100)
    df["previous_related_score"] = df["previous_related_score"].clip(0, 100)
    df["cgpa"]                   = df["cgpa"].clip(0, 10)
    df["class_avg_score"]        = df["class_avg_score"].clip(0, 100)
    df["trend_indicator"]        = df["trend_indicator"].clip(-1, 1).astype(int)
    df["is_practical"]           = df["is_practical"].clip(0, 1).astype(int)
    df["credits"]                = df["credits"].clip(1, 8).astype(int)
    df["semester"]               = df["semester"].clip(1, 8).astype(int)
    df["weakness_severity"]      = df["weakness_severity"].clip(0, 4).astype(int)
    df["needs_intervention"]     = df["needs_intervention"].clip(0, 1).astype(int)

    df = df.dropna(subset=["subject_score", "weakness_severity"])

    return df


# ══════════════════════════════════════════════════════════════
# STATISTICS REPORTING
# ══════════════════════════════════════════════════════════════

def print_stats(df: pd.DataFrame, name: str):
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")
    print(f"  Total records: {len(df):,}")

    if "archetype" in df.columns:
        print(f"\n  Archetype distribution:")
        for arch, cnt in df["archetype"].value_counts().items():
            bar = "█" * int(cnt / len(df) * 30)
            print(f"    {arch:<15} {cnt:>5}  {bar}")

    if "next_sgpa" in df.columns:
        s = df["next_sgpa"]
        print(f"\n  next_sgpa: mean={s.mean():.2f}  std={s.std():.2f}  "
              f"min={s.min():.2f}  max={s.max():.2f}")

    if "weakness_severity" in df.columns:
        print(f"\n  Severity distribution:")
        labels = {0: "none", 1: "low", 2: "medium", 3: "high", 4: "critical"}
        for sev, cnt in df["weakness_severity"].value_counts().sort_index().items():
            pct = cnt / len(df) * 100
            bar = "█" * int(pct / 3)
            print(f"    {labels.get(sev, str(sev)):<10} {cnt:>5}  ({pct:.1f}%)  {bar}")

    if "semester" in df.columns:
        print(f"\n  Semester distribution: {dict(df['semester'].value_counts().sort_index())}")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser(
        description="Generate ML training data from real student marks"
    )
    parser.add_argument(
        "--min-students", type=int, default=30,
        help="Minimum real records required before using real data (default: 30)"
    )
    parser.add_argument(
        "--blend", type=float, default=0.7,
        help="Ratio of real data in blended output (0.0-1.0, default: 0.7)"
    )
    parser.add_argument(
        "--real-only", action="store_true",
        help="Use only real data (no synthetic blending)"
    )
    parser.add_argument(
        "--synthetic-only", action="store_true",
        help="Regenerate synthetic data only (skip DB extraction)"
    )
    parser.add_argument(
        "--output-dir", default=OUTPUT_DIR,
        help="Output directory for training CSVs"
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    perf_path = os.path.join(args.output_dir, "performance_training_data.csv")
    weak_path = os.path.join(args.output_dir, "weakness_training_data.csv")

    if args.synthetic_only:
        # Delegate to generate_training_data_v2
        from scripts.generate_training_data_v2 import (
            generate_performance_dataset,
            generate_weakness_dataset,
        )
        logger.info("Generating synthetic data only...")
        perf_df = generate_performance_dataset(6000)
        perf_df.to_csv(perf_path, index=False)
        weak_df = generate_weakness_dataset(4000)
        weak_df.to_csv(weak_path, index=False)
        print_stats(perf_df, "Performance (synthetic)")
        print_stats(weak_df, "Weakness (synthetic)")
        return

    # ── Connect to DB ──
    client = await init_db()

    try:
        # ── Extract real data ──
        logger.info("\nExtracting performance records from DB...")
        real_perf_df = await extract_performance_records()

        logger.info("\nExtracting weakness records from DB...")
        real_weak_df = await extract_weakness_records()

        # ── Validate ──
        real_perf_df = validate_performance_df(real_perf_df)
        real_weak_df = validate_weakness_df(real_weak_df)

        logger.info(f"\nReal data: {len(real_perf_df)} performance, {len(real_weak_df)} weakness records")

        # ── Decide blend strategy ──
        real_ratio = args.blend if not args.real_only else 1.0

        if len(real_perf_df) < args.min_students:
            logger.warning(
                f"Only {len(real_perf_df)} real performance records "
                f"(< minimum {args.min_students}). "
                f"Using higher synthetic ratio."
            )
            real_ratio_perf = max(0.1, real_ratio - 0.3)
        else:
            real_ratio_perf = real_ratio

        if len(real_weak_df) < args.min_students:
            real_ratio_weak = max(0.1, real_ratio - 0.3)
        else:
            real_ratio_weak = real_ratio

        # ── Blend ──
        if args.real_only:
            final_perf_df = real_perf_df
            final_weak_df = real_weak_df
        else:
            final_perf_df = blend_with_synthetic(
                real_perf_df, perf_path, real_ratio_perf,
                "next_sgpa", PERFORMANCE_FEATURES
            )
            final_weak_df = blend_with_synthetic(
                real_weak_df, weak_path, real_ratio_weak,
                "weakness_severity", WEAKNESS_FEATURES
            )

        # ── Final validation ──
        final_perf_df = validate_performance_df(final_perf_df)
        final_weak_df = validate_weakness_df(final_weak_df)

        # ── Save ──
        final_perf_df[PERFORMANCE_FEATURES + ["next_sgpa", "archetype"]].to_csv(
            perf_path, index=False
        )
        final_weak_df[WEAKNESS_FEATURES + ["weakness_severity", "needs_intervention", "archetype"]].to_csv(
            weak_path, index=False
        )

        logger.info(f"\n✅ Saved performance data: {perf_path} ({len(final_perf_df)} records)")
        logger.info(f"✅ Saved weakness data:     {weak_path} ({len(final_weak_df)} records)")

        # ── Statistics ──
        print_stats(final_perf_df, f"Performance Training Data (real_ratio={real_ratio_perf:.0%})")
        print_stats(final_weak_df, f"Weakness Training Data (real_ratio={real_ratio_weak:.0%})")

        # ── Save metadata ──
        meta = {
            "generated_at": datetime.utcnow().isoformat(),
            "source": "real_db_with_blend",
            "real_perf_records": len(real_perf_df),
            "real_weak_records": len(real_weak_df),
            "final_perf_records": len(final_perf_df),
            "final_weak_records": len(final_weak_df),
            "real_ratio_perf": real_ratio_perf,
            "real_ratio_weak": real_ratio_weak,
            "feature_columns": PERFORMANCE_FEATURES,
            "weakness_feature_columns": WEAKNESS_FEATURES,
        }
        with open(os.path.join(args.output_dir, "data_generation_meta.json"), "w") as f:
            json.dump(meta, f, indent=2)

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())