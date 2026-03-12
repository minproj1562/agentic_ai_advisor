# scripts/add_more_topics.py
"""
Add standalone topics to database for chatbot - WORKING VERSION
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError


# ══════════════════════════════════════════════════════════
# TOPIC DEFINITIONS
# ══════════════════════════════════════════════════════════

TOPICS = {
    # Operating Systems
    "deadlock": {
        "name": "Deadlock",
        "subject_name": "Operating Systems",
        "subject_code": "OS",
        "definition": "A deadlock is a situation in computing where two or more processes are unable to proceed because each is waiting for the other to release a resource. It occurs when processes hold resources while waiting for others, creating a circular dependency.",
        "explanation": "Deadlock occurs when four conditions are met simultaneously: Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait. Breaking any one of these conditions prevents deadlock.",
        "key_points": [
            "Four necessary conditions: Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait",
            "Prevention strategies involve breaking at least one condition",
            "Detection uses Resource Allocation Graph (RAG)",
            "Recovery through process termination or resource preemption",
            "Banker's Algorithm is used for deadlock avoidance"
        ],
        "examples": [
            "Two trains approaching each other on a single track",
            "Dining Philosophers Problem",
            "Two processes each holding a resource the other needs"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["deadlock", "deadlocks", "circular wait", "resource allocation"]
    },
    "process": {
        "name": "Process",
        "subject_name": "Operating Systems",
        "subject_code": "OS",
        "definition": "A process is an instance of a program in execution, with its own memory space, system resources, and execution context. It is the fundamental unit of work in an operating system.",
        "key_points": [
            "Process states: New, Ready, Running, Waiting, Terminated",
            "PCB (Process Control Block) stores process information",
            "Context switching saves/restores process state",
            "Inter-process communication (IPC) mechanisms",
            "Process vs Thread distinction"
        ],
        "examples": [
            "Running a web browser creates a process",
            "Each Chrome tab runs as a separate process"
        ],
        "difficulty_level": "easy",
        "exam_frequency": "high",
        "keywords": ["process", "pcb", "process control block", "process states"]
    },
    "thread": {
        "name": "Thread",
        "subject_name": "Operating Systems",
        "subject_code": "OS",
        "definition": "A thread is the smallest unit of execution within a process. Multiple threads can exist within the same process and share resources like memory and file handles.",
        "key_points": [
            "Threads share code, data, and files of the process",
            "Each thread has its own stack and registers",
            "Faster context switching than processes",
            "Types: User-level threads, Kernel-level threads",
            "Multithreading enables parallel execution"
        ],
        "examples": [
            "Word processor: one thread for editing, another for spell-check",
            "Web server handling multiple requests with threads"
        ],
        "difficulty_level": "easy",
        "exam_frequency": "high",
        "keywords": ["thread", "threads", "multithreading", "concurrency"]
    },
    "mutex": {
        "name": "Mutex (Mutual Exclusion)",
        "subject_name": "Operating Systems",
        "subject_code": "OS",
        "definition": "A mutex is a synchronization primitive that grants exclusive access to a shared resource to only one thread at a time, preventing race conditions in concurrent programming.",
        "key_points": [
            "Binary nature: locked or unlocked",
            "Only the thread that locks can unlock (ownership)",
            "Prevents race conditions in critical sections",
            "Can cause deadlock if not used properly",
            "Used for protecting shared data structures"
        ],
        "examples": [
            "Protecting a shared counter variable",
            "Ensuring only one thread writes to a file at a time"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "medium",
        "keywords": ["mutex", "mutual exclusion", "lock", "synchronization"]
    },
    "semaphore": {
        "name": "Semaphore",
        "subject_name": "Operating Systems",
        "subject_code": "OS",
        "definition": "A semaphore is a synchronization primitive that controls access to a common resource by multiple processes using a counter variable.",
        "explanation": "Unlike mutex which is binary, semaphores can have a count greater than 1, allowing multiple threads to access a resource up to a limit.",
        "key_points": [
            "Binary Semaphore: Similar to mutex (0 or 1)",
            "Counting Semaphore: Can be any non-negative integer",
            "Wait (P) operation: Decrement and block if negative",
            "Signal (V) operation: Increment and wake waiting process",
            "No ownership concept unlike mutex"
        ],
        "examples": [
            "Producer-Consumer problem",
            "Reader-Writer problem",
            "Limiting concurrent database connections"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["semaphore", "semaphores", "wait", "signal", "p operation", "v operation"]
    },
    "paging": {
        "name": "Paging",
        "subject_name": "Operating Systems",
        "subject_code": "OS",
        "definition": "Paging is a memory management scheme that eliminates the need for contiguous memory allocation by dividing physical memory into fixed-size blocks called frames and logical memory into pages.",
        "key_points": [
            "Physical memory divided into frames",
            "Logical memory divided into pages",
            "Page table maps pages to frames",
            "Eliminates external fragmentation",
            "May have internal fragmentation"
        ],
        "examples": [
            "Virtual memory implementation",
            "Running programs larger than physical RAM"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["paging", "page table", "page fault", "frame", "virtual memory"]
    },
    "scheduling": {
        "name": "CPU Scheduling",
        "subject_name": "Operating Systems",
        "subject_code": "OS",
        "definition": "CPU scheduling determines which process runs at any given time, optimizing CPU utilization and system performance.",
        "key_points": [
            "FCFS (First Come First Serve) - Simple but convoy effect",
            "SJF (Shortest Job First) - Optimal but starvation possible",
            "Round Robin - Time quantum based, fair",
            "Priority Scheduling - Based on priority values",
            "Multilevel Queue Scheduling"
        ],
        "examples": [
            "Time-sharing operating systems",
            "Real-time scheduling in embedded systems"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["scheduling", "fcfs", "sjf", "round robin", "priority", "cpu scheduling"]
    },
    "virtual memory": {
        "name": "Virtual Memory",
        "subject_name": "Operating Systems",
        "subject_code": "OS",
        "definition": "Virtual memory is a memory management technique that provides an idealized abstraction of storage, creating an illusion of a very large main memory.",
        "key_points": [
            "Allows running programs larger than physical RAM",
            "Uses disk as extended memory (swap space)",
            "Demand paging - load pages only when needed",
            "Page replacement algorithms: LRU, FIFO, Optimal",
            "Thrashing occurs when too many page faults"
        ],
        "examples": [
            "Running multiple large applications simultaneously",
            "Memory-intensive games on limited RAM"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["virtual memory", "swap", "page replacement", "thrashing", "demand paging"]
    },
    
    # Database
    "normalization": {
        "name": "Normalization",
        "subject_name": "Database Management Systems",
        "subject_code": "DBMS",
        "definition": "Normalization is the process of organizing data in a database to reduce redundancy and improve data integrity by dividing tables and defining relationships between them.",
        "explanation": "Normalization involves organizing columns and tables to minimize data redundancy. Each normal form builds on the previous one.",
        "key_points": [
            "1NF: Atomic values, no repeating groups",
            "2NF: 1NF + No partial dependencies",
            "3NF: 2NF + No transitive dependencies",
            "BCNF: Every determinant is a candidate key",
            "Denormalization may be used for performance"
        ],
        "examples": [
            "Splitting a flat student-course table into separate tables",
            "Removing redundant address information"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["normalization", "1nf", "2nf", "3nf", "bcnf", "normal forms"]
    },
    "sql": {
        "name": "SQL (Structured Query Language)",
        "subject_name": "Database Management Systems",
        "subject_code": "DBMS",
        "definition": "SQL is a standard programming language used for managing and manipulating relational databases, including querying, inserting, updating, and deleting data.",
        "key_points": [
            "DDL: CREATE, ALTER, DROP (schema operations)",
            "DML: SELECT, INSERT, UPDATE, DELETE (data operations)",
            "DCL: GRANT, REVOKE (permissions)",
            "TCL: COMMIT, ROLLBACK (transactions)",
            "Joins: INNER, LEFT, RIGHT, FULL OUTER"
        ],
        "examples": [
            "SELECT * FROM students WHERE grade > 80",
            "INSERT INTO courses VALUES (101, 'DBMS', 4)"
        ],
        "difficulty_level": "easy",
        "exam_frequency": "high",
        "keywords": ["sql", "query", "select", "insert", "update", "delete", "ddl", "dml"]
    },
    "transaction": {
        "name": "Database Transaction",
        "subject_name": "Database Management Systems",
        "subject_code": "DBMS",
        "definition": "A database transaction is a unit of work that follows ACID properties, ensuring data integrity even in case of failures.",
        "key_points": [
            "Atomicity: All or nothing execution",
            "Consistency: Valid state transitions only",
            "Isolation: Concurrent transactions don't interfere",
            "Durability: Committed changes are permanent",
            "Managed using COMMIT and ROLLBACK"
        ],
        "examples": [
            "Bank transfer between two accounts",
            "E-commerce checkout process"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["transaction", "acid", "atomicity", "consistency", "isolation", "durability"]
    },
    "indexing": {
        "name": "Database Indexing",
        "subject_name": "Database Management Systems",
        "subject_code": "DBMS",
        "definition": "Indexing is a data structure technique used to quickly locate and access data in a database table without scanning every row.",
        "key_points": [
            "B-Tree indexes (most common)",
            "Hash indexes for equality searches",
            "Clustered vs Non-clustered indexes",
            "Trade-off: faster reads, slower writes",
            "Index maintenance overhead"
        ],
        "examples": [
            "Phone book as an index example",
            "Database primary key index"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "medium",
        "keywords": ["indexing", "index", "b-tree", "hash index", "clustered"]
    },
    "join": {
        "name": "SQL Joins",
        "subject_name": "Database Management Systems",
        "subject_code": "DBMS",
        "definition": "SQL joins combine rows from two or more tables based on related columns between them.",
        "key_points": [
            "INNER JOIN: Returns matching rows only",
            "LEFT JOIN: All left rows + matching right",
            "RIGHT JOIN: All right rows + matching left",
            "FULL OUTER JOIN: All rows from both tables",
            "CROSS JOIN: Cartesian product"
        ],
        "examples": [
            "SELECT * FROM students JOIN courses ON students.id = courses.student_id",
            "Finding employees with their departments"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["join", "inner join", "left join", "right join", "outer join"]
    },
    
    # Networking
    "tcp": {
        "name": "TCP (Transmission Control Protocol)",
        "subject_name": "Computer Networks",
        "subject_code": "CN",
        "definition": "TCP is a connection-oriented protocol that provides reliable, ordered, and error-checked delivery of data between applications over an IP network.",
        "key_points": [
            "Connection-oriented (three-way handshake)",
            "Reliable delivery with acknowledgments",
            "Flow control using sliding window",
            "Congestion control mechanisms",
            "Ordered data delivery"
        ],
        "examples": [
            "HTTP/HTTPS web browsing",
            "Email (SMTP, IMAP)",
            "File transfer (FTP)",
            "SSH connections"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["tcp", "transmission control protocol", "reliable", "connection-oriented"]
    },
    "udp": {
        "name": "UDP (User Datagram Protocol)",
        "subject_name": "Computer Networks",
        "subject_code": "CN",
        "definition": "UDP is a connectionless protocol that provides fast but unreliable data transmission without guaranteeing delivery or order.",
        "key_points": [
            "Connectionless - no handshake required",
            "No guaranteed delivery",
            "No ordering of packets",
            "Lower overhead than TCP",
            "Suitable for real-time applications"
        ],
        "examples": [
            "Video streaming",
            "Online gaming",
            "DNS queries",
            "VoIP calls"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["udp", "user datagram protocol", "connectionless", "unreliable"]
    },
    "http": {
        "name": "HTTP (Hypertext Transfer Protocol)",
        "subject_name": "Computer Networks",
        "subject_code": "CN",
        "definition": "HTTP is an application-layer protocol for transmitting hypermedia documents, forming the foundation of data communication on the web.",
        "key_points": [
            "Request-response model",
            "Stateless protocol",
            "Methods: GET, POST, PUT, DELETE, PATCH",
            "Status codes: 200 (OK), 404 (Not Found), 500 (Server Error)",
            "HTTPS adds encryption via TLS/SSL"
        ],
        "examples": [
            "Web browsing",
            "REST API communication",
            "File downloads"
        ],
        "difficulty_level": "easy",
        "exam_frequency": "high",
        "keywords": ["http", "https", "web", "request", "response", "rest"]
    },
    "osi model": {
        "name": "OSI Model",
        "subject_name": "Computer Networks",
        "subject_code": "CN",
        "definition": "The OSI (Open Systems Interconnection) model is a conceptual framework with 7 layers that standardizes network communication functions.",
        "key_points": [
            "Layer 7: Application (HTTP, FTP, SMTP)",
            "Layer 6: Presentation (Encryption, Compression)",
            "Layer 5: Session (Connection management)",
            "Layer 4: Transport (TCP, UDP)",
            "Layer 3: Network (IP, Routing)",
            "Layer 2: Data Link (MAC, Switching)",
            "Layer 1: Physical (Cables, Signals)"
        ],
        "examples": [
            "HTTP operates at Application layer",
            "TCP operates at Transport layer",
            "IP operates at Network layer",
            "Ethernet operates at Data Link layer"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["osi", "osi model", "7 layers", "network layers"]
    },
    "ip": {
        "name": "IP (Internet Protocol)",
        "subject_name": "Computer Networks",
        "subject_code": "CN",
        "definition": "IP is the principal communications protocol for relaying datagrams across network boundaries, enabling internetworking.",
        "key_points": [
            "IPv4 uses 32-bit addresses (e.g., 192.168.1.1)",
            "IPv6 uses 128-bit addresses",
            "Connectionless protocol",
            "Handles routing and addressing",
            "Fragmentation and reassembly"
        ],
        "examples": [
            "192.168.1.1 (private IPv4)",
            "8.8.8.8 (Google DNS)"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["ip", "ipv4", "ipv6", "internet protocol", "ip address"]
    },
    "dns": {
        "name": "DNS (Domain Name System)",
        "subject_name": "Computer Networks",
        "subject_code": "CN",
        "definition": "DNS is a hierarchical naming system that translates human-readable domain names to IP addresses.",
        "key_points": [
            "Distributed database system",
            "Hierarchical structure: root, TLD, domain",
            "Caching for performance",
            "Record types: A, AAAA, CNAME, MX, NS",
            "Recursive and iterative queries"
        ],
        "examples": [
            "google.com → 142.250.x.x",
            "Email routing via MX records"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["dns", "domain name", "nameserver", "resolution"]
    },
    
    # Data Structures
    "linked list": {
        "name": "Linked List",
        "subject_name": "Data Structures and Algorithms",
        "subject_code": "DSA",
        "definition": "A linked list is a linear data structure where elements are stored in nodes, and each node points to the next node in the sequence.",
        "key_points": [
            "Dynamic size - no fixed capacity",
            "Non-contiguous memory allocation",
            "Types: Singly, Doubly, Circular",
            "O(1) insertion/deletion at known position",
            "O(n) search time"
        ],
        "examples": [
            "Music playlist (next/previous songs)",
            "Browser history navigation"
        ],
        "difficulty_level": "easy",
        "exam_frequency": "high",
        "keywords": ["linked list", "singly linked", "doubly linked", "circular linked"]
    },
    "binary tree": {
        "name": "Binary Tree",
        "subject_name": "Data Structures and Algorithms",
        "subject_code": "DSA",
        "definition": "A binary tree is a hierarchical data structure in which each node has at most two children, referred to as the left child and the right child.",
        "key_points": [
            "Each node has at most 2 children",
            "Binary Search Tree: left < root < right",
            "Traversals: Inorder, Preorder, Postorder, Level-order",
            "Height and depth concepts",
            "Complete, Full, Perfect binary trees"
        ],
        "examples": [
            "Expression trees in compilers",
            "File system hierarchy",
            "Decision trees"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["binary tree", "bst", "tree traversal", "inorder", "preorder", "postorder"]
    },
    "graph": {
        "name": "Graph",
        "subject_name": "Data Structures and Algorithms",
        "subject_code": "DSA",
        "definition": "A graph is a non-linear data structure consisting of vertices (nodes) connected by edges.",
        "key_points": [
            "Directed vs Undirected graphs",
            "Weighted vs Unweighted edges",
            "Representations: Adjacency Matrix, Adjacency List",
            "BFS and DFS traversals",
            "Algorithms: Dijkstra, Bellman-Ford, Prim, Kruskal"
        ],
        "examples": [
            "Social networks (friendships)",
            "Road maps and navigation",
            "Web page linking"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["graph", "vertex", "edge", "directed", "undirected", "adjacency"]
    },
    "stack": {
        "name": "Stack",
        "subject_name": "Data Structures and Algorithms",
        "subject_code": "DSA",
        "definition": "A stack is a linear data structure that follows the LIFO (Last In, First Out) principle. Elements are added and removed from the same end called the top.",
        "key_points": [
            "LIFO: Last In, First Out",
            "Operations: Push, Pop, Peek/Top",
            "O(1) for push and pop operations",
            "Used in function call management",
            "Can be implemented using arrays or linked lists"
        ],
        "examples": [
            "Browser back button",
            "Undo operation in editors",
            "Function call stack"
        ],
        "difficulty_level": "easy",
        "exam_frequency": "high",
        "keywords": ["stack", "lifo", "push", "pop", "last in first out"]
    },
    "queue": {
        "name": "Queue",
        "subject_name": "Data Structures and Algorithms",
        "subject_code": "DSA",
        "definition": "A queue is a linear data structure that follows the FIFO (First In, First Out) principle. Elements are added at the rear and removed from the front.",
        "key_points": [
            "FIFO: First In, First Out",
            "Operations: Enqueue, Dequeue, Front, Rear",
            "Types: Simple, Circular, Priority, Deque",
            "BFS uses a queue",
            "Can be implemented using arrays or linked lists"
        ],
        "examples": [
            "Print queue",
            "Task scheduling",
            "Customer service line"
        ],
        "difficulty_level": "easy",
        "exam_frequency": "high",
        "keywords": ["queue", "fifo", "enqueue", "dequeue", "first in first out"]
    },
    "hash table": {
        "name": "Hash Table",
        "subject_name": "Data Structures and Algorithms",
        "subject_code": "DSA",
        "definition": "A hash table is a data structure that implements an associative array, using a hash function to compute an index into an array of buckets.",
        "key_points": [
            "O(1) average case for insert, delete, search",
            "Hash function maps keys to indices",
            "Collision handling: Chaining, Open Addressing",
            "Load factor affects performance",
            "Used in dictionaries and sets"
        ],
        "examples": [
            "Dictionary implementation",
            "Database indexing",
            "Caching systems"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["hash table", "hash map", "hashing", "collision", "hash function"]
    },
    "sorting": {
        "name": "Sorting Algorithms",
        "subject_name": "Data Structures and Algorithms",
        "subject_code": "DSA",
        "definition": "Sorting is the process of arranging elements in a specific order (ascending or descending).",
        "key_points": [
            "Bubble Sort: O(n²), simple but slow",
            "Quick Sort: O(n log n) average, in-place",
            "Merge Sort: O(n log n), stable, extra space",
            "Heap Sort: O(n log n), in-place",
            "Comparison-based vs Non-comparison (Counting, Radix)"
        ],
        "examples": [
            "Sorting student records by marks",
            "Arranging files by name or date"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["sorting", "bubble sort", "quick sort", "merge sort", "heap sort"]
    },
    "dynamic programming": {
        "name": "Dynamic Programming",
        "subject_name": "Data Structures and Algorithms",
        "subject_code": "DSA",
        "definition": "Dynamic programming is an algorithmic technique that solves complex problems by breaking them into simpler overlapping subproblems and storing results to avoid redundant computation.",
        "key_points": [
            "Optimal substructure property",
            "Overlapping subproblems",
            "Memoization (top-down approach)",
            "Tabulation (bottom-up approach)",
            "Used for optimization problems"
        ],
        "examples": [
            "Fibonacci sequence",
            "Longest Common Subsequence",
            "0/1 Knapsack problem",
            "Matrix Chain Multiplication"
        ],
        "difficulty_level": "hard",
        "exam_frequency": "high",
        "keywords": ["dynamic programming", "dp", "memoization", "tabulation", "optimal substructure"]
    },
    
    # Machine Learning
    "supervised learning": {
        "name": "Supervised Learning",
        "subject_name": "Machine Learning",
        "subject_code": "ML",
        "definition": "Supervised learning is a machine learning approach where models learn from labeled training data to make predictions on new, unseen data.",
        "key_points": [
            "Uses labeled data (input-output pairs)",
            "Types: Classification, Regression",
            "Algorithms: Linear Regression, Decision Trees, SVM, Neural Networks",
            "Evaluation: Accuracy, Precision, Recall, F1-Score",
            "Requires feature engineering"
        ],
        "examples": [
            "Spam email detection (classification)",
            "House price prediction (regression)",
            "Image classification"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["supervised learning", "classification", "regression", "labeled data"]
    },
    "unsupervised learning": {
        "name": "Unsupervised Learning",
        "subject_name": "Machine Learning",
        "subject_code": "ML",
        "definition": "Unsupervised learning is a machine learning approach where models find patterns and structures in unlabeled data without predefined outputs.",
        "key_points": [
            "No labeled data required",
            "Types: Clustering, Dimensionality Reduction, Association",
            "Algorithms: K-Means, DBSCAN, PCA, Hierarchical Clustering",
            "Finds hidden patterns and structures",
            "Used for exploratory data analysis"
        ],
        "examples": [
            "Customer segmentation",
            "Anomaly detection",
            "Topic modeling in documents"
        ],
        "difficulty_level": "medium",
        "exam_frequency": "high",
        "keywords": ["unsupervised learning", "clustering", "k-means", "pca", "unlabeled"]
    },
    "neural network": {
        "name": "Neural Network",
        "subject_name": "Machine Learning",
        "subject_code": "ML",
        "definition": "A neural network is a computational model inspired by biological neural networks, consisting of interconnected nodes (neurons) that process information.",
        "key_points": [
            "Layers: Input, Hidden, Output",
            "Activation functions: ReLU, Sigmoid, Tanh",
            "Backpropagation for training",
            "Deep learning: multiple hidden layers",
            "Types: CNN, RNN, Transformer"
        ],
        "examples": [
            "Image recognition",
            "Natural language processing",
            "Speech recognition"
        ],
        "difficulty_level": "hard",
        "exam_frequency": "high",
        "keywords": ["neural network", "deep learning", "neurons", "backpropagation", "cnn", "rnn"]
    },
}


async def main():
    """Add topics directly to MongoDB without using Beanie models."""
    print("=" * 70)
    print("📝 ADDING TOPICS TO DATABASE (Direct MongoDB)")
    print("=" * 70)
    
    from app.config import settings
    
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    topics_collection = db["topics"]
    
    added = 0
    skipped = 0
    
    for keyword, topic_data in TOPICS.items():
        # Check if exists
        existing = await topics_collection.find_one({"name": topic_data["name"]})
        
        if existing:
            print(f"  ⏭️ Exists: {topic_data['name']}")
            skipped += 1
            continue
        
        # Create document directly
        doc = {
            "name": topic_data["name"],
            "subject_name": topic_data.get("subject_name"),
            "subject_code": topic_data.get("subject_code"),
            "definition": topic_data.get("definition"),
            "explanation": topic_data.get("explanation", ""),
            "key_points": topic_data.get("key_points", []),
            "examples": topic_data.get("examples", []),
            "keywords": topic_data.get("keywords", [keyword]),
            "difficulty_level": topic_data.get("difficulty_level", "medium"),
            "exam_frequency": topic_data.get("exam_frequency", "medium"),
            "related_topics": [],
            "prerequisites": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        try:
            await topics_collection.insert_one(doc)
            print(f"  ✅ Added: {topic_data['name']}")
            added += 1
        except DuplicateKeyError:
            print(f"  ⏭️ Duplicate: {topic_data['name']}")
            skipped += 1
    
    # Final count
    total = await topics_collection.count_documents({})
    
    print("\n" + "=" * 70)
    print(f"✅ Added: {added} | Skipped: {skipped}")
    print(f"📊 Total topics in database: {total}")
    print("=" * 70)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(main())