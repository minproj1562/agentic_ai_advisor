# academic-advisor/academic-advisor-backend/app/ml/preprocessors/data_preprocessor.py
"""
Data preprocessor for recommendation model
Handles canonicalization, normalization, and validation
"""

from typing import Dict, List, Any
from app.ml.models.recommendation_engine import _canonicalise_marks, _normalise_interests


def preprocess_student_data(
    marks: Dict[str, float],
    interests: Any,
    projects: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Preprocess raw student data for the recommendation engine."""
    return {
        'marks': _canonicalise_marks(marks),
        'interests': _normalise_interests(interests),
        'projects': _validate_projects(projects),
    }


def _validate_projects(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure all project dicts have required fields."""
    validated = []
    for p in projects:
        validated.append({
            'title': p.get('title', 'Untitled'),
            'description': p.get('description', ''),
            'programming_languages': p.get('programming_languages', []),
            'frameworks': p.get('frameworks', []),
            'tools': p.get('tools', []),
            'technologies': p.get('technologies', []),
            'extracted_skills': p.get('extracted_skills', []),
            'is_team_project': p.get('is_team_project', False),
            'complexity_score': p.get('complexity_score', 0.5),
            'github_url': p.get('github_url'),
            'demo_url': p.get('demo_url'),
        })
    return validated