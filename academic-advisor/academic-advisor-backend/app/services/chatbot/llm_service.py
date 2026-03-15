# app/services/chatbot/llm_service.py
"""
Free LLM Service using Groq API
Llama 3.3 70B - Fast, free, and powerful!
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from functools import lru_cache

logger = logging.getLogger(__name__)

# Lazy load Groq client
_groq_client = None
_groq_available = False


def _get_groq_client():
    """Lazy load Groq client."""
    global _groq_client, _groq_available
    
    if _groq_client is not None:
        return _groq_client if _groq_available else None
    
    try:
        from groq import Groq
        from app.config import settings
        
        if not settings.GROQ_API_KEY:
            logger.warning("⚠️ GROQ_API_KEY not set - LLM features disabled")
            _groq_available = False
            return None
        
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
        _groq_available = True
        logger.info("✅ Groq client initialized (Llama 3.3 70B)")
        return _groq_client
        
    except ImportError:
        logger.warning("⚠️ groq package not installed - run: pip install groq")
        _groq_available = False
        return None
    except Exception as e:
        logger.error(f"❌ Failed to initialize Groq: {e}")
        _groq_available = False
        return None


# System prompts for different contexts
SYSTEM_PROMPTS = {
    "default": """You are "Academic Advisor", a helpful AI for FCRIT engineering students (Mumbai, India).

RULES:
1. ONLY answer academic & career questions (CS/IT engineering)
2. Keep responses under 1000 words — be concise
3. Use bullet points and bold for key terms
4. If asked non-academic questions, say "I can only help with academic topics"
5. NEVER pretend to be a professor or human
6. NEVER make up faculty names or specific data
7. Use Indian context (salaries in LPA, mention Indian companies)
8. Format with markdown: **bold**, bullet points, numbered lists""",

    "syllabus": """You explain CS/IT concepts to Indian engineering students.

STRICT FORMAT:
- 1-2 sentence clear definition first
- Then 3-5 bullet points with key concepts
- Maximum 1000 words TOTAL — be concise!
- Use **bold** for terms
- Do NOT write code unless specifically asked for code
- Do NOT say "as a professor" — you are an AI assistant
- Mention exam relevance in 1 sentence at the end""",

    "career": """You are a career counselor for Indian tech students.

FORMAT:
- Give realistic info (Indian salaries in LPA)
- Mention both Indian and global companies
- Suggest specific skills to learn
- Keep it under 1000 words
- Be encouraging but realistic""",

    "performance": """You analyze student academic performance.

FORMAT:
- Be encouraging but honest
- Give 2-3 specific actionable tips
- Keep it under 80 words
- Focus on improvement, not criticism""",

    "frustrated_user": """The student seems frustrated or confused.

RULES:
- Be extra empathetic and patient
- Acknowledge their feelings briefly (1 sentence)
- Then answer their actual question clearly
- Keep total response under 150 words
- Don't be condescending""",

    "detailed": """You explain CS/IT concepts to engineering students using a progressive flashcard approach.

You MUST return ONLY a valid JSON object (no markdown fences, no commentary) with this EXACT structure:
{
    "cards": [
        {
            "title": "What is it?",
            "icon": "📘",
            "points": [
                "**Definition**: A clear 2-3 sentence definition of the concept",
                "**Purpose**: Why this concept exists and why it matters in computing"
            ],
            "level": "beginner"
        },
        {
            "title": "How it Works",
            "icon": "⚙️",
            "points": [
                "**Mechanism**: Step-by-step explanation of how it operates internally",
                "**Process**: The detailed working procedure or algorithm steps",
                "**Key Formula/Rule**: Any important formulas, theorems, or rules"
            ],
            "level": "intermediate"
        },
        {
            "title": "Key Concepts",
            "icon": "🧠",
            "points": [
                "**Types/Variations**: Different types or classifications",
                "**Properties**: Important properties or characteristics",
                "**Comparison**: How it differs from related concepts"
            ],
            "level": "intermediate"
        },
        {
            "title": "Real-World Applications",
            "icon": "🚀",
            "points": [
                "**Industry Use**: Where this is used in real software systems",
                "**Example Scenario**: A concrete practical example with explanation",
                "**Related Technologies**: Connected tools, frameworks, or systems"
            ],
            "level": "advanced"
        },
        {
            "title": "Exam Focus & Mastery",
            "icon": "🎯",
            "points": [
                "**Commonly Asked**: Types of exam questions on this topic",
                "**Mistakes to Avoid**: Common errors students make",
                "**Learning Outcome**: What you should be able to do after mastering this",
                "**Memory Tip**: A mnemonic or trick to remember key aspects"
            ],
            "level": "advanced"
        }
    ]
}

RULES:
- ALWAYS return exactly 5 cards in the order shown above
- Each point should be 2-3 sentences with a **bold** leading term
- Card 1-2 cover basics, Card 3 goes deeper, Card 4-5 cover applications and exam mastery
- Be thorough — approximately 500 words total across all cards
- Include real examples, not generic descriptions
- The last card MUST include exam-specific tips and learning outcomes
- Return ONLY the JSON object — no text before or after, no markdown fences""",
}



