# academic-advisor/academic-advisor-backend/app/ml/preprocessors/feature_engineering.py
"""
Feature engineering for recommendation model
Extracts and transforms features from student data
"""

from typing import Dict, List, Any
from app.ml.models.recommendation_engine import recommendation_engine


def extract_features(
    marks: Dict[str, float],
    interests: Any,
    projects: List[Dict[str, Any]],
) -> list:
    """Extract feature vector from student data."""
    return recommendation_engine.extract_features(marks, interests, projects).tolist()


def get_feature_names() -> List[str]:
    """Get human-readable feature names for interpretability."""
    from app.ml.models.recommendation_engine import CANONICAL_SUBJECTS, INTEREST_AREAS

    names = []
    # Subject marks
    for subj in CANONICAL_SUBJECTS:
        names.append(f"mark_{subj}")

    # Aggregates
    names.extend(["marks_mean", "marks_std", "marks_max", "marks_min"])

    # Interests
    for area in INTEREST_AREAS:
        names.append(f"interest_{area}")

    # Project features
    names.extend([
        "project_count_norm",
        "project_hits_ML", "project_hits_WT", "project_hits_DWM", "project_hits_CCS",
        "total_skills_norm", "team_ratio", "avg_complexity", "github_ratio", "demo_ratio",
    ])

    return names