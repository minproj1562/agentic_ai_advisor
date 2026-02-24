# academic-advisor-backend/app/services/chatbot/context_manager.py

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import deque
import uuid
import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.chatbot import (
    ConversationSession, 
    ChatMessage, 
    ConversationContext,
    IntentType
)

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages conversation context for maintaining session continuity,
    resolving references, and providing context-aware responses.
    """
    
    MAX_CONTEXT_MESSAGES = 10
    SESSION_TIMEOUT_HOURS = 24
    CONTEXT_STACK_SIZE = 5
    
    def __init__(self, db: Session):
        self.db = db
        
    async def get_or_create_session(
        self, 
        user_id: str, 
        user_type: str,
        session_token: Optional[str] = None
    ) -> ConversationSession:
        """Get existing session or create new one"""
        
        if session_token:
            session = self.db.query(ConversationSession).filter(
                and_(
                    ConversationSession.session_token == session_token,
                    ConversationSession.is_active == True,
                    ConversationSession.expires_at > datetime.utcnow()
                )
            ).first()
            
            if session:
                session.updated_at = datetime.utcnow()
                self.db.commit()
                return session
                
        # Create new session
        session = ConversationSession(
            user_id=user_id,
            user_type=user_type,
            session_token=str(uuid.uuid4()),
            expires_at=datetime.utcnow() + timedelta(hours=self.SESSION_TIMEOUT_HOURS),
            metadata={"created_from": "chatbot"}
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        # Initialize context
        context = ConversationContext(
            session_id=session.id,
            discussed_topics=[],
            context_stack=[],
            student_context={}
        )
        self.db.add(context)
        self.db.commit()
        
        return session
        
    async def add_message(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        intent: Optional[IntentType] = None,
        response_type: Optional[str] = None,
        confidence: Optional[str] = None,
        structured_response: Optional[Dict] = None,
        retrieved_sources: Optional[List] = None,
        processing_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None
    ) -> ChatMessage:
        """Add a message to the conversation"""
        
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            intent=intent,
            response_type=response_type,
            confidence=confidence,
            structured_response=structured_response,
            retrieved_sources=retrieved_sources or [],
            processing_time_ms=processing_time_ms,
            tokens_used=tokens_used
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        # Update context
        await self._update_context(session_id, message)
        
        return message
        
    async def get_conversation_history(
        self,
        session_id: uuid.UUID,
        limit: int = None
    ) -> List[ChatMessage]:
        """Get recent conversation history"""
        
        limit = limit or self.MAX_CONTEXT_MESSAGES
        
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(
            ChatMessage.created_at.desc()
        ).limit(limit).all()
        
        return list(reversed(messages))
        
    async def get_context(self, session_id: uuid.UUID) -> Optional[ConversationContext]:
        """Get current conversation context"""
        
        return self.db.query(ConversationContext).filter(
            ConversationContext.session_id == session_id
        ).first()
        
    async def _update_context(self, session_id: uuid.UUID, message: ChatMessage):
        """Update conversation context based on new message"""
        
        context = await self.get_context(session_id)
        if not context:
            return
            
        # Update based on message role and content
        if message.role == "user":
            # Extract entities and update context
            entities = self._extract_entities(message.content)
            
            if entities.get('subject'):
                context.current_subject = entities['subject']
            if entities.get('topic'):
                context.current_topic = entities['topic']
            if entities.get('unit'):
                context.current_unit = entities['unit']
            if entities.get('faculty'):
                if context.referenced_faculty is None:
                    context.referenced_faculty = []
                context.referenced_faculty.append(entities['faculty'])
                
            # Update context stack for reference resolution
            context_entry = {
                'message_id': str(message.id),
                'content': message.content,
                'entities': entities,
                'timestamp': message.created_at.isoformat()
            }
            
            stack = context.context_stack or []
            stack.append(context_entry)
            if len(stack) > self.CONTEXT_STACK_SIZE:
                stack = stack[-self.CONTEXT_STACK_SIZE:]
            context.context_stack = stack
            
        elif message.role == "assistant":
            # Track discussed topics
            if message.intent:
                context.last_intent = message.intent
                
            if context.current_topic:
                discussed = context.discussed_topics or []
                if context.current_topic not in discussed:
                    discussed.append(context.current_topic)
                    context.discussed_topics = discussed
                    
        context.updated_at = datetime.utcnow()
        self.db.commit()
        
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract academic entities from text"""
        import re
        
        entities = {}
        text_lower = text.lower()
        
        # Subject patterns
        subject_patterns = {
            'operating systems': ['operating system', 'os', 'operating systems'],
            'database management': ['dbms', 'database', 'database management'],
            'data structures': ['data structure', 'dsa', 'data structures'],
            'computer networks': ['computer network', 'cn', 'networking'],
            'machine learning': ['machine learning', 'ml'],
            'artificial intelligence': ['artificial intelligence', 'ai'],
            'compiler design': ['compiler', 'compiler design'],
            'software engineering': ['software engineering', 'se'],
            'web technology': ['web technology', 'web tech', 'web development'],
            'cloud computing': ['cloud computing', 'cloud'],
        }
        
        for subject, patterns in subject_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    entities['subject'] = subject
                    break
                    
        # Unit extraction
        unit_match = re.search(r'unit\s*(\d+)', text_lower)
        if unit_match:
            entities['unit'] = int(unit_match.group(1))
            
        # Topic extraction (simplified)
        topic_keywords = [
            'deadlock', 'mutex', 'semaphore', 'normalization', 'sql',
            'sorting', 'searching', 'tree', 'graph', 'linked list',
            'tcp', 'udp', 'http', 'dns', 'routing',
            'regression', 'classification', 'clustering', 'neural network',
        ]
        
        for keyword in topic_keywords:
            if keyword in text_lower:
                entities['topic'] = keyword
                break
                
        # Faculty name extraction (would need actual faculty list)
        faculty_pattern = r'\b(dr\.?|prof\.?|professor)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)'
        faculty_match = re.search(faculty_pattern, text, re.IGNORECASE)
        if faculty_match:
            entities['faculty'] = faculty_match.group(2).strip()
            
        return entities
        
    async def resolve_references(self, query: str, session_id: uuid.UUID) -> str:
        """Resolve pronouns and references in query using context"""
        
        context = await self.get_context(session_id)
        if not context:
            return query
            
        resolved_query = query
        
        # Reference patterns
        reference_patterns = {
            r'\bit\b': 'topic',
            r'\bthis\b': 'topic',
            r'\bthat\b': 'topic',
            r'\bthe subject\b': 'subject',
            r'\bthis subject\b': 'subject',
            r'\bhe\b': 'faculty',
            r'\bshe\b': 'faculty',
            r'\bthey\b': 'faculty',
            r'\bthem\b': 'faculty',
        }
        
        import re
        for pattern, ref_type in reference_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                replacement = None
                
                if ref_type == 'topic' and context.current_topic:
                    replacement = context.current_topic
                elif ref_type == 'subject' and context.current_subject:
                    replacement = context.current_subject
                elif ref_type == 'faculty' and context.referenced_faculty:
                    replacement = context.referenced_faculty[-1]
                    
                if replacement:
                    resolved_query = re.sub(pattern, replacement, resolved_query, flags=re.IGNORECASE)
                    
        return resolved_query
        
    async def get_context_summary(self, session_id: uuid.UUID) -> Dict[str, Any]:
        """Get a summary of current conversation context"""
        
        context = await self.get_context(session_id)
        if not context:
            return {}
            
        return {
            'current_subject': context.current_subject,
            'current_topic': context.current_topic,
            'current_unit': context.current_unit,
            'discussed_topics': context.discussed_topics,
            'last_intent': context.last_intent.value if context.last_intent else None,
            'referenced_faculty': context.referenced_faculty,
        }
        
    async def enrich_with_student_data(
        self, 
        session_id: uuid.UUID, 
        student_data: Dict[str, Any]
    ):
        """Add student performance data to context"""
        
        context = await self.get_context(session_id)
        if context:
            context.student_context = student_data
            self.db.commit()
            
    async def clear_session(self, session_id: uuid.UUID):
        """Clear a conversation session"""
        
        session = self.db.query(ConversationSession).filter(
            ConversationSession.id == session_id
        ).first()
        
        if session:
            session.is_active = False
            self.db.commit()