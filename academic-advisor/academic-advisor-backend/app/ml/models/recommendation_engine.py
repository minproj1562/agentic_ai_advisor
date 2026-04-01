# app/ml/models/recommendation_engine.py
"""
Enhanced Cumulative Recommendation Engine
==========================================
Marks (40%) + Interests (30%) + Projects (30%)

Features:
  - Structured score breakdown for frontend visualization
  - Per-category confidence levels
  - Concept matching for project descriptions
  - Ranking explanation with comparisons
  - Open Elective (Sem-VII) recommendations
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
#  PROGRAM ELECTIVE CATALOGUE (Sem 5-6)
# ═══════════════════════════════════════════════════════════════════

ELECTIVE_META = {
    "ML": {
        "code": "ITPEC5012", "name": "Machine Learning", "credits": 3,
        "pair": "Pair 1 (ML vs WT)",
        "career_paths": ["ML Engineer", "Data Scientist", "AI Researcher", "NLP Engineer"],
        "skills": ["TensorFlow", "PyTorch", "Scikit-learn", "Neural Networks", "NLP"],
        "description": "Machine Learning covers supervised and unsupervised learning, neural networks, deep learning, NLP, and model deployment.",
    },
    "WT": {
        "code": "ITPEC5013", "name": "Wireless Technology", "credits": 3,
        "pair": "Pair 1 (ML vs WT)",
        "career_paths": ["IoT Engineer", "Network Engineer", "Embedded Developer", "RF Engineer"],
        "skills": ["IoT Protocols", "Embedded C", "Wireless Networks", "Sensor Integration"],
        "description": "Wireless Technology covers cellular networks, IoT protocols, sensor networks, MQTT, Bluetooth, ZigBee, and 5G.",
    },
    "DWM": {
        "code": "ITPEC5014", "name": "Data Warehouse and Mining", "credits": 3,
        "pair": "Pair 2 (DWM vs CCS)",
        "career_paths": ["Data Analyst", "BI Developer", "Data Engineer", "Analytics Manager"],
        "skills": ["SQL", "ETL", "OLAP", "Clustering", "Association Rules"],
        "description": "Data Warehousing and Mining covers OLAP, ETL, data cubes, classification, clustering, association rule mining, and BI tools.",
    },
    "CCS": {
        "code": "ITPEC5015", "name": "Cloud Computing Services", "credits": 3,
        "pair": "Pair 2 (DWM vs CCS)",
        "career_paths": ["Cloud Architect", "DevOps Engineer", "SRE", "Platform Engineer"],
        "skills": ["AWS", "Azure", "Docker", "Kubernetes", "Terraform"],
        "description": "Cloud Computing Services covers virtualisation, containers, AWS/Azure/GCP, serverless, micro-services, and CI/CD pipelines.",
    },
}

# ═══════════════════════════════════════════════════════════════════
#  OPEN ELECTIVE CATALOGUE (Sem VII) — NEW
# ═══════════════════════════════════════════════════════════════════

OPEN_ELECTIVE_META = {
    "RE": {
        "code": "OEC7012", "name": "Reliability Engineering", "credits": 3,
        "semester": 7, "category": "Open Elective",
        "career_paths": ["Reliability Engineer", "Quality Assurance Engineer", "Systems Engineer", "Safety Engineer", "Risk Analyst"],
        "skills": ["Probability Theory", "FMEA/FMECA", "Fault Tree Analysis", "Weibull Analysis", "System Reliability", "Markov Analysis"],
        "description": (
            "Reliability Engineering covers probability theory, reliability functions, failure analysis (Bath Tub Curve, MTTF, MTBF), "
            "hazard models (constant, time-dependent, Weibull), system reliability configurations (series, parallel, k-out-of-n, redundancy), "
            "maintainability, availability, FMECA, Fault Tree Analysis, and Event Tree Analysis."
        ),
        "modules": [
            "Probability (Baye's Theorem, conditional probability)",
            "Reliability Concepts (failure density, MTTF, MTBF, Bath Tub Curve)",
            "Reliability Hazard Models (Weibull, constant/time-dependent hazard)",
            "System Reliability (series, parallel, mixed, k-out-of-n, Markov)",
            "Maintainability and Availability (fault isolation, modularization)",
            "FMECA & Fault Tree Analysis (Event Tree Analysis)",
        ],
    },
    "OR": {
        "code": "OEC7015", "name": "Operation Research", "credits": 3,
        "semester": 7, "category": "Open Elective",
        "career_paths": ["Operations Analyst", "Supply Chain Analyst", "Management Consultant", "Logistics Manager", "Business Analyst"],
        "skills": ["Linear Programming", "Simplex Method", "Queuing Theory", "Game Theory", "Dynamic Programming", "Simulation", "Inventory Models"],
        "description": (
            "Operation Research covers linear programming (graphical, simplex, Big M, Two Phase, duality), "
            "queuing models (single/multi-server, Poisson, exponential), Monte-Carlo simulation, "
            "dynamic programming (shortest path, cargo loading, capital budgeting), "
            "game theory (saddle point, minimax, dominance, mixed strategy), and inventory models (EOQ, price breaks)."
        ),
        "modules": [
            "Introduction to OR (LPP, Simplex, Big M, Two Phase, Duality)",
            "Queuing Models (single/multi-server, Poisson input)",
            "Simulation (Monte-Carlo, methodology, applications)",
            "Dynamic Programming (shortest path, capital budgeting)",
            "Game Theory (saddle point, minimax, mixed strategy)",
            "Inventory Models (EOQ, price breaks, probabilistic EOQ)",
        ],
    },
    "CSL": {
        "code": "OEC7016", "name": "Cyber Security and Laws", "credits": 3,
        "semester": 7, "category": "Open Elective",
        "career_paths": ["Cybersecurity Analyst", "Compliance Officer", "Information Security Manager", "Legal Tech Consultant", "IT Auditor"],
        "skills": ["Cybercrime Analysis", "IT Act 2000/2008", "GDPR", "ISO 27001", "Social Engineering", "Digital Forensics", "Phishing Analysis"],
        "description": (
            "Cyber Security and Laws covers cybercrime classification, social engineering, botnets, phishing, password cracking, "
            "DoS/DDoS, SQL injection, identity theft, e-commerce security, Indian IT Act 2000 & 2008 amendments, "
            "cyber law (contract, IP, evidence, criminal aspects), and compliance standards (SOX, GLBA, HIPAA, ISO, PCI)."
        ),
        "modules": [
            "Introduction to Cybercrime (ITA 2000, global perspective)",
            "Cyber Offenses (social engineering, botnets, cloud/mobile security)",
            "Tools & Methods (phishing, keyloggers, viruses, DoS, SQL injection)",
            "Cyberspace Concepts (e-commerce, IP, cyber law, electronic banking)",
            "Indian IT Act (2000, 2008 amendments, penalties, adjudication)",
            "Information Security Compliances (SOX, HIPAA, ISO, PCI, FISMA)",
        ],
    },
    "DBM": {
        "code": "OEC7017", "name": "Digital Business Management", "credits": 3,
        "semester": 7, "category": "Open Elective",
        "career_paths": ["Digital Marketing Manager", "Product Manager", "E-commerce Manager", "Business Analyst", "Growth Hacker", "Data Analyst"],
        "skills": ["SEO/SEM", "Digital Strategy", "CRM", "A/B Testing", "Data Analytics", "Agile/Lean", "E-commerce", "Platform Business Models"],
        "description": (
            "Digital Business Management covers digital transformation (digitization vs digitalization), "
            "digital strategy frameworks, KPI dashboards, digital marketing (SEO, SEM, social media, content marketing), "
            "customer journey mapping, e-commerce models (B2B, B2C, C2C, D2C), omni-channel operations, "
            "data analytics and AI for business, platform ecosystems, API economy, Agile & Lean Startup, and ethics."
        ),
        "modules": [
            "Foundations of Digital Business (Marketplaces, Subscription, Freemium, PaaS)",
            "Digital Strategy & Transformation (KPI dashboards, CAC, LTV, roadmaps)",
            "Digital Marketing & Customer Acquisition (SEO, SEM, CRM, A/B testing)",
            "Ecommerce & Omni-channel Operations (B2B/B2C/D2C, fulfillment, logistics)",
            "Data, Analytics & AI for Business (SQL, predictive analytics, recommendation engines)",
            "Platforms, Ecosystems & Ethics (API economy, Agile, Lean Startup, GDPR)",
        ],
    },
    "EAM": {
        "code": "OEC7018", "name": "Energy Audit and Management", "credits": 3,
        "semester": 7, "category": "Open Elective",
        "career_paths": ["Energy Auditor", "Sustainability Consultant", "Energy Manager", "Green Building Consultant", "Environmental Engineer"],
        "skills": ["Energy Auditing", "Financial Analysis (NPV, ROI, IRR)", "Power Factor Correction", "HVAC Optimization", "ECBC", "BEE Standards"],
        "description": (
            "Energy Audit and Management covers energy scenarios (renewable/non-renewable, Energy Conservation Act 2001, BEE), "
            "energy audit principles (benchmarking, simple payback, NPV, ROI, IRR), "
            "energy management in electrical systems (power factor, motor loading, VSDs, lighting efficiency), "
            "thermal systems (boilers, furnaces, heat exchangers, HVAC), "
            "on-site energy performance assessment (ILER method), and Energy Conservation Building Codes (ECBC)."
        ),
        "modules": [
            "Energy Scenario (Conservation Act 2001, BEE, renewable/non-renewable)",
            "Energy Audit Principles (benchmarking, payback, NPV, ROI, IRR)",
            "Electrical Systems Management (power factor, motors, lighting, VSDs)",
            "Thermal Systems Management (boilers, furnaces, heat exchangers, HVAC)",
            "Energy Performance Assessment (ILER, on-site techniques)",
            "Energy Conservation in Buildings (ECBC, green buildings)",
        ],
    },
}

# Open Elective labels
OPEN_ELECTIVE_LABELS = ["RE", "OR", "CSL", "DBM", "EAM"]

# ═══════════════════════════════════════════════════════════════════
#  OPEN ELECTIVE SCORING WEIGHTS
# ═══════════════════════════════════════════════════════════════════

OE_SUBJECT_WEIGHTS: Dict[str, Dict[str, float]] = {
    "RE": {
        "Engineering Mathematics-III": 3.5, "Engineering Mathematics-IV": 3.0,
        "Data Structures and Algorithms": 1.5, "Software Engineering": 1.5,
        "Operating Systems": 1.0,
    },
    "OR": {
        "Engineering Mathematics-III": 3.5, "Engineering Mathematics-IV": 3.5,
        "Data Structures and Algorithms": 2.0, "Design & Analysis of Algorithms": 2.0,
        "Python": 1.0,
    },
    "CSL": {
        "Computer Networks": 3.5, "Cryptography & Network Security": 3.5,
        "Operating Systems": 2.0, "Software Engineering": 1.5,
        "Database Management Systems": 1.0,
    },
    "DBM": {
        "Database Management Systems": 2.5, "Software Engineering": 2.5,
        "Full Stack Development": 2.5, "Python": 1.5,
        "Data Structures and Algorithms": 1.0,
    },
    "EAM": {
        "Engineering Mathematics-III": 2.0, "Engineering Mathematics-IV": 2.0,
        "Microcontroller & Embedded Systems": 2.0, "IoT": 2.0,
        "Software Engineering": 1.0,
    },
}

OE_INTEREST_MAP = {
    "RE": [("Network & Wireless Systems", 1.5), ("Cloud & Distributed Systems", 1.0)],
    "OR": [("Data Science & Analytics", 2.0), ("Artificial Intelligence & Machine Learning", 1.0)],
    "CSL": [("Network & Wireless Systems", 2.5), ("Cloud & Distributed Systems", 1.0)],
    "DBM": [("Web Development", 2.0), ("Data Science & Analytics", 2.0), ("Cloud & Distributed Systems", 1.0)],
    "EAM": [("Mobile & IoT Development", 1.5), ("Network & Wireless Systems", 1.0)],
}

OE_PROJECT_SKILL_MAP = {
    "RE": [
        "probability", "statistics", "reliability", "failure analysis", "fmea", "fault tree",
        "weibull", "matlab", "simulation", "quality", "testing", "risk", "safety",
        "markov", "maintenance", "statistical analysis", "mtbf", "mttf",
        "system design", "redundancy", "hazard", "availability",
    ],
    "OR": [
        "optimization", "linear programming", "simulation", "queue", "queuing",
        "monte carlo", "scheduling", "inventory", "supply chain", "logistics",
        "game theory", "dynamic programming", "operations", "simplex",
        "python", "matlab", "scipy", "numpy", "decision", "mathematical model",
        "cost optimization", "resource allocation", "planning",
    ],
    "CSL": [
        "security", "cyber", "hacking", "penetration testing", "firewall",
        "encryption", "phishing", "malware", "forensics", "compliance",
        "vulnerability", "authentication", "authorization", "gdpr", "iso 27001",
        "network security", "intrusion detection", "ids", "ips",
        "sql injection", "xss", "ddos", "dos", "social engineering",
        "password", "cryptography", "digital signature", "certificate",
    ],
    "DBM": [
        "digital marketing", "seo", "sem", "social media", "analytics",
        "ecommerce", "e-commerce", "crm", "a/b testing", "marketing",
        "business", "strategy", "dashboard", "kpi", "product management",
        "agile", "lean", "api", "platform", "marketplace",
        "web", "react", "node", "fullstack", "full stack",
        "recommendation", "personalization", "customer", "user experience",
        "subscription", "saas", "startup", "growth",
    ],
    "EAM": [
        "energy", "audit", "solar", "renewable", "sustainability",
        "power", "electrical", "thermal", "hvac", "boiler",
        "green building", "conservation", "efficiency", "carbon",
        "iot", "smart grid", "monitoring", "sensor", "automation",
        "led", "lighting", "motor", "vsd", "vfd",
        "ecbc", "bee", "energy management", "insulation",
        "heat exchanger", "furnace", "power factor",
    ],
}

OE_CONCEPT_MAP = {
    "RE": [
        ("reliab", 0.6), ("fail", 0.5), ("hazard", 0.5), ("redundan", 0.5),
        ("mainten", 0.4), ("availab", 0.4), ("probabili", 0.4),
        ("bath tub", 0.6), ("weibull", 0.6), ("markov", 0.5),
        ("fault", 0.5), ("safety", 0.3), ("risk", 0.3), ("qualit", 0.3),
    ],
    "OR": [
        ("optimi", 0.5), ("linear", 0.4), ("simplex", 0.6), ("queue", 0.5),
        ("simulat", 0.4), ("inventor", 0.5), ("schedul", 0.4),
        ("game theor", 0.6), ("dynamic program", 0.6), ("logistic", 0.4),
        ("supply chain", 0.5), ("cost", 0.3), ("resource", 0.3),
    ],
    "CSL": [
        ("secur", 0.5), ("cyber", 0.5), ("hack", 0.5), ("phish", 0.6),
        ("malwar", 0.5), ("encrypt", 0.5), ("firewall", 0.5),
        ("complian", 0.5), ("forens", 0.5), ("vulnerab", 0.5),
        ("authent", 0.4), ("privac", 0.4), ("gdpr", 0.6), ("iso", 0.4),
    ],
    "DBM": [
        ("market", 0.4), ("digital", 0.4), ("ecommerce", 0.5), ("e-commerce", 0.5),
        ("seo", 0.6), ("strateg", 0.4), ("customer", 0.4), ("brand", 0.4),
        ("analytic", 0.4), ("dashboard", 0.4), ("kpi", 0.5), ("agile", 0.4),
        ("startup", 0.4), ("platform", 0.3), ("subscript", 0.4),
    ],
    "EAM": [
        ("energy", 0.5), ("audit", 0.5), ("solar", 0.5), ("renew", 0.5),
        ("sustain", 0.4), ("green", 0.4), ("conserv", 0.5), ("efficienc", 0.4),
        ("power", 0.3), ("thermal", 0.4), ("hvac", 0.6), ("boiler", 0.5),
        ("carbon", 0.4), ("insulation", 0.5), ("lighting", 0.3),
    ],
}


# ═══════════════════════════════════════════════════════════════════
#  PROGRAM ELECTIVE WEIGHTS (existing - unchanged)
# ═══════════════════════════════════════════════════════════════════

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
        "regression", "classification", "clustering", "random forest",
        "opencv", "hugging face", "transformers", "bert", "gpt",
        "langchain", "llm", "generative ai", "reinforcement learning",
        "model training", "feature engineering", "xgboost", "gradient boosting",
        "sentiment analysis", "text mining", "word2vec", "cnn", "rnn", "lstm",
        "image recognition", "object detection", "yolo", "recommendation system",
        "chatbot", "prediction", "forecast", "anomaly detection",
        "jupyter", "notebook", "kaggle", "matplotlib", "seaborn",
        "data preprocessing", "data cleaning", "artificial intelligence",
        "ai", "ml", "neural", "perceptron", "backpropagation",
    ],
    "WT": [
        "arduino", "raspberry pi", "iot", "embedded", "sensor",
        "wireless", "bluetooth", "zigbee", "mqtt", "microcontroller",
        "esp32", "esp8266", "lora", "rfid",
        "internet of things", "smart home", "wearable", "edge computing",
        "5g", "cellular", "wifi", "nfc", "gps", "gsm",
        "signal processing", "firmware", "real-time", "rtos",
        "nodemcu", "stm32", "arm", "gpio", "i2c", "spi", "uart",
        "home automation", "remote monitoring", "telemetry",
        "embedded c", "assembly", "verilog", "fpga",
        "protocol", "modbus", "can bus", "802.11",
    ],
    "DWM": [
        "sql", "mongodb", "data warehouse", "etl", "hadoop", "spark",
        "data mining", "analytics", "tableau", "power bi", "olap",
        "data pipeline", "redshift", "bigquery",
        "postgresql", "mysql", "database", "nosql", "cassandra",
        "data lake", "data mart", "star schema", "snowflake schema",
        "association rules", "apriori", "clustering", "decision tree",
        "data visualization", "dashboard", "report", "kpi",
        "business intelligence", "bi", "oltp",
        "data integration", "data quality", "data governance",
        "apache airflow", "dbt", "data engineering",
        "excel", "csv", "json", "xml", "data extraction",
        "web scraping", "crawling", "beautifulsoup", "scrapy",
    ],
    "CCS": [
        "aws", "azure", "gcp", "docker", "kubernetes", "cloud",
        "devops", "terraform", "serverless", "microservices",
        "ci/cd", "jenkins", "react", "node", "web", "fullstack",
        "rest api", "graphql", "nginx",
        "lambda", "ec2", "s3", "cloudformation", "azure devops",
        "google cloud", "heroku", "vercel", "netlify", "railway",
        "container", "orchestration", "helm", "istio",
        "github actions", "gitlab ci", "circleci", "ansible",
        "load balancer", "cdn", "api gateway", "service mesh",
        "full stack", "full-stack", "frontend", "backend", "mern",
        "mean", "express", "fastapi", "django", "flask", "spring",
        "next.js", "nuxt", "angular", "vue", "svelte",
        "mongodb", "postgresql", "redis", "elasticsearch",
        "html", "css", "javascript", "typescript",
        "responsive", "spa", "ssr", "pwa",
        "deployment", "hosting", "scaling", "monitoring",
        "prometheus", "grafana", "logging", "elk",
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
        "program": "AI / ML Honours", "type": "honours", "required_cgpa": 7.5,
        "relevant_subjects": ["Python", "Artificial Intelligence", "Data Structures and Algorithms"],
        "relevant_interests": ["Artificial Intelligence & Machine Learning", "Data Science & Analytics"],
        "project_keywords": ["python", "tensorflow", "pytorch", "machine learning", "deep learning", "ai", "neural", "prediction", "model"],
        "career_paths": ["ML Engineer", "Data Scientist", "AI Researcher"],
        "skills_gained": ["Deep Learning", "NLP", "Computer Vision", "MLOps"],
    },
    {
        "program": "Data Science minor", "type": "minor", "required_cgpa": 7.5,
        "relevant_subjects": ["Database Management Systems", "Python", "Data Structures and Algorithms"],
        "relevant_interests": ["Data Science & Analytics", "Artificial Intelligence & Machine Learning"],
        "project_keywords": ["sql", "data", "analytics", "pandas", "visualization", "database", "dashboard", "report"],
        "career_paths": ["Data Scientist", "Analytics Manager", "Research Scientist"],
        "skills_gained": ["Statistical Analysis", "Big Data", "Data Visualisation"],
    },
    {
        "program": "Cybersecurity Honours", "type": "honours", "required_cgpa": 7.0,
        "relevant_subjects": ["Computer Networks", "Operating Systems", "Cryptography & Network Security"],
        "relevant_interests": ["Network & Wireless Systems", "Cloud & Distributed Systems"],
        "project_keywords": ["security", "network", "firewall", "encryption", "penetration", "cyber", "authentication"],
        "career_paths": ["Security Analyst", "Penetration Tester", "Security Architect"],
        "skills_gained": ["Network Security", "Cryptography", "Ethical Hacking"],
    },
    {
        "program": "Cloud Computing Minor", "type": "minor", "required_cgpa": 7.0,
        "relevant_subjects": ["Computer Networks", "Operating Systems", "Full Stack Development"],
        "relevant_interests": ["Cloud & Distributed Systems", "Web Development"],
        "project_keywords": ["aws", "azure", "docker", "kubernetes", "cloud", "devops", "deploy", "container", "server"],
        "career_paths": ["Cloud Architect", "DevOps Engineer", "SRE"],
        "skills_gained": ["Cloud Architecture", "Containerisation", "CI/CD"],
    },
    {
        "program": "IoT & Embedded Minor", "type": "minor", "required_cgpa": 6.5,
        "relevant_subjects": ["Microcontroller & Embedded Systems", "Computer Networks", "IoT"],
        "relevant_interests": ["Mobile & IoT Development", "Network & Wireless Systems"],
        "project_keywords": ["iot", "arduino", "raspberry", "embedded", "sensor", "mqtt", "gpio", "smart home"],
        "career_paths": ["IoT Engineer", "Embedded Developer", "Hardware Engineer"],
        "skills_gained": ["Embedded Programming", "Sensor Integration", "IoT Protocols"],
    },
]

CAREER_CATALOG = [
    {
        "career": "Software Development Engineer", "required_cgpa": 7.0,
        "salary_range": "₹6-15 LPA", "growth_potential": "High",
        "top_companies": ["Google", "Microsoft", "Amazon", "Flipkart"],
        "relevant_electives": ["ML", "CCS"],
        "relevant_interests": ["Web Development", "Cloud & Distributed Systems"],
        "project_keywords": ["web", "api", "fullstack", "react", "node", "frontend", "backend", "deploy", "app"],
        "required_certifications": ["AWS Cloud Practitioner"],
        "preparation_path": ["Master DSA", "Build full-stack projects", "Practice LeetCode"],
    },
    {
        "career": "Data Scientist", "required_cgpa": 7.5,
        "salary_range": "₹8-20 LPA", "growth_potential": "Very High",
        "top_companies": ["Google", "Amazon", "Netflix", "Uber"],
        "relevant_electives": ["ML", "DWM"],
        "relevant_interests": ["Artificial Intelligence & Machine Learning", "Data Science & Analytics"],
        "project_keywords": ["machine learning", "data", "python", "tensorflow", "prediction", "model", "analytics"],
        "required_certifications": ["Google Data Analytics", "IBM Data Science"],
        "preparation_path": ["Complete ML courses", "Build ML projects", "Kaggle competitions"],
    },
    {
        "career": "Cloud / DevOps Engineer", "required_cgpa": 6.5,
        "salary_range": "₹7-18 LPA", "growth_potential": "High",
        "top_companies": ["AWS", "Microsoft Azure", "Google Cloud"],
        "relevant_electives": ["CCS"],
        "relevant_interests": ["Cloud & Distributed Systems", "Network & Wireless Systems"],
        "project_keywords": ["docker", "kubernetes", "aws", "cloud", "devops", "deploy", "ci/cd", "container"],
        "required_certifications": ["AWS Solutions Architect"],
        "preparation_path": ["Get cloud certification", "Learn Docker/K8s", "Build CI/CD pipelines"],
    },
    {
        "career": "IoT / Embedded Engineer", "required_cgpa": 6.5,
        "salary_range": "₹5-14 LPA", "growth_potential": "High",
        "top_companies": ["Bosch", "Siemens", "Texas Instruments", "Qualcomm"],
        "relevant_electives": ["WT"],
        "relevant_interests": ["Mobile & IoT Development", "Network & Wireless Systems"],
        "project_keywords": ["iot", "arduino", "embedded", "sensor", "raspberry pi", "mqtt", "hardware"],
        "required_certifications": ["ARM Certified Engineer"],
        "preparation_path": ["Master embedded C/C++", "Build IoT prototypes"],
    },
]


CONCEPT_MAP = {
    "ML": [
        ("predict", 0.5), ("train", 0.4), ("model", 0.4),
        ("accuracy", 0.5), ("dataset", 0.5), ("feature", 0.3),
        ("neural", 0.6), ("intelligent", 0.4), ("automat", 0.3),
        ("recogni", 0.5), ("detect", 0.4), ("classif", 0.5),
        ("generat", 0.3), ("recommend", 0.4), ("cluster", 0.4),
        ("sentiment", 0.6), ("chatbot", 0.5), ("smart", 0.2),
        ("analys", 0.3), ("label", 0.3), ("supervis", 0.5),
        ("optimi", 0.3), ("loss", 0.3), ("epoch", 0.6),
    ],
    "WT": [
        ("sensor", 0.6), ("device", 0.3), ("hardware", 0.5),
        ("circuit", 0.5), ("signal", 0.5), ("transmit", 0.5),
        ("monitor", 0.3), ("remote", 0.3), ("smart home", 0.6),
        ("track", 0.2), ("real-time", 0.3), ("wearable", 0.5),
        ("temperatur", 0.4), ("humid", 0.4), ("motor", 0.4),
        ("relay", 0.5), ("actuator", 0.5), ("gpio", 0.6),
    ],
    "DWM": [
        ("database", 0.5), ("query", 0.4), ("stor", 0.3),
        ("report", 0.4), ("insight", 0.4), ("trend", 0.3),
        ("visualiz", 0.5), ("chart", 0.3), ("graph", 0.3),
        ("metric", 0.3), ("pattern", 0.3), ("aggregat", 0.3),
        ("warehouse", 0.6), ("pipeline", 0.4), ("extract", 0.3),
        ("transform", 0.3), ("schema", 0.4), ("dimension", 0.4),
    ],
    "CCS": [
        ("deploy", 0.5), ("host", 0.4), ("server", 0.4),
        ("website", 0.4), ("app", 0.3), ("platform", 0.3),
        ("login", 0.3), ("authenticat", 0.4), ("crud", 0.4),
        ("responsive", 0.3), ("dashboard", 0.4), ("portal", 0.3),
        ("containeriz", 0.5), ("scalab", 0.4), ("endpoint", 0.4),
        ("route", 0.3), ("middlewar", 0.4), ("component", 0.3),
    ],
}


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
    """Count keyword hits across ALL project text fields."""
    hits = 0
    for p in projects:
        blob_parts = [
            p.get("title", ""),
            p.get("description", ""),
            p.get("detailed_description", "") or p.get("detailedDescription", ""),
            " ".join(p.get("programming_languages", []) or p.get("programmingLanguages", [])),
            " ".join(p.get("frameworks", [])),
            " ".join(p.get("tools", [])),
            " ".join(p.get("technologies", [])),
            " ".join(p.get("extracted_skills", []) or p.get("extractedSkills", [])),
            " ".join(p.get("key_achievements", []) or p.get("keyAchievements", [])),
            " ".join(p.get("challenges_faced", []) or p.get("challengesFaced", [])),
            " ".join(p.get("learnings", [])),
            p.get("role_in_project", "") or p.get("roleInProject", ""),
        ]
        blob = " ".join(str(part) for part in blob_parts if part).lower()
        hits += sum(1 for kw in keywords if kw in blob)
    return hits


def _matching_projects_detail(projects: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:
    """Return detailed info about matching projects."""
    matched = []
    for p in projects:
        blob_parts = [
            p.get("title", ""),
            p.get("description", ""),
            p.get("detailed_description", "") or p.get("detailedDescription", ""),
            " ".join(p.get("programming_languages", []) or p.get("programmingLanguages", [])),
            " ".join(p.get("frameworks", [])),
            " ".join(p.get("tools", [])),
            " ".join(p.get("technologies", [])),
            " ".join(p.get("extracted_skills", []) or p.get("extractedSkills", [])),
            " ".join(p.get("key_achievements", []) or p.get("keyAchievements", [])),
            " ".join(p.get("learnings", [])),
        ]
        blob = " ".join(str(part) for part in blob_parts if part).lower()
        matched_keywords = [kw for kw in keywords if kw in blob]
        if matched_keywords:
            all_proj_skills = list(set(
                (p.get("programming_languages", []) or p.get("programmingLanguages", [])) +
                p.get("frameworks", []) +
                p.get("tools", []) +
                (p.get("extracted_skills", []) or p.get("extractedSkills", []))
            ))
            matched.append({
                "title": p.get("title", "Untitled"),
                "matched_skills": matched_keywords[:8],
                "project_skills": all_proj_skills[:10],
                "complexity": p.get("complexity_score", 0.5),
                "relevance_score": min(len(matched_keywords) * 10, 100),
                "has_github": bool(p.get("github_url") or p.get("githubUrl")),
                "has_demo": bool(p.get("demo_url") or p.get("demoUrl")),
            })
    matched.sort(key=lambda x: x["relevance_score"], reverse=True)
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
#  SCORE BREAKDOWN CLASSES
# ═══════════════════════════════════════════════════════════════════

class ScoreBreakdown:
    def __init__(self):
        self.academic = {
            "score": 0.0, "max_possible": 40.0, "percentage": 0,
            "contributing_subjects": [], "missing_subjects": [],
            "strong_subjects": [], "weak_subjects": [],
        }
        self.interest = {
            "score": 0.0, "max_possible": 30.0, "percentage": 0,
            "matched_interests": [], "unmatched_interests": [],
            "semantic_similarity": 0.0,
        }
        self.project = {
            "score": 0.0, "max_possible": 30.0, "percentage": 0,
            "relevant_projects": [], "keyword_hits": 0,
            "missing_project_skills": [], "average_complexity": 0.0,
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
            "rank": self.rank, "total_options": self.total_options,
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
            "has_marks": False, "has_interests": False, "has_projects": False,
            "marks_count": 0, "project_count": 0, "interest_count": 0,
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
#  DATA AVAILABILITY PROFILES
# ═══════════════════════════════════════════════════════════════════

class DataAvailabilityProfile:
    """Determines what data a student has and adjusts weights accordingly."""

    def __init__(self, marks: Dict, interests: Any, projects: List):
        self.has_marks = len(marks) > 0
        self.has_interests = False
        self.has_projects = len(projects) > 0
        self.marks_count = len(marks)
        self.project_count = len(projects)
        self.interest_count = 0

        if isinstance(interests, list):
            self.interest_count = len(interests)
            self.has_interests = len(interests) > 0
        elif isinstance(interests, dict):
            self.interest_count = len([v for v in interests.values() if v > 0])
            self.has_interests = self.interest_count > 0

        # Dynamic weights based on what's available
        self.weights = self._compute_weights()
        self.profile_type = self._classify()
        self.recommendations_for_user: List[str] = self._generate_data_tips()

    def _compute_weights(self) -> Dict[str, float]:
        """
        Redistribute weights based on available data.
        
        Full data:    Marks 40% + Interests 30% + Projects 30%
        Marks only:   Marks 80% + Interests 0%  + Projects 0%  + Heuristic 20%
        Marks+Int:    Marks 55% + Interests 35% + Projects 0%  + Heuristic 10%
        Marks+Proj:   Marks 50% + Interests 0%  + Projects 40% + Heuristic 10%
        No data:      All heuristic (CGPA-based)
        """
        has_m = self.has_marks
        has_i = self.has_interests
        has_p = self.has_projects

        if has_m and has_i and has_p:
            return {"marks": 40, "interests": 30, "projects": 30, "heuristic": 0}
        elif has_m and has_i and not has_p:
            return {"marks": 55, "interests": 35, "projects": 0, "heuristic": 10}
        elif has_m and not has_i and has_p:
            return {"marks": 50, "interests": 0, "projects": 40, "heuristic": 10}
        elif has_m and not has_i and not has_p:
            return {"marks": 80, "interests": 0, "projects": 0, "heuristic": 20}
        elif not has_m and has_i and has_p:
            return {"marks": 0, "interests": 45, "projects": 45, "heuristic": 10}
        elif not has_m and has_i and not has_p:
            return {"marks": 0, "interests": 70, "projects": 0, "heuristic": 30}
        elif not has_m and not has_i and has_p:
            return {"marks": 0, "interests": 0, "projects": 70, "heuristic": 30}
        else:
            return {"marks": 0, "interests": 0, "projects": 0, "heuristic": 100}

    def _classify(self) -> str:
        if self.has_marks and self.has_interests and self.has_projects:
            return "full_profile"
        elif self.has_marks and (self.has_interests or self.has_projects):
            return "partial_profile"
        elif self.has_marks:
            return "marks_only"
        elif self.has_interests or self.has_projects:
            return "no_marks"
        else:
            return "empty_profile"

    def _generate_data_tips(self) -> List[str]:
        tips = []
        if not self.has_interests:
            tips.append("💡 Add your interests (AI/ML, Web Dev, etc.) for 30% better accuracy")
        if not self.has_projects:
            tips.append("🔧 Upload at least 2 projects to unlock project-based matching")
        if self.marks_count < 5:
            tips.append("📊 More subject marks = more accurate recommendations")
        if self.interest_count == 1:
            tips.append("💡 Adding a second interest area improves recommendation diversity")
        if self.project_count == 1:
            tips.append("🔧 One more project would significantly improve accuracy")
        return tips

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_type": self.profile_type,
            "has_marks": self.has_marks,
            "has_interests": self.has_interests,
            "has_projects": self.has_projects,
            "marks_count": self.marks_count,
            "interest_count": self.interest_count,
            "project_count": self.project_count,
            "weights_used": self.weights,
            "data_improvement_tips": self.recommendations_for_user,
        }


# ═══════════════════════════════════════════════════════════════════
#  WHAT-IF ANALYSIS (Student wants specific elective)
# ═══════════════════════════════════════════════════════════════════

class WhatIfAnalysis:
    """Analyze what happens if student picks a specific elective they want."""

    @staticmethod
    def analyze(
        chosen_elective: str,
        all_recommendations: List[Dict[str, Any]],
        canon_marks: Dict[str, float],
        elective_meta: Dict,
        subject_weights: Dict,
    ) -> Dict[str, Any]:
        """
        Returns analysis of chosen elective vs recommendations.
        """
        # Find the chosen one in recommendations
        chosen_rec = None
        chosen_rank = 0
        top_rec = all_recommendations[0] if all_recommendations else None

        for i, rec in enumerate(all_recommendations):
            code = rec.get("elective_code", "")
            name = rec.get("elective_name", "")
            if (chosen_elective.upper() in code.upper() or
                chosen_elective.lower() in name.lower()):
                chosen_rec = rec
                chosen_rank = i + 1
                break

        if not chosen_rec:
            return {
                "found": False,
                "message": f"'{chosen_elective}' not found in available electives",
            }

        # Determine risk level
        score = chosen_rec.get("match_score", 0)
        if score >= 65:
            risk = "low"
            risk_message = "Good fit! You're well-aligned with this elective."
        elif score >= 45:
            risk = "medium"
            risk_message = "Moderate fit. Some preparation recommended."
        elif score >= 25:
            risk = "high"
            risk_message = "Challenging choice. Significant preparation needed."
        else:
            risk = "very_high"
            risk_message = "Very challenging. Consider your top recommendation instead."

        # Find specific gaps
        gaps = chosen_rec.get("skill_gaps", [])
        weak_subjects = []
        bd = chosen_rec.get("score_breakdown", {})
        if bd:
            acad = bd.get("academic_component", {})
            weak_subjects = acad.get("weak_subjects", [])

        # Generate preparation plan
        prep_steps = []
        if weak_subjects:
            for subj in weak_subjects[:3]:
                prep_steps.append(f"📚 Revise {subj} — focus on fundamentals")
        if gaps:
            for gap in gaps[:2]:
                prep_steps.append(
                    f"📈 Improve {gap.get('subject', 'subject')} from "
                    f"{gap.get('current_score', 0)} to {gap.get('target_score', 60)}"
                )

        meta = elective_meta.get(chosen_elective, {})
        if meta.get("skills"):
            prep_steps.append(f"💻 Self-study: {', '.join(meta['skills'][:3])}")

        # Comparison with top choice
        comparison = {}
        if top_rec and chosen_rank > 1:
            diff = top_rec.get("match_score", 0) - score
            comparison = {
                "top_recommendation": top_rec.get("elective_name", ""),
                "top_score": top_rec.get("match_score", 0),
                "your_choice_score": score,
                "score_difference": round(diff, 1),
                "message": (
                    f"Your choice scores {round(diff, 1)} points lower than "
                    f"'{top_rec.get('elective_name', '')}'. "
                    f"{'This is a small gap — your choice is still viable!' if diff < 15 else 'Consider the top recommendation for best results.'}"
                ),
            }

        return {
            "found": True,
            "chosen_elective": chosen_rec.get("elective_name", ""),
            "chosen_code": chosen_rec.get("elective_code", ""),
            "your_rank": chosen_rank,
            "total_options": len(all_recommendations),
            "match_score": score,
            "risk_level": risk,
            "risk_message": risk_message,
            "weak_subjects": weak_subjects,
            "skill_gaps": gaps[:4],
            "preparation_plan": prep_steps,
            "comparison_with_top": comparison,
            "can_succeed": risk in ("low", "medium"),
            "advice": (
                "Go for it! Your profile aligns well." if risk == "low"
                else "Doable with some preparation. Follow the study plan." if risk == "medium"
                else "Challenging but not impossible. Consider tutoring or extra study hours." if risk == "high"
                else "We recommend reconsidering. Your top match is significantly better aligned."
            ),
        }

# ═══════════════════════════════════════════════════════════════════
#  ENGINE
# ═══════════════════════════════════════════════════════════════════

class CumulativeRecommendationEngine:
    MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved")
    ELECTIVE_META = ELECTIVE_META
    OPEN_ELECTIVE_META = OPEN_ELECTIVE_META

    def __init__(self, load_pretrained: bool = True):
        self.rf_clf: Optional[RandomForestClassifier] = None
        self.knn_clf: Optional[KNeighborsClassifier] = None
        self.scaler = StandardScaler()
        self.label_enc = LabelEncoder()
        self.is_trained = False
        # Open elective ML models (separate from program elective models)
        self.oe_rf_clf: Optional[RandomForestClassifier] = None
        self.oe_scaler = StandardScaler()
        self.oe_label_enc = LabelEncoder()
        self.oe_is_trained = False
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

    # ── Feature extraction ──────────────────────────────────────

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

    def extract_oe_features(
        self, marks: Dict[str, float], interests: Any, projects: List[Dict[str, Any]]
    ) -> np.ndarray:
        """Extract features for open elective recommendation."""
        canon_marks = _canonicalise_marks(marks)
        feat: List[float] = []
        # Subject scores
        for subj in CANONICAL_SUBJECTS:
            feat.append(canon_marks.get(subj, 0.0) / 100.0)
        # Aggregates
        vals = [v for v in canon_marks.values() if v > 0]
        if vals:
            feat += [np.mean(vals) / 100, np.std(vals) / 100, np.max(vals) / 100, np.min(vals) / 100]
        else:
            feat += [0.0, 0.0, 0.0, 0.0]
        # Interests
        ni = _normalise_interests(interests)
        for area in INTEREST_AREAS:
            feat.append(ni.get(area, 0.0))
        # Project features for OE categories
        n = len(projects)
        feat.append(min(n / 10.0, 1.0))
        for oe in OPEN_ELECTIVE_LABELS:
            feat.append(min(_project_hits(projects, OE_PROJECT_SKILL_MAP[oe]) / 15.0, 1.0))
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

    # ── Generic academic score (reusable for both PEC and OEC) ──

    def _calculate_academic_score_generic(
        self, canon_marks: Dict[str, float], weights: Dict[str, float]
    ) -> Tuple[float, ScoreBreakdown]:
        breakdown = ScoreBreakdown()
        total_weighted_score = 0.0
        total_weight = 0.0
        for subj, weight in weights.items():
            mark = canon_marks.get(subj, -1)
            if mark < 0:
                breakdown.academic["missing_subjects"].append({
                    "subject": subj, "weight": weight,
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
                    "subject": subj, "score": mark, "weight": weight,
                    "contribution": round((mark / 100) * weight * (40 / max(sum(weights.values()), 1)), 2),
                    "status": status
                })
        if total_weight > 0:
            score = (total_weighted_score / total_weight / 100) * 40
        else:
            score = 0.0
        breakdown.academic["score"] = round(score, 2)
        breakdown.academic["percentage"] = round((score / 40) * 100, 1) if score > 0 else 0
        return score, breakdown

    # ── Academic score (program electives) ──────────────────────

    def _calculate_academic_score(
        self, canon_marks: Dict[str, float], elective: str
    ) -> Tuple[float, ScoreBreakdown]:
        weights = SUBJECT_WEIGHTS.get(elective, {})
        return self._calculate_academic_score_generic(canon_marks, weights)

    # ── Interest score (generic) ────────────────────────────────

    def _calculate_interest_score_generic(
        self, norm_interests: Dict[str, float], mapping: List[Tuple[str, float]]
    ) -> Tuple[float, Dict[str, Any]]:
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
            "score": round(score, 2), "max_possible": 30.0,
            "percentage": round((score / 30) * 100, 1),
            "matched_interests": matched, "unmatched_interests": unmatched,
        }

    def _calculate_interest_score(
        self, norm_interests: Dict[str, float], elective: str, raw_interests: Any
    ) -> Tuple[float, Dict[str, Any]]:
        mapping = INTEREST_ELECTIVE_MAP.get(elective, [])
        return self._calculate_interest_score_generic(norm_interests, mapping)

    # ── Project score (generic) ─────────────────────────────────

    def _calculate_project_score_generic(
        self, projects: List[Dict[str, Any]], keywords: List[str],
        concept_map_key: Optional[str] = None
    ) -> Tuple[float, Dict[str, Any]]:
        hits = _project_hits(projects, keywords)
        matched_projects = _matching_projects_detail(projects, keywords)
        keyword_score = min(hits * 3.5, 20.0)

        concept_score = 0.0
        if concept_map_key and projects:
            concept_score = self._concept_match_score_generic(projects, concept_map_key)

        count_bonus = min(len(projects) * 0.8, 3.0)

        quality_bonus = 0.0
        for p in projects:
            if p.get("github_url") or p.get("githubUrl"):
                quality_bonus += 0.3
            if p.get("demo_url") or p.get("demoUrl"):
                quality_bonus += 0.3
            quality_bonus += p.get("complexity_score", 0.5) * 0.2
        quality_bonus = min(quality_bonus, 2.0)

        score = min(round(keyword_score + concept_score + count_bonus + quality_bonus, 2), 30.0)

        all_project_skills: set = set()
        for p in projects:
            for key in ("extracted_skills", "extractedSkills",
                        "programming_languages", "programmingLanguages",
                        "frameworks", "tools"):
                vals = p.get(key, [])
                if vals:
                    all_project_skills.update(s.lower() for s in vals)
        missing_skills = [kw for kw in keywords[:15] if kw not in all_project_skills][:5]

        complexities = [p.get("complexity_score", 0.5) for p in projects]
        avg_complexity = float(np.mean(complexities)) if complexities else 0.0

        return score, {
            "score": round(score, 2), "max_possible": 30.0,
            "percentage": round((score / 30) * 100, 1),
            "relevant_projects": matched_projects[:5],
            "keyword_hits": hits,
            "concept_match_score": round(concept_score, 2),
            "missing_project_skills": missing_skills,
            "average_complexity": round(avg_complexity, 2),
            "total_projects_analyzed": len(projects),
            "scoring_detail": {
                "keyword_score": round(keyword_score, 2),
                "concept_score": round(concept_score, 2),
                "count_bonus": round(count_bonus, 2),
                "quality_bonus": round(quality_bonus, 2),
            },
        }

    def _calculate_project_score(
        self, projects: List[Dict[str, Any]], elective: str
    ) -> Tuple[float, Dict[str, Any]]:
        keywords = PROJECT_SKILL_MAP.get(elective, [])
        return self._calculate_project_score_generic(projects, keywords, elective)

    # ── Concept matching (generic) ──────────────────────────────

    def _concept_match_score_generic(
        self, projects: List[Dict[str, Any]], key: str
    ) -> float:
        # Check both maps
        concepts = CONCEPT_MAP.get(key, OE_CONCEPT_MAP.get(key, []))
        if not concepts:
            return 0.0
        total = 0.0
        for p in projects:
            desc = " ".join([
                p.get("title", ""),
                p.get("description", ""),
                p.get("detailed_description", "") or p.get("detailedDescription", ""),
                " ".join(p.get("key_achievements", []) or p.get("keyAchievements", [])),
                " ".join(p.get("learnings", [])),
            ]).lower()
            for concept, weight in concepts:
                if concept in desc:
                    total += weight
        return min(total, 5.0)

    def _concept_match_score(
        self, projects: List[Dict[str, Any]], elective: str
    ) -> float:
        return self._concept_match_score_generic(projects, elective)

    # ── Semantic boost ──────────────────────────────────────────

    def _calculate_semantic_boost(self, interests: Any, projects: List, elective: str) -> float:
        if not self.sbert:
            return 0.0
        try:
            student_text = " ".join(interests if isinstance(interests, list) else [])
            for p in projects:
                student_text += " " + p.get("description", "")
            # Look up description in either meta dict
            meta = ELECTIVE_META.get(elective, OPEN_ELECTIVE_META.get(elective, {}))
            desc = meta.get("description", "")
            if not desc:
                return 0.0
            embs = self.sbert.encode([student_text, desc])
            sim = cos_sim([embs[0]], [embs[1]])[0][0]
            return float(sim) * 10
        except Exception:
            return 0.0

    # ── Improvement tips ────────────────────────────────────────

    def _generate_improvement_tips(self, breakdown: Dict[str, Any], elective: str) -> List[str]:
        tips = []
        meta = ELECTIVE_META.get(elective, OPEN_ELECTIVE_META.get(elective, {}))
        acad = breakdown.get("academic_component", {})
        if acad.get("missing_subjects"):
            m = acad["missing_subjects"][0]
            tips.append(f"Take {m['subject']} to potentially add {m['impact']}")
        if acad.get("weak_subjects"):
            tips.append(f"Improve your score in {acad['weak_subjects'][0]} (currently weak)")
        intr = breakdown.get("interest_component", {})
        if intr.get("unmatched_interests"):
            u = intr["unmatched_interests"][0]
            tips.append(f"Declaring interest in '{u['interest']}' could add {u['potential_boost']} points")
        proj = breakdown.get("project_component", {})
        if proj.get("missing_project_skills"):
            skills = proj["missing_project_skills"][:3]
            tips.append(f"Build a project using {', '.join(skills)} to improve alignment")
        if proj.get("total_projects_analyzed", 0) < 2:
            tips.append("Upload more projects for better accuracy")
        return tips[:4]

    # ── What-If Analysis endpoint ───────────────────────────────

    def analyze_elective_choice(
        self,
        chosen_elective: str,
        marks: Dict[str, float],
        interests: Any,
        projects: List[Dict[str, Any]],
        cgpa: float = 0.0,
        is_open_elective: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze a student's specific elective choice.
        Returns risk assessment, gaps, and preparation plan.
        """
        if is_open_elective:
            recs = self.recommend_open_electives(marks, interests, projects, cgpa)
            meta = OPEN_ELECTIVE_META
            weights = OE_SUBJECT_WEIGHTS
        else:
            recs = self.recommend_electives(marks, interests, projects, cgpa)
            meta = ELECTIVE_META
            weights = SUBJECT_WEIGHTS

        canon_marks = _canonicalise_marks(marks)

        return WhatIfAnalysis.analyze(
            chosen_elective=chosen_elective,
            all_recommendations=recs,
            canon_marks=canon_marks,
            elective_meta=meta,
            subject_weights=weights,
        )

    # ── Honours constraint check ────────────────────────────────

    @staticmethod
    def check_honours_constraints(
        student_honours: Optional[str],
        recommended_electives: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Apply honours/minor constraints.
        E.g., AIML Honours students should NOT be recommended ML as PEC.
        """
        if not student_honours:
            return recommended_electives

        constraints = {
            "AIML": ["ML"],           # AIML honours → can't take ML elective
            "AI/ML": ["ML"],
            "AI & Machine Learning": ["ML"],
            "Cybersecurity": ["CSL"],  # Cybersecurity honours → CSL overlap
        }

        blocked_keys = set()
        for honours_name, blocked in constraints.items():
            if honours_name.lower() in student_honours.lower():
                blocked_keys.update(blocked)

        if not blocked_keys:
            return recommended_electives

        filtered = []
        for rec in recommended_electives:
            code = rec.get("elective_code", "")
            # Check if this elective's key is blocked
            code_to_key = {
                "ITPEC5012": "ML", "ITPEC5013": "WT",
                "ITPEC5014": "DWM", "ITPEC5015": "CCS",
            }
            key = code_to_key.get(code, "")
            if key in blocked_keys:
                rec["_blocked"] = True
                rec["_blocked_reason"] = f"Overlaps with your {student_honours} Honours programme"
            filtered.append(rec)

        return filtered
    # ── Main elective recommendation (program electives) ────────

    def recommend_electives(
        self,
        marks: Dict[str, float],
        interests: Any,
        projects: List[Dict[str, Any]],
        cgpa: float = 0.0,
        use_ml: bool = True,
    ) -> List[Dict[str, Any]]:
        canon_marks = _canonicalise_marks(marks)
        norm_interests = _normalise_interests(interests)
        interest_list = interests if isinstance(interests, list) else list(interests.keys()) if isinstance(interests, dict) else []

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

        scored = []
        for elec in ["ML", "WT", "DWM", "CCS"]:
            academic_score, breakdown = self._calculate_academic_score(canon_marks, elec)
            interest_score, interest_details = self._calculate_interest_score(norm_interests, elec, interests)
            project_score, project_details = self._calculate_project_score(projects, elec)

            breakdown.interest = interest_details
            breakdown.project = project_details

            sem_boost = self._calculate_semantic_boost(interest_list, projects, elec)
            breakdown.interest["semantic_similarity"] = round(sem_boost / 10, 2)

            final = academic_score + interest_score + project_score
            ml_boost = 0.0
            if elec in ml_probs:
                ml_boost = ml_probs[elec] * 20
                final += ml_boost
            final += sem_boost
            final = round(min(max(final, 0), 100), 1)

            scored.append({
                "_key": elec, "_final": final,
                "_breakdown": breakdown.to_dict(),
                "_academic_score": academic_score,
                "_interest_score": interest_score,
                "_project_score": project_score,
                "_ml_boost": ml_boost, "_sem_boost": sem_boost,
            })

        scored.sort(key=lambda x: x["_final"], reverse=True)

        results = []
        for rank, item in enumerate(scored, 1):
            elec = item["_key"]
            meta = ELECTIVE_META[elec]

            ranking = RankingExplanation()
            ranking.rank = rank
            ranking.total_options = len(scored)
            if rank == 1:
                ranking.why_this_rank = "Strongest combined alignment across academics, interests, and projects"
                if len(scored) > 1:
                    diff = item["_final"] - scored[1]["_final"]
                    ranking.vs_other_electives.append({
                        "compared_to": ELECTIVE_META[scored[1]["_key"]]["name"],
                        "score_difference": round(diff, 1),
                        "message": f"{round(diff, 1)} points higher than second choice"
                    })
            elif rank == 2:
                ranking.why_this_rank = "Strong alternative - second best alignment"
                diff = scored[0]["_final"] - item["_final"]
                ranking.vs_other_electives.append({
                    "compared_to": ELECTIVE_META[scored[0]["_key"]]["name"],
                    "score_difference": round(-diff, 1),
                    "message": f"{round(diff, 1)} points below top choice"
                })
            else:
                ranking.why_this_rank = "Lower alignment - consider if schedule conflicts with top choices"

            ranking.improvement_tips = self._generate_improvement_tips(item["_breakdown"], elec)

            skill_gaps = []
            for subj in item["_breakdown"]["academic_component"].get("weak_subjects", []):
                for contrib in item["_breakdown"]["academic_component"].get("contributing_subjects", []):
                    if contrib["subject"] == subj:
                        skill_gaps.append({
                            "subject": subj, "current_score": contrib["score"],
                            "target_score": 60, "gap": round(60 - contrib["score"], 1),
                            "importance": "High" if contrib["weight"] >= 3.0 else "Medium"
                        })
                        break

            text_explanation = self._build_text_explanation(elec, item, rank, len(scored))

            results.append({
                "elective_code": meta["code"], "elective_name": meta["name"],
                "credits": meta["credits"], "match_score": item["_final"],
                "score_breakdown": item["_breakdown"],
                "ranking_explanation": ranking.to_dict(),
                "confidence": confidence.to_dict(),
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

    # ═══════════════════════════════════════════════════════════
    #  OPEN ELECTIVE RECOMMENDATION (Sem VII) — NEW
    # ═══════════════════════════════════════════════════════════

    def recommend_open_electives(
        self,
        marks: Dict[str, float],
        interests: Any,
        projects: List[Dict[str, Any]],
        cgpa: float = 0.0,
        use_ml: bool = True,
    ) -> List[Dict[str, Any]]:
        """Recommend from the 5 Semester-VII Open Electives."""
        canon_marks = _canonicalise_marks(marks)
        norm_interests = _normalise_interests(interests)
        interest_list = interests if isinstance(interests, list) else list(interests.keys()) if isinstance(interests, dict) else []

        confidence = ConfidenceMetrics()
        confidence.calculate(marks, interests, projects)

        # ML predictions for OE
        ml_probs: Dict[str, float] = {}
        if use_ml and self.oe_is_trained:
            try:
                feat = self.extract_oe_features(marks, interests, projects)
                feat_scaled = self.oe_scaler.transform([feat])
                probs = self.oe_rf_clf.predict_proba(feat_scaled)[0]
                ml_probs = dict(zip(self.oe_label_enc.classes_, probs))
            except Exception as e:
                logger.warning(f"OE ML prediction failed: {e}")

        scored = []
        for oe in OPEN_ELECTIVE_LABELS:
            weights = OE_SUBJECT_WEIGHTS.get(oe, {})
            academic_score, breakdown = self._calculate_academic_score_generic(canon_marks, weights)

            mapping = OE_INTEREST_MAP.get(oe, [])
            interest_score, interest_details = self._calculate_interest_score_generic(norm_interests, mapping)

            keywords = OE_PROJECT_SKILL_MAP.get(oe, [])
            project_score, project_details = self._calculate_project_score_generic(projects, keywords, oe)

            breakdown.interest = interest_details
            breakdown.project = project_details

            sem_boost = self._calculate_semantic_boost(interest_list, projects, oe)
            breakdown.interest["semantic_similarity"] = round(sem_boost / 10, 2)

            final = academic_score + interest_score + project_score
            ml_boost = 0.0
            if oe in ml_probs:
                ml_boost = ml_probs[oe] * 15
                final += ml_boost
            final += sem_boost
            final = round(min(max(final, 0), 100), 1)

            scored.append({
                "_key": oe, "_final": final,
                "_breakdown": breakdown.to_dict(),
                "_academic_score": academic_score,
                "_interest_score": interest_score,
                "_project_score": project_score,
                "_ml_boost": ml_boost, "_sem_boost": sem_boost,
            })

        scored.sort(key=lambda x: x["_final"], reverse=True)

        results = []
        for rank, item in enumerate(scored, 1):
            oe = item["_key"]
            meta = OPEN_ELECTIVE_META[oe]

            ranking = RankingExplanation()
            ranking.rank = rank
            ranking.total_options = len(scored)
            if rank == 1:
                ranking.why_this_rank = "Best overall alignment for your profile among open electives"
                if len(scored) > 1:
                    diff = item["_final"] - scored[1]["_final"]
                    ranking.vs_other_electives.append({
                        "compared_to": OPEN_ELECTIVE_META[scored[1]["_key"]]["name"],
                        "score_difference": round(diff, 1),
                        "message": f"{round(diff, 1)} points higher than second choice"
                    })
            elif rank == 2:
                ranking.why_this_rank = "Strong alternative open elective"
                diff = scored[0]["_final"] - item["_final"]
                ranking.vs_other_electives.append({
                    "compared_to": OPEN_ELECTIVE_META[scored[0]["_key"]]["name"],
                    "score_difference": round(-diff, 1),
                    "message": f"{round(diff, 1)} points below top choice"
                })
            else:
                ranking.why_this_rank = "Lower alignment — consider based on personal interest or schedule"

            ranking.improvement_tips = self._generate_improvement_tips(item["_breakdown"], oe)

            skill_gaps = []
            for subj in item["_breakdown"]["academic_component"].get("weak_subjects", []):
                for contrib in item["_breakdown"]["academic_component"].get("contributing_subjects", []):
                    if contrib["subject"] == subj:
                        skill_gaps.append({
                            "subject": subj, "current_score": contrib["score"],
                            "target_score": 60, "gap": round(60 - contrib["score"], 1),
                            "importance": "High" if contrib["weight"] >= 3.0 else "Medium"
                        })
                        break

            text_explanation = self._build_oe_text_explanation(oe, item, rank, len(scored))

            results.append({
                "elective_code": meta["code"],
                "elective_name": meta["name"],
                "credits": meta["credits"],
                "semester": meta["semester"],
                "category": meta["category"],
                "match_score": item["_final"],
                "score_breakdown": item["_breakdown"],
                "ranking_explanation": ranking.to_dict(),
                "confidence": confidence.to_dict(),
                "match_explanation": text_explanation,
                "prerequisites_met": True,
                "skill_alignment": meta["skills"][:6],
                "career_relevance": meta["career_paths"],
                "modules": meta.get("modules", []),
                "recommendation_basis": {
                    "interests_weight": round(item["_interest_score"], 1),
                    "performance_weight": round(item["_academic_score"], 1),
                    "projects_weight": round(item["_project_score"], 1),
                },
                "skill_gaps": skill_gaps[:4],
            })
        return results

    def _build_oe_text_explanation(self, oe: str, item: Dict, rank: int, total: int) -> str:
        meta = OPEN_ELECTIVE_META[oe]
        bd = item["_breakdown"]
        parts = [f"Ranked #{rank} of {total} open electives with a score of {item['_final']:.1f}%."]
        acad = bd["academic_component"]
        if acad["contributing_subjects"]:
            parts.append(f"\n📊 Academic ({acad['score']:.1f}/40, {acad['percentage']}%):")
            if acad["strong_subjects"]:
                parts.append(f"  Strengths: {', '.join(acad['strong_subjects'][:3])}")
            if acad["weak_subjects"]:
                parts.append(f"  Needs work: {', '.join(acad['weak_subjects'][:2])}")
        else:
            parts.append("\n📊 Academic: No relevant marks data.")
        intr = bd["interest_component"]
        if intr["matched_interests"]:
            names = [m["interest"] for m in intr["matched_interests"]]
            parts.append(f"\n💡 Interests ({intr['score']:.1f}/30): Matches {', '.join(names)}")
        else:
            parts.append("\n💡 Interests: No matching interests declared.")
        proj = bd["project_component"]
        if proj["relevant_projects"]:
            titles = [p["title"] for p in proj["relevant_projects"][:2]]
            parts.append(f"\n🔧 Projects ({proj['score']:.1f}/30, {proj['keyword_hits']} keyword matches):")
            parts.append(f"  Relevant: {', '.join(titles)}")
        else:
            parts.append(f"\n🔧 Projects: No matches. Build projects with {', '.join(meta['skills'][:3])}.")
        return "\n".join(parts)

    def _build_text_explanation(self, elec: str, item: Dict, rank: int, total: int) -> str:
        meta = ELECTIVE_META[elec]
        bd = item["_breakdown"]
        parts = [f"Ranked #{rank} of {total} with a score of {item['_final']:.1f}%."]
        acad = bd["academic_component"]
        if acad["contributing_subjects"]:
            parts.append(f"\n📊 Academic ({acad['score']:.1f}/40, {acad['percentage']}%):")
            if acad["strong_subjects"]:
                parts.append(f"  Strengths: {', '.join(acad['strong_subjects'][:3])}")
            if acad["weak_subjects"]:
                parts.append(f"  Needs work: {', '.join(acad['weak_subjects'][:2])}")
        else:
            parts.append("\n📊 Academic: No relevant marks data.")
        intr = bd["interest_component"]
        if intr["matched_interests"]:
            names = [m["interest"] for m in intr["matched_interests"]]
            parts.append(f"\n💡 Interests ({intr['score']:.1f}/30): Matches {', '.join(names)}")
        else:
            parts.append("\n💡 Interests: No matching interests declared.")
        proj = bd["project_component"]
        if proj["relevant_projects"]:
            titles = [p["title"] for p in proj["relevant_projects"][:2]]
            parts.append(f"\n🔧 Projects ({proj['score']:.1f}/30, {proj['keyword_hits']} keyword matches):")
            parts.append(f"  Relevant: {', '.join(titles)}")
        else:
            parts.append(f"\n🔧 Projects: No matches. Build projects with {', '.join(meta['skills'][:3])}.")
        return "\n".join(parts)

    # ── Honours recommendations ─────────────────────────────────

    def recommend_honours(self, marks, interests, projects, cgpa) -> List[Dict[str, Any]]:
        canon_marks = _canonicalise_marks(marks)
        norm_interests = _normalise_interests(interests)
        results = []
        for prog in HONOURS_PROGRAMS:
            eligible = cgpa >= prog["required_cgpa"]
            subj_score = 0.0
            matched_subjects = []
            for subj in prog["relevant_subjects"]:
                m = canon_marks.get(subj, 0)
                if m >= 60:
                    subj_score += 13.3
                    matched_subjects.append({"subject": subj, "score": m})
            subj_score = min(subj_score, 40)

            int_score = 0.0
            matched_interests = []
            for interest in prog["relevant_interests"]:
                val = norm_interests.get(interest, 0)
                if val > 0:
                    int_score += 15
                    matched_interests.append(interest)
            int_score = min(int_score, 30)

            hits = _project_hits(projects, prog["project_keywords"])
            proj_score = min(hits * 6, 30)
            matched_projects = _matching_projects_detail(projects, prog["project_keywords"])

            total_score = subj_score + int_score + proj_score
            explanation_parts = []
            if eligible:
                explanation_parts.append(f"✓ You meet the {prog['required_cgpa']} CGPA requirement (yours: {cgpa:.2f}).")
            else:
                gap = prog["required_cgpa"] - cgpa
                explanation_parts.append(f"✗ Need {gap:.2f} more CGPA (current: {cgpa:.2f}).")
            if matched_subjects:
                s = ", ".join([f"{x['subject']} ({x['score']}%)" for x in matched_subjects[:2]])
                explanation_parts.append(f"Strong in: {s}")
            if matched_interests:
                explanation_parts.append(f"Interest alignment: {', '.join(matched_interests)}")
            if matched_projects:
                explanation_parts.append(f"Relevant projects: {len(matched_projects)}")

            results.append({
                "program": prog["program"], "type": prog["type"],
                "match_score": round(min(total_score, 100), 1),
                "eligibility": eligible, "required_cgpa": prog["required_cgpa"],
                "career_paths": prog["career_paths"],
                "explanation": " | ".join(explanation_parts) or "Limited alignment.",
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

    # ── Career recommendations ──────────────────────────────────

    def recommend_careers(self, marks, interests, projects, cgpa) -> List[Dict[str, Any]]:
        norm_interests = _normalise_interests(interests)
        results = []
        for career in CAREER_CATALOG:
            cgpa_ok = cgpa >= career["required_cgpa"]
            int_score = 0.0
            matched_interests = []
            for interest in career["relevant_interests"]:
                val = norm_interests.get(interest, 0)
                if val > 0:
                    int_score += 20
                    matched_interests.append(interest)
            int_score = min(int_score, 40)
            hits = _project_hits(projects, career["project_keywords"])
            proj_score = min(hits * 7, 35)
            matched_projects = _matching_projects_detail(projects, career["project_keywords"])
            cgpa_score = 25 if cgpa_ok else (cgpa / career["required_cgpa"]) * 15
            total_score = int_score + proj_score + cgpa_score

            project_skills: set = set()
            for p in projects:
                project_skills.update(s.lower() for s in p.get("extracted_skills", []))
                project_skills.update(s.lower() for s in p.get("programming_languages", []) or p.get("programmingLanguages", []))
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

    # ── Training (program electives) ────────────────────────────

    def train(self, training_data: List[Dict[str, Any]], test_size: float = 0.2) -> Dict[str, Any]:
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
            "accuracy": round(acc, 4), "f1_weighted": round(f1w, 4),
            "f1_macro": round(f1_score(y_te, pred, average="macro"), 4),
            "cross_val_mean": round(cv.mean(), 4), "cross_val_std": round(cv.std(), 4),
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
            "n_training_samples": len(X_tr), "n_test_samples": len(X_te),
            "model_type": "RandomForest(200) + KNN(5)",
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ── Training (open electives) ───────────────────────────────

    def train_open_electives(self, training_data: List[Dict[str, Any]], test_size: float = 0.2) -> Dict[str, Any]:
        """Train the open elective recommendation model."""
        if len(training_data) < 20:
            raise ValueError(f"Need ≥20 OE samples, got {len(training_data)}")
        X, y = [], []
        for s in training_data:
            X.append(self.extract_oe_features(s.get("marks", {}), s.get("interests", []), s.get("projects", [])))
            y.append(s["label"])
        X, y = np.array(X), np.array(y)
        y_enc = self.oe_label_enc.fit_transform(y)
        X_tr, X_te, y_tr, y_te = train_test_split(X, y_enc, test_size=test_size, random_state=42, stratify=y_enc)
        X_tr_s = self.oe_scaler.fit_transform(X_tr)
        X_te_s = self.oe_scaler.transform(X_te)
        self.oe_rf_clf = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
        self.oe_rf_clf.fit(X_tr_s, y_tr)
        pred = self.oe_rf_clf.predict(X_te_s)
        acc = accuracy_score(y_te, pred)
        f1w = f1_score(y_te, pred, average="weighted")
        cv = cross_val_score(self.oe_rf_clf, X_tr_s, y_tr, cv=5)
        self.oe_is_trained = True
        self._save()
        report = classification_report(y_te, pred, output_dict=True)
        return {
            "accuracy": round(acc, 4), "f1_weighted": round(f1w, 4),
            "f1_macro": round(f1_score(y_te, pred, average="macro"), 4),
            "cross_val_mean": round(cv.mean(), 4), "cross_val_std": round(cv.std(), 4),
            "per_class": {
                self.oe_label_enc.classes_[i]: {
                    "precision": round(report[str(i)]["precision"], 4),
                    "recall": round(report[str(i)]["recall"], 4),
                    "f1": round(report[str(i)]["f1-score"], 4),
                }
                for i in range(len(self.oe_label_enc.classes_))
                if str(i) in report
            },
            "confusion_matrix": confusion_matrix(y_te, pred).tolist(),
            "n_training_samples": len(X_tr), "n_test_samples": len(X_te),
            "model_type": "RandomForest(200) — Open Electives",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _save(self) -> None:
        try:
            joblib.dump(self.rf_clf, os.path.join(self.MODEL_DIR, "rf_clf.joblib"))
            joblib.dump(self.knn_clf, os.path.join(self.MODEL_DIR, "knn_clf.joblib"))
            joblib.dump(self.scaler, os.path.join(self.MODEL_DIR, "scaler.joblib"))
            joblib.dump(self.label_enc, os.path.join(self.MODEL_DIR, "label_enc.joblib"))
            # Save OE models
            if self.oe_rf_clf is not None:
                joblib.dump(self.oe_rf_clf, os.path.join(self.MODEL_DIR, "oe_rf_clf.joblib"))
                joblib.dump(self.oe_scaler, os.path.join(self.MODEL_DIR, "oe_scaler.joblib"))
                joblib.dump(self.oe_label_enc, os.path.join(self.MODEL_DIR, "oe_label_enc.joblib"))
            meta = {
                "is_trained": True, "timestamp": datetime.utcnow().isoformat(),
                "model_version": "3.0.0", "feature_dimension": FEATURE_DIM,
                "labels": list(self.label_enc.classes_) if hasattr(self.label_enc, 'classes_') else ["ML", "WT", "DWM", "CCS"],
                "oe_is_trained": self.oe_is_trained,
                "oe_labels": list(self.oe_label_enc.classes_) if self.oe_is_trained and hasattr(self.oe_label_enc, 'classes_') else OPEN_ELECTIVE_LABELS,
            }
            with open(os.path.join(self.MODEL_DIR, "meta.json"), "w") as f:
                json.dump(meta, f, indent=2)
            logger.info(f"Models saved to {self.MODEL_DIR}")
        except Exception as e:
            logger.error(f"Save failed: {e}")

    def _try_load(self) -> None:
        try:
            rf_path = os.path.join(self.MODEL_DIR, "rf_clf.joblib")
            if os.path.exists(rf_path):
                self.rf_clf = joblib.load(rf_path)
                self.knn_clf = joblib.load(os.path.join(self.MODEL_DIR, "knn_clf.joblib"))
                self.scaler = joblib.load(os.path.join(self.MODEL_DIR, "scaler.joblib"))
                self.label_enc = joblib.load(os.path.join(self.MODEL_DIR, "label_enc.joblib"))
                self.is_trained = True
                logger.info("Pre-trained PEC models loaded successfully")
            # Load OE models
            oe_rf_path = os.path.join(self.MODEL_DIR, "oe_rf_clf.joblib")
            if os.path.exists(oe_rf_path):
                self.oe_rf_clf = joblib.load(oe_rf_path)
                self.oe_scaler = joblib.load(os.path.join(self.MODEL_DIR, "oe_scaler.joblib"))
                self.oe_label_enc = joblib.load(os.path.join(self.MODEL_DIR, "oe_label_enc.joblib"))
                self.oe_is_trained = True
                logger.info("Pre-trained OEC models loaded successfully")
        except Exception as e:
            logger.info(f"No pre-trained models found: {e}")


# ══════════════════════════════════════════════════════════════════
#  SINGLETON
# ══════════════════════════════════════════════════════════════════

recommendation_engine = CumulativeRecommendationEngine()