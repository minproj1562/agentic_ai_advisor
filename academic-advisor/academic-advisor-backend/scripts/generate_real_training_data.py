# scripts/generate_real_training_data.py
"""
Training Data Generator Using Real Marks from IT_COPY.xlsx
==========================================================
Replaces synthetic data with actual student performance data.
Uses practical marks TOT column for lab_performance.
Removes attendance field.

Usage:
    python -m scripts.generate_real_training_data
"""

import os, sys, json, argparse
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
np.random.seed(42)

EXCEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "exported_marks", "IT - Copy.xlsx",
)
OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app", "ml", "models", "saved",
)

# ═══════════════════════════════════════════════════════════════
#  SHEET CONFIGS — maps Excel structure to our data model
# ═══════════════════════════════════════════════════════════════

SHEET_CONFIGS = {
    "IT SEM-III SH-2024": {
        "semester": 3,
        "theory_subjects": {
            "Engineering Mathematics-III":            {"tot_col": 8,  "max": 125, "credits": 4},
            "Computer Organization & Architecture":   {"tot_col": 13, "max": 125, "credits": 4},
            "Data Structures & Analysis":             {"tot_col": 17, "max": 100, "credits": 3},
            "Database Management System":             {"tot_col": 21, "max": 100, "credits": 3},
            "Digital Logic Design & Analysis":        {"tot_col": 25, "max": 100, "credits": 3},
        },
        "practical_subjects": {
            "Data Structure Laboratory":  {"tot_col": 28, "max": 50, "credits": 1},
            "SQL Laboratory":             {"tot_col": 31, "max": 50, "credits": 1},
            "Python Laboratory":          {"tot_col": 34, "max": 50, "credits": 2},
        },
        "other_subjects": {
            "Mini Project-1A": {"col": 35, "max": 50, "credits": 1},
            "Product Design":  {"col": 36, "max": 50, "credits": 2},
        },
        "sgpi_col": 40,
        "cgpi_col": 43,
    },
    "IT SEM-IV FH-2025": {
        "semester": 4,
        "theory_subjects": {
            "Engineering Mathematics-IV":               {"tot_col": 8,  "max": 125, "credits": 4},
            "Computer Network":                         {"tot_col": 12, "max": 100, "credits": 3},
            "Operating System":                         {"tot_col": 16, "max": 100, "credits": 3},
            "Software Engineering":                     {"tot_col": 20, "max": 100, "credits": 3},
            "Microcontroller and Embedded Systems":     {"tot_col": 24, "max": 100, "credits": 3},
        },
        "practical_subjects": {
            "Networks Laboratory":               {"tot_col": 27, "max": 50, "credits": 1},
            "Linux Laboratory":                  {"tot_col": 30, "max": 50, "credits": 1},
            "Software Development Laboratory":   {"tot_col": 33, "max": 50, "credits": 1},
            "Full Stack Development Laboratory": {"tot_col": 36, "max": 100, "credits": 2},
            "Mini Project 1B":                   {"tot_col": 39, "max": 100, "credits": 2},
        },
        "other_subjects": {
            "Environment and Sustainability": {"col": 40, "max": 50, "credits": 1},
        },
        "sgpi_col": 44,
        "cgpi_col": 47,
    },
    "IT-V-SH 2025": {
        "semester": 5,
        "theory_subjects": {
            "Automata Theory":          {"tot_col": 7,  "max": 100, "credits": 3},
            "Artificial Intelligence":  {"tot_col": 11, "max": 100, "credits": 3},
            "Internet of Things":       {"tot_col": 15, "max": 100, "credits": 3},
            "Program Elective Course-I":{"tot_col": 19, "max": 100, "credits": 3},
        },
        "practical_subjects": {
            "Cloud Computing Laboratory":               {"tot_col": 22, "max": 50, "credits": 1},
            "Mobile Application Development Laboratory":{"tot_col": 25, "max": 50, "credits": 1},
            "Internet of Things Laboratory":            {"tot_col": 28, "max": 50, "credits": 1},
        },
        "other_subjects": {
            "Professional Communication and Ethics-II": {"col": 29, "max": 50, "credits": 2},
            "Mini Project-2A":                          {"col": 30, "max": 50, "credits": 1},
            "Entrepreneurship":                         {"col": 31, "max": 50, "credits": 2},
        },
        "sgpi_col": 35,
        "cgpi_col": 38,
    },
}

