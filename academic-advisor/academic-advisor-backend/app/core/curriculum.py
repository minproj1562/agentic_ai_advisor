# academic-advisor-backend/app/core/curriculum.py

from typing import Dict, List, Literal
from pydantic import BaseModel


class SubjectDefinition(BaseModel):
    subject_code: str
    subject_name: str
    credits: int
    course_type: Literal["PCC", "PEC", "LBC", "SBL", "MNP", "MJP", "INT", "BSC", "ESC", "AEC", "OEC"]
    internal_max: int
    external_max: int
    is_elective: bool = False
    is_practical: bool = False
    elective_group: str | None = None


# Pre-Autonomy Curriculum (2022-2024 batches for Sem 1-4)
PRE_AUTONOMY_CURRICULUM: Dict[int, List[SubjectDefinition]] = {
    1: [
        SubjectDefinition(subject_code="PHY101", subject_name="Engineering Physics-I", credits=3, course_type="BSC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="CHEM101", subject_name="Engineering Chemistry-I", credits=3, course_type="BSC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="MATH101", subject_name="Engineering Mathematics-I", credits=3, course_type="BSC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="MECH101", subject_name="Engineering Mechanics", credits=3, course_type="ESC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="BEE101", subject_name="Basic Electronic Engineering", credits=3, course_type="ESC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="WS101", subject_name="Workshop Practice", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
    ],
    2: [
        SubjectDefinition(subject_code="PHY102", subject_name="Engineering Physics-II", credits=3, course_type="BSC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="CHEM102", subject_name="Engineering Chemistry-II", credits=3, course_type="BSC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="MATH102", subject_name="Engineering Mathematics-II", credits=3, course_type="BSC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="CPP102", subject_name="C++ Programming", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="ACAD102", subject_name="AutoCAD", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="EG102", subject_name="Engineering Graphics", credits=2, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="PCE102", subject_name="Professional Communication & Ethics", credits=2, course_type="AEC", internal_max=20, external_max=80),
    ],
    3: [
        SubjectDefinition(subject_code="MATH301", subject_name="Engineering Mathematics-III", credits=4, course_type="BSC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="DSA301", subject_name="Data Structures and Algorithms", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="DBMS301", subject_name="Database Management Systems", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="DLDA301", subject_name="Digital Logic & Design", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="PYTHON301", subject_name="Python Programming", credits=2, course_type="SBL", internal_max=50, external_max=50, is_practical=True),
        SubjectDefinition(subject_code="DSAL301", subject_name="DSA Laboratory", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
    ],
    4: [
        SubjectDefinition(subject_code="MATH401", subject_name="Engineering Mathematics-IV", credits=4, course_type="BSC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="MES401", subject_name="Microcontroller & Embedded Systems", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="OS401", subject_name="Operating Systems", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="CN401", subject_name="Computer Networks", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="SE401", subject_name="Software Engineering", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="MESL401", subject_name="Microcontroller Lab", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="CNL401", subject_name="Computer Networks Lab", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
    ]
}


# Autonomy Curriculum (Sem 5-8 for all batches, Sem 1-4 for 2025+ batches)
AUTONOMY_CURRICULUM: Dict[int, List[SubjectDefinition]] = {
    # ===================== Semesters 1-4 for 2025+ batches =====================
    1: [
        SubjectDefinition(subject_code="BSC101", subject_name="Engineering Mathematics-I", credits=4, course_type="BSC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="BSC102", subject_name="Engineering Physics", credits=3, course_type="BSC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="BSC103", subject_name="Engineering Chemistry", credits=3, course_type="BSC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ESC101", subject_name="Programming for Problem Solving (C)", credits=3, course_type="ESC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ESC102", subject_name="Engineering Mechanics", credits=3, course_type="ESC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="LBC101", subject_name="Programming Lab (C)", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="LBC102", subject_name="Workshop Practice", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="AEC101", subject_name="English Communication", credits=2, course_type="AEC", internal_max=20, external_max=80),
    ],
    2: [
        SubjectDefinition(subject_code="BSC201", subject_name="Engineering Mathematics-II", credits=4, course_type="BSC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="BSC202", subject_name="Discrete Mathematics", credits=3, course_type="BSC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ESC201", subject_name="Basic Electrical Engineering", credits=3, course_type="ESC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ESC202", subject_name="Basic Electronics Engineering", credits=3, course_type="ESC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="LBC201", subject_name="Engineering Graphics Lab", credits=2, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="LBC202", subject_name="C++ Programming Lab", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="LBC203", subject_name="Basic Electrical & Electronics Lab", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="AEC201", subject_name="Professional Communication & Ethics-I", credits=2, course_type="AEC", internal_max=20, external_max=80),
    ],
    3: [
        SubjectDefinition(subject_code="BSC301", subject_name="Engineering Mathematics-III", credits=4, course_type="BSC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ITPCC301", subject_name="Data Structures and Algorithms", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ITPCC302", subject_name="Database Management Systems", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ITPCC303", subject_name="Digital Logic & Computer Architecture", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ITSBL301", subject_name="Python Programming Lab", credits=2, course_type="SBL", internal_max=50, external_max=50, is_practical=True),
        SubjectDefinition(subject_code="ITLBC301", subject_name="DSA Laboratory", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="ITLBC302", subject_name="DBMS Laboratory", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
    ],
    4: [
        SubjectDefinition(subject_code="BSC401", subject_name="Engineering Mathematics-IV", credits=4, course_type="BSC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ITPCC401", subject_name="Operating Systems", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ITPCC402", subject_name="Computer Networks", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ITPCC403", subject_name="Software Engineering", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ITPCC404", subject_name="Microcontroller & Embedded Systems", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ITLBC401", subject_name="Microcontroller Lab", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="ITLBC402", subject_name="Computer Networks Lab", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="MNP4A", subject_name="Mini Project-1A", credits=1, course_type="MNP", internal_max=50, external_max=0, is_practical=True),
    ],
    # ===================== Semesters 5-8 (for all batches) =====================
    5: [
        SubjectDefinition(subject_code="ITPCC509", subject_name="Automata Theory / Theory of Computer Science", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ITPCC501", subject_name="Design & Analysis of Algorithms", credits=3, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ITPEC501", subject_name="Program Elective-I", credits=3, course_type="PEC", internal_max=20, external_max=80, is_elective=True, elective_group="PEC1"),
        SubjectDefinition(subject_code="ITLBC506", subject_name="Cloud Computing Laboratory", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="ITLBC507", subject_name="Mobile App Development Lab (Flutter)", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="MNP5A", subject_name="Mini Project-2A", credits=1, course_type="MNP", internal_max=50, external_max=0, is_practical=True),
        SubjectDefinition(subject_code="AEC502", subject_name="Professional Communication-II", credits=2, course_type="AEC", internal_max=20, external_max=80),
    ],
    6: [
        SubjectDefinition(subject_code="ITPCC611", subject_name="Cryptography & Network Security", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ITPEC602", subject_name="Program Elective-II", credits=3, course_type="PEC", internal_max=20, external_max=80, is_elective=True, elective_group="PEC2"),
        SubjectDefinition(subject_code="ITLBC608", subject_name="Cryptography Lab", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="ITLBC609", subject_name="Data Science Laboratory", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="ITSBL603", subject_name="DevOps Laboratory", credits=2, course_type="SBL", internal_max=50, external_max=50, is_practical=True),
        SubjectDefinition(subject_code="MNP6B", subject_name="Mini Project-2B", credits=1, course_type="MNP", internal_max=50, external_max=0, is_practical=True),
        SubjectDefinition(subject_code="RM601", subject_name="Research Methodology", credits=2, course_type="AEC", internal_max=20, external_max=80),
    ],
    7: [
        SubjectDefinition(subject_code="ITPCC710", subject_name="Artificial Intelligence", credits=4, course_type="PCC", internal_max=20, external_max=80),
        SubjectDefinition(subject_code="ITPEC703", subject_name="Program Elective-III", credits=3, course_type="PEC", internal_max=20, external_max=80, is_elective=True, elective_group="PEC3"),
        SubjectDefinition(subject_code="ITPEC704", subject_name="Program Elective-IV", credits=3, course_type="PEC", internal_max=20, external_max=80, is_elective=True, elective_group="PEC4"),
        SubjectDefinition(subject_code="OEC701", subject_name="Open Elective-I", credits=3, course_type="OEC", internal_max=20, external_max=80, is_elective=True, elective_group="OEC1"),
        SubjectDefinition(subject_code="ITLBC711", subject_name="AI Laboratory", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="ITLBC712", subject_name="Data Analytics Lab", credits=1, course_type="LBC", internal_max=25, external_max=25, is_practical=True),
        SubjectDefinition(subject_code="MJP7A", subject_name="Major Project-A", credits=2, course_type="MJP", internal_max=50, external_max=0, is_practical=True),
    ],
    8: [
        SubjectDefinition(subject_code="ITPEC805", subject_name="Program Elective-V", credits=3, course_type="PEC", internal_max=20, external_max=80, is_elective=True, elective_group="PEC5"),
        SubjectDefinition(subject_code="OEC802", subject_name="Open Elective-II", credits=3, course_type="OEC", internal_max=20, external_max=80, is_elective=True, elective_group="OEC2"),
        SubjectDefinition(subject_code="MJP8B", subject_name="Major Project-B", credits=4, course_type="MJP", internal_max=50, external_max=0, is_practical=True),
        SubjectDefinition(subject_code="INT801", subject_name="Internship", credits=8, course_type="INT", internal_max=100, external_max=0, is_practical=True),
    ]
}


# Elective Options
ELECTIVE_OPTIONS: Dict[str, List[Dict[str, str]]] = {
    "PEC1": [
        {"code": "ITPEC5012", "name": "Machine Learning"},
        {"code": "ITPEC5013", "name": "Wireless Technology"},
        {"code": "ITPEC5014", "name": "Data Warehouse and Mining"},
        {"code": "ITPEC5015", "name": "Cloud Computing Services"},
    ],
    "PEC2": [
        {"code": "ITPEC6021", "name": "IT Infrastructure Management"},
        {"code": "ITPEC6022", "name": "Machine Learning (if not taken in Sem 5)"},
        {"code": "ITPEC6023", "name": "Wireless Technologies"},
        {"code": "ITPEC6024", "name": "Big Data Analytics"},
    ],
    "PEC3": [
        {"code": "ITPEC7031", "name": "Quantum Computing"},
        {"code": "ITPEC7032", "name": "Ethical Hacking"},
        {"code": "ITPEC7033", "name": "Natural Language Processing"},
        {"code": "ITPEC7034", "name": "Blockchain Technology"},
    ],
    "PEC4": [
        {"code": "ITPEC7041", "name": "AR/VR Technologies"},
        {"code": "ITPEC7042", "name": "Internet of Things"},
        {"code": "ITPEC7043", "name": "Edge Computing"},
        {"code": "ITPEC7044", "name": "Software Testing"},
    ],
    "PEC5": [
        {"code": "ITPEC8051", "name": "Deep Learning"},
        {"code": "ITPEC8052", "name": "Cyber Security"},
        {"code": "ITPEC8053", "name": "Distributed Systems"},
        {"code": "ITPEC8054", "name": "Mobile Computing"},
    ],
    "OEC1": [
        {"code": "OEC7011", "name": "Project Management"},
        {"code": "OEC7012", "name": "Financial Management"},
        {"code": "OEC7013", "name": "Entrepreneurship Development"},
        {"code": "OEC7014", "name": "IPR & Patents"},
    ],
    "OEC2": [
        {"code": "OEC8021", "name": "Green Technology"},
        {"code": "OEC8022", "name": "Business Analytics"},
        {"code": "OEC8023", "name": "Supply Chain Management"},
        {"code": "OEC8024", "name": "Digital Marketing"},
    ]
}


def get_semester_subjects(semester: int, admission_year: int, current_year: int = 2025) -> List[SubjectDefinition]:
    """
    Get subjects for a semester based on admission year.
    
    Rules:
      - Admission 2024 and earlier → Sem 1-4 from PRE_AUTONOMY, Sem 5-8 from AUTONOMY
      - Admission 2025+           → ALL semesters from AUTONOMY
    """
    # FIX: Changed from < 2024 to <= 2024
    is_pre_autonomy_batch = admission_year <= 2024

    if is_pre_autonomy_batch and semester <= 4:
        # Pre-2025 batch, semesters 1-4: use pre-autonomy curriculum
        return PRE_AUTONOMY_CURRICULUM.get(semester, [])
    elif is_pre_autonomy_batch and semester > 4:
        # Pre-2025 batch, semesters 5-8: use autonomy curriculum
        return AUTONOMY_CURRICULUM.get(semester, [])
    else:
        # 2025+ batch: use autonomy for all semesters
        subjects = AUTONOMY_CURRICULUM.get(semester, [])
        # Fallback to pre-autonomy if autonomy not defined (shouldn't happen)
        if not subjects:
            subjects = PRE_AUTONOMY_CURRICULUM.get(semester, [])
        return subjects


def get_elective_options(elective_group: str) -> List[Dict[str, str]]:
    """Get available elective options for a group"""
    return ELECTIVE_OPTIONS.get(elective_group, [])