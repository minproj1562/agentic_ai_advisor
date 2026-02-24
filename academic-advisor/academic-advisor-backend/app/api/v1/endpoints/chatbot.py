# academic-advisor-backend/app/api/v1/endpoints/chatbot.py

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field
import re
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_token: Optional[str] = None
    include_student_data: bool = True


# Knowledge base
KNOWLEDGE_BASE = {
    "deadlock": {
        "definition": "A deadlock is a situation in operating systems where two or more processes are unable to proceed because each is waiting for resources held by the other.",
        "key_points": [
            "Occurs when processes hold resources while waiting for others",
            "Four necessary conditions: Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait",
            "Can be prevented by eliminating any one of the four conditions",
            "Detection involves resource allocation graphs"
        ],
        "exam_relevance": "High - frequently asked in OS exams",
        "related_topics": ["Process Synchronization", "Mutex", "Semaphores"]
    },
    "normalization": {
        "definition": "Normalization is the process of organizing data in a database to reduce redundancy and improve data integrity.",
        "key_points": [
            "1NF: Eliminate repeating groups, ensure atomic values",
            "2NF: Remove partial dependencies",
            "3NF: Remove transitive dependencies",
            "BCNF: Every determinant must be a candidate key"
        ],
        "exam_relevance": "Very High - core DBMS concept",
        "related_topics": ["Functional Dependencies", "Database Design", "SQL"]
    },
    "mutex": {
        "definition": "A mutex (mutual exclusion) is a synchronization primitive that ensures only one thread can access a shared resource at a time.",
        "key_points": [
            "Binary state: locked or unlocked",
            "Only the locking thread can unlock",
            "Prevents race conditions",
            "Different from semaphore"
        ],
        "exam_relevance": "High - important for process synchronization",
        "related_topics": ["Semaphores", "Critical Section", "Deadlock"]
    },
    "semaphore": {
        "definition": "A semaphore is a synchronization tool used to control access to shared resources by multiple processes.",
        "key_points": [
            "Binary semaphore (0 or 1) and Counting semaphore",
            "Operations: wait()/P() and signal()/V()",
            "Used for producer-consumer problems",
            "Can cause deadlock if misused"
        ],
        "exam_relevance": "Very High - common in OS exams",
        "related_topics": ["Mutex", "Critical Section", "Process Synchronization"]
    }
}

# Out of scope patterns
OUT_OF_SCOPE_PATTERNS = [
    r'\b(movie|film|actor|actress|bollywood|hollywood|netflix)\b',
    r'\b(cricket|football|soccer|basketball|ipl|fifa)\b',
    r'\b(politics|election|vote|government|minister)\b',
    r'\b(weather|recipe|cook|travel|vacation)\b',
    r'\b(game|gaming|pubg|fortnite|minecraft)\b',
]


def is_out_of_scope(message: str) -> bool:
    """Check if message is out of scope"""
    message_lower = message.lower()
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, message_lower, re.IGNORECASE):
            return True
    return False


def find_topic(message: str) -> Optional[str]:
    """Find matching topic in knowledge base"""
    message_lower = message.lower()
    for topic in KNOWLEDGE_BASE.keys():
        if topic in message_lower:
            return topic
    return None


def classify_intent(message: str) -> str:
    """Classify message intent"""
    message_lower = message.lower()
    
    if is_out_of_scope(message):
        return "OUT_OF_SCOPE"
    
    syllabus_keywords = ['explain', 'what is', 'define', 'concept', 'topic', 'syllabus', 'unit']
    faculty_keywords = ['faculty', 'professor', 'teacher', 'mentor', 'who teaches']
    performance_keywords = ['performance', 'grade', 'cgpa', 'sgpa', 'marks', 'result']
    elective_keywords = ['elective', 'choose', 'recommend', 'select', 'course']
    career_keywords = ['career', 'job', 'placement', 'industry', 'future']
    
    for keyword in syllabus_keywords:
        if keyword in message_lower:
            return "SYLLABUS_QUERY"
    
    for keyword in faculty_keywords:
        if keyword in message_lower:
            return "FACULTY_QUERY"
    
    for keyword in performance_keywords:
        if keyword in message_lower:
            return "PERFORMANCE_QUERY"
    
    for keyword in elective_keywords:
        if keyword in message_lower:
            return "ELECTIVE_QUERY"
    
    for keyword in career_keywords:
        if keyword in message_lower:
            return "CAREER_QUERY"
    
    return "GENERAL"


