# academic-advisor/academic-advisor-backend/app/services/chatbot/response_generator.py
"""
Response Generator — FULLY FIXED based on actual DB diagnostic output.

DB Schema (from diagnostic):
  subjects:      code, name, credits, semester(int), score, grade, grade_points, trend, weaknesses
  topics:        name, subject_name, subject_code, unit_number, unit_title, definition(often EMPTY), key_points(often EMPTY), keywords
  subject_units: subject_code, unit_number, title, topics(array of {name}), description, hours
  faculty:       name, email, department, designation, teaching_subjects(list), specializations(list)

Key fixes:
  1. _db initialized at module level (CRITICAL FIX)
  2. _extract_subject() uses word-boundary matching (prevents "dl" matching inside "deadlock")
  3. _get_db() accesses connection._mongo_database directly
  4. _topic_query() falls through to LLM when DB topic has empty content
  5. _build_units_from_subject_units() queries subject_units collection first
  6. Faculty search uses correct field name: teaching_subjects
  7. Error handler returns type="text" + confidence="Low" so LLM can rescue
  8. Weakness suggestions include actionable resource links
"""

import re
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def safe_enum_value(v, default=""):
    if v is None:
        return default
    if isinstance(v, str):
        return v
    if hasattr(v, "value"):
        return v.value
    return str(v)


# ══════════════════════════════════════════════════════════
# MODULE-LEVEL DATABASE REFERENCE — CRITICAL FIX
# ══════════════════════════════════════════════════════════
_db = None  # THIS LINE WAS MISSING - causing NameError


def _get_db():
    """
    Get raw motor database.
    FIXED: Proper initialization and multiple fallback strategies.
    """
    global _db
    if _db is not None:
        return _db

    # Strategy 1: Import the module and read its private var directly
    try:
        import app.database.connection as _conn_mod
        if hasattr(_conn_mod, '_mongo_database') and _conn_mod._mongo_database is not None:
            _db = _conn_mod._mongo_database
            logger.info(f"✅ ResponseGenerator DB (strategy 1 - shared global): {_db.name}")
            return _db
        else:
            logger.debug("Strategy 1: _mongo_database is None or missing")
    except Exception as e:
        logger.debug(f"Strategy 1 failed: {e}")

    # Strategy 2: Call the getter function
    try:
        from app.database.connection import get_mongo_database
        result = get_mongo_database()
        if result is not None:
            _db = result
            logger.info(f"✅ ResponseGenerator DB (strategy 2 - getter): {_db.name}")
            return _db
        else:
            logger.warning("⚠️ get_mongo_database() returned None")
    except Exception as e:
        logger.warning(f"Strategy 2 failed: {e}")

    # Strategy 3: Create new motor client directly
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        from app.config import settings
        uri = getattr(settings, 'MONGODB_URL', 'mongodb://localhost:27017')
        db_name = getattr(settings, 'MONGODB_DATABASE', 'academic_advisor')
        logger.info(f"Strategy 3: connecting to {uri}/{db_name}")
        client = AsyncIOMotorClient(uri)
        _db = client[db_name]
        logger.info(f"✅ ResponseGenerator DB (strategy 3 - new client): {_db.name}")
        return _db
    except Exception as e:
        logger.error(f"❌ Strategy 3 failed: {e}")

    logger.error("❌❌❌ ALL DB strategies failed — chatbot DB queries will not work!")
    return None


def _col(name: str):
    """Get a raw motor collection by name."""
    db = _get_db()
    if db is None:
        logger.error(f"⚠️ _col('{name}'): DB is None — cannot query")
        return None
    return db[name]


# ══════════════════════════════════════════════════════════
# CAREER REPO
# ══════════════════════════════════════════════════════════

_CareerRepo = None
try:
    from app.repositories.career_repository import CareerRepository as _CR
    _CareerRepo = _CR
except ImportError:
    pass


# ══════════════════════════════════════════════════════════
# SUBJECT / CAREER ALIASES
# ══════════════════════════════════════════════════════════

_SUBJECT_ALIASES = {
    "os": "Operating System", "operating system": "Operating System",
    "operating systems": "Operating System",
    "dbms": "Database Management System", "database": "Database Management System",
    "database management": "Database Management System",
    "database management systems": "Database Management System",
    "dsa": "Data Structures", "data structure": "Data Structures",
    "data structures": "Data Structures",
    "data structures and algorithms": "Data Structures",
    "cn": "Computer Network", "computer network": "Computer Network",
    "computer networks": "Computer Network", "networking": "Computer Network",
    "ml": "Machine Learning", "machine learning": "Machine Learning",
    "ai": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    "dl": "Deep Learning", "deep learning": "Deep Learning",
    "aiml": "Artificial Intelligence", "ai/ml": "Artificial Intelligence",
    "se": "Software Engineering", "software engineering": "Software Engineering",
    "coa": "Computer Organization",
    "computer organization": "Computer Organization",
    "toc": "Theory of Computation", "automata": "Theory of Computation",
    "automata theory": "Theory of Computation",
    "daa": "Design & Analysis of Algorithm",
    "cns": "Cryptography & Network Security",
    "cryptography": "Cryptography & Network Security",
    "crypto": "Cryptography & Network Security",
    "cc": "Cloud Computing", "cloud computing": "Cloud Computing",
    "iot": "Internet of Things", "internet of things": "Internet of Things",
    "oop": "Object Oriented Programming",
    "oops": "Object Oriented Programming",
    "maths": "Engineering Mathematics", "math": "Engineering Mathematics",
    "mathematics": "Engineering Mathematics",
    "math 3": "Engineering Mathematics-III",
    "math 4": "Engineering Mathematics-IV",
    "maths 3": "Engineering Mathematics-III",
    "maths 4": "Engineering Mathematics-IV",
    "em3": "Engineering Mathematics-III",
    "em4": "Engineering Mathematics-IV",
    "discrete math": "Discrete Mathematics", "dm": "Discrete Mathematics",
    "discrete mathematics": "Discrete Mathematics",
    "physics": "Engineering Physics", "chemistry": "Engineering Chemistry",
    "python": "Python Programming", "java": "Java Programming",
    "c programming": "C Programming", "c language": "C Programming",
    "c++": "C++ Programming", "cpp": "C++ Programming",
    "web": "Web Technology", "wt": "Wireless Technology",
    "wireless": "Wireless Technology",
    "embedded": "Microcontroller & Embedded Systems",
    "embedded systems": "Microcontroller & Embedded Systems",
    "mes": "Microcontroller & Embedded Systems",
    "dld": "Digital Logic & Design",
    "blockchain": "Blockchain Technology",
    "nlp": "Natural Language Processing",
    "big data": "Big Data Analytics",
    "fsd": "Full Stack Development",
    "mini project": "Mini Project",
}

_CAREER_ALIASES = {
    "data scientist": "Data Scientist", "data science": "Data Scientist",
    "ml engineer": "ML Engineer", "software developer": "Software Developer",
    "software engineer": "Software Developer", "sde": "Software Developer",
    "devops": "DevOps Engineer", "full stack": "Full Stack Developer",
    "web developer": "Full Stack Developer",
    "cybersecurity": "Cybersecurity Analyst",
    "data analyst": "Data Analyst", "data engineer": "Data Engineer",
    "cloud architect": "Cloud Architect",
    "network engineer": "Network Engineer",
}


def _normalize_subject(t):
    return _SUBJECT_ALIASES.get(t.lower().strip(), t.strip())


def _extract_subject(text):
    """
    Extract subject name from text using WORD BOUNDARY matching.
    CRITICAL FIX: Prevents short aliases matching inside other words.
    e.g. "dl" must NOT match inside "deadlock", "ai" must NOT match inside "explain"
    """
    tl = text.lower().strip()
    # Sort by length descending so longer matches are tried first
    for alias in sorted(_SUBJECT_ALIASES, key=len, reverse=True):
        try:
            # Word boundary pattern - prevents partial matches
            pattern = r'(?<![a-z])' + re.escape(alias) + r'(?![a-z])'
            if re.search(pattern, tl):
                return _SUBJECT_ALIASES[alias]
        except re.error:
            # Fallback: check with spaces
            if f" {alias} " in f" {tl} ":
                return _SUBJECT_ALIASES[alias]
    return None


def _extract_career(q):
    ql = q.lower()
    for a in sorted(_CAREER_ALIASES, key=lambda x: -len(x)):
        if a in ql:
            return _CAREER_ALIASES[a]
    return None


