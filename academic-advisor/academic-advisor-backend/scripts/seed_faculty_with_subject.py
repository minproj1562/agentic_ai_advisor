"""
Seed Faculty with Proper Subject-to-Faculty Mapping
Based on FCRIT B.Tech IT/CSE Curriculum (Pre-Autonomy + Autonomy)

Each faculty teaches multiple subjects. Every curriculum subject is covered.
Does NOT delete existing faculty — only adds new ones.

Usage:
    python -m scripts.seed_faculty_with_subjects
    python -m scripts.seed_faculty_with_subjects --dry-run
    python -m scripts.seed_faculty_with_subjects --update-existing
    python -m scripts.seed_faculty_with_subjects --show-coverage
"""

import asyncio
import argparse
import os
import sys
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.models.faculty import (
    Faculty, FacultyStatus, UniformFacultyProfile,
    PersonalInfo, AcademicQualifications, CurrentPosition,
    ResearchExpertise, TeachingInfo, FacultyAvailability,
    PublicationSummary, Degree, MeetingSlot
)
from app.config import settings

# ======================================================================
#  COMPLETE SUBJECT → FACULTY MAPPING (FCRIT IT Curriculum)
# ======================================================================
#
#  This maps EVERY subject from app/core/curriculum.py to a faculty member.
#  Faculty listed as "EXISTING" are already in the database and will
#  optionally be updated. Faculty listed as "NEW" will be created.
#
#  Structure:  faculty_key → list of {code, name, semester, type}
# ======================================================================

EXISTING_FACULTY_SUBJECT_UPDATE = {
    # ─── Dr. Rajesh Kumar (EXISTING — yZqludDZiobRnLUwN7Y8tMHK4yq1) ───
    "rajesh.kumar@fcrit.ac.in": {
        "teaching_subjects": [
            "Machine Learning",
            "Artificial Intelligence",
            "Deep Learning",
            "AI Laboratory",
            "Data Analytics Lab",
        ],
        "specializations": [
            "Machine Learning", "Deep Learning", "Computer Vision",
            "Neural Networks", "Artificial Intelligence"
        ],
    },
    # ─── Dr. Priya Sharma (EXISTING — aIR1Kgry9VcM2uOmEQu1doKAM7n2) ───
    "priya.sharma@fcrit.ac.in": {
        "teaching_subjects": [
            "Data Structures and Algorithms",
            "Database Management Systems",
            "DSA Laboratory",
            "DBMS Laboratory",
            "Data Warehouse and Mining",
        ],
        "specializations": [
            "Data Structures", "Database Systems", "Data Mining",
            "Data Science", "Algorithm Design"
        ],
    },
    # ─── Dr. Amit Verma (EXISTING — LZmSBpC1oTQbMwxtFSzBEbARlnB2) ───
    "amit.verma@fcrit.ac.in": {
        "teaching_subjects": [
            "Cryptography & Network Security",
            "Computer Networks",
            "Cryptography Lab",
            "Computer Networks Lab",
        ],
        "specializations": [
            "Cryptography", "Network Security", "Computer Networks",
            "Information Security", "Network Protocols"
        ],
    },
    # ─── Dr. Sneha Patel (EXISTING — ta7458PS7ddcJUYJPIDUCs9VbE43) ───
    "sneha.patel@fcrit.ac.in": {
        "teaching_subjects": [
            "Cloud Computing Services",
            "Software Engineering",
            "Cloud Computing Laboratory",
            "IT Infrastructure Management",
        ],
        "specializations": [
            "Cloud Computing", "Software Engineering", "DevOps",
            "Distributed Systems", "IT Infrastructure"
        ],
    },
    # ─── Dr. Vikram Singh (EXISTING — QbQTk0UA9RNSTAbdDMvBVO0aEeO2) ───
    "vikram.singh@fcrit.ac.in": {
        "teaching_subjects": [
            "Automata Theory / Theory of Computer Science",
            "Design & Analysis of Algorithms",
            "Natural Language Processing",
        ],
        "specializations": [
            "Theory of Computation", "Algorithm Analysis",
            "Natural Language Processing", "Formal Languages",
            "Computational Complexity"
        ],
    },
}

# ======================================================================
#  NEW FACULTY DEFINITIONS
#  Each faculty teaches 3-6 subjects spanning the FCRIT curriculum
# ======================================================================