# Canonical subject name mapping for training features
CANONICAL_MAP = {
    "Engineering Mathematics-III": "Engineering Mathematics-III",
    "Engineering Mathematics-IV": "Engineering Mathematics-IV",
    "Computer Organization & Architecture": "Computer Organization & Architecture",
    "Data Structures & Analysis": "Data Structures and Algorithms",
    "Database Management System": "Database Management Systems",
    "Digital Logic Design & Analysis": "Digital Logic & Design",
    "Computer Network": "Computer Networks",
    "Operating System": "Operating Systems",
    "Software Engineering": "Software Engineering",
    "Microcontroller and Embedded Systems": "Microcontroller & Embedded Systems",
    "Automata Theory": "Automata Theory",
    "Artificial Intelligence": "Artificial Intelligence",
    "Internet of Things": "IoT",
    "Program Elective Course-I": "Program Elective-I",
}

CANONICAL_SUBJECTS = [
    "Engineering Mathematics-III", "Engineering Mathematics-IV",
    "Data Structures and Algorithms", "Database Management Systems",
    "Digital Logic & Design", "Operating Systems", "Computer Networks",
    "Microcontroller & Embedded Systems", "Software Engineering",
    "Computer Organization & Architecture",
    "Automata Theory", "Artificial Intelligence", "IoT",
    "Program Elective-I",
]

# ── Elective labels & affinity (kept from v2) ────────────────
PEC_LABELS = ["ML", "WT", "DWM", "CCS"]
OEC_LABELS = ["RE", "OR", "CSL", "DBM", "EAM"]

PEC_AFFINITY = {
    "ML":  {"boost_subjects": ["Artificial Intelligence", "Engineering Mathematics-III", "Data Structures and Algorithms"], "penalize_subjects": ["Microcontroller & Embedded Systems", "IoT"]},
    "WT":  {"boost_subjects": ["Computer Networks", "Microcontroller & Embedded Systems", "IoT"], "penalize_subjects": ["Artificial Intelligence"]},
    "DWM": {"boost_subjects": ["Database Management Systems", "Data Structures and Algorithms"], "penalize_subjects": ["IoT"]},
    "CCS": {"boost_subjects": ["Computer Networks", "Operating Systems", "Software Engineering"], "penalize_subjects": ["Microcontroller & Embedded Systems"]},
}
OEC_AFFINITY = {
    "RE":  {"boost_subjects": ["Engineering Mathematics-III", "Engineering Mathematics-IV"]},
    "OR":  {"boost_subjects": ["Engineering Mathematics-III", "Engineering Mathematics-IV", "Data Structures and Algorithms"]},
    "CSL": {"boost_subjects": ["Computer Networks"]},
    "DBM": {"boost_subjects": ["Database Management Systems", "Software Engineering"]},
    "EAM": {"boost_subjects": ["Microcontroller & Embedded Systems", "IoT"]},
}

INTEREST_AREAS = [
    "Artificial Intelligence & Machine Learning", "Mobile & IoT Development",
    "Web Development", "Data Science & Analytics",
    "Cloud & Distributed Systems", "Network & Wireless Systems",
]


def _clip(v, lo=0.0, hi=100.0):
    return float(np.clip(v, lo, hi))


# ═══════════════════════════════════════════════════════════════
#  EXCEL PARSER
# ═══════════════════════════════════════════════════════════════

def parse_sheet(excel_path: str, sheet_name: str, config: dict) -> pd.DataFrame:
    """Parse a semester sheet and return structured student data."""
    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)

    # Find header row
    header_idx = None
    for idx, row in df.iterrows():
        vals = [str(v).strip() for v in row.values if pd.notna(v)]
        if "Sr. No" in vals and "Name of Student" in vals:
            header_idx = idx
            break
    if header_idx is None:
        raise ValueError(f"Cannot find header in sheet '{sheet_name}'")

    students = []
    i = header_idx + 1
    while i < len(df):
        row = df.iloc[i]
        type_val = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
        if type_val != "MarksO":
            i += 1
            continue

        sr = row.iloc[0]
        try:
            sr_num = int(float(sr))
        except (ValueError, TypeError):
            i += 1
            continue

        name = str(row.iloc[2]).strip().title() if pd.notna(row.iloc[2]) else ""
        seat = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""

        student = {"sr_no": sr_num, "name": name, "seat_no": seat, "semester": config["semester"]}

        # Theory subjects
        theory_marks = {}
        for subj_name, info in config["theory_subjects"].items():
            val = row.iloc[info["tot_col"]]
            try:
                mark = float(val)
                pct = (mark / info["max"]) * 100
                theory_marks[subj_name] = {"raw": mark, "max": info["max"], "pct": round(pct, 1)}
            except (ValueError, TypeError):
                theory_marks[subj_name] = {"raw": 0, "max": info["max"], "pct": 0}
        student["theory_marks"] = theory_marks

        # Practical subjects (for lab_performance)
        prac_marks = {}
        for subj_name, info in config["practical_subjects"].items():
            val = row.iloc[info["tot_col"]]
            try:
                mark = float(val)
                pct = (mark / info["max"]) * 100
                prac_marks[subj_name] = {"raw": mark, "max": info["max"], "pct": round(pct, 1)}
            except (ValueError, TypeError):
                prac_marks[subj_name] = {"raw": 0, "max": info["max"], "pct": 0}
        student["practical_marks"] = prac_marks

        # SGPI / CGPI
        try:
            student["sgpi"] = round(float(row.iloc[config["sgpi_col"]]), 2)
        except:
            student["sgpi"] = 0.0
        try:
            student["cgpi"] = round(float(row.iloc[config["cgpi_col"]]), 2)
        except:
            student["cgpi"] = 0.0

        # Lab performance = average of practical percentages
        prac_pcts = [p["pct"] for p in prac_marks.values() if p["pct"] > 0]
        student["lab_performance"] = round(np.mean(prac_pcts), 1) if prac_pcts else 50.0

        students.append(student)
        i += 1

    return pd.DataFrame(students)


