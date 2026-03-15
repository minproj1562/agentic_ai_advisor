# app/services/chatbot/__init__.py
"""
Chatbot Services Package
Optimized with lazy loading for fast startup
"""

from .chatbot_service import ChatbotService
from .intent_classifier import IntentClassifier, IntentType
from .context_manager import ContextManager
from .response_generator import ResponseGenerator

# Lazy imports for optional services
def get_llm_service():
    from .llm_service import get_llm_service as _get
    return _get()

def get_sentiment_service():
    from .sentiment_service import get_sentiment_service as _get
    return _get()

def get_cache_service():
    from .cache_service import get_cache_service as _get
    return _get()

def get_student_data_service():
    from .student_data_service import get_student_data_service as _get
    return _get()

__all__ = [
    "ChatbotService",
    "IntentClassifier",
    "IntentType",
    "ContextManager",
    "ResponseGenerator",
    "get_llm_service",
    "get_sentiment_service",
    "get_cache_service",
    "get_student_data_service",
]