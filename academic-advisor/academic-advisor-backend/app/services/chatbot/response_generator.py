# app/services/chatbot/response_generator.py
"""
Response generator with safe enum handling and built-in concept definitions
"""

import re
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# SAFE ENUM VALUE HELPER
# ══════════════════════════════════════════════════════════

def safe_enum_value(enum_or_string, default: str = "") -> str:
    """Safely get .value from an enum or return string as-is."""
    if enum_or_string is None:
        return default
    if isinstance(enum_or_string, str):
        return enum_or_string
    if hasattr(enum_or_string, 'value'):
        return enum_or_string.value
    if hasattr(enum_or_string, 'name'):
        return enum_or_string.name
    return str(enum_or_string)


# ══════════════════════════════════════════════════════════
# IMPORTS
# ══════════════════════════════════════════════════════════
# At the top of response_generator.py, update the import:

try:
    from app.database.repositories.subject_repository import SubjectRepository
    _SUBJECT_REPO_AVAILABLE = True
    logger.info("✅ SubjectRepository imported")
except ImportError as e:
    SubjectRepository = None
    _SUBJECT_REPO_AVAILABLE = False
    logger.warning(f"⚠️ SubjectRepository not available: {e}")
    
# Import from shared models
try:
    from app.models.chatbot import IntentType, ResponseType, ConfidenceLevel
    MODELS_AVAILABLE = True
    logger.info("✅ Chatbot models imported successfully")
except ImportError as e:
    MODELS_AVAILABLE = False
    logger.warning(f"⚠️ Chatbot models not available: {e}")
    
    from enum import Enum
    class IntentType(str, Enum):
        SYLLABUS_QUERY = "SYLLABUS_QUERY"
        FACULTY_QUERY = "FACULTY_QUERY"
        PERFORMANCE_QUERY = "PERFORMANCE_QUERY"
        ELECTIVE_QUERY = "ELECTIVE_QUERY"
        CAREER_QUERY = "CAREER_QUERY"
        STUDY_PLAN_QUERY = "STUDY_PLAN_QUERY"
        CLARIFICATION = "CLARIFICATION"
        OUT_OF_SCOPE = "OUT_OF_SCOPE"
        GENERAL = "GENERAL"
    
    class ResponseType(str, Enum):
        TEXT = "text"
        CONCEPT_EXPLANATION = "concept_explanation"
        SYLLABUS_BREAKDOWN = "syllabus_breakdown"
        FACULTY_LIST = "faculty_list"
        FACULTY_RECOMMENDATION = "faculty_recommendation"
        PERFORMANCE_ANALYSIS = "performance_analysis"
        ELECTIVE_RECOMMENDATION = "elective_recommendation"
        CAREER_GUIDANCE = "career_guidance"
        CAREER_LIST = "career_list"
        STUDY_PLAN = "study_plan"
        ERROR = "error"

# Repository imports
FacultyRepository = None
SubjectRepository = None
CareerRepository = None

try:
    from app.repositories.faculty_repository import FacultyRepository
    logger.info("✅ FacultyRepository imported")
except ImportError:
    logger.warning("⚠️ FacultyRepository not available")

try:
    from app.database.repositories.subject_repository import SubjectRepository
    logger.info("✅ SubjectRepository imported")
except ImportError:
    logger.warning("⚠️ SubjectRepository not available")

try:
    from app.repositories.career_repository import CareerRepository
    logger.info("✅ CareerRepository imported")
except ImportError:
    logger.warning("⚠️ CareerRepository not available")


# ══════════════════════════════════════════════════════════
# SUBJECT & CAREER ALIASES
# ══════════════════════════════════════════════════════════

