# app/services/chatbot/intent_classifier.py
"""
Improved Intent Classifier with:
- Shortform handling (os, ml, ai, etc.)
- Incomplete sentence understanding
- Fuzzy matching for typos
- Better context awareness
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
    GREETING = "GREETING"
    MENTOR_QUERY = "MENTOR_QUERY"
    RESOURCE_QUERY = "RESOURCE_QUERY"


# ══════════════════════════════════════════════════════════
# MODULE-LEVEL CONSTANTS (not inside class)
# ══════════════════════════════════════════════════════════

ALL_KNOWN_SUBJECTS = [
    "os", "dbms", "cn", "dsa", "ml", "ai", "dl", "se", "coa", "toc",
    "daa", "oop", "dm", "cns", "cc", "iot", "cg", "mp", "dld",
    "operating systems", "database management systems",
    "computer networks", "data structures", "machine learning",
    "artificial intelligence", "deep learning", "software engineering",
    "computer organization", "theory of computation",
    "design & analysis of algorithm", "object oriented programming",
    "discrete mathematics", "cryptography & network security",
    "cloud computing", "internet of things", "computer graphics",
    "microprocessor", "digital logic & design",
    "python programming", "java programming", "c programming",
    "engineering mathematics-iii", "engineering mathematics-iv",
    "web technology", "blockchain technology",
    "natural language processing", "big data analytics",
    "research methodology", "embedded systems",
    "microcontroller and embedded systems", "wireless technology",
    "full stack development", "mini project",
        # Open Electives (Sem VII)
    "reliability engineering", "operation research", "operations research",
    "cyber security and laws", "digital business management",
    "energy audit and management", "energy audit",
    "fmea", "fault tree", "weibull", "linear programming", "simplex",
    "queuing theory", "game theory", "seo", "digital marketing",
    "energy conservation", "hvac", "power factor",
]

SUBJECT_QUERY_PATTERNS = [
    (r'(?:explain|define|what is|describe|teach me about?)\s+(.+)', lambda m: m.group(1)),
    (r'(?:who teaches|faculty for|professor of)\s+(.+)', lambda m: m.group(1)),
    (r'(?:syllabus|topics|units?)\s+(?:of|for|in)\s+(.+)', lambda m: m.group(1)),
    (r'(?:how to study|resources? for|notes? for)\s+(.+)', lambda m: m.group(1)),
    (r'(?:important topics? in|previous (?:year )?papers?)\s+(.+)', lambda m: m.group(1)),
        (r'(?:what|which)\s+(?:open\s+)?elective', lambda m: "open elective"),
    (r'(?:tell me about|explain)\s+(reliability engineering|operation research|cyber security|digital business|energy audit)', lambda m: m.group(1)),
]


class IntentClassifier:
    """
    Enhanced intent classifier with:
    - Rule-based patterns (fast)
    - Shortform expansion
    - Fuzzy matching
    - Optional semantic similarity (lazy loaded)
    """

    # ══════════════════════════════════════════════════════
    # SHORTFORM EXPANSIONS
    # ══════════════════════════════════════════════════════
    
    SHORTFORMS = {
        # Subjects
        "os": "operating systems",
        "dbms": "database management systems",
        "cn": "computer networks",
        "ds": "data structures",
        "dsa": "data structures and algorithms",
        "ml": "machine learning",
        "ai": "artificial intelligence",
        "aiml": "artificial intelligence and machine learning",
        "dl": "deep learning",
        "se": "software engineering",
        "coa": "computer organization and architecture",
        "co": "computer organization",
        "toc": "theory of computation",
        "daa": "design and analysis of algorithms",
        "oops": "object oriented programming",
        "oop": "object oriented programming",
        "dm": "discrete mathematics",
        "cns": "cryptography and network security",
        "cc": "cloud computing",
        "iot": "internet of things",
        "cg": "computer graphics",
        "mp": "microprocessor",
        "dld": "digital logic design",
        "es": "embedded systems",
        "mes": "microcontroller and embedded systems",
        "rm": "research methodology",
        "dlca": "digital logic and computer architecture",
        "wt": "wireless technology",
        "fsd": "full stack development",
        
        # Common abbreviations
        "perf": "performance",
        "sem": "semester",
        "prof": "professor",
        "dept": "department",
        "engg": "engineering",
        "pgm": "program",
        "prog": "programming",
        "algo": "algorithm",
        "func": "function",
        "param": "parameter",
        "db": "database",
        "comp": "computer",
        "info": "information",
        "tech": "technology",
        "dev": "development",
        "sys": "system",
        
        # Career related
        "sde": "software development engineer",
        "swe": "software engineer",
        "ds role": "data scientist role",
        "mle": "machine learning engineer",
        "devops": "development operations",

        # Conversational shortforms
        "tn": "thank you",
        "ty": "thank you",
        "thx": "thanks",
        "gn": "good night",
        "gm": "good morning",
        "ga": "good afternoon",
        "ge": "good evening",
        "idk": "i do not know",
        "pls": "please",
        "rn": "right now",
        "nvm": "never mind",
        "ngl": "not gonna lie",
        "tbh": "to be honest",
        "imo": "in my opinion",
        "brb": "be right back",
        
        # Labs
        "ccl": "cloud computing laboratory",
        "dsl": "data science laboratory",
        "cnl": "computer networks lab",
        "dsal": "dsa laboratory",
        "dbmsl": "dbms laboratory",
        "mcl": "microcontroller lab",
        "ail": "ai laboratory",
        "dal": "data analytics lab",
                # Open Elective shortforms
        "re": "reliability engineering",
        "or": "operation research",
        "csl": "cyber security and laws",
        "dbm": "digital business management",
        "eam": "energy audit and management",
        "fmea": "failure mode effects analysis",
        "lpp": "linear programming problem",
        "eoq": "economic order quantity",
        "ecbc": "energy conservation building code",
        "bee": "bureau of energy efficiency",
    }

    # ══════════════════════════════════════════════════════
    # INITIALIZATION
    # ══════════════════════════════════════════════════════

    def __init__(self):
        """Initialize patterns only - model is loaded lazily."""
        self._initialize_patterns()
        self._initialize_prohibited_patterns()
        self._initialize_keyword_mappings()
        self._embeddings_computed = False
        self.intent_embeddings = {}
        logger.debug("IntentClassifier initialized")

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
            logger.info("✅ SentenceTransformer model loaded")
            return _sentence_model
        except ImportError:
            logger.info("ℹ️ sentence-transformers not installed - using rule-based only")
            return None
        except Exception as e:
            logger.warning(f"⚠️ Failed to load SentenceTransformer: {e}")
            return None

    def _initialize_keyword_mappings(self):
        """Initialize keyword to intent mappings for quick lookups."""
        self.keyword_intents = {
            # Syllabus keywords
            "syllabus": IntentType.SYLLABUS_QUERY,
            "explain": IntentType.SYLLABUS_QUERY,
            "define": IntentType.SYLLABUS_QUERY,
            "what is": IntentType.SYLLABUS_QUERY,
            "tell me about": IntentType.SYLLABUS_QUERY,
            "topic": IntentType.SYLLABUS_QUERY,
            "concept": IntentType.SYLLABUS_QUERY,
            "unit": IntentType.SYLLABUS_QUERY,
            "chapter": IntentType.SYLLABUS_QUERY,
            "meaning": IntentType.SYLLABUS_QUERY,
            "definition": IntentType.SYLLABUS_QUERY,
            "how does": IntentType.SYLLABUS_QUERY,
            "types of": IntentType.SYLLABUS_QUERY,
            "difference between": IntentType.SYLLABUS_QUERY,
            "example": IntentType.SYLLABUS_QUERY,
            
            # Faculty keywords
            "who teaches": IntentType.FACULTY_QUERY,
            "teacher": IntentType.FACULTY_QUERY,
            "professor": IntentType.FACULTY_QUERY,
            "faculty": IntentType.FACULTY_QUERY,
            "instructor": IntentType.FACULTY_QUERY,
            "mentor": IntentType.MENTOR_QUERY,
            "taught by": IntentType.FACULTY_QUERY,
            
            # Performance keywords
            "my performance": IntentType.PERFORMANCE_QUERY,
            "my grades": IntentType.PERFORMANCE_QUERY,
            "my marks": IntentType.PERFORMANCE_QUERY,
            "my cgpa": IntentType.PERFORMANCE_QUERY,
            "my sgpa": IntentType.PERFORMANCE_QUERY,
            "my result": IntentType.PERFORMANCE_QUERY,
            "performance analysis": IntentType.PERFORMANCE_QUERY,
            "how am i doing": IntentType.PERFORMANCE_QUERY,
            "weak subjects": IntentType.PERFORMANCE_QUERY,
            "strong subjects": IntentType.PERFORMANCE_QUERY,
            "improve": IntentType.PERFORMANCE_QUERY,
            
            # Career keywords
            "career": IntentType.CAREER_QUERY,
            "job": IntentType.CAREER_QUERY,
            "placement": IntentType.CAREER_QUERY,
            "salary": IntentType.CAREER_QUERY,
            "become a": IntentType.CAREER_QUERY,
            "how to become": IntentType.CAREER_QUERY,
            "roadmap": IntentType.CAREER_QUERY,
            "career path": IntentType.CAREER_QUERY,
            "future": IntentType.CAREER_QUERY,
            "industry": IntentType.CAREER_QUERY,
            "companies": IntentType.CAREER_QUERY,
            "skills needed": IntentType.CAREER_QUERY,
            "data scientist": IntentType.CAREER_QUERY,
            "software engineer": IntentType.CAREER_QUERY,
            "developer": IntentType.CAREER_QUERY,
            
            # Elective keywords
            "elective": IntentType.ELECTIVE_QUERY,
            "which subject": IntentType.ELECTIVE_QUERY,
            "recommend subject": IntentType.ELECTIVE_QUERY,
            "suggest subject": IntentType.ELECTIVE_QUERY,
            "optional": IntentType.ELECTIVE_QUERY,
            "choose subject": IntentType.ELECTIVE_QUERY,
            
            # Study plan keywords
            "study plan": IntentType.STUDY_PLAN_QUERY,
            "study schedule": IntentType.STUDY_PLAN_QUERY,
            "how to study": IntentType.STUDY_PLAN_QUERY,
            "prepare for": IntentType.STUDY_PLAN_QUERY,
            "exam preparation": IntentType.STUDY_PLAN_QUERY,
            "timetable": IntentType.STUDY_PLAN_QUERY,

            # Mentor keywords
            "who should i reach out to": IntentType.MENTOR_QUERY,
            "who can help me": IntentType.MENTOR_QUERY,
            "need a mentor": IntentType.MENTOR_QUERY,
            "reach out to": IntentType.MENTOR_QUERY,
            "who should i contact": IntentType.MENTOR_QUERY,
            
            # Greeting keywords
            "hi": IntentType.GREETING,
            "hello": IntentType.GREETING,
            "hey": IntentType.GREETING,
            "good morning": IntentType.GREETING,
            "good afternoon": IntentType.GREETING,
            "good evening": IntentType.GREETING,
            "help": IntentType.GENERAL,

            # Resource keywords
            "resources": IntentType.RESOURCE_QUERY,
            "study material": IntentType.RESOURCE_QUERY,
            "notes": IntentType.RESOURCE_QUERY,
            "videos": IntentType.RESOURCE_QUERY,
            "tutorials": IntentType.RESOURCE_QUERY,
            "books": IntentType.RESOURCE_QUERY,
            "reference books": IntentType.RESOURCE_QUERY,
            "youtube": IntentType.RESOURCE_QUERY,
            "where to study": IntentType.RESOURCE_QUERY,
            "learning resources": IntentType.RESOURCE_QUERY,
        }
        
        # Subject keywords that indicate syllabus query
        self.subject_keywords = [
            "os", "dbms", "cn", "dsa", "ml", "ai", "dl", "se", "coa", "toc",
            "operating system", "database", "network", "data structure",
            "machine learning", "artificial intelligence", "deep learning",
            "algorithm", "programming", "compiler", "web", "cloud",
            "deadlock", "normalization", "sorting", "searching", "tree",
            "graph", "linked list", "sql", "joins", "tcp", "udp", "osi",
            "semaphore", "mutex", "process", "thread", "scheduling",
            "paging", "segmentation", "neural network", "regression",
            
        ]

    def _initialize_patterns(self):
        """Initialize regex patterns for rule-based classification."""
        self.intent_patterns = {
            IntentType.SYLLABUS_QUERY: [
                r'\b(syllabus|topic|unit|chapter|concept|explain|what is|define|definition|meaning)\b',
                r'\b(subject|course|module|curriculum|content)\b',
                r'\b(learn|study|understand|covers?|includes?)\b.*\b(subject|topic|unit)\b',
                r'\b(deadlock|mutex|semaphore|algorithm|data structure|oop|database|normalization|sql)\b',
                r'\b(unit\s*\d+|chapter\s*\d+)\b',
                r'\b(operating system|os|dbms|dsa|computer network|machine learning|artificial intelligence|cn|ml|ai)\b',
                r'\b(how does|how do|working of|mechanism|types of|kinds of)\b',
                r'\b(difference between|compare|vs|versus)\b',
                r'\btell me about\b',
            ],
            IntentType.FACULTY_QUERY: [
                r'\b(faculty|professor|teacher|instructor|dr\.?|prof\.?)\b',
                r'\b(who teaches|taught by|teaching|teaches)\b',
                r'\b(office hours|consultation|available)\b.*\b(faculty|professor)\b',
                r'\b(recommend|suggest)\b.*\b(faculty|professor)\b',
                r'\b(list|show|all)\b.*\b(faculty|professor|teacher)\b',
            ],
            IntentType.PERFORMANCE_QUERY: [
                r'\b(my|student)\b.*\b(performance|grade|marks|score|cgpa|gpa|sgpa|result)\b',
                r'\b(weak|strong|improve|better|progress)\b.*\b(subject|performance|grade)\b',
                r'\b(my|student)\b.*\b(analysis|report|standing|academics)\b',
                r'\b(attendance|assessment|exam|test)\b.*\b(performance|result)\b',
                r'\b(how am i doing|my grades|my marks|my cgpa|my sgpa|show my|analyze my)\b',
                r'\b(performance|grades|marks|cgpa|sgpa)\b',
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
                r'\b(data scientist|ml engineer|devops|cloud|cybersecurity|web developer|sde|swe)\b',
                r'\b(how to become|want to be|career in|future in|scope in|opportunities in)\b',
            ],
            IntentType.STUDY_PLAN_QUERY: [
                r'\b(study plan|study schedule|timetable|prepare|preparation)\b',
                r'\b(how to|best way)\b.*\b(study|prepare|learn)\b',
                r'\b(exam|semester|final)\b.*\b(preparation|plan|strategy)\b',
                r'\b(improve|better)\b.*\b(study|learning|grades)\b',
            ],
            IntentType.GREETING: [
                r'^(hi|hello|hey|greetings|good morning|good afternoon|good evening)\b',
                r'^(what\'s up|sup|yo)\b',
            ],
            IntentType.RESOURCE_QUERY: [
                r'\b(resource|resources|material|materials|notes|pdf|video|tutorial)\b',
                r'\b(recommend|suggest)\b.*\b(book|video|resource|material|notes)\b',
                r'\b(where|how)\b.*\b(study|learn|practice)\b',
                r'\b(youtube|coursera|udemy|nptel|geeksforgeeks|leetcode)\b',
                r'\b(reference|study material|learning material)\b',
            ],
            IntentType.MENTOR_QUERY: [
                r'\b(who should i|whom should i|who can i)\b.*\b(reach|contact|ask|approach|consult|talk)\b',
                r'\b(reach out|contact|approach|consult)\b.*\b(for help|for guidance|about|regarding)\b',
                r'\b(need|want|looking for)\b.*\b(mentor|guidance|help|advisor)\b',
                r'\b(mentor|advisor)\b.*\b(for|in|about)\b',
                r'\b(help me with|struggling with|weak in|poor in)\b.*\b(who|faculty|professor|mentor)\b',
                r'\b(faculty|professor)\b.*\b(help|weak|improve|struggling)\b',
                r'\b(who can help)\b',
            ],
        }

    def _initialize_prohibited_patterns(self):
        """Initialize patterns for out-of-scope detection."""
        self.prohibited_patterns = [
            r'\b(politic|election|vote|government|minister|parliament|democrat|republican|modi|trump|biden)\b',
            r'\b(cricket|football|soccer|basketball|tennis|ipl|fifa|olympic|match|player|team|score)\b',
            r'\b(movie|film|actor|actress|bollywood|hollywood|netflix|song|music|singer|celebrity|avengers|marvel)\b',
            r'\b(religion|god|church|temple|mosque|prayer|spiritual|divine|hindu|muslim|christian)\b',
            r'\b(weather|recipe|cook|travel|vacation|hotel|restaurant|food|dish)\b',
            r'\b(relationship|dating|love|marriage|personal|family problem|boyfriend|girlfriend)\b',
            r'\b(game|gaming|pubg|fortnite|minecraft|xbox|playstation|gta|valorant|cod)\b',
            r'\b(news|latest|breaking|headline|current affair)\b',
            r'\b(joke|funny|meme|lol|rofl)\b',
        ]

    # ══════════════════════════════════════════════════════
    # MAIN CLASSIFICATION
    # ══════════════════════════════════════════════════════

    def classify(self, query: str, context: Optional[Dict] = None) -> Tuple[IntentType, float]:
        if not query or not query.strip():
            return IntentType.GENERAL, 0.3

        original_lower = query.lower().strip()
        original_clean = original_lower.rstrip("?!. ")
        word_count = len(original_lower.split())
        
        # Expand shortforms BEFORE classification
        query_expanded = self._expand_shortforms(query)
        query_lower = query_expanded.lower().strip()

        # ═══════════════════════════════════════════════
        # PRIORITY 0: Greeting / Conversational / Meta
        # ═══════════════════════════════════════════════
        
        for check_text in [original_lower, query_lower]:
            conversational = [
                r'^who\s+are\s+you', r'^what\s+are\s+you',
                r'^what\s+can\s+you\s+do', r'^what\s+do\s+you\s+do',
                r'^are\s+you\s+(a\s+)?(bot|ai|chatbot|human)',
                r'^tell\s+me\s+about\s+(yourself|you|ur\s*self)',
                r'^introduce\s+yourself', r'^about\s+yourself',
                r'^(thanks?|thank\s+you|thx|ty)\b',
                r'^(thanks?\s+(a\s+lot|so\s+much|buddy|bro|man|dude))',
                r'^(ok|okay|sure|alright|got\s+it|cool|nice|great|awesome|perfect|right|fine)\s*[!.]*$',
                r'^(bye+|byee*|goodbye|see\s+you|later|cya|tata|bbye)\b',
                r'^(good\s*night|good\s*bye|gn|nighty?)\b',
                r'^(yo+|sup+|wassup|what\'?s?\s+up|heya?|howdy|hola|namaste)\b',
                r'^(hii+|heyy+|helloo+|hellooo+)\b',
                r'^(hi|hello|hey)\b',
                r'^(good\s+morning|good\s+afternoon|good\s+evening)\b',
                r'^(lol|lmao|haha+|rofl|😂|😆|🤣)\b',
                r'^(hehe+|hihi+)\b',
                r'\b(am\s+i|i\s+am|i\'m)\s+(a\s+)?(dumb|stupid|dufus|idiot|bad|weird|ugly|loser|fool)',
                r'\b(i\s+suck|i\'m\s+(so\s+)?bad|hate\s+myself)',
                r'^(i\s+(am|\'m)\s+(sad|happy|angry|frustrated|confused|bored|tired|stressed|anxious))\b',
                r'^that\'?s?\s+(sad|great|cool|nice|bad|good|awesome|terrible)',
                r'^i\s+(am|\'m)\s+(a\s+)?(student|in\s+sem|from|studying)\b',
                r'^my\s+name\s+is\b',
                r'^(brb|nvm|never\s+mind|forget\s+it)',
            ]
            for p in conversational:
                if re.search(p, check_text):
                    return IntentType.GREETING, 0.95
                
        # ═══════════════════════════════════════════════
        # PRIORITY 0.7: Quiz requests
        # ═══════════════════════════════════════════════
        if re.search(r'\b(quiz|test me|test myself|mcq|question)\b', original_lower):
            return IntentType.SYLLABUS_QUERY, 0.95

        # ═══════════════════════════════════════════════
        # PRIORITY 0.8: Resource requests
        # ═══════════════════════════════════════════════
        if re.search(r'\b(resources?|materials?|notes?|pdfs?|tutorials?|videos?)\b.*\b(for|on|about|of)\b', original_lower):
            return IntentType.RESOURCE_QUERY, 0.9
        if re.search(r'\b(where|how)\s+(to|can i)\s+(study|learn|practice|find)\b', original_lower):
            return IntentType.RESOURCE_QUERY, 0.85

        # ═══════════════════════════════════════════════
        # PRIORITY 0.5: Out-of-scope
        # ═══════════════════════════════════════════════
        if self._is_out_of_scope(original_lower):
            return IntentType.OUT_OF_SCOPE, 0.95

        existential = [
            r'\bwhy\s+do\s+i\s+(live|exist|suffer|feel)\b',
            r'\bwhat\s+is\s+(the\s+)?(meaning|purpose)\s+of\s+life\b',
            r'\b(meaning\s+of\s+life|purpose\s+of\s+life)\b',
            r'\b(kill\s+myself|suicide|self\s*harm|end\s+it)\b',
        ]
        for p in existential:
            if re.search(p, original_lower):
                return IntentType.OUT_OF_SCOPE, 0.99

        # ═══════════════════════════════════════════════
        # PRIORITY 1: "teach me X" → SYLLABUS
        # ═══════════════════════════════════════════════
        teach_match = re.match(r'^(?:teach|explain|describe|tell)\s+(?:me\s+)?(?:about\s+)?(.+)', original_lower)
        if teach_match:
            topic = teach_match.group(1).strip().rstrip("?!.")
            if not re.search(r'\bwho\s+teaches\b', topic):
                if topic and len(topic) >= 2:
                    return IntentType.SYLLABUS_QUERY, 0.85

        # ═══════════════════════════════════════════════
        # PRIORITY 2: Personal performance queries
        # ═══════════════════════════════════════════════
        perf = [
            r'\bmy\s+(performance|grades?|marks?|cgpa|sgpa|results?|academics?|progress|scores?)',
            r'\b(show|display|view|check|see|analyse|analyze)\s+my\b',
            r'\bhow\s+am\s+i\s+doing\b',
            r'\bmy\s+performance\b', r'\bmy\s+academic\b',
            r'\bmy\s+weak\b', r'\bmy\s+strong\b',
            r'\bsubjects?\s+i\s+should\s+focus\b',
            r'\bwhere\s+(should|can|do)\s+i\s+improve\b',
            r'\b(analyse|analyze)\s+my\s+(performance|grades|academics)\b',
            r'\btell\s+me\s+about\s+my\s+(performance|grades|marks|academics)\b',
        ]
        for p in perf:
            if re.search(p, original_lower):
                return IntentType.PERFORMANCE_QUERY, 0.95

        # ═══════════════════════════════════════════════
        # PRIORITY 3: Career queries
        # ═══════════════════════════════════════════════
        career_names = [
            "data scientist", "data science", "software developer", "software engineer",
            "ml engineer", "machine learning engineer", "devops", "full stack",
            "web developer", "frontend developer", "backend developer",
            "cloud architect", "cybersecurity", "security analyst",
            "data analyst", "data engineer", "ai engineer", "network engineer",
            "qa engineer", "test automation", "nlp engineer", "blockchain developer",
            "product manager", "project manager", "scrum master",
            "sde", "swe", "mle",
        ]
        for cn in career_names:
            if cn in original_lower:
                if not re.search(r'\bwho\s+teaches\b', original_lower):
                    return IntentType.CAREER_QUERY, 0.9

        if re.search(r'\b(career|careers|job|jobs|placement|salary|become a|how to become)\b', original_lower):
            return IntentType.CAREER_QUERY, 0.85

        # ═══════════════════════════════════════════════
        # PRIORITY 4: Semester queries
        # ═══════════════════════════════════════════════
        if re.search(r'sem(?:ester)?\s*\d+', original_lower):
            return IntentType.SYLLABUS_QUERY, 0.95
        if re.search(r'\d+(?:st|nd|rd|th)\s*sem', original_lower):
            return IntentType.SYLLABUS_QUERY, 0.95

        # ═══════════════════════════════════════════════
        # PRIORITY 5: Faculty queries
        # ═══════════════════════════════════════════════
        if re.search(r'\bwho\s+teaches\b', original_lower):
            return IntentType.FACULTY_QUERY, 0.95
        if re.search(r'(?:^|\b)(faculty|professors?|teachers?)\s*$', original_lower):
            return IntentType.FACULTY_QUERY, 0.9
        if re.search(r'(?:tell|know|show|list|all).*\b(faculty|professors?)\b', original_lower):
            return IntentType.FACULTY_QUERY, 0.9
        if re.search(r'\b(show|list)\s+all\s+faculty\b', original_lower):
            return IntentType.FACULTY_QUERY, 0.95

        # ═══════════════════════════════════════════════
        # PRIORITY 6: Mentor queries
        # ═══════════════════════════════════════════════
        mentor_pats = [
            r'\bwho\s+(?:should|can|do)\s+i\s+(?:reach|contact|ask|approach|consult|talk|meet)',
            r'\b(?:contact|reach)\s+(?:out\s+)?(?:for|about)',
            r'\bdoubts?\s+in\b', r'\bneed\s+(?:a\s+)?mentor\b',
            r'\bwho\s+can\s+help\b', r'\bstruggling\s+(?:with|in)\b',
        ]
        for p in mentor_pats:
            if re.search(p, original_lower):
                return IntentType.MENTOR_QUERY, 0.9

        # ═══════════════════════════════════════════════
        # PRIORITY 7: Study/resource queries
        # ═══════════════════════════════════════════════
        if re.search(r'\b(resources?|how to study|how to learn|study plan|study schedule|prepare for|exam tips?|timetable)\b', original_lower):
            return IntentType.STUDY_PLAN_QUERY, 0.85
        if re.search(r'\b(recommend|suggest)\s+(?:some\s+)?(?:books?|resources?|videos?|tutorials?)\b', original_lower):
            return IntentType.RESOURCE_QUERY, 0.85

        # ═══════════════════════════════════════════════
        # PRIORITY 8: Elective queries
        # ═══════════════════════════════════════════════
        if re.search(r'\b(elective|open\s+elective|program\s+elective|pe\s*\d|oe\s*\d)\b', original_lower):
            return IntentType.ELECTIVE_QUERY, 0.85
        if re.search(r'\b(recommend|suggest|choose|select)\b.*\b(elective|subject|course)\b', original_lower):
            if not self._is_out_of_scope(original_lower):
                return IntentType.ELECTIVE_QUERY, 0.80

        # ═══════════════════════════════════════════════
        # PRIORITY 9: Follow-up queries
        # ═══════════════════════════════════════════════
        if context and word_count <= 6:
            follow_ups = [
                r'^(tell me more|explain more|more details|go on|continue)',
                r'^(what about|how about|and)\s',
                r'^(the|its|their|those|these)\s+(topics?|units?|syllabus)',
                r'^(topics?|units?|syllabus)\s*(of|for|in)?\s*$',
                r'^(yes|ok|sure|please|more)',
                r'^(for all|all of them|list them|show all|every|full|complete)',
            ]
            for p in follow_ups:
                if re.match(p, original_lower):
                    last = context.get("last_intent")
                    if last:
                        try:
                            inherited = IntentType(last) if isinstance(last, str) else last
                            return inherited, 0.8
                        except (ValueError, KeyError):
                            pass

        # ═══════════════════════════════════════════════
        # STANDARD CLASSIFICATION
        # ═══════════════════════════════════════════════
        kw = self._keyword_match(query_lower)
        if kw[1] >= 0.7:
            return kw

        rule = self._rule_based_classification(query_lower)
        if rule[1] >= 0.5:
            return rule

        subj = self._detect_subject_query(original_lower, query_lower)
        if subj[1] >= 0.5:
            return subj

        if context:
            ctx = self._apply_context(rule, context, query_lower)
            if ctx[1] >= 0.5:
                return ctx

        if rule[1] < 0.4:
            sem = self._semantic_classification(query_expanded)
            if sem[1] > 0.7 and sem[1] > rule[1]:
                return sem

        if rule[1] < 0.3:
            return IntentType.GENERAL, 0.5

        return rule

    def _expand_shortforms(self, query: str) -> str:
        """Expand shortforms to full forms."""
        words = query.lower().split()
        expanded = []
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in self.SHORTFORMS:
                expanded.append(self.SHORTFORMS[clean_word])
            else:
                expanded.append(word)
        
        return ' '.join(expanded)

    def _keyword_match(self, query: str) -> Tuple[IntentType, float]:
        """Match keywords directly for quick classification."""
        best_intent = IntentType.GENERAL
        best_score = 0.0
        
        for keyword, intent in self.keyword_intents.items():
            if keyword in query:
                score = min(0.6 + (len(keyword) / 20), 0.9)
                if score > best_score:
                    best_score = score
                    best_intent = intent
        
        return best_intent, best_score

    def _detect_subject_query(self, original: str, expanded: str) -> Tuple[IntentType, float]:
        """Detect if query is about a subject."""
        original_clean = original.strip().lower().rstrip('?!.')
        
        subject_shortforms = ['os', 'ml', 'ai', 'cn', 'dbms', 'dsa', 'ds', 'dl', 'se', 'coa', 
                              'toc', 'daa', 'oop', 'oops', 'dm', 'cns', 'cc', 'iot', 'cg']
        
        if original_clean in subject_shortforms:
            return IntentType.SYLLABUS_QUERY, 0.75
        
        for keyword in self.subject_keywords:
            if keyword in expanded.lower():
                if any(fw in original.lower() for fw in ['who teaches', 'teacher', 'faculty', 'professor']):
                    return IntentType.FACULTY_QUERY, 0.8
                return IntentType.SYLLABUS_QUERY, 0.7
        
        return IntentType.GENERAL, 0.3

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
                try:
                    if re.search(pattern, query, re.IGNORECASE):
                        match_count += 1
                except re.error:
                    continue
            
            if match_count > 0:
                scores[intent] = min((match_count / len(patterns)) * 0.6 + 0.3, 0.95)

        if not scores:
            return IntentType.GENERAL, 0.3

        best_intent = max(scores, key=scores.get)
        return best_intent, scores[best_intent]

    def _semantic_classification(self, query: str) -> Tuple[IntentType, float]:
        """Classify using semantic similarity."""
        model = self._get_model()
        if not model:
            return IntentType.GENERAL, 0.4

        try:
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity
            
            if not self._embeddings_computed:
                self._compute_embeddings(model)

            if not self.intent_embeddings:
                return IntentType.GENERAL, 0.4

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

    def _compute_embeddings(self, model):
        """Compute embeddings for intent examples."""
        try:
            intent_examples = {
                IntentType.SYLLABUS_QUERY: [
                    "Explain the concept of deadlock in operating systems",
                    "What topics are covered in unit 3 of DBMS?",
                    "Define normalization in database",
                    "What is the syllabus for data structures?",
                    "Tell me about machine learning",
                    "Explain OOP concepts",
                    "What is OS",
                    "DBMS topics",
                ],
                IntentType.FACULTY_QUERY: [
                    "Who teaches operating systems?",
                    "Tell me about Dr. Smith's research areas",
                    "Which faculty is best for mentoring in machine learning?",
                    "Recommend a faculty mentor",
                    "Who teaches OS",
                    "Faculty for ML",
                ],
                IntentType.PERFORMANCE_QUERY: [
                    "What is my current CGPA?",
                    "Show my performance analysis",
                    "Which subjects am I weak in?",
                    "Analyze my academic performance",
                    "My grades",
                    "How am I doing",
                ],
                IntentType.ELECTIVE_QUERY: [
                    "Which electives should I choose?",
                    "Recommend electives for machine learning career",
                    "Best electives for software development",
                    "Suggest some electives",
                ],
                IntentType.CAREER_QUERY: [
                    "What career options are available after CSE?",
                    "How to become a data scientist?",
                    "What skills are needed for software engineering?",
                    "Career roadmap for machine learning",
                    "Career in AI",
                    "Jobs in ML",
                ],
                IntentType.STUDY_PLAN_QUERY: [
                    "How should I prepare for semester exams?",
                    "Create a study plan for DBMS",
                    "Best strategy to improve my grades",
                    "Study schedule",
                ],
            }
            
            for intent, examples in intent_examples.items():
                self.intent_embeddings[intent] = model.encode(examples)
            
            self._embeddings_computed = True
            logger.info("✅ Intent embeddings computed")
        except Exception as e:
            logger.warning(f"Failed to compute embeddings: {e}")
            self._embeddings_computed = True

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

        follow_up_patterns = [
            r'^(and|also|what about|how about|tell me more|explain more)',
            r'^(it|this|that|these|those)\b',
            r'^(yes|no|okay|sure|please|more|continue|go on)\b',
        ]

        for pattern in follow_up_patterns:
            if re.match(pattern, query, re.IGNORECASE):
                try:
                    if isinstance(last_intent, str):
                        inherited = IntentType(last_intent)
                    else:
                        inherited = last_intent
                    return inherited, min(confidence + 0.25, 0.85)
                except (ValueError, KeyError):
                    pass

        return result

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
    
    def extract_subject_from_query(self, query: str) -> Optional[str]:
        """Extract subject name from query."""
        for pattern, extractor in SUBJECT_QUERY_PATTERNS:
            m = re.search(pattern, query.lower())
            if m:
                return extractor(m).strip()
        
        for name in ALL_KNOWN_SUBJECTS:
            if name.lower() in query.lower():
                return name
        
        return None