NEW_FACULTY_DATA = [
    # ─────────────────────────────────────────────────────────────────
    #  1. Dr. Meera Iyer — Mathematics
    # ─────────────────────────────────────────────────────────────────
    {
        "name": "Dr. Meera Iyer",
        "email": "meera.iyer@fcrit.ac.in",
        "department": "Computer Science & Engineering",
        "designation": "Professor",
        "experience": 22,
        "teaching_subjects": [
            "Engineering Mathematics-I",
            "Engineering Mathematics-II",
            "Engineering Mathematics-III",
            "Engineering Mathematics-IV",
            "Discrete Mathematics",
        ],
        "research_primary": [
            "Applied Mathematics", "Numerical Methods", "Optimization Algorithms"
        ],
        "research_secondary": ["Graph Theory", "Mathematical Modelling"],
        "skills": [
            "MATLAB", "Python", "LaTeX", "Mathematica", "R",
            "NumPy", "SciPy", "Statistical Analysis"
        ],
        "degrees": [
            {"degree": "Ph.D.", "field": "Applied Mathematics", "institution": "IIT Bombay", "year": 2000},
            {"degree": "M.Sc.", "field": "Mathematics", "institution": "IIT Bombay", "year": 1996},
            {"degree": "B.Sc.", "field": "Mathematics", "institution": "University of Mumbai", "year": 1994},
        ],
        "publications_count": 45,
        "journal_papers": 28,
        "conference_papers": 17,
        "h_index": 12,
        "citations": 380,
    },
    # ─────────────────────────────────────────────────────────────────
    #  2. Dr. Sanjay Nair — Hardware & Embedded Systems
    # ─────────────────────────────────────────────────────────────────
    {
        "name": "Dr. Sanjay Nair",
        "email": "sanjay.nair@fcrit.ac.in",
        "department": "Computer Science & Engineering",
        "designation": "Associate Professor",
        "experience": 16,
        "teaching_subjects": [
            "Digital Logic & Computer Architecture",
            "Digital Logic & Design",
            "Microcontroller & Embedded Systems",
            "Microcontroller Lab",
            "Internet of Things",
        ],
        "research_primary": [
            "Embedded Systems", "IoT", "VLSI Design"
        ],
        "research_secondary": ["Edge Computing", "Sensor Networks"],
        "skills": [
            "Arduino", "Raspberry Pi", "VHDL", "Verilog", "C",
            "Assembly", "PCB Design", "MQTT", "ESP32"
        ],
        "degrees": [
            {"degree": "Ph.D.", "field": "Electronics & Embedded Systems", "institution": "IIT Madras", "year": 2006},
            {"degree": "M.Tech", "field": "VLSI Design", "institution": "NIT Trichy", "year": 2003},
            {"degree": "B.Tech", "field": "Electronics Engineering", "institution": "NIT Calicut", "year": 2001},
        ],
        "publications_count": 32,
        "journal_papers": 18,
        "conference_papers": 14,
        "h_index": 9,
        "citations": 260,
    },
    # ─────────────────────────────────────────────────────────────────
    #  3. Dr. Kavita Joshi — Data Science & Python
    # ─────────────────────────────────────────────────────────────────
    {
        "name": "Dr. Kavita Joshi",
        "email": "kavita.joshi@fcrit.ac.in",
        "department": "Computer Science & Engineering",
        "designation": "Assistant Professor",
        "experience": 10,
        "teaching_subjects": [
            "Python Programming Lab",
            "Data Science Laboratory",
            "Big Data Analytics",
            "Data Analytics Lab",
            "Data Warehouse and Mining",
        ],
        "research_primary": [
            "Data Science", "Big Data Analytics", "Data Mining"
        ],
        "research_secondary": ["Statistical Learning", "Data Visualization"],
        "skills": [
            "Python", "Pandas", "NumPy", "Scikit-learn", "PySpark",
            "Hadoop", "Tableau", "Power BI", "SQL", "MongoDB"
        ],
        "degrees": [
            {"degree": "Ph.D.", "field": "Data Science", "institution": "IISc Bangalore", "year": 2014},
            {"degree": "M.Tech", "field": "Computer Science", "institution": "BITS Pilani", "year": 2010},
            {"degree": "B.Tech", "field": "Information Technology", "institution": "VIT Vellore", "year": 2008},
        ],
        "publications_count": 22,
        "journal_papers": 12,
        "conference_papers": 10,
        "h_index": 7,
        "citations": 180,
    },
    # ─────────────────────────────────────────────────────────────────
    #  4. Dr. Arjun Deshmukh — Operating Systems & Distributed Systems
    # ─────────────────────────────────────────────────────────────────
    {
        "name": "Dr. Arjun Deshmukh",
        "email": "arjun.deshmukh@fcrit.ac.in",
        "department": "Computer Science & Engineering",
        "designation": "Associate Professor",
        "experience": 14,
        "teaching_subjects": [
            "Operating Systems",
            "Distributed Systems",
            "Edge Computing",
            "Mini Project-1A",
            "Mini Project-2A",
        ],
        "research_primary": [
            "Operating Systems", "Distributed Computing", "Edge Computing"
        ],
        "research_secondary": ["Virtualization", "Container Orchestration"],
        "skills": [
            "Linux", "C", "C++", "Docker", "Kubernetes",
            "Go", "Rust", "System Programming", "Shell Scripting"
        ],
        "degrees": [
            {"degree": "Ph.D.", "field": "Computer Science", "institution": "IIT Delhi", "year": 2008},
            {"degree": "M.Tech", "field": "Systems Engineering", "institution": "IIT Delhi", "year": 2005},
            {"degree": "B.E.", "field": "Computer Engineering", "institution": "University of Pune", "year": 2003},
        ],
        "publications_count": 28,
        "journal_papers": 16,
        "conference_papers": 12,
        "h_index": 8,
        "citations": 220,
    },
    # ─────────────────────────────────────────────────────────────────
    #  5. Dr. Neha Malhotra — Security & Emerging Tech
    # ─────────────────────────────────────────────────────────────────
    {
        "name": "Dr. Neha Malhotra",
        "email": "neha.malhotra@fcrit.ac.in",
        "department": "Computer Science & Engineering",
        "designation": "Assistant Professor",
        "experience": 9,
        "teaching_subjects": [
            "Blockchain Technology",
            "Quantum Computing",
            "Cyber Security",
        ],
        "research_primary": [
            "Blockchain", "Quantum Computing", "Cybersecurity"
        ],
        "research_secondary": ["Post-Quantum Cryptography", "Smart Contracts"],
        "skills": [
            "Solidity", "Python", "Qiskit", "Hyperledger",
            "Ethereum", "Web3.js", "Penetration Testing", "Wireshark"
        ],
        "degrees": [
            {"degree": "Ph.D.", "field": "Information Security", "institution": "IIT Bombay", "year": 2015},
            {"degree": "M.Tech", "field": "Cybersecurity", "institution": "IIT Kanpur", "year": 2011},
            {"degree": "B.Tech", "field": "Computer Science", "institution": "NIT Warangal", "year": 2009},
        ],
        "publications_count": 18,
        "journal_papers": 10,
        "conference_papers": 8,
        "h_index": 6,
        "citations": 140,
    },
    # ─────────────────────────────────────────────────────────────────
    #  6. Dr. Rahul Bose — Mobile, DevOps & Full Stack
    # ─────────────────────────────────────────────────────────────────
    {
        "name": "Dr. Rahul Bose",
        "email": "rahul.bose@fcrit.ac.in",
        "department": "Computer Science & Engineering",
        "designation": "Assistant Professor",
        "experience": 11,
        "teaching_subjects": [
            "Mobile App Development Lab (Flutter)",
            "DevOps Laboratory",
            "AR/VR Technologies",
            "Mobile Computing",
        ],
        "research_primary": [
            "Mobile Computing", "DevOps", "Augmented Reality"
        ],
        "research_secondary": ["Cross-Platform Development", "CI/CD Pipelines"],
        "skills": [
            "Flutter", "Dart", "React Native", "Swift", "Kotlin",
            "Jenkins", "GitHub Actions", "Docker", "AWS", "Unity3D"
        ],
        "degrees": [
            {"degree": "Ph.D.", "field": "Mobile Computing", "institution": "BITS Pilani", "year": 2012},
            {"degree": "M.Tech", "field": "Software Engineering", "institution": "IIIT Hyderabad", "year": 2009},
            {"degree": "B.Tech", "field": "Information Technology", "institution": "VIT Vellore", "year": 2007},
        ],
        "publications_count": 20,
        "journal_papers": 11,
        "conference_papers": 9,
        "h_index": 6,
        "citations": 150,
    },
    # ─────────────────────────────────────────────────────────────────
    #  7. Dr. Anita Kulkarni — Security Testing & Infrastructure
    # ─────────────────────────────────────────────────────────────────
    {
        "name": "Dr. Anita Kulkarni",
        "email": "anita.kulkarni@fcrit.ac.in",
        "department": "Computer Science & Engineering",
        "designation": "Associate Professor",
        "experience": 13,
        "teaching_subjects": [
            "Ethical Hacking",
            "IT Infrastructure Management",
            "Software Testing",
            "Research Methodology",
        ],
        "research_primary": [
            "Ethical Hacking", "Penetration Testing", "IT Governance"
        ],
        "research_secondary": ["Software Quality Assurance", "Risk Management"],
        "skills": [
            "Kali Linux", "Metasploit", "Burp Suite", "Nmap",
            "OWASP", "Selenium", "JMeter", "ITIL", "Python"
        ],
        "degrees": [
            {"degree": "Ph.D.", "field": "Information Security", "institution": "IIT Madras", "year": 2009},
            {"degree": "M.Tech", "field": "Computer Engineering", "institution": "NIT Surathkal", "year": 2006},
            {"degree": "B.E.", "field": "Computer Engineering", "institution": "University of Mumbai", "year": 2004},
        ],
        "publications_count": 25,
        "journal_papers": 14,
        "conference_papers": 11,
        "h_index": 8,
        "citations": 200,
    },
    # ─────────────────────────────────────────────────────────────────
    #  8. Dr. Suresh Menon — Wireless & Networks
    # ─────────────────────────────────────────────────────────────────
    {
        "name": "Dr. Suresh Menon",
        "email": "suresh.menon@fcrit.ac.in",
        "department": "Computer Science & Engineering",
        "designation": "Assistant Professor",
        "experience": 8,
        "teaching_subjects": [
            "Wireless Technology",
            "Wireless Technologies",
            "Professional Communication-II",
        ],
        "research_primary": [
            "Wireless Networks", "5G Technology", "Network Optimization"
        ],
        "research_secondary": ["Software Defined Networking", "Network Slicing"],
        "skills": [
            "NS3", "Wireshark", "Python", "MATLAB", "GNS3",
            "OpenFlow", "Cisco IOS", "TCP/IP", "LTE"
        ],
        "degrees": [
            {"degree": "Ph.D.", "field": "Wireless Communications", "institution": "NIT Trichy", "year": 2016},
            {"degree": "M.Tech", "field": "Communication Engineering", "institution": "NIT Warangal", "year": 2012},
            {"degree": "B.Tech", "field": "Electronics & Telecom", "institution": "VJTI Mumbai", "year": 2010},
        ],
        "publications_count": 15,
        "journal_papers": 8,
        "conference_papers": 7,
        "h_index": 5,
        "citations": 110,
    },
    # ─────────────────────────────────────────────────────────────────
    #  9. Prof. Deepa Krishnan — FY Programming & Basics
    # ─────────────────────────────────────────────────────────────────
    {
        "name": "Prof. Deepa Krishnan",
        "email": "deepa.krishnan@fcrit.ac.in",
        "department": "Computer Science & Engineering",
        "designation": "Assistant Professor",
        "experience": 7,
        "teaching_subjects": [
            "Programming for Problem Solving (C)",
            "Programming Lab (C)",
            "C++ Programming Lab",
            "Workshop Practice",
        ],
        "research_primary": [
            "Programming Education", "Software Development", "Computational Thinking"
        ],
        "research_secondary": ["Educational Technology", "Gamification in Learning"],
        "skills": [
            "C", "C++", "Java", "Python", "Git",
            "Visual Studio", "GCC", "Debugging", "Linux"
        ],
        "degrees": [
            {"degree": "M.Tech", "field": "Computer Science", "institution": "University of Mumbai", "year": 2016},
            {"degree": "B.E.", "field": "Computer Engineering", "institution": "University of Mumbai", "year": 2014},
        ],
        "publications_count": 8,
        "journal_papers": 4,
        "conference_papers": 4,
        "h_index": 3,
        "citations": 45,
    },
    # ─────────────────────────────────────────────────────────────────
    #  10. Prof. Manoj Pillai — Projects & Internships
    # ─────────────────────────────────────────────────────────────────
    {
        "name": "Prof. Manoj Pillai",
        "email": "manoj.pillai@fcrit.ac.in",
        "department": "Computer Science & Engineering",
        "designation": "Assistant Professor",
        "experience": 6,
        "teaching_subjects": [
            "Mini Project-2B",
            "Major Project-A",
            "Major Project-B",
            "Internship",
        ],
        "research_primary": [
            "Project Management", "Industry-Academia Collaboration", "Software Engineering"
        ],
        "research_secondary": ["Agile Methodologies", "Startup Ecosystems"],
        "skills": [
            "Python", "JavaScript", "React", "Node.js", "AWS",
            "Jira", "Agile", "Scrum", "Git", "Docker"
        ],
        "degrees": [
            {"degree": "M.Tech", "field": "Software Engineering", "institution": "BITS Pilani", "year": 2017},
            {"degree": "B.Tech", "field": "Computer Science", "institution": "VIT Vellore", "year": 2015},
        ],
        "publications_count": 6,
        "journal_papers": 3,
        "conference_papers": 3,
        "h_index": 2,
        "citations": 30,
    },
]


