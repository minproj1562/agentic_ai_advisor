# academic-advisor-backend/scripts/migrations/create_chatbot_tables.py

"""
Database migration script for chatbot tables.
Run this to create the necessary tables.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.database.base import Base
from app.models.chatbot import (
    ConversationSession,
    ChatMessage,
    ConversationContext,
    SyllabusContent,
    FacultyProfile,
    AcademicKnowledgeBase,
    ChatbotAnalytics
)


def create_tables():
    """Create all chatbot-related tables"""
    
    engine = create_engine(settings.DATABASE_URL)
    
    # Create tables
    Base.metadata.create_all(bind=engine, tables=[
        ConversationSession.__table__,
        ChatMessage.__table__,
        ConversationContext.__table__,
        SyllabusContent.__table__,
        FacultyProfile.__table__,
        AcademicKnowledgeBase.__table__,
        ChatbotAnalytics.__table__,
    ])
    
    print("✅ Chatbot tables created successfully!")
    
    # Create indexes
    with engine.connect() as conn:
        # Index for faster session lookups
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sessions_user_active 
            ON conversation_sessions(user_id, is_active);
        """))
        
        # Index for message history
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_time 
            ON chat_messages(session_id, created_at DESC);
        """))
        
        # Index for syllabus search
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_syllabus_subject 
            ON syllabus_content(subject_code, unit_number);
        """))
        
        # Full text search index for syllabus (PostgreSQL)
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_syllabus_fts 
                ON syllabus_content USING gin(to_tsvector('english', detailed_content));
            """))
        except Exception:
            print("Full text search index not created (may require PostgreSQL)")
            
        conn.commit()
        
    print("✅ Indexes created successfully!")


def seed_sample_data():
    """Seed sample syllabus and faculty data"""
    
    from sqlalchemy.orm import Session
    
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as session:
        # Sample syllabus data
        sample_syllabus = [
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
              # academic-advisor-backend/scripts/migrations/create_chatbot_tables.py (CONTINUED)

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
        
        # Sample faculty data
        sample_faculty = [
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
        
        # Sample knowledge base entries
        sample_knowledge = [
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
        
        # Add all data
        for syllabus in sample_syllabus:
            session.add(syllabus)
            
        for faculty in sample_faculty:
            session.add(faculty)
            
        for knowledge in sample_knowledge:
            session.add(knowledge)
            
        session.commit()
        print("✅ Sample data seeded successfully!")


if __name__ == "__main__":
    print("Creating chatbot tables...")
    create_tables()
    
    print("\nSeeding sample data...")
    seed_sample_data()
    
    print("\n✅ Migration complete!")