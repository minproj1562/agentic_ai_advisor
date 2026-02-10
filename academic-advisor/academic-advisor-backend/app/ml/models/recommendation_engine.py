# app/ml/models/recommendation_engine.py
"""
Enhanced Cumulative Recommendation Engine
==========================================
Marks (40%) + Interests (30%) + Projects (30%)

NEW FEATURES:
  - Structured score breakdown for frontend visualization
  - Per-category confidence levels
  - "What's missing" indicators
  - Ranking explanation with comparisons
"""

import numpy as np
import os
import json
import joblib
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from collections import defaultdict

from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity as cos_sim
    HAS_SBERT = True
except ImportError:
    HAS_SBERT = False

# ═══════════════════════════════════════════════════════════════════
#  SUBJECT-NAME ALIASES
# ═══════════════════════════════════════════════════════════════════

_ALIASES: Dict[str, str] = {
    "Data Structures and Algorithms": "Data Structures and Algorithms",
    "Database Management Systems": "Database Management Systems",
    "Operating Systems": "Operating Systems",
    "Computer Networks": "Computer Networks",
    "Microcontroller & Embedded Systems": "Microcontroller & Embedded Systems",
    "Software Engineering": "Software Engineering",
    "Digital Logic & Design": "Digital Logic & Design",
    "Digital Logic & Computer Architecture": "Digital Logic & Design",
    "Artificial Intelligence": "Artificial Intelligence",
    "Design & Analysis of Algorithms": "Design & Analysis of Algorithms",
    "Automata Theory / Theory of Computer Science": "Automata Theory",
    "Cryptography & Network Security": "Cryptography & Network Security",
    "Engineering Mathematics-III": "Engineering Mathematics-III",
    "Engineering Mathematics-IV": "Engineering Mathematics-IV",
    "Python Programming Lab": "Python",
    "Python Programming": "Python",
    "Python": "Python",
    "C++ Programming": "C++",
    "C": "C",
    "Java": "Java",
    "DSA Laboratory": "DSA Lab",
    "DBMS Laboratory": "DBMS Lab",
    "Cloud Computing Laboratory": "Cloud Lab",
    "Mobile App Development Lab (Flutter)": "Flutter Lab",
    "Database Management System": "Database Management Systems",
    "DBMS": "Database Management Systems",
    "DSA": "Data Structures and Algorithms",
    "OS": "Operating Systems",
    "CN": "Computer Networks",
    "SE": "Software Engineering",
    "AI": "Artificial Intelligence",
    "Microprocessor and Embedded Systems": "Microcontroller & Embedded Systems",
    "Full Stack Development (FSDL)": "Full Stack Development",
    "Full Stack Development": "Full Stack Development",
    "Flutter": "Flutter Lab",
    "Internet of Things (IoT)": "IoT",
    "IoT": "IoT",
}

def _canonical(name: str) -> str:
    return _ALIASES.get(name, name)

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

ALL_SUBJECTS = CANONICAL_SUBJECTS

# ═══════════════════════════════════════════════════════════════════
#  ELECTIVE CATALOGUE
# ═══════════════════════════════════════════════════════════════════

ELECTIVE_META = {
    "ML": {
        "code": "ITPEC5012",
        "name": "Machine Learning",
        "credits": 3,
        "pair": "Pair 1 (ML vs WT)",
        "career_paths": ["ML Engineer", "Data Scientist", "AI Researcher", "NLP Engineer"],
        "skills": ["TensorFlow", "PyTorch", "Scikit-learn", "Neural Networks", "NLP"],
        "description": "Machine Learning covers supervised and unsupervised learning, neural networks, deep learning, NLP, and model deployment.",
    },
    "WT": {
        "code": "ITPEC5013",
        "name": "Wireless Technology",
        "credits": 3,
        "pair": "Pair 1 (ML vs WT)",
        "career_paths": ["IoT Engineer", "Network Engineer", "Embedded Developer", "RF Engineer"],
        "skills": ["IoT Protocols", "Embedded C", "Wireless Networks", "Sensor Integration"],
        "description": "Wireless Technology covers cellular networks, IoT protocols, sensor networks, MQTT, Bluetooth, ZigBee, and 5G.",
    },
    "DWM": {
        "code": "ITPEC5014",
        "name": "Data Warehouse and Mining",
        "credits": 3,
        "pair": "Pair 2 (DWM vs CCS)",
        "career_paths": ["Data Analyst", "BI Developer", "Data Engineer", "Analytics Manager"],
        "skills": ["SQL", "ETL", "OLAP", "Clustering", "Association Rules"],
        "description": "Data Warehousing and Mining covers OLAP, ETL, data cubes, classification, clustering, association rule mining, and BI tools.",
    },
    "CCS": {
        "code": "ITPEC5015",
        "name": "Cloud Computing Services",
        "credits": 3,
        "pair": "Pair 2 (DWM vs CCS)",
        "career_paths": ["Cloud Architect", "DevOps Engineer", "SRE", "Platform Engineer"],
        "skills": ["AWS", "Azure", "Docker", "Kubernetes", "Terraform"],
        "description": "Cloud Computing Services covers virtualisation, containers, AWS/Azure/GCP, serverless, micro-services, and CI/CD pipelines.",
    },
}

