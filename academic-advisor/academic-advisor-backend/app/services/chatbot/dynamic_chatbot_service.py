import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from beanie import PydanticObjectId
from bson import ObjectId

from app.models.syllabus import (
    Subject, SubjectUnit, Topic, Faculty, FacultySubject,
    CareerPath, Department, StudentProfile, StudentPerformance
)

logger = logging.getLogger(__name__)


class DynamicChatbotService:
    """
    Dynamic chatbot service using Beanie ODM for MongoDB.
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

        # Intent patterns with weights
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

    async def search_topics(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search topics in the database using text search."""
        query_lower = query.lower()

        # Use regex for flexible matching (since MongoDB text search requires index)
        topics = await Topic.find(
            {"$or": [
                {"name": {"$regex": query_lower, "$options": "i"}},
                {"keywords": {"$in": [query_lower]}},
                {"definition": {"$regex": query_lower, "$options": "i"}}
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
                "unit_title": unit.title
            })

        return results

    async def get_subject_info(self, subject_query: str) -> Optional[Dict[str, Any]]:
        """Get subject information by code or name."""
        subject = await Subject.find_one(
            {"$or": [
                {"code": {"$regex": subject_query, "$options": "i"}},
                {"name": {"$regex": subject_query, "$options": "i"}}
            ]}
        )

        if not subject:
            return None

        # Get units with topics
        units = await SubjectUnit.find(SubjectUnit.subject.id == subject.id).to_list()
        unit_list = []
        for unit in units:
            topics = await Topic.find(Topic.unit.id == unit.id).to_list()
            unit_list.append({
                "unit_number": unit.unit_number,
                "title": unit.title,
                "topics": [t.name for t in topics]
            })

        # Get faculty teaching this subject
        faculty_assignments = await FacultySubject.find(
            FacultySubject.subject.id == subject.id
        ).to_list()
        faculty_list = []
        for fa in faculty_assignments:
            faculty = await fa.faculty.fetch()
            faculty_list.append({
                "name": faculty.name,
                "designation": faculty.designation,
                "rating": faculty.teaching_rating
            })

        return {
            "code": subject.code,
            "name": subject.name,
            "semester": subject.semester,
            "credits": subject.credits,
            "description": subject.description,
            "learning_outcomes": subject.learning_outcomes,
            "reference_books": subject.reference_books,
            "units": unit_list,
            "faculty": faculty_list
        }

    async def handle_syllabus_query(self, message: str) -> Dict[str, Any]:
        """Handle syllabus-related queries."""
        # First, search for specific topics
        topics = await self.search_topics(message)

        if topics:
            topic = topics[0]
            return {
                "type": "concept_explanation",
                "intent": "SYLLABUS_QUERY",
                "content": {
                    "topic": topic["topic_name"],
                    "definition": topic["definition"],
                    "key_points": topic["key_points"],
                    "exam_relevance": f"Frequency: {topic['exam_frequency'] or 'medium'}, Difficulty: {topic['difficulty_level']}",
                    "related_topics": topic.get("related_topics", []),
                    "context": {
                        "subject": topic["subject_name"],
                        "unit": f"Unit {topic['unit_number']}: {topic['unit_title']}"
                    }
                },
                "confidence": "High",
                "sources": [{"subject": topic["subject_code"], "unit": topic["unit_number"]}]
            }

        # Try to find subject information
        subject_keywords = ["subject", "course", "syllabus"]
        if any(kw in message.lower() for kw in subject_keywords):
            # Extract potential subject name after "of"/"for"/"about"
            words = message.lower().split()
            for i, word in enumerate(words):
                if word in ["of", "for", "about"] and i + 1 < len(words):
                    potential_subject = " ".join(words[i+1:])
                    subject_info = await self.get_subject_info(potential_subject)
                    if subject_info:
                        return {
                            "type": "syllabus_breakdown",
                            "intent": "SYLLABUS_QUERY",
                            "content": subject_info,
                            "confidence": "High"
                        }

        # Get list of available subjects
        subjects = await Subject.find(Subject.is_active == True).limit(10).to_list()
        subject_list = [{"code": s.code, "name": s.name, "semester": s.semester} for s in subjects]

        return {
            "type": "text",
            "intent": "SYLLABUS_QUERY",
            "content": {
                "message": "I can help you with syllabus-related queries. Please specify which topic or subject you'd like to know about.",
                "available_subjects": subject_list,
                "hint": "Try asking: 'Explain deadlock', 'What is normalization?', 'Topics in Operating Systems'"
            },
            "confidence": "Medium"
        }

    # ==================== FACULTY QUERIES ====================

    async def search_faculty(
        self,
        query: Optional[str] = None,
        subject: Optional[str] = None,
        department: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search faculty members."""
        filters = {"is_active": True}

        if department:
            dept = await Department.find_one({"name": {"$regex": department, "$options": "i"}})
            if dept:
                filters["department.$id"] = dept.id

        if subject:
            subj = await Subject.find_one(
                {"$or": [
                    {"name": {"$regex": subject, "$options": "i"}},
                    {"code": {"$regex": subject, "$options": "i"}}
                ]}
            )
            if subj:
                # Find faculty teaching this subject
                faculty_ids = []
                assignments = await FacultySubject.find(
                    FacultySubject.subject.id == subj.id
                ).to_list()
                for fa in assignments:
                    faculty_ids.append(fa.faculty.id)
                if faculty_ids:
                    filters["_id"] = {"$in": faculty_ids}

        if query:
            filters["$or"] = [
                {"name": {"$regex": query, "$options": "i"}},
                {"specializations": {"$in": [query]}},
                {"research_areas": {"$in": [query]}}
            ]

        faculty_list = await Faculty.find(filters).sort(-Faculty.teaching_rating).limit(limit).to_list()

        results = []
        for fac in faculty_list:
            dept = await fac.department.fetch()
            subjects_taught = []
            assignments = await FacultySubject.find(FacultySubject.faculty.id == fac.id).to_list()
            for fa in assignments:
                subj = await fa.subject.fetch()
                subjects_taught.append(subj.name)

            results.append({
                "name": fac.name,
                "designation": fac.designation,
                "department": dept.name if dept else None,
                "experience_years": fac.experience_years,
                "specializations": fac.specializations,
                "research_areas": fac.research_areas,
                "subjects_taught": subjects_taught,
                "teaching_style": fac.teaching_style,
                "mentoring_areas": fac.mentoring_areas,
                "office_hours": fac.office_hours,
                "office_location": fac.office_location,
                "teaching_rating": fac.teaching_rating,
                "is_available_for_mentoring": fac.is_available_for_mentoring
            })

        return results

    async def handle_faculty_query(self, message: str) -> Dict[str, Any]:
        """Handle faculty-related queries."""
        message_lower = message.lower()

        # Check if asking about specific subject
        subjects = await Subject.find(Subject.is_active == True).to_list()
        subject_match = None
        for subj in subjects:
            if subj.name.lower() in message_lower or subj.code.lower() in message_lower:
                subject_match = subj.name
                break

        # Check if asking for recommendation
        is_recommendation = any(word in message_lower for word in ['recommend', 'suggest', 'best', 'good', 'mentor'])

        faculty_list = await self.search_faculty(subject=subject_match)

        if not faculty_list:
            faculty_list = await self.search_faculty(limit=5)

        if is_recommendation and faculty_list:
            faculty_list.sort(key=lambda x: x.get('teaching_rating', 0) or 0, reverse=True)
            return {
                "type": "faculty_recommendation",
                "intent": "FACULTY_QUERY",
                "content": {
                    "recommendations": faculty_list[:3],
                    "selection_criteria": f"Based on {'subject expertise in ' + subject_match if subject_match else 'overall ratings and experience'}",
                    "total_found": len(faculty_list)
                },
                "confidence": "High"
            }

        return {
            "type": "faculty_list",
            "intent": "FACULTY_QUERY",
            "content": {
                "faculty": faculty_list,
                "count": len(faculty_list),
                "filter_applied": subject_match
            },
            "confidence": "High"
        }

    # ==================== CAREER QUERIES ====================

    async def search_careers(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search career paths."""
        filters = {"is_active": True}

        if query:
            filters["$or"] = [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"keywords": {"$in": [query]}}
            ]

        careers = await CareerPath.find(filters).to_list()

        results = []
        for career in careers:
            results.append({
                "title": career.title,
                "category": career.category,
                "description": career.description,
                "required_skills": career.required_skills,
                "recommended_subjects": career.recommended_subjects,
                "recommended_electives": career.recommended_electives,
                "certifications": career.certifications,
                "salary_range": career.salary_range,
                "job_titles": career.job_titles,
                "companies": career.companies,
                "growth_potential": career.growth_potential,
                "market_demand": career.market_demand,
                "roadmap": career.roadmap
            })

        return results

    async def handle_career_query(self, message: str) -> Dict[str, Any]:
        """Handle career-related queries."""
        careers = await self.search_careers(query=message)

        if careers:
            # If specific career found (title matches closely)
            if len(careers) == 1 or any(c['title'].lower() in message.lower() for c in careers):
                career = careers[0]
                return {
                    "type": "career_guidance",
                    "intent": "CAREER_QUERY",
                    "content": {
                        "career": career,
                        "roadmap": career.get("roadmap", []),
                        "next_steps": [
                            f"Focus on: {', '.join(career.get('recommended_subjects', [])[:3])}",
                            f"Consider electives: {', '.join(career.get('recommended_electives', [])[:2])}",
                            f"Get certified: {career.get('certifications', ['Start with fundamentals'])[0]}"
                        ]
                    },
                    "confidence": "High"
                }

            # Multiple careers
            return {
                "type": "career_list",
                "intent": "CAREER_QUERY",
                "content": {
                    "careers": careers[:5],
                    "message": "Here are career paths that might interest you:",
                    "tip": "Ask about a specific career for detailed guidance"
                },
                "confidence": "High"
            }

        # Default - list all careers
        all_careers = await self.search_careers()
        return {
            "type": "text",
            "intent": "CAREER_QUERY",
            "content": {
                "message": "I can help you explore career paths. Here are some options:",
                "available_careers": [c['title'] for c in all_careers],
                "hint": "Ask 'How to become a data scientist?' or 'Career path for software development'"
            },
            "confidence": "Medium"
        }

    # ==================== PERFORMANCE QUERIES ====================

    async def get_student_performance(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get student performance data from MongoDB."""
        # StudentProfile and StudentPerformance models need to be defined similarly.
        # Here we assume they exist with appropriate links.
        from app.models.student import StudentProfile, StudentPerformance

        # Find student by firebase_uid
        profile = await StudentProfile.find_one({"firebase_uid": student_id})
        if not profile:
            return None

        performances = await StudentPerformance.find(
            StudentPerformance.student.id == profile.id
        ).sort(-StudentPerformance.semester).to_list()

        if not performances:
            return {
                "profile": {
                    "name": profile.name,
                    "branch": profile.branch,
                    "semester": profile.current_semester,
                    "cgpa": profile.cgpa
                },
                "performance_data": None
            }

        # Calculate trends
        sgpa_trend = []
        weak_subjects = []

        for perf in performances:
            sgpa_trend.append({
                "semester": perf.semester,
                "sgpa": perf.sgpa,
                "credits": perf.credits_earned
            })
            # Identify weak subjects (grade < B) - adjust logic as needed
            if perf.subject_grades:
                for subject, grade in perf.subject_grades.items():
                    if grade in ['C', 'D', 'F', 'C+', 'D+']:
                        weak_subjects.append(subject)

        return {
            "profile": {
                "name": profile.name,
                "branch": profile.branch,
                "semester": profile.current_semester,
                "cgpa": profile.cgpa
            },
            "performance_data": {
                "sgpa_trend": sgpa_trend,
                "latest_sgpa": performances[0].sgpa if performances else None,
                "weak_subjects": list(set(weak_subjects)),
                "trend": "improving" if len(sgpa_trend) > 1 and sgpa_trend[0]["sgpa"] > sgpa_trend[1]["sgpa"] else "stable"
            }
        }

    async def handle_performance_query(self, message: str, student_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle performance-related queries."""
        if not student_id:
            return {
                "type": "text",
                "intent": "PERFORMANCE_QUERY",
                "content": {
                    "message": "To view your performance analysis, please ensure you're logged in and have completed your academic profile setup.",
                    "actions": [
                        "Complete your profile in the Academic Data Entry section",
                        "Add your semester-wise grades",
                        "Return here for personalized analysis"
                    ]
                },
                "confidence": "High"
            }

        performance = await self.get_student_performance(student_id)

        if not performance:
            return {
                "type": "text",
                "intent": "PERFORMANCE_QUERY",
                "content": {
                    "message": "No performance data found. Please complete your academic profile first."
                },
                "confidence": "Medium"
            }

        if not performance.get("performance_data"):
            return {
                "type": "text",
                "intent": "PERFORMANCE_QUERY",
                "content": {
                    "message": "Profile found but no grade data available. Please add your semester grades.",
                    "profile": performance["profile"]
                },
                "confidence": "Medium"
            }

        # Generate insights
        perf_data = performance["performance_data"]
        insights = []
        if perf_data["trend"] == "improving":
            insights.append("📈 Great progress! Your grades are improving.")
        elif len(perf_data.get("weak_subjects", [])) > 2:
            insights.append("⚠️ Focus needed on multiple subjects. Consider study groups.")
        if perf_data.get("weak_subjects"):
            insights.append(f"📚 Focus areas: {', '.join(perf_data['weak_subjects'][:3])}")

        return {
            "type": "performance_analysis",
            "intent": "PERFORMANCE_QUERY",
            "content": {
                "profile": performance["profile"],
                "current_cgpa": performance["profile"]["cgpa"],
                "latest_sgpa": perf_data["latest_sgpa"],
                "sgpa_trend": perf_data["sgpa_trend"],
                "trend_direction": perf_data["trend"],
                "weak_subjects": perf_data["weak_subjects"],
                "insights": insights,
                "recommendations": [
                    f"Strengthen {perf_data['weak_subjects'][0]}" if perf_data.get("weak_subjects") else "Maintain current performance",
                    "Review previous semester topics",
                    "Consider faculty mentoring for weak areas"
                ]
            },
            "confidence": "High"
        }

    # ==================== MAIN PROCESS METHOD ====================

    async def process_message(
        self,
        message: str,
        student_id: Optional[str] = None,
        student_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Main method to process user message and return appropriate response."""
        intent, confidence = self.classify_intent(message)

        if intent == "OUT_OF_SCOPE":
            return {
                "type": "text",
                "intent": "OUT_OF_SCOPE",
                "content": {
                    "message": "I'm here to help with academic queries only. Please ask about syllabus, faculty, career paths, or your academic performance."
                },
                "confidence": "High"
            }

        if intent == "SYLLABUS_QUERY":
            return await self.handle_syllabus_query(message)
        elif intent == "FACULTY_QUERY":
            return await self.handle_faculty_query(message)
        elif intent == "CAREER_QUERY":
            return await self.handle_career_query(message)
        elif intent == "PERFORMANCE_QUERY":
            return await self.handle_performance_query(message, student_id)
        elif intent == "ELECTIVE_QUERY":
            return {
                "type": "text",
                "intent": "ELECTIVE_QUERY",
                "content": {
                    "message": "For elective recommendations, please check the AI Recommendations section in your dashboard, which provides personalized suggestions based on your interests and career goals."
                },
                "confidence": "Medium"
            }

        # General fallback
        return {
            "type": "text",
            "intent": "GENERAL",
            "content": {
                "message": (
                    "I'm your Academic Guidance Assistant. I can help you with:\n\n"
                    "📚 **Syllabus** - Explain concepts and topics\n"
                    "👨‍🏫 **Faculty** - Find professors and mentors\n"
                    "📊 **Performance** - Analyze your grades\n"
                    "💼 **Career** - Explore career paths\n"
                    "📖 **Electives** - Course recommendations\n\n"
                    "What would you like to know?"
                ),
                "suggestions": [
                    "Explain deadlock in OS",
                    "Who teaches DBMS?",
                    "How to become a data scientist?"
                ]
            },
            "confidence": "High"
        }