# populate_topics.py
"""
Detailed syllabus topics for each subject with unit-wise breakdown
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os


async def populate_topics():
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client["fcrit_chatbot"]
    
    print("🔄 Populating detailed syllabus topics...")
    
    # Clear existing
    await db.syllabus.delete_many({})
    
    syllabus_data = [
        # ==================== DATA STRUCTURES ====================
        {
            "subject_code": "CSPCC303",
            "subject_name": "Data Structures",
            "units": [
                {
                    "unit_number": 1,
                    "unit_name": "Introduction to Data Structures",
                    "hours": 6,
                    "topics": [
                        "Introduction to data structures and algorithms",
                        "Abstract Data Types (ADT)",
                        "Algorithm analysis - Time and Space complexity",
                        "Big O, Big Omega, Big Theta notations",
                        "Best, Average, and Worst case analysis",
                        "Arrays - 1D, 2D, and Multi-dimensional arrays",
                        "Array operations - insertion, deletion, traversal",
                        "Sparse matrices and their representations"
                    ]
                },
                {
                    "unit_number": 2,
                    "unit_name": "Linked Lists",
                    "hours": 8,
                    "topics": [
                        "Introduction to linked lists",
                        "Singly linked list - operations and implementation",
                        "Doubly linked list - operations and implementation",
                        "Circular linked list - singly and doubly",
                        "Header linked list",
                        "Polynomial representation using linked list",
                        "Addition and multiplication of polynomials",
                        "Memory allocation and garbage collection"
                    ]
                },
                {
                    "unit_number": 3,
                    "unit_name": "Stacks and Queues",
                    "hours": 8,
                    "topics": [
                        "Stack ADT - definition and operations",
                        "Array implementation of stack",
                        "Linked list implementation of stack",
                        "Applications - expression evaluation",
                        "Infix to postfix conversion",
                        "Infix to prefix conversion",
                        "Queue ADT - definition and operations",
                        "Circular queue implementation",
                        "Double-ended queue (Deque)",
                        "Priority queue",
                        "Applications of queues"
                    ]
                },
                {
                    "unit_number": 4,
                    "unit_name": "Trees",
                    "hours": 10,
                    "topics": [
                        "Tree terminology and definitions",
                        "Binary tree - properties and types",
                        "Binary tree representations",
                        "Tree traversals - inorder, preorder, postorder",
                        "Level order traversal",
                        "Binary Search Tree (BST)",
                        "BST operations - insert, delete, search",
                        "Threaded binary trees",
                        "AVL trees - rotations and balancing",
                        "B-trees and B+ trees introduction",
                        "Heap - Min heap and Max heap",
                        "Heap operations and heapify"
                    ]
                },
                {
                    "unit_number": 5,
                    "unit_name": "Graphs",
                    "hours": 8,
                    "topics": [
                        "Graph terminology and representations",
                        "Adjacency matrix representation",
                        "Adjacency list representation",
                        "Graph traversals - BFS and DFS",
                        "Connected components",
                        "Spanning trees",
                        "Minimum Spanning Tree - Prim's algorithm",
                        "Minimum Spanning Tree - Kruskal's algorithm",
                        "Shortest path - Dijkstra's algorithm",
                        "Shortest path - Bellman-Ford algorithm",
                        "Topological sorting"
                    ]
                },
                {
                    "unit_number": 6,
                    "unit_name": "Searching and Sorting",
                    "hours": 8,
                    "topics": [
                        "Linear search",
                        "Binary search",
                        "Interpolation search",
                        "Bubble sort",
                        "Selection sort",
                        "Insertion sort",
                        "Merge sort",
                        "Quick sort",
                        "Heap sort",
                        "Radix sort",
                        "Counting sort",
                        "Comparison of sorting algorithms",
                        "Hashing - hash functions",
                        "Collision resolution techniques"
                    ]
                }
            ],
            "textbooks": [
                "Data Structures Using C - Aaron M. Tenenbaum, Yedidyah Langsam, Moshe J. Augenstein",
                "Data Structures and Algorithm Analysis in C - Mark Allen Weiss",
                "Fundamentals of Data Structures in C - Ellis Horowitz, Sartaj Sahni"
            ],
            "reference_books": [
                "Introduction to Algorithms - Thomas H. Cormen (CLRS)",
                "Data Structures and Algorithms Made Easy - Narasimha Karumanchi",
                "Classic Data Structures - D. Samanta"
            ],
            "online_resources": [
                "https://www.geeksforgeeks.org/data-structures/",
                "https://visualgo.net/en",
                "https://www.cs.usfca.edu/~galles/visualization/Algorithms.html"
            ]
        },
        
        # ==================== DATABASE MANAGEMENT SYSTEM ====================
        {
            "subject_code": "CSPCC304",
            "subject_name": "Database Management System",
            "units": [
                {
                    "unit_number": 1,
                    "unit_name": "Introduction to DBMS",
                    "hours": 6,
                    "topics": [
                        "Database system concepts and architecture",
                        "Data models - hierarchical, network, relational",
                        "Database users and administrators",
                        "Three-schema architecture",
                        "Data independence - logical and physical",
                        "Database languages - DDL, DML, DCL",
                        "DBMS architecture - centralized and client-server",
                        "Comparison of file system vs DBMS"
                    ]
                },
                {
                    "unit_number": 2,
                    "unit_name": "Entity-Relationship Model",
                    "hours": 6,
                    "topics": [
                        "Entity types and entity sets",
                        "Attributes - simple, composite, multivalued, derived",
                        "Keys - super key, candidate key, primary key",
                        "Relationships and relationship types",
                        "Cardinality ratios - 1:1, 1:N, M:N",
                        "Participation constraints - total and partial",
                        "Weak entity types",
                        "ER diagram notation",
                        "Extended ER features - specialization, generalization",
                        "Converting ER to relational schema"
                    ]
                },
                {
                    "unit_number": 3,
                    "unit_name": "Relational Model and SQL",
                    "hours": 10,
                    "topics": [
                        "Relational model concepts",
                        "Relational algebra - select, project, join",
                        "Set operations - union, intersection, difference",
                        "SQL - DDL commands (CREATE, ALTER, DROP)",
                        "SQL - DML commands (INSERT, UPDATE, DELETE)",
                        "SQL - SELECT queries",
                        "WHERE clause and conditions",
                        "ORDER BY, GROUP BY, HAVING clauses",
                        "Aggregate functions - COUNT, SUM, AVG, MAX, MIN",
                        "Joins - INNER, LEFT, RIGHT, FULL OUTER",
                        "Subqueries and nested queries",
                        "Views - creation and manipulation",
                        "Indexes and their types"
                    ]
                },
                {
                    "unit_number": 4,
                    "unit_name": "Normalization",
                    "hours": 8,
                    "topics": [
                        "Functional dependencies",
                        "Armstrong's axioms",
                        "Closure of functional dependencies",
                        "Canonical cover",
                        "First Normal Form (1NF)",
                        "Second Normal Form (2NF)",
                        "Third Normal Form (3NF)",
                        "Boyce-Codd Normal Form (BCNF)",
                        "Fourth Normal Form (4NF)",
                        "Fifth Normal Form (5NF)",
                        "Denormalization",
                        "Lossless join decomposition"
                    ]
                },
                {
                    "unit_number": 5,
                    "unit_name": "Transaction Management",
                    "hours": 8,
                    "topics": [
                        "Transaction concepts and states",
                        "ACID properties",
                        "Concurrent execution",
                        "Serializability - conflict and view",
                        "Concurrency control techniques",
                        "Lock-based protocols",
                        "Two-phase locking protocol",
                        "Deadlock handling",
                        "Timestamp-based protocols",
                        "Recovery system concepts",
                        "Log-based recovery",
                        "Checkpointing"
                    ]
                },
                {
                    "unit_number": 6,
                    "unit_name": "Advanced Topics",
                    "hours": 6,
                    "topics": [
                        "Stored procedures",
                        "Triggers",
                        "Cursors",
                        "Introduction to NoSQL databases",
                        "Types of NoSQL - document, key-value, column, graph",
                        "MongoDB basics",
                        "Distributed databases introduction",
                        "Data warehousing concepts"
                    ]
                }
            ],
            "textbooks": [
                "Database System Concepts - Abraham Silberschatz, Henry F. Korth, S. Sudarshan",
                "Fundamentals of Database Systems - Ramez Elmasri, Shamkant B. Navathe"
            ],
            "reference_books": [
                "Database Management Systems - Raghu Ramakrishnan, Johannes Gehrke",
                "An Introduction to Database Systems - C.J. Date",
                "SQL: The Complete Reference - James R. Groff"
            ],
            "online_resources": [
                "https://www.w3schools.com/sql/",
                "https://sqlzoo.net/",
                "https://www.db-fiddle.com/"
            ]
        },
        
        # ==================== OPERATING SYSTEM ====================
        {
            "subject_code": "CSPCC407",
            "subject_name": "Operating System",
            "units": [
                {
                    "unit_number": 1,
                    "unit_name": "Introduction to Operating Systems",
                    "hours": 6,
                    "topics": [
                        "Operating system definition and functions",
                        "Evolution of operating systems",
                        "Types of OS - batch, multiprogramming, time-sharing",
                        "Real-time operating systems",
                        "Distributed operating systems",
                        "OS structure - monolithic, layered, microkernel",
                        "System calls and their types",
                        "OS services and system programs"
                    ]
                },
                {
                    "unit_number": 2,
                    "unit_name": "Process Management",
                    "hours": 10,
                    "topics": [
                        "Process concepts and states",
                        "Process Control Block (PCB)",
                        "Process scheduling - long, short, medium term",
                        "Context switching",
                        "Operations on processes",
                        "Interprocess communication (IPC)",
                        "Shared memory systems",
                        "Message passing systems",
                        "Threads - concept and types",
                        "Multithreading models",
                        "Thread libraries - Pthreads, Java threads"
                    ]
                },
                {
                    "unit_number": 3,
                    "unit_name": "CPU Scheduling",
                    "hours": 8,
                    "topics": [
                        "Scheduling criteria",
                        "First-Come-First-Served (FCFS) scheduling",
                        "Shortest Job First (SJF) scheduling",
                        "Priority scheduling",
                        "Round Robin scheduling",
                        "Multilevel queue scheduling",
                        "Multilevel feedback queue scheduling",
                        "Real-time scheduling algorithms",
                        "Algorithm evaluation methods"
                    ]
                },
                {
                    "unit_number": 4,
                    "unit_name": "Process Synchronization and Deadlocks",
                    "hours": 10,
                    "topics": [
                        "Critical section problem",
                        "Peterson's solution",
                        "Synchronization hardware",
                        "Semaphores - counting and binary",
                        "Classic synchronization problems",
                        "Producer-consumer problem",
                        "Readers-writers problem",
                        "Dining philosophers problem",
                        "Monitors",
                        "Deadlock characterization",
                        "Deadlock prevention",
                        "Deadlock avoidance - Banker's algorithm",
                        "Deadlock detection and recovery"
                    ]
                },
                {
                    "unit_number": 5,
                    "unit_name": "Memory Management",
                    "hours": 10,
                    "topics": [
                        "Memory management concepts",
                        "Contiguous memory allocation",
                        "Fixed and variable partitioning",
                        "Fragmentation - internal and external",
                        "Paging - concept and implementation",
                        "Page table structure",
                        "Segmentation",
                        "Virtual memory concepts",
                        "Demand paging",
                        "Page replacement algorithms - FIFO, LRU, Optimal",
                        "Thrashing",
                        "Working set model"
                    ]
                },
                {
                    "unit_number": 6,
                    "unit_name": "File Systems and I/O",
                    "hours": 6,
                    "topics": [
                        "File concepts and attributes",
                        "File operations",
                        "Directory structure",
                        "File system mounting",
                        "File allocation methods - contiguous, linked, indexed",
                        "Free space management",
                        "I/O hardware",
                        "I/O software layers",
                        "Disk scheduling algorithms - FCFS, SSTF, SCAN, C-SCAN"
                    ]
                }
            ],
            "textbooks": [
                "Operating System Concepts - Abraham Silberschatz, Peter B. Galvin, Greg Gagne",
                "Modern Operating Systems - Andrew S. Tanenbaum"
            ],
            "reference_books": [
                "Operating Systems: Internals and Design Principles - William Stallings",
                "Operating Systems: A Design-Oriented Approach - Charles Crowley",
                "Understanding the Linux Kernel - Daniel P. Bovet, Marco Cesati"
            ],
            "online_resources": [
                "https://www.geeksforgeeks.org/operating-systems/",
                "https://pages.cs.wisc.edu/~remzi/OSTEP/",
                "https://www.os-book.com/"
            ]
        },
        
        # ==================== DESIGN & ANALYSIS OF ALGORITHM ====================
        {
            "subject_code": "CSPCC406",
            "subject_name": "Design & Analysis of Algorithm",
            "units": [
                {
                    "unit_number": 1,
                    "unit_name": "Introduction and Analysis",
                    "hours": 6,
                    "topics": [
                        "Algorithm definition and characteristics",
                        "Algorithm design techniques overview",
                        "Asymptotic notations - O, Ω, Θ",
                        "Time complexity analysis",
                        "Space complexity analysis",
                        "Recurrence relations",
                        "Solving recurrences - substitution method",
                        "Master theorem",
                        "Amortized analysis introduction"
                    ]
                },
                {
                    "unit_number": 2,
                    "unit_name": "Divide and Conquer",
                    "hours": 8,
                    "topics": [
                        "Divide and conquer strategy",
                        "Binary search",
                        "Merge sort - analysis and implementation",
                        "Quick sort - analysis and implementation",
                        "Randomized quick sort",
                        "Finding maximum and minimum",
                        "Strassen's matrix multiplication",
                        "Closest pair of points",
                        "Integer multiplication - Karatsuba algorithm"
                    ]
                },
                {
                    "unit_number": 3,
                    "unit_name": "Greedy Algorithms",
                    "hours": 8,
                    "topics": [
                        "Greedy approach characteristics",
                        "Activity selection problem",
                        "Fractional knapsack problem",
                        "Job sequencing with deadlines",
                        "Huffman coding",
                        "Minimum spanning tree - Prim's algorithm",
                        "Minimum spanning tree - Kruskal's algorithm",
                        "Single source shortest path - Dijkstra's algorithm",
                        "Greedy vs Dynamic Programming"
                    ]
                },
                {
                    "unit_number": 4,
                    "unit_name": "Dynamic Programming",
                    "hours": 10,
                    "topics": [
                        "Dynamic programming principles",
                        "Overlapping subproblems",
                        "Optimal substructure",
                        "Memoization vs tabulation",
                        "Fibonacci numbers",
                        "Longest common subsequence (LCS)",
                        "0/1 Knapsack problem",
                        "Matrix chain multiplication",
                        "All pairs shortest path - Floyd-Warshall",
                        "Bellman-Ford algorithm",
                        "Coin change problem",
                        "Edit distance",
                        "Longest increasing subsequence"
                    ]
                },
                {
                    "unit_number": 5,
                    "unit_name": "Backtracking and Branch & Bound",
                    "hours": 8,
                    "topics": [
                        "Backtracking strategy",
                        "N-Queens problem",
                        "Sum of subsets problem",
                        "Graph coloring",
                        "Hamiltonian cycle",
                        "Branch and bound technique",
                        "0/1 Knapsack using branch and bound",
                        "Traveling salesman problem",
                        "Assignment problem"
                    ]
                },
                {
                    "unit_number": 6,
                    "unit_name": "Complexity Theory",
                    "hours": 6,
                    "topics": [
                        "P and NP classes",
                        "Polynomial time reductions",
                        "NP-completeness",
                        "Cook's theorem",
                        "NP-complete problems - SAT, Clique, Vertex Cover",
                        "NP-hard problems",
                        "Approximation algorithms introduction",
                        "Randomized algorithms introduction"
                    ]
                }
            ],
            "textbooks": [
                "Introduction to Algorithms - Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein (CLRS)",
                "Fundamentals of Computer Algorithms - Ellis Horowitz, Sartaj Sahni, Sanguthevar Rajasekaran"
            ],
            "reference_books": [
                "Algorithm Design - Jon Kleinberg, Eva Tardos",
                "The Algorithm Design Manual - Steven S. Skiena",
                "Algorithms - Robert Sedgewick, Kevin Wayne"
            ],
            "online_resources": [
                "https://www.geeksforgeeks.org/fundamentals-of-algorithms/",
                "https://cp-algorithms.com/",
                "https://visualgo.net/en"
            ]
        },
        
        # ==================== COMPUTER NETWORK ====================
        {
            "subject_code": "CSPCC510",
            "subject_name": "Computer Network",
            "units": [
                {
                    "unit_number": 1,
                    "unit_name": "Introduction to Computer Networks",
                    "hours": 6,
                    "topics": [
                        "Data communication fundamentals",
                        "Network definition and components",
                        "Network topologies - bus, star, ring, mesh",
                        "Types of networks - LAN, MAN, WAN",
                        "OSI reference model - 7 layers",
                        "TCP/IP protocol suite",
                        "Comparison of OSI and TCP/IP",
                        "Network devices - hub, switch, router, gateway"
                    ]
                },
                {
                    "unit_number": 2,
                    "unit_name": "Physical Layer",
                    "hours": 6,
                    "topics": [
                        "Transmission media - guided and unguided",
                        "Twisted pair, coaxial cable, fiber optic",
                        "Wireless transmission",
                        "Signal encoding techniques",
                        "Digital modulation - ASK, FSK, PSK",
                        "Multiplexing - FDM, TDM, WDM",
                        "Switching techniques - circuit, packet, message",
                        "Transmission impairments"
                    ]
                },
                {
                    "unit_number": 3,
                    "unit_name": "Data Link Layer",
                    "hours": 8,
                    "topics": [
                        "Data link layer functions",
                        "Framing techniques",
                        "Error detection - parity, CRC, checksum",
                        "Error correction - Hamming code",
                        "Flow control mechanisms",
                        "Stop-and-wait protocol",
                        "Sliding window protocol - Go-Back-N, Selective Repeat",
                        "HDLC protocol",
                        "Point-to-Point Protocol (PPP)",
                        "Multiple access protocols - ALOHA, CSMA/CD, CSMA/CA",
                        "Ethernet - IEEE 802.3",
                        "Wireless LAN - IEEE 802.11"
                    ]
                },
                {
                    "unit_number": 4,
                    "unit_name": "Network Layer",
                    "hours": 10,
                    "topics": [
                        "Network layer functions",
                        "IPv4 addressing and subnetting",
                        "Classful and classless addressing",
                        "CIDR notation",
                        "Subnetting and supernetting",
                        "IPv4 packet format",
                        "IPv6 addressing and features",
                        "Routing algorithms - distance vector, link state",
                        "RIP protocol",
                        "OSPF protocol",
                        "BGP protocol",
                        "ICMP protocol",
                        "ARP and RARP",
                        "NAT and PAT"
                    ]
                },
                {
                    "unit_number": 5,
                    "unit_name": "Transport Layer",
                    "hours": 8,
                    "topics": [
                        "Transport layer services",
                        "Port numbers and sockets",
                        "UDP - User Datagram Protocol",
                        "TCP - Transmission Control Protocol",
                        "TCP segment format",
                        "TCP connection management",
                        "Three-way handshake",
                        "TCP flow control - sliding window",
                        "TCP congestion control",
                        "Slow start and congestion avoidance",
                        "Quality of Service (QoS)"
                    ]
                },
                {
                    "unit_number": 6,
                    "unit_name": "Application Layer",
                    "hours": 8,
                    "topics": [
                        "DNS - Domain Name System",
                        "HTTP and HTTPS protocols",
                        "FTP - File Transfer Protocol",
                        "SMTP - Simple Mail Transfer Protocol",
                        "POP3 and IMAP",
                        "DHCP - Dynamic Host Configuration Protocol",
                        "SNMP - Simple Network Management Protocol",
                        "Telnet and SSH",
                        "Web and HTTP",
                        "Email protocols",
                        "Introduction to network security"
                    ]
                }
            ],
            "textbooks": [
                "Computer Networks - Andrew S. Tanenbaum, David J. Wetherall",
                "Data Communications and Networking - Behrouz A. Forouzan"
            ],
            "reference_books": [
                "Computer Networking: A Top-Down Approach - James F. Kurose, Keith W. Ross",
                "TCP/IP Protocol Suite - Behrouz A. Forouzan",
                "Internetworking with TCP/IP - Douglas E. Comer"
            ],
            "online_resources": [
                "https://www.geeksforgeeks.org/computer-network-tutorials/",
                "https://www.cloudflare.com/learning/",
                "https://www.cisco.com/c/en/us/training-events.html"
            ]
        },
        
        # ==================== ARTIFICIAL INTELLIGENCE ====================
        {
            "subject_code": "CSPCC712",
            "subject_name": "Artificial Intelligence",
            "units": [
                {
                    "unit_number": 1,
                    "unit_name": "Introduction to AI",
                    "hours": 6,
                    "topics": [
                        "History and foundations of AI",
                        "Definition and scope of AI",
                        "AI applications",
                        "Intelligent agents",
                        "Types of agents - simple reflex, model-based, goal-based, utility-based",
                        "Environment types - deterministic, stochastic, episodic, sequential",
                        "PEAS description",
                        "Turing test"
                    ]
                },
                {
                    "unit_number": 2,
                    "unit_name": "Problem Solving and Search",
                    "hours": 10,
                    "topics": [
                        "Problem formulation",
                        "State space representation",
                        "Uninformed search strategies",
                        "Breadth-First Search (BFS)",
                        "Depth-First Search (DFS)",
                        "Depth-Limited Search",
                        "Iterative Deepening Search",
                        "Uniform Cost Search",
                        "Informed (Heuristic) search",
                        "Best-First Search",
                        "A* algorithm",
                        "Heuristic functions",
                        "Admissibility and consistency",
                        "Hill climbing",
                        "Simulated annealing"
                    ]
                },
                {
                    "unit_number": 3,
                    "unit_name": "Game Playing",
                    "hours": 6,
                    "topics": [
                        "Adversarial search",
                        "Game tree representation",
                        "Minimax algorithm",
                        "Alpha-beta pruning",
                        "Evaluation functions",
                        "Games with chance",
                        "Expectiminimax",
                        "Monte Carlo Tree Search introduction"
                    ]
                },
                {
                    "unit_number": 4,
                    "unit_name": "Knowledge Representation and Reasoning",
                    "hours": 10,
                    "topics": [
                        "Knowledge representation techniques",
                        "Propositional logic",
                        "First-order predicate logic",
                        "Inference rules",
                        "Forward and backward chaining",
                        "Resolution",
                        "Unification",
                        "Semantic networks",
                        "Frames",
                        "Production systems",
                        "Ontologies",
                        "Reasoning under uncertainty",
                        "Bayesian networks introduction"
                    ]
                },
                {
                    "unit_number": 5,
                    "unit_name": "Planning",
                    "hours": 6,
                    "topics": [
                        "Planning problem definition",
                        "STRIPS representation",
                        "Forward state-space planning",
                        "Backward state-space planning",
                        "Partial-order planning",
                        "Planning graphs",
                        "GRAPHPLAN algorithm",
                        "Hierarchical planning"
                    ]
                },
                {
                    "unit_number": 6,
                    "unit_name": "Machine Learning for AI",
                    "hours": 8,
                    "topics": [
                        "Learning agent architecture",
                        "Types of learning - supervised, unsupervised, reinforcement",
                        "Decision tree learning",
                        "Neural networks basics",
                        "Perceptron and multilayer networks",
                        "Backpropagation",
                        "Introduction to deep learning",
                        "Natural language processing basics",
                        "Computer vision basics",
                        "Expert systems"
                    ]
                }
            ],
            "textbooks": [
                "Artificial Intelligence: A Modern Approach - Stuart Russell, Peter Norvig",
                "Artificial Intelligence - Elaine Rich, Kevin Knight"
            ],
            "reference_books": [
                "Introduction to Artificial Intelligence - Wolfgang Ertel",
                "Artificial Intelligence: Structures and Strategies - George F. Luger",
                "Principles of Artificial Intelligence - Nils J. Nilsson"
            ],
            "online_resources": [
                "https://www.geeksforgeeks.org/artificial-intelligence/",
                "https://ai.berkeley.edu/course_schedule.html",
                "https://www.coursera.org/learn/ai-for-everyone"
            ]
        },
        
        # ==================== MACHINE LEARNING ====================
        {
            "subject_code": "CSPEC6021",
            "subject_name": "Machine Learning",
            "units": [
                {
                    "unit_number": 1,
                    "unit_name": "Introduction to Machine Learning",
                    "hours": 6,
                    "topics": [
                        "What is machine learning",
                        "Types of machine learning",
                        "Supervised learning overview",
                        "Unsupervised learning overview",
                        "Reinforcement learning overview",
                        "Machine learning workflow",
                        "Feature engineering basics",
                        "Training and test sets",
                        "Overfitting and underfitting",
                        "Bias-variance tradeoff"
                    ]
                },
                {
                    "unit_number": 2,
                    "unit_name": "Supervised Learning - Regression",
                    "hours": 8,
                    "topics": [
                        "Linear regression",
                        "Cost function and gradient descent",
                        "Multiple linear regression",
                        "Polynomial regression",
                        "Regularization - L1 (Lasso) and L2 (Ridge)",
                        "Elastic Net",
                        "Evaluation metrics - MSE, RMSE, MAE, R²",
                        "Cross-validation techniques"
                    ]
                },
                {
                    "unit_number": 3,
                    "unit_name": "Supervised Learning - Classification",
                    "hours": 10,
                    "topics": [
                        "Logistic regression",
                        "Sigmoid function",
                        "Decision boundaries",
                        "K-Nearest Neighbors (KNN)",
                        "Naive Bayes classifier",
                        "Decision trees",
                        "Information gain and entropy",
                        "Random forests",
                        "Support Vector Machines (SVM)",
                        "Kernel methods",
                        "Evaluation metrics - accuracy, precision, recall, F1",
                        "ROC curve and AUC",
                        "Confusion matrix"
                    ]
                },
                {
                    "unit_number": 4,
                    "unit_name": "Unsupervised Learning",
                    "hours": 8,
                    "topics": [
                        "Clustering algorithms",
                        "K-Means clustering",
                        "Hierarchical clustering",
                        "DBSCAN",
                        "Cluster evaluation metrics",
                        "Dimensionality reduction",
                        "Principal Component Analysis (PCA)",
                        "t-SNE",
                        "Association rule mining",
                        "Apriori algorithm"
                    ]
                },
                {
                    "unit_number": 5,
                    "unit_name": "Neural Networks",
                    "hours": 8,
                    "topics": [
                        "Perceptron model",
                        "Multi-layer perceptron (MLP)",
                        "Activation functions - sigmoid, tanh, ReLU",
                        "Backpropagation algorithm",
                        "Gradient descent variants",
                        "Batch, mini-batch, stochastic GD",
                        "Optimizers - Adam, RMSprop",
                        "Regularization in neural networks",
                        "Dropout",
                        "Batch normalization"
                    ]
                },
                {
                    "unit_number": 6,
                    "unit_name": "Ensemble Methods and Advanced Topics",
                    "hours": 6,
                    "topics": [
                        "Ensemble learning concepts",
                        "Bagging",
                        "Boosting - AdaBoost, Gradient Boosting",
                        "XGBoost",
                        "Model selection and hyperparameter tuning",
                        "Grid search and random search",
                        "Introduction to deep learning",
                        "CNN and RNN overview",
                        "Transfer learning basics"
                    ]
                }
            ],
            "textbooks": [
                "Pattern Recognition and Machine Learning - Christopher M. Bishop",
                "Machine Learning - Tom M. Mitchell"
            ],
            "reference_books": [
                "Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow - Aurélien Géron",
                "The Elements of Statistical Learning - Trevor Hastie, Robert Tibshirani, Jerome Friedman",
                "Deep Learning - Ian Goodfellow, Yoshua Bengio, Aaron Courville"
            ],
            "online_resources": [
                "https://scikit-learn.org/stable/tutorial/",
                "https://www.coursera.org/specializations/machine-learning-introduction",
                "https://www.kaggle.com/learn"
            ]
        },
        
        # ==================== CRYPTOGRAPHY & NETWORK SECURITY ====================
        {
            "subject_code": "CSPCC611",
            "subject_name": "Cryptography & Network Security",
            "units": [
                {
                    "unit_number": 1,
                    "unit_name": "Introduction to Security",
                    "hours": 6,
                    "topics": [
                        "Security goals - CIA triad",
                        "Types of attacks - passive and active",
                        "Security services and mechanisms",
                        "Classical encryption techniques",
                        "Substitution ciphers - Caesar, monoalphabetic, polyalphabetic",
                        "Transposition ciphers",
                        "Cryptanalysis basics",
                        "One-time pad"
                    ]
                },
                {
                    "unit_number": 2,
                    "unit_name": "Symmetric Key Cryptography",
                    "hours": 10,
                    "topics": [
                        "Block ciphers vs stream ciphers",
                        "Feistel cipher structure",
                        "Data Encryption Standard (DES)",
                        "DES algorithm details",
                        "Triple DES (3DES)",
                        "Advanced Encryption Standard (AES)",
                        "AES algorithm details",
                        "Modes of operation - ECB, CBC, CFB, OFB, CTR",
                        "RC4 stream cipher",
                        "Key distribution problem"
                    ]
                },
                {
                    "unit_number": 3,
                    "unit_name": "Public Key Cryptography",
                    "hours": 10,
                    "topics": [
                        "Principles of public key cryptography",
                        "RSA algorithm",
                        "RSA key generation",
                        "RSA encryption and decryption",
                        "Diffie-Hellman key exchange",
                        "ElGamal encryption",
                        "Elliptic Curve Cryptography (ECC)",
                        "Comparison of symmetric and asymmetric",
                        "Hybrid cryptosystems"
                    ]
                },
                {
                    "unit_number": 4,
                    "unit_name": "Hash Functions and Digital Signatures",
                    "hours": 8,
                    "topics": [
                        "Cryptographic hash functions",
                        "Properties of hash functions",
                        "MD5 algorithm",
                        "SHA family - SHA-1, SHA-256, SHA-3",
                        "Message Authentication Code (MAC)",
                        "HMAC",
                        "Digital signatures",
                        "RSA signature scheme",
                        "Digital Signature Algorithm (DSA)",
                        "Certificates and PKI"
                    ]
                },
                {
                    "unit_number": 5,
                    "unit_name": "Network Security Protocols",
                    "hours": 8,
                    "topics": [
                        "Key management",
                        "Kerberos authentication",
                        "X.509 certificates",
                        "Public Key Infrastructure (PKI)",
                        "SSL/TLS protocol",
                        "TLS handshake",
                        "IPSec protocol suite",
                        "AH and ESP protocols",
                        "VPN technologies"
                    ]
                },
                {
                    "unit_number": 6,
                    "unit_name": "System Security",
                    "hours": 6,
                    "topics": [
                        "Firewalls - types and architectures",
                        "Intrusion Detection Systems (IDS)",
                        "Intrusion Prevention Systems (IPS)",
                        "Email security - PGP, S/MIME",
                        "Web security",
                        "SQL injection",
                        "Cross-site scripting (XSS)",
                        "Malware types and protection"
                    ]
                }
            ],
            "textbooks": [
                "Cryptography and Network Security: Principles and Practice - William Stallings",
                "Network Security Essentials - William Stallings"
            ],
            "reference_books": [
                "Applied Cryptography - Bruce Schneier",
                "Understanding Cryptography - Christof Paar, Jan Pelzl",
                "Cryptography and Network Security - Atul Kahate"
            ],
            "online_resources": [
                "https://www.coursera.org/learn/crypto",
                "https://cryptopals.com/",
                "https://www.owasp.org/"
            ]
        },
        
        # ==================== SOFTWARE ENGINEERING ====================
        {
            "subject_code": "CSPCC408",
            "subject_name": "Software Engineering",
            "units": [
                {
                    "unit_number": 1,
                    "unit_name": "Introduction to Software Engineering",
                    "hours": 6,
                    "topics": [
                        "Software definition and characteristics",
                        "Software crisis",
                        "Software engineering principles",
                        "Software process and process models",
                        "Waterfall model",
                        "Iterative models",
                        "Incremental model",
                        "RAD model",
                        "Agile methodologies overview"
                    ]
                },
                {
                    "unit_number": 2,
                    "unit_name": "Requirements Engineering",
                    "hours": 8,
                    "topics": [
                        "Requirements engineering process",
                        "Types of requirements - functional, non-functional",
                        "Requirements elicitation techniques",
                        "Requirements analysis",
                        "Requirements specification - SRS document",
                        "IEEE SRS standard",
                        "Requirements validation",
                        "Requirements management",
                        "Use case modeling",
                        "Use case diagrams"
                    ]
                },
                {
                    "unit_number": 3,
                    "unit_name": "Software Design",
                    "hours": 10,
                    "topics": [
                        "Design concepts and principles",
                        "Modularity and coupling",
                        "Cohesion types",
                        "Architectural design",
                        "Architectural styles - layered, client-server, MVC",
                        "Component-level design",
                        "Object-oriented design",
                        "Design patterns overview",
                        "Creational patterns - Singleton, Factory",
                        "Structural patterns - Adapter, Facade",
                        "Behavioral patterns - Observer, Strategy",
                        "UML diagrams - class, sequence, state"
                    ]
                },
                {
                    "unit_number": 4,
                    "unit_name": "Software Testing",
                    "hours": 8,
                    "topics": [
                        "Software testing fundamentals",
                        "Testing levels - unit, integration, system, acceptance",
                        "White box testing techniques",
                        "Statement coverage",
                        "Branch coverage",
                        "Path coverage",
                        "Black box testing techniques",
                        "Equivalence partitioning",
                        "Boundary value analysis",
                        "Test case design",
                        "Regression testing",
                        "Automated testing introduction"
                    ]
                },
                {
                    "unit_number": 5,
                    "unit_name": "Software Quality and Metrics",
                    "hours": 6,
                    "topics": [
                        "Software quality attributes",
                        "Quality assurance vs quality control",
                        "Software reviews - inspection, walkthrough",
                        "Software metrics",
                        "Size metrics - LOC, function points",
                        "Complexity metrics - cyclomatic complexity",
                        "Quality metrics",
                        "Software reliability",
                        "ISO 9001 and CMMI overview"
                    ]
                },
                {
                    "unit_number": 6,
                    "unit_name": "Project Management and Agile",
                    "hours": 8,
                    "topics": [
                        "Software project management",
                        "Project planning and estimation",
                        "COCOMO model",
                        "Function point analysis",
                        "Risk management",
                        "Configuration management",
                        "Version control systems",
                        "Agile principles and values",
                        "Scrum framework",
                        "Sprint planning and retrospectives",
                        "Kanban",
                        "Extreme Programming (XP)",
                        "DevOps introduction"
                    ]
                }
            ],
            "textbooks": [
                "Software Engineering: A Practitioner's Approach - Roger S. Pressman",
                "Software Engineering - Ian Sommerville"
            ],
            "reference_books": [
                "Software Engineering: Principles and Practice - Hans Van Vliet",
                "Agile Software Development - Robert C. Martin",
                "Clean Code - Robert C. Martin"
            ],
            "online_resources": [
                "https://www.geeksforgeeks.org/software-engineering/",
                "https://www.scrum.org/resources",
                "https://www.agilealliance.org/agile101/"
            ]
        },
    ]
    
    # Insert all syllabus data
    result = await db.syllabus.insert_many(syllabus_data)
    print(f"✅ Inserted detailed syllabus for {len(result.inserted_ids)} subjects")
    
    # Print summary
    print("\n📊 Syllabus Coverage:")
    for syllabus in syllabus_data:
        total_topics = sum(len(unit["topics"]) for unit in syllabus["units"])
        print(f"   • {syllabus['subject_name']}: {len(syllabus['units'])} units, {total_topics} topics")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(populate_topics())