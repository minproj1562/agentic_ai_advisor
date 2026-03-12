# populate_complete_subjects.py
"""
Complete subject population for CS&E curriculum - ALL subjects
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os


async def populate_all_subjects():
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client["academic_advisor"]
    
    print("🔄 Populating COMPLETE subject list...")
    
    # Clear existing
    await db.subjects.delete_many({})
    
    all_subjects = [
        # ==================== SEMESTER 1 ====================
        {
            "code": "BSC101",
            "name": "Engineering Mathematics I",
            "semester": 1,
            "credits": 4,
            "subject_type": "BSC",
            "category": "Basic Science Course",
            "teaching_scheme": {"lecture": 4, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100, "theory": 80, "internal": 20},
            "description": "Differential calculus, integral calculus, matrices, and differential equations",
            "units": [
                {"unit_number": 1, "title": "Differential Calculus", "topics": ["Limits and Continuity", "Differentiation", "Applications of Derivatives", "Partial Derivatives"]},
                {"unit_number": 2, "title": "Integral Calculus", "topics": ["Indefinite Integrals", "Definite Integrals", "Applications", "Multiple Integrals"]},
                {"unit_number": 3, "title": "Matrices", "topics": ["Matrix Operations", "Rank", "System of Linear Equations", "Eigenvalues and Eigenvectors"]},
                {"unit_number": 4, "title": "Differential Equations", "topics": ["First Order ODE", "Second Order ODE", "Laplace Transform", "Applications"]},
            ]
        },
        {
            "code": "BSC102",
            "name": "Engineering Physics-I",
            "semester": 1,
            "credits": 2,
            "subject_type": "BSC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 75}
        },
        {
            "code": "BSC103",
            "name": "Engineering Chemistry-I",
            "semester": 1,
            "credits": 2,
            "subject_type": "BSC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 75}
        },
        {
            "code": "ESC101",
            "name": "Engineering Mechanics",
            "semester": 1,
            "credits": 3,
            "subject_type": "ESC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "ESC102",
            "name": "Basic Electrical Engineering",
            "semester": 1,
            "credits": 2,
            "subject_type": "ESC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 75}
        },
        {
            "code": "BSL101",
            "name": "Engineering Physics-I Laboratory",
            "semester": 1,
            "credits": 0.5,
            "subject_type": "BSL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 1},
            "examination_scheme": {"total": 25}
        },
        {
            "code": "BSL102",
            "name": "Engineering Chemistry-I Laboratory",
            "semester": 1,
            "credits": 0.5,
            "subject_type": "BSL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 1},
            "examination_scheme": {"total": 25}
        },
        {
            "code": "ESL101",
            "name": "Engineering Mechanics Laboratory",
            "semester": 1,
            "credits": 1,
            "subject_type": "ESL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 25}
        },
        {
            "code": "ESL102",
            "name": "Basic Electrical Engineering Laboratory",
            "semester": 1,
            "credits": 1,
            "subject_type": "ESL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "ESL103",
            "name": "Programming Laboratory-I (C)",
            "semester": 1,
            "credits": 2,
            "subject_type": "ESL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 4},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "SEC101",
            "name": "Basic Workshop Practice-I",
            "semester": 1,
            "credits": 1,
            "subject_type": "SEC",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "VEC101",
            "name": "Universal Human Values",
            "semester": 1,
            "credits": 2,
            "subject_type": "VEC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 50}
        },
        
        # ==================== SEMESTER 2 ====================
        {
            "code": "BSC204",
            "name": "Engineering Mathematics-II",
            "semester": 2,
            "credits": 4,
            "subject_type": "BSC",
            "teaching_scheme": {"lecture": 4, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "BSC205",
            "name": "Engineering Physics-II",
            "semester": 2,
            "credits": 2,
            "subject_type": "BSC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 75}
        },
        {
            "code": "BSC206",
            "name": "Engineering Chemistry-II",
            "semester": 2,
            "credits": 2,
            "subject_type": "BSC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 75}
        },
        {
            "code": "AEC201",
            "name": "Professional Communication and Ethics-I",
            "semester": 2,
            "credits": 3,
            "subject_type": "AEC",
            "teaching_scheme": {"lecture": 2, "tutorial": 2, "practical": 0},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "ESC203",
            "name": "Basic Electronics Engineering",
            "semester": 2,
            "credits": 2,
            "subject_type": "ESC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 75}
        },
        {
            "code": "BSL203",
            "name": "Engineering Physics-II Laboratory",
            "semester": 2,
            "credits": 0.5,
            "subject_type": "BSL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 1},
            "examination_scheme": {"total": 25}
        },
        {
            "code": "BSL204",
            "name": "Engineering Chemistry-II Laboratory",
            "semester": 2,
            "credits": 0.5,
            "subject_type": "BSL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 1},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "ESL204",
            "name": "Engineering Graphics Laboratory",
            "semester": 2,
            "credits": 2,
            "subject_type": "ESL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 4},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "ESL205",
            "name": "Programming Laboratory-II (Java)",
            "semester": 2,
            "credits": 2,
            "subject_type": "ESL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 4},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "ESL206",
            "name": "Basic Electronics Engineering Laboratory",
            "semester": 2,
            "credits": 1,
            "subject_type": "ESL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "SEC202",
            "name": "Basic Workshop Practice-II",
            "semester": 2,
            "credits": 1,
            "subject_type": "SEC",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "IKS201",
            "name": "Indian Knowledge System",
            "semester": 2,
            "credits": 2,
            "subject_type": "IKS",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 50}
        },
        
        # ==================== SEMESTER 3 ====================
        {
            "code": "CSPCC301",
            "name": "Engineering Mathematics-III",
            "semester": 3,
            "credits": 4,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 1, "practical": 0},
            "examination_scheme": {"total": 125}
        },
        {
            "code": "CSPCC302",
            "name": "Discrete Structure & Graph Theory",
            "semester": 3,
            "credits": 4,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 1, "practical": 0},
            "examination_scheme": {"total": 125}
        },
        {
            "code": "CSPCC303",
            "name": "Data Structures",
            "semester": 3,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPCC304",
            "name": "Database Management System",
            "semester": 3,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSLBC301",
            "name": "Data Structure Laboratory",
            "semester": 3,
            "credits": 1,
            "subject_type": "LBC",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "CSLBC302",
            "name": "SQL Laboratory",
            "semester": 3,
            "credits": 1,
            "subject_type": "LBC",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "CSSBL301",
            "name": "Python Laboratory",
            "semester": 3,
            "credits": 2,
            "subject_type": "SBL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 4},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSMNP301",
            "name": "Mini Project-1A",
            "semester": 3,
            "credits": 1,
            "subject_type": "MNP",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 3},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "HSS301",
            "name": "Product Design",
            "semester": 3,
            "credits": 2,
            "subject_type": "HSS",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 50}
        },
        
        # ==================== SEMESTER 4 ====================
        {
            "code": "CSPCC405",
            "name": "Engineering Mathematics-IV",
            "semester": 4,
            "credits": 4,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 1, "practical": 0},
            "examination_scheme": {"total": 125}
        },
        {
            "code": "CSPCC406",
            "name": "Design & Analysis of Algorithm",
            "semester": 4,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPCC407",
            "name": "Operating System",
            "semester": 4,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPCC408",
            "name": "Software Engineering",
            "semester": 4,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSLBC403",
            "name": "Design & Analysis of Algorithm Laboratory",
            "semester": 4,
            "credits": 1,
            "subject_type": "LBC",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "CSLBC404",
            "name": "Linux Laboratory",
            "semester": 4,
            "credits": 1,
            "subject_type": "LBC",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "CSLBC405",
            "name": "Software Development Laboratory",
            "semester": 4,
            "credits": 1,
            "subject_type": "LBC",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "CSSBL402",
            "name": "Full stack development Laboratory",
            "semester": 4,
            "credits": 2,
            "subject_type": "SBL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 4},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSMNP402",
            "name": "Mini Project-1B",
            "semester": 4,
            "credits": 1,
            "subject_type": "MNP",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 3},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "VEC402",
            "name": "Environment and Sustainability",
            "semester": 4,
            "credits": 2,
            "subject_type": "VEC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 50}
        },
        
        # ==================== SEMESTER 5 ====================
        {
            "code": "CSPCC509",
            "name": "Theory of Computer Science",
            "semester": 5,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPCC510",
            "name": "Computer Network",
            "semester": 5,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSLBC506",
            "name": "Network Laboratory",
            "semester": 5,
            "credits": 1,
            "subject_type": "LBC",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "CSLBC507",
            "name": "Cloud Computing Laboratory",
            "semester": 5,
            "credits": 1,
            "subject_type": "LBC",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "AEC502",
            "name": "Professional Communication and Ethics-II",
            "semester": 5,
            "credits": 2,
            "subject_type": "AEC",
            "teaching_scheme": {"lecture": 1, "tutorial": 2, "practical": 0},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "CSMNP503",
            "name": "Mini Project-2A",
            "semester": 5,
            "credits": 1,
            "subject_type": "MNP",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 3},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "HSS502",
            "name": "Entrepreneurship",
            "semester": 5,
            "credits": 2,
            "subject_type": "HSS",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 50}
        },
        
        # Semester 5 - Program Electives
        {
            "code": "CSPEC5011",
            "name": "Soft Computing",
            "semester": 5,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC5012",
            "name": "Advanced Database System",
            "semester": 5,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC5013",
            "name": "Cloud Computing Services",
            "semester": 5,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC5014",
            "name": "Cyber Security",
            "semester": 5,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC5015",
            "name": "Computer graphics",
            "semester": 5,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        
        # ==================== SEMESTER 6 ====================
        {
            "code": "CSPCC611",
            "name": "Cryptography & Network Security",
            "semester": 6,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 1, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSLBC608",
            "name": "Cryptography & Network Security Laboratory",
            "semester": 6,
            "credits": 1,
            "subject_type": "LBC",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "CSLBC609",
            "name": "Data Science Laboratory",
            "semester": 6,
            "credits": 1,
            "subject_type": "LBC",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "CSSBL603",
            "name": "Devops Laboratory",
            "semester": 6,
            "credits": 2,
            "subject_type": "SBL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 4},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSMNPG604",
            "name": "Mini Project-2B",
            "semester": 6,
            "credits": 1,
            "subject_type": "MNP",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 3},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "ELC601",
            "name": "Research Methodology",
            "semester": 6,
            "credits": 2,
            "subject_type": "ELC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 50}
        },
        
        # Semester 6 - Program Electives
        {
            "code": "CSPEC6021",
            "name": "Machine Learning",
            "semester": 6,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC6022",
            "name": "Dataware housing & Mining",
            "semester": 6,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC6023",
            "name": "Wireless Technology",
            "semester": 6,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC6024",
            "name": "Ethical Hacking",
            "semester": 6,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC6025",
            "name": "System Programming and Compiler Construction",
            "semester": 6,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        
        # Semester 6 - Liberal Learning Courses
        {
            "code": "LLC6011",
            "name": "Art of Living",
            "semester": 6,
            "credits": 2,
            "subject_type": "LLC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "LLC6012",
            "name": "Yoga and Meditation",
            "semester": 6,
            "credits": 2,
            "subject_type": "LLC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "LLC6013",
            "name": "Health and Wellness",
            "semester": 6,
            "credits": 2,
            "subject_type": "LLC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "LLC6014",
            "name": "Diet and Nutrition",
            "semester": 6,
            "credits": 2,
            "subject_type": "LLC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "LLC6015",
            "name": "Personality Development",
            "semester": 6,
            "credits": 2,
            "subject_type": "LLC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 50}
        },
        
        # ==================== SEMESTER 7 ====================
        {
            "code": "CSPCC712",
            "name": "Artificial Intelligence",
            "semester": 7,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSLBC710",
            "name": "Artificial Intelligence Laboratory",
            "semester": 7,
            "credits": 1,
            "subject_type": "LBC",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "CSLBC711",
            "name": "Data analytics & Visualization Laboratory",
            "semester": 7,
            "credits": 1,
            "subject_type": "LBC",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "CSMJP701",
            "name": "Major Project-A",
            "semester": 7,
            "credits": 2,
            "subject_type": "MJP",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 6},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "HSS703",
            "name": "Financial Planning",
            "semester": 7,
            "credits": 2,
            "subject_type": "HSS",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 50}
        },
        
        # Semester 7 - Program Electives III
        {
            "code": "CSPEC7031",
            "name": "Natural Language Processing",
            "semester": 7,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC7032",
            "name": "Big Data Analytics",
            "semester": 7,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC7033",
            "name": "Edge Computing",
            "semester": 7,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC7034",
            "name": "Digital Forensics",
            "semester": 7,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC7035",
            "name": "Information Retrieval System",
            "semester": 7,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        
        # Semester 7 - Program Electives IV
        {
            "code": "CSPEC7041",
            "name": "Foundation Models & Generative AI",
            "semester": 7,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC7042",
            "name": "Time Series Analysis",
            "semester": 7,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC7043",
            "name": "Quantum Computing",
            "semester": 7,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC7044",
            "name": "Human Computer Interaction",
            "semester": 7,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        
        # Semester 7 - Open Electives I
        {
            "code": "OEC7011",
            "name": "Product Lifecycle Management",
            "semester": 7,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC7012",
            "name": "Reliability Engineering",
            "semester": 7,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC7013",
            "name": "Management Information System",
            "semester": 7,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC7014",
            "name": "Design of Experiments",
            "semester": 7,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC7015",
            "name": "Operation Research",
            "semester": 7,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC7016",
            "name": "Cyber Security and Laws",
            "semester": 7,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC7017",
            "name": "Disaster Management and Mitigation Measures",
            "semester": 7,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC7018",
            "name": "Energy Audit and Management",
            "semester": 7,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC7019",
            "name": "Development Engineering",
            "semester": 7,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        
        # ==================== SEMESTER 8 ====================
        {
            "code": "CSMJP802",
            "name": "Major Project-B",
            "semester": 8,
            "credits": 4,
            "subject_type": "MJP",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 12},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "INT801",
            "name": "Internship",
            "semester": 8,
            "credits": 8,
            "subject_type": "INT",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        
        # Semester 8 - Program Electives V
        {
            "code": "CSPEC8051",
            "name": "Responsible & Safe AI Systems",
            "semester": 8,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC8052",
            "name": "Recommender System",
            "semester": 8,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC8053",
            "name": "High Performance Computing",
            "semester": 8,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC8054",
            "name": "Cyber Physical Systems",
            "semester": 8,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSPEC8055",
            "name": "Blockchain Technology",
            "semester": 8,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        
        # Semester 8 - Open Electives II
        {
            "code": "OEC8021",
            "name": "Project Management",
            "semester": 8,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC8022",
            "name": "Finance Management",
            "semester": 8,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC8023",
            "name": "Entrepreneurship Development and Management",
            "semester": 8,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC8024",
            "name": "Human Resource Management",
            "semester": 8,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC8025",
            "name": "Professional Ethics and CSR",
            "semester": 8,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC8026",
            "name": "Circular Economy",
            "semester": 8,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC8027",
            "name": "IPR and Patenting",
            "semester": 8,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC8028",
            "name": "Digital Business Management",
            "semester": 8,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "OEC8029",
            "name": "Environmental Management",
            "semester": 8,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        
        # ==================== MDM COURSES ====================
        {
            "code": "CSMDM301",
            "name": "Data Structures and Algorithms",
            "semester": 3,
            "credits": 3,
            "subject_type": "MDM",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSMDM402",
            "name": "Database Management System",
            "semester": 4,
            "credits": 3,
            "subject_type": "MDM",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSMDM503",
            "name": "Cloud Computing",
            "semester": 5,
            "credits": 3,
            "subject_type": "MDM",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        {
            "code": "CSMDL501",
            "name": "Machine Learning Laboratory",
            "semester": 5,
            "credits": 1,
            "subject_type": "MDL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
        {
            "code": "CSMDM604",
            "name": "Soft Computing",
            "semester": 6,
            "credits": 4,
            "subject_type": "MDM",
            "teaching_scheme": {"lecture": 4, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
    ]
    
    result = await db.subjects.insert_many(all_subjects)
    print(f"✅ Inserted {len(result.inserted_ids)} subjects")
    
    client.close()
    
    # Print summary
    print("\n📊 Subject Distribution:")
    for sem in range(1, 9):
        count = len([s for s in all_subjects if s["semester"] == sem])
        print(f"   Semester {sem}: {count} subjects")
    
    print(f"\n✅ Total subjects: {len(all_subjects)}")


if __name__ == "__main__":
    asyncio.run(populate_all_subjects())