SUBJECT_WEIGHTS: Dict[str, Dict[str, float]] = {
    "ML": {
        "Python": 3.0, "Data Structures and Algorithms": 2.5,
        "Engineering Mathematics-III": 2.0, "Engineering Mathematics-IV": 1.5,
        "Database Management Systems": 1.5, "Artificial Intelligence": 3.5, "Java": 1.0,
    },
    "WT": {
        "Computer Networks": 3.5, "Microcontroller & Embedded Systems": 3.0,
        "IoT": 3.5, "Operating Systems": 2.0, "Digital Logic & Design": 2.0, "C++": 1.5,
    },
    "DWM": {
        "Database Management Systems": 3.5, "Data Structures and Algorithms": 2.5,
        "Python": 2.0, "Engineering Mathematics-IV": 1.5, "Java": 1.5,
    },
    "CCS": {
        "Computer Networks": 3.0, "Operating Systems": 2.5,
        "Database Management Systems": 2.0, "Full Stack Development": 3.0,
        "Software Engineering": 2.0, "Python": 1.5,
    },
}

INTEREST_ELECTIVE_MAP = {
    "ML": [("Artificial Intelligence & Machine Learning", 2.0), ("Data Science & Analytics", 1.5)],
    "WT": [("Network & Wireless Systems", 2.0), ("Mobile & IoT Development", 1.5)],
    "DWM": [("Data Science & Analytics", 2.0), ("Artificial Intelligence & Machine Learning", 1.0)],
    "CCS": [("Cloud & Distributed Systems", 2.0), ("Web Development", 1.5)],
}

PROJECT_SKILL_MAP = {
    "ML": [
        "python", "tensorflow", "pytorch", "sklearn", "scikit-learn",
        "machine learning", "deep learning", "nlp", "neural network",
        "data science", "pandas", "numpy", "keras", "computer vision",
        "regression", "classification", "clustering",
    ],
    "WT": [
        "arduino", "raspberry pi", "iot", "embedded", "sensor",
        "wireless", "bluetooth", "zigbee", "mqtt", "microcontroller",
        "esp32", "esp8266", "lora", "rfid",
    ],
    "DWM": [
        "sql", "mongodb", "data warehouse", "etl", "hadoop", "spark",
        "data mining", "analytics", "tableau", "power bi", "olap",
        "data pipeline", "redshift", "bigquery",
    ],
    "CCS": [
        "aws", "azure", "gcp", "docker", "kubernetes", "cloud",
        "devops", "terraform", "serverless", "microservices",
        "ci/cd", "jenkins", "react", "node", "web", "fullstack",
        "rest api", "graphql", "nginx",
    ],
}

INTEREST_KEYWORD_MAP = {
    "Artificial Intelligence & Machine Learning": ["ai", "ml", "machine learning", "deep learning", "nlp", "data science"],
    "Mobile & IoT Development": ["mobile", "iot", "android", "ios", "flutter", "embedded", "arduino"],
    "Web Development": ["web", "frontend", "backend", "fullstack", "react", "angular", "node"],
    "Data Science & Analytics": ["data", "analytics", "statistics", "visualization", "bi", "tableau"],
    "Cloud & Distributed Systems": ["cloud", "aws", "azure", "distributed", "devops", "docker", "kubernetes"],
    "Network & Wireless Systems": ["network", "wireless", "security", "cyber", "routing", "protocol"],
}

HONOURS_PROGRAMS = [
    {
        "program": "AI / ML Honours",
        "type": "honours",
        "required_cgpa": 7.5,
        "relevant_subjects": ["Python", "Artificial Intelligence", "Data Structures and Algorithms"],
        "relevant_interests": ["Artificial Intelligence & Machine Learning", "Data Science & Analytics"],
        "project_keywords": ["python", "tensorflow", "pytorch", "machine learning"],
        "career_paths": ["ML Engineer", "Data Scientist", "AI Researcher"],
        "skills_gained": ["Deep Learning", "NLP", "Computer Vision", "MLOps"],
    },
    {
        "program": "Data Science Honours",
        "type": "honours",
        "required_cgpa": 7.5,
        "relevant_subjects": ["Database Management Systems", "Python", "Data Structures and Algorithms"],
        "relevant_interests": ["Data Science & Analytics", "Artificial Intelligence & Machine Learning"],
        "project_keywords": ["sql", "data", "analytics", "pandas", "visualization"],
        "career_paths": ["Data Scientist", "Analytics Manager", "Research Scientist"],
        "skills_gained": ["Statistical Analysis", "Big Data", "Data Visualisation"],
    },
    {
        "program": "Cybersecurity Minor",
        "type": "minor",
        "required_cgpa": 7.0,
        "relevant_subjects": ["Computer Networks", "Operating Systems", "Cryptography & Network Security"],
        "relevant_interests": ["Network & Wireless Systems", "Cloud & Distributed Systems"],
        "project_keywords": ["security", "network", "firewall", "encryption", "penetration"],
        "career_paths": ["Security Analyst", "Penetration Tester", "Security Architect"],
        "skills_gained": ["Network Security", "Cryptography", "Ethical Hacking"],
    },
    {
        "program": "Cloud Computing Minor",
        "type": "minor",
        "required_cgpa": 7.0,
        "relevant_subjects": ["Computer Networks", "Operating Systems", "Full Stack Development"],
        "relevant_interests": ["Cloud & Distributed Systems", "Web Development"],
        "project_keywords": ["aws", "azure", "docker", "kubernetes", "cloud", "devops"],
        "career_paths": ["Cloud Architect", "DevOps Engineer", "SRE"],
        "skills_gained": ["Cloud Architecture", "Containerisation", "CI/CD"],
    },
    {
        "program": "IoT & Embedded Minor",
        "type": "minor",
        "required_cgpa": 6.5,
        "relevant_subjects": ["Microcontroller & Embedded Systems", "Computer Networks", "IoT"],
        "relevant_interests": ["Mobile & IoT Development", "Network & Wireless Systems"],
        "project_keywords": ["iot", "arduino", "raspberry", "embedded", "sensor"],
        "career_paths": ["IoT Engineer", "Embedded Developer", "Hardware Engineer"],
        "skills_gained": ["Embedded Programming", "Sensor Integration", "IoT Protocols"],
    },
]