_SUBJECT_ALIASES = {
    "os": "Operating Systems",
    "operating system": "Operating Systems",
    "operating systems": "Operating Systems",
    "dbms": "Database Management Systems",
    "database": "Database Management Systems",
    "dsa": "Data Structures and Algorithms",
    "data structure": "Data Structures and Algorithms",
    "data structures": "Data Structures and Algorithms",
    "cn": "Computer Networks",
    "computer network": "Computer Networks",
    "ml": "Machine Learning",
    "ai": "Artificial Intelligence",
    "oop": "Object Oriented Programming",
    "oops": "Object Oriented Programming",
}

_CAREER_ALIASES = {
    "data scientist": "Data Scientist",
    "data science": "Data Scientist",
    "ml engineer": "ML Engineer",
    "machine learning": "ML Engineer",
    "software developer": "Software Developer",
    "software engineer": "Software Developer",
    "sde": "Software Developer",
    "devops": "DevOps Engineer",
    "cloud": "Cloud Architect",
    "cybersecurity": "Cybersecurity Analyst",
    "web developer": "Full Stack Developer",
    "full stack": "Full Stack Developer",
}


def _normalize_subject(query: str) -> str:
    """Normalize subject name using aliases."""
    ql = query.lower().strip()
    return _SUBJECT_ALIASES.get(ql, query)


def _extract_career_name(query: str) -> Optional[str]:
    """Extract career name from query."""
    ql = query.lower()
    for alias, name in sorted(_CAREER_ALIASES.items(), key=lambda x: -len(x[0])):
        if alias in ql:
            return name
    return None


# ══════════════════════════════════════════════════════════
# BUILT-IN CONCEPT DEFINITIONS
# ══════════════════════════════════════════════════════════