def _normalize_name_for_search(name: str) -> str:
    """Normalize subject names for matching: remove hyphens, extra spaces."""
    return re.sub(r'[\-–—]', ' ', name).strip()


# ══════════════════════════════════════════════════════════
# BUILT-IN CONCEPTS KB (Fallback when DB is empty)
# ══════════════════════════════════════════════════════════

CONCEPTS = {
    "deadlock": {
        "topic": "Deadlock", "subject": "Operating Systems",
        "definition": "A deadlock occurs when two or more processes are blocked forever, each waiting for the other to release a resource.",
        "key_points": [
            "4 necessary conditions: Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait",
            "Prevention: break any one condition",
            "Avoidance: Banker's Algorithm checks safe states",
            "Detection: Resource Allocation Graph (RAG)",
            "Recovery: Process termination or resource preemption",
        ],
        "examples": ["Dining Philosophers Problem", "Two processes each holding a lock the other needs"],
        "related_topics": ["mutex", "semaphore", "process synchronization", "Banker's Algorithm"],
        "exam_relevance": "Very High — asked in almost every OS exam",
    },
    "normalization": {
        "topic": "Normalization", "subject": "Database Management Systems",
        "definition": "Normalization organizes data to minimize redundancy and dependency by dividing tables into smaller ones linked by relationships.",
        "key_points": [
            "1NF: All values atomic (no repeating groups)",
            "2NF: No partial dependencies (all non-key attrs depend on full key)",
            "3NF: No transitive dependencies",
            "BCNF: Every determinant is a candidate key",
            "4NF: No multi-valued dependencies",
        ],
        "examples": ["Converting a flat customer-orders table into separate Customer, Order, and OrderItem tables"],
        "related_topics": ["functional dependency", "SQL", "ER model", "joins", "denormalization"],
        "exam_relevance": "Very High — core DBMS concept",
    },
    "paging": {
        "topic": "Paging", "subject": "Operating Systems",
        "definition": "Paging divides physical memory into fixed-size frames and logical memory into same-size pages, eliminating external fragmentation.",
        "key_points": [
            "Pages mapped to frames via page table",
            "TLB (Translation Lookaside Buffer) caches page table entries",
            "Eliminates external fragmentation",
            "Virtual address = page number + offset",
            "Page fault occurs when page not in memory",
        ],
        "related_topics": ["virtual memory", "segmentation", "page replacement", "TLB", "demand paging"],
        "exam_relevance": "High — core OS concept",
    },
    "semaphore": {
        "topic": "Semaphore", "subject": "Operating Systems",
        "definition": "A semaphore is a synchronization tool using wait() and signal() operations to control access to shared resources.",
        "key_points": [
            "Binary semaphore: 0 or 1 (mutex)",
            "Counting semaphore: for multiple resources",
            "wait()/P(): decrements; blocks if < 0",
            "signal()/V(): increments; wakes blocked process",
            "Used to solve producer-consumer, readers-writers problems",
        ],
        "related_topics": ["mutex", "deadlock", "producer-consumer", "critical section"],
        "exam_relevance": "Very High",
    },
    "mutex": {
        "topic": "Mutex", "subject": "Operating Systems",
        "definition": "A mutex (mutual exclusion) ensures only one thread accesses a critical section at a time. Only the locking thread can unlock it.",
        "key_points": [
            "Binary: locked/unlocked states",
            "Ownership: only the locker can unlock",
            "Prevents race conditions",
            "Lighter than semaphore for single-resource protection",
        ],
        "related_topics": ["semaphore", "deadlock", "critical section", "spinlock"],
        "exam_relevance": "High",
    },
    "sql joins": {
        "topic": "SQL Joins", "subject": "Database Management Systems",
        "definition": "SQL Joins combine rows from two or more tables based on a related column between them.",
        "key_points": [
            "INNER JOIN: Only matching rows from both tables",
            "LEFT JOIN: All rows from left + matching from right",
            "RIGHT JOIN: All rows from right + matching from left",
            "FULL OUTER JOIN: All rows from both tables",
            "CROSS JOIN: Cartesian product of both tables",
        ],
        "examples": ["SELECT * FROM orders INNER JOIN customers ON orders.customer_id = customers.id"],
        "related_topics": ["SQL", "normalization", "foreign key", "subqueries"],
        "exam_relevance": "Very High",
    },
    "tcp": {
        "topic": "TCP (Transmission Control Protocol)", "subject": "Computer Networks",
        "definition": "TCP is a connection-oriented, reliable transport layer protocol ensuring ordered, error-checked delivery of data.",
        "key_points": [
            "3-way handshake: SYN, SYN-ACK, ACK",
            "Reliable: ACKs, retransmissions, checksums",
            "Flow control: sliding window protocol",
            "Congestion control: slow start, congestion avoidance",
            "Connection termination: 4-way handshake (FIN)",
        ],
        "related_topics": ["UDP", "OSI model", "HTTP", "flow control", "socket programming"],
        "exam_relevance": "Very High",
    },
    "osi model": {
        "topic": "OSI Model", "subject": "Computer Networks",
        "definition": "The OSI (Open Systems Interconnection) model is a 7-layer framework standardizing how network systems communicate.",
        "key_points": [
            "Layer 7 - Application: HTTP, FTP, SMTP (user interface)",
            "Layer 6 - Presentation: Encryption, compression",
            "Layer 5 - Session: Session management",
            "Layer 4 - Transport: TCP/UDP (end-to-end)",
            "Layer 3 - Network: IP, routing (logical addressing)",
            "Layer 2 - Data Link: MAC, frames (physical addressing)",
            "Layer 1 - Physical: Cables, bits, signals",
        ],
        "examples": ["Mnemonic: All People Seem To Need Data Processing (top-down)"],
        "related_topics": ["TCP/IP model", "TCP", "IP", "Ethernet"],
        "exam_relevance": "Very High — foundation of networking",
    },
    "dynamic programming": {
        "topic": "Dynamic Programming", "subject": "Data Structures & Algorithms",
        "definition": "DP solves complex problems by breaking them into overlapping subproblems, storing solutions to avoid redundant computation.",
        "key_points": [
            "Two properties: Optimal Substructure + Overlapping Subproblems",
            "Top-down: Memoization (recursion + cache)",
            "Bottom-up: Tabulation (iterative)",
            "Time-space tradeoff: memory for speed",
            "Common problems: Fibonacci, Knapsack, LCS, Coin Change, Edit Distance",
        ],
        "related_topics": ["recursion", "greedy algorithms", "memoization", "divide and conquer"],
        "exam_relevance": "Very High — essential for coding interviews",
    },
    "linked list": {
        "topic": "Linked List", "subject": "Data Structures",
        "definition": "A linked list is a linear data structure where elements (nodes) are connected via pointers, not stored contiguously in memory.",
        "key_points": [
            "Types: Singly, Doubly, Circular linked lists",
            "Insert/Delete at head: O(1)",
            "Search/Access by index: O(n)",
            "No fixed size; dynamic memory allocation",
            "Used for implementing Stack, Queue, Graph adjacency lists",
        ],
        "related_topics": ["array", "stack", "queue", "memory allocation"],
        "exam_relevance": "Very High",
    },
    "binary search": {
        "topic": "Binary Search", "subject": "Data Structures & Algorithms",
        "definition": "Binary Search finds a target value in a sorted array by repeatedly halving the search space. Time complexity: O(log n).",
        "key_points": [
            "Prerequisite: Array MUST be sorted",
            "O(log n) — much faster than linear O(n) search",
            "Compare target with middle element",
            "Eliminate half of remaining elements each step",
            "Can be implemented iteratively or recursively",
        ],
        "examples": ["Finding 7 in [1,3,5,7,9,11]: check 5 (too small) → check 9 (too big) → found 7"],
        "related_topics": ["sorting", "divide and conquer", "binary search tree"],
        "exam_relevance": "Very High",
    },
    "process scheduling": {
        "topic": "Process Scheduling", "subject": "Operating Systems",
        "definition": "Process scheduling determines which process runs on the CPU and for how long, maximizing CPU utilization and throughput.",
        "key_points": [
            "FCFS (First Come First Serve): Simple but convoy effect",
            "SJF (Shortest Job First): Optimal average wait time but starvation possible",
            "Round Robin: Time quantum, good for time-sharing systems",
            "Priority Scheduling: Can cause starvation (solved by aging)",
            "MLFQ (Multilevel Feedback Queue): Multiple queues with different priorities",
        ],
        "related_topics": ["process", "CPU", "context switch", "throughput", "turnaround time"],
        "exam_relevance": "Very High",
    },
    "bfs": {
        "topic": "Breadth-First Search (BFS)", "subject": "Data Structures & Algorithms",
        "definition": "BFS is a graph traversal algorithm that explores all vertices at the current depth before moving to the next level.",
        "key_points": [
            "Uses a Queue (FIFO) data structure",
            "Finds shortest path in unweighted graphs",
            "Time: O(V + E), Space: O(V)",
            "Level-order traversal in trees",
            "Applications: shortest path, connected components, web crawling",
        ],
        "related_topics": ["DFS", "graph", "queue", "shortest path", "tree traversal"],
        "exam_relevance": "Very High",
    },
    "dfs": {
        "topic": "Depth-First Search (DFS)", "subject": "Data Structures & Algorithms",
        "definition": "DFS is a graph traversal algorithm that explores as far as possible along each branch before backtracking.",
        "key_points": [
            "Uses a Stack (or recursion)",
            "Time: O(V + E), Space: O(V)",
            "Three types: Pre-order, In-order, Post-order (for trees)",
            "Applications: cycle detection, topological sort, path finding, maze solving",
            "Can detect back edges (cycles) in directed graphs",
        ],
        "related_topics": ["BFS", "graph", "stack", "recursion", "topological sort"],
        "exam_relevance": "Very High",
    },
    "acid properties": {
        "topic": "ACID Properties", "subject": "Database Management Systems",
        "definition": "ACID properties ensure reliable database transactions: Atomicity, Consistency, Isolation, Durability.",
        "key_points": [
            "Atomicity: All or nothing — transaction completes fully or not at all",
            "Consistency: Database moves from one valid state to another",
            "Isolation: Concurrent transactions don't interfere with each other",
            "Durability: Committed changes survive system failures",
            "Implemented using locks, logs, and recovery mechanisms",
        ],
        "related_topics": ["transactions", "concurrency control", "locking", "rollback", "commit"],
        "exam_relevance": "Very High",
    },
}