CAREER_CATALOG = [
    {
        "career": "Software Development Engineer",
        "required_cgpa": 7.0,
        "salary_range": "₹6-15 LPA",
        "growth_potential": "High",
        "top_companies": ["Google", "Microsoft", "Amazon", "Flipkart"],
        "relevant_electives": ["ML", "CCS"],
        "relevant_interests": ["Web Development", "Cloud & Distributed Systems"],
        "project_keywords": ["web", "api", "fullstack", "react", "node"],
        "required_certifications": ["AWS Cloud Practitioner"],
        "preparation_path": ["Master DSA", "Build full-stack projects", "Practice LeetCode"],
    },
    {
        "career": "Data Scientist",
        "required_cgpa": 7.5,
        "salary_range": "₹8-20 LPA",
        "growth_potential": "Very High",
        "top_companies": ["Google", "Amazon", "Netflix", "Uber"],
        "relevant_electives": ["ML", "DWM"],
        "relevant_interests": ["Artificial Intelligence & Machine Learning", "Data Science & Analytics"],
        "project_keywords": ["machine learning", "data", "python", "tensorflow"],
        "required_certifications": ["Google Data Analytics", "IBM Data Science"],
        "preparation_path": ["Complete ML courses", "Build ML projects", "Kaggle competitions"],
    },
    {
        "career": "Cloud / DevOps Engineer",
        "required_cgpa": 6.5,
        "salary_range": "₹7-18 LPA",
        "growth_potential": "High",
        "top_companies": ["AWS", "Microsoft Azure", "Google Cloud"],
        "relevant_electives": ["CCS"],
        "relevant_interests": ["Cloud & Distributed Systems", "Network & Wireless Systems"],
        "project_keywords": ["docker", "kubernetes", "aws", "cloud", "devops"],
        "required_certifications": ["AWS Solutions Architect"],
        "preparation_path": ["Get cloud certification", "Learn Docker/K8s", "Build CI/CD pipelines"],
    },
    {
        "career": "IoT / Embedded Engineer",
        "required_cgpa": 6.5,
        "salary_range": "₹5-14 LPA",
        "growth_potential": "High",
        "top_companies": ["Bosch", "Siemens", "Texas Instruments", "Qualcomm"],
        "relevant_electives": ["WT"],
        "relevant_interests": ["Mobile & IoT Development", "Network & Wireless Systems"],
        "project_keywords": ["iot", "arduino", "embedded", "sensor", "raspberry pi"],
        "required_certifications": ["ARM Certified Engineer"],
        "preparation_path": ["Master embedded C/C++", "Build IoT prototypes"],
    },
]


# ═══════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════

def _normalise_interests(raw) -> Dict[str, float]:
    rated = {a: 0.0 for a in INTEREST_AREAS}
    if isinstance(raw, dict):
        for area, val in raw.items():
            if area in rated:
                rated[area] = float(val) / 5.0 if val > 1 else float(val)
        return rated
    if isinstance(raw, list):
        for s in raw:
            low = s.lower().strip()
            for area in INTEREST_AREAS:
                if area.lower() == low:
                    rated[area] = 1.0
                    break
            else:
                for area, kws in INTEREST_KEYWORD_MAP.items():
                    if any(kw in low for kw in kws):
                        rated[area] = max(rated[area], 1.0)
                        break
    return rated


def _canonicalise_marks(marks: Dict[str, float]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for name, val in marks.items():
        canon = _canonical(name)
        out[canon] = max(out.get(canon, 0), val)
    return out


def _project_hits(projects: List[Dict[str, Any]], keywords: List[str]) -> int:
    hits = 0
    for p in projects:
        blob = " ".join([
            p.get("title", ""),
            p.get("description", ""),
            " ".join(p.get("programming_languages", [])),
            " ".join(p.get("frameworks", [])),
            " ".join(p.get("tools", [])),
            " ".join(p.get("technologies", [])),
            " ".join(p.get("extracted_skills", [])),
        ]).lower()
        hits += sum(1 for kw in keywords if kw in blob)
    return hits


def _matching_projects_detail(projects: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:
    """Return detailed info about matching projects"""
    matched = []
    for p in projects:
        blob = " ".join([
            p.get("title", ""),
            p.get("description", ""),
            " ".join(p.get("programming_languages", [])),
            " ".join(p.get("frameworks", [])),
            " ".join(p.get("extracted_skills", [])),
        ]).lower()
        
        matched_keywords = [kw for kw in keywords if kw in blob]
        if matched_keywords:
            matched.append({
                "title": p.get("title", "Untitled"),
                "matched_skills": matched_keywords[:5],
                "complexity": p.get("complexity_score", 0.5),
                "relevance_score": min(len(matched_keywords) * 10, 100)
            })
    return matched


# ═══════════════════════════════════════════════════════════════════
#  FEATURE VECTOR
# ═══════════════════════════════════════════════════════════════════

N_SUBJ = len(CANONICAL_SUBJECTS)
N_AGG = 4
N_INT = len(INTEREST_AREAS)
N_PROJ = 10
FEATURE_DIM = N_SUBJ + N_AGG + N_INT + N_PROJ


# ═══════════════════════════════════════════════════════════════════
#  NEW: STRUCTURED SCORE BREAKDOWN CLASSES
# ═══════════════════════════════════════════════════════════════════

class SubjectContribution:
    def __init__(self, name: str, score: float, weight: float, status: str):
        self.name = name
        self.score = score
        self.weight = weight
        self.contribution = round((score / 100) * weight * 10, 2)  # Normalized contribution
        self.status = status  # "strong", "adequate", "weak", "missing"


class ScoreBreakdown:
    def __init__(self):
        self.academic = {
            "score": 0.0,
            "max_possible": 40.0,
            "percentage": 0,
            "contributing_subjects": [],
            "missing_subjects": [],
            "strong_subjects": [],
            "weak_subjects": [],
        }
        self.interest = {
            "score": 0.0,
            "max_possible": 30.0,
            "percentage": 0,
            "matched_interests": [],
            "unmatched_interests": [],
            "semantic_similarity": 0.0,
        }
        self.project = {
            "score": 0.0,
            "max_possible": 30.0,
            "percentage": 0,
            "relevant_projects": [],
            "keyword_hits": 0,
            "missing_project_skills": [],
            "average_complexity": 0.0,
        }
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "academic_component": self.academic,
            "interest_component": self.interest,
            "project_component": self.project,
        }


class RankingExplanation:
    def __init__(self):
        self.rank = 0
        self.total_options = 0
        self.why_this_rank = ""
        self.vs_other_electives = []
        self.improvement_tips = []
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "total_options": self.total_options,
            "why_this_rank": self.why_this_rank,
            "vs_other_electives": self.vs_other_electives,
            "improvement_tips": self.improvement_tips,
        }


