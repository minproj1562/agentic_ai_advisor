# academic-advisor/academic-advisor-backend/app/ml/utils/training.py
"""
Comprehensive Training Data Generation & Training Pipeline
============================================================
Generates diverse elective recommendation training data covering:
  - ALL score ranges (5-100, not just 65-98)
  - Student archetypes: toppers, average, struggling, failing, improving
  - Proper labels based on RELATIVE subject alignment
  - Realistic interest & project skill patterns
  - Honours/Minors training data

The key insight: a student scoring 35% overall can still be labeled "ML"
if their Python (42) and Math-III (40) are their BEST subjects relative
to CN (25) and MES (22).
"""

import os
import sys
import json
import logging
import asyncio
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
#  CONSTANTS — aligned with recommendation_engine.py
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

ELECTIVE_LABELS = ["ML", "WT", "DWM", "CCS"]

# Which subjects each elective "boosts" — students labeled X have
# relatively higher scores in these subjects
ELECTIVE_SUBJECT_AFFINITY = {
    "ML": {
        "boost": {
            "Python": (8, 18), "Artificial Intelligence": (10, 22),
            "Engineering Mathematics-III": (5, 15),
            "Engineering Mathematics-IV": (3, 12),
            "Data Structures and Algorithms": (3, 10),
            "Database Management Systems": (0, 5),
        },
        "penalize": {
            "Computer Networks": (-5, -15), "Microcontroller & Embedded Systems": (-8, -18),
            "IoT": (-8, -20), "Digital Logic & Design": (-3, -10),
            "Full Stack Development": (-3, -10), "Operating Systems": (-2, -8),
        },
    },
    "WT": {
        "boost": {
            "Computer Networks": (10, 20), "Microcontroller & Embedded Systems": (8, 18),
            "IoT": (10, 22), "Digital Logic & Design": (5, 12),
            "C++": (3, 10), "Operating Systems": (2, 8),
        },
        "penalize": {
            "Python": (-3, -10), "Artificial Intelligence": (-8, -18),
            "Engineering Mathematics-III": (-3, -10),
            "Database Management Systems": (-5, -12),
            "Full Stack Development": (-5, -15),
        },
    },
    "DWM": {
        "boost": {
            "Database Management Systems": (10, 20),
            "Data Structures and Algorithms": (5, 12),
            "Python": (3, 10), "Engineering Mathematics-IV": (3, 10),
            "Java": (2, 8),
        },
        "penalize": {
            "Computer Networks": (-3, -10), "Microcontroller & Embedded Systems": (-8, -18),
            "IoT": (-8, -20), "Full Stack Development": (-5, -12),
            "Operating Systems": (-3, -8),
        },
    },
    "CCS": {
        "boost": {
            "Computer Networks": (5, 15), "Operating Systems": (5, 12),
            "Full Stack Development": (10, 22), "Software Engineering": (5, 12),
            "Database Management Systems": (2, 8), "Python": (2, 8),
        },
        "penalize": {
            "Microcontroller & Embedded Systems": (-5, -15),
            "IoT": (-5, -15), "Engineering Mathematics-III": (-3, -10),
            "Artificial Intelligence": (-5, -12),
            "Digital Logic & Design": (-3, -10),
        },
    },
}

# Interest patterns per elective
ELECTIVE_INTEREST_PATTERNS = {
    "ML": {
        "primary": ["Artificial Intelligence & Machine Learning", "Data Science & Analytics"],
        "secondary": ["Web Development", "Cloud & Distributed Systems"],
        "unlikely": ["Network & Wireless Systems", "Mobile & IoT Development"],
    },
    "WT": {
        "primary": ["Network & Wireless Systems", "Mobile & IoT Development"],
        "secondary": ["Cloud & Distributed Systems"],
        "unlikely": ["Artificial Intelligence & Machine Learning", "Data Science & Analytics", "Web Development"],
    },
    "DWM": {
        "primary": ["Data Science & Analytics", "Artificial Intelligence & Machine Learning"],
        "secondary": ["Web Development"],
        "unlikely": ["Network & Wireless Systems", "Mobile & IoT Development", "Cloud & Distributed Systems"],
    },
    "CCS": {
        "primary": ["Cloud & Distributed Systems", "Web Development"],
        "secondary": ["Network & Wireless Systems", "Data Science & Analytics"],
        "unlikely": ["Mobile & IoT Development", "Artificial Intelligence & Machine Learning"],
    },
}