# ======================================================================
#  COMPLETE CURRICULUM COVERAGE MAP
#  Maps every subject code → faculty email for verification
# ======================================================================

SUBJECT_COVERAGE = {
    # ── Pre-Autonomy Sem 1 ──
    "PHY101":   "meera.iyer@fcrit.ac.in",       # Physics → Math faculty (cross-dept placeholder)
    "CHEM101":  "meera.iyer@fcrit.ac.in",       # Chemistry → placeholder
    "MATH101":  "meera.iyer@fcrit.ac.in",       # Engineering Mathematics-I
    "MECH101":  "meera.iyer@fcrit.ac.in",       # Engineering Mechanics → placeholder
    "BEE101":   "sanjay.nair@fcrit.ac.in",      # Basic Electronic Engineering
    "WS101":    "deepa.krishnan@fcrit.ac.in",   # Workshop Practice

    # ── Pre-Autonomy Sem 2 ──
    "PHY102":   "meera.iyer@fcrit.ac.in",
    "CHEM102":  "meera.iyer@fcrit.ac.in",
    "MATH102":  "meera.iyer@fcrit.ac.in",       # Engineering Mathematics-II
    "CPP102":   "deepa.krishnan@fcrit.ac.in",   # C++ Programming
    "ACAD102":  "deepa.krishnan@fcrit.ac.in",
    "EG102":    "deepa.krishnan@fcrit.ac.in",
    "PCE102":   "suresh.menon@fcrit.ac.in",     # Professional Communication

    # ── Pre-Autonomy Sem 3 ──
    "MATH301":  "meera.iyer@fcrit.ac.in",       # Engineering Mathematics-III
    "DSA301":   "priya.sharma@fcrit.ac.in",     # Data Structures and Algorithms
    "DBMS301":  "priya.sharma@fcrit.ac.in",     # Database Management Systems
    "DLDA301":  "sanjay.nair@fcrit.ac.in",      # Digital Logic & Design
    "PYTHON301":"kavita.joshi@fcrit.ac.in",     # Python Programming
    "DSAL301":  "priya.sharma@fcrit.ac.in",     # DSA Laboratory

    # ── Pre-Autonomy Sem 4 ──
    "MATH401":  "meera.iyer@fcrit.ac.in",       # Engineering Mathematics-IV
    "MES401":   "sanjay.nair@fcrit.ac.in",      # Microcontroller & Embedded Systems
    "OS401":    "arjun.deshmukh@fcrit.ac.in",   # Operating Systems
    "CN401":    "amit.verma@fcrit.ac.in",       # Computer Networks
    "SE401":    "sneha.patel@fcrit.ac.in",      # Software Engineering
    "MESL401":  "sanjay.nair@fcrit.ac.in",      # Microcontroller Lab
    "CNL401":   "amit.verma@fcrit.ac.in",       # Computer Networks Lab

    # ── Autonomy Sem 1 (2025+ batches) ──
    "BSC101":   "meera.iyer@fcrit.ac.in",
    "BSC102":   "meera.iyer@fcrit.ac.in",
    "BSC103":   "meera.iyer@fcrit.ac.in",
    "ESC101":   "deepa.krishnan@fcrit.ac.in",   # Programming (C)
    "ESC102":   "meera.iyer@fcrit.ac.in",
    "LBC101":   "deepa.krishnan@fcrit.ac.in",   # Programming Lab
    "LBC102":   "deepa.krishnan@fcrit.ac.in",   # Workshop
    "AEC101":   "suresh.menon@fcrit.ac.in",

    # ── Autonomy Sem 2 ──
    "BSC201":   "meera.iyer@fcrit.ac.in",       # Engineering Mathematics-II
    "BSC202":   "meera.iyer@fcrit.ac.in",       # Discrete Mathematics
    "ESC201":   "sanjay.nair@fcrit.ac.in",
    "ESC202":   "sanjay.nair@fcrit.ac.in",
    "LBC201":   "deepa.krishnan@fcrit.ac.in",
    "LBC202":   "deepa.krishnan@fcrit.ac.in",   # C++ Lab
    "LBC203":   "sanjay.nair@fcrit.ac.in",
    "AEC201":   "suresh.menon@fcrit.ac.in",

    # ── Autonomy Sem 3 ──
    "BSC301":   "meera.iyer@fcrit.ac.in",       # Engineering Mathematics-III
    "ITPCC301": "priya.sharma@fcrit.ac.in",     # DSA
    "ITPCC302": "priya.sharma@fcrit.ac.in",     # DBMS
    "ITPCC303": "sanjay.nair@fcrit.ac.in",      # Digital Logic & Computer Architecture
    "ITSBL301": "kavita.joshi@fcrit.ac.in",     # Python Programming Lab
    "ITLBC301": "priya.sharma@fcrit.ac.in",     # DSA Lab
    "ITLBC302": "priya.sharma@fcrit.ac.in",     # DBMS Lab

    # ── Autonomy Sem 4 ──
    "BSC401":   "meera.iyer@fcrit.ac.in",       # Engineering Mathematics-IV
    "ITPCC401": "arjun.deshmukh@fcrit.ac.in",   # Operating Systems
    "ITPCC402": "amit.verma@fcrit.ac.in",       # Computer Networks
    "ITPCC403": "sneha.patel@fcrit.ac.in",      # Software Engineering
    "ITPCC404": "sanjay.nair@fcrit.ac.in",      # Microcontroller & Embedded Systems
    "ITLBC401": "sanjay.nair@fcrit.ac.in",      # Microcontroller Lab
    "ITLBC402": "amit.verma@fcrit.ac.in",       # Computer Networks Lab
    "MNP4A":    "arjun.deshmukh@fcrit.ac.in",   # Mini Project-1A

    # ── Autonomy Sem 5 ──
    "ITPCC509": "vikram.singh@fcrit.ac.in",     # Automata Theory
    "ITPCC501": "vikram.singh@fcrit.ac.in",     # Design & Analysis of Algorithms
    "ITPEC501": "rajesh.kumar@fcrit.ac.in",     # PE-I placeholder (ML by default)
    "ITLBC506": "sneha.patel@fcrit.ac.in",      # Cloud Computing Laboratory
    "ITLBC507": "rahul.bose@fcrit.ac.in",       # Mobile App Dev Lab
    "MNP5A":    "arjun.deshmukh@fcrit.ac.in",   # Mini Project-2A
    "AEC502":   "suresh.menon@fcrit.ac.in",     # Professional Communication-II

    # PE-I Elective Options
    "ITPEC5012":"rajesh.kumar@fcrit.ac.in",     # Machine Learning
    "ITPEC5013":"suresh.menon@fcrit.ac.in",     # Wireless Technology
    "ITPEC5014":"kavita.joshi@fcrit.ac.in",     # Data Warehouse and Mining
    "ITPEC5015":"sneha.patel@fcrit.ac.in",      # Cloud Computing Services

    # ── Autonomy Sem 6 ──
    "ITPCC611": "amit.verma@fcrit.ac.in",       # Cryptography & Network Security
    "ITPEC602": "sneha.patel@fcrit.ac.in",      # PE-II placeholder
    "ITLBC608": "amit.verma@fcrit.ac.in",       # Cryptography Lab
    "ITLBC609": "kavita.joshi@fcrit.ac.in",     # Data Science Laboratory
    "ITSBL603": "rahul.bose@fcrit.ac.in",       # DevOps Laboratory
    "MNP6B":    "manoj.pillai@fcrit.ac.in",     # Mini Project-2B
    "RM601":    "anita.kulkarni@fcrit.ac.in",   # Research Methodology

    # PE-II Elective Options
    "ITPEC6021":"anita.kulkarni@fcrit.ac.in",   # IT Infrastructure Management
    "ITPEC6022":"rajesh.kumar@fcrit.ac.in",     # Machine Learning (if not in Sem 5)
    "ITPEC6023":"suresh.menon@fcrit.ac.in",     # Wireless Technologies
    "ITPEC6024":"kavita.joshi@fcrit.ac.in",     # Big Data Analytics

    # ── Autonomy Sem 7 ──
    "ITPCC710": "rajesh.kumar@fcrit.ac.in",     # Artificial Intelligence
    "ITPEC703": "vikram.singh@fcrit.ac.in",     # PE-III placeholder
    "ITPEC704": "sanjay.nair@fcrit.ac.in",      # PE-IV placeholder
    "OEC701":   "anita.kulkarni@fcrit.ac.in",   # Open Elective-I placeholder
    "ITLBC711": "rajesh.kumar@fcrit.ac.in",     # AI Laboratory
    "ITLBC712": "kavita.joshi@fcrit.ac.in",     # Data Analytics Lab
    "MJP7A":    "manoj.pillai@fcrit.ac.in",     # Major Project-A

    # PE-III Elective Options
    "ITPEC7031":"neha.malhotra@fcrit.ac.in",    # Quantum Computing
    "ITPEC7032":"anita.kulkarni@fcrit.ac.in",   # Ethical Hacking
    "ITPEC7033":"vikram.singh@fcrit.ac.in",     # Natural Language Processing
    "ITPEC7034":"neha.malhotra@fcrit.ac.in",    # Blockchain Technology

    # PE-IV Elective Options
    "ITPEC7041":"rahul.bose@fcrit.ac.in",       # AR/VR Technologies
    "ITPEC7042":"sanjay.nair@fcrit.ac.in",      # Internet of Things
    "ITPEC7043":"arjun.deshmukh@fcrit.ac.in",   # Edge Computing (via Distributed Sys)
    "ITPEC7044":"anita.kulkarni@fcrit.ac.in",   # Software Testing

    # ── Autonomy Sem 8 ──
    "ITPEC805": "rajesh.kumar@fcrit.ac.in",     # PE-V placeholder
    "OEC802":   "anita.kulkarni@fcrit.ac.in",   # Open Elective-II placeholder
    "MJP8B":    "manoj.pillai@fcrit.ac.in",     # Major Project-B
    "INT801":   "manoj.pillai@fcrit.ac.in",     # Internship

    # PE-V Elective Options
    "ITPEC8051":"rajesh.kumar@fcrit.ac.in",     # Deep Learning
    "ITPEC8052":"neha.malhotra@fcrit.ac.in",    # Cyber Security
    "ITPEC8053":"arjun.deshmukh@fcrit.ac.in",   # Distributed Systems
    "ITPEC8054":"rahul.bose@fcrit.ac.in",       # Mobile Computing
}