class ConfidenceMetrics:
    def __init__(self):
        self.overall = 0.0
        self.data_completeness = 0.0
        self.model_confidence = 0.0
        self.factors = {
            "has_marks": False,
            "has_interests": False,
            "has_projects": False,
            "marks_count": 0,
            "project_count": 0,
            "interest_count": 0,
        }
        
    def calculate(self, marks: Dict, interests: Any, projects: List):
        self.factors["marks_count"] = len(marks)
        self.factors["has_marks"] = len(marks) > 0
        
        if isinstance(interests, list):
            self.factors["interest_count"] = len(interests)
        elif isinstance(interests, dict):
            self.factors["interest_count"] = len([v for v in interests.values() if v > 0])
        self.factors["has_interests"] = self.factors["interest_count"] > 0
        
        self.factors["project_count"] = len(projects)
        self.factors["has_projects"] = len(projects) > 0
        
        # Calculate completeness
        completeness = 0
        if self.factors["marks_count"] >= 5:
            completeness += 40
        elif self.factors["marks_count"] > 0:
            completeness += self.factors["marks_count"] * 8
            
        if self.factors["interest_count"] >= 2:
            completeness += 30
        elif self.factors["interest_count"] > 0:
            completeness += 15
            
        if self.factors["project_count"] >= 2:
            completeness += 30
        elif self.factors["project_count"] > 0:
            completeness += 15
            
        self.data_completeness = min(completeness / 100, 1.0)
        self.model_confidence = 0.7 if self.data_completeness > 0.5 else 0.5
        self.overall = (self.data_completeness * 0.6) + (self.model_confidence * 0.4)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": round(self.overall, 2),
            "data_completeness": round(self.data_completeness, 2),
            "model_confidence": round(self.model_confidence, 2),
            "factors": self.factors,
        }


# ═══════════════════════════════════════════════════════════════════
#  ENGINE
# ═══════════════════════════════════════════════════════════════════

