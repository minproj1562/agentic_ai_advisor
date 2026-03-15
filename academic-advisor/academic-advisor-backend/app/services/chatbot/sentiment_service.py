# app/services/chatbot/sentiment_service.py
"""
Sentiment Analysis Service using VADER
Completely FREE - runs locally, no API needed!
"""

import re
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Lazy load VADER
_vader_analyzer = None
_vader_available = False
_vader_load_attempted = False


def _get_vader():
    """Lazy load VADER sentiment analyzer."""
    global _vader_analyzer, _vader_available, _vader_load_attempted
    
    if _vader_load_attempted:
        return _vader_analyzer if _vader_available else None
    
    _vader_load_attempted = True
    
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        _vader_analyzer = SentimentIntensityAnalyzer()
        _vader_available = True
        logger.info("✅ VADER sentiment analyzer loaded")
        return _vader_analyzer
    except ImportError:
        logger.warning("⚠️ vaderSentiment not installed - run: pip install vaderSentiment")
        _vader_available = False
        return None
    except Exception as e:
        logger.error(f"Failed to load VADER: {e}")
        _vader_available = False
        return None


@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    compound: float = 0.0  # -1 to 1 overall score
    positive: float = 0.0  # 0 to 1
    negative: float = 0.0  # 0 to 1
    neutral: float = 1.0   # 0 to 1
    
    is_frustrated: bool = False
    is_confused: bool = False
    is_anxious: bool = False
    is_positive: bool = False
    is_urgent: bool = False
    
    mood: str = "neutral"  # "positive", "negative", "neutral", "frustrated", "confused"
    confidence: float = 0.5  # How confident we are in the analysis
    
    # Adaptive response suggestions
    tone_adjustment: str = "normal"  # "empathetic", "encouraging", "patient", "normal"
    suggest_human_advisor: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SentimentService:
    """
    Analyzes user sentiment to adapt chatbot responses.
    Uses VADER (Valence Aware Dictionary and sEntiment Reasoner).
    """
    
    # Patterns for detecting specific emotional states
    FRUSTRATION_PATTERNS = [
        r'\b(frustrated|annoyed|irritated|angry|mad|upset|hate|sick of|tired of)\b',
        r'\b(doesn\'t work|not working|broken|useless|terrible|worst)\b',
        r'\b(wtf|ugh|argh|damn|hell)\b',
        r'!{2,}',  # Multiple exclamation marks
        r'\?{2,}',  # Multiple question marks
        r'(why (won\'t|can\'t|doesn\'t|isn\'t))',
    ]
    
    CONFUSION_PATTERNS = [
        r'\b(confused|don\'t understand|doesn\'t make sense|what do you mean)\b',
        r'\b(huh|what\?|unclear|lost|clueless)\b',
        r'\b(can you explain|help me understand|i\'m not sure)\b',
        r'\b(how does|what is the|what are the)\b.*\?',
        r'\b(difference between|compare|versus|vs)\b',
    ]
    
    ANXIETY_PATTERNS = [
        r'\b(worried|anxious|nervous|scared|afraid|stressed|panic)\b',
        r'\b(exam|test|fail|failing|deadline|urgent)\b',
        r'\b(help|please|desperate|asap|immediately)\b',
        r'\b(will i|am i going to|what if)\b',
    ]
    
    URGENCY_PATTERNS = [
        r'\b(urgent|asap|immediately|right now|hurry|quickly)\b',
        r'\b(tomorrow|today|deadline|due|exam tomorrow)\b',
        r'\b(last minute|running out of time|no time)\b',
    ]
    
    POSITIVE_PATTERNS = [
        r'\b(thank|thanks|great|awesome|amazing|helpful|perfect)\b',
        r'\b(love|excellent|wonderful|fantastic|brilliant)\b',
        r'\b(understand|got it|makes sense|clear now)\b',
        r'😊|😀|👍|🙏|❤️|💯',
    ]

    def __init__(self):
        self.analyzer = None
        
    def _ensure_analyzer(self) -> bool:
        """Ensure VADER is loaded."""
        if self.analyzer is None:
            self.analyzer = _get_vader()
        return self.analyzer is not None
    
    def analyze(self, text: str, conversation_history: Optional[List[str]] = None) -> SentimentResult:
        """
        Analyze sentiment of user message.
        
        Args:
            text: The user's message
            conversation_history: Recent messages for context
        
        Returns:
            SentimentResult with analysis and recommendations
        """
        if not text:
            return SentimentResult()
            
        text_lower = text.lower()
        
        # VADER analysis (if available)
        if self._ensure_analyzer():
            try:
                scores = self.analyzer.polarity_scores(text)
                compound = scores['compound']
                positive = scores['pos']
                negative = scores['neg']
                neutral = scores['neu']
            except Exception as e:
                logger.warning(f"VADER analysis failed: {e}")
                compound, positive, negative, neutral = self._fallback_analysis(text_lower)
        else:
            # Fallback: simple rule-based
            compound, positive, negative, neutral = self._fallback_analysis(text_lower)
        
        # Pattern-based detection
        is_frustrated = self._matches_patterns(text_lower, self.FRUSTRATION_PATTERNS)
        is_confused = self._matches_patterns(text_lower, self.CONFUSION_PATTERNS)
        is_anxious = self._matches_patterns(text_lower, self.ANXIETY_PATTERNS)
        is_urgent = self._matches_patterns(text_lower, self.URGENCY_PATTERNS)
        is_positive = self._matches_patterns(text_lower, self.POSITIVE_PATTERNS) or compound > 0.5
        
        # Check conversation history for sustained negative sentiment
        sustained_frustration = False
        if conversation_history and len(conversation_history) >= 2:
            recent_neg = sum(1 for msg in conversation_history[-3:] 
                           if self._matches_patterns(msg.lower(), self.FRUSTRATION_PATTERNS))
            sustained_frustration = recent_neg >= 2
        
        # Determine overall mood
        mood = self._determine_mood(
            compound, is_frustrated, is_confused, is_anxious, is_positive
        )
        
        # Determine tone adjustment
        tone_adjustment = self._get_tone_adjustment(
            mood, is_frustrated, is_confused, is_anxious, is_urgent
        )
        
        # Should we suggest human advisor?
        suggest_human = self._should_suggest_human(
            is_frustrated, is_anxious, sustained_frustration, compound
        )
        
        # Confidence in analysis
        confidence = self._calculate_confidence(compound, text)
        
        return SentimentResult(
            compound=round(compound, 3),
            positive=round(positive, 3),
            negative=round(negative, 3),
            neutral=round(neutral, 3),
            is_frustrated=is_frustrated or sustained_frustration,
            is_confused=is_confused,
            is_anxious=is_anxious,
            is_positive=is_positive,
            is_urgent=is_urgent,
            mood=mood,
            confidence=round(confidence, 2),
            tone_adjustment=tone_adjustment,
            suggest_human_advisor=suggest_human,
        )
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the patterns."""
        for pattern in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except re.error:
                continue
        return False
    
    def _fallback_analysis(self, text: str) -> tuple:
        """Simple fallback sentiment analysis without VADER."""
        positive_words = ['good', 'great', 'thanks', 'helpful', 'awesome', 'excellent', 'love', 'nice', 'cool']
        negative_words = ['bad', 'hate', 'terrible', 'worst', 'angry', 'frustrated', 'confused', 'difficult', 'hard']
        
        words = text.lower().split()
        pos_count = sum(1 for w in words if w in positive_words)
        neg_count = sum(1 for w in words if w in negative_words)
        total = len(words) if words else 1
        
        positive = min(pos_count / total, 1.0)
        negative = min(neg_count / total, 1.0)
        neutral = max(0, 1 - positive - negative)
        compound = (positive - negative)  # Range: -1 to 1
        
        return compound, positive, negative, neutral
    
    def _determine_mood(
        self,
        compound: float,
        is_frustrated: bool,
        is_confused: bool,
        is_anxious: bool,
        is_positive: bool
    ) -> str:
        """Determine overall mood category."""
        if is_frustrated:
            return "frustrated"
        if is_confused:
            return "confused"
        if is_anxious:
            return "anxious"
        if is_positive or compound > 0.3:
            return "positive"
        if compound < -0.3:
            return "negative"
        return "neutral"
    
    def _get_tone_adjustment(
        self,
        mood: str,
        is_frustrated: bool,
        is_confused: bool,
        is_anxious: bool,
        is_urgent: bool
    ) -> str:
        """Determine how to adjust response tone."""
        if is_frustrated:
            return "empathetic"
        if is_confused:
            return "patient"
        if is_anxious or is_urgent:
            return "reassuring"
        if mood == "positive":
            return "encouraging"
        return "normal"
    
    def _should_suggest_human(
        self,
        is_frustrated: bool,
        is_anxious: bool,
        sustained_frustration: bool,
        compound: float
    ) -> bool:
        """Determine if we should suggest talking to a human advisor."""
        return (
            sustained_frustration or
            (is_anxious and compound < -0.3) or
            compound < -0.6
        )
    
    def _calculate_confidence(self, compound: float, text: str) -> float:
        """Calculate confidence in sentiment analysis."""
        word_count = len(text.split())
        length_factor = min(word_count / 10, 1.0)
        sentiment_factor = abs(compound)
        confidence = (length_factor * 0.4 + sentiment_factor * 0.6)
        return min(max(confidence, 0.3), 1.0)
    
    def get_adaptive_intro(self, sentiment: SentimentResult) -> str:
        """Get an adaptive introduction based on sentiment."""
        if sentiment.is_frustrated:
            return "I understand this might be frustrating. Let me help you with that. "
        if sentiment.is_confused:
            return "No worries, let me explain this clearly. "
        if sentiment.is_anxious:
            return "I can see this is important to you. Don't worry, I'll help. "
        if sentiment.is_urgent:
            return "I'll get you the information you need right away. "
        if sentiment.is_positive:
            return "Great question! "
        return ""
    
    def get_advisor_suggestion(self, sentiment: SentimentResult) -> Optional[Dict[str, str]]:
        """Get human advisor suggestion if needed."""
        if not sentiment.suggest_human_advisor:
            return None
        
        return {
            "message": "💡 For complex or personal academic concerns, consider speaking with a human advisor.",
            "action": "Schedule a meeting with your faculty advisor",
            "reason": "human_escalation"
        }


# ══════════════════════════════════════════════════════════
# SINGLETON INSTANCE AND GETTER FUNCTION
# ══════════════════════════════════════════════════════════

_sentiment_service: Optional[SentimentService] = None


def get_sentiment_service() -> SentimentService:
    """Get or create sentiment service singleton."""
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = SentimentService()
    return _sentiment_service


# Export for convenience
__all__ = ['SentimentService', 'SentimentResult', 'get_sentiment_service']