# ═══════════════════════════════════════════════════════════════
#  TRAINING DATA GENERATORS
# ═══════════════════════════════════════════════════════════════

def _student_canonical_marks(student_rows: list) -> dict:
    """Merge a student's marks across semesters into canonical subject scores (0-100)."""
    marks = {}
    for row in student_rows:
        for subj, info in row.get("theory_marks", {}).items():
            canonical = CANONICAL_MAP.get(subj, subj)
            marks[canonical] = info["pct"]
    return marks


def _compute_elective_score(marks: dict, affinity: dict) -> float:
    """Compute affinity score for a specific elective based on student marks."""
    score = 0
    count = 0
    for subj in affinity.get("boost_subjects", []):
        if subj in marks:
            score += marks[subj] * 1.5
            count += 1
    for subj in affinity.get("penalize_subjects", []):
        if subj in marks:
            score -= marks[subj] * 0.3
            count += 1
    avg_mark = np.mean(list(marks.values())) if marks else 50
    return score + avg_mark * 0.5


def generate_elective_training(all_students: dict, n_augment: int = 5) -> tuple:
    """Generate PEC and OEC training data from real student marks."""
    pec_rows, oec_rows = [], []

    for name, semesters in all_students.items():
        marks = _student_canonical_marks(semesters)
        if not marks:
            continue

        lab_perfs = [s.get("lab_performance", 50) for s in semesters]
        avg_lab = np.mean(lab_perfs)

        # Compute PEC scores and pick best
        pec_scores = {lbl: _compute_elective_score(marks, PEC_AFFINITY[lbl]) for lbl in PEC_LABELS}
        best_pec = max(pec_scores, key=pec_scores.get)

        # Compute OEC scores and pick best
        oec_scores = {lbl: _compute_elective_score(marks, OEC_AFFINITY[lbl]) for lbl in OEC_LABELS}
        best_oec = max(oec_scores, key=oec_scores.get)

        interest = np.random.choice(INTEREST_AREAS)
        sgpis = [s.get("sgpi", 5.0) for s in semesters]
        avg_sgpi = np.mean(sgpis)

        # Base row
        base = {}
        for subj in CANONICAL_SUBJECTS:
            base[subj] = marks.get(subj, 50.0)
        base["lab_performance"] = avg_lab
        base["sgpi"] = avg_sgpi
        base["interest_area"] = interest
        base["project_skills"] = ""

        # PEC row
        pec_row = {**base, "recommended_pec": best_pec}
        pec_rows.append(pec_row)

        # OEC row
        oec_row = {**base, "recommended_oec": best_oec}
        oec_rows.append(oec_row)

        # Augment with noise
        for _ in range(n_augment):
            noisy = {k: _clip(v + np.random.normal(0, 3)) if isinstance(v, (int, float)) else v for k, v in base.items()}
            noisy["interest_area"] = np.random.choice(INTEREST_AREAS)
            pec_rows.append({**noisy, "recommended_pec": best_pec})
            oec_rows.append({**noisy, "recommended_oec": best_oec})

    return pd.DataFrame(pec_rows), pd.DataFrame(oec_rows)