class CumulativeRecommendationEngine:
    MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved")
    ELECTIVE_META = ELECTIVE_META

    def __init__(self, load_pretrained: bool = True):
        self.rf_clf: Optional[RandomForestClassifier] = None
        self.knn_clf: Optional[KNeighborsClassifier] = None
        self.scaler = StandardScaler()
        self.label_enc = LabelEncoder()
        self.is_trained = False
        self._sbert = None
        os.makedirs(self.MODEL_DIR, exist_ok=True)
        if load_pretrained:
            self._try_load()

    @property
    def sbert(self):
        if self._sbert is None and HAS_SBERT:
            try:
                self._sbert = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                logger.warning(f"SentenceTransformer load failed: {e}")
        return self._sbert

    def extract_features(
        self, marks: Dict[str, float], interests: Any, projects: List[Dict[str, Any]]
    ) -> np.ndarray:
        canon_marks = _canonicalise_marks(marks)
        feat: List[float] = []

        for subj in CANONICAL_SUBJECTS:
            feat.append(canon_marks.get(subj, 0.0) / 100.0)

        vals = [v for v in canon_marks.values() if v > 0]
        if vals:
            feat += [np.mean(vals) / 100, np.std(vals) / 100, np.max(vals) / 100, np.min(vals) / 100]
        else:
            feat += [0.0, 0.0, 0.0, 0.0]

        ni = _normalise_interests(interests)
        for area in INTEREST_AREAS:
            feat.append(ni.get(area, 0.0))

        n = len(projects)
        feat.append(min(n / 10.0, 1.0))
        for elec in ["ML", "WT", "DWM", "CCS"]:
            feat.append(min(_project_hits(projects, PROJECT_SKILL_MAP[elec]) / 20.0, 1.0))
        total_sk = sum(len(p.get("extracted_skills", [])) for p in projects)
        feat.append(min(total_sk / 50.0, 1.0))
        team = sum(1 for p in projects if p.get("is_team_project"))
        feat.append(team / max(n, 1))
        cmplx = np.mean([p.get("complexity_score", 0.5) for p in projects]) if projects else 0.5
        feat.append(cmplx)
        gh = sum(1 for p in projects if p.get("github_url"))
        feat.append(gh / max(n, 1))
        demo = sum(1 for p in projects if p.get("demo_url"))
        feat.append(demo / max(n, 1))

        return np.array(feat, dtype=np.float32)

    # ── Enhanced Sub-score calculators with detailed breakdown ──────

    def _calculate_academic_score(
        self, canon_marks: Dict[str, float], elective: str
    ) -> Tuple[float, ScoreBreakdown]:
        """Calculate academic score with detailed breakdown"""
        weights = SUBJECT_WEIGHTS.get(elective, {})
        breakdown = ScoreBreakdown()
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for subj, weight in weights.items():
            mark = canon_marks.get(subj, -1)
            
            if mark < 0:
                breakdown.academic["missing_subjects"].append({
                    "subject": subj,
                    "weight": weight,
                    "impact": f"Could add up to {round(weight * 10, 1)} points if taken"
                })
            else:
                total_weighted_score += mark * weight
                total_weight += weight
                
                if mark >= 75:
                    status = "strong"
                    breakdown.academic["strong_subjects"].append(subj)
                elif mark >= 60:
                    status = "adequate"
                else:
                    status = "weak"
                    breakdown.academic["weak_subjects"].append(subj)
                
                breakdown.academic["contributing_subjects"].append({
                    "subject": subj,
                    "score": mark,
                    "weight": weight,
                    "contribution": round((mark / 100) * weight * (40 / sum(weights.values())), 2),
                    "status": status
                })
        
        if total_weight > 0:
            weighted_avg = total_weighted_score / total_weight
            # Scale to 40 points max
            score = (weighted_avg / 100) * 40
        else:
            score = 0.0
            
        breakdown.academic["score"] = round(score, 2)
        breakdown.academic["percentage"] = round((score / 40) * 100, 1) if score > 0 else 0
        
        return score, breakdown

    def _calculate_interest_score(
        self, norm_interests: Dict[str, float], elective: str, raw_interests: Any
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate interest score with detailed breakdown"""
        mapping = INTEREST_ELECTIVE_MAP.get(elective, [])
        
        score = 0.0
        matched = []
        unmatched = []
        
        for area, weight in mapping:
            val = norm_interests.get(area, 0.0)
            if val > 0:
                matched.append({
                    "interest": area,
                    "strength": round(val * 100, 1),
                    "contribution": round(val * weight * 15, 2)
                })
                score += val * weight * 15
            else:
                unmatched.append({
                    "interest": area,
                    "potential_boost": round(weight * 15, 1)
                })
        
        score = min(score, 30.0)
        
        return score, {
            "score": round(score, 2),
            "max_possible": 30.0,
            "percentage": round((score / 30) * 100, 1),
            "matched_interests": matched,
            "unmatched_interests": unmatched,
        }

    def _calculate_project_score(
        self, projects: List[Dict[str, Any]], elective: str
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate project score with detailed breakdown"""
        keywords = PROJECT_SKILL_MAP.get(elective, [])
        meta = ELECTIVE_META.get(elective, {})
        
        hits = _project_hits(projects, keywords)
        matched_projects = _matching_projects_detail(projects, keywords)
        
        # Calculate score (max 30 points)
        score = min(hits * 5, 30.0)
        
        # Find missing skills that would help
        all_project_skills = set()
        for p in projects:
            all_project_skills.update(s.lower() for s in p.get("extracted_skills", []))
            all_project_skills.update(s.lower() for s in p.get("programming_languages", []))
            all_project_skills.update(s.lower() for s in p.get("frameworks", []))
        
        missing_skills = [kw for kw in keywords[:10] if kw not in all_project_skills][:5]
        
        # Calculate average complexity
        complexities = [p.get("complexity_score", 0.5) for p in projects]
        avg_complexity = np.mean(complexities) if complexities else 0.0
        
        return score, {
            "score": round(score, 2),
            "max_possible": 30.0,
            "percentage": round((score / 30) * 100, 1),
            "relevant_projects": matched_projects[:5],
            "keyword_hits": hits,
            "missing_project_skills": missing_skills,
            "average_complexity": round(avg_complexity, 2),
            "total_projects_analyzed": len(projects),
        }

    def _calculate_semantic_boost(self, interests: Any, projects: List, elective: str) -> float:
        if not self.sbert:
            return 0.0
        try:
            student_text = " ".join(interests if isinstance(interests, list) else [])
            for p in projects:
                student_text += " " + p.get("description", "")
            desc = ELECTIVE_META[elective]["description"]
            embs = self.sbert.encode([student_text, desc])
            sim = cos_sim([embs[0]], [embs[1]])[0][0]
            return float(sim) * 10
        except Exception:
            return 0.0

    def _generate_improvement_tips(
        self, 
        breakdown: Dict[str, Any], 
        elective: str
    ) -> List[str]:
        """Generate actionable improvement tips"""
        tips = []
        meta = ELECTIVE_META.get(elective, {})
        
        # Academic tips
        if breakdown.get("academic_component", {}).get("missing_subjects"):
            missing = breakdown["academic_component"]["missing_subjects"]
            if missing:
                tips.append(f"Take {missing[0]['subject']} to potentially add {missing[0]['impact']}")
        
        if breakdown.get("academic_component", {}).get("weak_subjects"):
            weak = breakdown["academic_component"]["weak_subjects"]
            if weak:
                tips.append(f"Improve your score in {weak[0]} (currently weak) to boost academic alignment")
        
        # Interest tips
        if breakdown.get("interest_component", {}).get("unmatched_interests"):
            unmatched = breakdown["interest_component"]["unmatched_interests"]
            if unmatched:
                tips.append(f"Declaring interest in '{unmatched[0]['interest']}' could add {unmatched[0]['potential_boost']} points")
        
        # Project tips
        if breakdown.get("project_component", {}).get("missing_project_skills"):
            missing_skills = breakdown["project_component"]["missing_project_skills"]
            if missing_skills:
                tips.append(f"Build a project using {', '.join(missing_skills[:3])} to improve project alignment")
        
        if breakdown.get("project_component", {}).get("total_projects_analyzed", 0) < 2:
            tips.append("Upload more projects to get a more accurate recommendation")
        
        return tips[:4]

    # ── Main recommend method with enhanced response ──────

    def recommend_electives(
        self,
        marks: Dict[str, float],
        interests: Any,
        projects: List[Dict[str, Any]],
        cgpa: float = 0.0,
        use_ml: bool = True,
    ) -> List[Dict[str, Any]]:
        """Generate elective recommendations with full breakdown"""
        canon_marks = _canonicalise_marks(marks)
        norm_interests = _normalise_interests(interests)
        interest_list = interests if isinstance(interests, list) else list(interests.keys()) if isinstance(interests, dict) else []

        # Calculate confidence metrics
        confidence = ConfidenceMetrics()
        confidence.calculate(marks, interests, projects)

        # ML predictions
        ml_probs: Dict[str, float] = {}
        if use_ml and self.is_trained:
            try:
                feat = self.extract_features(marks, interests, projects)
                feat_scaled = self.scaler.transform([feat])
                probs = self.rf_clf.predict_proba(feat_scaled)[0]
                ml_probs = dict(zip(self.label_enc.classes_, probs))
            except Exception as e:
                logger.warning(f"ML prediction failed: {e}")

        # Score each elective with detailed breakdown
        scored = []
        for elec in ["ML", "WT", "DWM", "CCS"]:
            # Calculate component scores with breakdown
            academic_score, breakdown = self._calculate_academic_score(canon_marks, elec)
            interest_score, interest_details = self._calculate_interest_score(norm_interests, elec, interests)
            project_score, project_details = self._calculate_project_score(projects, elec)
            
            # Update breakdown with interest and project details
            breakdown.interest = interest_details
            breakdown.project = project_details
            
            # Calculate semantic boost
            sem_boost = self._calculate_semantic_boost(interest_list, projects, elec)
            breakdown.interest["semantic_similarity"] = round(sem_boost / 10, 2)
            
            # Calculate final score
            final = academic_score + interest_score + project_score
            
            # Add ML boost if available
            ml_boost = 0.0
            if elec in ml_probs:
                ml_boost = ml_probs[elec] * 20
                final += ml_boost
            
            # Add semantic boost
            final += sem_boost
            
            final = round(min(max(final, 0), 100), 1)

            scored.append({
                "_key": elec,
                "_final": final,
                "_breakdown": breakdown.to_dict(),
                "_academic_score": academic_score,
                "_interest_score": interest_score,
                "_project_score": project_score,
                "_ml_boost": ml_boost,
                "_sem_boost": sem_boost,
            })

        # Sort by final score
        scored.sort(key=lambda x: x["_final"], reverse=True)
        
        # Generate ranking explanations
        results = []
        for rank, item in enumerate(scored, 1):
            elec = item["_key"]
            meta = ELECTIVE_META[elec]
            
            # Build ranking explanation
            ranking_explanation = RankingExplanation()
            ranking_explanation.rank = rank
            ranking_explanation.total_options = len(scored)
            
            if rank == 1:
                ranking_explanation.why_this_rank = "Strongest combined alignment across academics, interests, and projects"
                if len(scored) > 1:
                    diff = item["_final"] - scored[1]["_final"]
                    ranking_explanation.vs_other_electives.append({
                        "compared_to": ELECTIVE_META[scored[1]["_key"]]["name"],
                        "score_difference": round(diff, 1),
                        "message": f"{round(diff, 1)} points higher than second choice"
                    })
            elif rank == 2:
                ranking_explanation.why_this_rank = "Strong alternative - second best alignment with your profile"
                diff = scored[0]["_final"] - item["_final"]
                ranking_explanation.vs_other_electives.append({
                    "compared_to": ELECTIVE_META[scored[0]["_key"]]["name"],
                    "score_difference": round(-diff, 1),
                    "message": f"{round(diff, 1)} points below top choice"
                })
            else:
                ranking_explanation.why_this_rank = "Lower alignment - consider if schedule conflicts with top choices"
            
            # Generate improvement tips
            ranking_explanation.improvement_tips = self._generate_improvement_tips(
                item["_breakdown"], elec
            )
            
            # Build skill gaps
            skill_gaps = []
            for subj in item["_breakdown"]["academic_component"].get("weak_subjects", []):
                # Find the subject score
                for contrib in item["_breakdown"]["academic_component"].get("contributing_subjects", []):
                    if contrib["subject"] == subj:
                        skill_gaps.append({
                            "subject": subj,
                            "current_score": contrib["score"],
                            "target_score": 60,
                            "gap": round(60 - contrib["score"], 1),
                            "importance": "High" if contrib["weight"] >= 3.0 else "Medium"
                        })
                        break
            
            # Build legacy text explanation (for backward compatibility)
            text_explanation = self._build_text_explanation(
                elec, item, rank, len(scored)
            )

            results.append({
                "elective_code": meta["code"],
                "elective_name": meta["name"],
                "credits": meta["credits"],
                "match_score": item["_final"],
                
                # NEW: Structured breakdown
                "score_breakdown": item["_breakdown"],
                
                # NEW: Ranking explanation
                "ranking_explanation": ranking_explanation.to_dict(),
                
                # NEW: Confidence metrics
                "confidence": confidence.to_dict(),
                
                # Legacy fields (keep for backward compatibility)
                "match_explanation": text_explanation,
                "prerequisites_met": True,
                "skill_alignment": meta["skills"][:5],
                "career_relevance": meta["career_paths"],
                "recommendation_basis": {
                    "interests_weight": round(item["_interest_score"], 1),
                    "performance_weight": round(item["_academic_score"], 1),
                    "projects_weight": round(item["_project_score"], 1),
                },
                "pair": meta["pair"],
                "skill_gaps": skill_gaps[:4],
            })

        return results

    def _build_text_explanation(
        self, elec: str, item: Dict, rank: int, total: int
    ) -> str:
        """Build legacy text explanation for backward compatibility"""
        meta = ELECTIVE_META[elec]
        breakdown = item["_breakdown"]
        parts = []
        
        parts.append(f"Ranked #{rank} of {total} electives with a cumulative score of {item['_final']:.1f}%.")
        
        # Academic
        acad = breakdown["academic_component"]
        if acad["contributing_subjects"]:
            parts.append(f"\n📊 Academic Performance ({acad['score']:.1f}/40 points, {acad['percentage']}%):")
            if acad["strong_subjects"]:
                parts.append(f"  Strengths: {', '.join(acad['strong_subjects'][:3])}")
            if acad["weak_subjects"]:
                parts.append(f"  Needs work: {', '.join(acad['weak_subjects'][:2])}")
        else:
            parts.append("\n📊 Academic: No relevant marks data available.")
        
        # Interest
        intr = breakdown["interest_component"]
        if intr["matched_interests"]:
            matched_names = [m["interest"] for m in intr["matched_interests"]]
            parts.append(f"\n💡 Interest Alignment ({intr['score']:.1f}/30 points): Matches {', '.join(matched_names)}")
        else:
            parts.append(f"\n💡 Interest Alignment: No matching interests declared.")
        
        # Projects
        proj = breakdown["project_component"]
        if proj["relevant_projects"]:
            titles = [p["title"] for p in proj["relevant_projects"][:2]]
            parts.append(f"\n🔧 Project Portfolio ({proj['score']:.1f}/30 points, {proj['keyword_hits']} keyword matches):")
            parts.append(f"  Relevant projects: {', '.join(titles)}")
        else:
            parts.append(f"\n🔧 Projects: No matching projects found. Build projects with {', '.join(meta['skills'][:3])}.")
        
        return "\n".join(parts)

    def recommend_honours(self, marks, interests, projects, cgpa) -> List[Dict[str, Any]]:
        """Honours/Minor recommendations with score breakdown"""
        canon_marks = _canonicalise_marks(marks)
        norm_interests = _normalise_interests(interests)
        results = []

        for prog in HONOURS_PROGRAMS:
            eligible = cgpa >= prog["required_cgpa"]
            
            # Subject match (40%)
            subj_score = 0.0
            matched_subjects = []
            for subj in prog["relevant_subjects"]:
                m = canon_marks.get(subj, 0)
                if m >= 60:
                    subj_score += 13.3  # ~40/3
                    matched_subjects.append({"subject": subj, "score": m})
            subj_score = min(subj_score, 40)

            # Interest match (30%)
            int_score = 0.0
            matched_interests = []
            for interest in prog["relevant_interests"]:
                val = norm_interests.get(interest, 0)
                if val > 0:
                    int_score += 15
                    matched_interests.append(interest)
            int_score = min(int_score, 30)

            # Project match (30%)
            hits = _project_hits(projects, prog["project_keywords"])
            proj_score = min(hits * 6, 30)
            matched_projects = _matching_projects_detail(projects, prog["project_keywords"])

            total_score = subj_score + int_score + proj_score

            # Build explanation
            explanation_parts = []
            if eligible:
                explanation_parts.append(f"✓ You meet the {prog['required_cgpa']} CGPA requirement (your CGPA: {cgpa:.2f}).")
            else:
                gap = prog["required_cgpa"] - cgpa
                explanation_parts.append(f"✗ Need {gap:.2f} more CGPA (current: {cgpa:.2f}, required: {prog['required_cgpa']}).")
            
            if matched_subjects:
                subj_str = ", ".join([f"{s['subject']} ({s['score']}%)" for s in matched_subjects[:2]])
                explanation_parts.append(f"Strong in: {subj_str}")
            
            if matched_interests:
                explanation_parts.append(f"Interest alignment: {', '.join(matched_interests)}")
            
            if matched_projects:
                explanation_parts.append(f"Relevant projects: {len(matched_projects)}")

            results.append({
                "program": prog["program"],
                "type": prog["type"],
                "match_score": round(min(total_score, 100), 1),
                "eligibility": eligible,
                "required_cgpa": prog["required_cgpa"],
                "career_paths": prog["career_paths"],
                "explanation": " | ".join(explanation_parts) if explanation_parts else "Limited alignment with profile.",
                "skills_gained": prog["skills_gained"],
                "score_breakdown": {
                    "academic_score": round(subj_score, 1),
                    "interest_score": round(int_score, 1),
                    "project_score": round(proj_score, 1),
                    "matched_subjects": matched_subjects,
                    "matched_interests": matched_interests,
                    "relevant_projects": matched_projects[:3],
                }
            })

        results.sort(key=lambda x: (x["eligibility"], x["match_score"]), reverse=True)
        return results

    def recommend_careers(self, marks, interests, projects, cgpa) -> List[Dict[str, Any]]:
        """Career recommendations with detailed breakdown"""
        norm_interests = _normalise_interests(interests)
        results = []

        for career in CAREER_CATALOG:
            cgpa_ok = cgpa >= career["required_cgpa"]
            
            # Interest score
            int_score = 0.0
            matched_interests = []
            for interest in career["relevant_interests"]:
                val = norm_interests.get(interest, 0)
                if val > 0:
                    int_score += 20
                    matched_interests.append(interest)
            int_score = min(int_score, 40)

            # Project score
            hits = _project_hits(projects, career["project_keywords"])
            proj_score = min(hits * 7, 35)
            matched_projects = _matching_projects_detail(projects, career["project_keywords"])

            # CGPA score
            cgpa_score = 25 if cgpa_ok else (cgpa / career["required_cgpa"]) * 15

            total_score = int_score + proj_score + cgpa_score

            # Find missing skills
            project_skills = set()
            for p in projects:
                project_skills.update(s.lower() for s in p.get("extracted_skills", []))
            missing = [kw for kw in career["project_keywords"][:5] if not any(kw in sk for sk in project_skills)]

            results.append({
                "career": career["career"],
                "match_score": round(min(total_score, 100), 1),
                "cgpa_eligible": cgpa_ok,
                "required_cgpa": career["required_cgpa"],
                "salary_range": career["salary_range"],
                "growth_potential": career["growth_potential"],
                "top_companies": career["top_companies"],
                "missing_skills": missing[:5],
                "preparation_path": career["preparation_path"],
                "required_certifications": career.get("required_certifications", []),
                "score_breakdown": {
                    "interest_score": round(int_score, 1),
                    "project_score": round(proj_score, 1),
                    "cgpa_score": round(cgpa_score, 1),
                    "matched_interests": matched_interests,
                    "relevant_projects": matched_projects[:3],
                }
            })

        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results

    # ── Training methods ────

    def train(self, training_data: List[Dict[str, Any]], test_size: float = 0.2):
        if len(training_data) < 20:
            raise ValueError(f"Need ≥20 samples, got {len(training_data)}")

        X, y = [], []
        for s in training_data:
            X.append(self.extract_features(s.get("marks", {}), s.get("interests", []), s.get("projects", [])))
            y.append(s["label"])

        X, y = np.array(X), np.array(y)
        y_enc = self.label_enc.fit_transform(y)
        X_tr, X_te, y_tr, y_te = train_test_split(X, y_enc, test_size=test_size, random_state=42, stratify=y_enc)

        X_tr_s = self.scaler.fit_transform(X_tr)
        X_te_s = self.scaler.transform(X_te)

        self.rf_clf = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
        self.rf_clf.fit(X_tr_s, y_tr)

        self.knn_clf = KNeighborsClassifier(n_neighbors=5)
        self.knn_clf.fit(X_tr_s, y_tr)

        pred = self.rf_clf.predict(X_te_s)
        acc = accuracy_score(y_te, pred)
        f1w = f1_score(y_te, pred, average="weighted")
        cv = cross_val_score(self.rf_clf, X_tr_s, y_tr, cv=5)

        self.is_trained = True
        self._save()

        report = classification_report(y_te, pred, output_dict=True)
        return {
            "accuracy": round(acc, 4),
            "f1_weighted": round(f1w, 4),
            "f1_macro": round(f1_score(y_te, pred, average="macro"), 4),
            "cross_val_mean": round(cv.mean(), 4),
            "cross_val_std": round(cv.std(), 4),
            "per_class": {
                self.label_enc.classes_[i]: {
                    "precision": round(report[str(i)]["precision"], 4),
                    "recall": round(report[str(i)]["recall"], 4),
                    "f1": round(report[str(i)]["f1-score"], 4),
                }
                for i in range(len(self.label_enc.classes_))
                if str(i) in report
            },
            "confusion_matrix": confusion_matrix(y_te, pred).tolist(),
            "n_training_samples": len(X_tr),
            "n_test_samples": len(X_te),
            "model_type": "RandomForest(200) + KNN(5) Ensemble",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _save(self):
        try:
            joblib.dump(self.rf_clf, os.path.join(self.MODEL_DIR, "rf_clf.joblib"))
            joblib.dump(self.knn_clf, os.path.join(self.MODEL_DIR, "knn_clf.joblib"))
            joblib.dump(self.scaler, os.path.join(self.MODEL_DIR, "scaler.joblib"))
            joblib.dump(self.label_enc, os.path.join(self.MODEL_DIR, "label_enc.joblib"))
            with open(os.path.join(self.MODEL_DIR, "meta.json"), "w") as f:
                json.dump({"is_trained": True, "ts": datetime.utcnow().isoformat()}, f)
            logger.info("Models saved")
        except Exception as e:
            logger.error(f"Save failed: {e}")

    def _try_load(self):
        try:
            rf = os.path.join(self.MODEL_DIR, "rf_clf.joblib")
            if os.path.exists(rf):
                self.rf_clf = joblib.load(rf)
                self.knn_clf = joblib.load(os.path.join(self.MODEL_DIR, "knn_clf.joblib"))
                self.scaler = joblib.load(os.path.join(self.MODEL_DIR, "scaler.joblib"))
                self.label_enc = joblib.load(os.path.join(self.MODEL_DIR, "label_enc.joblib"))
                self.is_trained = True
                logger.info("Pretrained models loaded")
        except Exception as e:
            logger.info(f"No pretrained models: {e}")


# Singleton
recommendation_engine = CumulativeRecommendationEngine()