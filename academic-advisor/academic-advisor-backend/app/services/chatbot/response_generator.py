# academic-advisor-backend/app/services/chatbot/response_generator.py

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from sqlalchemy.orm import Session

from app.models.chatbot import IntentType, ResponseType, ConfidenceLevel
from app.services.chatbot.rag_service import RAGService
from app.core.config import settings

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """
    Generates structured responses based on intent, context, and retrieved data.
    Enforces domain restrictions and anti-hallucination policies.
    """
    
    SYSTEM_PROMPT = """You are the AI Academic Guidance Assistant for an Engineering Student Guidance Platform.
    
STRICT RULES:
1. You ONLY respond to engineering academic queries
2. You MUST use ONLY the retrieved academic data provided - DO NOT generate information not in the context
3. If information is not available, respond with: "Information not available in academic database"
4. You MUST NOT discuss politics, sports, entertainment, religion, or any non-academic topics
5. Responses must be formal, structured, and precise
6. DO NOT hallucinate or make up data

RESPONSE FORMAT:
- For concept explanations: Include definition, key points, and exam relevance
- For faculty queries: Include only verified faculty metadata
- For performance queries: Base analysis on actual student data
- For recommendations: Provide logical justification

Current Context:
{context}

Retrieved Academic Data:
{retrieved_data}

Student Data (if available):
{student_data}
"""

    def __init__(self, db: Session, rag_service: RAGService):
        self.db = db
        self.rag_service = rag_service
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.1,  # Low temperature for consistent, factual responses
            api_key=settings.OPENAI_API_KEY
        )
        
    async def generate_response(
        self,
        query: str,
        intent: IntentType,
        context: Dict[str, Any],
        student_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate a response based on intent and retrieved data.
        
        Returns structured JSON response conforming to the schema.
        """
        
        # Handle out-of-scope immediately
        if intent == IntentType.OUT_OF_SCOPE:
            return self._create_out_of_scope_response()
            
        # Retrieve relevant data based on intent
        retrieved_data = await self._retrieve_for_intent(query, intent, context)
        
        # Check if we have sufficient data
        if not retrieved_data or not self._has_sufficient_data(retrieved_data):
            return self._create_insufficient_data_response(intent)
            
        # Generate response based on intent type
        response_generators = {
            IntentType.SYLLABUS_QUERY: self._generate_syllabus_response,
            IntentType.FACULTY_QUERY: self._generate_faculty_response,
            IntentType.PERFORMANCE_QUERY: self._generate_performance_response,
            IntentType.ELECTIVE_QUERY: self._generate_elective_response,
            IntentType.CAREER_QUERY: self._generate_career_response,
            IntentType.STUDY_PLAN_QUERY: self._generate_study_plan_response,
            IntentType.CLARIFICATION: self._generate_clarification_response,
        }
        
        generator = response_generators.get(intent, self._generate_generic_response)
        response = await generator(query, retrieved_data, context, student_data)
        
        return response
        
    async def _retrieve_for_intent(
        self, 
        query: str, 
        intent: IntentType, 
        context: Dict
    ) -> Dict[str, Any]:
        """Retrieve relevant data based on intent"""
        
        retrieved = {
            'sources': [],
            'confidence': 'Low'
        }
        
        if intent == IntentType.SYLLABUS_QUERY:
            results = await self.rag_service.retrieve_syllabus_content(
                query,
                subject_code=context.get('current_subject'),
                unit=context.get('current_unit')
            )
            retrieved['syllabus_data'] = results
            retrieved['sources'] = [r.get('metadata', {}) for r in results]
            
        elif intent == IntentType.FACULTY_QUERY:
            results = await self.rag_service.retrieve_faculty_info(
                query,
                department=context.get('department'),
                subject=context.get('current_subject')
            )
            retrieved['faculty_data'] = results
            retrieved['sources'] = [r.get('metadata', {}) for r in results]
            
        elif intent in [IntentType.ELECTIVE_QUERY, IntentType.CAREER_QUERY]:
            results = await self.rag_service.retrieve_knowledge(
                query,
                category='elective' if intent == IntentType.ELECTIVE_QUERY else 'career'
            )
            retrieved['knowledge_data'] = results
            retrieved['sources'] = [r.get('metadata', {}) for r in results]
            
        # Calculate confidence
        all_results = (
            retrieved.get('syllabus_data', []) + 
            retrieved.get('faculty_data', []) + 
            retrieved.get('knowledge_data', [])
        )
        retrieved['confidence'] = await self.rag_service.get_retrieval_confidence(all_results)
        
        return retrieved
        
    def _has_sufficient_data(self, retrieved_data: Dict) -> bool:
        """Check if retrieved data is sufficient for response"""
        
        total_results = (
            len(retrieved_data.get('syllabus_data', [])) +
            len(retrieved_data.get('faculty_data', [])) +
            len(retrieved_data.get('knowledge_data', []))
        )
        
        return total_results > 0 and retrieved_data.get('confidence') != 'Low'
        
    async def _generate_syllabus_response(
        self,
        query: str,
        retrieved_data: Dict,
        context: Dict,
        student_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate response for syllabus queries"""
        
        syllabus_data = retrieved_data.get('syllabus_data', [])
        
        if not syllabus_data:
            return self._create_insufficient_data_response(IntentType.SYLLABUS_QUERY)
            
        # Prepare context for LLM
        data_context = self._format_syllabus_data(syllabus_data)
        
        # Generate structured response using LLM
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.SYSTEM_PROMPT),
            HumanMessagePromptTemplate.from_template(
                """Based on the retrieved syllabus data, answer this query: {query}
                
Provide response in this JSON format:
{{
    "definition": "Clear definition if applicable",
    "key_points": ["point1", "point2", ...],
    "subtopics": ["subtopic1", "subtopic2", ...],
    "important_notes": "Any important notes",
    "exam_relevance": "Relevance for exams",
    "unit_context": "Which unit this belongs to"
}}

ONLY use information from the retrieved data. Do not add external information."""
            )
        ])
        
        messages = prompt.format_messages(
            context=json.dumps(context),
            retrieved_data=data_context,
            student_data=json.dumps(student_data or {}),
            query=query
        )
        
        try:
            response = await self.llm.ainvoke(messages)
            content = self._parse_llm_response(response.content)
            
            return {
                "type": ResponseType.CONCEPT_EXPLANATION.value,
                "intent": IntentType.SYLLABUS_QUERY.value,
                "content": content,
                "confidence": retrieved_data.get('confidence', 'Medium'),
                "sources": retrieved_data.get('sources', [])
            }
        except Exception as e:
            logger.error(f"Error generating syllabus response: {e}")
            return self._create_error_response()
            
    async def _generate_faculty_response(
        self,
        query: str,
        retrieved_data: Dict,
        context: Dict,
        student_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate response for faculty queries"""
        
        faculty_data = retrieved_data.get('faculty_data', [])
        
        if not faculty_data:
            return self._create_insufficient_data_response(IntentType.FACULTY_QUERY)
            
        # Check if this is a recommendation or info query
        is_recommendation = any(word in query.lower() for word in ['recommend', 'suggest', 'best', 'suitable'])
        
        if is_recommendation:
            return await self._generate_faculty_recommendation(query, faculty_data, context, student_data)
        else:
            return await self._generate_faculty_info(query, faculty_data, context)
            
    async def _generate_faculty_recommendation(
        self,
        query: str,
        faculty_data: List[Dict],
        context: Dict,
        student_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate faculty recommendation"""
        
        # Score faculty based on student needs
        scored_faculty = []
        
        student_weaknesses = student_data.get('weak_subjects', []) if student_data else []
        student_interests = student_data.get('interests', []) if student_data else []
        
        for faculty in faculty_data:
            content = faculty.get('content', {})
            if isinstance(content, str):
                continue
                
            score = 0
            reasons = []
            
            # Match subjects
            subjects_taught = content.get('subjects_taught', [])
            for weakness in student_weaknesses:
                if weakness.lower() in [s.lower() for s in subjects_taught]:
                    score += 2
                    reasons.append(f"Teaches {weakness}")
                    
            # Match interests with research areas
            research_areas = content.get('research_areas', [])
            for interest in student_interests:
                if interest.lower() in [r.lower() for r in research_areas]:
                    score += 1.5
                    reasons.append(f"Research in {interest}")
                    
            # Consider experience and rating
            if content.get('experience_years', 0) > 10:
                score += 0.5
                reasons.append("Highly experienced")
                
            if content.get('rating', 0) >= 4.0:
                score += 0.5
                reasons.append("Highly rated")
                
            scored_faculty.append({
                'faculty': content,
                'score': score,
                'reasons': reasons
            })
            
        # Sort by score
        scored_faculty.sort(key=lambda x: x['score'], reverse=True)
        
        # Take top recommendations
        recommendations = scored_faculty[:3]
        
        return {
            "type": ResponseType.FACULTY_RECOMMENDATION.value,
            "intent": IntentType.FACULTY_QUERY.value,
            "content": {
                "recommendations": [
                    {
                        "name": r['faculty'].get('name'),
                        "department": r['faculty'].get('department'),
                        "subjects": r['faculty'].get('subjects_taught', []),
                        "research_areas": r['faculty'].get('research_areas', []),
                        "teaching_style": r['faculty'].get('teaching_style'),
                        "reasoning": r['reasons'],
                        "match_score": r['score']
                    }
                    for r in recommendations
                ],
                "selection_criteria": "Based on subject expertise, research alignment, and student needs"
            },
            "confidence": retrieved_data.get('confidence', 'Medium')
        }
        
    async def _generate_faculty_info(
        self,
        query: str,
        faculty_data: List[Dict],
        context: Dict
    ) -> Dict[str, Any]:
        """Generate faculty information response"""
        
        # Extract relevant faculty info
        faculty_list = []
        
        for faculty in faculty_data:
            content = faculty.get('content', {})
            if isinstance(content, str):
                # Parse string content
                continue
                
            faculty_list.append({
                "name": content.get('name'),
                "department": content.get('department'),
                "designation": content.get('designation'),
                "subjects_taught": content.get('subjects_taught', []),
                "experience_years": content.get('experience_years'),
                "teaching_style": content.get('teaching_style'),
                "research_areas": content.get('research_areas', []),
                "office_hours": content.get('office_hours'),
                "available_for_mentoring": content.get('available_for_mentoring', True)
            })
            
        return {
            "type": ResponseType.FACULTY_LIST.value,
            "intent": IntentType.FACULTY_QUERY.value,
            "content": {
                "faculty": faculty_list,
                "count": len(faculty_list)
            },
            "confidence": "High" if faculty_list else "Low"
        }
        
    async def _generate_performance_response(
        self,
        query: str,
        retrieved_data: Dict,
        context: Dict,
        student_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate performance analysis response"""
        
        if not student_data:
            return {
                "type": ResponseType.TEXT.value,
                "intent": IntentType.PERFORMANCE_QUERY.value,
                "content": {
                    "message": "Please provide your student ID or login to access performance data."
                },
                "confidence": "High"
            }
            
        # Analyze performance data
        analysis = self._analyze_performance(student_data)
        
        return {
            "type": ResponseType.PERFORMANCE_ANALYSIS.value,
            "intent": IntentType.PERFORMANCE_QUERY.value,
            "content": {
                "overall_performance": {
                    "cgpa": student_data.get('cgpa'),
                    "semester": student_data.get('current_semester'),
                    "credits_completed": student_data.get('credits_completed')
                },
                "subject_analysis": analysis.get('subject_breakdown', []),
                "weak_areas": analysis.get('weak_areas', []),
                "strong_areas": analysis.get('strong_areas', []),
                "improvement_suggestions": analysis.get('suggestions', []),
                "attendance": student_data.get('attendance_percentage')
            },
            "confidence": "High"
        }
        
    def _analyze_performance(self, student_data: Dict) -> Dict[str, Any]:
        """Analyze student performance data"""
        
        subject_grades = student_data.get('subject_grades', {})
        
        weak_areas = []
        strong_areas = []
        subject_breakdown = []
        
        for subject, grade in subject_grades.items():
            grade_value = self._grade_to_value(grade)
            
            subject_breakdown.append({
                "subject": subject,
                "grade": grade,
                "status": "weak" if grade_value < 2.5 else "strong" if grade_value >= 3.5 else "average"
            })
            
            if grade_value < 2.5:
                weak_areas.append(subject)
            elif grade_value >= 3.5:
                strong_areas.append(subject)
                
        suggestions = []
        for weak_subject in weak_areas:
            suggestions.append(f"Focus on improving {weak_subject} - consider additional tutoring or study groups")
            
        return {
            "subject_breakdown": subject_breakdown,
            "weak_areas": weak_areas,
            "strong_areas": strong_areas,
            "suggestions": suggestions
        }
        
    def _grade_to_value(self, grade: str) -> float:
        """Convert letter grade to numeric value"""
        grade_map = {
            'A+': 4.0, 'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0, 'D-': 0.7,
            'F': 0.0
        }
        return grade_map.get(grade.upper(), 2.0)
        
    async def _generate_elective_response(
        self,
        query: str,
        retrieved_data: Dict,
        context: Dict,
        student_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate elective recommendation response"""
        
        knowledge_data = retrieved_data.get('knowledge_data', [])
        
        # Get student interests and career goals
        interests = student_data.get('interests', []) if student_data else []
        career_goal = student_data.get('career_goal', '') if student_data else ''
        
        # Generate recommendations
        recommendations = []
        
        for item in knowledge_data:
            content = item.get('content', '')
            metadata = item.get('metadata', {})
            
            recommendations.append({
                "elective_name": metadata.get('title', 'Unknown'),
                "category": metadata.get('category', 'elective'),
                "relevance": item.get('score', 0.5),
                "description": content[:200] if isinstance(content, str) else ''
            })
            
        return {
            "type": ResponseType.ELECTIVE_RECOMMENDATION.value,
            "intent": IntentType.ELECTIVE_QUERY.value,
            "content": {
                "recommendations": recommendations[:5],
                "based_on": {
                    "interests": interests,
                    "career_goal": career_goal
                },
                "selection_advice": "Choose electives that align with your career goals and strengthen weak areas"
            },
            "confidence": retrieved_data.get('confidence', 'Medium')
        }
        
    async def _generate_career_response(
        self,
        query: str,
        retrieved_data: Dict,
        context: Dict,
        student_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate career guidance response"""
        
        knowledge_data = retrieved_data.get('knowledge_data', [])
        
        # Prepare career information
        career_info = []
        for item in knowledge_data:
            career_info.append({
                "content": item.get('content', ''),
                "metadata": item.get('metadata', {})
            })
            
        # Generate career guidance using LLM
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.SYSTEM_PROMPT),
            HumanMessagePromptTemplate.from_template(
                """Based on the career information, answer: {query}
                
Provide response in JSON format:
{{
    "career_paths": ["path1", "path2"],
    "required_skills": ["skill1", "skill2"],
    "recommended_subjects": ["subject1", "subject2"],
    "industry_insights": "brief insights",
    "next_steps": ["step1", "step2"]
}}

Use ONLY the provided information."""
            )
        ])
        
        try:
            messages = prompt.format_messages(
                context=json.dumps(context),
                retrieved_data=json.dumps(career_info),
                student_data=json.dumps(student_data or {}),
                query=query
            )
            
            response = await self.llm.ainvoke(messages)
            content = self._parse_llm_response(response.content)
            
            return {
                "type": ResponseType.TEXT.value,
                "intent": IntentType.CAREER_QUERY.value,
                "content": content,
                "confidence": retrieved_data.get('confidence', 'Medium')
            }
        except Exception as e:
            logger.error(f"Error generating career response: {e}")
            return self._create_error_response()
            
    async def _generate_study_plan_response(
        self,
        query: str,
        retrieved_data: Dict,
        context: Dict,
        student_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate study plan response"""
        
        # Get student's weak areas
        weak_areas = student_data.get('weak_subjects', []) if student_data else []
        subjects = student_data.get('enrolled_subjects', []) if student_data else []
        
        # Generate study plan
        study_plan = {
            "daily_schedule": [],
            "weekly_goals": [],
            "focus_areas": weak_areas,
            "recommendations": []
        }
        
        # Create basic schedule
        for subject in subjects:
            priority = "high" if subject in weak_areas else "normal"
            study_plan["daily_schedule"].append({
                "subject": subject,
                "priority": priority,
                "suggested_hours": 2 if priority == "high" else 1
            })
            
        study_plan["weekly_goals"] = [
            "Complete all assignments on time",
            "Review weak subjects daily",
            "Practice previous year questions",
            "Attend all classes"
        ]
        
        study_plan["recommendations"] = [
            f"Focus extra time on {area}" for area in weak_areas[:3]
        ]
        
        return {
            "type": ResponseType.STUDY_PLAN.value,
            "intent": IntentType.STUDY_PLAN_QUERY.value,
            "content": study_plan,
            "confidence": "Medium"
        }
        
    async def _generate_clarification_response(
        self,
        query: str,
        retrieved_data: Dict,
        context: Dict,
        student_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate clarification request"""
        
        return {
            "type": ResponseType.TEXT.value,
            "intent": IntentType.CLARIFICATION.value,
            "content": {
                "message": "Could you please provide more details? Specifically:",
                "clarification_questions": [
                    "Which subject are you asking about?",
                    "Which unit or topic specifically?",
                    "What aspect would you like to know more about?"
                ]
            },
            "confidence": "High"
        }
        
    async def _generate_generic_response(
        self,
        query: str,
        retrieved_data: Dict,
        context: Dict,
        student_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate generic response when intent doesn't match specific handlers"""
        
        return {
            "type": ResponseType.TEXT.value,
            "intent": "GENERAL",
            "content": {
                "message": "I can help you with academic queries related to syllabus, faculty, performance analysis, electives, and career guidance. Please specify your question."
            },
            "confidence": "Medium"
        }
        
    def _create_out_of_scope_response(self) -> str:
        """Return out of scope message - NOT JSON"""
        return "Beyond my scope"
        
    def _create_insufficient_data_response(self, intent: IntentType) -> Dict[str, Any]:
        """Create response when data is insufficient"""
        
        return {
            "type": ResponseType.TEXT.value,
            "intent": intent.value,
            "content": {
                "message": "Information not available in academic database."
            },
            "confidence": "Low"
        }
        
    def _create_error_response(self) -> Dict[str, Any]:
        """Create error response"""
        
        return {
            "type": ResponseType.ERROR.value,
            "intent": "ERROR",
            "content": {
                "message": "An error occurred while processing your request. Please try again."
            },
            "confidence": "Low"
        }
        
    def _format_syllabus_data(self, syllabus_data: List[Dict]) -> str:
        """Format syllabus data for LLM context"""
        
        formatted = []
        for item in syllabus_data:
            content = item.get('content', '')
            metadata = item.get('metadata', {})
            
            formatted.append(f"""
Subject: {metadata.get('subject_name', 'Unknown')}
Unit: {metadata.get('unit', 'N/A')}
Content: {content}
---""")
            
        return "\n".join(formatted)
        
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract JSON"""
        
        try:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            return {"message": response}
        except json.JSONDecodeError:
            return {"message": response}