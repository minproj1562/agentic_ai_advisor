# academic-advisor-backend/scripts/migrations/create_chatbot_tables.py
"""
Database migration script for chatbot collections (MongoDB + Beanie).
Run this to create the necessary collections, indexes, and seed sample data.
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import Document, Indexed, init_beanie, PydanticObjectId
from pydantic import Field, BaseModel

# Import your settings (adjust import path as needed)
from app.core.config import settings


# ------------------------------------------------------------------------------
# Document Models (equivalent to original SQLAlchemy models)
# ------------------------------------------------------------------------------

class ConversationSession(Document):
    """Chat conversation session."""
    session_id: str = Indexed(unique=True)
    user_id: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "conversation_sessions"
        indexes = [
            [("user_id", 1), ("is_active", 1)],  # compound index for active user sessions
        ]


class ChatMessage(Document):
    """Individual message in a conversation."""
    session_id: PydanticObjectId
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tokens_used: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "chat_messages"
        indexes = [
            [("session_id", 1), ("timestamp", -1)],  # for message history retrieval
        ]


class ConversationContext(Document):
    """Context information for active conversations."""
    session_id: PydanticObjectId = Indexed(unique=True)
    context_data: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "conversation_contexts"


class SyllabusContent(Document):
    """Syllabus content for subjects."""
    subject_code: str = Indexed()
    subject_name: str
    department: str
    semester: int
    unit_number: int
    unit_title: str
    topics: List[str] = Field(default_factory=list)
    detailed_content: str
    learning_objectives: List[str] = Field(default_factory=list)
    exam_weightage: Optional[float] = None
    keywords: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "syllabus_content"
        indexes = [
            [("subject_code", 1), ("unit_number", 1)],  # compound for subject/unit lookup
            [("keywords", 1)],                           # for keyword search
            # Full-text search index (requires MongoDB Atlas or self‑managed with text index)
            # If you need text search, uncomment the line below and ensure your MongoDB supports it.
            # [("detailed_content", "text")],
        ]


class FacultyProfile(Document):
    """Faculty information."""
    faculty_id: str = Indexed(unique=True)
    name: str
    department: str
    designation: str
    subjects_taught: List[str] = Field(default_factory=list)
    experience_years: int
    teaching_style: Optional[str] = None
    research_areas: List[str] = Field(default_factory=list)
    mentoring_focus: List[str] = Field(default_factory=list)
    specializations: List[str] = Field(default_factory=list)
    available_for_mentoring: bool = False
    rating: Optional[float] = None
    office_hours: Dict[str, str] = Field(default_factory=dict)  # e.g., {"monday": "10:00-12:00"}
    profile_image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "faculty_profiles"
        indexes = [
            "department",
            "subjects_taught",
            "available_for_mentoring",
        ]


class AcademicKnowledgeBase(Document):
    """General academic knowledge articles."""
    category: str  # e.g., "career", "elective", "general"
    title: str
    content: str
    keywords: List[str] = Field(default_factory=list)
    related_subjects: List[str] = Field(default_factory=list)
    department: Optional[str] = None
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "academic_knowledge_base"
        indexes = [
            "category",
            "keywords",
            "department",
            "is_verified",
        ]


class ChatbotAnalytics(Document):
    """Analytics data for chatbot usage."""
    session_id: Optional[PydanticObjectId] = None
    user_id: Optional[str] = None
    event_type: str  # e.g., "session_start", "message", "feedback", "error"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "chatbot_analytics"
        indexes = [
            [("user_id", 1), ("timestamp", -1)],
            [("event_type", 1), ("timestamp", -1)],
        ]


# ------------------------------------------------------------------------------
# Initialization and Seeding Functions
# ------------------------------------------------------------------------------

async def init_database():
    """Initialize Beanie with the document models."""
    # Create MongoDB client
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    # Get database name from connection string or use default
    db_name = settings.MONGODB_DB_NAME if hasattr(settings, "MONGODB_DB_NAME") else "academic_advisor"
    
    # Initialize Beanie
    await init_beanie(
        database=client[db_name],
        document_models=[
            ConversationSession,
            ChatMessage,
            ConversationContext,
            SyllabusContent,
            FacultyProfile,
            AcademicKnowledgeBase,
            ChatbotAnalytics,
        ]
    )
    print("✅ Beanie initialized successfully!")


async def create_indexes():
    """Ensure all indexes are created (Beanie does this automatically on init, 
    but we can force creation if needed. Usually it's enough to define them in Settings.
    """
    # Beanie automatically creates indexes when the documents are registered.
    # You can manually create them by calling <Document>.get_motor_collection().create_indexes()
    # However, we'll rely on Beanie's automatic behavior.
    print("✅ Indexes will be created automatically by Beanie (or already exist).")
    # Optionally, you can iterate over all models and create indexes explicitly:
    # for model in [ConversationSession, ...]:
    #     await model.get_motor_collection().create_indexes(model.get_indexes())
    # But this is not necessary as init_beanie already does it.


async def seed_sample_data():
    """Insert sample syllabus, faculty, and knowledge base documents."""
    print("Seeding sample data...")

    # --- Syllabus Content ---
    syllabus_samples = [
        SyllabusContent(
            subject_code="CS301",
            subject_name="Operating Systems",
            department="Computer Science",
            semester=5,
            unit_number=1,
            unit_title="Introduction to Operating Systems",
            topics=["OS Overview", "Types of OS", "OS Services", "System Calls"],
            detailed_content="""
An operating system is system software that manages computer hardware, 
software resources, and provides common services for computer programs.

Types of Operating Systems:
1. Batch Operating System
2. Time-Sharing Operating System
3. Distributed Operating System
4. Network Operating System
5. Real-Time Operating System

OS Services include process management, memory management, 
file system management, I/O management, and security.
            """,
            learning_objectives=[
                "Understand the role of OS",
                "Identify different types of OS",
                "Explain OS services"
            ],
            exam_weightage=15.0,
            keywords=["operating system", "os", "system calls", "kernel"]
        ),
        SyllabusContent(
            subject_code="CS301",
            subject_name="Operating Systems",
            department="Computer Science",
            semester=5,
            unit_number=2,
            unit_title="Process Management",
            topics=["Process Concept", "Process States", "PCB", "Process Scheduling", "Context Switching"],
            detailed_content="""
A process is a program in execution. It includes the program code, 
current activity, stack, data section, and heap.

Process States:
1. New - Process is being created
2. Ready - Process is waiting to be assigned to a processor
3. Running - Instructions are being executed
4. Waiting - Process is waiting for some event
5. Terminated - Process has finished execution

Process Control Block (PCB) contains process state, program counter,
CPU registers, memory management information, and I/O status.
            """,
            learning_objectives=[
                "Understand process concept",
                "Explain process states",
                "Describe PCB structure"
            ],
            exam_weightage=20.0,
            keywords=["process", "pcb", "scheduling", "context switch"]
        ),
        SyllabusContent(
            subject_code="CS301",
            subject_name="Operating Systems",
            department="Computer Science",
            semester=5,
            unit_number=3,
            unit_title="Process Synchronization",
            topics=["Critical Section", "Mutex", "Semaphores", "Deadlock", "Deadlock Prevention"],
            detailed_content="""
Process Synchronization is the coordination of execution of multiple processes 
in a multi-process system to ensure that they access shared resources in a 
controlled and predictable manner.

Critical Section Problem:
A critical section is a code segment that accesses shared variables and has 
to be executed as an atomic action.

Mutex (Mutual Exclusion):
A mutex is a locking mechanism used to synchronize access to a resource.
Only one task can acquire the mutex at a time.

Semaphores:
A semaphore is a signaling mechanism. Two types:
1. Binary Semaphore (0 or 1)
2. Counting Semaphore (can have any non-negative value)

Deadlock:
A deadlock is a situation where a set of processes are blocked because 
each process is holding a resource and waiting for another resource 
acquired by some other process.

Conditions for Deadlock (Coffman Conditions):
1. Mutual Exclusion
2. Hold and Wait
3. No Preemption
4. Circular Wait

Deadlock Prevention:
- Eliminate Mutual Exclusion
- Eliminate Hold and Wait
- Allow Preemption
- Eliminate Circular Wait
            """,
            learning_objectives=[
                "Understand critical section problem",
                "Implement mutex and semaphores",
                "Identify and prevent deadlock"
            ],
            exam_weightage=25.0,
            keywords=["deadlock", "mutex", "semaphore", "synchronization", "critical section"]
        ),
        SyllabusContent(
            subject_code="CS302",
            subject_name="Database Management Systems",
            department="Computer Science",
            semester=5,
            unit_number=1,
            unit_title="Introduction to DBMS",
            topics=["Database Concepts", "DBMS Architecture", "Data Models", "ER Model"],
            detailed_content="""
A Database Management System (DBMS) is software that enables users to 
define, create, maintain, and control access to databases.

DBMS Architecture:
1. Single-tier Architecture
2. Two-tier Architecture (Client-Server)
3. Three-tier Architecture

Data Models:
1. Hierarchical Model
2. Network Model
3. Relational Model
4. Object-Oriented Model

Entity-Relationship (ER) Model:
- Entity: Real-world object
- Attribute: Property of an entity
- Relationship: Association between entities
            """,
            learning_objectives=[
                "Understand DBMS concepts",
                "Explain DBMS architecture",
                "Design ER diagrams"
            ],
            exam_weightage=15.0,
            keywords=["dbms", "database", "er model", "data model"]
        ),
        SyllabusContent(
            subject_code="CS302",
            subject_name="Database Management Systems",
            department="Computer Science",
            semester=5,
            unit_number=2,
            unit_title="Relational Model and SQL",
            topics=["Relational Model", "SQL Basics", "DDL", "DML", "Joins", "Subqueries"],
            detailed_content="""
Relational Model:
The relational model represents data as relations (tables).
Key concepts: Relation, Tuple, Attribute, Domain, Schema

SQL (Structured Query Language):
Standard language for managing relational databases.

DDL (Data Definition Language):
- CREATE: Create database objects
- ALTER: Modify database objects
- DROP: Delete database objects
- TRUNCATE: Remove all records

DML (Data Manipulation Language):
- SELECT: Retrieve data
- INSERT: Add new records
- UPDATE: Modify existing records
- DELETE: Remove records

Types of Joins:
1. INNER JOIN: Returns matching rows
2. LEFT JOIN: Returns all left table rows
3. RIGHT JOIN: Returns all right table rows
4. FULL OUTER JOIN: Returns all rows
5. CROSS JOIN: Cartesian product
            """,
            learning_objectives=[
                "Understand relational model",
                "Write SQL queries",
                "Use different types of joins"
            ],
            exam_weightage=25.0,
            keywords=["sql", "relational", "join", "ddl", "dml", "query"]
        ),
        SyllabusContent(
            subject_code="CS302",
            subject_name="Database Management Systems",
            department="Computer Science",
            semester=5,
            unit_number=3,
            unit_title="Normalization",
            topics=["Functional Dependencies", "1NF", "2NF", "3NF", "BCNF", "Decomposition"],
            detailed_content="""
Normalization is the process of organizing data to reduce redundancy 
and improve data integrity.

Functional Dependency:
A functional dependency X → Y means that Y is functionally dependent on X.
If two tuples have the same value for X, they must have the same value for Y.

First Normal Form (1NF):
- Eliminate repeating groups
- Each cell contains a single value
- Each record is unique

Second Normal Form (2NF):
- Must be in 1NF
- No partial dependencies
- Non-key attributes depend on the entire primary key

Third Normal Form (3NF):
- Must be in 2NF
- No transitive dependencies
- Non-key attributes depend only on the primary key

Boyce-Codd Normal Form (BCNF):
- Must be in 3NF
- For every functional dependency X → Y, X must be a superkey

Decomposition:
Process of breaking a relation into smaller relations to achieve normalization.
Should be lossless and dependency preserving.
            """,
            learning_objectives=[
                "Identify functional dependencies",
                "Apply normalization rules",
                "Decompose relations properly"
            ],
            exam_weightage=20.0,
            keywords=["normalization", "1nf", "2nf", "3nf", "bcnf", "functional dependency"]
        ),
    ]

    # Insert syllabus (avoid duplicates by checking subject_code+unit_number)
    for syllabus in syllabus_samples:
        existing = await SyllabusContent.find_one(
            SyllabusContent.subject_code == syllabus.subject_code,
            SyllabusContent.unit_number == syllabus.unit_number
        )
        if not existing:
            await syllabus.insert()
            print(f"  Inserted syllabus: {syllabus.subject_code} - Unit {syllabus.unit_number}")
        else:
            print(f"  Syllabus already exists: {syllabus.subject_code} - Unit {syllabus.unit_number}")

    # --- Faculty Profiles ---
    faculty_samples = [
        FacultyProfile(
            faculty_id="FAC001",
            name="Dr. Rajesh Kumar",
            department="Computer Science",
            designation="Associate Professor",
            subjects_taught=["Operating Systems", "Computer Networks", "System Programming"],
            experience_years=15,
            teaching_style="Interactive with practical demonstrations",
            research_areas=["Distributed Systems", "Cloud Computing", "Network Security"],
            mentoring_focus=["System-level projects", "Research methodology"],
            specializations=["Linux Kernel", "Network Protocols"],
            available_for_mentoring=True,
            rating=4.5,
            office_hours={"monday": "10:00-12:00", "wednesday": "14:00-16:00"}
        ),
        FacultyProfile(
            faculty_id="FAC002",
            name="Dr. Priya Sharma",
            department="Computer Science",
            designation="Professor",
            subjects_taught=["Database Management Systems", "Data Warehousing", "Big Data Analytics"],
            experience_years=20,
            teaching_style="Conceptual with real-world case studies",
            research_areas=["Data Mining", "Machine Learning", "NoSQL Databases"],
            mentoring_focus=["Data-driven projects", "Industry collaboration"],
            specializations=["Oracle", "MongoDB", "Hadoop"],
            available_for_mentoring=True,
            rating=4.8,
            office_hours={"tuesday": "11:00-13:00", "thursday": "15:00-17:00"}
        ),
        FacultyProfile(
            faculty_id="FAC003",
            name="Dr. Amit Verma",
            department="Computer Science",
            designation="Assistant Professor",
            subjects_taught=["Machine Learning", "Artificial Intelligence", "Deep Learning"],
            experience_years=8,
            teaching_style="Project-based learning with coding exercises",
            research_areas=["Neural Networks", "Computer Vision", "NLP"],
            mentoring_focus=["AI/ML projects", "Research papers"],
            specializations=["TensorFlow", "PyTorch", "Computer Vision"],
            available_for_mentoring=True,
            rating=4.6,
            office_hours={"monday": "14:00-16:00", "friday": "10:00-12:00"}
        ),
        FacultyProfile(
            faculty_id="FAC004",
            name="Dr. Sunita Patel",
            department="Computer Science",
            designation="Associate Professor",
            subjects_taught=["Data Structures", "Algorithms", "Competitive Programming"],
            experience_years=12,
            teaching_style="Problem-solving focused with algorithmic thinking",
            research_areas=["Algorithm Optimization", "Computational Complexity"],
            mentoring_focus=["Competitive programming", "Placement preparation"],
            specializations=["Dynamic Programming", "Graph Algorithms"],
            available_for_mentoring=True,
            rating=4.7,
            office_hours={"wednesday": "10:00-12:00", "friday": "14:00-16:00"}
        ),
    ]

    for faculty in faculty_samples:
        existing = await FacultyProfile.find_one(FacultyProfile.faculty_id == faculty.faculty_id)
        if not existing:
            await faculty.insert()
            print(f"  Inserted faculty: {faculty.name}")
        else:
            print(f"  Faculty already exists: {faculty.name}")

    # --- Academic Knowledge Base ---
    knowledge_samples = [
        AcademicKnowledgeBase(
            category="career",
            title="Software Developer Career Path",
            content="""
Career Path for Software Developer:

Entry Level (0-2 years):
- Junior Developer / Software Engineer
- Skills: Programming basics, version control, testing
- Salary Range: 3-6 LPA

Mid Level (2-5 years):
- Software Developer / Senior Developer
- Skills: System design, code review, mentoring
- Salary Range: 6-15 LPA

Senior Level (5-10 years):
- Senior Software Engineer / Tech Lead
- Skills: Architecture, team leadership, technical decisions
- Salary Range: 15-30 LPA

Leadership (10+ years):
- Engineering Manager / Director / CTO
- Skills: Strategic planning, business alignment
- Salary Range: 30+ LPA

Required Skills:
- Programming Languages (Python, Java, JavaScript)
- Data Structures and Algorithms
- System Design
- Database Management
- Version Control (Git)
- Cloud Platforms (AWS, Azure, GCP)
            """,
            keywords=["software developer", "career", "programming", "engineer"],
            related_subjects=["Data Structures", "Algorithms", "Software Engineering"],
            department="Computer Science",
            is_verified=True
        ),
        AcademicKnowledgeBase(
            category="career",
            title="Data Scientist Career Path",
            content="""
Career Path for Data Scientist:

Entry Level:
- Data Analyst / Junior Data Scientist
- Skills: Statistics, SQL, Python/R, visualization
- Salary Range: 4-8 LPA

Mid Level:
- Data Scientist / ML Engineer
- Skills: Machine learning, deep learning, feature engineering
- Salary Range: 10-20 LPA

Senior Level:
- Senior Data Scientist / Lead ML Engineer
- Skills: Research, model deployment, team leadership
- Salary Range: 20-40 LPA

Required Skills:
- Statistics and Mathematics
- Machine Learning algorithms
- Python (NumPy, Pandas, Scikit-learn)
- Deep Learning (TensorFlow, PyTorch)
- SQL and databases
- Data visualization
- Big Data tools (Spark, Hadoop)
            """,
            keywords=["data scientist", "machine learning", "analytics", "ai"],
            related_subjects=["Machine Learning", "Statistics", "Big Data"],
            department="Computer Science",
            is_verified=True
        ),
        AcademicKnowledgeBase(
            category="elective",
            title="Cloud Computing Elective",
            content="""
Cloud Computing - Professional Elective

Course Overview:
Introduction to cloud computing concepts, service models, 
deployment models, and major cloud platforms.

Topics Covered:
- Cloud fundamentals and architecture
- IaaS, PaaS, SaaS models
- AWS, Azure, GCP services
- Containerization (Docker, Kubernetes)
- Serverless computing
- Cloud security

Career Benefits:
- High demand in industry
- Cloud certifications add value
- Essential for DevOps roles

Prerequisites:
- Operating Systems
- Computer Networks
- Basic programming

Recommended For:
- Students interested in infrastructure
- DevOps aspirants
- System administrators
            """,
            keywords=["cloud computing", "aws", "azure", "devops", "elective"],
            related_subjects=["Operating Systems", "Computer Networks"],
            department="Computer Science",
            is_verified=True
        ),
        AcademicKnowledgeBase(
            category="elective",
            title="Cybersecurity Elective",
            content="""
Cybersecurity - Professional Elective

Course Overview:
Comprehensive study of information security principles, 
threats, and defense mechanisms.

Topics Covered:
- Security fundamentals and CIA triad
- Cryptography and encryption
- Network security
- Web application security
- Ethical hacking basics
- Security tools and frameworks

Career Benefits:
- Growing demand for security professionals
- High-paying career path
- Critical for all organizations

Prerequisites:
- Computer Networks
- Operating Systems
- Programming fundamentals

Certifications to Consider:
- CompTIA Security+
- CEH (Certified Ethical Hacker)
- CISSP (advanced)
            """,
            keywords=["cybersecurity", "security", "ethical hacking", "encryption"],
            related_subjects=["Computer Networks", "Operating Systems"],
            department="Computer Science",
            is_verified=True
        ),
    ]

    for knowledge in knowledge_samples:
        # Avoid duplicates by title and category (simple check)
        existing = await AcademicKnowledgeBase.find_one(
            AcademicKnowledgeBase.title == knowledge.title,
            AcademicKnowledgeBase.category == knowledge.category
        )
        if not existing:
            await knowledge.insert()
            print(f"  Inserted knowledge: {knowledge.title}")
        else:
            print(f"  Knowledge already exists: {knowledge.title}")

    print("✅ Sample data seeding completed.")


async def main():
    """Main migration function."""
    print("Starting MongoDB migration...")
    await init_database()
    await create_indexes()
    await seed_sample_data()
    print("✅ Migration complete!")


if __name__ == "__main__":
    asyncio.run(main())