def generate_performance_training(all_students: dict) -> pd.DataFrame:
    """Generate performance prediction training data."""
    rows = []
    for name, semesters in all_students.items():
        marks = _student_canonical_marks(semesters)
        if not marks:
            continue

        lab_perfs = [s.get("lab_performance", 50) for s in semesters]
        sgpis = [s.get("sgpi", 5.0) for s in semesters]

        row = {}
        for subj in CANONICAL_SUBJECTS:
            row[subj] = marks.get(subj, 50.0)
        row["lab_performance"] = np.mean(lab_perfs)
        row["target_sgpa"] = np.mean(sgpis)

        rows.append(row)

        # Augment
        for _ in range(3):
            noisy = {k: _clip(v + np.random.normal(0, 4)) if isinstance(v, (int, float)) else v for k, v in row.items()}
            noisy["target_sgpa"] = _clip(row["target_sgpa"] + np.random.normal(0, 0.3), 2, 10)
            rows.append(noisy)

    return pd.DataFrame(rows)


def generate_weakness_training(all_students: dict) -> pd.DataFrame:
    """Generate weakness detection training data."""
    rows = []
    for name, semesters in all_students.items():
        marks = _student_canonical_marks(semesters)
        if not marks:
            continue

        for subj, score in marks.items():
            if score < 40:
                severity = "critical"
            elif score < 55:
                severity = "moderate"
            elif score < 70:
                severity = "mild"
            else:
                severity = "none"

            lab_perfs = [s.get("lab_performance", 50) for s in semesters]

            row = {"subject": subj, "score": score, "lab_performance": np.mean(lab_perfs)}
            # Add other subject scores as context
            for other_subj in CANONICAL_SUBJECTS:
                if other_subj != subj:
                    row[f"ctx_{other_subj}"] = marks.get(other_subj, 50.0)
            row["severity"] = severity
            rows.append(row)

    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("  GENERATE TRAINING DATA FROM REAL MARKS")
    print("=" * 70)

    if not os.path.exists(EXCEL_PATH):
        print(f"\n  ❌ Excel not found: {EXCEL_PATH}")
        sys.exit(1)

    # Parse all semester sheets
    all_semester_data = {}
    for sheet_name, config in SHEET_CONFIGS.items():
        try:
            print(f"\n  📄 Parsing '{sheet_name}' (Semester {config['semester']})...")
            df = parse_sheet(EXCEL_PATH, sheet_name, config)
            print(f"     ✅ Found {len(df)} students")

            for _, row in df.iterrows():
                name = row["name"]
                if name not in all_semester_data:
                    all_semester_data[name] = []
                all_semester_data[name].append(row.to_dict())
        except Exception as e:
            print(f"     ⚠️  Error parsing {sheet_name}: {e}")

    print(f"\n  📊 Total unique students: {len(all_semester_data)}")

    # Generate training data
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\n  🔄 Generating PEC & OEC training data...")
    pec_df, oec_df = generate_elective_training(all_semester_data)
    pec_path = os.path.join(OUTPUT_DIR, "pec_training_data.csv")
    oec_path = os.path.join(OUTPUT_DIR, "oec_training_data.csv")
    pec_df.to_csv(pec_path, index=False)
    oec_df.to_csv(oec_path, index=False)
    print(f"     ✅ PEC: {len(pec_df)} samples → {pec_path}")
    print(f"     ✅ OEC: {len(oec_df)} samples → {oec_path}")

    print("\n  🔄 Generating performance prediction data...")
    perf_df = generate_performance_training(all_semester_data)
    perf_path = os.path.join(OUTPUT_DIR, "performance_training_data.csv")
    perf_df.to_csv(perf_path, index=False)
    print(f"     ✅ Performance: {len(perf_df)} samples → {perf_path}")

    print("\n  🔄 Generating weakness detection data...")
    weak_df = generate_weakness_training(all_semester_data)
    weak_path = os.path.join(OUTPUT_DIR, "weakness_training_data.csv")
    weak_df.to_csv(weak_path, index=False)
    print(f"     ✅ Weakness: {len(weak_df)} samples → {weak_path}")

    # Summary
    print("\n" + "=" * 70)
    print("  ✅ ALL TRAINING DATA GENERATED FROM REAL MARKS!")
    print(f"  Output directory: {OUTPUT_DIR}")
    print("  Files:")
    print(f"    • pec_training_data.csv       ({len(pec_df)} rows)")
    print(f"    • oec_training_data.csv       ({len(oec_df)} rows)")
    print(f"    • performance_training_data.csv ({len(perf_df)} rows)")
    print(f"    • weakness_training_data.csv  ({len(weak_df)} rows)")
    print("=" * 70)


if __name__ == "__main__":
    main()
