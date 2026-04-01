# app/ml/utils/training.py
"""
Comprehensive Training Data Generation & Training Pipeline
============================================================
Generates diverse training data for:
  - Program Elective recommendations (ML, WT, DWM, CCS)
  - Open Elective recommendations (RE, OR, CSL, DBM, EAM) — Sem VII

Key design:
  - ALL score ranges (5-100)
  - Student archetypes: toppers, average, struggling, failing, improving
  - Labels based on RELATIVE subject alignment
  - Realistic interest & project skill patterns
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
OPEN_ELECTIVE_LABELS = ["RE", "OR", "CSL", "DBM", "EAM"]

# ═══════════════════════════════════════════════════════════════════
#  PROGRAM ELECTIVE SUBJECT AFFINITY (existing — unchanged)
# ═══════════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════════
#  OPEN ELECTIVE SUBJECT AFFINITY — NEW
# ═══════════════════════════════════════════════════════════════════

OE_SUBJECT_AFFINITY = {
    "RE": {
        "boost": {
            "Engineering Mathematics-III": (10, 22),
            "Engineering Mathematics-IV": (8, 18),
            "Software Engineering": (5, 12),
            "Operating Systems": (3, 10),
            "Data Structures and Algorithms": (2, 8),
        },
        "penalize": {
            "Full Stack Development": (-5, -15),
            "IoT": (-3, -10),
            "Python": (-2, -8),
            "Artificial Intelligence": (-3, -10),
            "Database Management Systems": (-2, -8),
        },
    },
    "OR": {
        "boost": {
            "Engineering Mathematics-III": (10, 22),
            "Engineering Mathematics-IV": (10, 22),
            "Data Structures and Algorithms": (5, 12),
            "Design & Analysis of Algorithms": (5, 15),
            "Python": (2, 8),
        },
        "penalize": {
            "Microcontroller & Embedded Systems": (-5, -15),
            "IoT": (-5, -15),
            "Full Stack Development": (-3, -10),
            "Digital Logic & Design": (-3, -10),
            "Computer Networks": (-2, -8),
        },
    },
    "CSL": {
        "boost": {
            "Computer Networks": (10, 22),
            "Cryptography & Network Security": (10, 22),
            "Operating Systems": (5, 12),
            "Software Engineering": (3, 10),
            "Database Management Systems": (2, 8),
        },
        "penalize": {
            "Engineering Mathematics-III": (-3, -10),
            "IoT": (-3, -10),
            "Microcontroller & Embedded Systems": (-5, -12),
            "Python": (-2, -8),
            "Full Stack Development": (-2, -8),
        },
    },
    "DBM": {
        "boost": {
            "Database Management Systems": (8, 18),
            "Software Engineering": (8, 18),
            "Full Stack Development": (8, 18),
            "Python": (3, 10),
            "Data Structures and Algorithms": (2, 8),
        },
        "penalize": {
            "Microcontroller & Embedded Systems": (-5, -15),
            "IoT": (-5, -12),
            "Digital Logic & Design": (-5, -15),
            "Engineering Mathematics-III": (-3, -10),
            "Engineering Mathematics-IV": (-3, -10),
        },
    },
    "EAM": {
        "boost": {
            "Engineering Mathematics-III": (5, 15),
            "Engineering Mathematics-IV": (5, 15),
            "Microcontroller & Embedded Systems": (8, 18),
            "IoT": (8, 18),
            "Operating Systems": (2, 8),
        },
        "penalize": {
            "Full Stack Development": (-5, -15),
            "Database Management Systems": (-3, -10),
            "Artificial Intelligence": (-5, -15),
            "Software Engineering": (-2, -8),
            "Automata Theory": (-3, -10),
        },
    },
}

# ═══════════════════════════════════════════════════════════════════
#  INTEREST PATTERNS
# ═══════════════════════════════════════════════════════════════════

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

OE_INTEREST_PATTERNS = {
    "RE": {
        "primary": ["Network & Wireless Systems", "Cloud & Distributed Systems"],
        "secondary": ["Data Science & Analytics"],
        "unlikely": ["Web Development", "Artificial Intelligence & Machine Learning"],
    },
    "OR": {
        "primary": ["Data Science & Analytics", "Artificial Intelligence & Machine Learning"],
        "secondary": ["Cloud & Distributed Systems"],
        "unlikely": ["Mobile & IoT Development", "Network & Wireless Systems"],
    },
    "CSL": {
        "primary": ["Network & Wireless Systems"],
        "secondary": ["Cloud & Distributed Systems", "Web Development"],
        "unlikely": ["Artificial Intelligence & Machine Learning", "Mobile & IoT Development"],
    },
    "DBM": {
        "primary": ["Web Development", "Data Science & Analytics"],
        "secondary": ["Cloud & Distributed Systems"],
        "unlikely": ["Mobile & IoT Development", "Network & Wireless Systems"],
    },
    "EAM": {
        "primary": ["Mobile & IoT Development", "Network & Wireless Systems"],
        "secondary": ["Cloud & Distributed Systems"],
        "unlikely": ["Artificial Intelligence & Machine Learning", "Web Development", "Data Science & Analytics"],
    },
}

# ═══════════════════════════════════════════════════════════════════
#  PROJECT SKILL POOLS
# ═══════════════════════════════════════════════════════════════════

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

OE_PROJECT_SKILL_POOLS = {
    "RE": {
        "titles": [
            "System Reliability Simulator", "FMEA Analysis Tool",
            "Fault Tree Generator", "Weibull Distribution Analyzer",
            "Predictive Maintenance Dashboard", "Reliability Database System",
            "Component Failure Tracker", "Markov Chain Simulator",
            "Quality Assurance Automation", "Risk Assessment Calculator",
            "Availability Monitoring Tool", "Redundancy Planner",
            "MTBF/MTTF Calculator", "Bath Tub Curve Visualizer",
        ],
        "skills": [
            "probability", "statistics", "reliability", "fmea", "fault tree",
            "weibull", "matlab", "simulation", "quality", "testing", "risk",
            "markov", "maintenance", "statistical analysis", "mtbf", "mttf",
            "python", "numpy", "scipy", "excel", "data analysis",
        ],
        "languages": ["Python", "MATLAB", "R", "Excel VBA"],
        "frameworks": ["SciPy", "NumPy", "Matplotlib", "Reliability (Python lib)"],
    },
    "OR": {
        "titles": [
            "Linear Programming Solver", "Job Scheduling Optimizer",
            "Supply Chain Simulator", "Inventory Management System",
            "Queue Simulation Tool", "Transportation Problem Solver",
            "Game Theory Analyzer", "Monte Carlo Simulator",
            "Resource Allocation Optimizer", "Production Planning Tool",
            "Network Flow Optimizer", "Assignment Problem Solver",
            "Dynamic Programming Visualizer", "Cost Optimization Dashboard",
        ],
        "skills": [
            "optimization", "linear programming", "simulation", "queuing",
            "monte carlo", "scheduling", "inventory", "supply chain",
            "game theory", "dynamic programming", "simplex", "python",
            "scipy", "numpy", "matlab", "operations research",
            "mathematical model", "cost optimization", "resource allocation",
        ],
        "languages": ["Python", "MATLAB", "R", "Java"],
        "frameworks": ["SciPy", "PuLP", "OR-Tools", "SimPy"],
    },
    "CSL": {
        "titles": [
            "Network Vulnerability Scanner", "Phishing Detection System",
            "Firewall Rule Analyzer", "Intrusion Detection System",
            "Password Strength Analyzer", "Cyber Incident Logger",
            "Compliance Audit Checker", "Digital Forensics Toolkit",
            "Malware Behavior Analyzer", "Web Application Security Scanner",
            "IT Act Compliance Dashboard", "Data Privacy Audit Tool",
            "Social Engineering Awareness Platform", "Encryption/Decryption Tool",
        ],
        "skills": [
            "security", "cyber", "hacking", "penetration testing", "firewall",
            "encryption", "phishing", "malware", "forensics", "compliance",
            "vulnerability", "authentication", "gdpr", "iso 27001",
            "network security", "intrusion detection", "python",
            "sql injection", "xss", "social engineering", "cryptography",
        ],
        "languages": ["Python", "Bash", "C", "JavaScript"],
        "frameworks": ["Scapy", "Nmap", "Wireshark", "Metasploit", "OWASP ZAP"],
    },
    "DBM": {
        "titles": [
            "E-Commerce Analytics Dashboard", "Social Media Marketing Tool",
            "SEO Keyword Analyzer", "Customer Journey Mapper",
            "A/B Testing Platform", "CRM System", "Digital Ad Manager",
            "Product Recommendation Engine", "KPI Dashboard Builder",
            "Subscription Management Platform", "Content Management System",
            "Market Research Aggregator", "Lead Scoring System",
            "Omni-channel Analytics Tool", "Growth Metrics Tracker",
        ],
        "skills": [
            "digital marketing", "seo", "sem", "social media", "analytics",
            "ecommerce", "crm", "a/b testing", "marketing", "business",
            "strategy", "dashboard", "kpi", "product management", "agile",
            "api", "platform", "web", "react", "node", "fullstack",
            "recommendation", "personalization", "sql", "python",
        ],
        "languages": ["Python", "JavaScript", "SQL", "TypeScript"],
        "frameworks": ["React", "Node.js", "Django", "Tableau", "Google Analytics"],
    },
    "EAM": {
        "titles": [
            "Energy Consumption Monitor", "Solar Panel Efficiency Tracker",
            "Smart Grid Simulator", "Building Energy Audit Tool",
            "HVAC Optimization System", "Power Factor Analyzer",
            "Carbon Footprint Calculator", "Renewable Energy Dashboard",
            "Motor Efficiency Tester", "Lighting Audit Automation",
            "Energy Cost Optimizer", "Green Building Assessment Tool",
            "Industrial Energy Logger", "Heat Exchanger Performance Tool",
        ],
        "skills": [
            "energy", "audit", "solar", "renewable", "sustainability",
            "power", "electrical", "thermal", "hvac", "boiler",
            "green building", "conservation", "efficiency", "carbon",
            "iot", "smart grid", "monitoring", "sensor", "automation",
            "arduino", "raspberry pi", "python", "led", "motor",
        ],
        "languages": ["Python", "C", "MATLAB", "Arduino C++"],
        "frameworks": ["Arduino IDE", "Matplotlib", "Pandas", "Streamlit", "Node-RED"],
    },
}

# ═══════════════════════════════════════════════════════════════════
#  STUDENT ARCHETYPES
# ═══════════════════════════════════════════════════════════════════

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
    affinity_map: Dict[str, Dict] = None,
) -> Dict[str, float]:
    if affinity_map is None:
        affinity_map = ELECTIVE_SUBJECT_AFFINITY
    affinity = affinity_map[label]
    boost_map = affinity["boost"]
    penalty_map = affinity["penalize"]

    marks = {}
    noise_std = (1 - consistency) * 12 + 4

    for subj in CANONICAL_SUBJECTS:
        score = base_ability + np.random.normal(0, noise_std)
        if subj in boost_map:
            lo, hi = boost_map[subj]
            score += np.random.uniform(lo, hi)
        elif subj in penalty_map:
            lo, hi = penalty_map[subj]
            score += np.random.uniform(hi, lo)
        else:
            score += np.random.uniform(-5, 5)
        marks[subj] = round(_clip(score, 2, 100), 1)

    return marks


def _generate_interests(label: str, pattern_map: Dict[str, Dict] = None) -> List[str]:
    if pattern_map is None:
        pattern_map = ELECTIVE_INTEREST_PATTERNS
    pattern = pattern_map[label]
    interests = []
    n_primary = np.random.choice([1, 2], p=[0.3, 0.7])
    primary = list(np.random.choice(
        pattern["primary"],
        size=min(n_primary, len(pattern["primary"])),
        replace=False
    ))
    interests.extend(primary)
    if np.random.random() < 0.5 and pattern["secondary"]:
        sec = np.random.choice(pattern["secondary"])
        if sec not in interests:
            interests.append(sec)
    if np.random.random() < 0.08 and pattern["unlikely"]:
        unl = np.random.choice(pattern["unlikely"])
        if unl not in interests:
            interests.append(unl)
    return interests


def _generate_projects(
    label: str,
    n_projects: int = None,
    base_ability: float = 60,
    skill_pool_map: Dict[str, Dict] = None,
    all_labels: List[str] = None,
) -> List[Dict[str, Any]]:
    if skill_pool_map is None:
        skill_pool_map = PROJECT_SKILL_POOLS
    if all_labels is None:
        all_labels = ELECTIVE_LABELS
    pool = skill_pool_map[label]

    if n_projects is None:
        n_projects = np.random.choice([1, 2, 3, 4], p=[0.2, 0.35, 0.3, 0.15])

    projects = []
    used_titles = set()

    for _ in range(n_projects):
        available = [t for t in pool["titles"] if t not in used_titles]
        if not available:
            available = pool["titles"]
        title = np.random.choice(available)
        used_titles.add(title)

        n_skills = np.random.randint(3, min(8, len(pool["skills"])) + 1)
        skills = list(np.random.choice(pool["skills"], size=n_skills, replace=False))

        if np.random.random() < 0.3:
            other_labels = [l for l in all_labels if l != label]
            if other_labels:
                other = np.random.choice(other_labels)
                if other in skill_pool_map:
                    other_skills = skill_pool_map[other]["skills"]
                    noise_skill = np.random.choice(other_skills)
                    if noise_skill not in skills:
                        skills.append(noise_skill)

        n_lang = np.random.randint(1, min(3, len(pool["languages"])) + 1)
        languages = list(np.random.choice(pool["languages"], size=n_lang, replace=False))

        n_fw = np.random.randint(0, min(3, len(pool["frameworks"])) + 1)
        frameworks = list(np.random.choice(pool["frameworks"], size=n_fw, replace=False))

        complexity = _clip(base_ability / 100 * 0.6 + np.random.uniform(0, 0.4), 0.1, 1.0)
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
            "tools": [np.random.choice(["Git", "VS Code", "Jupyter", "Postman", "Docker", "Excel", "MATLAB"])],
            "technologies": skills[:3],
            "extracted_skills": skills,
            "key_achievements": [_generate_achievement(label, skills)],
            "learnings": [f"Learned {skills[0]}", f"Improved {skills[1]} skills"],
            "is_team_project": is_team,
            "team_size": np.random.randint(2, 5) if is_team else 1,
            "complexity_score": round(complexity, 2),
            "github_url": "https://github.com/student/project" if has_github else "",
            "demo_url": "https://demo.example.com" if has_demo else "",
        })

    return projects


def _generate_achievement(label: str, skills: List[str]) -> str:
    templates = {
        "ML": f"Achieved {np.random.randint(70, 99)}% accuracy",
        "WT": f"Integrated {np.random.randint(2, 8)} sensors",
        "DWM": f"Processed {np.random.randint(1000, 50000)} records",
        "CCS": f"Deployed to {np.random.choice(['AWS', 'Azure', 'Heroku'])}",
        "RE": f"Analyzed {np.random.randint(5, 50)} failure modes",
        "OR": f"Optimized cost by {np.random.randint(10, 40)}%",
        "CSL": f"Detected {np.random.randint(10, 100)} vulnerabilities",
        "DBM": f"Improved conversion rate by {np.random.randint(5, 35)}%",
        "EAM": f"Reduced energy consumption by {np.random.randint(8, 30)}%",
    }
    return templates.get(label, f"Completed using {skills[0]}")


# ═══════════════════════════════════════════════════════════════════
#  MAIN DATASET GENERATORS
# ═══════════════════════════════════════════════════════════════════

def generate_training_dataset(
    n_samples_per_class: int = 1500,
    include_hard_samples: bool = True,
) -> List[Dict[str, Any]]:
    """Generate Program Elective (ML/WT/DWM/CCS) training data."""
    return _generate_dataset_generic(
        labels=ELECTIVE_LABELS,
        affinity_map=ELECTIVE_SUBJECT_AFFINITY,
        interest_map=ELECTIVE_INTEREST_PATTERNS,
        skill_pool_map=PROJECT_SKILL_POOLS,
        n_samples_per_class=n_samples_per_class,
        include_hard_samples=include_hard_samples,
        dataset_name="Program Elective",
    )


def generate_oe_training_dataset(
    n_samples_per_class: int = 1500,
    include_hard_samples: bool = True,
) -> List[Dict[str, Any]]:
    """Generate Open Elective (RE/OR/CSL/DBM/EAM) training data."""
    return _generate_dataset_generic(
        labels=OPEN_ELECTIVE_LABELS,
        affinity_map=OE_SUBJECT_AFFINITY,
        interest_map=OE_INTEREST_PATTERNS,
        skill_pool_map=OE_PROJECT_SKILL_POOLS,
        n_samples_per_class=n_samples_per_class,
        include_hard_samples=include_hard_samples,
        dataset_name="Open Elective",
    )


def _generate_dataset_generic(
    labels: List[str],
    affinity_map: Dict,
    interest_map: Dict,
    skill_pool_map: Dict,
    n_samples_per_class: int,
    include_hard_samples: bool,
    dataset_name: str,
) -> List[Dict[str, Any]]:
    dataset = []
    archetype_names = list(STUDENT_ARCHETYPES.keys())
    archetype_probs = [STUDENT_ARCHETYPES[a]["pct"] for a in archetype_names]
    total_p = sum(archetype_probs)
    archetype_probs = [p / total_p for p in archetype_probs]

    for label in labels:
        logger.info(f"  Generating {n_samples_per_class} {dataset_name} samples for {label}...")

        for i in range(n_samples_per_class):
            archetype = np.random.choice(archetype_names, p=archetype_probs)
            cfg = STUDENT_ARCHETYPES[archetype]
            base_ability = np.random.uniform(*cfg["ability"])
            consistency = cfg["consistency"] + np.random.uniform(-0.08, 0.08)
            consistency = np.clip(consistency, 0.15, 0.95)

            marks = _generate_marks(label, base_ability, consistency, affinity_map)
            interests = _generate_interests(label, interest_map)
            projects = _generate_projects(label, base_ability=base_ability,
                                          skill_pool_map=skill_pool_map, all_labels=labels)

            dataset.append({
                "marks": marks,
                "interests": interests,
                "projects": projects,
                "label": label,
                "_archetype": archetype,
                "_base_ability": round(base_ability, 1),
            })

    if include_hard_samples:
        n_hard = int(n_samples_per_class * 0.15)
        logger.info(f"  Adding {n_hard * len(labels)} hard/ambiguous {dataset_name} samples...")

        for label in labels:
            for _ in range(n_hard):
                base_ability = np.random.uniform(40, 70)
                consistency = 0.3 + np.random.uniform(0, 0.3)

                marks = _generate_marks(label, base_ability, consistency, affinity_map)
                interests = _generate_interests(label, interest_map)
                other_label = np.random.choice([l for l in labels if l != label])
                other_interests = _generate_interests(other_label, interest_map)
                if other_interests and np.random.random() < 0.4:
                    interests.append(other_interests[0])
                interests = list(set(interests))

                projects = _generate_projects(label, n_projects=np.random.randint(1, 3),
                                              base_ability=base_ability,
                                              skill_pool_map=skill_pool_map, all_labels=labels)
                if np.random.random() < 0.3:
                    cross_project = _generate_projects(other_label, n_projects=1,
                                                       base_ability=base_ability,
                                                       skill_pool_map=skill_pool_map, all_labels=labels)
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

    from collections import Counter
    label_counts = Counter(d["label"] for d in dataset)
    all_scores = [s for d in dataset for s in d["marks"].values()]

    logger.info(f"\n  📊 {dataset_name} Dataset Statistics:")
    logger.info(f"     Total samples: {len(dataset)}")
    logger.info(f"     Labels: {dict(label_counts)}")
    logger.info(f"     Score range: {min(all_scores):.1f} – {max(all_scores):.1f}")
    logger.info(f"     Score mean: {np.mean(all_scores):.1f} ± {np.std(all_scores):.1f}")

    return dataset


def generate_training_csv(
    dataset: List[Dict[str, Any]],
    output_path: str,
) -> str:
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

            sorted_subjects = sorted(marks.items(), key=lambda x: x[1], reverse=True)[:5]

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

            while len(row) < 6 + 10:
                row.extend(["", 0])

            row.extend([proj_title, proj_skills])
            row.extend([sample.get("_archetype", ""), sample.get("_base_ability", 0)])

            writer.writerow(row)

    logger.info(f"  ✅ CSV exported to {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════════
#  SINGLE SAMPLE GENERATOR
# ═══════════════════════════════════════════════════════════════════

def generate_synthetic_sample(
    label: str,
    noise_level: float = 0.3,
    archetype: Optional[str] = None,
    is_open_elective: bool = False,
) -> Dict[str, Any]:
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

    if is_open_elective:
        affinity_map = OE_SUBJECT_AFFINITY
        interest_map = OE_INTEREST_PATTERNS
        skill_pool_map = OE_PROJECT_SKILL_POOLS
        all_labels = OPEN_ELECTIVE_LABELS
    else:
        affinity_map = ELECTIVE_SUBJECT_AFFINITY
        interest_map = ELECTIVE_INTEREST_PATTERNS
        skill_pool_map = PROJECT_SKILL_POOLS
        all_labels = ELECTIVE_LABELS

    marks = _generate_marks(label, base_ability, consistency, affinity_map)
    interests = _generate_interests(label, interest_map)
    projects = _generate_projects(label, base_ability=base_ability,
                                  skill_pool_map=skill_pool_map, all_labels=all_labels)

    if noise_level > 0.3:
        other_labels = [l for l in all_labels if l != label]
        other = np.random.choice(other_labels)
        other_marks = _generate_marks(other, base_ability, consistency, affinity_map)
        blend_ratio = min(noise_level * 0.4, 0.35)
        for subj in marks:
            if np.random.random() < blend_ratio:
                marks[subj] = round(
                    marks[subj] * (1 - blend_ratio) + other_marks.get(subj, marks[subj]) * blend_ratio,
                    1
                )

    return {
        "marks": marks, "interests": interests, "projects": projects,
        "label": label, "_archetype": archetype,
        "_base_ability": round(base_ability, 1), "_noise_level": noise_level,
    }


# ═══════════════════════════════════════════════════════════════════
#  TRAINING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

async def train_recommendation_model(
    n_synthetic: int = 1500,
    include_feedback: bool = False,
    test_size: float = 0.2,
) -> Dict[str, Any]:
    """Train BOTH Program Elective and Open Elective models."""
    from app.ml.models.recommendation_engine import recommendation_engine

    # ── Step 1: Program Elective model ──
    logger.info("📦 Generating Program Elective training data...")
    pec_data = generate_training_dataset(
        n_samples_per_class=n_synthetic,
        include_hard_samples=True,
    )

    if include_feedback:
        try:
            from app.models.recommendation import RecommendationFeedback
            feedback_records = await RecommendationFeedback.find_all().to_list()
            for fb in feedback_records:
                if fb.selected_elective and fb.student_marks:
                    pec_data.append({
                        "marks": fb.student_marks,
                        "interests": fb.student_interests or [],
                        "projects": fb.student_projects or [],
                        "label": fb.selected_elective,
                    })
            logger.info(f"  Added {len(feedback_records)} feedback records")
        except Exception as e:
            logger.warning(f"  Could not load feedback: {e}")

    csv_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scripts", "training_data",
    )
    os.makedirs(csv_dir, exist_ok=True)

    pec_csv = os.path.join(csv_dir, "elective_training_data.csv")
    generate_training_csv(pec_data, pec_csv)

    logger.info("🚀 Training Program Elective model...")
    pec_metrics = recommendation_engine.train(pec_data, test_size=test_size)
    logger.info(f"  ✅ PEC Training — Accuracy: {pec_metrics['accuracy']:.4f}, F1: {pec_metrics['f1_weighted']:.4f}")

    # ── Step 2: Open Elective model ──
    logger.info("📦 Generating Open Elective training data...")
    oec_data = generate_oe_training_dataset(
        n_samples_per_class=n_synthetic,
        include_hard_samples=True,
    )

    oec_csv = os.path.join(csv_dir, "oe_training_data.csv")
    generate_training_csv(oec_data, oec_csv)

    logger.info("🚀 Training Open Elective model...")
    oec_metrics = recommendation_engine.train_open_electives(oec_data, test_size=test_size)
    logger.info(f"  ✅ OEC Training — Accuracy: {oec_metrics['accuracy']:.4f}, F1: {oec_metrics['f1_weighted']:.4f}")

    return {
        "program_elective_metrics": pec_metrics,
        "open_elective_metrics": oec_metrics,
        "total_pec_samples": len(pec_data),
        "total_oec_samples": len(oec_data),
    }


async def evaluate_model_accuracy(
    n_test_per_class: int = 200,
) -> Dict[str, Any]:
    from app.ml.models.recommendation_engine import recommendation_engine

    if not recommendation_engine.is_trained:
        return {"error": "Model not trained"}

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

        results = recommendation_engine.recommend_electives(
            marks=sample["marks"],
            interests=sample["interests"],
            projects=sample["projects"],
            use_ml=True,
        )

        if results:
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
            per_class_accuracy[label] = round(per_class_correct[label] / per_class_total[label], 4)
        else:
            per_class_accuracy[label] = 0

    # Also evaluate OE model
    oe_results = {}
    if recommendation_engine.oe_is_trained:
        oe_test = generate_oe_training_dataset(n_samples_per_class=n_test_per_class, include_hard_samples=True)
        oe_correct = 0
        oe_total = 0
        oe_per_class = {l: {"correct": 0, "total": 0} for l in OPEN_ELECTIVE_LABELS}

        oe_code_to_label = {
            "OEC7012": "RE", "OEC7015": "OR", "OEC7016": "CSL",
            "OEC7017": "DBM", "OEC7018": "EAM",
        }

        for sample in oe_test:
            true_label = sample["label"]
            oe_per_class[true_label]["total"] += 1
            oe_total += 1

            recs = recommendation_engine.recommend_open_electives(
                marks=sample["marks"], interests=sample["interests"],
                projects=sample["projects"], use_ml=True,
            )
            if recs:
                pred = oe_code_to_label.get(recs[0].get("elective_code", ""), "")
                if pred == true_label:
                    oe_correct += 1
                    oe_per_class[true_label]["correct"] += 1

        oe_results = {
            "accuracy": round(oe_correct / oe_total, 4) if oe_total else 0,
            "total_samples": oe_total,
            "per_class_accuracy": {
                l: round(v["correct"] / v["total"], 4) if v["total"] else 0
                for l, v in oe_per_class.items()
            },
        }

    return {
        "program_electives": {
            "accuracy": round(accuracy, 4),
            "total_samples": total,
            "correct": correct,
            "per_class_accuracy": per_class_accuracy,
        },
        "open_electives": oe_results,
    }