# populate_all_subjects.py (save in project root)
"""
Populate all CS&E subjects from curriculum
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os


async def populate_subjects():
    # Connect to MongoDB
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client["academic_advisor"]
    
    print("🔄 Populating all subjects...")
    
    # Clear existing subjects
    await db.subjects.delete_many({})
    
    # All subjects data
    all_subjects = [
        # ============ SEMESTER 1 ============
        {
            "code": "BSC101",
            "name": "Engineering Mathematics I",
            "semester": 1,
            "credits": 4,
            "subject_type": "BSC",
            "teaching_scheme": {"lecture": 4, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100},
            "description": "Covers calculus, linear algebra, and differential equations for engineering applications",
            "units": [
                {"unit_number": 1, "title": "Differential Calculus", "topics": ["Limits", "Continuity", "Differentiation"]},
                {"unit_number": 2, "title": "Integral Calculus", "topics": ["Integration", "Applications"]},
                {"unit_number": 3, "title": "Linear Algebra", "topics": ["Matrices", "Eigenvalues", "Eigenvectors"]},
                {"unit_number": 4, "title": "Differential Equations", "topics": ["First Order", "Second Order", "Applications"]},
            ]
        },
        {
            "code": "BSC102",
            "name": "Engineering Physics-I",
            "semester": 1,
            "credits": 2,
            "subject_type": "BSC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 75},
            "description": "Fundamentals of physics including mechanics, waves, and optics"
        },
        {
            "code": "BSC103",
            "name": "Engineering Chemistry-I",
            "semester": 1,
            "credits": 2,
            "subject_type": "BSC",
            "teaching_scheme": {"lecture": 2, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 75},
            "description": "Basic chemistry concepts for engineering applications"
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
            "code": "ESL103",
            "name": "Programming Laboratory-I (C)",
            "semester": 1,
            "credits": 2,
            "subject_type": "ESL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 4},
            "examination_scheme": {"total": 100},
            "description": "C programming fundamentals and problem solving"
        },
        
        # ============ SEMESTER 2 ============
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
            "code": "ESL205",
            "name": "Programming Laboratory-II (Java)",
            "semester": 2,
            "credits": 2,
            "subject_type": "ESL",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 4},
            "examination_scheme": {"total": 100},
            "description": "Object-oriented programming with Java"
        },
        
        # ============ SEMESTER 3 (CS CORE) ============
        {
            "code": "CSPCC301",
            "name": "Engineering Mathematics-III",
            "semester": 3,
            "credits": 4,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 1, "practical": 0},
            "examination_scheme": {"total": 125},
            "description": "Advanced mathematics including probability, statistics, and numerical methods"
        },
        {
            "code": "CSPCC302",
            "name": "Discrete Structure & Graph Theory",
            "semester": 3,
            "credits": 4,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 1, "practical": 0},
            "examination_scheme": {"total": 125},
            "description": "Mathematical foundations for computer science including sets, relations, graphs"
        },
        {
            "code": "CSPCC303",
            "name": "Data Structures",
            "semester": 3,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100},
            "description": "Linear and non-linear data structures, algorithms, and their applications",
            "units": [
                {"unit_number": 1, "title": "Arrays and Linked Lists", "topics": ["Arrays", "Linked Lists", "Stacks", "Queues"]},
                {"unit_number": 2, "title": "Trees", "topics": ["Binary Trees", "BST", "AVL Trees", "B-Trees"]},
                {"unit_number": 3, "title": "Graphs", "topics": ["Graph Representation", "Traversals", "Shortest Path"]},
                {"unit_number": 4, "title": "Hashing and Sorting", "topics": ["Hash Tables", "Sorting Algorithms"]},
            ]
        },
        {
            "code": "CSPCC304",
            "name": "Database Management System",
            "semester": 3,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100},
            "description": "Relational database concepts, SQL, normalization, transactions, and NoSQL",
            "units": [
                {"unit_number": 1, "title": "Database Concepts", "topics": ["ER Model", "Relational Model", "SQL Basics"]},
                {"unit_number": 2, "title": "SQL and Normalization", "topics": ["Advanced SQL", "Normalization", "Database Design"]},
                {"unit_number": 3, "title": "Transactions", "topics": ["ACID Properties", "Concurrency Control", "Recovery"]},
                {"unit_number": 4, "title": "Advanced Topics", "topics": ["Indexing", "Query Optimization", "NoSQL"]},
            ]
        },
        
        # ============ SEMESTER 4 ============
        {
            "code": "CSPCC406",
            "name": "Design & Analysis of Algorithm",
            "semester": 4,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100},
            "description": "Algorithm design paradigms, complexity analysis, and optimization techniques"
        },
        {
            "code": "CSPCC407",
            "name": "Operating System",
            "semester": 4,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100},
            "description": "OS concepts including process management, memory management, file systems",
            "units": [
                {"unit_number": 1, "title": "Process Management", "topics": ["Process", "Thread", "CPU Scheduling"]},
                {"unit_number": 2, "title": "Synchronization", "topics": ["Deadlock", "Mutex", "Semaphore"]},
                {"unit_number": 3, "title": "Memory Management", "topics": ["Paging", "Segmentation", "Virtual Memory"]},
                {"unit_number": 4, "title": "File Systems", "topics": ["File Organization", "Directory Structure", "Protection"]},
            ]
        },
        {
            "code": "CSPCC408",
            "name": "Software Engineering",
            "semester": 4,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100},
            "description": "Software development life cycle, agile methods, testing, and project management"
        },
        
        # ============ SEMESTER 5 ============
        {
            "code": "CSPCC509",
            "name": "Theory of Computer Science",
            "semester": 5,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100},
            "description": "Automata theory, formal languages, and computability"
        },
        {
            "code": "CSPCC510",
            "name": "Computer Network",
            "semester": 5,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100},
            "description": "Network protocols, OSI model, TCP/IP, routing, and network security",
            "units": [
                {"unit_number": 1, "title": "Network Fundamentals", "topics": ["OSI Model", "TCP/IP", "Network Devices"]},
                {"unit_number": 2, "title": "Data Link Layer", "topics": ["Error Detection", "Flow Control", "MAC Protocols"]},
                {"unit_number": 3, "title": "Network Layer", "topics": ["IP Addressing", "Routing Algorithms", "IPv4/IPv6"]},
                {"unit_number": 4, "title": "Transport & Application Layer", "topics": ["TCP", "UDP", "HTTP", "DNS"]},
            ]
        },
        
        # Program Electives Sem 5
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
        
        # ============ SEMESTER 6 ============
        {
            "code": "CSPCC611",
            "name": "Cryptography & Network Security",
            "semester": 6,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 1, "practical": 0},
            "examination_scheme": {"total": 100},
            "description": "Encryption, digital signatures, security protocols, and network security"
        },
        
        # Program Electives Sem 6
        {
            "code": "CSPEC6021",
            "name": "Machine Learning",
            "semester": 6,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100},
            "description": "Supervised, unsupervised learning, neural networks, and ML applications"
        },
        {
            "code": "CSPEC6022",
            "name": "Data Warehousing & Mining",
            "semester": 6,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        
        # ============ SEMESTER 7 ============
        {
            "code": "CSPCC712",
            "name": "Artificial Intelligence",
            "semester": 7,
            "credits": 3,
            "subject_type": "PCC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100},
            "description": "AI fundamentals, search algorithms, knowledge representation, expert systems"
        },
        
        # Program Electives Sem 7
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
        
        # Open Electives
        {
            "code": "OEC7016",
            "name": "Cyber Security and Laws",
            "semester": 7,
            "credits": 3,
            "subject_type": "OEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
        
        # ============ SEMESTER 8 ============
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
            "code": "CSPEC8055",
            "name": "Blockchain Technology",
            "semester": 8,
            "credits": 3,
            "subject_type": "PEC",
            "teaching_scheme": {"lecture": 3, "tutorial": 0, "practical": 0},
            "examination_scheme": {"total": 100}
        },
    ]
    
    # Insert subjects
    result = await db.subjects.insert_many(all_subjects)
    print(f"✅ Inserted {len(result.inserted_ids)} subjects")
    
    # Add Lab courses
    lab_subjects = [
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
            "code": "CSLBC506",
            "name": "Network Laboratory",
            "semester": 5,
            "credits": 1,
            "subject_type": "LBC",
            "teaching_scheme": {"lecture": 0, "tutorial": 0, "practical": 2},
            "examination_scheme": {"total": 50}
        },
    ]
    
    result2 = await db.subjects.insert_many(lab_subjects)
    print(f"✅ Inserted {len(result2.inserted_ids)} lab subjects")
    
    client.close()
    print("\n✅ All subjects populated successfully!")
    
    # Show summary
    print("\n📊 Summary:")
    print(f"Total subjects added: {len(all_subjects) + len(lab_subjects)}")


if __name__ == "__main__":
    asyncio.run(populate_subjects())