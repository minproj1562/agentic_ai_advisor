# app/services/chatbot/intent_classifier.py
"""
Intent classifier with lazy model loading for fast startup
"""

import re
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Global lazy-loaded model
_sentence_model = None
_model_load_attempted = False


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


class IntentClassifier:
    """
    Intent classifier using rule-based patterns with optional semantic similarity.
    Uses lazy loading to prevent slow startup.
    """

    def __init__(self):
        """Initialize patterns only - model is loaded lazily."""
        self._initialize_patterns()
        self._initialize_prohibited_patterns()
        self._embeddings_computed = False
        self.intent_embeddings = {}
        logger.debug("IntentClassifier initialized (lightweight)")

    def _get_model(self):
        """Lazy load the SentenceTransformer model."""
        global _sentence_model, _model_load_attempted
        
        if _model_load_attempted:
            return _sentence_model
        
        _model_load_attempted = True
        
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading SentenceTransformer model...")
            _sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ SentenceTransformer model loaded successfully")
            return _sentence_model
        except ImportError:
            logger.warning("⚠️ sentence-transformers not installed - using rule-based only")
            return None
        except Exception as e:
            logger.warning(f"⚠️ Failed to load SentenceTransformer: {e}")
            return None

    def _compute_embeddings_if_needed(self):
        """Compute embeddings lazily when first needed."""
        if self._embeddings_computed:
            return
        
        model = self._get_model()
        if not model:
            self._embeddings_computed = True
            return
        
        try:
            intent_examples = {
                IntentType.SYLLABUS_QUERY: [
                    "Explain the concept of deadlock in operating systems",
                    "What topics are covered in unit 3 of DBMS?",
                    "Define normalization in database",
                    "What is the syllabus for data structures?",
                    "Explain OOP concepts",
                ],
                IntentType.FACULTY_QUERY: [
                    "Who teaches operating systems?",
                    "Tell me about Dr. Smith's research areas",
                    "Which faculty is best for mentoring in machine learning?",
                    "Recommend a faculty mentor for database projects",
                ],
                IntentType.PERFORMANCE_QUERY: [
                    "What is my current CGPA?",
                    "Show my performance analysis",
                    "Which subjects am I weak in?",
                    "Analyze my academic performance",
                ],
                IntentType.ELECTIVE_QUERY: [
                    "Which electives should I choose?",
                    "Recommend electives for machine learning career",
                    "Best electives for software development",
                ],
                IntentType.CAREER_QUERY: [
                    "What career options are available after CSE?",
                    "How to become a data scientist?",
                    "What skills are needed for software engineering?",
                    "Career roadmap for machine learning",
                ],
                IntentType.STUDY_PLAN_QUERY: [
                    "How should I prepare for semester exams?",
                    "Create a study plan for DBMS",
                    "Best strategy to improve my grades",
                ],
            }
            
            for intent, examples in intent_examples.items():
                self.intent_embeddings[intent] = model.encode(examples)
            
            self._embeddings_computed = True
            logger.info("✅ Intent embeddings computed")
        except Exception as e:
            logger.warning(f"Failed to compute embeddings: {e}")
            self._embeddings_computed = True

    def _initialize_patterns(self):
        """Initialize regex patterns for rule-based classification."""
        self.intent_patterns = {
            IntentType.SYLLABUS_QUERY: [
                r'\b(syllabus|topic|unit|chapter|concept|explain|what is|define|definition)\b',
                r'\b(subject|course|module|curriculum|content)\b',
                r'\b(learn|study|understand|covers?|includes?)\b.*\b(subject|topic|unit)\b',
                r'\b(deadlock|mutex|semaphore|algorithm|data structure|oop|database|normalization|sql)\b',
                r'\b(unit\s*\d+|chapter\s*\d+)\b',
                r'\b(operating system|os|dbms|dsa|computer network|machine learning|artificial intelligence)\b',
            ],
            IntentType.FACULTY_QUERY: [
                r'\b(faculty|professor|teacher|instructor|mentor|dr\.?|prof\.?)\b',
                r'\b(who teaches|taught by|teaching)\b',
                r'\b(office hours|consultation|available)\b.*\b(faculty|professor)\b',
                r'\b(recommend|suggest)\b.*\b(mentor|faculty|professor)\b',
                r'\b(list|show|all)\b.*\b(faculty|professor|teacher)\b',
            ],
            IntentType.PERFORMANCE_QUERY: [
                r'\b(performance|grade|marks|score|cgpa|gpa|sgpa|result)\b',
                r'\b(weak|strong|improve|better|progress)\b.*\b(subject|performance)\b',
                r'\b(my|student)\b.*\b(analysis|report|standing)\b',
                r'\b(attendance|assessment|exam|test)\b.*\b(performance|result)\b',
                r'\b(how am i doing|my grades|my marks)\b',
            ],
            IntentType.ELECTIVE_QUERY: [
                r'\b(elective|optional|choose|select)\b.*\b(subject|course)\b',
                r'\b(which|what)\b.*\b(elective|subject)\b.*\b(choose|take|select)\b',
                r'\b(recommend|suggest)\b.*\b(elective|course|subject)\b',
                r'\b(open elective|professional elective|pe|oe)\b',
            ],
            IntentType.CAREER_QUERY: [
                r'\b(career|job|placement|industry|company|work|profession)\b',
                r'\b(skill|roadmap|path|future|opportunity)\b',
                r'\b(software|developer|engineer|analyst|scientist)\b.*\b(become|career|how to)\b',
                r'\b(internship|resume|interview|hire|salary)\b',
                r'\b(data scientist|ml engineer|devops|cloud|cybersecurity|web developer)\b',
                r'\b(how to become|want to be|career in)\b',
            ],
            IntentType.STUDY_PLAN_QUERY: [
                r'\b(study plan|schedule|timetable|prepare|preparation)\b',
                r'\b(how to|best way)\b.*\b(study|prepare|learn)\b',
                r'\b(exam|semester|final)\b.*\b(preparation|plan|strategy)\b',
                r'\b(improve|better)\b.*\b(study|learning|grades)\b',
            ],
        }

    def _initialize_prohibited_patterns(self):
        """Initialize patterns for out-of-scope detection."""
        self.prohibited_patterns = [
            r'\b(politic|election|vote|government|minister|parliament|democrat|republican)\b',
            r'\b(cricket|football|soccer|basketball|tennis|ipl|fifa|olympic|match|player)\b',
            r'\b(movie|film|actor|actress|bollywood|hollywood|netflix|song|music|singer|celebrity)\b',
            r'\b(religion|god|church|temple|mosque|prayer|spiritual|divine)\b',
            r'\b(weather|recipe|cook|travel|vacation|hotel|restaurant)\b',
            r'\b(relationship|dating|love|marriage|personal|family problem)\b',
            r'\b(game|gaming|pubg|fortnite|minecraft|xbox|playstation)\b',
            r'\b(news|latest|breaking|headline|current affair)\b',
        ]

    def classify(self, query: str, context: Optional[Dict] = None) -> Tuple[IntentType, float]:
        """
        Classify the intent of a user query.
        Uses rule-based first (fast), then semantic if needed (slower).
        """
        query_lower = query.lower().strip()

        # Step 1: Check for out-of-scope
        if self._is_out_of_scope(query_lower):
            return IntentType.OUT_OF_SCOPE, 0.95

        # Step 2: Rule-based pattern matching (fast)
        rule_result = self._rule_based_classification(query_lower)
        if rule_result[1] >= 0.5:
            logger.debug(f"Rule-based classification: {rule_result[0].value} ({rule_result[1]:.2f})")
            return rule_result

        # Step 3: Context-based adjustment
        if context:
            context_result = self._apply_context(rule_result, context, query_lower)
            if context_result[1] >= 0.5:
                return context_result

        # Step 4: Semantic classification (slower, only if rule-based is uncertain)
        if rule_result[1] < 0.4:
            semantic_result = self._semantic_classification(query)
            if semantic_result[1] > rule_result[1]:
                return semantic_result

        # Step 5: Ambiguity check
        if rule_result[1] < 0.3:
            if self._is_ambiguous(query_lower):
                return IntentType.CLARIFICATION, 0.6
            return IntentType.GENERAL, 0.5

        return rule_result

    def _is_out_of_scope(self, query: str) -> bool:
        """Check if query matches prohibited patterns."""
        for pattern in self.prohibited_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False

    def _rule_based_classification(self, query: str) -> Tuple[IntentType, float]:
        """Classify using regex patterns."""
        scores = {}

        for intent, patterns in self.intent_patterns.items():
            match_count = 0
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    match_count += 1
            if match_count > 0:
                # Score based on match ratio plus a base boost
                scores[intent] = min((match_count / len(patterns)) + 0.3, 0.95)

        if not scores:
            return IntentType.GENERAL, 0.3

        best_intent = max(scores, key=scores.get)
        return best_intent, scores[best_intent]

    def _semantic_classification(self, query: str) -> Tuple[IntentType, float]:
        """Classify using semantic similarity (lazy loaded)."""
        model = self._get_model()
        if not model:
            return IntentType.GENERAL, 0.4

        self._compute_embeddings_if_needed()
        
        if not self.intent_embeddings:
            return IntentType.GENERAL, 0.4

        try:
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity

            query_embedding = model.encode([query])

            best_intent = IntentType.GENERAL
            best_score = 0.0

            for intent, embeddings in self.intent_embeddings.items():
                similarities = cosine_similarity(query_embedding, embeddings)[0]
                max_similarity = float(np.max(similarities))

                if max_similarity > best_score:
                    best_score = max_similarity
                    best_intent = intent

            return best_intent, best_score

        except Exception as e:
            logger.warning(f"Semantic classification failed: {e}")
            return IntentType.GENERAL, 0.4

    def _apply_context(
        self,
        result: Tuple[IntentType, float],
        context: Dict,
        query: str
    ) -> Tuple[IntentType, float]:
        """Adjust classification based on conversation context."""
        intent, confidence = result

        last_intent = context.get('last_intent')
        if not last_intent:
            return result

        # Follow-up patterns
        follow_up_patterns = [
            r'^(and|also|what about|how about|tell me more|explain more)',
            r'^(it|this|that|these|those)\b',
            r'^(yes|no|okay|sure|please|more|continue)\b',
        ]

        for pattern in follow_up_patterns:
            if re.match(pattern, query):
                try:
                    inherited = IntentType(last_intent) if isinstance(last_intent, str) else last_intent
                    return inherited, min(confidence + 0.25, 0.85)
                except (ValueError, KeyError):
                    pass

        return result

    def _is_ambiguous(self, query: str) -> bool:
        """Check if query is too ambiguous to classify."""
        words = query.split()
        if len(words) < 2:
            return True
        
        stop_words = {'the', 'a', 'an', 'is', 'are', 'what', 'how', 'why', 'when', 'where', 'i', 'me', 'my'}
        meaningful_words = [w for w in words if w.lower() not in stop_words]
        
        return len(meaningful_words) < 1

    def get_sub_intent(self, query: str, main_intent: IntentType) -> Optional[str]:
        """Get more specific sub-intent."""
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
                'list': r'\b(list|all|show)\b',
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