# ======================================================================
#  HELPER FUNCTIONS
# ======================================================================

def build_uniform_profile(data: dict) -> UniformFacultyProfile:
    """Build a complete UniformFacultyProfile from faculty data dict."""

    name = data["name"]
    email = data["email"]
    department = data["department"]
    designation = data["designation"]
    experience = data["experience"]
    idx = NEW_FACULTY_DATA.index(data) if data in NEW_FACULTY_DATA else 0

    degrees = [
        Degree(
            degree=d["degree"],
            field=d["field"],
            institution=d["institution"],
            year=d.get("year")
        )
        for d in data.get("degrees", [])
    ]

    top_degree = degrees[0] if degrees else None

    return UniformFacultyProfile(
        personal_info=PersonalInfo(
            name=name,
            email=email,
            phone=f"+91 98765{random.randint(10000, 99999)}",
            photo_url=None,
        ),
        academic_qualifications=AcademicQualifications(
            highest_degree=top_degree.degree if top_degree else "Ph.D.",
            specialization=data["research_primary"][0] if data["research_primary"] else department,
            university=top_degree.institution if top_degree else "Unknown",
            graduation_year=top_degree.year if top_degree else None,
            all_degrees=degrees,
        ),
        current_position=CurrentPosition(
            designation=designation,
            department=department,
            institution="Fr. C. Rodrigues Institute of Technology",
            years_of_experience=experience,
            joining_year=datetime.now().year - experience,
        ),
        research_expertise=ResearchExpertise(
            primary_areas=data.get("research_primary", []),
            secondary_interests=data.get("research_secondary", []),
            keywords=data.get("skills", [])[:6],
        ),
        teaching=TeachingInfo(
            current_subjects=data["teaching_subjects"],
            past_subjects=[],
            preferred_areas=data.get("research_primary", [])[:2],
        ),
        availability=FacultyAvailability(
            office_location=f"Room {310 + idx * 5}, CSE Building",
            office_hours="Mon-Wed 10:00 AM - 12:00 PM",
            available_slots=[
                MeetingSlot(
                    day="Monday",
                    start_time="10:00",
                    end_time="11:00",
                    venue=f"Room {310 + idx * 5}",
                    is_available=True,
                ),
                MeetingSlot(
                    day="Wednesday",
                    start_time="14:00",
                    end_time="15:00",
                    venue=f"Room {310 + idx * 5}",
                    is_available=True,
                ),
                MeetingSlot(
                    day="Friday",
                    start_time="11:00",
                    end_time="12:00",
                    venue=f"Room {310 + idx * 5}",
                    is_available=True,
                ),
            ],
            preferred_meeting_duration=30,
        ),
        publications=PublicationSummary(
            total_count=data.get("publications_count", 0),
            journal_papers=data.get("journal_papers", 0),
            conference_papers=data.get("conference_papers", 0),
            notable_works=[
                f"A Novel Approach to {data['research_primary'][0]}" if data.get("research_primary") else "",
                f"Survey on {data['research_primary'][1]} Techniques" if len(data.get("research_primary", [])) > 1 else "",
            ],
            h_index=data.get("h_index"),
            citations=data.get("citations"),
        ),
        others={
            "certifications": [],
            "languages": ["English", "Hindi", "Marathi"],
            "professional_memberships": random.sample(["IEEE", "ACM", "CSI", "ISTE"], 2),
        },
        profile_completeness=random.randint(88, 100),
        last_updated=datetime.utcnow(),
    )