@router.post("/chat")
async def chat(request: ChatMessageRequest):
    """Process chat message and return response"""
    
    try:
        message = request.message.strip()
        
        # Check out of scope
        if is_out_of_scope(message):
            return PlainTextResponse(content="Beyond my scope")
        
        # Classify intent
        intent = classify_intent(message)
        
        # Find topic in knowledge base
        topic = find_topic(message)
        
        if topic and topic in KNOWLEDGE_BASE:
            data = KNOWLEDGE_BASE[topic]
            return JSONResponse(content={
                "type": "concept_explanation",
                "intent": intent,
                "content": {
                    "definition": data["definition"],
                    "key_points": data["key_points"],
                    "exam_relevance": data["exam_relevance"],
                    "related_topics": data["related_topics"]
                },
                "confidence": "High",
                "session_token": request.session_token or "demo-session"
            })
        
        # Default responses based on intent
        if intent == "SYLLABUS_QUERY":
            return JSONResponse(content={
                "type": "text",
                "intent": intent,
                "content": {
                    "message": "I can help you understand academic concepts. Please specify which topic you'd like to learn about (e.g., deadlock, normalization, mutex, semaphore)."
                },
                "confidence": "Medium",
                "session_token": request.session_token or "demo-session"
            })
        
        if intent == "FACULTY_QUERY":
            return JSONResponse(content={
                "type": "faculty_list",
                "intent": intent,
                "content": {
                    "faculty": [
                        {"name": "Dr. Rajesh Kumar", "subjects_taught": ["Operating Systems", "Networks"], "experience_years": 15},
                        {"name": "Dr. Priya Sharma", "subjects_taught": ["DBMS", "Big Data"], "experience_years": 20},
                        {"name": "Dr. Amit Verma", "subjects_taught": ["Machine Learning", "AI"], "experience_years": 8}
                    ],
                    "count": 3
                },
                "confidence": "High",
                "session_token": request.session_token or "demo-session"
            })
        
        if intent == "CAREER_QUERY":
            return JSONResponse(content={
                "type": "text",
                "intent": intent,
                "content": {
                    "message": "**Career Paths in Engineering:**\n\n• **Software Development** - 6-30+ LPA\n• **Data Science/ML** - 8-35+ LPA\n• **Cloud/DevOps** - 8-25+ LPA\n• **Cybersecurity** - 6-20+ LPA\n\nWould you like details on any specific path?"
                },
                "confidence": "High",
                "session_token": request.session_token or "demo-session"
            })
        
        # General response
        return JSONResponse(content={
            "type": "text",
            "intent": intent,
            "content": {
                "message": "I'm your Academic Guidance Assistant. I can help you with:\n\n📚 Syllabus explanations\n👨‍🏫 Faculty information\n📊 Performance analysis\n📖 Elective recommendations\n💼 Career guidance\n\nHow can I assist you today?"
            },
            "confidence": "High",
            "session_token": request.session_token or "demo-session"
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "type": "error",
                "intent": "ERROR",
                "content": {"message": "An error occurred. Please try again."},
                "confidence": "Low"
            }
        )


@router.get("/suggestions")
async def get_suggestions():
    """Get query suggestions"""
    return {
        "suggestions": [
            "Explain the concept of deadlock",
            "What is normalization in DBMS?",
            "Who teaches Operating Systems?",
            "Recommend electives for ML career",
            "How to become a data scientist?"
        ]
    }


@router.get("/history")
async def get_history():
    """Get conversation history (placeholder)"""
    return {
        "messages": [],
        "session_token": None
    }