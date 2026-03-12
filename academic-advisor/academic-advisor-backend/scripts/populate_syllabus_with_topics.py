# scripts/populate_syllabus_with_topics.py
"""
Enhanced syllabus population script that also creates Topic documents
for chatbot searchability.
"""

import asyncio
import json
import re
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from pymongo.errors import DuplicateKeyError

from app.models.syllabus import (
    Department, Subject, SubjectUnit, Topic,
    ProgramElective, OpenElective, MDMCourse,
    LiberalLearningCourse, Abbreviation, CreditStructure
)
from app.config import settings

# ══════════════════════════════════════════════════════════
# TOPIC DEFINITIONS DATABASE
# For topics that need detailed explanations
# ══════════════════════════════════════════════════════════

TOPIC_DEFINITIONS = {
    # Operating Systems
    "deadlock": {
        "name": "Deadlock",
        "definition": "A deadlock is a situation in computing where two or more processes are unable to proceed because each is waiting for the other to release a resource.",
        "key_points": [
            "Four conditions: Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait",
            "Prevention involves breaking one of the four conditions",
            "Detection uses Resource Allocation Graph",
            "Recovery via process termination or resource preemption"
        ],
        "examples": [
            "Two trains on single track",
            "Dining Philosophers Problem"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high"
    },
    "process": {
        "name": "Process",
        "definition": "A process is an instance of a program in execution, with its own memory space and system resources.",
        "key_points": [
            "Process states: New, Ready, Running, Waiting, Terminated",
            "PCB (Process Control Block) stores process info",
            "Context switching between processes",
            "Process vs Thread distinction"
        ],
        "examples": ["Running a browser", "Each Chrome tab as a process"],
        "difficulty_level": "easy",
        "exam_frequency": "high"
    },
    "thread": {
        "name": "Thread",
        "definition": "A thread is the smallest unit of execution within a process, sharing the process's resources.",
        "key_points": [
            "Threads share code, data, and files",
            "Each thread has its own stack and registers",
            "User-level vs Kernel-level threads",
            "Multithreading enables parallelism"
        ],
        "examples": ["Word processor with spell-check thread"],
        "difficulty_level": "easy",
        "exam_frequency": "high"
    },
    "mutex": {
        "name": "Mutex",
        "definition": "A mutex (mutual exclusion) is a synchronization primitive that grants exclusive access to a shared resource.",
        "key_points": [
            "Binary: locked or unlocked",
            "Only locking thread can unlock",
            "Prevents race conditions"
        ],
        "examples": ["Protecting a shared counter"],
        "difficulty_level": "medium",
        "exam_frequency": "medium"
    },
    "semaphore": {
        "name": "Semaphore",
        "definition": "A semaphore is a synchronization primitive using a counter to control access to shared resources.",
        "key_points": [
            "Binary Semaphore: 0 or 1",
            "Counting Semaphore: any non-negative integer",
            "Wait (P) decrements, Signal (V) increments"
        ],
        "examples": ["Producer-Consumer problem", "Reader-Writer problem"],
        "difficulty_level": "medium",
        "exam_frequency": "high"
    },
    "paging": {
        "name": "Paging",
        "definition": "Paging is a memory management scheme that eliminates the need for contiguous memory allocation.",
        "key_points": [
            "Physical memory divided into frames",
            "Logical memory divided into pages",
            "Page table maps pages to frames",
            "Eliminates external fragmentation"
        ],
        "examples": ["Virtual memory implementation"],
        "difficulty_level": "medium",
        "exam_frequency": "high"
    },
    "scheduling": {
        "name": "CPU Scheduling",
        "definition": "CPU scheduling determines which process runs at any given time, optimizing CPU utilization.",
        "key_points": [
            "FCFS (First Come First Serve)",
            "SJF (Shortest Job First)",
            "Round Robin",
            "Priority Scheduling",
            "Multilevel Queue Scheduling"
        ],
        "examples": ["Time-sharing systems", "Real-time scheduling"],
        "difficulty_level": "medium",
        "exam_frequency": "high"
    },
    
    # Database
    "normalization": {
        "name": "Normalization",
        "definition": "Normalization is the process of organizing database tables to reduce redundancy and improve data integrity.",
        "key_points": [
            "1NF: Atomic values, no repeating groups",
            "2NF: No partial dependencies",
            "3NF: No transitive dependencies",
            "BCNF: Every determinant is a candidate key"
        ],
        "examples": ["Splitting customer-order table"],
        "difficulty_level": "medium",
        "exam_frequency": "high"
    },
    "sql": {
        "name": "SQL",
        "definition": "SQL (Structured Query Language) is a standard language for managing relational databases.",
        "key_points": [
            "DDL: CREATE, ALTER, DROP",
            "DML: SELECT, INSERT, UPDATE, DELETE",
            "DCL: GRANT, REVOKE",
            "Joins: INNER, LEFT, RIGHT, FULL"
        ],
        "examples": ["SELECT * FROM students WHERE grade > 80"],
        "difficulty_level": "easy",
        "exam_frequency": "high"
    },
    "transaction": {
        "name": "Transaction",
        "definition": "A database transaction is a unit of work that follows ACID properties.",
        "key_points": [
            "Atomicity: All or nothing",
            "Consistency: Valid state transitions",
            "Isolation: Concurrent independence",
            "Durability: Permanent changes"
        ],
        "examples": ["Bank transfer between accounts"],
        "difficulty_level": "medium",
        "exam_frequency": "high"
    },
    "indexing": {
        "name": "Indexing",
        "definition": "Indexing is a data structure technique to quickly locate data without scanning every row.",
        "key_points": [
            "B-Tree indexes",
            "Hash indexes",
            "Clustered vs Non-clustered",
            "Trade-off: faster reads, slower writes"
        ],
        "examples": ["Phone book index", "Database primary key index"],
        "difficulty_level": "medium",
        "exam_frequency": "medium"
    },
    
    # Data Structures
    "linked list": {
        "name": "Linked List",
        "definition": "A linked list is a linear data structure where elements are stored in nodes pointing to the next node.",
        "key_points": [
            "Dynamic size",
            "Non-contiguous memory",
            "Types: Singly, Doubly, Circular",
            "O(1) insertion/deletion at known position"
        ],
        "examples": ["Music playlist", "Browser history"],
        "difficulty_level": "easy",
        "exam_frequency": "high"
    },
    "binary tree": {
        "name": "Binary Tree",
        "definition": "A binary tree is a hierarchical structure where each node has at most two children.",
        "key_points": [
            "Left and right children",
            "Binary Search Tree property",
            "Traversals: Inorder, Preorder, Postorder",
            "Height and depth concepts"
        ],
        "examples": ["File system hierarchy", "Expression trees"],
        "difficulty_level": "medium",
        "exam_frequency": "high"
    },
    "graph": {
        "name": "Graph",
        "definition": "A graph is a non-linear structure consisting of vertices connected by edges.",
        "key_points": [
            "Directed vs Undirected",
            "Weighted vs Unweighted",
            "BFS and DFS traversals",
            "Shortest path algorithms"
        ],
        "examples": ["Social networks", "Road maps"],
        "difficulty_level": "medium",
        "exam_frequency": "high"
    },
    "hash table": {
        "name": "Hash Table",
        "definition": "A hash table uses a hash function to map keys to array indices for fast lookup.",
        "key_points": [
            "O(1) average lookup",
            "Collision handling: Chaining, Open Addressing",
            "Load factor affects performance",
            "Hash function properties"
        ],
        "examples": ["Dictionary implementation", "Database indexing"],
        "difficulty_level": "medium",
        "exam_frequency": "high"
    },
    "stack": {
        "name": "Stack",
        "definition": "A stack is a LIFO (Last In, First Out) data structure.",
        "key_points": [
            "Push and Pop operations",
            "O(1) for both operations",
            "Applications: recursion, undo"
        ],
        "examples": ["Browser back button", "Function call stack"],
        "difficulty_level": "easy",
        "exam_frequency": "high"
    },
    "queue": {
        "name": "Queue",
        "definition": "A queue is a FIFO (First In, First Out) data structure.",
        "key_points": [
            "Enqueue and Dequeue operations",
            "Types: Simple, Circular, Priority, Deque",
            "BFS uses queue"
        ],
        "examples": ["Print queue", "Task scheduling"],
        "difficulty_level": "easy",
        "exam_frequency": "high"
    },
    
    # Networking
    "tcp": {
        "name": "TCP",
        "definition": "TCP (Transmission Control Protocol) provides reliable, ordered delivery of data.",
        "key_points": [
            "Connection-oriented",
            "Three-way handshake",
            "Flow and congestion control",
            "Guaranteed delivery"
        ],
        "examples": ["HTTP, FTP, Email"],
        "difficulty_level": "medium",
        "exam_frequency": "high"
    },
    "udp": {
        "name": "UDP",
        "definition": "UDP (User Datagram Protocol) provides fast but unreliable data transmission.",
        "key_points": [
            "Connectionless",
            "No guaranteed delivery",
            "Lower overhead",
            "Used for streaming"
        ],
        "examples": ["Video streaming", "DNS", "Gaming"],
        "difficulty_level": "medium",
        "exam_frequency": "medium"
    },
    "osi model": {
        "name": "OSI Model",
        "definition": "The OSI model is a 7-layer conceptual framework for network communication.",
        "key_points": [
            "Physical, Data Link, Network, Transport, Session, Presentation, Application",
            "Each layer has specific functions",
            "Encapsulation concept"
        ],
        "examples": ["HTTP at Application layer", "IP at Network layer"],
        "difficulty_level": "medium",
        "exam_frequency": "high"
    },
    
    # Algorithms
    "sorting": {
        "name": "Sorting",
        "definition": "Sorting arranges elements in a specific order (ascending/descending).",
        "key_points": [
            "Comparison-based: Quick, Merge, Heap",
            "Non-comparison: Counting, Radix",
            "Time complexity varies",
            "In-place vs extra space"
        ],
        "examples": ["Sorting student records"],
        "difficulty_level": "medium",
        "exam_frequency": "high"
    },
    "dynamic programming": {
        "name": "Dynamic Programming",
        "definition": "DP solves complex problems by breaking them into overlapping subproblems.",
        "key_points": [
            "Optimal substructure",
            "Overlapping subproblems",
            "Memoization (top-down)",
            "Tabulation (bottom-up)"
        ],
        "examples": ["Fibonacci", "Knapsack", "LCS"],
        "difficulty_level": "hard",
        "exam_frequency": "high"
    },
}


async def create_topic_documents(subject: Subject, unit: SubjectUnit):
    """Create Topic documents from unit content and definitions."""
    
    # Get keywords from unit content
    content = getattr(unit, 'description', '') or ''
    title = getattr(unit, 'title', '') or ''
    
    # Find matching topic definitions
    for keyword, topic_def in TOPIC_DEFINITIONS.items():
        if keyword in title.lower() or keyword in content.lower():
            # Check if topic already exists
            existing = await Topic.find_one(
                Topic.name == topic_def["name"],
                Topic.unit.id == unit.id
            )
            
            if not existing:
                topic = Topic(
                    name=topic_def["name"],
                    unit=unit,
                    definition=topic_def["definition"],
                    key_points=topic_def.get("key_points", []),
                    examples=topic_def.get("examples", []),
                    keywords=[keyword] + topic_def["name"].lower().split(),
                    difficulty_level=topic_def.get("difficulty_level", "medium"),
                    exam_frequency=topic_def.get("exam_frequency", "medium"),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                try:
                    await topic.insert()
                    print(f"      + Created topic: {topic_def['name']}")
                except DuplicateKeyError:
                    pass


async def create_standalone_topics():
    """Create standalone Topic documents for common CS concepts."""
    print("\n📝 Creating standalone topic documents...")
    
    for keyword, topic_def in TOPIC_DEFINITIONS.items():
        existing = await Topic.find_one(Topic.name == topic_def["name"])
        
        if not existing:
            topic = Topic(
                name=topic_def["name"],
                unit=None,  # Standalone topic
                definition=topic_def["definition"],
                key_points=topic_def.get("key_points", []),
                examples=topic_def.get("examples", []),
                keywords=[keyword] + topic_def["name"].lower().split(),
                difficulty_level=topic_def.get("difficulty_level", "medium"),
                exam_frequency=topic_def.get("exam_frequency", "medium"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            try:
                await topic.insert()
                print(f"  ✅ Created: {topic_def['name']}")
            except DuplicateKeyError:
                print(f"  ⏭️ Exists: {topic_def['name']}")


async def main(reset: bool = False):
    """Main function to populate database."""
    
    print("=" * 70)
    print("🌱 POPULATING SYLLABUS DATABASE WITH TOPICS")
    print("=" * 70)
    
    # Connect
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    await init_beanie(
        database=db,
        document_models=[
            Department, Subject, SubjectUnit, Topic,
            ProgramElective, OpenElective, MDMCourse,
            LiberalLearningCourse, Abbreviation, CreditStructure
        ]
    )
    
    if reset:
        print("\n🗑️ Clearing existing topic documents...")
        await Topic.delete_all()
    
    # Create standalone topics
    await create_standalone_topics()
    
    # Also create topics linked to units
    print("\n🔗 Linking topics to subject units...")
    
    subjects = await Subject.find().to_list()
    for subject in subjects:
        units = await SubjectUnit.find(
            SubjectUnit.subject.id == subject.id
        ).to_list()
        
        for unit in units:
            await create_topic_documents(subject, unit)
    
    # Final count
    topic_count = await Topic.find().count()
    print(f"\n✅ Total topics in database: {topic_count}")
    
    print("=" * 70)
    print("🎉 DONE!")
    print("=" * 70)
    
    client.close()


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    asyncio.run(main(reset=reset_flag))