CAREERS = {
    "Data Scientist": {
        "title": "Data Scientist",
        "description": "Analyze complex data using statistics, ML, and domain expertise to extract actionable insights.",
        "required_skills": ["Python", "Machine Learning", "Statistics", "SQL", "Data Visualization", "Deep Learning"],
        "market_demand": "Very High",
        "salary_range": {"entry_level": "₹6-10 LPA", "mid_level": "₹12-20 LPA", "senior_level": "₹20-40 LPA"},
        "roadmap": [
            {"step": 1, "title": "Python & SQL", "description": "Master pandas, NumPy, SQL", "duration": "2-3 months"},
            {"step": 2, "title": "Statistics", "description": "Hypothesis testing, distributions", "duration": "2 months"},
            {"step": 3, "title": "Machine Learning", "description": "Scikit-learn, Kaggle competitions", "duration": "3 months"},
            {"step": 4, "title": "Deep Learning & NLP", "description": "PyTorch, transformers, projects", "duration": "3 months"},
        ],
    },
    "Software Developer": {
        "title": "Software Developer",
        "description": "Design, code, test, and maintain software applications across the full development lifecycle.",
        "required_skills": ["Java/Python/JS", "DSA", "Git", "System Design", "Databases", "REST APIs"],
        "market_demand": "Very High",
        "salary_range": {"entry_level": "₹5-8 LPA", "mid_level": "₹10-20 LPA", "senior_level": "₹20-40 LPA"},
        "roadmap": [
            {"step": 1, "title": "Master One Language", "description": "Java, Python, or JavaScript deeply", "duration": "3 months"},
            {"step": 2, "title": "DSA Practice", "description": "LeetCode 200+ problems", "duration": "4-6 months"},
            {"step": 3, "title": "Build Projects", "description": "Full-stack applications with deployment", "duration": "3 months"},
        ],
    },
    "ML Engineer": {
        "title": "ML Engineer",
        "description": "Build, train, and deploy ML models in production at scale.",
        "required_skills": ["Python", "TensorFlow/PyTorch", "MLOps", "Docker", "Cloud", "SQL"],
        "market_demand": "Very High",
        "salary_range": {"entry_level": "₹8-12 LPA", "mid_level": "₹15-25 LPA", "senior_level": "₹25-45 LPA"},
        "roadmap": [
            {"step": 1, "title": "ML Foundations", "description": "Scikit-learn, feature engineering", "duration": "3 months"},
            {"step": 2, "title": "Deep Learning", "description": "PyTorch, CNNs, RNNs, Transformers", "duration": "3 months"},
            {"step": 3, "title": "MLOps", "description": "Docker, CI/CD, model serving", "duration": "2 months"},
        ],
    },
    "DevOps Engineer": {
        "title": "DevOps Engineer",
        "description": "Automate software delivery, manage infrastructure, and ensure system reliability.",
        "required_skills": ["Linux", "Docker", "Kubernetes", "CI/CD", "Cloud (AWS/GCP/Azure)", "Terraform"],
        "market_demand": "Very High",
        "salary_range": {"entry_level": "₹6-10 LPA", "mid_level": "₹12-22 LPA", "senior_level": "₹22-40 LPA"},
        "roadmap": [
            {"step": 1, "title": "Linux & Scripting", "description": "Bash, Python scripting", "duration": "2 months"},
            {"step": 2, "title": "Containers", "description": "Docker, Kubernetes", "duration": "2 months"},
            {"step": 3, "title": "CI/CD & Cloud", "description": "Jenkins/GitHub Actions, AWS", "duration": "2 months"},
        ],
    },
    "Full Stack Developer": {
        "title": "Full Stack Developer",
        "description": "Build complete web applications — frontend UI and backend APIs.",
        "required_skills": ["HTML/CSS/JS", "React/Vue", "Node.js/Python", "Databases", "REST APIs", "Git"],
        "market_demand": "High",
        "salary_range": {"entry_level": "₹4-7 LPA", "mid_level": "₹8-18 LPA", "senior_level": "₹18-35 LPA"},
        "roadmap": [
            {"step": 1, "title": "Frontend", "description": "React/Vue, Tailwind CSS", "duration": "3 months"},
            {"step": 2, "title": "Backend", "description": "Node.js or FastAPI/Django", "duration": "3 months"},
            {"step": 3, "title": "Deploy", "description": "Docker, Vercel/AWS, databases", "duration": "1 month"},
        ],
    },
}

_CURATED_RESOURCES = {
    "operating system": [
        {"title": "OS - Neso Academy (Full Playlist)", "type": "Video", "url": "https://youtube.com/playlist?list=PLBlnK6fEyqRiVhbXDGLXDk_OQAdc0cPiS", "platform": "YouTube", "rating": 4.8, "difficulty": "Beginner"},
        {"title": "OS Notes - GeeksforGeeks", "type": "Notes", "url": "https://www.geeksforgeeks.org/operating-systems/", "platform": "GFG", "rating": 4.5, "difficulty": "All"},
        {"title": "OS Gate Smasher", "type": "Video", "url": "https://youtube.com/playlist?list=PLxCzCOWd7aiGz9donHRrE9I3Mwn6XdP8p", "platform": "YouTube", "rating": 4.7, "difficulty": "Intermediate"},
    ],
    "database": [
        {"title": "DBMS - Gate Smashers (Full)", "type": "Video", "url": "https://youtube.com/playlist?list=PLxCzCOWd7aiFAN6I8CuViBuCdJgiOkT2Y", "platform": "YouTube", "rating": 4.7, "difficulty": "Beginner"},
        {"title": "SQL Tutorial - W3Schools", "type": "Interactive", "url": "https://www.w3schools.com/sql/", "platform": "W3Schools", "rating": 4.5, "difficulty": "Beginner"},
        {"title": "DBMS Notes - GFG", "type": "Notes", "url": "https://www.geeksforgeeks.org/dbms/", "platform": "GFG", "rating": 4.6, "difficulty": "All"},
    ],
    "machine learning": [
        {"title": "ML by Andrew Ng", "type": "Course", "url": "https://www.coursera.org/learn/machine-learning", "platform": "Coursera", "rating": 4.9, "difficulty": "Intermediate"},
        {"title": "ML - StatQuest (Visual)", "type": "Video", "url": "https://youtube.com/playlist?list=PLblh5JKOoLUICTaGLRoHQDuF_7q2GfuJF", "platform": "YouTube", "rating": 4.9, "difficulty": "Beginner"},
        {"title": "Hands-on ML - Kaggle", "type": "Practice", "url": "https://www.kaggle.com/learn/intro-to-machine-learning", "platform": "Kaggle", "rating": 4.7, "difficulty": "Beginner"},
    ],
    "data structure": [
        {"title": "DSA - Abdul Bari (Best)", "type": "Video", "url": "https://youtube.com/playlist?list=PLdo5W4Nhv31bbKJzrsKfMpo_grxuLl8LU", "platform": "YouTube", "rating": 4.9, "difficulty": "Beginner"},
        {"title": "NeetCode Roadmap", "type": "Practice", "url": "https://neetcode.io/roadmap", "platform": "NeetCode", "rating": 4.8, "difficulty": "Intermediate"},
        {"title": "DSA - Striver's A2Z Sheet", "type": "Practice", "url": "https://takeuforward.org/strivers-a2z-dsa-course/strivers-a2z-dsa-course-sheet-2", "platform": "TakeUForward", "rating": 4.9, "difficulty": "All"},
    ],
    "computer network": [
        {"title": "CN - Gate Smashers", "type": "Video", "url": "https://youtube.com/playlist?list=PLxCzCOWd7aiGFBD2-2joCpWOLUrDLvVV_", "platform": "YouTube", "rating": 4.7, "difficulty": "Beginner"},
        {"title": "Networking Basics - Cisco", "type": "Course", "url": "https://www.netacad.com/courses/networking", "platform": "Cisco", "rating": 4.6, "difficulty": "Beginner"},
    ],
    "python": [
        {"title": "Python - Mosh (6 hrs)", "type": "Video", "url": "https://www.youtube.com/watch?v=kqtD5dpn9C8", "platform": "YouTube", "rating": 4.8, "difficulty": "Beginner"},
        {"title": "Python Docs", "type": "Docs", "url": "https://docs.python.org/3/tutorial/", "platform": "Official", "rating": 4.7, "difficulty": "All"},
    ],
    "deep learning": [
        {"title": "Deep Learning - 3Blue1Brown", "type": "Video", "url": "https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi", "platform": "YouTube", "rating": 4.9, "difficulty": "Beginner"},
        {"title": "Fast.ai Course", "type": "Course", "url": "https://course.fast.ai/", "platform": "Fast.ai", "rating": 4.8, "difficulty": "Intermediate"},
    ],
}