class LLMService:
    """
    LLM Service using Groq's free API.
    Provides intelligent responses when built-in knowledge isn't sufficient.
    """
    
    def __init__(self):
        self.model = "llama-3.3-70b-versatile"  # Free and fast!
        self.fallback_model = "llama-3.1-8b-instant"  # Faster fallback
        self.max_tokens = 500
        self.temperature = 0.7
        
    @property
    def is_available(self) -> bool:
        """Check if LLM service is available."""
        return _get_groq_client() is not None
    
    async def generate_response(
        self,
        query: str,
        context_type: str = "default",
        student_context: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None,
        sentiment: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        Generate a response using Groq's LLM.
        
        Args:
            query: User's question
            context_type: Type of query (syllabus, career, etc.)
            student_context: Student's academic data
            conversation_history: Recent conversation messages
            sentiment: Sentiment analysis results
        
        Returns:
            Generated response or None if unavailable
        """
        client = _get_groq_client()
        if not client:
            return None
        
        try:
            # Build system prompt
            system_prompt = SYSTEM_PROMPTS.get(context_type, SYSTEM_PROMPTS["default"])
            
            # Add frustrated user handling if detected
            if sentiment and sentiment.get("is_frustrated"):
                system_prompt = SYSTEM_PROMPTS["frustrated_user"] + "\n\n" + system_prompt
            
            # Add student context if available
            if student_context:
                context_str = self._format_student_context(student_context)
                system_prompt += f"\n\nStudent Context:\n{context_str}"
            
            # Build messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (last 3 turns)
            if conversation_history:
                for msg in conversation_history[-6:]:  # Last 3 exchanges
                    role = "user" if msg.get("role") == "user" else "assistant"
                    content = msg.get("content", "")
                    if isinstance(content, dict):
                        content = content.get("message", str(content))
                    messages.append({"role": role, "content": str(content)[:500]})
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            # Call Groq API (run in thread pool for async)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            # Try fallback model
            return await self._fallback_generate(query, context_type)
    
    async def _fallback_generate(
        self,
        query: str,
        context_type: str
    ) -> Optional[str]:
        """Fallback to smaller/faster model."""
        client = _get_groq_client()
        if not client:
            return None
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=self.fallback_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPTS.get(context_type, SYSTEM_PROMPTS["default"])},
                        {"role": "user", "content": query}
                    ],
                    temperature=0.5,
                    max_tokens=300,
                )
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Fallback LLM error: {e}")
            return None
    
    async def enhance_response(
        self,
        base_response: Dict[str, Any],
        query: str,
        student_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Enhance a built-in response with personalized LLM insights.
        
        Args:
            base_response: The response from built-in knowledge
            query: Original user query
            student_context: Student's academic data
        
        Returns:
            Enhanced response with AI insights
        """
        if not self.is_available:
            return base_response
        
        try:
            # Only enhance certain response types
            response_type = base_response.get("type", "")
            if response_type not in ["performance_analysis", "career_guidance", "study_plan", "elective_recommendation"]:
                return base_response
            
            # Generate personalized insight
            prompt = self._build_enhancement_prompt(base_response, query, student_context)
            insight = await self.generate_response(prompt, context_type=response_type.replace("_", " "))
            
            if insight:
                # Add to appropriate field
                content = base_response.get("content", {})
                if response_type == "performance_analysis":
                    content["ai_insights"] = insight
                elif response_type == "career_guidance":
                    content["personalized_advice"] = insight
                elif response_type == "study_plan":
                    content["ai_study_tips"] = insight
                elif response_type == "elective_recommendation":
                    content["ai_advice"] = insight
                
                base_response["content"] = content
                base_response["llm_enhanced"] = True
            
            return base_response
            
        except Exception as e:
            logger.warning(f"Response enhancement failed: {e}")
            return base_response
    
    def _format_student_context(self, ctx: Dict) -> str:
        """Format student context for the prompt."""
        parts = []
        if ctx.get("name"):
            parts.append(f"Name: {ctx['name']}")
        if ctx.get("branch"):
            parts.append(f"Branch: {ctx['branch']}")
        if ctx.get("semester"):
            parts.append(f"Semester: {ctx['semester']}")
        if ctx.get("cgpa"):
            parts.append(f"CGPA: {ctx['cgpa']}")
        if ctx.get("weak_subjects"):
            parts.append(f"Weak subjects: {', '.join(ctx['weak_subjects'][:3])}")
        if ctx.get("strong_subjects"):
            parts.append(f"Strong subjects: {', '.join(ctx['strong_subjects'][:3])}")
        if ctx.get("interests"):
            parts.append(f"Interests: {', '.join(ctx['interests'][:3])}")
        if ctx.get("career_goals"):
            parts.append(f"Career goals: {', '.join(ctx['career_goals'][:2])}")
        
        return "\n".join(parts) if parts else "No student data available"
    
    def _build_enhancement_prompt(
        self,
        response: Dict,
        query: str,
        student_context: Optional[Dict]
    ) -> str:
        """Build prompt for response enhancement."""
        response_type = response.get("type", "")
        content = response.get("content", {})
        
        if response_type == "performance_analysis":
            return f"""Based on this student's performance data:
CGPA: {content.get('current_cgpa', 'N/A')}
Weak subjects: {content.get('weak_subjects', [])}
Trend: {content.get('trend_direction', 'stable')}

Give 2-3 specific, actionable tips for improvement in 50 words or less."""

        elif response_type == "career_guidance":
            career = content.get("career", {})
            return f"""Student asked about: {career.get('title', query)}
Their CGPA: {student_context.get('cgpa', 'N/A') if student_context else 'N/A'}
Their skills: {student_context.get('skills', []) if student_context else []}

Give personalized advice for this career path in 50 words or less."""

        elif response_type == "study_plan":
            return f"""Student needs a study plan. Focus areas: {content.get('focus_areas', [])}
Give 2-3 practical study tips in 40 words or less."""

        else:
            return f"Provide a brief helpful tip for: {query} (30 words max)"

    async def generate_detailed_explanation(
        self,
        topic: str,
        subject: str = "",
        existing_points: list = None,
        conversation_history: list = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate progressive flashcard-style explanation.
        Returns dict with 'cards' array for swipeable UI.
        """
        client = _get_groq_client()
        if not client:
            return None

        existing_ctx = ""
        if existing_points:
            existing_ctx = (
                "\nThe student already knows these basics — go deeper:\n"
                + "\n".join(f"- {p}" for p in existing_points[:5])
            )

        user_prompt = (
            f'Explain "{topic}"'
            f'{" in the context of " + subject if subject else ""}'
            f" in comprehensive detail for an engineering student."
            f"{existing_ctx}"
        )

        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPTS["detailed"]},
            ]

            if conversation_history:
                for msg in conversation_history[-4:]:
                    role = "user" if msg.get("role") == "user" else "assistant"
                    content = msg.get("content", "")
                    if isinstance(content, dict):
                        content = content.get("message", str(content))
                    messages.append({"role": role, "content": str(content)[:300]})

            messages.append({"role": "user", "content": user_prompt})

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.5,
                    max_tokens=1200,
                ),
            )

            text = response.choices[0].message.content.strip()

            # ── Parse JSON ───────────────────────────────
            import json as _json

            # Strip markdown fences if present
            if text.startswith("```"):
                lines = text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines).strip()

            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = _json.loads(text[start:end])

                # ── New card format ──────────────────────
                if isinstance(parsed, dict) and "cards" in parsed:
                    cards = parsed["cards"]
                    if isinstance(cards, list) and len(cards) > 0:
                        # Validate card structure
                        valid_cards = []
                        for c in cards:
                            if isinstance(c, dict) and "title" in c and "points" in c:
                                c.setdefault("icon", "📄")
                                c.setdefault("level", "beginner")
                                if isinstance(c["points"], list) and len(c["points"]) > 0:
                                    valid_cards.append(c)
                        if valid_cards:
                            logger.info(
                                f"✅ Flashcard explanation for '{topic}': "
                                f"{len(valid_cards)} cards"
                            )
                            return {"cards": valid_cards}

                # ── Old format fallback: convert to cards ─
                if isinstance(parsed, dict) and "definition" in parsed:
                    cards = self._convert_old_format_to_cards(parsed, topic)
                    if cards:
                        return {"cards": cards}

            # ── Raw text fallback: single card ───────────
            logger.warning("LLM returned non-JSON for detailed explanation")
            return {
                "cards": [{
                    "title": "Explanation",
                    "icon": "📘",
                    "points": [text[:1500]],
                    "level": "beginner",
                }]
            }

        except Exception as e:
            logger.error(f"generate_detailed_explanation error: {e}")
            try:
                fallback_resp = await self._fallback_generate(
                    f"Explain {topic} in detail for an engineering student.",
                    "syllabus",
                )
                if fallback_resp:
                    return {
                        "cards": [{
                            "title": "Explanation",
                            "icon": "📘",
                            "points": [fallback_resp],
                            "level": "beginner",
                        }]
                    }
            except Exception:
                pass
            return None

    @staticmethod
    def _convert_old_format_to_cards(parsed: dict, topic: str) -> list:
        """Convert old definition/key_points format into flashcard cards."""
        cards = []

        if parsed.get("definition"):
            cards.append({
                "title": "What is it?",
                "icon": "📘",
                "points": [parsed["definition"]],
                "level": "beginner",
            })

        if parsed.get("key_points"):
            # Split key_points into two cards if many
            kps = parsed["key_points"]
            if len(kps) > 3:
                cards.append({
                    "title": "Core Concepts",
                    "icon": "🧠",
                    "points": kps[:3],
                    "level": "intermediate",
                })
                cards.append({
                    "title": "Deep Dive",
                    "icon": "⚙️",
                    "points": kps[3:],
                    "level": "intermediate",
                })
            elif kps:
                cards.append({
                    "title": "Key Concepts",
                    "icon": "🧠",
                    "points": kps,
                    "level": "intermediate",
                })

        if parsed.get("examples"):
            cards.append({
                "title": "Examples & Applications",
                "icon": "💡",
                "points": parsed["examples"],
                "level": "advanced",
            })

        exam_points = []
        if parsed.get("common_mistakes"):
            exam_points.extend(
                f"**Mistake to avoid**: {m}" for m in parsed["common_mistakes"]
            )
        if parsed.get("exam_relevance"):
            exam_points.append(f"**Exam Focus**: {parsed['exam_relevance']}")
        if exam_points:
            cards.append({
                "title": "Exam Focus",
                "icon": "🎯",
                "points": exam_points,
                "level": "advanced",
            })

        return cards if cards else None

# Singleton instance
_llm_service = None


def get_llm_service() -> LLMService:
    """Get or create LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service