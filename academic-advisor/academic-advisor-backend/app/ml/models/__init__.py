#academic-advisor/academic-advisor-backend/app/ml/models/__init__.py
"""
ML Models Package — Academic Advisor
"""

# Recommendation engine (always available)
from app.ml.models.recommendation_engine import recommendation_engine

# Performance predictor (may not have singleton yet)
try:
    from app.ml.models.performance_predictor import performance_predictor
except ImportError:
    performance_predictor = None

# Weakness detector (may not have singleton yet)
try:
    from app.ml.models.weakness_detector import weakness_detector
except ImportError:
    weakness_detector = None

__all__ = [
    "recommendation_engine",
    "performance_predictor",
    "weakness_detector",
]