# Project skill pools per elective
PROJECT_SKILL_POOLS = {
    "ML": {
        "titles": [
            "Sentiment Analysis Tool", "Image Classifier", "Chatbot System",
            "Recommendation Engine", "Fraud Detection System", "Price Predictor",
            "NLP Pipeline", "Object Detection App", "Speech Recognition",
            "Handwriting Recognizer", "Spam Filter", "Music Genre Classifier",
            "Face Recognition System", "Stock Predictor", "Disease Diagnosis Tool",
            "Customer Churn Predictor", "Text Summarizer", "Language Translator",
        ],
        "skills": [
            "python", "tensorflow", "pytorch", "sklearn", "pandas", "numpy",
            "machine learning", "deep learning", "nlp", "neural network",
            "data science", "classification", "regression", "keras",
            "computer vision", "opencv", "matplotlib", "jupyter",
        ],
        "languages": ["Python", "R"],
        "frameworks": ["TensorFlow", "PyTorch", "Scikit-learn", "Keras", "Flask"],
    },
    "WT": {
        "titles": [
            "Smart Home System", "Weather Station", "GPS Tracker",
            "IoT Security Monitor", "Wireless Sensor Network", "Smart Agriculture",
            "Health Monitoring Wearable", "Remote Water Quality Monitor",
            "Smart Parking System", "Industrial IoT Gateway", "BLE Beacon Tracker",
            "LoRa Communication System", "RFID Attendance System",
            "Gesture Controlled Robot", "Smart Streetlight System",
        ],
        "skills": [
            "arduino", "raspberry pi", "iot", "embedded", "sensor",
            "wireless", "bluetooth", "mqtt", "microcontroller", "esp32",
            "lora", "rfid", "zigbee", "gpio", "i2c", "freertos",
        ],
        "languages": ["C", "C++", "Python"],
        "frameworks": ["Arduino IDE", "ESP-IDF", "FreeRTOS", "MicroPython"],
    },
    "DWM": {
        "titles": [
            "Sales Dashboard", "Data Pipeline System", "ETL Automation Tool",
            "Business Intelligence Portal", "Customer Analytics Platform",
            "Survey Data Analyzer", "Academic Performance Dashboard",
            "Crime Data Analysis", "Healthcare Data Warehouse",
            "Social Media Analytics", "Financial Data Mining Tool",
            "Log Analysis System", "Census Data Visualizer",
            "Market Basket Analyzer", "Clickstream Analyzer",
        ],
        "skills": [
            "sql", "mongodb", "data warehouse", "etl", "hadoop", "spark",
            "data mining", "analytics", "tableau", "power bi", "pandas",
            "data pipeline", "postgresql", "mysql", "data visualization",
        ],
        "languages": ["Python", "SQL", "R"],
        "frameworks": ["Apache Spark", "Tableau", "Power BI", "Pandas"],
    },
    "CCS": {
        "titles": [
            "Cloud Deployment Platform", "CI/CD Pipeline Builder",
            "Containerized Microservices App", "Serverless API Gateway",
            "Full Stack E-Commerce Site", "Real-Time Chat Application",
            "Portfolio Website Builder", "Task Management System",
            "REST API Service", "Blog Platform with CMS",
            "Online Learning Platform", "Cloud File Storage",
            "Multi-tenant SaaS App", "Service Mesh Dashboard",
            "Kubernetes Cluster Monitor",
        ],
        "skills": [
            "aws", "azure", "docker", "kubernetes", "cloud", "devops",
            "terraform", "serverless", "microservices", "ci/cd", "react",
            "node", "fullstack", "rest api", "jenkins", "nginx",
        ],
        "languages": ["JavaScript", "Python", "Go", "TypeScript"],
        "frameworks": ["React", "Node.js", "Express", "Next.js", "Docker", "Kubernetes"],
    },
}

