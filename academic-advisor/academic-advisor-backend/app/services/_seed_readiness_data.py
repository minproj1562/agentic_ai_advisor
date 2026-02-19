# app/services/_seed_readiness_data.py
"""
Builds the initial SubjectRequirementMap documents.
Called ONCE when the collection is empty.
All values live in the DB after seeding — the engine never uses this file again.
"""

from typing import List
from app.models.readiness import SubjectRequirementMap, RequiredSubject


def _rs(
    name: str,
    code: str = "",
    aliases: List[str] = None,
    importance: float = 0.5,
    label: str = "Medium",
    min_score: float = 60,
    weight: float = 1.0,
) -> RequiredSubject:
    return RequiredSubject(
        subject_name=name,
        subject_code=code or None,
        aliases=aliases or [],
        importance=importance,
        importance_label=label,
        min_score=min_score,
        weight=weight,
    )


def build_seed_documents() -> List[SubjectRequirementMap]:
    docs: List[SubjectRequirementMap] = []

    # ═══════════════════════════════════════════════════════════════
    #  INTERESTS
    # ═══════════════════════════════════════════════════════════════

    # ─── Computer Vision ───────────────────────────────────────────
    docs.append(SubjectRequirementMap(
        target_type="interest",
        target_name="Computer Vision",
        target_aliases=["CV", "computer vision", "image processing", "Image Processing", "Vision"],
        required_subjects=[
            _rs("Python", "ITSBL301", ["Python Programming", "Python Programming Lab"],
                1.0, "Critical", 70, 3.0),
            _rs("Engineering Mathematics-III", "BSC301", ["Math-III", "Mathematics-III", "Mathematics"],
                0.9, "Critical", 65, 2.5),
            _rs("Engineering Mathematics-IV", "BSC401", ["Math-IV", "Statistics", "Probability"],
                0.85, "High", 60, 2.0),
            _rs("Data Structures and Algorithms", "ITPCC301", ["DSA", "Data Structures"],
                0.75, "High", 60, 2.0),
            _rs("Artificial Intelligence", "ITPCC710", ["AI"],
                0.9, "Critical", 65, 3.0),
            _rs("Digital Logic & Computer Architecture", "ITPCC303", ["DLCA", "Digital Logic", "DLDA"],
                0.6, "Medium", 55, 1.5),
        ],
    ))

    # ─── Machine Learning ──────────────────────────────────────────
    docs.append(SubjectRequirementMap(
        target_type="interest",
        target_name="Machine Learning",
        target_aliases=["ML", "machine learning", "AI/ML"],
        required_subjects=[
            _rs("Python", "ITSBL301", ["Python Programming", "Python Programming Lab"],
                1.0, "Critical", 65, 3.0),
            _rs("Engineering Mathematics-III", "BSC301", ["Math-III", "Mathematics-III", "Mathematics"],
                0.9, "Critical", 65, 2.0),
            _rs("Data Structures and Algorithms", "ITPCC301", ["DSA", "Data Structures"],
                0.8, "High", 60, 2.5),
            _rs("Engineering Mathematics-IV", "BSC401", ["Math-IV", "Statistics", "Probability"],
                0.7, "High", 60, 1.5),
            _rs("Database Management Systems", "ITPCC302", ["DBMS", "Database Management System"],
                0.5, "Medium", 55, 1.5),
            _rs("Artificial Intelligence", "ITPCC710", ["AI"],
                0.95, "Critical", 65, 3.5),
        ],
    ))

    # ─── Artificial Intelligence ───────────────────────────────────
    docs.append(SubjectRequirementMap(
        target_type="interest",
        target_name="Artificial Intelligence",
        target_aliases=["AI", "artificial intelligence"],
        required_subjects=[
            _rs("Python", "", ["Python Programming"], 0.95, "Critical", 65, 3.0),
            _rs("Engineering Mathematics-III", "", ["Math-III", "Mathematics"],
                0.9, "Critical", 65, 2.0),
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.85, "High", 60, 2.5),
            _rs("Engineering Mathematics-IV", "", ["Math-IV", "Statistics"],
                0.75, "High", 60, 1.5),
            _rs("Automata Theory", "", ["Theory of Computer Science", "Automata Theory / Theory of Computer Science"],
                0.6, "Medium", 55, 1.0),
        ],
    ))

    # ─── Deep Learning ─────────────────────────────────────────────
    docs.append(SubjectRequirementMap(
        target_type="interest",
        target_name="Deep Learning",
        target_aliases=["DL", "deep learning", "neural networks", "Neural Networks"],
        required_subjects=[
            _rs("Python", "", ["Python Programming"], 1.0, "Critical", 70, 3.0),
            _rs("Engineering Mathematics-III", "", ["Math-III", "Mathematics"],
                0.9, "Critical", 65, 2.5),
            _rs("Engineering Mathematics-IV", "", ["Math-IV", "Statistics"],
                0.85, "High", 60, 2.0),
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.7, "High", 60, 2.0),
            _rs("Artificial Intelligence", "", ["AI"], 0.95, "Critical", 65, 3.5),
        ],
    ))

    # ─── Natural Language Processing ───────────────────────────────
    docs.append(SubjectRequirementMap(
        target_type="interest",
        target_name="Natural Language Processing",
        target_aliases=["NLP", "nlp", "text processing", "Language Processing"],
        required_subjects=[
            _rs("Python", "", ["Python Programming"], 1.0, "Critical", 70, 3.0),
            _rs("Engineering Mathematics-III", "", ["Math-III", "Mathematics"],
                0.8, "High", 60, 2.0),
            _rs("Engineering Mathematics-IV", "", ["Math-IV", "Statistics", "Probability"],
                0.75, "High", 60, 1.5),
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.7, "High", 60, 2.0),
            _rs("Artificial Intelligence", "", ["AI"], 0.9, "Critical", 65, 3.0),
        ],
    ))

    # ─── Data Science ──────────────────────────────────────────────
    docs.append(SubjectRequirementMap(
        target_type="interest",
        target_name="Data Science",
        target_aliases=["data science", "Data Analytics", "analytics", "Big Data"],
        required_subjects=[
            _rs("Engineering Mathematics-IV", "", ["Statistics", "Math-IV"],
                0.95, "Critical", 65, 2.5),
            _rs("Python", "", ["Python Programming"], 0.9, "Critical", 65, 2.5),
            _rs("Database Management Systems", "", ["DBMS"], 0.85, "High", 60, 2.0),
            _rs("Engineering Mathematics-III", "", ["Mathematics"], 0.7, "High", 60, 1.5),
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.6, "Medium", 55, 1.5),
        ],
    ))

    # ─── Web Development ───────────────────────────────────────────
    docs.append(SubjectRequirementMap(
        target_type="interest",
        target_name="Web Development",
        target_aliases=["web dev", "Full Stack", "frontend", "backend", "Full Stack Development"],
        required_subjects=[
            _rs("Database Management Systems", "", ["DBMS"], 0.9, "Critical", 65, 2.5),
            _rs("Python", "", ["Python Programming"], 0.8, "High", 60, 2.0),
            _rs("Computer Networks", "", ["CN", "Networking"], 0.7, "High", 60, 2.0),
            _rs("Software Engineering", "", ["SE"], 0.6, "Medium", 55, 1.5),
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.65, "Medium", 55, 1.5),
        ],
    ))

    # ─── Cloud Computing ───────────────────────────────────────────
    docs.append(SubjectRequirementMap(
        target_type="interest",
        target_name="Cloud Computing",
        target_aliases=["cloud", "DevOps", "Cloud & Distributed Systems", "AWS", "Azure"],
        required_subjects=[
            _rs("Computer Networks", "", ["CN", "Networking"], 0.95, "Critical", 65, 3.0),
            _rs("Operating Systems", "", ["OS", "Operating System"], 0.9, "Critical", 65, 2.5),
            _rs("Database Management Systems", "", ["DBMS"], 0.7, "High", 55, 2.0),
            _rs("Software Engineering", "", ["SE"], 0.6, "Medium", 55, 1.5),
        ],
    ))

    # ─── Cybersecurity ─────────────────────────────────────────────
    docs.append(SubjectRequirementMap(
        target_type="interest",
        target_name="Cybersecurity",
        target_aliases=["security", "cyber security", "Network Security", "Information Security", "Ethical Hacking"],
        required_subjects=[
            _rs("Computer Networks", "", ["CN"], 1.0, "Critical", 65, 3.5),
            _rs("Operating Systems", "", ["OS"], 0.9, "Critical", 65, 2.5),
            _rs("Cryptography & Network Security", "", ["Cryptography", "CNS"],
                0.95, "Critical", 65, 3.0),
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.6, "Medium", 55, 1.5),
        ],
    ))

    # ─── IoT ───────────────────────────────────────────────────────
    docs.append(SubjectRequirementMap(
        target_type="interest",
        target_name="IoT",
        target_aliases=["Internet of Things", "Embedded Systems", "Mobile & IoT Development", "Embedded"],
        required_subjects=[
            _rs("Microcontroller & Embedded Systems", "", ["Microprocessor and Embedded Systems", "MES"],
                0.95, "Critical", 65, 3.0),
            _rs("Computer Networks", "", ["CN"], 0.85, "High", 60, 2.5),
            _rs("Digital Logic & Computer Architecture", "", ["Digital Logic & Design", "DLDA", "DLCA"],
                0.7, "High", 60, 2.0),
            _rs("Python", "", ["Python Programming"], 0.6, "Medium", 55, 1.5),
        ],
    ))

    # ─── Blockchain ────────────────────────────────────────────────
    docs.append(SubjectRequirementMap(
        target_type="interest",
        target_name="Blockchain",
        target_aliases=["blockchain", "distributed ledger", "Cryptocurrency", "Web3"],
        required_subjects=[
            _rs("Cryptography & Network Security", "", ["Cryptography"], 0.95, "Critical", 65, 3.0),
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.85, "High", 60, 2.5),
            _rs("Computer Networks", "", ["CN"], 0.7, "High", 60, 2.0),
            _rs("Database Management Systems", "", ["DBMS"], 0.6, "Medium", 55, 1.5),
        ],
    ))

    # ─── Mobile Development ────────────────────────────────────────
    docs.append(SubjectRequirementMap(
        target_type="interest",
        target_name="Mobile Development",
        target_aliases=["mobile dev", "Android", "iOS", "Flutter", "App Development", "Mobile App"],
        required_subjects=[
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.85, "High", 60, 2.5),
            _rs("Database Management Systems", "", ["DBMS"], 0.8, "High", 60, 2.0),
            _rs("Software Engineering", "", ["SE"], 0.7, "High", 55, 1.5),
            _rs("Operating Systems", "", ["OS"], 0.6, "Medium", 55, 1.5),
        ],
    ))

    # ─── Robotics ──────────────────────────────────────────────────
    docs.append(SubjectRequirementMap(
        target_type="interest",
        target_name="Robotics",
        target_aliases=["robotics", "Automation", "Robot"],
        required_subjects=[
            _rs("Python", "", ["Python Programming"], 0.9, "Critical", 65, 2.5),
            _rs("Microcontroller & Embedded Systems", "", ["MES", "Embedded Systems"],
                0.95, "Critical", 65, 3.0),
            _rs("Engineering Mathematics-III", "", ["Math-III"], 0.8, "High", 60, 2.0),
            _rs("Digital Logic & Computer Architecture", "", ["DLDA", "DLCA"], 0.7, "High", 60, 2.0),
        ],
    ))

    # ─── Game Development ──────────────────────────────────────────
    docs.append(SubjectRequirementMap(
        target_type="interest",
        target_name="Game Development",
        target_aliases=["game dev", "Gaming", "Game Design", "Games"],
        required_subjects=[
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.9, "Critical", 65, 2.5),
            _rs("Python", "", ["Python Programming"], 0.7, "High", 60, 2.0),
            _rs("Engineering Mathematics-III", "", ["Math-III", "Mathematics"], 0.75, "High", 60, 2.0),
            _rs("Software Engineering", "", ["SE"], 0.6, "Medium", 55, 1.5),
        ],
    ))

    # ─── Software Engineering (Career) ─────────────────────────────
    docs.append(SubjectRequirementMap(
        target_type="interest",
        target_name="Software Engineering",
        target_aliases=["SDE", "Software Development", "Programming", "Coding"],
        required_subjects=[
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.95, "Critical", 70, 3.0),
            _rs("Database Management Systems", "", ["DBMS"], 0.85, "High", 60, 2.5),
            _rs("Operating Systems", "", ["OS"], 0.75, "High", 60, 2.0),
            _rs("Software Engineering", "", ["SE"], 0.8, "High", 60, 2.0),
            _rs("Python", "", ["Python Programming"], 0.7, "High", 60, 2.0),
        ],
    ))

    # ═══════════════════════════════════════════════════════════════
    #  ELECTIVES (from curriculum PEC groups)
    # ═══════════════════════════════════════════════════════════════

    docs.append(SubjectRequirementMap(
        target_type="elective",
        target_name="Machine Learning",
        target_aliases=["ML", "ITPEC5012"],
        target_code="ITPEC5012",
        required_subjects=[
            _rs("Python", "", ["Python Programming"], 0.95, "Critical", 65, 3.0),
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.8, "High", 60, 2.5),
            _rs("Engineering Mathematics-III", "", ["Math-III", "Mathematics"],
                0.85, "High", 60, 2.0),
            _rs("Engineering Mathematics-IV", "", ["Math-IV", "Statistics"],
                0.65, "Medium", 55, 1.5),
            _rs("Database Management Systems", "", ["DBMS"], 0.6, "Medium", 55, 1.5),
        ],
    ))

    docs.append(SubjectRequirementMap(
        target_type="elective",
        target_name="Wireless Technology",
        target_aliases=["WT", "ITPEC5013", "Wireless Technologies"],
        target_code="ITPEC5013",
        required_subjects=[
            _rs("Computer Networks", "", ["CN", "Networking"], 0.95, "Critical", 65, 3.5),
            _rs("Microcontroller & Embedded Systems", "", ["MES", "Microprocessor"],
                0.9, "Critical", 60, 3.0),
            _rs("Digital Logic & Computer Architecture", "", ["DLDA", "DLCA"],
                0.7, "High", 55, 2.0),
            _rs("Operating Systems", "", ["OS"], 0.65, "Medium", 55, 2.0),
        ],
    ))

    docs.append(SubjectRequirementMap(
        target_type="elective",
        target_name="Data Warehouse and Mining",
        target_aliases=["DWM", "ITPEC5014", "Data Warehouse and Data Mining", "Data Mining"],
        target_code="ITPEC5014",
        required_subjects=[
            _rs("Database Management Systems", "", ["DBMS"], 0.95, "Critical", 65, 3.5),
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.8, "High", 60, 2.5),
            _rs("Python", "", ["Python Programming"], 0.7, "High", 55, 2.0),
            _rs("Engineering Mathematics-IV", "", ["Math-IV", "Statistics"],
                0.6, "Medium", 55, 1.5),
        ],
    ))

    docs.append(SubjectRequirementMap(
        target_type="elective",
        target_name="Cloud Computing Services",
        target_aliases=["CCS", "ITPEC5015", "Cloud Computing"],
        target_code="ITPEC5015",
        required_subjects=[
            _rs("Computer Networks", "", ["CN"], 0.9, "Critical", 65, 3.0),
            _rs("Operating Systems", "", ["OS"], 0.85, "High", 60, 2.5),
            _rs("Database Management Systems", "", ["DBMS"], 0.7, "High", 55, 2.0),
            _rs("Software Engineering", "", ["SE"], 0.6, "Medium", 55, 2.0),
        ],
    ))

    docs.append(SubjectRequirementMap(
        target_type="elective",
        target_name="Big Data Analytics",
        target_aliases=["BDA", "ITPEC6024", "Big Data"],
        target_code="ITPEC6024",
        required_subjects=[
            _rs("Database Management Systems", "", ["DBMS"], 0.9, "Critical", 65, 3.0),
            _rs("Python", "", ["Python Programming"], 0.85, "High", 60, 2.5),
            _rs("Engineering Mathematics-IV", "", ["Statistics"], 0.7, "High", 60, 2.0),
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.65, "Medium", 55, 1.5),
        ],
    ))

    docs.append(SubjectRequirementMap(
        target_type="elective",
        target_name="Natural Language Processing",
        target_aliases=["NLP", "ITPEC7033"],
        target_code="ITPEC7033",
        required_subjects=[
            _rs("Python", "", ["Python Programming"], 0.95, "Critical", 70, 3.0),
            _rs("Artificial Intelligence", "", ["AI"], 0.9, "Critical", 65, 3.0),
            _rs("Engineering Mathematics-IV", "", ["Statistics"], 0.7, "High", 60, 2.0),
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.6, "Medium", 55, 1.5),
        ],
    ))

    docs.append(SubjectRequirementMap(
        target_type="elective",
        target_name="Deep Learning",
        target_aliases=["DL", "ITPEC8051"],
        target_code="ITPEC8051",
        required_subjects=[
            _rs("Python", "", ["Python Programming"], 0.95, "Critical", 70, 3.0),
            _rs("Artificial Intelligence", "", ["AI"], 0.9, "Critical", 65, 3.0),
            _rs("Engineering Mathematics-III", "", ["Math-III"], 0.8, "High", 60, 2.0),
            _rs("Engineering Mathematics-IV", "", ["Statistics"], 0.75, "High", 60, 2.0),
        ],
    ))

    docs.append(SubjectRequirementMap(
        target_type="elective",
        target_name="Ethical Hacking",
        target_aliases=["ITPEC7032", "Hacking", "Penetration Testing"],
        target_code="ITPEC7032",
        required_subjects=[
            _rs("Computer Networks", "", ["CN"], 0.95, "Critical", 65, 3.5),
            _rs("Operating Systems", "", ["OS"], 0.9, "Critical", 65, 3.0),
            _rs("Cryptography & Network Security", "", ["CNS", "Cryptography"], 0.85, "High", 60, 2.5),
        ],
    ))

    docs.append(SubjectRequirementMap(
        target_type="elective",
        target_name="Internet of Things",
        target_aliases=["IoT", "ITPEC7042"],
        target_code="ITPEC7042",
        required_subjects=[
            _rs("Microcontroller & Embedded Systems", "", ["MES"], 0.95, "Critical", 65, 3.0),
            _rs("Computer Networks", "", ["CN"], 0.85, "High", 60, 2.5),
            _rs("Python", "", ["Python Programming"], 0.7, "High", 55, 2.0),
        ],
    ))

    docs.append(SubjectRequirementMap(
        target_type="elective",
        target_name="Blockchain Technology",
        target_aliases=["Blockchain", "ITPEC7034"],
        target_code="ITPEC7034",
        required_subjects=[
            _rs("Cryptography & Network Security", "", ["CNS", "Cryptography"], 0.95, "Critical", 65, 3.0),
            _rs("Computer Networks", "", ["CN"], 0.8, "High", 60, 2.5),
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.75, "High", 60, 2.0),
        ],
    ))

    # ═══════════════════════════════════════════════════════════════
    #  HONOURS / MINORS
    # ═══════════════════════════════════════════════════════════════

    docs.append(SubjectRequirementMap(
        target_type="honours",
        target_name="AI / ML Honours",
        target_aliases=["AI Honours", "ML Honours", "AI/ML Honours", "Machine Learning Honours"],
        min_cgpa=7.5,
        required_subjects=[
            _rs("Python", "", ["Python Programming"], 1.0, "Critical", 70, 3.0),
            _rs("Artificial Intelligence", "", ["AI"], 0.95, "Critical", 65, 3.5),
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.8, "High", 60, 2.5),
            _rs("Engineering Mathematics-III", "", ["Mathematics"], 0.85, "High", 65, 2.0),
            _rs("Engineering Mathematics-IV", "", ["Statistics"], 0.7, "High", 60, 1.5),
        ],
    ))

    docs.append(SubjectRequirementMap(
        target_type="honours",
        target_name="Data Science Honours",
        target_aliases=["Data Science", "DS Honours", "Analytics Honours"],
        min_cgpa=7.5,
        required_subjects=[
            _rs("Database Management Systems", "", ["DBMS"], 0.95, "Critical", 65, 3.0),
            _rs("Python", "", ["Python Programming"], 0.9, "Critical", 65, 2.5),
            _rs("Data Structures and Algorithms", "", ["DSA"], 0.8, "High", 60, 2.0),
            _rs("Engineering Mathematics-IV", "", ["Statistics"], 0.85, "High", 65, 2.0),
        ],
    ))

    docs.append(SubjectRequirementMap(
        target_type="honours",
        target_name="Cybersecurity Minor",
        target_aliases=["Cyber Minor", "Security Minor", "Network Security Minor"],
        min_cgpa=7.0,
        required_subjects=[
            _rs("Computer Networks", "", ["CN"], 0.95, "Critical", 65, 3.5),
            _rs("Operating Systems", "", ["OS"], 0.9, "Critical", 65, 2.5),
            _rs("Cryptography & Network Security", "", ["Cryptography", "CNS"],
                0.95, "Critical", 65, 3.0),
        ],
    ))

    docs.append(SubjectRequirementMap(
        target_type="honours",
        target_name="Cloud Computing Minor",
        target_aliases=["Cloud Minor", "DevOps Minor"],
        min_cgpa=7.0,
        required_subjects=[
            _rs("Computer Networks", "", ["CN"], 0.9, "Critical", 65, 3.0),
            _rs("Operating Systems", "", ["OS"], 0.85, "High", 60, 2.5),
            _rs("Database Management Systems", "", ["DBMS"], 0.7, "High", 55, 2.0),
        ],
    ))

    docs.append(SubjectRequirementMap(
        target_type="honours",
        target_name="IoT & Embedded Minor",
        target_aliases=["IoT Minor", "Embedded Minor", "Embedded Systems Minor"],
        min_cgpa=6.5,
        required_subjects=[
            _rs("Microcontroller & Embedded Systems", "", ["MES", "Microprocessor"],
                0.95, "Critical", 65, 3.0),
            _rs("Computer Networks", "", ["CN"], 0.8, "High", 60, 2.5),
            _rs("Digital Logic & Computer Architecture", "", ["DLDA", "DLCA"], 0.7, "High", 55, 2.0),
        ],
    ))

    return docs