CONCEPT_DEFINITIONS = {
    "deadlock": {
        "topic": "Deadlock",
        "subject": "Operating Systems",
        "definition": "A deadlock is a situation in computing where two or more processes are unable to proceed because each is waiting for the other to release a resource. It occurs when processes hold resources while waiting for others, creating a circular dependency.",
        "explanation": "Deadlock occurs when four conditions are met simultaneously:\n\n1. **Mutual Exclusion**: Resources cannot be shared\n2. **Hold and Wait**: Processes hold resources while waiting for others\n3. **No Preemption**: Resources cannot be forcibly taken\n4. **Circular Wait**: Circular chain of processes waiting for each other",
        "key_points": [
            "Four necessary conditions: Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait",
            "Prevention strategies involve breaking at least one condition",
            "Detection uses resource allocation graphs",
            "Recovery through process termination or resource preemption",
            "Banker's Algorithm is used for deadlock avoidance"
        ],
        "examples": [
            "Two trains approaching each other on a single track",
            "Dining Philosophers Problem",
            "Two processes each holding a resource the other needs"
        ],
        "exam_frequency": "high",
        "exam_weightage": "8-10 marks"
    },
    "normalization": {
        "topic": "Normalization",
        "subject": "Database Management Systems",
        "definition": "Normalization is the process of organizing data in a database to reduce redundancy and improve data integrity by dividing tables and defining relationships between them.",
        "explanation": "Normalization involves organizing columns and tables to minimize data redundancy.\n\n**Normal Forms:**\n- **1NF**: Atomic values, no repeating groups\n- **2NF**: 1NF + No partial dependencies\n- **3NF**: 2NF + No transitive dependencies\n- **BCNF**: Every determinant is a candidate key",
        "key_points": [
            "1NF: Eliminate repeating groups, ensure atomic values",
            "2NF: Remove partial dependencies on composite keys",
            "3NF: Remove transitive dependencies",
            "BCNF: Stricter version of 3NF",
            "Denormalization may be used for performance optimization"
        ],
        "examples": [
            "Converting a flat student-course table into separate Student and Course tables",
            "Removing redundant address information by creating an Address table"
        ],
        "exam_frequency": "high",
        "exam_weightage": "10-12 marks"
    },
    "mutex": {
        "topic": "Mutex (Mutual Exclusion)",
        "subject": "Operating Systems",
        "definition": "A mutex is a synchronization primitive that grants exclusive access to a shared resource to only one thread at a time, preventing race conditions in concurrent programming.",
        "explanation": "Mutex ensures that only one thread can execute a critical section at any given time. When a thread acquires a mutex, other threads must wait until the mutex is released.",
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
        "exam_frequency": "medium",
        "exam_weightage": "5-6 marks"
    },
    "semaphore": {
        "topic": "Semaphore",
        "subject": "Operating Systems",
        "definition": "A semaphore is a synchronization primitive that controls access to a common resource by multiple processes using a counter variable.",
        "explanation": "Unlike mutex which is binary, semaphores can have a count greater than 1, allowing multiple threads to access a resource up to a limit.\n\n**Operations:**\n- **Wait (P/Down)**: Decrement counter, block if negative\n- **Signal (V/Up)**: Increment counter, wake waiting process",
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
        "exam_frequency": "high",
        "exam_weightage": "8-10 marks"
    },
    "process": {
        "topic": "Process",
        "subject": "Operating Systems",
        "definition": "A process is an instance of a program in execution. It includes the program code, current activity, and resources allocated to it.",
        "explanation": "A process is more than just program code. It includes:\n- Program counter\n- CPU registers\n- Stack\n- Data section\n- Heap",
        "key_points": [
            "Process states: New, Ready, Running, Waiting, Terminated",
            "PCB (Process Control Block) stores process information",
            "Processes have independent memory spaces",
            "Inter-process communication (IPC) needed for communication",
            "Context switching required when CPU switches between processes"
        ],
        "examples": [
            "Running a web browser creates a process",
            "Each tab in Chrome is a separate process"
        ],
        "exam_frequency": "high",
        "exam_weightage": "6-8 marks"
    },
    "thread": {
        "topic": "Thread",
        "subject": "Operating Systems",
        "definition": "A thread is the smallest unit of execution within a process. Multiple threads can exist within the same process and share resources.",
        "explanation": "Threads are lightweight processes that share the same memory space and resources of their parent process, making context switching faster.",
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
        "exam_frequency": "high",
        "exam_weightage": "6-8 marks"
    },
    "sql": {
        "topic": "SQL (Structured Query Language)",
        "subject": "Database Management Systems",
        "definition": "SQL is a standard programming language used for managing and manipulating relational databases.",
        "explanation": "SQL provides commands for:\n- **DDL**: CREATE, ALTER, DROP\n- **DML**: SELECT, INSERT, UPDATE, DELETE\n- **DCL**: GRANT, REVOKE\n- **TCL**: COMMIT, ROLLBACK",
        "key_points": [
            "DDL: Data Definition Language (schema operations)",
            "DML: Data Manipulation Language (data operations)",
            "DCL: Data Control Language (permissions)",
            "Joins: INNER, LEFT, RIGHT, FULL OUTER",
            "Aggregate functions: COUNT, SUM, AVG, MAX, MIN"
        ],
        "examples": [
            "SELECT * FROM students WHERE grade > 80",
            "INSERT INTO courses VALUES (101, 'DBMS', 4)"
        ],
        "exam_frequency": "high",
        "exam_weightage": "10-15 marks"
    },
}


# ══════════════════════════════════════════════════════════
# CAREER DEFINITIONS
# ══════════════════════════════════════════════════════════

