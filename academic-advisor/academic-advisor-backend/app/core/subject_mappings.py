# app/core/subject_mappings.py
"""
Comprehensive Subject-Requirement Mappings for Academic Weakness Analysis

This module defines the relationships between:
- Student Interests → Required foundational subjects
- Electives → Prerequisites with importance levels
- Honours/Minors → Required subjects for eligibility

All mappings include:
- Subject name
- Required minimum score (threshold)
- Importance weight (0.0 - 1.0)
- Source tracking (which interest/elective/honours needs it)
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from app.core.curriculum import (
    PRE_AUTONOMY_CURRICULUM, 
    AUTONOMY_CURRICULUM, 
    ELECTIVE_OPTIONS,
    get_semester_subjects
)


class ImportanceLevel(str, Enum):
    """Importance levels for prerequisites"""
    CRITICAL = "critical"      # Must have - blocks progress
    HIGH = "high"              # Very important - significantly impacts success
    MEDIUM = "medium"          # Important - helps but not essential
    LOW = "low"                # Nice to have - marginal benefit


class RequirementSource(str, Enum):
    """Source of the requirement"""
    INTEREST = "interest"
    ELECTIVE = "elective"
    HONOURS = "honours"
    MINOR = "minor"


@dataclass
class SubjectRequirement:
    """A single subject requirement"""
    subject_name: str
    subject_code: Optional[str] = None
    min_score: float = 60.0              # Minimum required score
    importance: ImportanceLevel = ImportanceLevel.MEDIUM
    weight: float = 0.5                   # 0.0 to 1.0
    source_type: RequirementSource = RequirementSource.INTEREST
    source_name: str = ""                 # Which interest/elective this is for
    description: str = ""
    alternative_subjects: List[str] = field(default_factory=list)


@dataclass 
class AcademicTarget:
    """Complete academic target profile for a student"""
    student_id: str
    interests: List[str] = field(default_factory=list)
    electives: List[str] = field(default_factory=list)
    honours_minors: List[str] = field(default_factory=list)
    all_requirements: List[SubjectRequirement] = field(default_factory=list)
    merged_requirements: Dict[str, SubjectRequirement] = field(default_factory=dict)
    

# ============== INTEREST TO SUBJECT MAPPINGS ==============
# These define what foundational subjects are needed for each interest area

INTEREST_REQUIREMENTS: Dict[str, List[SubjectRequirement]] = {
    "Machine Learning": [
        SubjectRequirement(
            subject_name="Engineering Mathematics-III",
            subject_code="MATH301",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=1.0,
            description="Linear algebra, calculus essential for ML algorithms"
        ),
        SubjectRequirement(
            subject_name="Engineering Mathematics-IV",
            subject_code="MATH401",
            min_score=65,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            description="Probability and statistics for ML"
        ),
        SubjectRequirement(
            subject_name="Python Programming",
            subject_code="PYTHON301",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            description="Primary language for ML implementation"
        ),
        SubjectRequirement(
            subject_name="Data Structures and Algorithms",
            subject_code="DSA301",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            description="Algorithm optimization for ML"
        ),
        SubjectRequirement(
            subject_name="Database Management Systems",
            subject_code="DBMS301",
            min_score=60,
            importance=ImportanceLevel.MEDIUM,
            weight=0.7,
            description="Data handling and storage"
        ),
    ],
    
    "Artificial Intelligence": [
        SubjectRequirement(
            subject_name="Engineering Mathematics-III",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=1.0,
            description="Mathematical foundations for AI"
        ),
        SubjectRequirement(
            subject_name="Data Structures and Algorithms",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            description="Search algorithms, graph traversal"
        ),
        SubjectRequirement(
            subject_name="Design & Analysis of Algorithms",
            subject_code="ITPCC501",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.9,
            description="Algorithm complexity analysis"
        ),
        SubjectRequirement(
            subject_name="Python Programming",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            description="AI implementation language"
        ),
        SubjectRequirement(
            subject_name="Automata Theory",
            subject_code="ITPCC509",
            min_score=60,
            importance=ImportanceLevel.MEDIUM,
            weight=0.7,
            description="Formal languages and computation"
        ),
    ],
    
    "Data Science": [
        SubjectRequirement(
            subject_name="Engineering Mathematics-IV",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=1.0,
            description="Statistics and probability"
        ),
        SubjectRequirement(
            subject_name="Python Programming",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            description="Primary data science tool"
        ),
        SubjectRequirement(
            subject_name="Database Management Systems",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.9,
            description="Data storage and retrieval"
        ),
        SubjectRequirement(
            subject_name="Engineering Mathematics-III",
            min_score=60,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            description="Linear algebra for data manipulation"
        ),
    ],
    
    "Web Development": [
        SubjectRequirement(
            subject_name="Database Management Systems",
            min_score=65,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            description="Backend data management"
        ),
        SubjectRequirement(
            subject_name="Computer Networks",
            subject_code="CN401",
            min_score=60,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            description="Understanding HTTP, APIs"
        ),
        SubjectRequirement(
            subject_name="Software Engineering",
            subject_code="SE401",
            min_score=60,
            importance=ImportanceLevel.MEDIUM,
            weight=0.7,
            description="Development methodologies"
        ),
        SubjectRequirement(
            subject_name="Python Programming",
            min_score=60,
            importance=ImportanceLevel.MEDIUM,
            weight=0.7,
            description="Backend development"
        ),
    ],
    
    "Cloud Computing": [
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=1.0,
            description="Networking fundamentals"
        ),
        SubjectRequirement(
            subject_name="Operating Systems",
            subject_code="OS401",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            description="Virtualization, containers"
        ),
        SubjectRequirement(
            subject_name="Database Management Systems",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            description="Cloud databases"
        ),
        SubjectRequirement(
            subject_name="Cryptography & Network Security",
            subject_code="ITPCC611",
            min_score=60,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            description="Cloud security"
        ),
    ],
    
    "Cybersecurity": [
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=75,
            importance=ImportanceLevel.CRITICAL,
            weight=1.0,
            description="Network security fundamentals"
        ),
        SubjectRequirement(
            subject_name="Operating Systems",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            description="System security"
        ),
        SubjectRequirement(
            subject_name="Cryptography & Network Security",
            min_score=75,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            description="Core security concepts"
        ),
        SubjectRequirement(
            subject_name="Data Structures and Algorithms",
            min_score=60,
            importance=ImportanceLevel.MEDIUM,
            weight=0.7,
            description="Security algorithm implementation"
        ),
    ],
    
    "IoT": [
        SubjectRequirement(
            subject_name="Microcontroller & Embedded Systems",
            subject_code="MES401",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=1.0,
            description="IoT device programming"
        ),
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=65,
            importance=ImportanceLevel.CRITICAL,
            weight=0.9,
            description="IoT communication protocols"
        ),
        SubjectRequirement(
            subject_name="Digital Logic & Design",
            subject_code="DLDA301",
            min_score=60,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            description="Hardware fundamentals"
        ),
        SubjectRequirement(
            subject_name="Python Programming",
            min_score=60,
            importance=ImportanceLevel.MEDIUM,
            weight=0.7,
            description="IoT scripting"
        ),
    ],
    
    "DevOps": [
        SubjectRequirement(
            subject_name="Operating Systems",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=1.0,
            description="Linux, process management"
        ),
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.9,
            description="Networking for deployment"
        ),
        SubjectRequirement(
            subject_name="Software Engineering",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            description="CI/CD concepts"
        ),
        SubjectRequirement(
            subject_name="Python Programming",
            min_score=60,
            importance=ImportanceLevel.MEDIUM,
            weight=0.75,
            description="Automation scripting"
        ),
    ],
    
    "Mobile Development": [
        SubjectRequirement(
            subject_name="Data Structures and Algorithms",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            description="Efficient mobile apps"
        ),
        SubjectRequirement(
            subject_name="Database Management Systems",
            min_score=60,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            description="Local and remote data"
        ),
        SubjectRequirement(
            subject_name="Software Engineering",
            min_score=60,
            importance=ImportanceLevel.MEDIUM,
            weight=0.7,
            description="App architecture"
        ),
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=55,
            importance=ImportanceLevel.MEDIUM,
            weight=0.65,
            description="API integration"
        ),
    ],
    
    "Blockchain": [
        SubjectRequirement(
            subject_name="Cryptography & Network Security",
            min_score=75,
            importance=ImportanceLevel.CRITICAL,
            weight=1.0,
            description="Cryptographic foundations"
        ),
        SubjectRequirement(
            subject_name="Data Structures and Algorithms",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            description="Merkle trees, hash functions"
        ),
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            description="Distributed systems"
        ),
        SubjectRequirement(
            subject_name="Database Management Systems",
            min_score=60,
            importance=ImportanceLevel.MEDIUM,
            weight=0.7,
            description="Distributed ledger concepts"
        ),
    ],
}


# ============== ELECTIVE PREREQUISITES ==============
# These define what subjects must be strong before taking each elective

ELECTIVE_REQUIREMENTS: Dict[str, List[SubjectRequirement]] = {
    # Program Elective 1 Options (Semester 5)
    "Machine Learning": [
        SubjectRequirement(
            subject_name="Python Programming",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="Machine Learning"
        ),
        SubjectRequirement(
            subject_name="Engineering Mathematics-III",
            min_score=65,
            importance=ImportanceLevel.CRITICAL,
            weight=0.9,
            source_type=RequirementSource.ELECTIVE,
            source_name="Machine Learning"
        ),
        SubjectRequirement(
            subject_name="Engineering Mathematics-IV",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            source_type=RequirementSource.ELECTIVE,
            source_name="Machine Learning"
        ),
        SubjectRequirement(
            subject_name="Data Structures and Algorithms",
            min_score=60,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            source_type=RequirementSource.ELECTIVE,
            source_name="Machine Learning"
        ),
    ],
    
    "ML": [  # Alias
        SubjectRequirement(
            subject_name="Python Programming",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="ML"
        ),
        SubjectRequirement(
            subject_name="Engineering Mathematics-III",
            min_score=65,
            importance=ImportanceLevel.CRITICAL,
            weight=0.9,
            source_type=RequirementSource.ELECTIVE,
            source_name="ML"
        ),
        SubjectRequirement(
            subject_name="Data Structures and Algorithms",
            min_score=60,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            source_type=RequirementSource.ELECTIVE,
            source_name="ML"
        ),
    ],
    
    "Wireless Technology": [
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="Wireless Technology"
        ),
        SubjectRequirement(
            subject_name="Microcontroller & Embedded Systems",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            source_type=RequirementSource.ELECTIVE,
            source_name="Wireless Technology"
        ),
        SubjectRequirement(
            subject_name="Digital Logic & Design",
            min_score=60,
            importance=ImportanceLevel.MEDIUM,
            weight=0.7,
            source_type=RequirementSource.ELECTIVE,
            source_name="Wireless Technology"
        ),
    ],
    
    "WT": [  # Alias for Wireless Technology
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="WT"
        ),
        SubjectRequirement(
            subject_name="Microcontroller & Embedded Systems",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            source_type=RequirementSource.ELECTIVE,
            source_name="WT"
        ),
    ],
    
    "Data Warehouse and Mining": [
        SubjectRequirement(
            subject_name="Database Management Systems",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="Data Warehouse and Mining"
        ),
        SubjectRequirement(
            subject_name="Data Structures and Algorithms",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            source_type=RequirementSource.ELECTIVE,
            source_name="Data Warehouse and Mining"
        ),
        SubjectRequirement(
            subject_name="Python Programming",
            min_score=60,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            source_type=RequirementSource.ELECTIVE,
            source_name="Data Warehouse and Mining"
        ),
    ],
    
    "DWM": [  # Alias
        SubjectRequirement(
            subject_name="Database Management Systems",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="DWM"
        ),
        SubjectRequirement(
            subject_name="Data Structures and Algorithms",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            source_type=RequirementSource.ELECTIVE,
            source_name="DWM"
        ),
    ],
    
    "Cloud Computing Services": [
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="Cloud Computing Services"
        ),
        SubjectRequirement(
            subject_name="Operating Systems",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.9,
            source_type=RequirementSource.ELECTIVE,
            source_name="Cloud Computing Services"
        ),
        SubjectRequirement(
            subject_name="Database Management Systems",
            min_score=60,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            source_type=RequirementSource.ELECTIVE,
            source_name="Cloud Computing Services"
        ),
    ],
    
    "CCS": [  # Alias
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="CCS"
        ),
        SubjectRequirement(
            subject_name="Operating Systems",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.9,
            source_type=RequirementSource.ELECTIVE,
            source_name="CCS"
        ),
    ],
    
    # Program Elective 2 Options (Semester 6)
    "Big Data Analytics": [
        SubjectRequirement(
            subject_name="Database Management Systems",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="Big Data Analytics"
        ),
        SubjectRequirement(
            subject_name="Python Programming",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            source_type=RequirementSource.ELECTIVE,
            source_name="Big Data Analytics"
        ),
        SubjectRequirement(
            subject_name="Engineering Mathematics-IV",
            min_score=60,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            source_type=RequirementSource.ELECTIVE,
            source_name="Big Data Analytics"
        ),
    ],
    
    # Program Elective 3 Options (Semester 7)
    "Natural Language Processing": [
        SubjectRequirement(
            subject_name="Artificial Intelligence",
            subject_code="ITPCC710",
            min_score=65,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="NLP"
        ),
        SubjectRequirement(
            subject_name="Python Programming",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.9,
            source_type=RequirementSource.ELECTIVE,
            source_name="NLP"
        ),
        SubjectRequirement(
            subject_name="Engineering Mathematics-IV",
            min_score=60,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            source_type=RequirementSource.ELECTIVE,
            source_name="NLP"
        ),
    ],
    
    "Quantum Computing": [
        SubjectRequirement(
            subject_name="Engineering Mathematics-III",
            min_score=75,
            importance=ImportanceLevel.CRITICAL,
            weight=1.0,
            source_type=RequirementSource.ELECTIVE,
            source_name="Quantum Computing"
        ),
        SubjectRequirement(
            subject_name="Engineering Mathematics-IV",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="Quantum Computing"
        ),
        SubjectRequirement(
            subject_name="Data Structures and Algorithms",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            source_type=RequirementSource.ELECTIVE,
            source_name="Quantum Computing"
        ),
    ],
    
    "Ethical Hacking": [
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=75,
            importance=ImportanceLevel.CRITICAL,
            weight=1.0,
            source_type=RequirementSource.ELECTIVE,
            source_name="Ethical Hacking"
        ),
        SubjectRequirement(
            subject_name="Operating Systems",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="Ethical Hacking"
        ),
        SubjectRequirement(
            subject_name="Cryptography & Network Security",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.9,
            source_type=RequirementSource.ELECTIVE,
            source_name="Ethical Hacking"
        ),
    ],
    
    "Blockchain Technology": [
        SubjectRequirement(
            subject_name="Cryptography & Network Security",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="Blockchain Technology"
        ),
        SubjectRequirement(
            subject_name="Data Structures and Algorithms",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            source_type=RequirementSource.ELECTIVE,
            source_name="Blockchain Technology"
        ),
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=60,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            source_type=RequirementSource.ELECTIVE,
            source_name="Blockchain Technology"
        ),
    ],
    
    # Program Elective 4 Options (Semester 7)
    "Internet of Things": [
        SubjectRequirement(
            subject_name="Microcontroller & Embedded Systems",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="IoT"
        ),
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=65,
            importance=ImportanceLevel.CRITICAL,
            weight=0.9,
            source_type=RequirementSource.ELECTIVE,
            source_name="IoT"
        ),
        SubjectRequirement(
            subject_name="Python Programming",
            min_score=60,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            source_type=RequirementSource.ELECTIVE,
            source_name="IoT"
        ),
    ],
    
    "AR/VR Technologies": [
        SubjectRequirement(
            subject_name="Data Structures and Algorithms",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            source_type=RequirementSource.ELECTIVE,
            source_name="AR/VR"
        ),
        SubjectRequirement(
            subject_name="Engineering Mathematics-III",
            min_score=60,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            description="3D mathematics, transformations"
        ),
    ],
    
    # Program Elective 5 Options (Semester 8)
    "Deep Learning": [
        SubjectRequirement(
            subject_name="Artificial Intelligence",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="Deep Learning"
        ),
        SubjectRequirement(
            subject_name="Python Programming",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.9,
            source_type=RequirementSource.ELECTIVE,
            source_name="Deep Learning"
        ),
        SubjectRequirement(
            subject_name="Engineering Mathematics-III",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            source_type=RequirementSource.ELECTIVE,
            source_name="Deep Learning"
        ),
    ],
    
    "Cyber Security": [
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.ELECTIVE,
            source_name="Cyber Security"
        ),
        SubjectRequirement(
            subject_name="Cryptography & Network Security",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.9,
            source_type=RequirementSource.ELECTIVE,
            source_name="Cyber Security"
        ),
        SubjectRequirement(
            subject_name="Operating Systems",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            source_type=RequirementSource.ELECTIVE,
            source_name="Cyber Security"
        ),
    ],
}


# ============== HONOURS/MINOR REQUIREMENTS ==============
# Higher thresholds as these are advanced programs

HONOURS_REQUIREMENTS: Dict[str, List[SubjectRequirement]] = {
    "Data Science Honours": [
        SubjectRequirement(
            subject_name="Engineering Mathematics-IV",
            min_score=75,
            importance=ImportanceLevel.CRITICAL,
            weight=1.0,
            source_type=RequirementSource.HONOURS,
            source_name="Data Science Honours"
        ),
        SubjectRequirement(
            subject_name="Python Programming",
            min_score=75,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.HONOURS,
            source_name="Data Science Honours"
        ),
        SubjectRequirement(
            subject_name="Database Management Systems",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.9,
            source_type=RequirementSource.HONOURS,
            source_name="Data Science Honours"
        ),
        SubjectRequirement(
            subject_name="Engineering Mathematics-III",
            min_score=70,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            source_type=RequirementSource.HONOURS,
            source_name="Data Science Honours"
        ),
        SubjectRequirement(
            subject_name="Data Structures and Algorithms",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            source_type=RequirementSource.HONOURS,
            source_name="Data Science Honours"
        ),
    ],
    
    "AI Minor": [
        SubjectRequirement(
            subject_name="Engineering Mathematics-III",
            min_score=75,
            importance=ImportanceLevel.CRITICAL,
            weight=1.0,
            source_type=RequirementSource.MINOR,
            source_name="AI Minor"
        ),
        SubjectRequirement(
            subject_name="Data Structures and Algorithms",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.MINOR,
            source_name="AI Minor"
        ),
        SubjectRequirement(
            subject_name="Python Programming",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.9,
            source_type=RequirementSource.MINOR,
            source_name="AI Minor"
        ),
        SubjectRequirement(
            subject_name="Engineering Mathematics-IV",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            source_type=RequirementSource.MINOR,
            source_name="AI Minor"
        ),
    ],
    
    "Cybersecurity Minor": [
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=75,
            importance=ImportanceLevel.CRITICAL,
            weight=1.0,
            source_type=RequirementSource.MINOR,
            source_name="Cybersecurity Minor"
        ),
        SubjectRequirement(
            subject_name="Operating Systems",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.MINOR,
            source_name="Cybersecurity Minor"
        ),
        SubjectRequirement(
            subject_name="Cryptography & Network Security",
            min_score=75,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.MINOR,
            source_name="Cybersecurity Minor"
        ),
        SubjectRequirement(
            subject_name="Data Structures and Algorithms",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            source_type=RequirementSource.MINOR,
            source_name="Cybersecurity Minor"
        ),
    ],
    
    "Cloud Computing Minor": [
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=75,
            importance=ImportanceLevel.CRITICAL,
            weight=1.0,
            source_type=RequirementSource.MINOR,
            source_name="Cloud Computing Minor"
        ),
        SubjectRequirement(
            subject_name="Operating Systems",
            min_score=75,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.MINOR,
            source_name="Cloud Computing Minor"
        ),
        SubjectRequirement(
            subject_name="Database Management Systems",
            min_score=70,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            source_type=RequirementSource.MINOR,
            source_name="Cloud Computing Minor"
        ),
        SubjectRequirement(
            subject_name="Software Engineering",
            min_score=65,
            importance=ImportanceLevel.MEDIUM,
            weight=0.75,
            source_type=RequirementSource.MINOR,
            source_name="Cloud Computing Minor"
        ),
    ],
    
    "Full Stack Development Minor": [
        SubjectRequirement(
            subject_name="Database Management Systems",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.95,
            source_type=RequirementSource.MINOR,
            source_name="Full Stack Development Minor"
        ),
        SubjectRequirement(
            subject_name="Python Programming",
            min_score=70,
            importance=ImportanceLevel.CRITICAL,
            weight=0.9,
            source_type=RequirementSource.MINOR,
            source_name="Full Stack Development Minor"
        ),
        SubjectRequirement(
            subject_name="Computer Networks",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.85,
            source_type=RequirementSource.MINOR,
            source_name="Full Stack Development Minor"
        ),
        SubjectRequirement(
            subject_name="Software Engineering",
            min_score=65,
            importance=ImportanceLevel.HIGH,
            weight=0.8,
            source_type=RequirementSource.MINOR,
            source_name="Full Stack Development Minor"
        ),
    ],
}


# ============== SUBJECT NAME ALIASES ==============
# Maps various names to canonical subject names

SUBJECT_ALIASES: Dict[str, str] = {
    # Mathematics
    "math": "Engineering Mathematics-III",
    "mathematics": "Engineering Mathematics-III",
    "maths": "Engineering Mathematics-III",
    "math-3": "Engineering Mathematics-III",
    "math-4": "Engineering Mathematics-IV",
    "linear algebra": "Engineering Mathematics-III",
    "calculus": "Engineering Mathematics-III",
    "statistics": "Engineering Mathematics-IV",
    "probability": "Engineering Mathematics-IV",
    
    # Programming
    "python": "Python Programming",
    "py": "Python Programming",
    "c": "C Programming",
    "c++": "C++ Programming",
    "cpp": "C++ Programming",
    
    # Core CS
    "dsa": "Data Structures and Algorithms",
    "data structures": "Data Structures and Algorithms",
    "algorithms": "Data Structures and Algorithms",
    "dbms": "Database Management Systems",
    "database": "Database Management Systems",
    "db": "Database Management Systems",
    "os": "Operating Systems",
    "cn": "Computer Networks",
    "networking": "Computer Networks",
    "networks": "Computer Networks",
    "se": "Software Engineering",
    
    # Specialized
    "crypto": "Cryptography & Network Security",
    "cryptography": "Cryptography & Network Security",
    "security": "Cryptography & Network Security",
    "embedded": "Microcontroller & Embedded Systems",
    "microcontroller": "Microcontroller & Embedded Systems",
    "embedded systems": "Microcontroller & Embedded Systems",
    "ai": "Artificial Intelligence",
    "toc": "Automata Theory",
    "automata": "Automata Theory",
    "daa": "Design & Analysis of Algorithms",
}


class SubjectMappingService:
    """
    Service for handling subject-requirement mappings
    """
    
    def __init__(self):
        self.interest_requirements = INTEREST_REQUIREMENTS
        self.elective_requirements = ELECTIVE_REQUIREMENTS
        self.honours_requirements = HONOURS_REQUIREMENTS
        self.subject_aliases = SUBJECT_ALIASES
    
    def get_canonical_subject_name(self, name: str) -> str:
        """Convert any subject name to canonical form"""
        name_lower = name.lower().strip()
        return self.subject_aliases.get(name_lower, name)
    
    def get_requirements_for_interest(
        self, 
        interest: str
    ) -> List[SubjectRequirement]:
        """Get all subject requirements for an interest"""
        # Try exact match first
        if interest in self.interest_requirements:
            reqs = self.interest_requirements[interest]
            for req in reqs:
                req.source_type = RequirementSource.INTEREST
                req.source_name = interest
            return reqs
        
        # Try case-insensitive match
        for key, reqs in self.interest_requirements.items():
            if key.lower() == interest.lower():
                for req in reqs:
                    req.source_type = RequirementSource.INTEREST
                    req.source_name = interest
                return reqs
        
        return []
    
    def get_requirements_for_elective(
        self, 
        elective: str
    ) -> List[SubjectRequirement]:
        """Get all subject requirements for an elective"""
        # Try exact match first
        if elective in self.elective_requirements:
            return self.elective_requirements[elective]
        
        # Try case-insensitive and partial match
        elective_lower = elective.lower()
        for key, reqs in self.elective_requirements.items():
            if key.lower() == elective_lower or key.lower() in elective_lower:
                return reqs
        
        return []
    
    def get_requirements_for_honours(
        self, 
        programme: str
    ) -> List[SubjectRequirement]:
        """Get all subject requirements for an honours/minor programme"""
        # Try exact match first
        if programme in self.honours_requirements:
            return self.honours_requirements[programme]
        
        # Try case-insensitive and partial match
        programme_lower = programme.lower()
        for key, reqs in self.honours_requirements.items():
            if key.lower() == programme_lower or programme_lower in key.lower():
                return reqs
        
        return []
    
    def build_academic_target_profile(
        self,
        student_id: str,
        interests: List[str],
        electives: List[str],
        honours_minors: List[str]
    ) -> AcademicTarget:
        """
        Build complete academic target profile with merged requirements.
        
        This implements Step 1 of the Master Prompt:
        - Collect all subjects required for interests, electives, honours
        - Merge duplicates with highest importance
        - Track source of each requirement
        """
        target = AcademicTarget(
            student_id=student_id,
            interests=interests,
            electives=electives,
            honours_minors=honours_minors
        )
        
        all_requirements: List[SubjectRequirement] = []
        
        # Collect from interests
        for interest in interests:
            reqs = self.get_requirements_for_interest(interest)
            all_requirements.extend(reqs)
        
        # Collect from electives
        for elective in electives:
            reqs = self.get_requirements_for_elective(elective)
            all_requirements.extend(reqs)
        
        # Collect from honours/minors
        for programme in honours_minors:
            reqs = self.get_requirements_for_honours(programme)
            all_requirements.extend(reqs)
        
        target.all_requirements = all_requirements
        
        # Merge requirements - same subject keeps highest importance
        merged: Dict[str, SubjectRequirement] = {}
        
        for req in all_requirements:
            canonical_name = self.get_canonical_subject_name(req.subject_name)
            
            if canonical_name not in merged:
                merged[canonical_name] = SubjectRequirement(
                    subject_name=canonical_name,
                    subject_code=req.subject_code,
                    min_score=req.min_score,
                    importance=req.importance,
                    weight=req.weight,
                    source_type=req.source_type,
                    source_name=req.source_name,
                    description=req.description
                )
            else:
                existing = merged[canonical_name]
                
                # Keep higher min_score
                if req.min_score > existing.min_score:
                    existing.min_score = req.min_score
                
                # Keep higher importance
                importance_order = [
                    ImportanceLevel.LOW,
                    ImportanceLevel.MEDIUM,
                    ImportanceLevel.HIGH,
                    ImportanceLevel.CRITICAL
                ]
                if importance_order.index(req.importance) > importance_order.index(existing.importance):
                    existing.importance = req.importance
                
                # Keep higher weight
                if req.weight > existing.weight:
                    existing.weight = req.weight
                
                # Combine source names
                if req.source_name not in existing.source_name:
                    existing.source_name = f"{existing.source_name}, {req.source_name}"
        
        target.merged_requirements = merged
        
        return target
    
    def get_available_interests(self) -> List[str]:
        """Get list of all available interests"""
        return list(self.interest_requirements.keys())
    
    def get_available_electives(self) -> List[str]:
        """Get list of all available electives"""
        return list(self.elective_requirements.keys())
    
    def get_available_honours(self) -> List[str]:
        """Get list of all available honours/minors"""
        return list(self.honours_requirements.keys())


# Singleton instance
_mapping_service: Optional[SubjectMappingService] = None

def get_subject_mapping_service() -> SubjectMappingService:
    """Get singleton instance of SubjectMappingService"""
    global _mapping_service
    if _mapping_service is None:
        _mapping_service = SubjectMappingService()
    return _mapping_service

# ============== IT DEPARTMENT HONOURS/MINORS CLASSIFICATION ==============
# For IT Department ONLY:
# - Honours: Cybersecurity, AIML
# - Minors: Everything else

IT_HONOURS_PROGRAMS = [
    "Cybersecurity",
    "Cyber Security", 
    "Cybersecurity Honours",
    "AIML",
    "AI/ML",
    "Artificial Intelligence & Machine Learning",
    "AI & Machine Learning",
    "AI & ML Honours",
    "AI/ML Honours",
]

IT_MINOR_PROGRAMS = [
    "Data Science",
    "Data Science Minor",
    "Cloud Computing",
    "Cloud Computing Minor",
    "Blockchain",
    "Blockchain Technology",
    "Full Stack Development",
    "Full Stack Development Minor",
    "IoT",
    "Internet of Things",
    "DevOps",
    "DevOps Minor",
    "AR/VR",
    "AR/VR Technologies",
    "Game Development",
    "Quantum Computing",
]

def get_programme_type_for_branch(programme_name: str, branch: str) -> str:
    """
    Determine if a programme is Honours or Minor for a specific branch.
    
    For IT Department:
    - Honours: Cybersecurity, AIML
    - Minor: Everything else
    
    For other departments, use generic logic.
    """
    programme_lower = programme_name.lower().strip()
    
    if branch.upper() == 'IT':
        # Check if it's an IT Honours program
        for honours in IT_HONOURS_PROGRAMS:
            if honours.lower() in programme_lower or programme_lower in honours.lower():
                return 'honours'
        
        # Check if it's explicitly an IT Minor
        for minor in IT_MINOR_PROGRAMS:
            if minor.lower() in programme_lower or programme_lower in minor.lower():
                return 'minor'
        
        # Default for IT: if not in honours list, it's a minor
        return 'minor'
    
    # For COMP department
    elif branch.upper() == 'COMP':
        # COMP honours might include AI/ML, Data Science
        if any(h.lower() in programme_lower for h in ['aiml', 'ai/ml', 'data science', 'machine learning']):
            return 'honours'
        return 'minor'
    
    # For EXTC department
    elif branch.upper() == 'EXTC':
        if any(h.lower() in programme_lower for h in ['iot', 'vlsi', 'embedded', 'communication']):
            return 'honours'
        return 'minor'
    
    # Default: use naming convention
    if 'honours' in programme_lower:
        return 'honours'
    elif 'minor' in programme_lower:
        return 'minor'
    
    # Fallback based on common programmes
    honours_keywords = ['cybersecurity', 'aiml', 'ai/ml', 'artificial intelligence']
    if any(kw in programme_lower for kw in honours_keywords):
        return 'honours'
    
    return 'minor'


def get_available_programmes_for_branch(branch: str) -> Dict[str, List[str]]:
    """Get available Honours and Minor programmes for a branch."""
    
    if branch.upper() == 'IT':
        return {
            'honours': [
                'Cybersecurity',
                'AI & Machine Learning',
            ],
            'minors': [
                'Data Science',
                'Cloud Computing', 
                'Blockchain Technology',
                'Full Stack Development',
                'IoT',
                'DevOps',
            ]
        }
    
    elif branch.upper() == 'COMP':
        return {
            'honours': [
                'AI & Machine Learning',
                'Data Science',
            ],
            'minors': [
                'Cybersecurity',
                'Cloud Computing',
                'Blockchain Technology',
                'Full Stack Development',
            ]
        }
    
    elif branch.upper() == 'EXTC':
        return {
            'honours': [
                'IoT',
                'VLSI Design',
                'Embedded Systems',
            ],
            'minors': [
                'AI & Machine Learning',
                'Data Science',
                'Robotics',
            ]
        }
    
    # Default for other branches
    return {
        'honours': ['AI & Machine Learning'],
        'minors': ['Data Science', 'Cloud Computing', 'Full Stack Development']
    }