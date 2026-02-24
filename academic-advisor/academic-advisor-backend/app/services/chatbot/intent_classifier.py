# academic-advisor-backend/app/services/chatbot/intent_classifier.py

import re
from typing import Dict, List, Tuple, Optional
from enum import Enum
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    SYLLABUS_QUERY = "SYLLABUS_QUERY"
    FACULTY_QUERY = "FACULTY_QUERY"
    PERFORMANCE_QUERY = "PERFORMANCE_QUERY"
    ELECTIVE_QUERY = "ELECTIVE_QUERY"
    CAREER_QUERY = "CAREER_QUERY"
    STUDY_PLAN_QUERY = "STUDY_PLAN_QUERY"
    CLARIFICATION = "CLARIFICATION"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class IntentClassifier:
    """
    Enterprise-grade intent classifier for academic queries.
    Uses a combination of rule-based patterns and semantic similarity.
    """
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._initialize_patterns()
        self._initialize_embeddings()
        self._initialize_prohibited_patterns()
        
    def _initialize_patterns(self):
        """Initialize regex patterns for rule-based classification"""
        self.intent_patterns = {
            IntentType.SYLLABUS_QUERY: [
                r'\b(syllabus|topic|unit|chapter|concept|explain|what is|define|definition)\b',
                r'\b(subject|course|module|curriculum|content)\b',
                r'\b(learn|study|understand|covers?|includes?)\b.*\b(subject|topic|unit)\b',
                r'\b(deadlock|mutex|semaphore|algorithm|data structure|oop|database)\b',
                r'\b(unit\s*\d+|chapter\s*\d+)\b',
            ],
            IntentType.FACULTY_QUERY: [
                r'\b(faculty|professor|teacher|instructor|mentor|dr\.?|prof\.?)\b',
                r'\b(who teaches|taught by|teaching)\b',
                r'\b(office hours|consultation|available)\b.*\b(faculty|professor)\b',
                r'\b(recommend|suggest)\b.*\b(mentor|faculty|professor)\b',
            ],
            IntentType.PERFORMANCE_QUERY: [
                r'\b(performance|grade|marks|score|cgpa|gpa|result)\b',
                r'\b(weak|strong|improve|better|progress)\b.*\b(subject|performance)\b',
                r'\b(my|student)\b.*\b(analysis|report|standing)\b',
                r'\b(attendance|assessment|exam|test)\b.*\b(performance|result)\b',
            ],
            IntentType.ELECTIVE_QUERY: [
                r'\b(elective|optional|choose|select)\b.*\b(subject|course)\b',
                r'\b(which|what)\b.*\b(elective|subject)\b.*\b(choose|take|select)\b',
                r'\b(recommend|suggest)\b.*\b(elective|course|subject)\b',
                r'\b(open elective|professional elective|pe|oe)\b',
            ],
            IntentType.CAREER_QUERY: [
                r'\b(career|job|placement|industry|company|work)\b',
                r'\b(skill|roadmap|path|future|opportunity)\b',
                r'\b(software|developer|engineer|analyst|scientist)\b.*\b(become|career)\b',
                r'\b(internship|resume|interview|hire)\b',
            ],
            IntentType.STUDY_PLAN_QUERY: [
                r'\b(study plan|schedule|timetable|prepare|preparation)\b',
                r'\b(how to|best way)\b.*\b(study|prepare|learn)\b',
                r'\b(exam|semester|final)\b.*\b(preparation|plan|strategy)\b',
                r'\b(improve|better)\b.*\b(study|learning|grades)\b',
            ],
        }
        
    def _initialize_embeddings(self):
        """Initialize semantic embeddings for intent examples"""
        self.intent_examples = {
            IntentType.SYLLABUS_QUERY: [
                "Explain the concept of deadlock in operating systems",
                "What topics are covered in unit 3 of DBMS?",
                "Define normalization in database",
                "What is the syllabus for data structures?",
                "Explain OOP concepts",
                "What are the topics in computer networks unit 2?",
                "Describe the working of semaphores",
                "What is machine learning covered in AI subject?",
            ],
            IntentType.FACULTY_QUERY: [
                "Who teaches operating systems?",
                "Tell me about Dr. Smith's research areas",
                "Which faculty is best for mentoring in machine learning?",
                "What are the office hours for Prof. Johnson?",
                "Recommend a faculty mentor for database projects",
                "Who is the instructor for compiler design?",
            ],
            IntentType.PERFORMANCE_QUERY: [
                "What is my current CGPA?",
                "Show my performance analysis",
                "Which subjects am I weak in?",
                "How can I improve my grades?",
                "What is my attendance percentage?",
                "Analyze my academic performance",
            ],
            IntentType.ELECTIVE_QUERY: [
                "Which electives should I choose?",
                "Recommend electives for machine learning career",
                "What are the available professional electives?",
                "Should I take cloud computing or cybersecurity?",
                "Best electives for software development",
            ],
            IntentType.CAREER_QUERY: [
                "What career options are available after CSE?",
                "How to become a data scientist?",
                "What skills are needed for software engineering?",
                "Career roadmap for machine learning",
                "What companies hire from our college?",
            ],
            IntentType.STUDY_PLAN_QUERY: [
                "How should I prepare for semester exams?",
                "Create a study plan for DBMS",
                "Best strategy to improve my grades",
                "How to manage time for multiple subjects?",
                "Study schedule for final exams",
            ],
        }
        
        # Pre-compute embeddings
        self.intent_embeddings = {}
        for intent, examples in self.intent_examples.items():
            self.intent_embeddings[intent] = self.model.encode(examples)
            
    def _initialize_prohibited_patterns(self):
        """Initialize patterns for out-of-scope detection"""
        self.prohibited_patterns = [
            # Politics
            r'\b(politic|election|vote|government|minister|parliament|democrat|republican)\b',
            # Sports
            r'\b(cricket|football|soccer|basketball|tennis|ipl|fifa|olympic|match|score|team|player)\b',
            # Entertainment
            r'\b(movie|film|actor|actress|bollywood|hollywood|netflix|song|music|singer|celebrity)\b',
            # Religion
            r'\b(religion|god|church|temple|mosque|prayer|spiritual|divine)\b',
            # General trivia
            r'\b(weather|recipe|cook|travel|vacation|hotel|restaurant)\b',
            # Personal advice
            r'\b(relationship|dating|love|marriage|personal|family problem)\b',
            # Current events
            r'\b(news|latest|breaking|headline|today\'s|current affair)\b',
            # Gaming
            r'\b(game|gaming|pubg|fortnite|minecraft|xbox|playstation)\b',
        ]
        
    def classify(self, query: str, context: Optional[Dict] = None) -> Tuple[IntentType, float]:
        """
        Classify the intent of a user query.
        
        Args:
            query: The user's input query
            context: Optional conversation context
            
        Returns:
            Tuple of (IntentType, confidence_score)
        """
        # Normalize query
        query_lower = query.lower().strip()
        
        # Step 1: Check for prohibited/out-of-scope content
        if self._is_out_of_scope(query_lower):
            return IntentType.OUT_OF_SCOPE, 1.0
            
        # Step 2: Rule-based pattern matching
        rule_based_result = self._rule_based_classification(query_lower)
        if rule_based_result[1] > 0.8:
            return rule_based_result
            
        # Step 3: Semantic similarity classification
        semantic_result = self._semantic_classification(query)
        
        # Step 4: Context-aware adjustment
        if context:
            semantic_result = self._apply_context(semantic_result, context)
            
        # Step 5: Determine final classification
        if semantic_result[1] < 0.4:
            # Low confidence - might be out of scope or need clarification
            if self._is_ambiguous(query_lower):
                return IntentType.CLARIFICATION, 0.6
            return IntentType.OUT_OF_SCOPE, 0.5
            
        return semantic_result
        
    def _is_out_of_scope(self, query: str) -> bool:
        """Check if query matches prohibited patterns"""
        for pattern in self.prohibited_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
        
    def _rule_based_classification(self, query: str) -> Tuple[IntentType, float]:
        """Classify using regex patterns"""
        scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            match_count = 0
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    match_count += 1
            scores[intent] = match_count / len(patterns)
            
        if not scores:
            return IntentType.OUT_OF_SCOPE, 0.0
            
        best_intent = max(scores, key=scores.get)
        return best_intent, scores[best_intent]
        
    def _semantic_classification(self, query: str) -> Tuple[IntentType, float]:
        """Classify using semantic similarity"""
        query_embedding = self.model.encode([query])
        
        best_intent = None
        best_score = 0.0
        
        for intent, embeddings in self.intent_embeddings.items():
            similarities = cosine_similarity(query_embedding, embeddings)[0]
            max_similarity = float(np.max(similarities))
            
            if max_similarity > best_score:
                best_score = max_similarity
                best_intent = intent
                
        return best_intent or IntentType.OUT_OF_SCOPE, best_score
        
    def _apply_context(self, result: Tuple[IntentType, float], context: Dict) -> Tuple[IntentType, float]:
        """Adjust classification based on conversation context"""
        intent, confidence = result
        
        # If the query seems like a follow-up, inherit context intent
        last_intent = context.get('last_intent')
        if last_intent and confidence < 0.6:
            # Check for follow-up indicators
            follow_up_patterns = [
                r'^(and|also|what about|how about|tell me more|explain more|continue)',
                r'^(it|this|that|these|those)\b',
                r'^(yes|no|okay|sure|please)\b',
            ]
            
            query_lower = context.get('current_query', '').lower()
            for pattern in follow_up_patterns:
                if re.match(pattern, query_lower):
                    return IntentType(last_intent), confidence + 0.2
                    
        return result
        
    def _is_ambiguous(self, query: str) -> bool:
        """Check if query is too ambiguous to classify"""
        # Very short queries
        if len(query.split()) < 2:
            return True
        # Only stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'what', 'how', 'why', 'when', 'where'}
        words = set(query.split())
        if words.issubset(stop_words):
            return True
        return False
        
    def get_sub_intent(self, query: str, main_intent: IntentType) -> Optional[str]:
        """Get more specific sub-intent within main category"""
        query_lower = query.lower()
        
        sub_intents = {
            IntentType.SYLLABUS_QUERY: {
                'definition': r'\b(what is|define|definition|meaning)\b',
                'explanation': r'\b(explain|describe|how does|working)\b',
                'topics': r'\b(topics|covers|includes|syllabus)\b',
                'comparison': r'\b(difference|compare|versus|vs)\b',
            },
            IntentType.FACULTY_QUERY: {
                'info': r'\b(who|tell me about|information)\b',
                'recommendation': r'\b(recommend|suggest|best|suitable)\b',
                'contact': r'\b(contact|office|hours|email|reach)\b',
            },
            IntentType.PERFORMANCE_QUERY: {
                'analysis': r'\b(analyze|analysis|report|overview)\b',
                'weakness': r'\b(weak|improve|problem|struggle)\b',
                'comparison': r'\b(compare|ranking|standing)\b',
            },
        }
        
        if main_intent in sub_intents:
            for sub_intent, pattern in sub_intents[main_intent].items():
                if re.search(pattern, query_lower):
                    return sub_intent
                    
        return None