# ══════════════════════════════════════════════════════════
# FACULTY SEARCH — searches correct collections+fields
# ══════════════════════════════════════════════════════════

async def _search_faculty(subject_name: str, limit: int = 5) -> list:
    p = re.escape(subject_name)
    for col_name in ["faculty", "faculty_members"]:
        col = _col(col_name)
        if col is None:  # ← FIXED: was "if col is None: continue"
            continue

        try:
            count = await col.count_documents({})
            if count == 0:
                continue
            results = await col.find(
                {"$or": [
                    {"teaching_subjects": {"$regex": p, "$options": "i"}},
                    {"specializations": {"$regex": p, "$options": "i"}},
                    {"subjects_taught": {"$regex": p, "$options": "i"}},
                    {"subjects": {"$regex": p, "$options": "i"}},
                    {"research_areas": {"$regex": p, "$options": "i"}},
                ]}
            ).limit(limit).to_list(length=limit)
            if results:
                logger.info(f"Found {len(results)} faculty for '{subject_name}' in {col_name}")
                return results
        except Exception as e:
            logger.debug(f"Faculty search in {col_name} failed: {e}")
    return []


def _fmt_faculty(f: dict) -> dict:
    """Format faculty doc — handles all field name variants."""
    subjects = (f.get("teaching_subjects")
                or f.get("subjects_taught")
                or f.get("subjects")
                or [])
    if isinstance(subjects, str):
        subjects = [subjects]

    specs = f.get("specializations", []) or []
    specs = [s if isinstance(s, str) else
             (s.get("name", str(s)) if isinstance(s, dict) else str(s))
             for s in specs]

    return {
        "name": f.get("name", ""),
        "department": f.get("department", ""),
        "designation": f.get("designation", ""),
        "email": str(f.get("email", "")),
        "phone": f.get("phone", ""),
        "office_location": f.get("office_location", ""),
        "subjects_taught": subjects,
        "specializations": specs,
        "years_of_experience": f.get("years_of_experience", 0),
    }


# ══════════════════════════════════════════════════════════
# RESPONSE GENERATOR
# ══════════════════════════════════════════════════════════