CAREER_DEFINITIONS = {
    "Data Scientist": {
        "title": "Data Scientist",
        "description": "Data Scientists analyze complex data to help organizations make better decisions. They combine statistics, machine learning, and domain expertise to extract insights from data.",
        "required_skills": ["Python", "Machine Learning", "Statistics", "SQL", "Data Visualization", "Deep Learning", "NLP"],
        "recommended_subjects": ["Machine Learning", "Statistics", "Database Management", "Data Mining", "Linear Algebra"],
        "market_demand": "Very High",
        "salary_range": {"min": "₹8 LPA", "max": "₹30 LPA", "average": "₹15 LPA"},
        "next_steps": [
            "📚 Master Python and data science libraries (NumPy, Pandas, Scikit-learn)",
            "📊 Learn statistics and probability thoroughly",
            "🤖 Build ML projects on Kaggle",
            "📜 Consider certifications: Google Data Analytics, IBM Data Science"
        ]
    },
    "Software Developer": {
        "title": "Software Developer",
        "description": "Software Developers design, code, test, and maintain software applications. They work in various domains from web to mobile to systems programming.",
        "required_skills": ["Programming (Java/Python/JS)", "Data Structures", "Algorithms", "Git", "System Design", "Databases"],
        "recommended_subjects": ["Data Structures", "Algorithms", "Operating Systems", "Database Management", "Software Engineering"],
        "market_demand": "Very High",
        "salary_range": {"min": "₹6 LPA", "max": "₹25 LPA", "average": "₹12 LPA"},
        "next_steps": [
            "💻 Master at least one programming language deeply",
            "🧮 Practice DSA on LeetCode/HackerRank regularly",
            "🛠️ Build full-stack projects for portfolio",
            "📝 Prepare for technical interviews (system design, coding)"
        ]
    },
    "ML Engineer": {
        "title": "ML Engineer",
        "description": "ML Engineers build and deploy machine learning models at scale. They bridge the gap between data science and software engineering, focusing on production systems.",
        "required_skills": ["Python", "TensorFlow/PyTorch", "MLOps", "Docker", "Cloud (AWS/GCP)", "System Design"],
        "recommended_subjects": ["Machine Learning", "Deep Learning", "Software Engineering", "Cloud Computing", "Distributed Systems"],
        "market_demand": "Very High",
        "salary_range": {"min": "₹10 LPA", "max": "₹35 LPA", "average": "₹18 LPA"},
        "next_steps": [
            "🤖 Master ML/DL frameworks (TensorFlow, PyTorch)",
            "☁️ Learn cloud platforms (AWS SageMaker, GCP AI Platform)",
            "🐳 Learn Docker and Kubernetes for ML deployment",
            "📜 Consider MLOps certifications"
        ]
    },
    "DevOps Engineer": {
        "title": "DevOps Engineer",
        "description": "DevOps Engineers bridge development and operations, automating software delivery and infrastructure management.",
        "required_skills": ["Linux", "Docker", "Kubernetes", "CI/CD", "Cloud (AWS/Azure/GCP)", "Terraform", "Python/Bash"],
        "recommended_subjects": ["Operating Systems", "Computer Networks", "Cloud Computing", "Software Engineering"],
        "market_demand": "Very High",
        "salary_range": {"min": "₹8 LPA", "max": "₹28 LPA", "average": "₹14 LPA"},
        "next_steps": [
            "🐧 Master Linux and shell scripting",
            "🐳 Learn Docker and container orchestration",
            "☁️ Get certified in AWS/Azure/GCP",
            "🔄 Practice CI/CD pipeline setup"
        ]
    },
    "Full Stack Developer": {
        "title": "Full Stack Developer",
        "description": "Full Stack Developers work on both frontend and backend of web applications, handling everything from user interface to database management.",
        "required_skills": ["HTML/CSS/JavaScript", "React/Vue/Angular", "Node.js/Python/Java", "Databases", "REST APIs", "Git"],
        "recommended_subjects": ["Web Development", "Database Management", "Software Engineering", "Computer Networks"],
        "market_demand": "High",
        "salary_range": {"min": "₹5 LPA", "max": "₹22 LPA", "average": "₹10 LPA"},
        "next_steps": [
            "🎨 Master frontend (React/Vue/Angular)",
            "⚙️ Learn backend (Node.js/Python/Java)",
            "🗄️ Practice with SQL and NoSQL databases",
            "🚀 Build and deploy full-stack projects"
        ]
    },
}


