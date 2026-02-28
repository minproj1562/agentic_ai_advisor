# app/services/chatbot/dynamic_chatbot_service.py
"""
Dynamic Chatbot Service — Safe version
Handles syllabus/faculty queries via Person A's models when available.
Falls back gracefully when models don't exist yet.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Safe imports — Person A's models may not exist yet ────
_SYLLABUS_MODELS_AVAILABLE = False
try:
    from app.models.syllabus import (
        Subject, SubjectUnit, Topic, Faculty, FacultySubject,
        CareerPath, Department,
    )
    _SYLLABUS_MODELS_AVAILABLE = True
    logger.info("✅ Syllabus models available (Person A)")
except ImportError:
    logger.info("ℹ️ Syllabus models not yet available — using fallback responses")


class DynamicChatbotService:
    """
    Dynamic chatbot service using Beanie ODM for MongoDB.
    Gracefully handles missing Person A models.
    """

    # ==================== INTENT CLASSIFICATION ====================

    @staticmethod
    def classify_intent(message: str) -> Tuple[str, float]:
        """Classify user intent based on message content."""
        message_lower = message.lower()

        # Out of scope patterns
        out_of_scope = [
            r'\b(movie|film|actor|actress|bollywood|hollywood|netflix)\b',
            r'\b(cricket|football|soccer|basketball|ipl|fifa|sports)\b',
            r'\b(politics|election|vote|government|minister|party)\b',
            r'\b(weather|recipe|cook|food|restaurant|hotel)\b',
            r'\b(game|gaming|pubg|fortnite|minecraft|gta)\b',
            r'\b(relationship|dating|love|marriage)\b',
        ]
        for pattern in out_of_scope:
            if re.search(pattern, message_lower):
                return "OUT_OF_SCOPE", 0.95

        intent_patterns = {
            "SYLLABUS_QUERY": [
                (r'\b(explain|what is|define|describe|tell me about)\b', 0.4),
                (r'\b(topic|concept|unit|chapter|syllabus)\b', 0.3),
                (r'\b(how does|how do|working of|mechanism)\b', 0.3),
            ],
            "FACULTY_QUERY": [
                (r'\b(faculty|professor|teacher|instructor|dr\.?|prof\.?)\b', 0.4),
                (r'\b(who teaches|taught by|teaches)\b', 0.4),
                (r'\b(mentor|mentoring|guide|advisor)\b', 0.3),
            ],
            "PERFORMANCE_QUERY": [
                (r'\b(my|performance|grade|marks|cgpa|sgpa|result)\b', 0.4),
                (r'\b(weak|weakness|improve|better|poor)\b', 0.3),
                (r'\b(analysis|report|progress|standing)\b', 0.3),
            ],
            "ELECTIVE_QUERY": [
                (r'\b(elective|optional|choose|select)\b.*\b(subject|course)\b', 0.5),
                (r'\b(recommend|suggest)\b.*\b(elective|course|subject)\b', 0.4),
                (r'\b(which|what)\b.*\b(elective|subject)\b', 0.3),
            ],
            "CAREER_QUERY": [
                (r'\b(career|job|placement|work|profession)\b', 0.4),
                (r'\b(become|future|path|roadmap)\b', 0.3),
                (r'\b(skill|company|industry|salary)\b', 0.3),
            ],
        }

        scores = {}
        for intent, patterns in intent_patterns.items():
            score = 0
            for pattern, weight in patterns:
                if re.search(pattern, message_lower):
                    score += weight
            if score > 0:
                scores[intent] = min(score, 0.95)

        if scores:
            best_intent = max(scores, key=scores.get)
            return best_intent, scores[best_intent]

        return "GENERAL", 0.5

    # ==================== SYLLABUS QUERIES ====================

    async def handle_syllabus_query(self, message: str) -> Dict[str, Any]:
        """Handle syllabus-related queries."""
        if not _SYLLABUS_MODELS_AVAILABLE:
            return self._syllabus_fallback(message)

        try:
            # Try Person A's full implementation
            topics = await self._search_topics(message)
            if topics:
                topic = topics[0]
                return {
                    "type": "concept_explanation",
                    "intent": "SYLLABUS_QUERY",
                    "content": {
                        "topic": topic["topic_name"],
                        "definition": topic["definition"],
                        "key_points": topic["key_points"],
                        "exam_relevance": f"Frequency: {topic.get('exam_frequency', 'medium')}",
                        "related_topics": topic.get("related_topics", []),
                        "context": {
                            "subject": topic.get("subject_name"),
                            "unit": f"Unit {topic.get('unit_number', '?')}: {topic.get('unit_title', '')}",
                        },
                    },
                    "confidence": "High",
                    "sources": [{"subject": topic.get("subject_code"), "unit": topic.get("unit_number")}],
                }

            subject_info = await self._find_subject(message)
            if subject_info:
                return {
                    "type": "syllabus_breakdown",
                    "intent": "SYLLABUS_QUERY",
                    "content": subject_info,
                    "confidence": "High",
                }
        except Exception as e:
            logger.warning(f"Syllabus query with models failed: {e}")

        return self._syllabus_fallback(message)

    async def _search_topics(self, query: str, limit: int = 5) -> List[Dict]:
        if not _SYLLABUS_MODELS_AVAILABLE:
            return []
        try:
            query_lower = query.lower()
            topics = await Topic.find(
                {"$or": [
                    {"name": {"$regex": query_lower, "$options": "i"}},
                    {"keywords": {"$in": [query_lower]}},
                    {"definition": {"$regex": query_lower, "$options": "i"}},
                ]}
            ).limit(limit).to_list()

            results = []
            for topic in topics:
                unit = await topic.unit.fetch()
                subject = await unit.subject.fetch()
                results.append({
                    "topic_name": topic.name,
                    "definition": topic.definition,
                    "key_points": topic.key_points,
                    "exam_frequency": topic.exam_frequency,
                    "difficulty_level": topic.difficulty_level,
                    "related_topics": topic.related_topics,
                    "subject_name": subject.name,
                    "subject_code": subject.code,
                    "unit_number": unit.unit_number,
                    "unit_title": unit.title,
                })
            return results
        except Exception as e:
            logger.warning(f"Topic search failed: {e}")
            return []

    async def _find_subject(self, query: str) -> Optional[Dict]:
        if not _SYLLABUS_MODELS_AVAILABLE:
            return None
        try:
            words = query.lower().split()
            for i, word in enumerate(words):
                if word in ["of", "for", "about"] and i + 1 < len(words):
                    potential = " ".join(words[i + 1:])
                    subject = await Subject.find_one(
                        {"$or": [
                            {"code": {"$regex": potential, "$options": "i"}},
                            {"name": {"$regex": potential, "$options": "i"}},
                        ]}
                    )
                    if subject:
                        return {"code": subject.code, "name": subject.name,
                                "semester": subject.semester, "credits": subject.credits}
        except Exception as e:
            logger.warning(f"Subject search failed: {e}")
        return None

    def _syllabus_fallback(self, message: str) -> Dict[str, Any]:
        """Fallback when syllabus models aren't available yet."""
        # Basic knowledge base
        KB = {
            "deadlock": {
                "definition": "A deadlock is a situation in operating systems where two or more processes are unable to proceed because each is waiting for resources held by the other.",
                "key_points": [
                    "Four conditions: Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait",
                    "Can be prevented by eliminating any one condition",
                    "Detection uses resource allocation graphs",
                ],
                "exam_relevance": "High — frequently asked in OS exams",
                "related_topics": ["Mutex", "Semaphore", "Process Synchronization"],
            },
            "normalization": {
                "definition": "Normalization is the process of organizing data in a database to reduce redundancy and improve integrity.",
                "key_points": [
                    "1NF: Atomic values, no repeating groups",
                    "2NF: Remove partial dependencies",
                    "3NF: Remove transitive dependencies",
                    "BCNF: Every determinant is a candidate key",
                ],
                "exam_relevance": "Very High — core DBMS concept",
                "related_topics": ["Functional Dependencies", "SQL", "Database Design"],
            },
            "mutex": {
                "definition": "A mutex ensures only one thread can access a shared resource at a time.",
                "key_points": [
                    "Binary state: locked or unlocked",
                    "Only the locking thread can unlock",
                    "Prevents race conditions",
                ],
                "exam_relevance": "High",
                "related_topics": ["Semaphore", "Deadlock", "Critical Section"],
            },
            "semaphore": {
                "definition": "A semaphore controls access to shared resources using wait() and signal() operations.",
                "key_points": [
                    "Binary (0/1) and Counting types",
                    "wait()/P() decrements, signal()/V() increments",
                    "Solves producer-consumer problems",
                ],
                "exam_relevance": "Very High",
                "related_topics": ["Mutex", "Deadlock", "Process Synchronization"],
            },
        }

        msg_lower = message.lower()
        for topic, data in KB.items():
            if topic in msg_lower:
                return {
                    "type": "concept_explanation",
                    "intent": "SYLLABUS_QUERY",
                    "content": data,
                    "confidence": "High",
                }

        return {
            "type": "text",
            "intent": "SYLLABUS_QUERY",
            "content": {
                "message": (
                    "I can help with academic concepts. Try asking:\n\n"
                    "• 'Explain deadlock'\n"
                    "• 'What is normalization?'\n"
                    "• 'Define semaphore'\n"
                    "• 'What is mutex?'\n\n"
                    "Full syllabus search will be available soon."
                ),
            },
            "confidence": "Medium",
        }

    # ==================== FACULTY QUERIES ====================

    async def handle_faculty_query(self, message: str) -> Dict[str, Any]:
        """Handle faculty-related queries."""
        if not _SYLLABUS_MODELS_AVAILABLE:
            return self._faculty_fallback(message)

        try:
            faculty_list = await self._search_faculty(message)
            if faculty_list:
                is_rec = any(w in message.lower() for w in
                             ['recommend', 'suggest', 'best', 'good', 'mentor'])
                if is_rec:
                    return {
                        "type": "faculty_recommendation",
                        "intent": "FACULTY_QUERY",
                        "content": {
                            "recommendations": faculty_list[:3],
                            "selection_criteria": "Based on expertise and ratings",
                        },
                        "confidence": "High",
                    }
                return {
                    "type": "faculty_list",
                    "intent": "FACULTY_QUERY",
                    "content": {"faculty": faculty_list, "count": len(faculty_list)},
                    "confidence": "High",
                }
        except Exception as e:
            logger.warning(f"Faculty query with models failed: {e}")

        return self._faculty_fallback(message)

    async def _search_faculty(self, query: str, limit: int = 5) -> List[Dict]:
        if not _SYLLABUS_MODELS_AVAILABLE:
            return []
        try:
            faculty_list = await Faculty.find(
                {"is_active": True}
            ).sort(-Faculty.teaching_rating).limit(limit).to_list()

            results = []
            for fac in faculty_list:
                dept = await fac.department.fetch() if hasattr(fac, 'department') else None
                results.append({
                    "name": fac.name,
                    "designation": getattr(fac, "designation", "Professor"),
                    "department": dept.name if dept else "CS",
                    "experience_years": getattr(fac, "experience_years", 0),
                    "specializations": getattr(fac, "specializations", []),
                    "research_areas": getattr(fac, "research_areas", []),
                    "teaching_style": getattr(fac, "teaching_style", "Interactive"),
                    "teaching_rating": getattr(fac, "teaching_rating", 0),
                    "subjects_taught": [],
                })
            return results
        except Exception as e:
            logger.warning(f"Faculty search failed: {e}")
            return []

    def _faculty_fallback(self, message: str) -> Dict[str, Any]:
        """Fallback faculty data."""
        sample_faculty = [
            {
                "name": "Dr. Rajesh Kumar",
                "department": "IT",
                "subjects_taught": ["Operating Systems", "Computer Networks"],
                "experience_years": 15,
                "teaching_style": "Interactive with demos",
                "rating": 4.5,
                "research_areas": ["Distributed Systems", "Cloud Computing"],
            },
            {
                "name": "Dr. Priya Sharma",
                "department": "IT",
                "subjects_taught": ["DBMS", "Data Warehousing"],
                "experience_years": 20,
                "teaching_style": "Case study driven",
                "rating": 4.8,
                "research_areas": ["Data Mining", "ML"],
            },
            {
                "name": "Dr. Amit Verma",
                "department": "IT",
                "subjects_taught": ["Machine Learning", "AI"],
                "experience_years": 8,
                "teaching_style": "Project-based learning",
                "rating": 4.6,
                "research_areas": ["Neural Networks", "NLP"],
            },
        ]

        is_rec = any(w in message.lower() for w in
                     ['recommend', 'suggest', 'best', 'mentor'])
        if is_rec:
            return {
                "type": "faculty_recommendation",
                "intent": "FACULTY_QUERY",
                "content": {
                    "recommendations": sample_faculty,
                    "selection_criteria": "Based on expertise and experience (sample data)",
                },
                "confidence": "Medium",
            }

        return {
            "type": "faculty_list",
            "intent": "FACULTY_QUERY",
            "content": {
                "faculty": sample_faculty,
                "count": len(sample_faculty),
            },
            "confidence": "Medium",
        }

    # ==================== MAIN PROCESS METHOD ====================

    async def process_message(
        self,
        message: str,
        student_id: Optional[str] = None,
        student_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Main method to process user message."""
        intent, confidence = self.classify_intent(message)

        if intent == "OUT_OF_SCOPE":
            return {
                "type": "text",
                "intent": "OUT_OF_SCOPE",
                "content": {
                    "message": "I'm here to help with academic queries only."
                },
                "confidence": "High",
            }

        if intent == "SYLLABUS_QUERY":
            return await self.handle_syllabus_query(message)
        elif intent == "FACULTY_QUERY":
            return await self.handle_faculty_query(message)

        # Other intents are handled by ChatbotService → ResponseGenerator
        return {
            "type": "text",
            "intent": "GENERAL",
            "content": {
                "message": (
                    "I'm your Academic Guidance Assistant. I can help with:\n\n"
                    "📚 **Syllabus** — Concept explanations\n"
                    "👨‍🏫 **Faculty** — Mentor recommendations\n"
                    "📊 **Performance** — Grade analysis\n"
                    "📖 **Electives** — Course selection\n"
                    "💼 **Career** — Career roadmaps\n"
                    "📅 **Study Plan** — Schedules\n\n"
                    "What would you like to know?"
                ),
            },
            "confidence": "High",
        }