def build_faculty_document(data: dict, index: int) -> Faculty:
    """Build a Faculty document from data dict."""

    profile = build_uniform_profile(data)

    return Faculty(
        user_id=f"faculty_new_{index + 1:03d}",   # Synthetic — sync script replaces with Firebase UID
        name=data["name"],
        email=data["email"],
        department=data["department"],
        designation=data["designation"],
        phone=profile.personal_info.phone,
        office_location=profile.availability.office_location,
        years_of_experience=data["experience"],
        teaching_subjects=data["teaching_subjects"],
        specializations=data.get("research_primary", []),
        skills=data.get("skills", []),
        uniform_profile=profile,
        profile_setup_complete=True,
        status=FacultyStatus.ACTIVE,
        mentee_ids=[],
        max_mentees=15,
        available_slots=profile.availability.available_slots,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def print_coverage_report():
    """Print which faculty teaches which subjects across the curriculum."""

    from app.core.curriculum import (
        PRE_AUTONOMY_CURRICULUM, AUTONOMY_CURRICULUM, ELECTIVE_OPTIONS
    )

    print("\n" + "=" * 80)
    print("📚 SUBJECT → FACULTY COVERAGE REPORT")
    print("=" * 80)

    # Build reverse map: faculty_email → list of subject names
    faculty_subjects: Dict[str, list] = {}
    for code, email in SUBJECT_COVERAGE.items():
        faculty_subjects.setdefault(email, []).append(code)

    # All existing + new faculty emails
    all_faculty_emails = set(EXISTING_FACULTY_SUBJECT_UPDATE.keys())
    for fac in NEW_FACULTY_DATA:
        all_faculty_emails.add(fac["email"])

    print(f"\n👨‍🏫 Faculty count: {len(all_faculty_emails)}")
    print(f"📖 Subjects mapped: {len(SUBJECT_COVERAGE)}")

    for email in sorted(all_faculty_emails):
        codes = faculty_subjects.get(email, [])
        # Find name
        name = email
        for fac in NEW_FACULTY_DATA:
            if fac["email"] == email:
                name = fac["name"]
                break
        for em, data in EXISTING_FACULTY_SUBJECT_UPDATE.items():
            if em == email:
                name = f"[EXISTING] {email.split('@')[0].replace('.', ' ').title()}"
                break

        print(f"\n  {name} ({email})")
        print(f"    Subjects ({len(codes)}): {', '.join(codes)}")

    # Check for uncovered subjects
    all_curriculum_codes = set()
    for sem_subjects in PRE_AUTONOMY_CURRICULUM.values():
        for s in sem_subjects:
            all_curriculum_codes.add(s.subject_code)
    for sem_subjects in AUTONOMY_CURRICULUM.values():
        for s in sem_subjects:
            all_curriculum_codes.add(s.subject_code)
    for group_options in ELECTIVE_OPTIONS.values():
        for opt in group_options:
            all_curriculum_codes.add(opt["code"])

    covered = set(SUBJECT_COVERAGE.keys())
    uncovered = all_curriculum_codes - covered
    if uncovered:
        print(f"\n  ⚠️  Uncovered subject codes: {', '.join(sorted(uncovered))}")
    else:
        print(f"\n  ✅ All {len(all_curriculum_codes)} curriculum subjects are covered!")


# ======================================================================
#  MAIN SEED FUNCTION
# ======================================================================

async def seed_faculty(
    dry_run: bool = False,
    update_existing: bool = False,
    show_coverage: bool = False,
):
    print("\n" + "=" * 70)
    print("🌱 Seed Faculty with Subject Mapping")
    print("=" * 70)

    if dry_run:
        print("⚠️  DRY RUN — No changes will be made\n")

    if show_coverage:
        print_coverage_report()
        if dry_run:
            return

    # Connect
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.MONGODB_DATABASE],
        document_models=[Faculty],
    )
    print(f"✅ Connected to MongoDB: {settings.MONGODB_DATABASE}\n")

    existing_faculty = await Faculty.find().to_list()
    existing_emails = {f.email for f in existing_faculty}
    existing_uids = {f.user_id for f in existing_faculty}

    print(f"📋 Existing faculty in DB: {len(existing_faculty)}")
    for f in existing_faculty:
        print(f"   • {f.name} ({f.email}) — UID: {f.user_id}")

    # ── Step 1: Optionally update existing faculty teaching_subjects ──
    if update_existing:
        print(f"\n🔄 Updating existing faculty teaching_subjects...")
        updated = 0
        for fac in existing_faculty:
            if fac.email in EXISTING_FACULTY_SUBJECT_UPDATE:
                update_data = EXISTING_FACULTY_SUBJECT_UPDATE[fac.email]
                old_subjects = fac.teaching_subjects
                new_subjects = update_data["teaching_subjects"]
                new_specializations = update_data.get("specializations", fac.specializations)

                if set(old_subjects) != set(new_subjects):
                    print(f"   📝 {fac.name}:")
                    print(f"      Old: {old_subjects}")
                    print(f"      New: {new_subjects}")

                    if not dry_run:
                        fac.teaching_subjects = new_subjects
                        fac.specializations = new_specializations
                        if fac.uniform_profile and fac.uniform_profile.teaching:
                            fac.uniform_profile.teaching.current_subjects = new_subjects
                        fac.updated_at = datetime.utcnow()
                        await fac.save()
                    updated += 1

        print(f"   ✅ Updated {updated} existing faculty" + (" (dry run)" if dry_run else ""))

    # ── Step 2: Create new faculty ──
    print(f"\n➕ Creating new faculty...")
    created = 0
    skipped = 0

    for i, fac_data in enumerate(NEW_FACULTY_DATA):
        email = fac_data["email"]
        name = fac_data["name"]

        if email in existing_emails:
            print(f"   ⏭️  {name} ({email}) — already exists, skipping")
            skipped += 1
            continue

        faculty_doc = build_faculty_document(fac_data, i)

        # Ensure user_id is unique
        while faculty_doc.user_id in existing_uids:
            faculty_doc.user_id = f"faculty_new_{random.randint(100,999):03d}"

        print(f"   ✅ {name}")
        print(f"      Email: {email}")
        print(f"      Subjects: {', '.join(fac_data['teaching_subjects'])}")
        print(f"      user_id: {faculty_doc.user_id}")

        if not dry_run:
            await faculty_doc.insert()
            existing_uids.add(faculty_doc.user_id)
        existing_emails.add(email)
        created += 1

    # ── Summary ──
    print("\n" + "=" * 70)
    print("📊 SEED SUMMARY")
    print("=" * 70)
    print(f"  Created: {created}" + (" (dry run)" if dry_run else ""))
    print(f"  Skipped (already exist): {skipped}")
    if update_existing:
        print(f"  Existing updated: yes")
    print()

    # Show final state
    if not dry_run:
        final_faculty = await Faculty.find().to_list()
        print(f"📋 Total faculty now: {len(final_faculty)}")
        for f in final_faculty:
            subj_count = len(f.teaching_subjects)
            print(f"   • {f.name} — {subj_count} subjects — UID: {f.user_id}")
    
    # Print coverage
    print_coverage_report()

    # Next steps
    print("\n" + "=" * 70)
    print("📌 NEXT STEPS")
    print("=" * 70)
    print("  1. Run Firebase sync to create accounts for new faculty:")
    print("     python -m scripts.sync_faculty_to_firebase")
    print()
    print("  2. New faculty login credentials will be:")
    print("     Password: Faculty@FCRIT2024")
    print("     (Change on first login)")
    print()

    client.close()
    print("✅ Done!")


def main():
    parser = argparse.ArgumentParser(
        description="Seed faculty with proper subject-to-faculty mapping"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without making them"
    )
    parser.add_argument(
        "--update-existing", action="store_true",
        help="Also update teaching_subjects on existing faculty"
    )
    parser.add_argument(
        "--show-coverage", action="store_true",
        help="Print subject coverage report"
    )
    args = parser.parse_args()

    asyncio.run(seed_faculty(
        dry_run=args.dry_run,
        update_existing=args.update_existing,
        show_coverage=args.show_coverage,
    ))


if __name__ == "__main__":
    main()