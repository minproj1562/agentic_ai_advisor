# academic-advisor-backend/app/services/chatbot/chatbot_service.py

from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import uuid
import logging
import json

from sqlalchemy.orm import Session

from app.services.chatbot.intent_classifier import IntentClassifier, IntentType
from app.services.chatbot.context_manager import ContextManager
from app.services.chatbot.response_generator import ResponseGenerator
from app.services.chatbot.rag_service import RAGService
from app.models.chatbot import ConversationSession, ChatMessage, ConfidenceLevel

logger = logging.getLogger(__name__)


class ChatbotService:
    """
    Main chatbot service that orchestrates all components.
    Handles the complete chat flow from input to response.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.intent_classifier = IntentClassifier()
        self.context_manager = ContextManager(db)
        self.rag_service = RAGService(db)
        self.response_generator = ResponseGenerator(db, self.rag_service)
        
    async def process_message(
        self,
        user_id: str,
        user_type: str,
        message: str,
        session_token: Optional[str] = None,
        student_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and generate appropriate response.
        
        Args:
            user_id: The user's ID
            user_type: 'student' or 'faculty'
            message: The user's message
            session_token: Optional session token for continuity
            student_data: Optional student performance data
            
        Returns:
            Structured response dict or out-of-scope message
        """
        
        start_time = time.time()
        
        try:
            # Step 1: Get or create session
            session = await self.context_manager.get_or_create_session(
                user_id, 
                user_type, 
                session_token
            )
            
            # Step 2: Store user message
            await self.context_manager.add_message(
                session_id=session.id,
                role="user",
                content=message
            )
            
            # Step 3: Resolve any references in the message
            context_summary = await self.context_manager.get_context_summary(session.id)
            resolved_message = await self.context_manager.resolve_references(
                message, 
                session.id
            )
            
            # Step 4: Classify intent
            intent, confidence = self.intent_classifier.classify(
                resolved_message, 
                context_summary
            )
            
            logger.info(f"Classified intent: {intent}, confidence: {confidence}")
            
            # Step 5: Handle out-of-scope queries
            if intent == IntentType.OUT_OF_SCOPE:
                # Store the response and return plain text
                await self.context_manager.add_message(
                    session_id=session.id,
                    role="assistant",
                    content="Beyond my scope",
                    intent=intent,
                    confidence=ConfidenceLevel.HIGH
                )
                return "Beyond my scope"
                
            # Step 6: Enrich context with student data if available
            if student_data:
                await self.context_manager.enrich_with_student_data(
                    session.id, 
                    student_data
                )
                
            # Step 7: Generate response
            response = await self.response_generator.generate_response(
                query=resolved_message,
                intent=intent,
                context=context_summary,
                student_data=student_data
            )
            
            # Handle string responses (out of scope, errors)
            if isinstance(response, str):
                await self.context_manager.add_message(
                    session_id=session.id,
                    role="assistant",
                    content=response,
                    intent=intent
                )
                return response
                
            # Step 8: Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Step 9: Store assistant response
            response_content = json.dumps(response.get('content', {}))
            
            await self.context_manager.add_message(
                session_id=session.id,
                role="assistant",
                content=response_content,
                intent=intent,
                response_type=response.get('type'),
                confidence=self._map_confidence(response.get('confidence', 'Medium')),
                structured_response=response,
                retrieved_sources=response.get('sources', []),
                processing_time_ms=processing_time
            )
            
            # Step 10: Add session info to response
            response['session_token'] = session.session_token
            response['processing_time_ms'] = processing_time
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "type": "error",
                "intent": "ERROR",
                "content": {
                    "message": "An error occurred while processing your request."
                },
                "confidence": "Low"
            }
            
    async def get_conversation_history(
        self,
        user_id: str,
        session_token: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a user"""
        
        if session_token:
            session = await self.context_manager.get_or_create_session(
                user_id, 
                'student',  # Default type
                session_token
            )
        else:
            # Get most recent session
            session = self.db.query(ConversationSession).filter(
                ConversationSession.user_id == user_id,
                ConversationSession.is_active == True
            ).order_by(
                ConversationSession.updated_at.desc()
            ).first()
            
        if not session:
            return []
            
        messages = await self.context_manager.get_conversation_history(
            session.id, 
            limit
        )
        
        return [
            {
                'id': str(msg.id),
                'role': msg.role,
                'content': msg.content if msg.role == 'user' else msg.structured_response or msg.content,
                'timestamp': msg.created_at.isoformat(),
                'intent': msg.intent.value if msg.intent else None
            }
            for msg in messages
        ]
        
    async def clear_session(self, user_id: str, session_token: str):
        """Clear a conversation session"""
        
        session = self.db.query(ConversationSession).filter(
            ConversationSession.user_id == user_id,
            ConversationSession.session_token == session_token
        ).first()
        
        if session:
            await self.context_manager.clear_session(session.id)
            
    def _map_confidence(self, confidence: str) -> ConfidenceLevel:
        """Map string confidence to enum"""
        
        mapping = {
            'High': ConfidenceLevel.HIGH,
            'Medium': ConfidenceLevel.MEDIUM,
            'Low': ConfidenceLevel.LOW
        }
        return mapping.get(confidence, ConfidenceLevel.MEDIUM)
        
    async def get_suggestions(
        self,
        user_id: str,
        session_token: Optional[str] = None
    ) -> List[str]:
        """Get suggested queries based on context"""
        
        if not session_token:
            # Return default suggestions
            return [
                "What topics are covered in Operating Systems?",
                "Recommend a faculty mentor for my project",
                "Show my academic performance analysis",
                "Which electives should I choose?",
                "Create a study plan for my semester"
            ]
            
        session = await self.context_manager.get_or_create_session(
            user_id, 
            'student', 
            session_token
        )
        
        context = await self.context_manager.get_context_summary(session.id)
        
        suggestions = []
        
        if context.get('current_subject'):
            subject = context['current_subject']
            suggestions.extend([
                f"What topics are covered in {subject}?",
                f"Who teaches {subject}?",
                f"Important topics for {subject} exam"
            ])
        else:
            suggestions.extend([
                "Explain a concept from my syllabus",
                "Show my performance analysis",
                "Recommend electives for my career goals"
            ])
            
        return suggestions[:5]