# ══════════════════════════════════════════════════════════
# RESPONSE GENERATOR CLASS
# ══════════════════════════════════════════════════════════

class ResponseGenerator:
    """Generates responses based on intent and context."""

    def __init__(self, db=None, rag_service=None):
        self.db = db
        self.faculty_repo = FacultyRepository() if FacultyRepository else None
        self.subject_repo = SubjectRepository() if SubjectRepository else None
        self.career_repo = CareerRepository() if CareerRepository else None
        logger.info("ResponseGenerator initialized")

    async def generate_response(
        self,
        query: str,
        intent,  # Can be IntentType enum or string
        context: Dict[str, Any],
        student_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate a response based on intent."""
        
        # Normalize intent to string for safe comparison
        intent_str = safe_enum_value(intent, "GENERAL")
        
        logger.info(f"Generating response for intent: {intent_str}")
        
        # Handle out-of-scope
        if intent_str == "OUT_OF_SCOPE":
            return self._handle_out_of_scope()

        # Handler mapping using strings
        handlers = {
            "SYLLABUS_QUERY": self._handle_syllabus,
            "FACULTY_QUERY": self._handle_faculty,
            "PERFORMANCE_QUERY": self._handle_performance,
            "ELECTIVE_QUERY": self._handle_elective,
            "CAREER_QUERY": self._handle_career,
            "STUDY_PLAN_QUERY": self._handle_study_plan,
            "CLARIFICATION": self._handle_clarification,
            "GENERAL": self._handle_generic,
        }

        handler = handlers.get(intent_str, self._handle_generic)
        
        try:
            response = await handler(query, context, student_data)
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return self._create_error_response(str(e))

    # ══════════════════════════════════════════════════════
    # SYLLABUS HANDLER
    # ══════════════════════════════════════════════════════

    async def _handle_syllabus(
        self,
        query: str,
        context: Dict[str, Any],
        student_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Handle syllabus queries."""
        
        # First check built-in concepts
        concept_response = self._get_concept_from_builtin(query)
        if concept_response:
            return concept_response
        
        # Try repository if available
        if self.subject_repo:
            try:
                topic_data = await self.subject_repo.find_topic_by_name(query)
                if topic_data:
                    return self._format_topic_response(topic_data)
                
                topics = await self.subject_repo.search_topics(query, limit=5)
                if topics:
                    return self._format_topic_response(topics[0])
            except Exception as e:
                logger.warning(f"Subject repo error: {e}")
        
        # Not found response
        return {
            "type": "text",
            "intent": "SYLLABUS_QUERY",
            "content": {
                "message": f"I couldn't find specific information about '{query}' in my database.",
                "suggestions": [
                    "Try: 'What is deadlock?'",
                    "Try: 'Explain normalization'",
                    "Try: 'Define mutex'",
                    "Try: 'What is semaphore?'"
                ],
                "hint": "Ask about specific CS concepts or topics."
            },
            "confidence": "Low"
        }

    def _get_concept_from_builtin(self, query: str) -> Optional[Dict[str, Any]]:
        """Get concept explanation from built-in definitions."""
        query_lower = query.lower()
        
        for keyword, concept in CONCEPT_DEFINITIONS.items():
            if keyword in query_lower:
                return {
                    "type": "concept_explanation",
                    "intent": "SYLLABUS_QUERY",
                    "content": {
                        "subject": concept["subject"],
                        "topic": concept["topic"],
                        "definition": concept["definition"],
                        "explanation": concept.get("explanation", ""),
                        "key_points": concept.get("key_points", []),
                        "examples": concept.get("examples", []),
                        "exam_relevance": f"Frequency: {concept.get('exam_frequency', 'medium')}, Weightage: {concept.get('exam_weightage', 'N/A')}",
                    },
                    "confidence": "High"
                }
        
        return None

    def _format_topic_response(self, topic_data: Dict) -> Dict[str, Any]:
        """Format topic data into response."""
        topic_info = topic_data.get('topic', {})
        return {
            "type": "concept_explanation",
            "intent": "SYLLABUS_QUERY",
            "content": {
                "subject": topic_data.get('subject_name', 'Unknown'),
                "topic": topic_info.get('name', ''),
                "definition": topic_info.get('definition', ''),
                "explanation": topic_info.get('explanation', ''),
                "key_points": topic_info.get('key_points', []),
                "examples": topic_info.get('examples', []),
                "exam_relevance": f"Frequency: {topic_info.get('exam_frequency', 'medium')}",
            },
            "confidence": "High"
        }

    # ══════════════════════════════════════════════════════
    # FACULTY HANDLER
    # ══════════════════════════════════════════════════════

    async def _handle_faculty(
        self,
        query: str,
        context: Dict[str, Any],
        student_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Handle faculty queries."""
        
        query_lower = query.lower()
        
        # Extract subject from "who teaches X"
        match = re.search(r'who\s+teaches\s+(.+?)[\?]?$', query_lower)
        if match:
            subject = _normalize_subject(match.group(1).strip())
            
            if self.faculty_repo:
                try:
                    faculty_list = await self.faculty_repo.find_by_subject(subject, limit=5)
                    if faculty_list:
                        return {
                            "type": "faculty_list",
                            "intent": "FACULTY_QUERY",
                            "content": {
                                "subject": subject,
                                "faculty": [
                                    {
                                        "name": getattr(f, 'name', 'Unknown'),
                                        "designation": getattr(f, 'designation', ''),
                                        "department": getattr(f, 'department', ''),
                                        "email": getattr(f, 'email', ''),
                                    }
                                    for f in faculty_list
                                ],
                                "count": len(faculty_list),
                                "message": f"Found {len(faculty_list)} faculty member(s) teaching {subject}"
                            },
                            "confidence": "High"
                        }
                except Exception as e:
                    logger.warning(f"Faculty search error: {e}")
            
            return {
                "type": "text",
                "intent": "FACULTY_QUERY",
                "content": {
                    "message": f"I couldn't find faculty information for '{subject}'.",
                    "suggestions": [
                        "Please check the Faculty section in your dashboard",
                        "Or ask: 'List all faculty in CSE department'"
                    ]
                },
                "confidence": "Low"
            }
        
        return {
            "type": "text",
            "intent": "FACULTY_QUERY",
            "content": {
                "message": "I can help you find faculty information. Try:",
                "suggestions": [
                    "'Who teaches Operating Systems?'",
                    "'Who teaches DBMS?'",
                    "'List faculty in CSE department'",
                    "'Recommend a mentor for ML project'"
                ]
            },
            "confidence": "Medium"
        }

    # ══════════════════════════════════════════════════════
    # CAREER HANDLER
    # ══════════════════════════════════════════════════════

    async def _handle_career(
        self,
        query: str,
        context: Dict[str, Any],
        student_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Handle career queries."""
        
        career_name = _extract_career_name(query)
        
        # Check built-in definitions first
        if career_name and career_name in CAREER_DEFINITIONS:
            career = CAREER_DEFINITIONS[career_name]
            return {
                "type": "career_guidance",
                "intent": "CAREER_QUERY",
                "content": {
                    "career": {
                        "title": career["title"],
                        "description": career["description"],
                        "required_skills": career["required_skills"],
                        "recommended_subjects": career["recommended_subjects"],
                        "market_demand": career["market_demand"],
                        "salary_range": career["salary_range"],
                    },
                    "next_steps": career["next_steps"],
                },
                "confidence": "High"
            }
        
        # Try repository
        if career_name and self.career_repo:
            try:
                career = await self.career_repo.find_by_title(career_name)
                if career:
                    market_demand = getattr(career, 'market_demand', 'Medium')
                    if hasattr(market_demand, 'value'):
                        market_demand = market_demand.value
                    
                    return {
                        "type": "career_guidance",
                        "intent": "CAREER_QUERY",
                        "content": {
                            "career": {
                                "title": getattr(career, 'title', career_name),
                                "description": getattr(career, 'description', ''),
                                "required_skills": getattr(career, 'required_skills', []),
                                "recommended_subjects": getattr(career, 'recommended_subjects', []),
                                "market_demand": str(market_demand),
                            },
                        },
                        "confidence": "High"
                    }
            except Exception as e:
                logger.warning(f"Career lookup failed: {e}")
        
        # Default career list
        return {
            "type": "career_list",
            "intent": "CAREER_QUERY",
            "content": {
                "message": "Here are popular career paths in tech:",
                "careers": [
                    {"title": "Software Developer", "demand": "Very High", "salary": "₹6-25 LPA"},
                    {"title": "Data Scientist", "demand": "Very High", "salary": "₹8-30 LPA"},
                    {"title": "ML Engineer", "demand": "Very High", "salary": "₹10-35 LPA"},
                    {"title": "DevOps Engineer", "demand": "Very High", "salary": "₹8-28 LPA"},
                    {"title": "Full Stack Developer", "demand": "High", "salary": "₹5-22 LPA"},
                ],
                "hint": "Ask about a specific career for detailed guidance, e.g., 'How to become a data scientist?'"
            },
            "confidence": "Medium"
        }

    # ══════════════════════════════════════════════════════
    # OTHER HANDLERS
    # ══════════════════════════════════════════════════════

    async def _handle_performance(
        self,
        query: str,
        context: Dict[str, Any],
        student_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Handle performance queries."""
        
        if not student_data:
            return {
                "type": "text",
                "intent": "PERFORMANCE_QUERY",
                "content": {
                    "message": "Please complete your academic profile to view performance analysis.",
                    "action": "Go to Profile → Academic Data to add your semester results.",
                },
                "confidence": "High"
            }
        
        return {
            "type": "performance_analysis",
            "intent": "PERFORMANCE_QUERY",
            "content": {
                "overall_performance": {
                    "cgpa": student_data.get('cgpa'),
                    "semester": student_data.get('semester'),
                    "latest_sgpa": student_data.get('latest_sgpa'),
                },
                "weak_areas": student_data.get('weak_subjects', []),
                "strong_areas": student_data.get('strong_subjects', []),
                "message": f"Your CGPA is {student_data.get('cgpa', 'N/A')}",
            },
            "confidence": "High"
        }

    async def _handle_elective(
        self,
        query: str,
        context: Dict[str, Any],
        student_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Handle elective queries."""
        
        recommendations = [
            {"name": "Machine Learning", "reason": "High demand in AI/ML industry", "career_paths": ["Data Scientist", "ML Engineer"]},
            {"name": "Cloud Computing", "reason": "Essential for modern software development", "career_paths": ["DevOps Engineer", "Cloud Architect"]},
            {"name": "Cybersecurity", "reason": "Growing field with excellent opportunities", "career_paths": ["Security Analyst", "Ethical Hacker"]},
            {"name": "Data Science", "reason": "Combines stats, programming, and domain knowledge", "career_paths": ["Data Scientist", "Data Analyst"]},
        ]
        
        return {
            "type": "elective_recommendation",
            "intent": "ELECTIVE_QUERY",
            "content": {
                "message": "Here are recommended electives based on industry trends:",
                "recommendations": recommendations,
                "advice": "Choose electives that align with your career goals and interests."
            },
            "confidence": "Medium"
        }

    async def _handle_study_plan(
        self,
        query: str,
        context: Dict[str, Any],
        student_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Handle study plan queries."""
        
        if not student_data:
            return {
                "type": "text",
                "intent": "STUDY_PLAN_QUERY",
                "content": {
                    "message": "Complete your profile for a personalized study plan.",
                    "general_tips": [
                        "📅 Create a daily study schedule",
                        "📚 Focus on understanding concepts, not memorizing",
                        "✍️ Practice previous year questions",
                        "🔄 Regular revision is key",
                        "💤 Get adequate sleep before exams"
                    ]
                },
                "confidence": "Medium"
            }
        
        weak_areas = student_data.get('weak_subjects', [])
        
        return {
            "type": "study_plan",
            "intent": "STUDY_PLAN_QUERY",
            "content": {
                "focus_areas": weak_areas[:5] if weak_areas else ["All subjects"],
                "daily_schedule": [
                    {"subject": area, "priority": "high", "suggested_hours": 2}
                    for area in weak_areas[:3]
                ] if weak_areas else [],
                "weekly_goals": [
                    "Complete all assignments on time",
                    "Review weak subjects daily",
                    "Practice previous year questions",
                    "Attend all classes",
                ],
                "exam_tips": [
                    "Start preparation 3 weeks before exams",
                    "Allocate more time to weak subjects",
                    "Practice numerical problems daily",
                ]
            },
            "confidence": "Medium"
        }

    async def _handle_clarification(
        self,
        query: str,
        context: Dict[str, Any],
        student_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Handle clarification."""
        return {
            "type": "text",
            "intent": "CLARIFICATION",
            "content": {
                "message": "I'd be happy to help! Could you please provide more details?",
                "suggestions": [
                    "Try: 'What is deadlock in OS?'",
                    "Or: 'Who teaches Machine Learning?'",
                    "Or: 'How to become a data scientist?'",
                    "Or: 'Explain normalization in DBMS'"
                ]
            },
            "confidence": "High"
        }

    async def _handle_generic(
        self,
        query: str,
        context: Dict[str, Any],
        student_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Handle generic/greeting queries."""
        
        name = ""
        if student_data and student_data.get('name'):
            name = f" {student_data['name']}"
        
        return {
            "type": "text",
            "intent": "GENERAL",
            "content": {
                "message": f"Hello{name}! 👋 I'm your Academic Advisor Assistant.\n\n"
                          "I can help you with:\n\n"
                          "📚 **Syllabus & Concepts**\n"
                          "   'What is deadlock?', 'Explain normalization'\n\n"
                          "👨‍🏫 **Faculty Information**\n"
                          "   'Who teaches OS?', 'Who teaches ML?'\n\n"
                          "📊 **Academic Performance**\n"
                          "   'Show my grades', 'My weak subjects'\n\n"
                          "💼 **Career Guidance**\n"
                          "   'How to become a data scientist?'\n\n"
                          "📖 **Electives & Study Plans**\n"
                          "   'Recommend electives', 'Study plan for exams'\n\n"
                          "What would you like to know?",
            },
            "confidence": "High"
        }

    def _handle_out_of_scope(self) -> Dict[str, Any]:
        """Handle out-of-scope queries."""
        return {
            "type": "text",
            "intent": "OUT_OF_SCOPE",
            "content": {
                "message": "I'm an academic advisor and can only help with academic-related queries. 📚",
                "scope": [
                    "📚 Syllabus and course content",
                    "👨‍🏫 Faculty information",
                    "📊 Academic performance analysis",
                    "💼 Career guidance in tech",
                    "📖 Elective recommendations",
                    "📅 Study planning"
                ],
                "hint": "Please ask me something related to your academics!"
            },
            "confidence": "High"
        }

    def _create_error_response(self, error_msg: str = "") -> Dict[str, Any]:
        """Create error response."""
        return {
            "type": "error",
            "intent": "ERROR",
            "content": {
                "message": "I encountered an error processing your request. Please try again.",
                "error": error_msg if error_msg else "Unknown error",
            },
            "confidence": "Low"
        }