class ResponseGenerator:
    def __init__(self):
        self.career_repo = _CareerRepo() if _CareerRepo else None

    async def generate_response(self, query, intent, context, student_data=None):
        i = safe_enum_value(intent, "GENERAL")
        handlers = {
            "SYLLABUS_QUERY": self._syllabus,
            "FACULTY_QUERY": self._faculty,
            "PERFORMANCE_QUERY": self._performance,
            "CAREER_QUERY": self._career,
            "ELECTIVE_QUERY": self._elective,
            "STUDY_PLAN_QUERY": self._study_plan,
            "MENTOR_QUERY": self._mentor,
            "RESOURCE_QUERY": self._resources,
            "CLARIFICATION": self._clarify,
            "GREETING": self._generic,
            "GENERAL": self._generic,
            "OUT_OF_SCOPE": lambda q, c, s: self._oos(),
        }
        try:
            handler = handlers.get(i, self._generic)
            result = await handler(query, context, student_data)
            if not isinstance(result, dict):
                result = {"type": "text", "intent": i,
                          "content": {"message": str(result)}, "confidence": "Medium"}
            result.setdefault("type", "text")
            result.setdefault("confidence", "Medium")
            result.setdefault("intent", i)
            if "content" not in result or not isinstance(result.get("content"), dict):
                result["content"] = {"message": str(result.get("content", ""))}
            return result
        except Exception as e:
            logger.error(f"Handler {i} error: {e}", exc_info=True)
            return {
                "type": "text", "intent": i,
                "content": {"message": "I had trouble looking that up. Let me try another way.",
                            "suggestions": ["Syllabus for sem 3", "Who teaches ML?",
                                            "Explain deadlock", "Career in AI"]},
                "confidence": "Low", "_handler_error": True,
            }

    # ══════════════════════════════════════════════════════
    # SYLLABUS — Now queries subject_units properly
    # ══════════════════════════════════════════════════════

    async def _syllabus(self, query, context, student_data):
        # Check for semester query first
        sem = self._get_sem(query)
        if sem:
            return await self._sem_query(sem)

        # Check for subject query
        subj_name = _extract_subject(query)
        if subj_name:
            return await self._subj_query(subj_name)

        # Check for topic/concept query
        topic_name = self._get_topic(query)
        if topic_name:
            return await self._topic_query(topic_name)

        # Use context if available
        if context and context.get("current_subject"):
            return await self._subj_query(context["current_subject"])

        return {
            "type": "text", "intent": "SYLLABUS_QUERY",
            "content": {
                "message": "I can help with syllabus! Try:\n\n"
                           "- **Syllabus for sem 4** — list subjects\n"
                           "- **OS syllabus** — subject details & units\n"
                           "- **Explain deadlock** — concept explanation",
                "suggestions": ["Syllabus for sem 3", "OS syllabus", "Explain deadlock"],
            },
            "confidence": "Medium",
        }

    async def _sem_query(self, sem: int):
        """Query subjects for a specific semester."""
        col = _col("subjects")
        if col is None:  # ← FIXED: was "if not col:"
            logger.warning("subjects collection not accessible")
            return {"type": "text", "intent": "SYLLABUS_QUERY",
                    "content": {"message": "Database unavailable. Please try again."},
                    "confidence": "Low"}

        subjects = []
        try:
            # Diagnostic confirmed: semester is stored as int
            cursor = col.find({"semester": sem}).sort("code", 1)
            async for s in cursor:
                subjects.append({
                    "code": s.get("code", ""),
                    "name": s.get("name", ""),
                    "credits": s.get("credits", 0),
                    "subject_type": self._guess_subject_type(s.get("code", "")),
                })
        except Exception as e:
            logger.error(f"Semester query error: {e}", exc_info=True)

        if subjects:
            tc = sum(s.get("credits", 0) for s in subjects
                     if isinstance(s.get("credits"), (int, float)))
            return {
                "type": "semester_subjects", "intent": "SYLLABUS_QUERY",
                "content": {
                    "semester": sem, "subjects": subjects,
                    "count": len(subjects), "total_credits": tc,
                    "message": f"Semester {sem} — **{len(subjects)} subjects** ({tc} credits):",
                },
                "confidence": "High",
            }

        # Check if subjects collection is empty
        try:
            total = await col.count_documents({})
            if total == 0:
                return {"type": "text", "intent": "SYLLABUS_QUERY",
                        "content": {"message": "Syllabus database hasn't been populated yet.",
                                    "suggestions": ["Explain deadlock", "Career in data science"]},
                        "confidence": "Medium"}
        except Exception:
            pass

        return {"type": "text", "intent": "SYLLABUS_QUERY",
                "content": {"message": f"No subjects found for semester {sem}.",
                            "suggestions": [f"Syllabus for sem {max(1,sem-1)}",
                                            f"Syllabus for sem {min(8,sem+1)}"]},
                "confidence": "Low"}

    async def _subj_query(self, name: str):
        col = _col("subjects")
        if col is None:  # ← FIXED: was "if not col:"
            return {"type": "text", "intent": "SYLLABUS_QUERY",
                    "content": {"message": f"Let me explain **{name}**."},
                    "confidence": "Low"}

        try:
            # Find subject
            doc = await col.find_one(
                {"name": {"$regex": re.escape(name), "$options": "i"}}
            )
            if not doc:
                # Try normalized (hyphen ↔ space)
                norm = _normalize_name_for_search(name)
                doc = await col.find_one(
                    {"name": {"$regex": re.escape(norm), "$options": "i"}}
                )
            if not doc:
                # Try partial word match
                for w in [w for w in name.split() if len(w) > 3]:
                    doc = await col.find_one(
                        {"name": {"$regex": re.escape(w), "$options": "i"}}
                    )
                    if doc:
                        break

            if doc:
                subj_name = doc.get("name", name)
                subj_code = doc.get("code", "")
                
                # Get units from subject_units collection (NEW!)
                units = await self._get_units_from_subject_units(subj_code, subj_name)
                
                # Fallback to topics collection if no units found
                if not units:
                    units = await self._build_units_from_topics(subj_name, subj_code)
                
                # Get faculty
                faculty = await _search_faculty(subj_name, limit=3)
                faculty_list = [{"name": f.get("name", ""), "designation": f.get("designation", "")}
                                for f in faculty]

                return {
                    "type": "syllabus_breakdown", "intent": "SYLLABUS_QUERY",
                    "content": {
                        "code": subj_code,
                        "name": subj_name,
                        "semester": doc.get("semester"),
                        "credits": doc.get("credits", 0),
                        "description": doc.get("description", ""),
                        "learning_outcomes": doc.get("learning_outcomes", []),
                        "reference_books": doc.get("reference_books", []),
                        "units": units,
                        "faculty": faculty_list,
                    },
                    "confidence": "High" if units else "Medium",
                }
        except Exception as e:
            logger.warning(f"Subject query error: {e}")

        return {"type": "text", "intent": "SYLLABUS_QUERY",
                "content": {"message": f"No details found for **{name}**.",
                            "suggestions": [f"Who teaches {name}?", "Syllabus for sem 3"]},
                "confidence": "Low"}

    async def _get_units_from_subject_units(self, subject_code: str, subject_name: str) -> list:
        col = _col("subject_units")
        if col is None:  # ← FIXED
            return []
        
        try:
            # Build flexible search
            or_clauses = []
            if subject_code:
                or_clauses.append({"subject_code": {"$regex": re.escape(subject_code), "$options": "i"}})
            if subject_name:
                or_clauses.append({"subject_name": {"$regex": re.escape(subject_name), "$options": "i"}})
                norm = _normalize_name_for_search(subject_name)
                if norm != subject_name:
                    or_clauses.append({"subject_name": {"$regex": re.escape(norm), "$options": "i"}})
            
            if not or_clauses:
                return []
            
            cursor = col.find({"$or": or_clauses}).sort("unit_number", 1)
            units = []
            async for u in cursor:
                topics = u.get("topics", [])
                # Extract topic names from the topics array
                topic_names = []
                for t in topics:
                    if isinstance(t, str):
                        topic_names.append(t)
                    elif isinstance(t, dict):
                        topic_names.append(t.get("name", str(t)))
                    else:
                        topic_names.append(str(t))
                
                units.append({
                    "unit_number": u.get("unit_number", len(units) + 1),
                    "title": u.get("title", f"Unit {u.get('unit_number', len(units) + 1)}"),
                    "topics": topic_names,
                    "description": u.get("description", ""),
                    "hours": u.get("hours", ""),
                })
            
            if units:
                logger.info(f"Found {len(units)} units in subject_units for {subject_code or subject_name}")
            return units
            
        except Exception as e:
            logger.warning(f"subject_units query failed: {e}")
            return []

    async def _build_units_from_topics(self, subject_name: str, subject_code: str = "") -> list:
        col = _col("topics")
        if col is None:  # ← FIXED
            return []

        try:
            # Build flexible search
            name_norm = _normalize_name_for_search(subject_name)
            or_clauses = [
                {"subject_name": {"$regex": re.escape(subject_name), "$options": "i"}},
                {"subject_name": {"$regex": re.escape(name_norm), "$options": "i"}},
            ]
            if subject_code:
                or_clauses.append({"subject_code": {"$regex": re.escape(subject_code), "$options": "i"}})

            cursor = col.find({"$or": or_clauses}).limit(60)
            unit_map = {}
            async for t in cursor:
                ut = t.get("unit_title") or str(t.get("unit_number", "General"))
                key = str(ut).strip()
                if key not in unit_map:
                    unit_map[key] = {
                        "unit_number": t.get("unit_number", len(unit_map) + 1),
                        "title": t.get("unit_title", key),
                        "topics": [],
                    }
                tn = t.get("name", "")
                if tn and tn not in unit_map[key]["topics"]:
                    unit_map[key]["topics"].append(tn)
            return sorted(unit_map.values(), key=lambda u: u.get("unit_number", 0))
        except Exception as e:
            logger.warning(f"Topics search failed: {e}")
            return []

    async def _topic_query(self, topic_name: str):
        col = _col("topics")
        if col is not None:  # ← FIXED: was "if col:"
            try:
                doc = await col.find_one(
                    {"$or": [
                        {"name": {"$regex": re.escape(topic_name), "$options": "i"}},
                        {"keywords": {"$regex": re.escape(topic_name), "$options": "i"}},
                    ]}
                )

                if doc:
                    # Check if DB topic has actual content (diagnostic showed they're often empty)
                    defn = (doc.get("definition") or "").strip()
                    kps = doc.get("key_points") or []
                    has_content = bool(defn) or bool(kps)

                    if has_content:
                        subj = doc.get("subject_name", "")
                        return {
                            "type": "concept_explanation", "intent": "SYLLABUS_QUERY",
                            "content": {
                                "topic": doc.get("name", topic_name),
                                "subject": subj,
                                "definition": defn,
                                "explanation": (doc.get("explanation") or "").strip(),
                                "key_points": kps,
                                "examples": doc.get("examples", []),
                                "related_topics": doc.get("related_topics", []),
                                "exam_relevance": doc.get("exam_frequency"),
                                "suggestions": [f"Quiz me on {doc.get('name', topic_name)}",
                                                f"Resources for {subj or topic_name}",
                                                f"Who teaches {subj or topic_name}?"],
                            },
                            "confidence": "High",
                        }
                    # DB topic found but has no content — fall through to built-in KB
                    logger.debug(f"DB topic '{topic_name}' has empty content, trying built-in KB")
            except Exception as e:
                logger.warning(f"Topic DB search failed: {e}")

        # 2) Built-in KB — multiple matching strategies
        tl = topic_name.lower().strip()
        for key, data in CONCEPTS.items():
            if (key == tl or key in tl or tl in key
                    or any(w == key for w in tl.split())
                    or any(w in tl for w in key.split() if len(w) > 3)):
                return {
                    "type": "concept_explanation", "intent": "SYLLABUS_QUERY",
                    "content": {
                        **data,
                        "suggestions": [
                            f"Quiz me on {data['topic']}",
                            f"Resources for {data.get('subject', '')}",
                            f"Who teaches {data.get('subject', '')}?",
                        ],
                    },
                    "confidence": "High",
                }

        # 3) Not found — Low confidence for LLM to pick up
        clean = topic_name.strip("?!. ").title()
        return {
            "type": "text", "intent": "SYLLABUS_QUERY",
            "content": {"message": f"Let me explain **{clean}** for you.",
                        "_topic_hint": clean,
                        "suggestions": [f"Resources for {clean}", "Syllabus for sem 3"]},
            "confidence": "Low",
        }

    # ══════════════════════════════════════════════════════
    # QUIZ
    # ══════════════════════════════════════════════════════

    async def generate_quiz(self, topic: str, subject: str = "",
                            learning_outcomes: list = None,
                            num_questions: int = 4) -> Dict[str, Any]:
        try:
            from app.services.chatbot.llm_service import get_llm_service
            llm = get_llm_service()
            if llm and llm.is_available:
                quiz = await self._llm_quiz(llm, topic, subject, learning_outcomes, num_questions)
                if quiz:
                    return quiz
        except Exception as e:
            logger.warning(f"LLM quiz failed: {e}")
        return self._fallback_quiz(topic, subject)

    async def _llm_quiz(self, llm, topic, subject, los, n):
        prompt = (f"Generate {n} MCQs about '{topic}'{' in '+subject if subject else ''}.\n"
                  f"Return ONLY JSON array:\n"
                  f'[{{"q":"...","options":["A","B","C","D"],"correct":0,"explanation":"..."}}]')
        import json as jm
        resp = await llm.generate_response(prompt, context_type="syllabus")
        if not resp:
            return None
        try:
            t = resp.strip(); s = t.find("["); e = t.rfind("]")+1
            if s >= 0 and e > s:
                qs = jm.loads(t[s:e])
                if isinstance(qs, list) and qs:
                    return {"type": "quiz", "intent": "SYLLABUS_QUERY",
                            "content": {"topic": topic, "subject": subject,
                                        "questions": qs[:n], "total": min(len(qs), n),
                                        "source": "ai_generated"}, "confidence": "High"}
        except Exception:
            pass
        return None

    def _fallback_quiz(self, topic, subject):
        tl = topic.lower()
        bank = {
            "deadlock": [
                {"q": "Which is NOT a necessary condition for deadlock?",
                 "options": ["Mutual Exclusion", "Preemption", "Hold & Wait", "Circular Wait"],
                 "correct": 1, "explanation": "Preemption PREVENTS deadlock by allowing resources to be taken away."},
                {"q": "Banker's Algorithm is for deadlock ___?",
                 "options": ["Detection", "Avoidance", "Prevention", "Recovery"],
                 "correct": 1, "explanation": "Banker's Algorithm checks if a state is safe before granting resources."},
                {"q": "Which resource allocation graph indicates deadlock?",
                 "options": ["Linear graph", "Cycle with single instance resources", "Tree structure", "Disconnected graph"],
                 "correct": 1, "explanation": "A cycle in RAG with single instance resources definitely indicates deadlock."},
            ],
            "normalization": [
                {"q": "Which Normal Form removes partial dependencies?",
                 "options": ["1NF", "2NF", "3NF", "BCNF"],
                 "correct": 1, "explanation": "2NF eliminates partial dependencies on the primary key."},
                {"q": "1NF requires:",
                 "options": ["No multi-valued attributes", "No transitive dependencies", "Every determinant is a key", "No null values"],
                 "correct": 0, "explanation": "1NF requires atomic values - no repeating groups or multi-valued attributes."},
            ],
            "tcp": [
                {"q": "TCP uses which handshake for connection?",
                 "options": ["2-way", "3-way", "4-way", "5-way"],
                 "correct": 1, "explanation": "TCP uses 3-way handshake: SYN, SYN-ACK, ACK."},
                {"q": "TCP provides:",
                 "options": ["Unreliable delivery", "Connectionless service", "Ordered delivery", "Broadcast only"],
                 "correct": 2, "explanation": "TCP provides reliable, ordered delivery of data."},
            ],
            "bfs": [
                {"q": "BFS uses which data structure?",
                 "options": ["Stack", "Queue", "Heap", "Tree"],
                 "correct": 1, "explanation": "BFS uses Queue (FIFO) to explore level by level."},
            ],
            "dfs": [
                {"q": "DFS uses which data structure?",
                 "options": ["Queue", "Stack", "Heap", "Array"],
                 "correct": 1, "explanation": "DFS uses Stack (or recursion) to explore depth-first."},
            ],
        }
        for key, qs in bank.items():
            if key in tl:
                return {"type": "quiz", "intent": "SYLLABUS_QUERY",
                        "content": {"topic": topic, "subject": subject,
                                    "questions": qs, "total": len(qs), "source": "built_in"},
                        "confidence": "High"}
        return {"type": "text", "intent": "SYLLABUS_QUERY",
                "content": {"message": f"No quiz for **{topic}** yet. Try 'Quiz me on deadlock' or 'Quiz me on normalization'.",
                            "suggestions": ["Quiz me on deadlock", "Quiz me on TCP", "Quiz me on BFS"]},
                "confidence": "Medium"}

    # ══════════════════════════════════════════════════════
    # FACULTY
    # ══════════════════════════════════════════════════════

    async def _faculty(self, query, context, student_data):
        subj = self._get_faculty_subject(query)
        if subj:
            results = await _search_faculty(subj)
            if results:
                return {
                    "type": "faculty_list", "intent": "FACULTY_QUERY",
                    "content": {
                        "faculty": [_fmt_faculty(f) for f in results],
                        "count": len(results),
                        "message": f"Found {len(results)} faculty for **{subj}**",
                    },
                    "confidence": "High",
                }

            # Word-level fallback
            for w in [w for w in re.split(r'[\s/&,\-]+', subj) if len(w) >= 3]:
                results = await _search_faculty(w, limit=3)
                if results:
                    return {
                        "type": "faculty_list", "intent": "FACULTY_QUERY",
                        "content": {
                            "faculty": [_fmt_faculty(f) for f in results],
                            "count": len(results),
                            "message": f"Faculty related to **{subj}**:",
                        },
                        "confidence": "Medium",
                    }

            return {"type": "text", "intent": "FACULTY_QUERY",
                    "content": {"message": f"No faculty found for **{subj}**. Try checking the college website.",
                                "suggestions": ["Show all faculty", "Who teaches ML?", "Who teaches OS?"]},
                    "confidence": "Medium"}

        # List all faculty
        for col_name in ["faculty", "faculty_members"]:
            col = _col(col_name)
            if col is None:  # ← FIXED: was "if not col:"
                continue
            try:
                all_f = await col.find().limit(15).to_list(length=15)
                if all_f:
                    return {"type": "faculty_list", "intent": "FACULTY_QUERY",
                            "content": {"faculty": [_fmt_faculty(f) for f in all_f],
                                        "count": len(all_f), "message": "Faculty members:"},
                            "confidence": "Medium"}
            except Exception:
                continue

        return {"type": "text", "intent": "FACULTY_QUERY",
                "content": {"message": "Faculty database unavailable. Please check the college website."},
                "confidence": "Low"}

    # ══════════════════════════════════════════════════════
    # MENTOR
    # ══════════════════════════════════════════════════════

    async def _mentor(self, query, context, student_data):
        subj = _extract_subject(query)
        weak = (student_data or {}).get("weak_subjects", [])
        targets = []
        if subj:
            targets.append(subj)
        targets.extend(weak[:3])
        seen = set()
        targets = [t for t in targets if not (t in seen or seen.add(t))]

        if not targets:
            return {"type": "text", "intent": "MENTOR_QUERY",
                    "content": {"message": "Which subject do you need help with?",
                                "suggestions": ["Who should I contact for OS help?",
                                                "Who can help me with DBMS?"]},
                    "confidence": "Medium"}

        recs = []
        for s in targets:
            found = await _search_faculty(s, limit=3)
            for f in found:
                if not any(r["name"] == f.get("name") for r in recs):
                    d = _fmt_faculty(f)
                    d["match_reason"] = f"Teaches/specializes in {s}"
                    recs.append(d)

        if recs:
            return {"type": "mentor_recommendation", "intent": "MENTOR_QUERY",
                    "content": {"recommendations": recs[:5],
                                "based_on": {"weak_subjects": weak, "query_subject": subj},
                                "message": "Faculty who can help:"},
                    "confidence": "High"}

        return {"type": "text", "intent": "MENTOR_QUERY",
                "content": {"message": f"No faculty matched **{', '.join(targets)}**. Try contacting your department."},
                "confidence": "Low"}

    # ══════════════════════════════════════════════════════
    # PERFORMANCE (with actionable weakness suggestions)
    # ══════════════════════════════════════════════════════

    async def _performance(self, query, context, student_data):
        if not student_data:
            return {"type": "text", "intent": "PERFORMANCE_QUERY",
                    "content": {
                        "message": "I don't have your academic data yet.\n\n"
                                   "Go to **Student Dashboard** → **Academic Data** → Enter results.",
                        "suggestions": ["Career guidance", "Who teaches ML?"]},
                    "confidence": "High"}

        cgpa = student_data.get("cgpa")
        if cgpa is None or student_data.get("_partial"):
            name = student_data.get("name", "")
            return {"type": "text", "intent": "PERFORMANCE_QUERY",
                    "content": {
                        "message": f"Hey {name}! Add your grades in **Academic Data Entry** to get analysis.",
                        "suggestions": ["Career in data science", "Explain deadlock"]},
                    "confidence": "High"}

        name = student_data.get("name", "Student")
        weak = student_data.get("weak_subjects", [])[:5]
        strong = student_data.get("strong_subjects", [])[:5]
        sgpa_trend = student_data.get("sgpa_trend", [])
        latest_sgpa = student_data.get("latest_sgpa", 0)
        perf = student_data.get("performance_summary", {})
        trend = perf.get("trend", "stable")
        subjects = student_data.get("subjects", [])

        ql = query.lower()
        asking_improvement = any(w in ql for w in [
            "improve", "overcome", "weak", "help", "better", "how to",
            "suggestion", "tips", "struggle", "advice",
        ])

        subject_analysis = []
        for s in subjects[-10:]:
            score = s.get("score", 0)
            subject_analysis.append({
                "subject": s.get("name", "?"), "score": score,
                "grade": s.get("grade", ""),
                "status": "weak" if score < 50 else ("strong" if score >= 75 else "average"),
            })

        insights = []
        if trend == "improving":
            insights.append("📈 Your grades are improving — keep it up!")
        elif trend == "declining":
            insights.append("📉 Your grades dipped recently. Let's work on that together.")
        else:
            insights.append("➡️ Your performance is stable.")
        if weak:
            insights.append(f"🎯 Focus areas: **{', '.join(weak[:3])}**")
        if strong:
            insights.append(f"💪 Strong in: **{', '.join(strong[:3])}**")

        roadmap = []
        if cgpa >= 7.5:
            roadmap.append(f"✅ Eligible for most campus placements (CGPA: {cgpa})")
        elif cgpa >= 6.0:
            roadmap.append("🎯 Focus on raising CGPA above 7.0 for better opportunities")
        else:
            roadmap.append("⚠️ Priority: Clear backlogs and raise CGPA above 6.0")
        
        if weak:
            # Actionable suggestions for weak subjects
            roadmap.append(f"\n**📚 Action Plan for {weak[0]}:**")
            resources = self._get_curated_resources(weak[0])
            if resources:
                roadmap.append(f"• Study: *{resources[0].get('title', 'Online resources')}*")
            roadmap.append(f"• Ask: **'Resources for {weak[0]}'** for study materials")
            roadmap.append(f"• Find help: **'Who teaches {weak[0]}?'** to contact faculty")
            
            if asking_improvement and len(weak) > 1:
                roadmap.append(f"\n**For {weak[1]}:** Try 'Resources for {weak[1]}'")

        suggestions = [
            f"Resources for {weak[0]}" if weak else "Resources for OS",
            "Career guidance",
            f"Who teaches {weak[0]}?" if weak else "Who teaches ML?",
        ]

        return {
            "type": "performance_analysis", "intent": "PERFORMANCE_QUERY",
            "content": {
                "current_cgpa": cgpa, "latest_sgpa": latest_sgpa,
                "sgpa_trend": sgpa_trend, "trend_direction": trend,
                "weak_subjects": weak, "strong_subjects": strong,
                "subject_analysis": subject_analysis,
                "insights": insights, "recommendations": roadmap,
                "suggestions": suggestions,
                "profile": {"name": name, "branch": student_data.get("branch", "IT"),
                            "semester": student_data.get("semester", "?"), "cgpa": cgpa},
            }, "confidence": "High",
        }

    # ══════════════════════════════════════════════════════
    # CAREER
    # ══════════════════════════════════════════════════════

    async def _career(self, query, context, student_data):
        cn = _extract_career(query)
        if cn and self.career_repo:
            try:
                c = await self.career_repo.find_by_title(cn)
                if c:
                    return self._fmt_career_db(c, student_data)
            except Exception as e:
                logger.warning(f"Career DB: {e}")

        if cn and cn in CAREERS:
            c = CAREERS[cn]
            return {"type": "career_guidance", "intent": "CAREER_QUERY",
                    "content": {"career": {k: v for k, v in c.items() if k != "roadmap"},
                                "roadmap": c.get("roadmap", []),
                                "gap_analysis": self._gap(c.get("required_skills", []), student_data)},
                    "confidence": "High"}

        cl = [{"title": k, "demand": v["market_demand"], "description": v["description"][:100]}
              for k, v in CAREERS.items()]
        return {"type": "career_list", "intent": "CAREER_QUERY",
                "content": {"message": "Popular tech careers:", "careers": cl,
                            "hint": "Click a career or ask 'How to become a data scientist?'"},
                "confidence": "Medium"}

    # ══════════════════════════════════════════════════════
    # RESOURCES
    # ══════════════════════════════════════════════════════

    async def _resources(self, query, context, student_data):
        subj = _extract_subject(query)
        topic = self._get_topic(query)
        term = subj or topic or query.strip()

        col = _col("study_resources")
        resources = []
        if col is not None:  # ← FIXED: was "if col:"
            try:
                p = re.escape(term)
                cursor = col.find({"$or": [
                    {"title": {"$regex": p, "$options": "i"}},
                    {"tags": {"$regex": p, "$options": "i"}},
                ]}).limit(5)
                async for r in cursor:
                    resources.append({"title": r.get("title", ""), "type": r.get("type", ""),
                                      "url": r.get("url", ""), "platform": r.get("platform", ""),
                                      "rating": r.get("rating", 0), "difficulty": r.get("difficulty", "")})
            except Exception:
                pass

        if not resources:
            resources = self._get_curated_resources(term)

        return {"type": "resource_list", "intent": "RESOURCE_QUERY",
                "content": {"query": term, "resources": resources, "count": len(resources),
                            "message": f"Resources for **{term}**:",
                            "cta": {"text": "Browse resource library →", "url": "/resources"}},
                "confidence": "High" if resources else "Medium"}

    def _get_curated_resources(self, term):
        tl = term.lower()
        for key, res in _CURATED_RESOURCES.items():
            if key in tl or tl in key:
                return res
        # Generic fallback
        return [
            {"title": f"Search '{term}' on YouTube", "type": "Video",
             "url": f"https://www.youtube.com/results?search_query={term.replace(' ', '+')}+engineering+tutorial",
             "platform": "YouTube", "rating": 0, "difficulty": "All"},
            {"title": f"{term} - GeeksforGeeks", "type": "Notes",
             "url": f"https://www.geeksforgeeks.org/{term.lower().replace(' ', '-')}/",
             "platform": "GFG", "rating": 0, "difficulty": "All"},
        ]

    # ══════════════════════════════════════════════════════
    # ELECTIVE / STUDY / GENERIC / OOS
    # ══════════════════════════════════════════════════════

    async def _elective(self, q, c, s):
        recs = [
            {"name": "Machine Learning", "category": "PEC", "credits": 3,
             "reasons": ["High industry demand", "Builds on math and programming"],
             "career_paths": ["Data Scientist", "ML Engineer"]},
            {"name": "Cloud Computing", "category": "PEC", "credits": 3,
             "reasons": ["Essential for modern deployment", "Remote job opportunities"],
             "career_paths": ["DevOps Engineer", "Cloud Architect"]},
            {"name": "Cybersecurity", "category": "PEC", "credits": 3,
             "reasons": ["Growing field with job security", "Critical for every organization"],
             "career_paths": ["Security Analyst", "Penetration Tester"]},
        ]
        return {"type": "elective_recommendation", "intent": "ELECTIVE_QUERY",
                "content": {"recommendations": recs,
                            "advice": "Choose electives that align with your career goals and interests."},
                "confidence": "Medium"}

    async def _study_plan(self, q, c, s):
        weak = (s or {}).get("weak_subjects", [])
        subj = _extract_subject(q)
        focus = [subj] if subj else (weak[:4] if weak else ["All subjects"])
        sch = [{"subject": f, "priority": "high" if i < 2 else "normal", "suggested_hours": 2}
               for i, f in enumerate(focus)]
        return {"type": "study_plan", "intent": "STUDY_PLAN_QUERY",
                "content": {"daily_schedule": sch,
                            "total_daily_hours": sum(x["suggested_hours"] for x in sch),
                            "focus_areas": focus,
                            "exam_tips": ["Start preparation 3 weeks early",
                                          "Solve at least 3 previous year papers",
                                          "Focus on frequently asked topics",
                                          "Take regular breaks (Pomodoro technique)"]},
                "confidence": "Medium" if not s else "High"}

    async def _clarify(self, q, c, s):
        return {"type": "text", "intent": "CLARIFICATION",
                "content": {"message": "Could you be more specific?",
                            "suggestions": ["Explain deadlock", "Who teaches ML?", "Career in AI"]},
                "confidence": "High"}

    async def _generic(self, query, context, student_data):
        ql = query.lower().strip().rstrip("?!.")
        ql_exp = self._expand_sf(query).lower().strip().rstrip("?!.")
        n = f" {student_data['name']}" if student_data and student_data.get("name") else ""
        wc = len(query.strip().split())

        # Identity/capability questions
        if any(p in ql for p in ["who are you", "what are you", "what can you do"]):
            return {"type": "text", "intent": "GREETING",
                    "content": {"message": f"Hey{n}! I'm your **Academic Advisor** for FCRIT.\n\n"
                                           "I can help you with:\n\n"
                                           "📚 **Explain concepts** — OS, DBMS, ML, DSA\n"
                                           "👨‍🏫 **Find faculty** — who teaches what\n"
                                           "📊 **Analyze performance** — CGPA, weak areas\n"
                                           "💼 **Career guidance** — roadmaps & salaries\n"
                                           "🧠 **Quiz you** — test your knowledge\n"
                                           "📖 **Study resources** — videos, notes",
                                "suggestions": ["Explain deadlock", "Who teaches ML?", "Career in AI"]},
                    "confidence": "High"}
        
        # Thanks
        if any(w in ql for w in ["thank", "thanks", "thx"]) or "thank you" in ql_exp:
            return {"type": "text", "intent": "GREETING",
                    "content": {"message": f"You're welcome{n}! Happy to help. Anything else?",
                                "suggestions": ["Explain a topic", "Career guidance"]}, "confidence": "High"}
        
        # Acknowledgments
        if ql in ["ok", "okay", "alright", "sure", "got it", "cool", "nice", "great", "awesome",
                   "perfect", "fine", "understood", "hmm", "k"]:
            return {"type": "text", "intent": "GREETING",
                    "content": {"message": "Let me know if you need anything!",
                                "suggestions": ["Syllabus for sem 4", "Career options"]}, "confidence": "High"}
        
        # Goodbye
        if any(w in ql for w in ["bye", "goodbye", "see you", "later", "cya"]) or "good night" in ql_exp:
            return {"type": "text", "intent": "GREETING",
                    "content": {"message": f"Bye{n}! Good luck with your studies! 🎓"}, "confidence": "High"}
        
        # Greetings
        if any(w in ql_exp for w in ["good morning", "good afternoon", "good evening"]):
            g = "Good morning" if "morning" in ql_exp else ("Good afternoon" if "afternoon" in ql_exp else "Good evening")
            return {"type": "text", "intent": "GREETING",
                    "content": {"message": f"{g}{n}! How can I help you today?",
                                "suggestions": ["Explain a concept", "Show my grades"]}, "confidence": "High"}
        
        # Laughter
        if any(w in ql for w in ["haha", "lol", "lmao"]):
            return {"type": "text", "intent": "GREETING",
                    "content": {"message": f"😄 Need any academic help{n}?",
                                "suggestions": ["Explain a concept", "Career guidance"]}, "confidence": "High"}
        
        # Emotional support
        if any(w in ql for w in ["sad", "stressed", "anxious", "worried", "overwhelmed"]):
            return {"type": "text", "intent": "GREETING",
                    "content": {"message": f"I hear you{n}. Academic stress is real. Let me help:\n\n"
                                           "📋 Create a **study plan** to manage time\n"
                                           "🎯 Identify **weak areas** and suggest resources\n"
                                           "👨‍🏫 Find **faculty** you can talk to\n\n"
                                           "You've got this! 💪",
                                "suggestions": ["Create study plan", "Show my weak subjects", "Who can help me?"]},
                    "confidence": "High"}
        
        # Short query
        if wc <= 2:
            return {"type": "text", "intent": "GENERAL",
                    "content": {"message": f"Could you be more specific{n}?",
                                "suggestions": ["Explain deadlock", "Who teaches ML?", "Career in AI"]}, "confidence": "Medium"}

        # Default greeting
        return {"type": "text", "intent": "GREETING",
                "content": {"message": f"Hello{n}! I'm your Academic Advisor.\n\n"
                                       "I help with syllabus, faculty, performance, careers, quizzes & resources.",
                            "suggestions": ["Explain deadlock", "Syllabus for sem 4", "Career in AI/ML", "Show my performance"]},
                "confidence": "High"}

    def _oos(self):
        return {"type": "text", "intent": "OUT_OF_SCOPE",
                "content": {"message": "I can only help with **academic** topics. Let me know if you have questions about:",
                            "scope": ["📚 Syllabus & concepts", "👨‍🏫 Faculty info", "📊 Performance analysis", "💼 Career guidance"],
                            "suggestions": ["Explain deadlock", "Career in data science", "Who teaches ML?"]},
                "confidence": "High"}

    # ══════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════

    @staticmethod
    def _get_sem(q):
        for p in [r'sem(?:ester)?\s*(\d+)', r'(\d+)(?:st|nd|rd|th)\s*sem']:
            m = re.search(p, q.lower())
            if m:
                n = int(m.group(1))
                if 1 <= n <= 8:
                    return n
        return None

    @staticmethod
    def _get_topic(q):
        t = q.lower().strip()
        for pfx in ["explain", "define", "what is", "what are", "tell me about",
                     "describe", "how does", "meaning of", "definition of",
                     "types of", "teach me about", "teach me", "help me understand",
                     "what does", "what do", "how do"]:
            if t.startswith(pfx):
                t = t[len(pfx):].strip()
                break
        t = re.sub(r"\s+in\s+(os|dbms|dsa|cn|ml|ai|se|operating.*|database.*|computer.*|machine.*)\.?$", "", t, flags=re.I)
        t = re.sub(r'\s+mean\s*$', '', t)
        result = t.strip("?!. ")
        return result if result and len(result) >= 2 else None

    def _get_faculty_subject(self, q):
        ql = q.lower()
        for pat in [r'who\s+teaches\s+(.+?)[\?]?$',
                     r'(?:faculty|professor|teacher)\s+(?:for|of|in)\s+(.+?)[\?]?$']:
            m = re.search(pat, ql)
            if m:
                return _normalize_subject(m.group(1).strip())
        return _extract_subject(q)

    @staticmethod
    def _guess_subject_type(code: str) -> str:
        code = code.upper()
        if any(code.startswith(p) for p in ["FEC", "BSC", "ESC", "HSM", "PCC", "PWS"]):
            return "core"
        if "PEC" in code or "OEC" in code or "LLC" in code:
            return "elective"
        return "core"

    @staticmethod
    def _expand_sf(text):
        shorts = {"gn": "good night", "gm": "good morning", "tn": "thank you",
                  "ty": "thank you", "thx": "thanks", "ga": "good afternoon", "ge": "good evening"}
        return " ".join(shorts.get(w, w) for w in text.lower().split())

    def _fmt_career_db(self, c, sd):
        sal = getattr(c, "salary_range", None)
        sd_dict = {k: getattr(sal, k, "") for k in ["entry_level", "mid_level", "senior_level"]} if sal else {}
        rm = [{"step": getattr(s, "step", 0), "title": getattr(s, "title", ""),
               "description": getattr(s, "description", ""), "duration": getattr(s, "duration", "")}
              for s in (getattr(c, "roadmap", []) or [])]
        return {"type": "career_guidance", "intent": "CAREER_QUERY",
                "content": {"career": {"title": c.title, "description": c.description or "",
                                       "required_skills": c.required_skills or [],
                                       "market_demand": safe_enum_value(c.market_demand),
                                       "salary_range": sd_dict},
                            "roadmap": rm, "gap_analysis": self._gap(c.required_skills or [], sd)},
                "confidence": "High"}

    @staticmethod
    def _gap(skills, sd):
        if not sd:
            return None
        mine = set(s.lower() for s in (sd.get("skills", []) + sd.get("strong_subjects", [])))
        req = set(s.lower() for s in skills)
        m, mi = mine & req, req - mine
        return {"matching_skills": list(m), "missing_skills": list(mi),
                "skill_match_pct": int(len(m) / max(len(req), 1) * 100),
                "your_cgpa": sd.get("cgpa"), "recommended_cgpa": 7.0,
                "cgpa_meets": (sd.get("cgpa", 0) or 0) >= 7.0}