# Student archetype definitions
STUDENT_ARCHETYPES = {
    "topper":       {"pct": 0.12, "ability": (78, 97), "consistency": 0.88},
    "strong":       {"pct": 0.18, "ability": (65, 80), "consistency": 0.80},
    "above_avg":    {"pct": 0.15, "ability": (55, 67), "consistency": 0.72},
    "average":      {"pct": 0.22, "ability": (42, 57), "consistency": 0.65},
    "below_avg":    {"pct": 0.15, "ability": (30, 44), "consistency": 0.55},
    "struggling":   {"pct": 0.10, "ability": (18, 32), "consistency": 0.45},
    "failing":      {"pct": 0.04, "ability": (5, 20),  "consistency": 0.35},
    "improving":    {"pct": 0.02, "ability": (45, 65), "consistency": 0.58},
    "inconsistent": {"pct": 0.02, "ability": (35, 72), "consistency": 0.25},
}


# ═══════════════════════════════════════════════════════════════════
#  SCORE GENERATION
# ═══════════════════════════════════════════════════════════════════

def _clip(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return float(np.clip(val, lo, hi))


def _generate_marks(
    label: str,
    base_ability: float,
    consistency: float,
) -> Dict[str, float]:
    """
    Generate subject marks for a student with given label.
    
    The student's elective-aligned subjects get a RELATIVE boost,
    while non-aligned subjects get a penalty. This ensures the label
    is correct even for struggling students.
    """
    affinity = ELECTIVE_SUBJECT_AFFINITY[label]
    boost_map = affinity["boost"]
    penalty_map = affinity["penalize"]

    marks = {}
    noise_std = (1 - consistency) * 12 + 4

    for subj in CANONICAL_SUBJECTS:
        # Start from base ability
        score = base_ability + np.random.normal(0, noise_std)

        # Apply boost/penalty
        if subj in boost_map:
            lo, hi = boost_map[subj]
            score += np.random.uniform(lo, hi)
        elif subj in penalty_map:
            lo, hi = penalty_map[subj]
            score += np.random.uniform(hi, lo)  # hi is negative, lo is less negative
        else:
            # Neutral — small random variation
            score += np.random.uniform(-5, 5)

        marks[subj] = round(_clip(score, 2, 100), 1)

    return marks


def _generate_interests(label: str) -> List[str]:
    """Generate interest list aligned with the elective label."""
    pattern = ELECTIVE_INTEREST_PATTERNS[label]

    interests = []
    # Always include 1-2 primary interests
    n_primary = np.random.choice([1, 2], p=[0.3, 0.7])
    primary = list(np.random.choice(pattern["primary"],
                                      size=min(n_primary, len(pattern["primary"])),
                                      replace=False))
    interests.extend(primary)

    # Sometimes add 1 secondary interest
    if np.random.random() < 0.5 and pattern["secondary"]:
        sec = np.random.choice(pattern["secondary"])
        if sec not in interests:
            interests.append(sec)

    # Rarely add an unlikely interest (noise)
    if np.random.random() < 0.08 and pattern["unlikely"]:
        unl = np.random.choice(pattern["unlikely"])
        if unl not in interests:
            interests.append(unl)

    return interests


def _generate_projects(
    label: str,
    n_projects: int = None,
    base_ability: float = 60,
) -> List[Dict[str, Any]]:
    """Generate project list aligned with the elective label."""
    pool = PROJECT_SKILL_POOLS[label]

    if n_projects is None:
        n_projects = np.random.choice([1, 2, 3, 4], p=[0.2, 0.35, 0.3, 0.15])

    projects = []
    used_titles = set()

    for _ in range(n_projects):
        # Pick a title
        available = [t for t in pool["titles"] if t not in used_titles]
        if not available:
            available = pool["titles"]
        title = np.random.choice(available)
        used_titles.add(title)

        # Pick skills (3-8 from the aligned pool)
        n_skills = np.random.randint(3, min(8, len(pool["skills"])) + 1)
        skills = list(np.random.choice(pool["skills"], size=n_skills, replace=False))

        # Sometimes add 1-2 cross-domain skills (noise/realism)
        if np.random.random() < 0.3:
            other_labels = [l for l in ELECTIVE_LABELS if l != label]
            other = np.random.choice(other_labels)
            other_skills = PROJECT_SKILL_POOLS[other]["skills"]
            noise_skill = np.random.choice(other_skills)
            if noise_skill not in skills:
                skills.append(noise_skill)

        # Pick languages
        n_lang = np.random.randint(1, min(3, len(pool["languages"])) + 1)
        languages = list(np.random.choice(pool["languages"], size=n_lang, replace=False))

        # Pick frameworks
        n_fw = np.random.randint(0, min(3, len(pool["frameworks"])) + 1)
        frameworks = list(np.random.choice(pool["frameworks"], size=n_fw, replace=False))

        # Complexity correlates loosely with ability
        complexity = _clip(
            base_ability / 100 * 0.6 + np.random.uniform(0, 0.4),
            0.1, 1.0
        )

        is_team = np.random.random() < 0.45
        has_github = np.random.random() < (0.3 + base_ability / 200)
        has_demo = np.random.random() < (0.15 + base_ability / 300)

        desc_templates = [
            f"Built a {title.lower()} using {', '.join(skills[:3])}",
            f"Developed {title.lower()} with {languages[0]} and {frameworks[0] if frameworks else skills[0]}",
            f"Created an end-to-end {title.lower()} application",
            f"Implemented {title.lower()} for real-world use case",
        ]

        projects.append({
            "title": title,
            "description": np.random.choice(desc_templates),
            "detailed_description": f"A comprehensive project focusing on {', '.join(skills[:4])}. "
                                     f"Technologies used: {', '.join(frameworks[:2] + languages[:2])}.",
            "programming_languages": languages,
            "frameworks": frameworks,
            "tools": [np.random.choice(["Git", "VS Code", "Jupyter", "Postman", "Docker"])],
            "technologies": skills[:3],
            "extracted_skills": skills,
            "key_achievements": [f"Achieved {np.random.randint(70, 99)}% accuracy" if label == "ML"
                                 else f"Processed {np.random.randint(1000, 50000)} records" if label == "DWM"
                                 else f"Deployed to {np.random.choice(['AWS', 'Azure', 'Heroku'])}" if label == "CCS"
                                 else f"Integrated {np.random.randint(2, 8)} sensors"],
            "learnings": [f"Learned {skills[0]}", f"Improved {skills[1]} skills"],
            "is_team_project": is_team,
            "team_size": np.random.randint(2, 5) if is_team else 1,
            "complexity_score": round(complexity, 2),
            "github_url": "https://github.com/student/project" if has_github else "",
            "demo_url": "https://demo.example.com" if has_demo else "",
        })

    return projects


# ═══════════════════════════════════════════════════════════════════
#  MAIN DATASET GENERATOR
# ═══════════════════════════════════════════════════════════════════

def generate_training_dataset(
    n_samples_per_class: int = 1500,
    include_hard_samples: bool = True,
) -> List[Dict[str, Any]]:
    """
    Generate comprehensive elective recommendation training data.
    
    Covers ALL score ranges from 5 to 100 with proper labels.
    Labels are assigned based on RELATIVE subject alignment,
    not absolute scores.
    
    Args:
        n_samples_per_class: samples per elective class
        include_hard_samples: add ambiguous/borderline samples
    
    Returns:
        List of dicts with keys: marks, interests, projects, label
    """
    dataset = []
    archetype_names = list(STUDENT_ARCHETYPES.keys())
    archetype_probs = [STUDENT_ARCHETYPES[a]["pct"] for a in archetype_names]
    total_p = sum(archetype_probs)
    archetype_probs = [p / total_p for p in archetype_probs]

    for label in ELECTIVE_LABELS:
        logger.info(f"  Generating {n_samples_per_class} samples for {label}...")

        for i in range(n_samples_per_class):
            # Pick archetype
            archetype = np.random.choice(archetype_names, p=archetype_probs)
            cfg = STUDENT_ARCHETYPES[archetype]

            base_ability = np.random.uniform(*cfg["ability"])
            consistency = cfg["consistency"] + np.random.uniform(-0.08, 0.08)
            consistency = np.clip(consistency, 0.15, 0.95)

            # Generate marks with elective-aligned bias
            marks = _generate_marks(label, base_ability, consistency)

            # Generate interests aligned with elective
            interests = _generate_interests(label)

            # Generate projects aligned with elective
            projects = _generate_projects(label, base_ability=base_ability)

            dataset.append({
                "marks": marks,
                "interests": interests,
                "projects": projects,
                "label": label,
                "_archetype": archetype,
                "_base_ability": round(base_ability, 1),
            })

    # ── Add hard/ambiguous samples ──
    if include_hard_samples:
        n_hard = int(n_samples_per_class * 0.15)
        logger.info(f"  Adding {n_hard * 4} hard/ambiguous samples...")

        for label in ELECTIVE_LABELS:
            for _ in range(n_hard):
                base_ability = np.random.uniform(40, 70)
                consistency = 0.3 + np.random.uniform(0, 0.3)

                marks = _generate_marks(label, base_ability, consistency)

                # Mix interests — add some from OTHER electives
                interests = _generate_interests(label)
                other_label = np.random.choice([l for l in ELECTIVE_LABELS if l != label])
                other_interests = _generate_interests(other_label)
                if other_interests and np.random.random() < 0.4:
                    interests.append(other_interests[0])
                interests = list(set(interests))  # deduplicate

                # Mix project skills slightly
                projects = _generate_projects(label, n_projects=np.random.randint(1, 3),
                                              base_ability=base_ability)
                # Add one cross-domain project sometimes
                if np.random.random() < 0.3:
                    cross_project = _generate_projects(other_label, n_projects=1,
                                                       base_ability=base_ability)
                    projects.extend(cross_project)

                dataset.append({
                    "marks": marks,
                    "interests": interests,
                    "projects": projects,
                    "label": label,
                    "_archetype": "hard_sample",
                    "_base_ability": round(base_ability, 1),
                })

    np.random.shuffle(dataset)

    # Print distribution stats
    from collections import Counter
    label_counts = Counter(d["label"] for d in dataset)
    archetype_counts = Counter(d["_archetype"] for d in dataset)
    all_scores = [s for d in dataset for s in d["marks"].values()]

    logger.info(f"\n  📊 Dataset Statistics:")
    logger.info(f"     Total samples: {len(dataset)}")
    logger.info(f"     Labels: {dict(label_counts)}")
    logger.info(f"     Score range: {min(all_scores):.1f} – {max(all_scores):.1f}")
    logger.info(f"     Score mean: {np.mean(all_scores):.1f} ± {np.std(all_scores):.1f}")

    # Score distribution
    bins = [(0, 25), (25, 40), (40, 50), (50, 60), (60, 75), (75, 90), (90, 101)]
    for lo, hi in bins:
        count = sum(1 for s in all_scores if lo <= s < hi)
        pct = count / len(all_scores) * 100
        bar = "█" * int(pct)
        logger.info(f"     {lo:>3}-{hi-1:>3}: {count:>6} ({pct:5.1f}%) {bar}")

    logger.info(f"     Archetypes: {dict(archetype_counts)}")

    return dataset


def generate_training_csv(
    dataset: List[Dict[str, Any]],
    output_path: str,
) -> str:
    """
    Export training dataset to CSV format matching the user's original format.
    
    Format: label, source, age, n_interests, n_projects, interests,
            subj1_name, subj1_score, ..., subj5_name, subj5_score,
            project_title, project_skills
    """
    import csv

    headers = [
        "label", "source", "age", "n_interests", "n_projects", "interests",
        "subject_1_name", "subject_1_score",
        "subject_2_name", "subject_2_score",
        "subject_3_name", "subject_3_score",
        "subject_4_name", "subject_4_score",
        "subject_5_name", "subject_5_score",
        "project_title", "project_skills",
        "archetype", "base_ability",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for sample in dataset:
            marks = sample["marks"]
            interests = sample["interests"]
            projects = sample["projects"]

            # Get top 5 subjects by score
            sorted_subjects = sorted(marks.items(), key=lambda x: x[1], reverse=True)[:5]

            # Flatten project info
            if projects:
                proj_title = projects[0].get("title", "Untitled")
                all_skills = []
                for p in projects:
                    all_skills.extend(p.get("extracted_skills", []))
                proj_skills = "|".join(list(set(all_skills))[:8])
            else:
                proj_title = "No Project"
                proj_skills = ""

            row = [
                sample["label"],
                "synthetic",
                np.random.randint(18, 23),
                len(interests),
                len(projects),
                "|".join(interests),
            ]

            for name, score in sorted_subjects:
                row.extend([name, score])

            # Pad if fewer than 5 subjects
            while len(row) < 6 + 10:
                row.extend(["", 0])

            row.extend([proj_title, proj_skills])
            row.extend([sample.get("_archetype", ""), sample.get("_base_ability", 0)])

            writer.writerow(row)

    logger.info(f"  ✅ CSV exported to {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════════
#  TRAINING FUNCTION (called by scripts/train_models.py)
# ═══════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════
#  SINGLE SAMPLE GENERATOR (used by compare_models.py)
# ═══════════════════════════════════════════════════════════════════

def generate_synthetic_sample(
    label: str,
    noise_level: float = 0.3,
    archetype: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a single synthetic training sample for the given elective label.
    
    Used by:
      - compare_models.py for hard sample generation
      - evaluate_model_accuracy for individual test cases
    
    Args:
        label: One of ML, WT, DWM, CCS
        noise_level: 0.0 (clean) to 1.0 (very noisy)
        archetype: Force a specific archetype, or random
    
    Returns:
        Dict with keys: marks, interests, projects, label
    """
    if archetype is None:
        arch_names = list(STUDENT_ARCHETYPES.keys())
        arch_probs = [STUDENT_ARCHETYPES[a]["pct"] for a in arch_names]
        total_p = sum(arch_probs)
        arch_probs = [p / total_p for p in arch_probs]
        archetype = np.random.choice(arch_names, p=arch_probs)
    
    cfg = STUDENT_ARCHETYPES.get(archetype, STUDENT_ARCHETYPES["average"])
    
    base_ability = np.random.uniform(*cfg["ability"])
    consistency = cfg["consistency"] + np.random.uniform(-0.08, 0.08)
    consistency = np.clip(consistency * (1 - noise_level * 0.5), 0.1, 0.95)
    
    marks = _generate_marks(label, base_ability, consistency)
    interests = _generate_interests(label)
    projects = _generate_projects(label, base_ability=base_ability)
    
    # Apply noise: randomly swap some subject affinities
    if noise_level > 0.3:
        other_labels = [l for l in ELECTIVE_LABELS if l != label]
        other = np.random.choice(other_labels)
        other_marks = _generate_marks(other, base_ability, consistency)
        # Blend some marks from the other label
        blend_ratio = min(noise_level * 0.4, 0.35)
        for subj in marks:
            if np.random.random() < blend_ratio:
                marks[subj] = round(
                    marks[subj] * (1 - blend_ratio) + other_marks.get(subj, marks[subj]) * blend_ratio,
                    1
                )
    
    return {
        "marks": marks,
        "interests": interests,
        "projects": projects,
        "label": label,
        "_archetype": archetype,
        "_base_ability": round(base_ability, 1),
        "_noise_level": noise_level,
    }

async def train_recommendation_model(
    n_synthetic: int = 1500,
    include_feedback: bool = False,
    test_size: float = 0.2,
) -> Dict[str, Any]:
    """
    Generate data, train the recommendation engine, return metrics.
    
    Args:
        n_synthetic: samples per class for synthetic data
        include_feedback: whether to include MongoDB feedback data
        test_size: test split proportion
    """
    from app.ml.models.recommendation_engine import recommendation_engine

    # ── Step 1: Generate synthetic data ──
    logger.info("📦 Generating diverse training data...")
    training_data = generate_training_dataset(
        n_samples_per_class=n_synthetic,
        include_hard_samples=True,
    )

    # ── Step 2: Load feedback from MongoDB (optional) ──
    if include_feedback:
        try:
            from app.models.recommendation import RecommendationFeedback
            feedback_records = await RecommendationFeedback.find_all().to_list()

            for fb in feedback_records:
                if fb.selected_elective and fb.student_marks:
                    training_data.append({
                        "marks": fb.student_marks,
                        "interests": fb.student_interests or [],
                        "projects": fb.student_projects or [],
                        "label": fb.selected_elective,
                    })
            logger.info(f"  Added {len(feedback_records)} feedback records")
        except Exception as e:
            logger.warning(f"  Could not load feedback: {e}")

    # ── Step 3: Export CSV for review ──
    csv_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scripts", "training_data",
    )
    os.makedirs(csv_dir, exist_ok=True)
    csv_path = os.path.join(csv_dir, "elective_training_data.csv")
    generate_training_csv(training_data, csv_path)

    # ── Step 4: Train ──
    logger.info("🚀 Training recommendation model...")
    metrics = recommendation_engine.train(training_data, test_size=test_size)

    logger.info(f"  ✅ Training complete — Accuracy: {metrics['accuracy']:.4f}, F1: {metrics['f1_weighted']:.4f}")

    return metrics


async def evaluate_model_accuracy(
    n_test_per_class: int = 200,
) -> Dict[str, Any]:
    """
    Evaluate model on a fresh held-out test set.
    """
    from app.ml.models.recommendation_engine import recommendation_engine

    if not recommendation_engine.is_trained:
        return {"error": "Model not trained"}

    # Generate fresh test data
    test_data = generate_training_dataset(
        n_samples_per_class=n_test_per_class,
        include_hard_samples=True,
    )

    correct = 0
    total = 0
    per_class_correct = {label: 0 for label in ELECTIVE_LABELS}
    per_class_total = {label: 0 for label in ELECTIVE_LABELS}

    for sample in test_data:
        true_label = sample["label"]
        per_class_total[true_label] += 1
        total += 1

        # Get recommendation
        results = recommendation_engine.recommend_electives(
            marks=sample["marks"],
            interests=sample["interests"],
            projects=sample["projects"],
            use_ml=True,
        )

        if results:
            # The top recommendation's code maps to a label
            top_code = results[0].get("elective_code", "")
            code_to_label = {
                "ITPEC5012": "ML", "ITPEC5013": "WT",
                "ITPEC5014": "DWM", "ITPEC5015": "CCS",
            }
            predicted_label = code_to_label.get(top_code, "")

            if predicted_label == true_label:
                correct += 1
                per_class_correct[true_label] += 1

    accuracy = correct / total if total > 0 else 0

    per_class_accuracy = {}
    for label in ELECTIVE_LABELS:
        if per_class_total[label] > 0:
            per_class_accuracy[label] = round(
                per_class_correct[label] / per_class_total[label], 4
            )
        else:
            per_class_accuracy[label] = 0

    return {
        "accuracy": round(accuracy, 4),
        "total_samples": total,
        "correct": correct,
        "per_class_accuracy": per_class_accuracy,
    }