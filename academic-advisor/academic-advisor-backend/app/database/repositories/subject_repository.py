# app/database/repositories/subject_repository.py
"""
Subject Repository - Unified data access layer for syllabus/subject data
Supports both Beanie ODM and direct MongoDB access with fallback
"""

from typing import List, Optional, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)


class SubjectRepository:
    """
    Repository for accessing subject and syllabus data.
    Primary: Beanie ODM
    Fallback: Direct MongoDB access
    """
    
    def __init__(self):
        self._initialized = False
        self._db = None
        self._use_beanie = True  # Try Beanie first

    async def _ensure_initialized(self):
        """Lazy initialization to avoid circular import issues."""
        if self._initialized:
            return
        
        try:
            # Try to import Beanie models
            from app.models.syllabus import Subject, SubjectUnit, Topic
            self._use_beanie = True
            logger.info("SubjectRepository initialized with Beanie ODM")
        except Exception as e:
            logger.warning(f"Beanie models not available, using direct MongoDB: {e}")
            self._use_beanie = False
            await self._get_db()
        
        self._initialized = True

    async def _get_db(self):
        """Get direct database connection (fallback)."""
        if self._db is None:
            try:
                from app.database.connection import get_database
                self._db = get_database()
                logger.info("Direct MongoDB connection established")
            except Exception as e:
                logger.error(f"Failed to get database connection: {e}")
        return self._db

    # ══════════════════════════════════════════════════════
    # SUBJECT OPERATIONS
    # ══════════════════════════════════════════════════════

    async def get_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Get a subject by its code.
        
        Args:
            code: Subject code (e.g., "ITPCC301", "CSC401")
            
        Returns:
            Subject data as dictionary or None
        """
        await self._ensure_initialized()
        
        if self._use_beanie:
            return await self._get_by_code_beanie(code)
        else:
            return await self._get_by_code_mongodb(code)

    async def _get_by_code_beanie(self, code: str) -> Optional[Dict[str, Any]]:
        """Get subject using Beanie ODM."""
        try:
            from app.models.syllabus import Subject
            
            # Try exact match first
            subject = await Subject.find_one(Subject.code == code)
            if subject:
                return await self._subject_to_dict_with_units(subject)
            
            # Try case-insensitive match
            subject = await Subject.find_one(
                {"code": {"$regex": f"^{re.escape(code)}$", "$options": "i"}}
            )
            if subject:
                return await self._subject_to_dict_with_units(subject)
            
            return None
        except Exception as e:
            logger.error(f"Error getting subject by code {code} (Beanie): {e}")
            # Try MongoDB fallback
            return await self._get_by_code_mongodb(code)

    async def _get_by_code_mongodb(self, code: str) -> Optional[Dict[str, Any]]:
        """Get subject using direct MongoDB."""
        try:
            db = await self._get_db()
            if db is None:
                return None
            
            subjects_coll = db["subjects"]
            subject = await subjects_coll.find_one(
                {"code": {"$regex": f"^{re.escape(code)}$", "$options": "i"}}
            )
            
            if subject:
                return self._format_subject_mongodb(subject)
            return None
        except Exception as e:
            logger.error(f"Error getting subject by code {code} (MongoDB): {e}")
            return None

    async def get_subject_syllabus(self, code: str) -> Optional[Dict[str, Any]]:
        """Get complete subject with syllabus details (alias for get_by_code)."""
        return await self.get_by_code(code)

    async def get_subjects_by_semester(
        self, 
        semester: int, 
        department: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all subjects for a specific semester.
        
        Args:
            semester: Semester number (1-8)
            department: Optional department filter (e.g., "IT", "CSE")
            
        Returns:
            List of subject dictionaries
        """
        await self._ensure_initialized()
        
        if self._use_beanie:
            return await self._get_subjects_by_semester_beanie(semester, department)
        else:
            return await self._get_subjects_by_semester_mongodb(semester, department)

    async def _get_subjects_by_semester_beanie(
        self, 
        semester: int, 
        department: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get subjects by semester using Beanie."""
        try:
            from app.models.syllabus import Subject
            
            query = {"semester": semester}
            subjects = await Subject.find(query).to_list()
            
            results = []
            for s in subjects:
                data = await self._subject_to_dict_with_units(s)
                results.append(data)
            
            return results
        except Exception as e:
            logger.error(f"Error getting subjects by semester {semester} (Beanie): {e}")
            return await self._get_subjects_by_semester_mongodb(semester, department)

    async def _get_subjects_by_semester_mongodb(
        self, 
        semester: int, 
        department: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get subjects by semester using MongoDB."""
        try:
            db = await self._get_db()
            if db is None:
                return []
            
            subjects_coll = db["subjects"]
            query = {"semester": semester}
            
            cursor = subjects_coll.find(query)
            subjects = await cursor.to_list(length=100)
            
            return [self._format_subject_mongodb(s) for s in subjects]
        except Exception as e:
            logger.error(f"Error getting subjects by semester {semester} (MongoDB): {e}")
            return []

    async def get_all_subjects(
        self,
        department: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all subjects with optional filtering."""
        await self._ensure_initialized()
        
        if self._use_beanie:
            return await self._get_all_subjects_beanie(department, limit, skip)
        else:
            return await self._get_all_subjects_mongodb(department, limit, skip)

    async def _get_all_subjects_beanie(
        self,
        department: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all subjects using Beanie."""
        try:
            from app.models.syllabus import Subject
            
            query = {}
            if department:
                query["department"] = {"$regex": department, "$options": "i"}
            
            subjects = await Subject.find(query).skip(skip).limit(limit).to_list()
            
            return [self._subject_to_simple_dict(s) for s in subjects]
        except Exception as e:
            logger.error(f"Error getting all subjects (Beanie): {e}")
            return await self._get_all_subjects_mongodb(department, limit, skip)

    async def _get_all_subjects_mongodb(
        self,
        department: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all subjects using MongoDB."""
        try:
            db = await self._get_db()
            if db is None:
                return []
            
            subjects_coll = db["subjects"]
            query = {}
            
            cursor = subjects_coll.find(query).skip(skip).limit(limit)
            subjects = await cursor.to_list(length=limit)
            
            return [self._format_subject_mongodb(s) for s in subjects]
        except Exception as e:
            logger.error(f"Error getting all subjects (MongoDB): {e}")
            return []

    async def text_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Full-text search on subjects.
        Searches name, code, description, and learning outcomes.
        """
        await self._ensure_initialized()
        
        if self._use_beanie:
            return await self._text_search_beanie(query, limit)
        else:
            return await self._text_search_mongodb(query, limit)

    async def _text_search_beanie(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Text search using Beanie."""
        try:
            from app.models.syllabus import Subject
            
            query_escaped = re.escape(query)
            
            subjects = await Subject.find({
                "$or": [
                    {"name": {"$regex": query_escaped, "$options": "i"}},
                    {"code": {"$regex": query_escaped, "$options": "i"}},
                    {"description": {"$regex": query_escaped, "$options": "i"}},
                    {"learning_outcomes": {"$elemMatch": {"$regex": query_escaped, "$options": "i"}}},
                ]
            }).limit(limit).to_list()
            
            results = []
            for s in subjects:
                data = await self._subject_to_dict_with_units(s)
                results.append(data)
            
            return results
        except Exception as e:
            logger.error(f"Error in text search (Beanie): {e}")
            return await self._text_search_mongodb(query, limit)

    async def _text_search_mongodb(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Text search using MongoDB."""
        try:
            db = await self._get_db()
            if db is None:
                return []
            
            subjects_coll = db["subjects"]
            query_escaped = re.escape(query)
            
            cursor = subjects_coll.find({
                "$or": [
                    {"name": {"$regex": query_escaped, "$options": "i"}},
                    {"code": {"$regex": query_escaped, "$options": "i"}},
                ]
            }).limit(limit)
            
            subjects = await cursor.to_list(length=limit)
            return [self._format_subject_mongodb(s) for s in subjects]
        except Exception as e:
            logger.error(f"Error in text search (MongoDB): {e}")
            return []

    async def count_subjects(self, semester: Optional[int] = None) -> int:
        """Count total subjects."""
        await self._ensure_initialized()
        
        try:
            if self._use_beanie:
                from app.models.syllabus import Subject
                query = {"semester": semester} if semester else {}
                return await Subject.find(query).count()
            else:
                db = await self._get_db()
                if db is None:
                    return 0
                subjects_coll = db["subjects"]
                query = {"semester": semester} if semester else {}
                return await subjects_coll.count_documents(query)
        except Exception as e:
            logger.error(f"Error counting subjects: {e}")
            return 0

    # ══════════════════════════════════════════════════════
    # TOPIC OPERATIONS
    # ══════════════════════════════════════════════════════

    async def search_topics(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for topics matching the query.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of topic data with subject and unit context
        """
        await self._ensure_initialized()
        
        if self._use_beanie:
            return await self._search_topics_beanie(query, limit)
        else:
            return await self._search_topics_mongodb(query, limit)

    async def _search_topics_beanie(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search topics using Beanie."""
        try:
            from app.models.syllabus import Topic
            
            query_escaped = re.escape(query)
            
            topics = await Topic.find({
                "$or": [
                    {"name": {"$regex": query_escaped, "$options": "i"}},
                    {"keywords": {"$elemMatch": {"$regex": query_escaped, "$options": "i"}}},
                    {"definition": {"$regex": query_escaped, "$options": "i"}},
                    {"key_points": {"$elemMatch": {"$regex": query_escaped, "$options": "i"}}},
                ]
            }).limit(limit).to_list()
            
            results = []
            for topic in topics:
                result = await self._enrich_topic_with_context(topic)
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error searching topics (Beanie): {e}")
            return await self._search_topics_mongodb(query, limit)

    async def _search_topics_mongodb(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search topics using MongoDB."""
        try:
            db = await self._get_db()
            if db is None:
                return []
            
            topics_coll = db["topics"]
            query_escaped = re.escape(query.lower())
            
            cursor = topics_coll.find({
                "$or": [
                    {"name": {"$regex": query_escaped, "$options": "i"}},
                    {"keywords": {"$elemMatch": {"$regex": query_escaped, "$options": "i"}}},
                    {"definition": {"$regex": query_escaped, "$options": "i"}},
                ]
            }).limit(limit)
            
            topics = await cursor.to_list(length=limit)
            return [self._format_topic_result_mongodb(t) for t in topics]
        except Exception as e:
            logger.error(f"Error searching topics (MongoDB): {e}")
            return []

    async def find_topic_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find a specific topic by exact or partial name match.
        
        Args:
            name: Topic name to search for
            
        Returns:
            Topic data with subject and unit context, or None
        """
        await self._ensure_initialized()
        
        if self._use_beanie:
            result = await self._find_topic_by_name_beanie(name)
        else:
            result = await self._find_topic_by_name_mongodb(name)
        
        # If not found in database, return fallback
        if not result:
            result = self._generate_fallback_topic(name)
        
        return result

    async def _find_topic_by_name_beanie(self, name: str) -> Optional[Dict[str, Any]]:
        """Find topic using Beanie."""
        try:
            from app.models.syllabus import Topic
            
            name_escaped = re.escape(name)
            
            # Try exact match first
            topic = await Topic.find_one(
                {"name": {"$regex": f"^{name_escaped}$", "$options": "i"}}
            )
            
            # Try partial match
            if not topic:
                topic = await Topic.find_one(
                    {"name": {"$regex": name_escaped, "$options": "i"}}
                )
            
            # Search in keywords
            if not topic:
                topic = await Topic.find_one(
                    {"keywords": {"$elemMatch": {"$regex": name_escaped, "$options": "i"}}}
                )
            
            if topic:
                return await self._enrich_topic_with_context(topic)
            
            return None
        except Exception as e:
            logger.error(f"Error finding topic by name {name} (Beanie): {e}")
            return await self._find_topic_by_name_mongodb(name)

    async def _find_topic_by_name_mongodb(self, name: str) -> Optional[Dict[str, Any]]:
        """Find topic using MongoDB."""
        try:
            db = await self._get_db()
            if db is None:
                return None
            
            topics_coll = db["topics"]
            name_lower = name.lower().strip()
            name_escaped = re.escape(name_lower)
            
            # Try exact match first
            topic = await topics_coll.find_one(
                {"name": {"$regex": f"^{name_escaped}$", "$options": "i"}}
            )
            
            # Try partial match
            if not topic:
                topic = await topics_coll.find_one(
                    {"name": {"$regex": name_escaped, "$options": "i"}}
                )
            
            # Try keywords
            if not topic:
                topic = await topics_coll.find_one(
                    {"keywords": {"$elemMatch": {"$regex": name_escaped, "$options": "i"}}}
                )
            
            # Try definition search
            if not topic:
                topic = await topics_coll.find_one(
                    {"definition": {"$regex": name_escaped, "$options": "i"}}
                )
            
            if topic:
                return self._format_topic_result_mongodb(topic)
            
            return None
        except Exception as e:
            logger.error(f"Error finding topic '{name}' (MongoDB): {e}")
            return None

    async def _enrich_topic_with_context(self, topic) -> Dict[str, Any]:
        """Enrich a topic with its subject and unit context (Beanie)."""
        try:
            unit = None
            subject = None
            
            if hasattr(topic, 'unit') and topic.unit:
                try:
                    unit = await topic.unit.fetch()
                    if unit and hasattr(unit, 'subject') and unit.subject:
                        subject = await unit.subject.fetch()
                except Exception as e:
                    logger.debug(f"Could not fetch unit/subject: {e}")
            
            return {
                "topic": {
                    "name": topic.name,
                    "definition": topic.definition or self._get_topic_definition(topic.name),
                    "explanation": getattr(topic, 'explanation', '') or "",
                    "key_points": topic.key_points or [],
                    "examples": topic.examples or [],
                    "difficulty_level": getattr(topic, 'difficulty_level', 'medium'),
                    "exam_frequency": getattr(topic, 'exam_frequency', None),
                    "exam_weightage": getattr(topic, 'exam_weightage', None),
                    "related_topics": getattr(topic, 'related_topics', []) or [],
                    "prerequisites": getattr(topic, 'prerequisites', []) or [],
                    "keywords": topic.keywords or [],
                },
                "subject_code": subject.code if subject else "Unknown",
                "subject_name": subject.name if subject else "Unknown",
                "unit_title": unit.title if unit else "Unknown",
                "unit_number": unit.unit_number if unit else None,
            }
        except Exception as e:
            logger.error(f"Error enriching topic: {e}")
            return self._create_basic_topic_dict(topic.name)

    def _format_topic_result_mongodb(self, topic: Dict) -> Dict[str, Any]:
        """Format a topic document from MongoDB."""
        return {
            "topic": {
                "name": topic.get("name", ""),
                "definition": topic.get("definition", "") or self._get_topic_definition(topic.get("name", "")),
                "explanation": topic.get("explanation", ""),
                "key_points": topic.get("key_points", []),
                "examples": topic.get("examples", []),
                "difficulty_level": topic.get("difficulty_level", "medium"),
                "exam_frequency": topic.get("exam_frequency", "medium"),
                "exam_weightage": topic.get("exam_weightage"),
                "related_topics": topic.get("related_topics", []),
                "prerequisites": topic.get("prerequisites", []),
                "keywords": topic.get("keywords", []),
            },
            "subject_name": topic.get("subject_name", "Unknown"),
            "subject_code": topic.get("subject_code", ""),
            "unit_title": topic.get("unit_title", ""),
            "unit_number": topic.get("unit_number"),
        }

    def _generate_fallback_topic(self, name: str) -> Optional[Dict[str, Any]]:
        """Generate a fallback topic response for common CS topics."""
        definition = self._get_topic_definition(name)
        
        if definition:
            return {
                "topic": {
                    "name": name.title(),
                    "definition": definition,
                    "explanation": "",
                    "key_points": [],
                    "examples": [],
                    "difficulty_level": "medium",
                    "exam_frequency": None,
                    "exam_weightage": None,
                    "related_topics": [],
                    "prerequisites": [],
                    "keywords": [name.lower()],
                },
                "subject_code": "Unknown",
                "subject_name": "Unknown",
                "unit_title": "Unknown",
                "unit_number": None,
            }
        return None

    def _create_basic_topic_dict(self, name: str) -> Dict[str, Any]:
        """Create a basic topic dictionary."""
        return {
            "topic": {
                "name": name,
                "definition": self._get_topic_definition(name) or "",
                "explanation": "",
                "key_points": [],
                "examples": [],
                "difficulty_level": "medium",
                "exam_frequency": None,
                "exam_weightage": None,
                "related_topics": [],
                "prerequisites": [],
                "keywords": [name.lower()],
            },
            "subject_code": "Unknown",
            "subject_name": "Unknown",
            "unit_title": "Unknown",
            "unit_number": None,
        }

    def _get_topic_definition(self, topic_name: str) -> Optional[str]:
        """Get definition for common CS/IT topics (Extended database)."""
        definitions = {
            # Operating Systems
            "deadlock": "A deadlock is a situation in computing where two or more processes are unable to proceed because each is waiting for the other to release a resource. It occurs when processes hold resources while waiting for others, creating a circular dependency.",
            "mutex": "A mutex (mutual exclusion) is a synchronization primitive that prevents multiple threads from simultaneously accessing a shared resource. Only one thread can hold the mutex at a time.",
            "semaphore": "A semaphore is a synchronization mechanism used to control access to a common resource by multiple processes in a concurrent system. It maintains a counter to track available resources.",
            "process": "A process is an instance of a program in execution, with its own memory space, system resources, and execution context. It is the fundamental unit of work in an operating system.",
            "thread": "A thread is the smallest unit of execution within a process. Multiple threads share the process's memory and resources but have their own execution stack.",
            "scheduling": "CPU scheduling is the method by which the operating system decides which process runs at any given time. Common algorithms include FCFS, SJF, Round Robin, and Priority Scheduling.",
            "paging": "Paging is a memory management scheme that eliminates the need for contiguous memory allocation. Physical memory is divided into fixed-size blocks called frames, and logical memory into pages.",
            "virtual memory": "Virtual memory is a memory management technique that provides an idealized abstraction of the storage resources, creating an illusion of a very large main memory.",
            "segmentation": "Segmentation is a memory management technique that divides the address space into logical segments based on program structure (code, data, stack).",
            "thrashing": "Thrashing occurs when a computer's virtual memory is excessively swapping data between RAM and disk, degrading performance significantly.",
            
            # Database Management Systems
            "normalization": "Normalization is the process of organizing data in a database to reduce redundancy and improve data integrity. It involves dividing tables and establishing relationships between them.",
            "indexing": "Indexing is a data structure technique used to quickly locate and access data in a database table without scanning every row, similar to a book index.",
            "sql": "SQL (Structured Query Language) is a standard language for managing and manipulating relational databases. It includes commands for querying, inserting, updating, and deleting data.",
            "transaction": "A database transaction is a unit of work that is performed against a database. It follows ACID properties: Atomicity, Consistency, Isolation, and Durability.",
            "acid": "ACID is a set of properties that guarantee database transactions are processed reliably: Atomicity (all or nothing), Consistency (valid state), Isolation (concurrent execution), and Durability (permanent changes).",
            "join": "A JOIN clause is used to combine rows from two or more tables based on a related column. Types include INNER JOIN, LEFT JOIN, RIGHT JOIN, and FULL JOIN.",
            "foreign key": "A foreign key is a field in one table that references the primary key in another table, establishing a relationship between the tables.",
            "primary key": "A primary key is a unique identifier for each record in a database table. It must contain unique values and cannot contain NULL values.",
            "er model": "An Entity-Relationship (ER) model is a conceptual data model that defines data entities and their relationships using diagrams.",
            
            # Computer Networks
            "tcp": "TCP (Transmission Control Protocol) is a connection-oriented protocol that provides reliable, ordered, and error-checked delivery of data between applications over an IP network.",
            "udp": "UDP (User Datagram Protocol) is a connectionless protocol that provides fast but unreliable data transmission without guaranteeing delivery or order.",
            "http": "HTTP (Hypertext Transfer Protocol) is an application-layer protocol for transmitting hypermedia documents. It follows a request-response model between client and server.",
            "https": "HTTPS (HTTP Secure) is an extension of HTTP that uses SSL/TLS encryption to secure communication between client and server.",
            "routing": "Routing is the process of selecting paths in a network along which to send network traffic. Routers use routing tables and protocols to determine the best path.",
            "osi model": "The OSI (Open Systems Interconnection) model is a conceptual framework with 7 layers that standardizes the functions of a communication system: Physical, Data Link, Network, Transport, Session, Presentation, and Application.",
            "ip address": "An IP address is a unique numerical identifier assigned to each device on a network, used for routing and communication.",
            "subnet": "A subnet (subnetwork) is a logical subdivision of an IP network, improving network performance and security.",
            "dns": "DNS (Domain Name System) translates human-readable domain names into IP addresses that computers use to identify each other.",
            "firewall": "A firewall is a network security system that monitors and controls incoming and outgoing network traffic based on predetermined security rules.",
            "arp": "ARP (Address Resolution Protocol) maps IP addresses to physical MAC addresses in a local network.",
            
            # Data Structures
            "linked list": "A linked list is a linear data structure where elements are stored in nodes, and each node points to the next node in the sequence. Unlike arrays, elements are not stored in contiguous memory.",
            "binary tree": "A binary tree is a hierarchical data structure in which each node has at most two children, referred to as the left child and the right child.",
            "bst": "A Binary Search Tree (BST) is a binary tree where each node's left subtree contains only values less than the node, and the right subtree contains only values greater.",
            "graph": "A graph is a non-linear data structure consisting of vertices (nodes) and edges that connect pairs of vertices. Graphs can be directed or undirected.",
            "hash table": "A hash table is a data structure that implements an associative array, using a hash function to compute an index into an array of buckets from which the desired value can be found.",
            "stack": "A stack is a linear data structure that follows the LIFO (Last In, First Out) principle. Elements are added and removed from the same end, called the top.",
            "queue": "A queue is a linear data structure that follows the FIFO (First In, First Out) principle. Elements are added at the rear and removed from the front.",
            "heap": "A heap is a specialized tree-based data structure that satisfies the heap property: in a max heap, parent nodes are greater than children; in a min heap, parent nodes are smaller.",
            "trie": "A trie is a tree-like data structure used for efficient retrieval of strings, commonly used in autocomplete and spell-checking applications.",
            "array": "An array is a collection of elements stored in contiguous memory locations, accessible by an index.",
            
            # Algorithms
            "sorting": "Sorting is the process of arranging elements in a specific order (ascending or descending). Common algorithms include Quick Sort, Merge Sort, Bubble Sort, and Heap Sort.",
            "searching": "Searching is the process of finding a specific element in a data structure. Common algorithms include Linear Search, Binary Search, and Hash-based Search.",
            "dynamic programming": "Dynamic programming is an algorithmic technique that solves complex problems by breaking them into simpler subproblems and storing results to avoid redundant computation.",
            "greedy algorithm": "A greedy algorithm makes the locally optimal choice at each step with the hope of finding a global optimum. Examples include Dijkstra's algorithm and Huffman coding.",
            "divide and conquer": "Divide and conquer is an algorithm design paradigm that breaks a problem into smaller subproblems, solves them recursively, and combines their solutions.",
            "backtracking": "Backtracking is an algorithmic technique that tries different solutions and abandons them if they don't satisfy the constraints (e.g., N-Queens problem).",
            "bfs": "BFS (Breadth-First Search) is a graph traversal algorithm that explores all neighbors at the present depth before moving to nodes at the next depth level.",
            "dfs": "DFS (Depth-First Search) is a graph traversal algorithm that explores as far as possible along each branch before backtracking.",
            "dijkstra": "Dijkstra's algorithm finds the shortest path from a source vertex to all other vertices in a weighted graph with non-negative edge weights.",
            
            # Machine Learning & AI
            "regression": "Regression is a supervised learning technique used to predict continuous numerical values based on input features. Examples include Linear Regression and Polynomial Regression.",
            "classification": "Classification is a supervised learning technique used to predict categorical labels. Examples include Logistic Regression, Decision Trees, and SVM.",
            "clustering": "Clustering is an unsupervised learning technique that groups similar data points together. Examples include K-Means, Hierarchical Clustering, and DBSCAN.",
            "neural network": "A neural network is a computational model inspired by biological neural networks, consisting of interconnected nodes (neurons) that process information using connectionist approaches.",
            "supervised learning": "Supervised learning is a machine learning paradigm where the model learns from labeled training data to make predictions on new, unseen data.",
            "unsupervised learning": "Unsupervised learning is a machine learning paradigm where the model finds patterns in unlabeled data without explicit guidance.",
            "overfitting": "Overfitting occurs when a machine learning model learns the training data too well, including noise, resulting in poor performance on new data.",
            "gradient descent": "Gradient descent is an optimization algorithm used to minimize a function by iteratively moving in the direction of steepest descent.",
            
            # Software Engineering
            "agile": "Agile is an iterative software development methodology that emphasizes flexibility, collaboration, and customer feedback through short development cycles called sprints.",
            "scrum": "Scrum is an Agile framework for managing product development, using fixed-length iterations called sprints and defined roles (Scrum Master, Product Owner, Team).",
            "waterfall": "Waterfall is a sequential software development model where each phase must be completed before the next begins, following a linear progression.",
            "cicd": "CI/CD (Continuous Integration/Continuous Deployment) is a DevOps practice that automates code integration, testing, and deployment.",
            "version control": "Version control is a system that tracks changes to files over time, allowing multiple developers to collaborate and revert to previous versions (e.g., Git).",
            "design pattern": "A design pattern is a reusable solution to a commonly occurring problem in software design. Examples include Singleton, Factory, and Observer patterns.",
            
            # Web Development
            "rest": "REST (Representational State Transfer) is an architectural style for designing networked applications, using stateless HTTP requests for CRUD operations.",
            "api": "An API (Application Programming Interface) is a set of protocols and tools that allows different software applications to communicate with each other.",
            "json": "JSON (JavaScript Object Notation) is a lightweight data interchange format that is easy for humans to read and write and easy for machines to parse.",
            "oauth": "OAuth is an open standard for access delegation, commonly used for token-based authentication without exposing passwords.",
            "cors": "CORS (Cross-Origin Resource Sharing) is a security mechanism that allows or restricts resources on a web page to be requested from another domain.",
            
            # Mathematics & Theory
            "vector space": "A vector space is a mathematical structure formed by a collection of vectors that can be added together and multiplied by scalars, following specific axioms.",
            "linear mapping": "A linear mapping (or linear transformation) is a function between vector spaces that preserves vector addition and scalar multiplication operations.",
            "matrix": "A matrix is a rectangular array of numbers arranged in rows and columns. Matrices are used in linear algebra for representing linear transformations and solving systems of equations.",
            "eigenvalue": "An eigenvalue is a scalar associated with a linear transformation. When a matrix is multiplied by its eigenvector, the result is the eigenvector scaled by the eigenvalue.",
            "big o notation": "Big O notation describes the upper bound of an algorithm's time or space complexity, expressing how performance scales with input size.",
            "np complete": "NP-Complete problems are decision problems for which no known polynomial-time solution exists, but solutions can be verified in polynomial time.",
        }
        
        name_lower = topic_name.lower().strip()
        
        # Direct match
        if name_lower in definitions:
            return definitions[name_lower]
        
        # Partial match
        for key, definition in definitions.items():
            if key in name_lower or name_lower in key:
                return definition
        
        return None

    # ══════════════════════════════════════════════════════
    # UNIT OPERATIONS
    # ══════════════════════════════════════════════════════

    async def get_units_by_subject(self, subject_code: str) -> List[Dict[str, Any]]:
        """Get all units for a subject."""
        await self._ensure_initialized()
        
        try:
            subject_data = await self.get_by_code(subject_code)
            if subject_data and "units" in subject_data:
                return subject_data["units"]
            return []
        except Exception as e:
            logger.error(f"Error getting units for subject {subject_code}: {e}")
            return []

    # ══════════════════════════════════════════════════════
    # HELPER METHODS - BEANIE
    # ══════════════════════════════════════════════════════

    def _subject_to_simple_dict(self, subject) -> Dict[str, Any]:
        """Convert Subject document to simple dict (without units)."""
        return {
            "code": subject.code,
            "name": subject.name,
            "semester": subject.semester,
            "credits": subject.credits,
            "subject_type": subject.subject_type,
            "category": getattr(subject, 'category', None),
            "description": getattr(subject, 'description', ''),
            "is_active": getattr(subject, 'is_active', True),
        }

    async def _subject_to_dict_with_units(self, subject) -> Dict[str, Any]:
        """Convert Subject document to dict with units and topics (Beanie)."""
        try:
            from app.models.syllabus import SubjectUnit, Topic
            
            # Fetch units for this subject
            units = await SubjectUnit.find(
                SubjectUnit.subject.id == subject.id
            ).sort("unit_number").to_list()
            
            units_data = []
            for unit in units:
                # Fetch topics for this unit
                topics = await Topic.find(Topic.unit.id == unit.id).to_list()
                
                units_data.append({
                    "unit_number": unit.unit_number,
                    "title": unit.title,
                    "description": getattr(unit, 'description', ''),
                    "lecture_hours": getattr(unit, 'lecture_hours', None),
                    "keywords": getattr(unit, 'keywords', []),
                    "topics": [
                        {
                            "name": t.name,
                            "definition": getattr(t, 'definition', ''),
                            "key_points": t.key_points or [],
                            "examples": t.examples or [],
                            "difficulty_level": getattr(t, 'difficulty_level', 'medium'),
                            "keywords": t.keywords or [],
                        }
                        for t in topics
                    ]
                })
            
            return {
                "code": subject.code,
                "name": subject.name,
                "semester": subject.semester,
                "credits": subject.credits,
                "subject_type": subject.subject_type,
                "category": getattr(subject, 'category', None),
                "teaching_scheme": subject.teaching_scheme or {},
                "description": getattr(subject, 'description', ''),
                "learning_outcomes": subject.learning_outcomes or [],
                "reference_books": subject.reference_books or [],
                "prerequisites": subject.prerequisites or [],
                "examination_scheme": subject.examination_scheme or {},
                "is_active": getattr(subject, 'is_active', True),
                "units": units_data,
            }
        except Exception as e:
            logger.error(f"Error converting subject to dict: {e}")
            return self._subject_to_simple_dict(subject)

    # ══════════════════════════════════════════════════════
    # HELPER METHODS - MONGODB
    # ══════════════════════════════════════════════════════

    def _format_subject_mongodb(self, subject: Dict) -> Dict[str, Any]:
        """Format a subject document from MongoDB."""
        return {
            "code": subject.get("code", ""),
            "name": subject.get("name", ""),
            "semester": subject.get("semester", 0),
            "credits": subject.get("credits", 0),
            "subject_type": subject.get("subject_type", "core"),
            "description": subject.get("description", ""),
            "learning_outcomes": subject.get("learning_outcomes", []),
            "reference_books": subject.get("reference_books", []),
            "prerequisites": subject.get("prerequisites", []),
            "teaching_scheme": subject.get("teaching_scheme", {}),
            "examination_scheme": subject.get("examination_scheme", {}),
            "units": subject.get("units", []),
        }

    # ══════════════════════════════════════════════════════
    # API CONVERSION HELPERS
    # ══════════════════════════════════════════════════════

    def subject_to_dict(self, subject: Dict[str, Any]) -> Dict[str, Any]:
        """Convert subject data to API-friendly dict."""
        return {
            "code": subject.get("code"),
            "name": subject.get("name"),
            "semester": subject.get("semester"),
            "credits": subject.get("credits"),
            "subject_type": subject.get("subject_type"),
            "category": subject.get("category"),
            "teaching_scheme": subject.get("teaching_scheme", {}),
            "description": subject.get("description"),
            "learning_outcomes": subject.get("learning_outcomes", []),
            "reference_books": subject.get("reference_books", []),
            "prerequisites": subject.get("prerequisites", []),
            "examination_scheme": subject.get("examination_scheme", {}),
            "is_active": subject.get("is_active", True),
            "units": subject.get("units", []),
        }

    def topic_to_dict(self, topic_result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert topic search result to API-friendly dict."""
        topic = topic_result.get("topic", {})
        return {
            "name": topic.get("name"),
            "definition": topic.get("definition"),
            "explanation": topic.get("explanation"),
            "key_points": topic.get("key_points", []),
            "examples": topic.get("examples", []),
            "difficulty_level": topic.get("difficulty_level", "medium"),
            "exam_frequency": topic.get("exam_frequency"),
            "exam_weightage": topic.get("exam_weightage"),
            "related_topics": topic.get("related_topics", []),
            "prerequisites": topic.get("prerequisites", []),
            "keywords": topic.get("keywords", []),
            "subject_code": topic_result.get("subject_code"),
            "subject_name": topic_result.get("subject_name"),
            "unit_title": topic_result.get("unit_title"),
            "unit_number": topic_result.get("unit_number"),
        }