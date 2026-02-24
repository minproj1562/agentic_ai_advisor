"""
Comprehensive data seeding script for the Academic Chatbot using MongoDB with Beanie ODM.
Run this to populate all necessary data for dynamic responses based on FCRIT CSE syllabus.
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, Link, PydanticObjectId

from app.core.config import settings
from app.models.syllabus import (
    Department, Subject, SubjectUnit, Topic,
    Faculty, FacultySubject, CareerPath,
    ProgramElective, OpenElective, LiberalLearningCourse,
    Abbreviation, CreditStructure, MDMCourse
)


async def seed_abbreviations():
    """Seed abbreviation data from syllabus"""
    
    abbreviations = [
        {"code": "AEC", "full_form": "Ability Enhancement Course", "description": "Courses designed to enhance communication and professional skills"},
        {"code": "AU", "full_form": "Audit Course", "description": "Courses taken without credit, recorded on grade sheet"},
        {"code": "BSC", "full_form": "Basic Science Course", "description": "Mathematics and basic science foundation courses"},
        {"code": "BSL", "full_form": "Basic Science Laboratory Course", "description": "Laboratory courses for basic sciences"},
        {"code": "ELC", "full_form": "Experiential Learning Course", "description": "Hands-on learning experiences including projects"},
        {"code": "ESC", "full_form": "Engineering Sciences Course", "description": "Fundamental engineering courses"},
        {"code": "ESL", "full_form": "Engineering Sciences Laboratory Course", "description": "Laboratory courses for engineering sciences"},
        {"code": "HMC", "full_form": "Honours or Minor Core Course", "description": "Core courses for honours/minor specialization"},
        {"code": "HML", "full_form": "Honours or Minor Laboratory", "description": "Laboratory courses for honours/minor"},
        {"code": "HMP", "full_form": "Honours or Minor Mini Project", "description": "Project work for honours/minor"},
        {"code": "HSS", "full_form": "Humanities Social Sciences and Management Course", "description": "Courses in humanities and management"},
        {"code": "IKS", "full_form": "Indian Knowledge System Course", "description": "Courses on Indian knowledge systems"},
        {"code": "INT", "full_form": "Internship", "description": "Industrial or research internship"},
        {"code": "L", "full_form": "Lecture", "description": "Theoretical instruction hours"},
        {"code": "LBC", "full_form": "Laboratory Course", "description": "Practical laboratory sessions"},
        {"code": "LLC", "full_form": "Liberal Learning Course", "description": "Courses for holistic development"},
        {"code": "MDM", "full_form": "Multidisciplinary Minor Course", "description": "Minor courses from other disciplines"},
        {"code": "MDL", "full_form": "Multidisciplinary Laboratory Course", "description": "Laboratory courses for multidisciplinary minor"},
        {"code": "MJP", "full_form": "Major Project", "description": "Capstone project work"},
        {"code": "MNP", "full_form": "Mini Project", "description": "Small-scale project work"},
        {"code": "OEC", "full_form": "Open Elective Course", "description": "Elective courses open to all students"},
        {"code": "P", "full_form": "Practical", "description": "Practical session hours"},
        {"code": "PCC", "full_form": "Program Core Course", "description": "Core courses in the program"},
        {"code": "PEC", "full_form": "Program Elective Course", "description": "Elective courses within the program"},
        {"code": "RPC", "full_form": "Research Project Coursework", "description": "Research-oriented project work"},
        {"code": "RPR", "full_form": "Research Project", "description": "Research project"},
        {"code": "SBL", "full_form": "Skill Based Laboratory", "description": "Laboratory courses for skill development"},
        {"code": "SEC", "full_form": "Skill Enhancement Course", "description": "Courses for enhancing practical skills"},
        {"code": "T", "full_form": "Tutorial", "description": "Tutorial session hours"},
        {"code": "VEC", "full_form": "Value Education Course", "description": "Courses on values and ethics"}
    ]
    
    created = []
    for abbr_data in abbreviations:
        existing = await Abbreviation.find_one({"code": abbr_data["code"]})
        if not existing:
            abbr = Abbreviation(**abbr_data)
            await abbr.insert()
            created.append(abbr_data["code"])
    
    print(f"✅ Created/Updated {len(created)} abbreviations")
    return created


async def seed_departments() -> Dict[str, PydanticObjectId]:
    """Seed department data"""
    
    departments = [
        {
            "code": "CSE",
            "name": "Computer Science and Engineering",
            "description": "Department focusing on computer science fundamentals, software engineering, and emerging technologies. Offers B.Tech program with specializations in AI/ML, Cybersecurity, and Data Science.",
            "hod_name": "Dr. Ramesh Sharma",
            "vision": "To be a center of excellence in computer science education and research, producing globally competent professionals with ethical values.",
            "mission": [
                "Provide quality education in computer science with industry-aligned curriculum",
                "Foster research and innovation in emerging technologies",
                "Develop professionals with strong ethical values and social responsibility"
            ],
            "programs_offered": ["B.Tech Computer Science and Engineering"],
            "duration": "4 years",
            "total_seats": 120
        },
        {
            "code": "IT",
            "name": "Information Technology",
            "description": "Department focusing on information systems, web technologies, and IT infrastructure.",
            "hod_name": "Dr. Priya Patel",
            "vision": "To produce competent IT professionals capable of developing innovative solutions for industry and society.",
            "mission": [
                "Impart strong theoretical and practical knowledge in IT",
                "Encourage entrepreneurship and innovation",
                "Inculcate professional ethics and lifelong learning skills"
            ],
            "programs_offered": ["B.Tech Information Technology"],
            "duration": "4 years",
            "total_seats": 60
        }
    ]
    
    created_depts = {}
    for dept_data in departments:
        existing = await Department.find_one({"code": dept_data["code"]})
        if existing:
            created_depts[dept_data["code"]] = existing.id
        else:
            dept = Department(**dept_data)
            await dept.insert()
            created_depts[dept_data["code"]] = dept.id
    
    print(f"✅ Created/Updated {len(created_depts)} departments")
    return created_depts


async def seed_credit_structure():
    """Seed credit structure from syllabus"""
    
    credit_data = {
        "program": "B.Tech Computer Science and Engineering",
        "total_credits": 166,
        "min_credits_per_semester": 12,
        "max_credits_per_semester": 28,
        "semester_wise_distribution": {
            "1": {"total": 21, "breakdown": {
                "BSC": 8, "BSL": 1, "ESC": 5, "ESL": 4, 
                "SEC": 1, "VEC": 2
            }},
            "2": {"total": 22, "breakdown": {
                "BSC": 8, "BSL": 1, "AEC": 2, "ESC": 2,
                "ESL": 5, "SEC": 1, "IKS": 2
            }},
            "3": {"total": 24, "breakdown": {
                "PCC": 14, "LBC": 2, "SBL": 2, "MNP": 1, "HSS": 2, "MDM": 3
            }},
            "4": {"total": 24, "breakdown": {
                "PCC": 13, "LBC": 3, "SBL": 2, "MNP": 1, "VEC": 2, "MDM": 3
            }},
            "5": {"total": 20, "breakdown": {
                "PCC": 6, "PEC": 3, "LBC": 2, "MDL": 1, "AEC": 2,
                "MNP": 1, "HSS": 2, "MDM": 3
            }},
            "6": {"total": 19, "breakdown": {
                "PCC": 3, "PEC": 3, "LBC": 2, "SBL": 2,
                "MNP": 1, "ELC": 2, "LLC": 2, "MDM": 4
            }},
            "7": {"total": 18, "breakdown": {
                "PCC": 3, "PEC": 6, "OEC": 3, "LBC": 2,
                "MJP": 2, "HSS": 2
            }},
            "8": {"total": 18, "breakdown": {
                "PEC": 3, "OEC": 3, "MJP": 4, "INT": 8
            }}
        },
        "category_wise_total": {
            "BSC": 16, "BSL": 2, "ESC": 7, "ESL": 9, "PCC": 39,
            "LBC": 11, "PEC": 15, "MDM": 13, "MDL": 1, "OEC": 6,
            "SEC": 2, "SBL": 6, "AEC": 5, "HSS": 6, "IKS": 2,
            "VEC": 4, "ELC": 2, "MNP": 4, "MJP": 6, "INT": 8,
            "LLC": 2
        }
    }
    
    existing = await CreditStructure.find_one({"program": credit_data["program"]})
    if existing:
        for key, value in credit_data.items():
            setattr(existing, key, value)
        await existing.save()
    else:
        structure = CreditStructure(**credit_data)
        await structure.insert()
    
    print(f"✅ Credit structure seeded")
    return credit_data


async def seed_subjects(dept_ids: Dict[str, PydanticObjectId]) -> Dict[str, PydanticObjectId]:
    """Seed subject data with full syllabus from PDF"""
    
    subjects_data = [
        # ========== Semester 3 ==========
        {
            "code": "CSPCC301",
            "name": "Engineering Mathematics-III",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 3,
            "credits": 4,
            "subject_type": "core",
            "category": "PCC",
            "teaching_scheme": {"L": 3, "T": 1, "P": 0},
            "description": "Advanced mathematical concepts including Laplace transforms, Fourier series, complex analysis, and probability distributions.",
            "learning_outcomes": [
                "Apply Laplace transforms to solve differential equations",
                "Analyze functions using Fourier series",
                "Apply complex analysis techniques",
                "Use probability distributions for engineering problems"
            ],
            "reference_books": [
                "Advanced Engineering Mathematics - Erwin Kreyszig",
                "Higher Engineering Mathematics - B.S. Grewal",
                "Complex Variables - Churchill"
            ],
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "total": 125,
                "tutorial": 25
            }
        },
        {
            "code": "CSPCC302",
            "name": "Discrete Structure & Graph Theory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 3,
            "credits": 4,
            "subject_type": "core",
            "category": "PCC",
            "teaching_scheme": {"L": 3, "T": 1, "P": 0},
            "description": "Study of discrete mathematical structures including sets, relations, functions, logic, and graph theory.",
            "learning_outcomes": [
                "Apply mathematical logic for problem solving",
                "Analyze combinatorial structures",
                "Apply graph theory concepts",
                "Use algebraic structures in computing"
            ],
            "reference_books": [
                "Discrete Mathematics and Its Applications - Kenneth Rosen",
                "Elements of Discrete Mathematics - C.L. Liu",
                "Graph Theory - Narsingh Deo"
            ],
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "total": 125,
                "tutorial": 25
            }
        },
        {
            "code": "CSPCC303",
            "name": "Data Structures",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 3,
            "credits": 3,
            "subject_type": "core",
            "category": "PCC",
            "teaching_scheme": {"L": 3, "T": 0, "P": 0},
            "description": "Fundamental data structures and their applications in problem solving.",
            "learning_outcomes": [
                "Understand and implement various data structures",
                "Analyze time and space complexity",
                "Apply appropriate data structures for problem solving",
                "Compare different data structures for given scenarios"
            ],
            "reference_books": [
                "Data Structures Using C - Reema Thareja",
                "Introduction to Algorithms - CLRS",
                "Data Structures and Algorithms Made Easy - Narasimha Karumanchi"
            ],
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "total": 100
            },
            "units": [
                {
                    "unit_number": 1,
                    "title": "Introduction to Data Structures",
                    "topics": [
                        {
                            "name": "Arrays",
                            "definition": "An array is a collection of elements stored at contiguous memory locations, where each element can be accessed using an index.",
                            "key_points": [
                                "Fixed size collection of elements",
                                "O(1) access time using index",
                                "Contiguous memory allocation",
                                "Static vs Dynamic arrays"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "easy",
                            "keywords": ["array", "index", "contiguous", "static", "dynamic"]
                        },
                        {
                            "name": "Linked Lists",
                            "definition": "A linked list is a linear data structure where elements are stored in nodes, and each node points to the next node in the sequence.",
                            "key_points": [
                                "Dynamic size - can grow or shrink",
                                "Types: Singly, Doubly, Circular",
                                "Insertion/Deletion: O(1) at known position",
                                "Access: O(n) - no direct indexing"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "medium",
                            "keywords": ["linked list", "node", "pointer", "singly", "doubly", "circular"]
                        }
                    ],
                    "keywords": ["arrays", "linked lists", "basic structures"]
                },
                {
                    "unit_number": 2,
                    "title": "Stacks and Queues",
                    "topics": [
                        {
                            "name": "Stack",
                            "definition": "A stack is a linear data structure that follows the Last-In-First-Out (LIFO) principle, where elements are added and removed from the same end called the top.",
                            "key_points": [
                                "LIFO (Last In First Out) principle",
                                "Operations: push, pop, peek/top",
                                "Applications: Expression evaluation, Backtracking",
                                "Can be implemented using array or linked list"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "easy",
                            "keywords": ["stack", "LIFO", "push", "pop", "top"]
                        },
                        {
                            "name": "Queue",
                            "definition": "A queue is a linear data structure that follows the First-In-First-Out (FIFO) principle, where elements are added at the rear and removed from the front.",
                            "key_points": [
                                "FIFO (First In First Out) principle",
                                "Operations: enqueue, dequeue, front, rear",
                                "Types: Simple, Circular, Priority, Deque",
                                "Applications: CPU scheduling, BFS"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "easy",
                            "keywords": ["queue", "FIFO", "enqueue", "dequeue", "circular queue"]
                        }
                    ],
                    "keywords": ["stack", "queue", "LIFO", "FIFO"]
                },
                {
                    "unit_number": 3,
                    "title": "Trees",
                    "topics": [
                        {
                            "name": "Binary Tree",
                            "definition": "A binary tree is a hierarchical data structure where each node has at most two children, referred to as left child and right child.",
                            "key_points": [
                                "Each node has at most 2 children",
                                "Types: Full, Complete, Perfect, Balanced",
                                "Traversals: Inorder, Preorder, Postorder, Level-order",
                                "Height = log₂(n) for balanced tree"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "medium",
                            "keywords": ["binary tree", "traversal", "inorder", "preorder", "postorder"]
                        },
                        {
                            "name": "Binary Search Tree (BST)",
                            "definition": "A Binary Search Tree is a binary tree where the left subtree contains only nodes with values less than the parent, and the right subtree contains only nodes with values greater than the parent.",
                            "key_points": [
                                "Left child < Parent < Right child",
                                "Inorder traversal gives sorted sequence",
                                "Search, Insert, Delete: O(log n) average, O(n) worst",
                                "Self-balancing variants: AVL, Red-Black Tree"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "medium",
                            "keywords": ["BST", "binary search tree", "search", "balanced"]
                        }
                    ],
                    "keywords": ["tree", "binary tree", "BST", "traversal"]
                },
                {
                    "unit_number": 4,
                    "title": "Graphs",
                    "topics": [
                        {
                            "name": "Graph Representation",
                            "definition": "A graph is a non-linear data structure consisting of vertices (nodes) and edges that connect pairs of vertices.",
                            "key_points": [
                                "Types: Directed, Undirected, Weighted",
                                "Representations: Adjacency Matrix, Adjacency List",
                                "Matrix: O(V²) space, O(1) edge lookup",
                                "List: O(V+E) space, efficient for sparse graphs"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "medium",
                            "keywords": ["graph", "vertex", "edge", "adjacency matrix", "adjacency list"]
                        },
                        {
                            "name": "Graph Traversal",
                            "definition": "Graph traversal refers to the process of visiting all vertices in a graph systematically.",
                            "key_points": [
                                "BFS: Level-by-level, uses Queue, O(V+E)",
                                "DFS: Depth-first, uses Stack/Recursion, O(V+E)",
                                "BFS finds shortest path in unweighted graphs",
                                "DFS used for cycle detection, topological sort"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "medium",
                            "keywords": ["BFS", "DFS", "breadth first", "depth first", "traversal"]
                        }
                    ],
                    "keywords": ["graph", "BFS", "DFS", "traversal"]
                },
                {
                    "unit_number": 5,
                    "title": "Sorting and Searching",
                    "topics": [
                        {
                            "name": "Sorting Algorithms",
                            "definition": "Sorting algorithms arrange elements in a specific order (ascending or descending) based on comparison or distribution.",
                            "key_points": [
                                "Comparison sorts: Bubble, Selection, Insertion, Merge, Quick, Heap",
                                "Non-comparison: Counting, Radix, Bucket",
                                "Quick Sort: Average O(n log n), Worst O(n²)",
                                "Merge Sort: Always O(n log n), stable, extra space"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "medium",
                            "keywords": ["sorting", "quick sort", "merge sort", "bubble sort", "heap sort"]
                        },
                        {
                            "name": "Searching Algorithms",
                            "definition": "Searching algorithms are used to locate specific elements within a data structure.",
                            "key_points": [
                                "Linear Search: O(n), works on unsorted data",
                                "Binary Search: O(log n), requires sorted data",
                                "Hash-based: O(1) average with hash tables",
                                "Binary search can be iterative or recursive"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "easy",
                            "keywords": ["searching", "binary search", "linear search", "hash"]
                        }
                    ],
                    "keywords": ["sorting", "searching", "algorithms", "complexity"]
                }
            ]
        },
        {
            "code": "CSPCC304",
            "name": "Database Management System",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 3,
            "credits": 3,
            "subject_type": "core",
            "category": "PCC",
            "teaching_scheme": {"L": 3, "T": 0, "P": 0},
            "description": "Study of database concepts, design, and implementation including SQL and transaction management.",
            "learning_outcomes": [
                "Design and implement relational databases",
                "Write complex SQL queries",
                "Apply normalization techniques",
                "Understand transaction management"
            ],
            "reference_books": [
                "Database System Concepts - Silberschatz, Korth, Sudarshan",
                "Fundamentals of Database Systems - Elmasri, Navathe",
                "Database Management Systems - Raghu Ramakrishnan"
            ],
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "total": 100
            }
        },
        {
            "code": "CSLBC301",
            "name": "Data Structure Laboratory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 3,
            "credits": 1,
            "subject_type": "lab",
            "category": "LBC",
            "teaching_scheme": {"L": 0, "T": 0, "P": 2},
            "description": "Implementation of various data structures using programming languages.",
            "examination_scheme": {
                "continuous_assessment": 25,
                "end_sem_exam": 25,
                "total": 50
            }
        },
        {
            "code": "CSLBC302",
            "name": "SQL Laboratory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 3,
            "credits": 1,
            "subject_type": "lab",
            "category": "LBC",
            "teaching_scheme": {"L": 0, "T": 0, "P": 2},
            "description": "Practical implementation of SQL queries and database operations.",
            "examination_scheme": {
                "continuous_assessment": 25,
                "end_sem_exam": 25,
                "total": 50
            }
        },
        {
            "code": "CSSBL301",
            "name": "Python Laboratory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 3,
            "credits": 2,
            "subject_type": "lab",
            "category": "SBL",
            "teaching_scheme": {"L": 0, "T": 0, "P": 4},
            "description": "Practical implementation of Python programming concepts.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 50,
                "total": 100
            }
        },
        {
            "code": "CSMNP301",
            "name": "Mini Project-1A",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 3,
            "credits": 1,
            "subject_type": "project",
            "category": "MNP",
            "teaching_scheme": {"L": 0, "T": 0, "P": 3},
            "description": "First part of mini project in semester 3.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 0,
                "total": 50
            }
        },
        {
            "code": "HSS301",
            "name": "Product Design",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 3,
            "credits": 2,
            "subject_type": "humanities",
            "category": "HSS",
            "teaching_scheme": {"L": 2, "T": 0, "P": 0},
            "description": "Introduction to product design principles and methodologies.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 0,
                "total": 50
            }
        },
        # ========== Semester 4 ==========
        {
            "code": "CSPCC405",
            "name": "Engineering Mathematics-IV",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 4,
            "credits": 4,
            "subject_type": "core",
            "category": "PCC",
            "teaching_scheme": {"L": 3, "T": 1, "P": 0},
            "description": "Advanced mathematical concepts including numerical methods, optimization, and probability.",
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "tutorial": 25,
                "total": 125
            }
        },
        {
            "code": "CSPCC406",
            "name": "Design & Analysis of Algorithm",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 4,
            "credits": 3,
            "subject_type": "core",
            "category": "PCC",
            "teaching_scheme": {"L": 3, "T": 0, "P": 0},
            "description": "Study of algorithm design techniques and complexity analysis.",
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "total": 100
            }
        },
        {
            "code": "CSPCC407",
            "name": "Operating System",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 4,
            "credits": 3,
            "subject_type": "core",
            "category": "PCC",
            "teaching_scheme": {"L": 3, "T": 0, "P": 0},
            "description": "Study of operating system concepts, process management, memory management, and file systems.",
            "learning_outcomes": [
                "Understand OS architecture and functions",
                "Analyze process scheduling algorithms",
                "Implement synchronization mechanisms",
                "Design memory management strategies"
            ],
            "reference_books": [
                "Operating System Concepts - Silberschatz, Galvin, Gagne",
                "Modern Operating Systems - Andrew Tanenbaum",
                "Operating Systems: Internals and Design Principles - William Stallings"
            ],
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "total": 100
            },
            "units": [
                {
                    "unit_number": 1,
                    "title": "Introduction to Operating Systems",
                    "topics": [
                        {
                            "name": "Operating System Basics",
                            "definition": "An Operating System (OS) is system software that manages computer hardware, software resources, and provides common services for computer programs.",
                            "key_points": [
                                "Acts as intermediary between user and hardware",
                                "Functions: Process, Memory, File, I/O management",
                                "Types: Batch, Time-sharing, Distributed, Real-time",
                                "Components: Kernel, Shell, File System"
                            ],
                            "exam_frequency": "medium",
                            "difficulty_level": "easy",
                            "keywords": ["operating system", "OS", "kernel", "shell", "system software"]
                        },
                        {
                            "name": "System Calls",
                            "definition": "System calls provide the interface between a running program and the operating system, allowing user-level processes to request services from the kernel.",
                            "key_points": [
                                "Bridge between user mode and kernel mode",
                                "Categories: Process, File, Device, Information, Communication",
                                "Examples: fork(), exec(), open(), read(), write()",
                                "Invoked using software interrupt (trap)"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "medium",
                            "keywords": ["system call", "kernel", "trap", "fork", "exec"]
                        }
                    ],
                    "keywords": ["OS basics", "system calls", "kernel"]
                },
                {
                    "unit_number": 2,
                    "title": "Process Management",
                    "topics": [
                        {
                            "name": "Process",
                            "definition": "A process is a program in execution. It includes the program code, current activity (program counter), stack, data section, and heap.",
                            "key_points": [
                                "Process States: New, Ready, Running, Waiting, Terminated",
                                "PCB stores process information",
                                "Context switching saves/restores process state",
                                "Process vs Thread: Thread shares address space"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "medium",
                            "keywords": ["process", "PCB", "process state", "context switch"]
                        },
                        {
                            "name": "CPU Scheduling",
                            "definition": "CPU Scheduling is the process of determining which process runs on the CPU at any given time, maximizing CPU utilization and throughput.",
                            "key_points": [
                                "FCFS: Simple, non-preemptive, convoy effect",
                                "SJF: Optimal average waiting time, starvation possible",
                                "Round Robin: Time quantum based, good response time",
                                "Priority: Can cause starvation, use aging to prevent"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "medium",
                            "keywords": ["scheduling", "FCFS", "SJF", "round robin", "priority"]
                        }
                    ],
                    "keywords": ["process", "scheduling", "CPU"]
                },
                {
                    "unit_number": 3,
                    "title": "Process Synchronization",
                    "topics": [
                        {
                            "name": "Critical Section Problem",
                            "definition": "The critical section problem involves designing a protocol that processes can use to cooperate, ensuring that when one process is executing in its critical section, no other process is allowed to execute in its critical section.",
                            "key_points": [
                                "Requirements: Mutual Exclusion, Progress, Bounded Waiting",
                                "Race condition occurs without proper synchronization",
                                "Solutions: Peterson's, Hardware support, Semaphores",
                                "Entry and Exit sections control access"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "medium",
                            "keywords": ["critical section", "race condition", "mutual exclusion"]
                        },
                        {
                            "name": "Semaphore",
                            "definition": "A semaphore is a synchronization tool that provides a way for processes to synchronize their activities by using two atomic operations: wait (P) and signal (V).",
                            "key_points": [
                                "Binary Semaphore: Value is 0 or 1 (like mutex)",
                                "Counting Semaphore: Can have any non-negative value",
                                "wait(S): If S>0, decrement; else block",
                                "signal(S): Increment S, wake up blocked process"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "medium",
                            "keywords": ["semaphore", "wait", "signal", "P", "V", "synchronization"]
                        },
                        {
                            "name": "Mutex",
                            "definition": "A mutex (mutual exclusion) is a locking mechanism used to synchronize access to a resource, ensuring that only one thread can access the resource at a time.",
                            "key_points": [
                                "Only owner thread can release the lock",
                                "Provides ownership semantics",
                                "Used for protecting critical sections",
                                "Different from binary semaphore in ownership"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "medium",
                            "keywords": ["mutex", "lock", "mutual exclusion", "thread safety"]
                        },
                        {
                            "name": "Deadlock",
                            "definition": "A deadlock is a situation where a set of processes are blocked because each process is holding a resource and waiting for another resource acquired by some other process.",
                            "key_points": [
                                "Four conditions: Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait",
                                "Prevention: Eliminate one of the four conditions",
                                "Avoidance: Banker's Algorithm",
                                "Detection: Resource Allocation Graph"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "hard",
                            "keywords": ["deadlock", "circular wait", "banker's algorithm", "resource allocation"]
                        }
                    ],
                    "keywords": ["synchronization", "semaphore", "mutex", "deadlock"]
                },
                {
                    "unit_number": 4,
                    "title": "Memory Management",
                    "topics": [
                        {
                            "name": "Paging",
                            "definition": "Paging is a memory management scheme that eliminates the need for contiguous allocation of physical memory by dividing physical memory into fixed-size frames and logical memory into pages of the same size.",
                            "key_points": [
                                "Eliminates external fragmentation",
                                "Page Table maps logical to physical addresses",
                                "Page fault occurs when page not in memory",
                                "TLB (Translation Lookaside Buffer) speeds up translation"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "hard",
                            "keywords": ["paging", "page table", "page fault", "TLB", "frame"]
                        },
                        {
                            "name": "Virtual Memory",
                            "definition": "Virtual memory is a technique that allows the execution of processes that are not completely in memory, providing the illusion of a very large memory space.",
                            "key_points": [
                                "Allows running programs larger than physical memory",
                                "Demand paging: Load pages only when needed",
                                "Page replacement: FIFO, LRU, Optimal",
                                "Thrashing: Excessive page faults"
                            ],
                            "exam_frequency": "high",
                            "difficulty_level": "hard",
                            "keywords": ["virtual memory", "demand paging", "page replacement", "thrashing"]
                        }
                    ],
                    "keywords": ["memory management", "paging", "virtual memory"]
                },
                {
                    "unit_number": 5,
                    "title": "File Systems",
                    "topics": [
                        {
                            "name": "File System Structure",
                            "definition": "A file system is the method and data structure that an operating system uses to control how data is stored and retrieved on a storage device.",
                            "key_points": [
                                "File attributes: Name, Type, Location, Size, Protection",
                                "Directory structure: Single-level, Two-level, Tree, Graph",
                                "Allocation methods: Contiguous, Linked, Indexed",
                                "Free space management: Bit vector, Linked list"
                            ],
                            "exam_frequency": "medium",
                            "difficulty_level": "medium",
                            "keywords": ["file system", "directory", "allocation", "inode"]
                        }
                    ],
                    "keywords": ["file system", "storage", "directory"]
                }
            ]
        },
        {
            "code": "CSPCC408",
            "name": "Software Engineering",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 4,
            "credits": 3,
            "subject_type": "core",
            "category": "PCC",
            "teaching_scheme": {"L": 3, "T": 0, "P": 0},
            "description": "Study of software development lifecycle, methodologies, and project management.",
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "total": 100
            }
        },
        {
            "code": "CSLBC403",
            "name": "Design & Analysis of Algorithm Laboratory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 4,
            "credits": 1,
            "subject_type": "lab",
            "category": "LBC",
            "teaching_scheme": {"L": 0, "T": 0, "P": 2},
            "description": "Laboratory for implementing and analyzing algorithms.",
            "examination_scheme": {
                "continuous_assessment": 25,
                "end_sem_exam": 25,
                "total": 50
            }
        },
        {
            "code": "CSLBC404",
            "name": "Linux Laboratory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 4,
            "credits": 1,
            "subject_type": "lab",
            "category": "LBC",
            "teaching_scheme": {"L": 0, "T": 0, "P": 2},
            "description": "Hands-on experience with Linux operating system and commands.",
            "examination_scheme": {
                "continuous_assessment": 25,
                "end_sem_exam": 25,
                "total": 50
            }
        },
        {
            "code": "CSLBC405",
            "name": "Software Development Laboratory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 4,
            "credits": 1,
            "subject_type": "lab",
            "category": "LBC",
            "teaching_scheme": {"L": 0, "T": 0, "P": 2},
            "description": "Practical software development using modern tools and practices.",
            "examination_scheme": {
                "continuous_assessment": 25,
                "end_sem_exam": 25,
                "total": 50
            }
        },
        {
            "code": "CSSBL402",
            "name": "Full stack development Laboratory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 4,
            "credits": 2,
            "subject_type": "lab",
            "category": "SBL",
            "teaching_scheme": {"L": 0, "T": 0, "P": 4},
            "description": "Development of web applications using full stack technologies.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 50,
                "total": 100
            }
        },
        {
            "code": "CSMNP402",
            "name": "Mini Project-1B",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 4,
            "credits": 1,
            "subject_type": "project",
            "category": "MNP",
            "teaching_scheme": {"L": 0, "T": 0, "P": 3},
            "description": "Second part of mini project.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 0,
                "total": 50
            }
        },
        {
            "code": "VEC402",
            "name": "Environment and Sustainability",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 4,
            "credits": 2,
            "subject_type": "value_education",
            "category": "VEC",
            "teaching_scheme": {"L": 2, "T": 0, "P": 0},
            "description": "Study of environmental issues and sustainable practices.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 0,
                "total": 50
            }
        },
        # ========== Semester 5 ==========
        {
            "code": "CSPCC509",
            "name": "Theory of Computer Science",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 5,
            "credits": 3,
            "subject_type": "core",
            "category": "PCC",
            "teaching_scheme": {"L": 3, "T": 0, "P": 0},
            "description": "Study of automata theory, formal languages, and computability.",
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "total": 100
            }
        },
        {
            "code": "CSPCC510",
            "name": "Computer Network",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 5,
            "credits": 3,
            "subject_type": "core",
            "category": "PCC",
            "teaching_scheme": {"L": 3, "T": 0, "P": 0},
            "description": "Study of computer networking concepts, protocols, and architectures.",
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "total": 100
            }
        },
        {
            "code": "CSLBC506",
            "name": "Network Laboratory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 5,
            "credits": 1,
            "subject_type": "lab",
            "category": "LBC",
            "teaching_scheme": {"L": 0, "T": 0, "P": 2},
            "description": "Practical implementation of networking concepts and protocols.",
            "examination_scheme": {
                "continuous_assessment": 25,
                "end_sem_exam": 25,
                "total": 50
            }
        },
        {
            "code": "CSLBC507",
            "name": "Cloud Computing Laboratory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 5,
            "credits": 1,
            "subject_type": "lab",
            "category": "LBC",
            "teaching_scheme": {"L": 0, "T": 0, "P": 2},
            "description": "Hands-on with cloud platforms and services.",
            "examination_scheme": {
                "continuous_assessment": 25,
                "end_sem_exam": 25,
                "total": 50
            }
        },
        {
            "code": "XXMDL501",
            "name": "Multidisciplinary Laboratory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 5,
            "credits": 1,
            "subject_type": "lab",
            "category": "MDL",
            "teaching_scheme": {"L": 0, "T": 0, "P": 2},
            "description": "Laboratory for multidisciplinary projects.",
            "examination_scheme": {
                "continuous_assessment": 25,
                "end_sem_exam": 25,
                "total": 50
            }
        },
        {
            "code": "AEC502",
            "name": "Professional Communication and Ethics-II",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 5,
            "credits": 2,
            "subject_type": "ability_enhancement",
            "category": "AEC",
            "teaching_scheme": {"L": 1, "T": 1, "P": 0},
            "description": "Advanced communication skills and professional ethics.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 0,
                "total": 50
            }
        },
        {
            "code": "CSMNP503",
            "name": "Mini Project-2A",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 5,
            "credits": 1,
            "subject_type": "project",
            "category": "MNP",
            "teaching_scheme": {"L": 0, "T": 0, "P": 3},
            "description": "First part of second mini project.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 0,
                "total": 50
            }
        },
        {
            "code": "HSS502",
            "name": "Entrepreneurship",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 5,
            "credits": 2,
            "subject_type": "humanities",
            "category": "HSS",
            "teaching_scheme": {"L": 2, "T": 0, "P": 0},
            "description": "Fundamentals of entrepreneurship and business planning.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 0,
                "total": 50
            }
        },
        # ========== Semester 6 ==========
        {
            "code": "CSPCC611",
            "name": "Cryptography & Network Security",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 6,
            "credits": 3,
            "subject_type": "core",
            "category": "PCC",
            "teaching_scheme": {"L": 3, "T": 0, "P": 0},
            "description": "Principles of cryptography and network security.",
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "total": 100
            }
        },
        {
            "code": "CSLBC608",
            "name": "Cryptography & Network Security Laboratory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 6,
            "credits": 1,
            "subject_type": "lab",
            "category": "LBC",
            "teaching_scheme": {"L": 0, "T": 0, "P": 2},
            "description": "Implementation of cryptographic algorithms and security protocols.",
            "examination_scheme": {
                "continuous_assessment": 25,
                "end_sem_exam": 25,
                "total": 50
            }
        },
        {
            "code": "CSLBC609",
            "name": "Data Science Laboratory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 6,
            "credits": 1,
            "subject_type": "lab",
            "category": "LBC",
            "teaching_scheme": {"L": 0, "T": 0, "P": 2},
            "description": "Practical data science using Python and relevant libraries.",
            "examination_scheme": {
                "continuous_assessment": 25,
                "end_sem_exam": 25,
                "total": 50
            }
        },
        {
            "code": "CSSBL603",
            "name": "Devops Laboratory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 6,
            "credits": 2,
            "subject_type": "lab",
            "category": "SBL",
            "teaching_scheme": {"L": 0, "T": 0, "P": 4},
            "description": "Hands-on with DevOps tools and practices.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 50,
                "total": 100
            }
        },
        {
            "code": "CSMNPG604",
            "name": "Mini Project-2B",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 6,
            "credits": 1,
            "subject_type": "project",
            "category": "MNP",
            "teaching_scheme": {"L": 0, "T": 0, "P": 3},
            "description": "Second part of second mini project.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 0,
                "total": 50
            }
        },
        {
            "code": "ELC601",
            "name": "Research Methodology",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 6,
            "credits": 2,
            "subject_type": "experiential",
            "category": "ELC",
            "teaching_scheme": {"L": 2, "T": 0, "P": 0},
            "description": "Introduction to research methods and scientific writing.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 0,
                "total": 50
            }
        },
        # ========== Semester 7 ==========
        {
            "code": "CSPCC712",
            "name": "Artificial Intelligence",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 7,
            "credits": 3,
            "subject_type": "core",
            "category": "PCC",
            "teaching_scheme": {"L": 3, "T": 0, "P": 0},
            "description": "Introduction to artificial intelligence concepts, algorithms, and applications.",
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "total": 100
            }
        },
        {
            "code": "CSLBC710",
            "name": "Artificial Intelligence Laboratory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 7,
            "credits": 1,
            "subject_type": "lab",
            "category": "LBC",
            "teaching_scheme": {"L": 0, "T": 0, "P": 2},
            "description": "Implementation of AI algorithms and techniques.",
            "examination_scheme": {
                "continuous_assessment": 25,
                "end_sem_exam": 25,
                "total": 50
            }
        },
        {
            "code": "CSLBC711",
            "name": "Data analytics & Visualization Laboratory",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 7,
            "credits": 1,
            "subject_type": "lab",
            "category": "LBC",
            "teaching_scheme": {"L": 0, "T": 0, "P": 2},
            "description": "Data analysis and visualization using modern tools.",
            "examination_scheme": {
                "continuous_assessment": 25,
                "end_sem_exam": 25,
                "total": 50
            }
        },
        {
            "code": "CSMJP701",
            "name": "Major Project-A",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 7,
            "credits": 2,
            "subject_type": "project",
            "category": "MJP",
            "teaching_scheme": {"L": 0, "T": 0, "P": 6},
            "description": "First part of major project.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 0,
                "total": 50
            }
        },
        {
            "code": "HSS703",
            "name": "Financial Planning",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 7,
            "credits": 2,
            "subject_type": "humanities",
            "category": "HSS",
            "teaching_scheme": {"L": 2, "T": 0, "P": 0},
            "description": "Basics of financial planning and management.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 0,
                "total": 50
            }
        },
        # ========== Semester 8 ==========
        {
            "code": "CSMJP802",
            "name": "Major Project-B",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 8,
            "credits": 4,
            "subject_type": "project",
            "category": "MJP",
            "teaching_scheme": {"L": 0, "T": 0, "P": 12},
            "description": "Second part of major project.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 0,
                "total": 50
            }
        },
        {
            "code": "INT801",
            "name": "Internship",
            "department": Link(dept_ids["CSE"], Department),
            "semester": 8,
            "credits": 8,
            "subject_type": "internship",
            "category": "INT",
            "teaching_scheme": {"L": 0, "T": 0, "P": 0},
            "description": "Industrial or research internship.",
            "examination_scheme": {
                "continuous_assessment": 50,
                "end_sem_exam": 0,
                "total": 50
            }
        }
    ]
    
    created_subjects = {}
    
    for subj_data in subjects_data:
        units_data = subj_data.pop("units", [])
        
        existing = await Subject.find_one({"code": subj_data["code"]})
        if existing:
            created_subjects[subj_data["code"]] = existing.id
            continue
        
        subject = Subject(**subj_data)
        await subject.insert()
        created_subjects[subj_data["code"]] = subject.id
        
        # Create units and topics
        for unit_data in units_data:
            topics_data = unit_data.pop("topics", [])
            
            unit = SubjectUnit(
                subject=Link(subject.id, Subject),
                unit_number=unit_data["unit_number"],
                title=unit_data["title"],
                keywords=unit_data.get("keywords", [])
            )
            await unit.insert()
            
            for topic_data in topics_data:
                topic = Topic(
                    unit=Link(unit.id, SubjectUnit),
                    name=topic_data["name"],
                    definition=topic_data.get("definition"),
                    key_points=topic_data.get("key_points", []),
                    exam_frequency=topic_data.get("exam_frequency"),
                    difficulty_level=topic_data.get("difficulty_level", "medium"),
                    keywords=topic_data.get("keywords", [])
                )
                await topic.insert()
    
    print(f"✅ Created/Updated {len(subjects_data)} subjects with units and topics")
    return created_subjects


async def seed_program_electives(dept_ids: Dict[str, PydanticObjectId]):
    """Seed program elective courses"""
    
    electives_data = [
        # Semester 5 - Program Elective Course-I
        {
            "semester": 5,
            "category": "PEC",
            "courses": [
                {
                    "code": "CSPEC5011",
                    "name": "Soft Computing",
                    "description": "Introduction to neural networks, fuzzy logic, and evolutionary algorithms.",
                    "credits": 3
                },
                {
                    "code": "CSPEC5012",
                    "name": "Advanced Database System",
                    "description": "Advanced concepts in database systems including NoSQL and distributed databases.",
                    "credits": 3
                },
                {
                    "code": "CSPEC5013",
                    "name": "Cloud Computing Services",
                    "description": "Study of cloud computing models, services, and platforms.",
                    "credits": 3
                },
                {
                    "code": "CSPEC5014",
                    "name": "Cyber Security",
                    "description": "Introduction to cybersecurity concepts, threats, and countermeasures.",
                    "credits": 3
                },
                {
                    "code": "CSPEC5015",
                    "name": "Computer graphics",
                    "description": "Fundamentals of computer graphics and visualization techniques.",
                    "credits": 3
                }
            ]
        },
        # Semester 6 - Program Elective Course-II
        {
            "semester": 6,
            "category": "PEC",
            "courses": [
                {
                    "code": "CSPEC6021",
                    "name": "Machine Learning",
                    "description": "Introduction to machine learning algorithms and applications.",
                    "credits": 3
                },
                {
                    "code": "CSPEC6022",
                    "name": "Dataware housing & Mining",
                    "description": "Concepts of data warehousing and data mining techniques.",
                    "credits": 3
                },
                {
                    "code": "CSPEC6023",
                    "name": "Wireless Technology",
                    "description": "Study of wireless communication technologies and protocols.",
                    "credits": 3
                },
                {
                    "code": "CSPEC6024",
                    "name": "Ethical Hacking",
                    "description": "Techniques and methodologies of ethical hacking and penetration testing.",
                    "credits": 3
                },
                {
                    "code": "CSPEC6025",
                    "name": "System Programming and Compiler Construction",
                    "description": "Study of system software and compiler design principles.",
                    "credits": 3
                }
            ]
        },
        # Semester 7 - Program Elective Course-III
        {
            "semester": 7,
            "category": "PEC",
            "courses": [
                {
                    "code": "CSPEC7031",
                    "name": "Natural Language Processing",
                    "description": "Techniques for processing and analyzing human language.",
                    "credits": 3
                },
                {
                    "code": "CSPEC7032",
                    "name": "Big Data Analytics",
                    "description": "Tools and techniques for big data processing and analytics.",
                    "credits": 3
                },
                {
                    "code": "CSPEC7033",
                    "name": "Edge Computing",
                    "description": "Concepts and architectures of edge computing systems.",
                    "credits": 3
                },
                {
                    "code": "CSPEC7034",
                    "name": "Digital Forensics",
                    "description": "Principles and practices of digital forensic investigation.",
                    "credits": 3
                },
                {
                    "code": "CSPEC7035",
                    "name": "Information Retrieval System",
                    "description": "Techniques for information storage, retrieval, and search.",
                    "credits": 3
                }
            ]
        },
        # Semester 7 - Program Elective Course-IV
        {
            "semester": 7,
            "category": "PEC",
            "courses": [
                {
                    "code": "CSPEC7041",
                    "name": "Foundation Models & Generative AI",
                    "description": "Study of large language models and generative AI techniques.",
                    "credits": 3
                },
                {
                    "code": "CSPEC7042",
                    "name": "Time Series Analysis",
                    "description": "Methods for analyzing time series data and forecasting.",
                    "credits": 3
                },
                {
                    "code": "CSPEC7043",
                    "name": "Quantum Computing",
                    "description": "Introduction to quantum computing principles and algorithms.",
                    "credits": 3
                },
                {
                    "code": "CSPEC7044",
                    "name": "Secure Software Engg.",
                    "description": "Principles and practices for developing secure software.",
                    "credits": 3
                },
                {
                    "code": "CSPEC7045",
                    "name": "Human Computer Interaction",
                    "description": "Design and evaluation of user interfaces and interaction techniques.",
                    "credits": 3
                }
            ]
        },
        # Semester 8 - Program Elective Course-V
        {
            "semester": 8,
            "category": "PEC",
            "courses": [
                {
                    "code": "CSPEC8051",
                    "name": "Responsible & Safe AI Systems",
                    "description": "Principles for developing ethical and safe AI systems.",
                    "credits": 3
                },
                {
                    "code": "CSPEC8052",
                    "name": "Recommender System",
                    "description": "Design and implementation of recommendation systems.",
                    "credits": 3
                },
                {
                    "code": "CSPEC8053",
                    "name": "High Performance Computing",
                    "description": "Techniques for parallel and high-performance computing.",
                    "credits": 3
                },
                {
                    "code": "CSPEC8054",
                    "name": "Cyber Physical Systems",
                    "description": "Integration of computation with physical processes.",
                    "credits": 3
                },
                {
                    "code": "CSPEC8055",
                    "name": "Blockchain Technology",
                    "description": "Principles and applications of blockchain technology.",
                    "credits": 3
                }
            ]
        }
    ]
    
    created_count = 0
    for sem_data in electives_data:
        for course_data in sem_data["courses"]:
            existing = await ProgramElective.find_one({"code": course_data["code"]})
            if not existing:
                course = ProgramElective(
                    **course_data,
                    semester=sem_data["semester"],
                    category=sem_data["category"],
                    department=Link(dept_ids["CSE"], Department)
                )
                await course.insert()
                created_count += 1
    
    print(f"✅ Created {created_count} program elective courses")


async def seed_open_electives():
    """Seed open elective courses"""
    
    electives_data = [
        # Semester 7 - Open Elective Course-I
        {
            "semester": 7,
            "courses": [
                {"code": "OEC7011", "name": "Product Lifecycle Management"},
                {"code": "OEC7012", "name": "Reliability Engineering"},
                {"code": "OEC7013", "name": "Management Information System"},
                {"code": "OEC7014", "name": "Design of Experiments"},
                {"code": "OEC7015", "name": "Operation Research"},
                {"code": "OEC7016", "name": "Cyber Security and Laws"},
                {"code": "OEC7017", "name": "Disaster Management and Mitigation Measures"},
                {"code": "OEC7018", "name": "Energy Audit and Management"},
                {"code": "OEC7019", "name": "Development Engineering"}
            ]
        },
        # Semester 8 - Open Elective Course-II
        {
            "semester": 8,
            "courses": [
                {"code": "OEC8021", "name": "Project Management"},
                {"code": "OEC8022", "name": "Finance Management"},
                {"code": "OEC8023", "name": "Entrepreneurship Development and Management"},
                {"code": "OEC8024", "name": "Human Resource Management"},
                {"code": "OEC8025", "name": "Professional Ethics and CSR"},
                {"code": "OEC8026", "name": "Circular Economy"},
                {"code": "OEC8027", "name": "IPR and Patenting"},
                {"code": "OEC8028", "name": "Digital Business Management"},
                {"code": "OEC8029", "name": "Environmental Management"}
            ]
        }
    ]
    
    created_count = 0
    for sem_data in electives_data:
        for course_data in sem_data["courses"]:
            existing = await OpenElective.find_one({"code": course_data["code"]})
            if not existing:
                course = OpenElective(
                    **course_data,
                    semester=sem_data["semester"],
                    credits=3
                )
                await course.insert()
                created_count += 1
    
    print(f"✅ Created {created_count} open elective courses")


async def seed_liberal_learning_courses():
    """Seed liberal learning courses for semester 6"""
    
    courses = [
        {"code": "LLC6011", "name": "Art of Living"},
        {"code": "LLC6012", "name": "Yoga and Meditation"},
        {"code": "LLC6013", "name": "Health and Wellness"},
        {"code": "LLC6014", "name": "Diet and Nutrition"},
        {"code": "LLC6015", "name": "Personality Development"}
    ]
    
    created_count = 0
    for course_data in courses:
        existing = await LiberalLearningCourse.find_one({"code": course_data["code"]})
        if not existing:
            course = LiberalLearningCourse(
                **course_data,
                semester=6,
                credits=2,
                description=f"Liberal learning course focusing on {course_data['name'].lower()}"
            )
            await course.insert()
            created_count += 1
    
    print(f"✅ Created {created_count} liberal learning courses")


async def seed_mdm_courses(dept_ids: Dict[str, PydanticObjectId]):
    """Seed Multidisciplinary Minor courses offered by CSE for other programs"""
    
    courses = [
        {
            "code": "CSMDM301",
            "name": "Data Structures and Algorithms",
            "semester": 3,
            "credits": 3,
            "teaching_scheme": {"L": 3, "T": 0, "P": 0},
            "description": "Introduction to fundamental data structures and algorithms for non-CSE students.",
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "total": 100
            }
        },
        {
            "code": "CSMDM402",
            "name": "Database Management System",
            "semester": 4,
            "credits": 3,
            "teaching_scheme": {"L": 3, "T": 0, "P": 0},
            "description": "Introduction to database concepts and SQL for non-CSE students.",
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "total": 100
            }
        },
        {
            "code": "CSMDM503",
            "name": "Cloud Computing",
            "semester": 5,
            "credits": 3,
            "teaching_scheme": {"L": 3, "T": 0, "P": 0},
            "description": "Introduction to cloud computing concepts and services for non-CSE students.",
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "total": 100
            }
        },
        {
            "code": "CSMDL501",
            "name": "Machine Learning Laboratory",
            "semester": 5,
            "credits": 1,
            "subject_type": "lab",
            "teaching_scheme": {"L": 0, "T": 0, "P": 2},
            "description": "Practical implementation of machine learning algorithms.",
            "examination_scheme": {
                "continuous_assessment": 25,
                "end_sem_exam": 25,
                "total": 50
            }
        },
        {
            "code": "CSMDM604",
            "name": "Soft Computing",
            "semester": 6,
            "credits": 4,
            "teaching_scheme": {"L": 4, "T": 0, "P": 0},
            "description": "Introduction to neural networks, fuzzy logic, and evolutionary algorithms for non-CSE students.",
            "examination_scheme": {
                "continuous_assessment": 20,
                "mid_sem_exam": 30,
                "end_sem_exam": 50,
                "total": 100
            }
        }
    ]
    
    created_count = 0
    for course_data in courses:
        existing = await MDMCourse.find_one({"code": course_data["code"]})
        if not existing:
            course = MDMCourse(
                **course_data,
                department=Link(dept_ids["CSE"], Department),
                category="MDM"
            )
            await course.insert()
            created_count += 1
    
    print(f"✅ Created {created_count} Multidisciplinary Minor courses")


async def seed_faculty(dept_ids: Dict[str, PydanticObjectId], subject_ids: Dict[str, PydanticObjectId]):
    """Seed faculty data"""
    
    faculty_data = [
        {
            "employee_id": "FAC001",
            "name": "Dr. Rajesh Kumar",
            "email": "rajesh.kumar@fcrit.ac.in",
            "department": Link(dept_ids["CSE"], Department),
            "designation": "Professor",
            "qualification": "Ph.D. in Computer Science",
            "experience_years": 18,
            "specializations": ["Operating Systems", "Distributed Systems", "Cloud Computing"],
            "research_areas": ["Cloud Computing", "Virtualization", "Container Technologies"],
            "teaching_style": "Interactive lectures with real-world examples and hands-on labs. Known for making complex OS concepts easy to understand.",
            "mentoring_areas": ["System Programming", "Linux Kernel", "Research Projects"],
            "office_location": "Block A, Room 301",
            "office_hours": {"monday": "10:00-12:00", "wednesday": "14:00-16:00", "friday": "10:00-11:00"},
            "teaching_rating": 4.7,
            "subjects": ["CSPCC407"]  # Operating Systems
        },
        {
            "employee_id": "FAC002",
            "name": "Dr. Priya Sharma",
            "email": "priya.sharma@fcrit.ac.in",
            "department": Link(dept_ids["CSE"], Department),
            "designation": "Associate Professor",
            "qualification": "Ph.D. in Database Systems",
            "experience_years": 14,
            "specializations": ["Database Systems", "Data Mining", "Big Data Analytics"],
            "research_areas": ["NoSQL Databases", "Data Warehousing", "Machine Learning"],
            "teaching_style": "Concept-focused teaching with extensive use of case studies. Emphasizes practical SQL skills and database design principles.",
            "mentoring_areas": ["Database Projects", "Data Science", "Industry Internships"],
            "office_location": "Block A, Room 205",
            "office_hours": {"tuesday": "11:00-13:00", "thursday": "15:00-17:00"},
            "teaching_rating": 4.8,
            "subjects": ["CSPCC304"]  # DBMS
        },
        {
            "employee_id": "FAC003",
            "name": "Dr. Amit Verma",
            "email": "amit.verma@fcrit.ac.in",
            "department": Link(dept_ids["CSE"], Department),
            "designation": "Assistant Professor",
            "qualification": "Ph.D. in Machine Learning",
            "experience_years": 8,
            "specializations": ["Machine Learning", "Deep Learning", "Computer Vision"],
            "research_areas": ["Neural Networks", "Natural Language Processing", "Reinforcement Learning"],
            "teaching_style": "Project-based learning with coding assignments. Uses Jupyter notebooks and live coding demonstrations.",
            "mentoring_areas": ["ML Projects", "Kaggle Competitions", "Research Papers"],
            "office_location": "Block B, Room 102",
            "office_hours": {"monday": "14:00-16:00", "wednesday": "10:00-12:00"},
            "teaching_rating": 4.6,
            "subjects": []
        },
        {
            "employee_id": "FAC004",
            "name": "Dr. Sunita Patel",
            "email": "sunita.patel@fcrit.ac.in",
            "department": Link(dept_ids["CSE"], Department),
            "designation": "Associate Professor",
            "qualification": "Ph.D. in Algorithms",
            "experience_years": 12,
            "specializations": ["Data Structures", "Algorithms", "Competitive Programming"],
            "research_areas": ["Algorithm Optimization", "Graph Theory", "Computational Geometry"],
            "teaching_style": "Problem-solving focused with whiteboard explanations. Conducts regular coding contests and encourages competitive programming.",
            "mentoring_areas": ["Placement Preparation", "Coding Competitions", "Algorithm Design"],
            "office_location": "Block A, Room 108",
            "office_hours": {"tuesday": "09:00-11:00", "friday": "14:00-16:00"},
            "teaching_rating": 4.9,
            "subjects": ["CSPCC303"]  # Data Structures
        },
        {
            "employee_id": "FAC005",
            "name": "Dr. Vikram Singh",
            "email": "vikram.singh@fcrit.ac.in",
            "department": Link(dept_ids["CSE"], Department),
            "designation": "Professor",
            "qualification": "Ph.D. in Computer Networks",
            "experience_years": 20,
            "specializations": ["Computer Networks", "Network Security", "IoT"],
            "research_areas": ["5G Networks", "Cybersecurity", "Software Defined Networking"],
            "teaching_style": "Theoretical foundations with Packet Tracer simulations. Extensive lab sessions for practical understanding.",
            "mentoring_areas": ["Network Projects", "Security Research", "Cisco Certifications"],
            "office_location": "Block C, Room 201",
            "office_hours": {"monday": "11:00-13:00", "thursday": "10:00-12:00"},
            "teaching_rating": 4.5,
            "subjects": []
        }
    ]
    
    for fac_data in faculty_data:
        subject_codes = fac_data.pop("subjects", [])
        
        existing = await Faculty.find_one({"employee_id": fac_data["employee_id"]})
        if existing:
            for key, value in fac_data.items():
                setattr(existing, key, value)
            await existing.save()
            faculty = existing
        else:
            faculty = Faculty(**fac_data)
            await faculty.insert()
        
        # Create faculty-subject assignments
        for subj_code in subject_codes:
            if subj_code in subject_ids:
                existing_assign = await FacultySubject.find_one(
                    FacultySubject.faculty.id == faculty.id,
                    FacultySubject.subject.id == subject_ids[subj_code]
                )
                if not existing_assign:
                    assignment = FacultySubject(
                        faculty=Link(faculty.id, Faculty),
                        subject=Link(subject_ids[subj_code], Subject),
                        academic_year="2024-25",
                        semester=1
                    )
                    await assignment.insert()
    
    print(f"✅ Created/Updated {len(faculty_data)} faculty members")


async def seed_career_paths():
    """Seed career path data"""
    
    careers = [
        {
            "title": "Software Developer",
            "category": "development",
            "description": "Design, develop, and maintain software applications. Work with various programming languages and frameworks to build solutions.",
            "required_skills": ["Programming (Java/Python/JavaScript)", "Data Structures", "Algorithms", "System Design", "Version Control (Git)", "Problem Solving"],
            "recommended_subjects": ["Data Structures", "Algorithms", "Operating Systems", "DBMS", "Software Engineering"],
            "recommended_electives": ["Web Technologies", "Mobile App Development", "Cloud Computing"],
            "certifications": ["AWS Certified Developer", "Oracle Java Certification", "Microsoft Azure Developer"],
            "salary_range": {"entry": "4-8 LPA", "mid": "10-20 LPA", "senior": "20-40 LPA"},
            "job_titles": ["Junior Developer", "Software Engineer", "Senior Developer", "Tech Lead", "Architect"],
            "companies": ["Google", "Microsoft", "Amazon", "Flipkart", "Infosys", "TCS", "Wipro"],
            "growth_potential": "high",
            "market_demand": "high",
            "roadmap": [
                "Master one programming language deeply",
                "Learn data structures and algorithms",
                "Build projects and contribute to open source",
                "Learn system design concepts",
                "Practice coding interviews"
            ],
            "keywords": ["software", "developer", "programmer", "coding", "engineer"],
            "matching_interests": ["programming", "coding", "software development", "web development"]
        },
        {
            "title": "Data Scientist",
            "category": "data",
            "description": "Analyze complex data to help organizations make better decisions. Use statistical methods and machine learning to extract insights.",
            "required_skills": ["Python/R", "Statistics", "Machine Learning", "SQL", "Data Visualization", "Deep Learning"],
            "recommended_subjects": ["Machine Learning", "Statistics", "DBMS", "Data Mining", "Algorithms"],
            "recommended_electives": ["Deep Learning", "Big Data Analytics", "Natural Language Processing"],
            "certifications": ["Google Data Analytics", "IBM Data Science", "AWS Machine Learning"],
            "salary_range": {"entry": "6-10 LPA", "mid": "15-30 LPA", "senior": "30-50 LPA"},
            "job_titles": ["Data Analyst", "Data Scientist", "ML Engineer", "Senior Data Scientist", "Principal Data Scientist"],
            "companies": ["Google", "Facebook", "Netflix", "Uber", "Amazon", "Flipkart"],
            "growth_potential": "high",
            "market_demand": "high",
            "roadmap": [
                "Learn Python and statistics fundamentals",
                "Master machine learning algorithms",
                "Work on Kaggle competitions",
                "Build a portfolio of data projects",
                "Learn deep learning and NLP"
            ],
            "keywords": ["data science", "machine learning", "ML", "AI", "analytics"],
            "matching_interests": ["machine learning", "data analysis", "AI", "statistics"]
        },
        {
            "title": "Cloud Engineer",
            "category": "infrastructure",
            "description": "Design, implement, and manage cloud infrastructure. Work with cloud platforms to deploy and scale applications.",
            "required_skills": ["AWS/Azure/GCP", "Docker", "Kubernetes", "Terraform", "Linux", "Networking"],
            "recommended_subjects": ["Operating Systems", "Computer Networks", "DBMS", "Distributed Systems"],
            "recommended_electives": ["Cloud Computing", "DevOps", "Container Technologies"],
            "certifications": ["AWS Solutions Architect", "Google Cloud Professional", "Azure Administrator"],
            "salary_range": {"entry": "5-8 LPA", "mid": "12-25 LPA", "senior": "25-45 LPA"},
            "job_titles": ["Cloud Engineer", "DevOps Engineer", "Site Reliability Engineer", "Cloud Architect"],
            "companies": ["Amazon", "Microsoft", "Google", "IBM", "Accenture"],
            "growth_potential": "high",
            "market_demand": "high",
            "roadmap": [
                "Learn Linux administration",
                "Get familiar with one cloud platform",
                "Learn containerization (Docker, Kubernetes)",
                "Understand Infrastructure as Code",
                "Get certified"
            ],
            "keywords": ["cloud", "AWS", "Azure", "DevOps", "infrastructure"],
            "matching_interests": ["cloud computing", "DevOps", "infrastructure", "automation"]
        },
        {
            "title": "Cybersecurity Analyst",
            "category": "security",
            "description": "Protect organizations from cyber threats. Monitor systems, identify vulnerabilities, and implement security measures.",
            "required_skills": ["Network Security", "Penetration Testing", "Security Tools", "Cryptography", "Linux", "Python"],
            "recommended_subjects": ["Computer Networks", "Operating Systems", "Cryptography", "Network Security"],
            "recommended_electives": ["Ethical Hacking", "Digital Forensics", "Cybersecurity"],
            "certifications": ["CompTIA Security+", "CEH", "CISSP", "OSCP"],
            "salary_range": {"entry": "4-7 LPA", "mid": "10-20 LPA", "senior": "20-35 LPA"},
            "job_titles": ["Security Analyst", "Penetration Tester", "Security Engineer", "Security Architect"],
            "companies": ["Deloitte", "EY", "PwC", "IBM Security", "FireEye"],
            "growth_potential": "high",
            "market_demand": "high",
            "roadmap": [
                "Learn networking fundamentals",
                "Understand common vulnerabilities",
                "Practice on platforms like HackTheBox",
                "Get CompTIA Security+ certification",
                "Specialize in a security domain"
            ],
            "keywords": ["security", "cybersecurity", "hacking", "penetration testing"],
            "matching_interests": ["security", "hacking", "network security", "cryptography"]
        }
    ]
    
    created_count = 0
    for career_data in careers:
        existing = await CareerPath.find_one({"title": career_data["title"]})
        if not existing:
            career = CareerPath(**career_data)
            await career.insert()
            created_count += 1
    
    print(f"✅ Created {created_count} career paths")


async def main():
    """Main seeding function"""
    print("🚀 Starting data seeding for Academic Chatbot...\n")
    print("📊 Using MongoDB with Beanie ODM")
    print("=" * 50)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[
            Department, Subject, SubjectUnit, Topic,
            Faculty, FacultySubject, CareerPath,
            ProgramElective, OpenElective, LiberalLearningCourse,
            Abbreviation, CreditStructure, MDMCourse
        ]
    )
    
    try:
        print("\n📁 Seeding abbreviations...")
        await seed_abbreviations()
        
        print("\n📁 Seeding departments...")
        dept_ids = await seed_departments()
        
        print("\n📊 Seeding credit structure...")
        await seed_credit_structure()
        
        print("\n📚 Seeding subjects with syllabus...")
        subject_ids = await seed_subjects(dept_ids)
        
        print("\n📚 Seeding program electives...")
        await seed_program_electives(dept_ids)
        
        print("\n📚 Seeding open electives...")
        await seed_open_electives()
        
        print("\n📚 Seeding liberal learning courses...")
        await seed_liberal_learning_courses()
        
        print("\n📚 Seeding MDM courses...")
        await seed_mdm_courses(dept_ids)
        
        print("\n👨‍🏫 Seeding faculty...")
        await seed_faculty(dept_ids, subject_ids)
        
        print("\n💼 Seeding career paths...")
        await seed_career_paths()
        
        print("\n" + "=" * 50)
        print("✅ All data seeded successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())