# app/schemas/recommendation_schemas.py
"""
Enhanced Pydantic schemas for recommendation API
Includes Open Elective support for Semester VII
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ==================== SCORE BREAKDOWN SCHEMAS ====================

class SubjectContributionSchema(BaseModel):
    subject: str
    score: float
    weight: float
    contribution: float
    status: str


class AcademicComponentSchema(BaseModel):
    score: float = 0.0
    max_possible: float = 40.0
    percentage: float = 0.0
    contributing_subjects: List[Dict[str, Any]] = Field(default_factory=list)
    missing_subjects: List[Dict[str, Any]] = Field(default_factory=list)
    strong_subjects: List[str] = Field(default_factory=list)
    weak_subjects: List[str] = Field(default_factory=list)


class InterestComponentSchema(BaseModel):
    score: float = 0.0
    max_possible: float = 30.0
    percentage: float = 0.0
    matched_interests: List[Dict[str, Any]] = Field(default_factory=list)
    unmatched_interests: List[Dict[str, Any]] = Field(default_factory=list)
    semantic_similarity: float = 0.0


class ProjectComponentSchema(BaseModel):
    score: float = 0.0
    max_possible: float = 30.0
    percentage: float = 0.0
    relevant_projects: List[Dict[str, Any]] = Field(default_factory=list)
    keyword_hits: int = 0
    missing_project_skills: List[str] = Field(default_factory=list)
    average_complexity: float = 0.0
    total_projects_analyzed: int = 0


class ScoreBreakdownSchema(BaseModel):
    academic_component: AcademicComponentSchema = Field(default_factory=AcademicComponentSchema)
    interest_component: InterestComponentSchema = Field(default_factory=InterestComponentSchema)
    project_component: ProjectComponentSchema = Field(default_factory=ProjectComponentSchema)


class RankingExplanationSchema(BaseModel):
    rank: int = 0
    total_options: int = 0
    why_this_rank: str = ""
    vs_other_electives: List[Dict[str, Any]] = Field(default_factory=list)
    improvement_tips: List[str] = Field(default_factory=list)


class ConfidenceMetricsSchema(BaseModel):
    overall: float = 0.0
    data_completeness: float = 0.0
    model_confidence: float = 0.0
    factors: Dict[str, Any] = Field(default_factory=dict)


# ==================== REQUEST SCHEMAS ====================

class GenerateRecommendationsRequest(BaseModel):
    include_electives: bool = True
    include_open_electives: bool = True
    include_honours: bool = True
    include_career: bool = True
    use_transformer: bool = True
    use_knn: bool = True
    use_logistic: bool = True
    force_refresh: bool = False


class RecommendationFeedbackRequest(BaseModel):
    type: str
    recommendation_id: str
    rating: int = Field(ge=1, le=5)
    feedback: str = ""
    timestamp: Optional[str] = None


class RefreshRecommendationsRequest(BaseModel):
    update_basis: List[str] = Field(default=["interests", "marks", "projects"])


class ManualMarksInput(BaseModel):
    marks: Dict[str, float]
    interests: List[str] = Field(default_factory=list)
    semester: int = 5


# ==================== RESPONSE SCHEMAS ====================

class RecommendationBasisResponse(BaseModel):
    interests_weight: float = 0.0
    performance_weight: float = 0.0
    projects_weight: float = 0.0


class SkillGapSchema(BaseModel):
    subject: str
    current_score: float
    target_score: float = 60.0
    gap: float
    importance: str = "Medium"


class ElectiveRecommendationResponse(BaseModel):
    elective_code: str
    elective_name: str
    credits: int = 3
    match_score: float
    score_breakdown: Optional[ScoreBreakdownSchema] = None
    ranking_explanation: Optional[RankingExplanationSchema] = None
    confidence: Optional[ConfidenceMetricsSchema] = None
    match_explanation: str = ""
    prerequisites_met: bool = True
    skill_alignment: List[str] = Field(default_factory=list)
    career_relevance: List[str] = Field(default_factory=list)
    recommendation_basis: RecommendationBasisResponse = Field(default_factory=RecommendationBasisResponse)
    pair: Optional[str] = None
    skill_gaps: List[SkillGapSchema] = Field(default_factory=list)


class OpenElectiveRecommendationResponse(BaseModel):
    """Response schema for Semester-VII Open Elective recommendations."""
    elective_code: str
    elective_name: str
    credits: int = 3
    semester: int = 7
    category: str = "Open Elective"
    match_score: float
    score_breakdown: Optional[ScoreBreakdownSchema] = None
    ranking_explanation: Optional[RankingExplanationSchema] = None
    confidence: Optional[ConfidenceMetricsSchema] = None
    match_explanation: str = ""
    prerequisites_met: bool = True
    skill_alignment: List[str] = Field(default_factory=list)
    career_relevance: List[str] = Field(default_factory=list)
    modules: List[str] = Field(default_factory=list)
    recommendation_basis: RecommendationBasisResponse = Field(default_factory=RecommendationBasisResponse)
    skill_gaps: List[SkillGapSchema] = Field(default_factory=list)


class HonoursScoreBreakdownSchema(BaseModel):
    academic_score: float = 0.0
    interest_score: float = 0.0
    project_score: float = 0.0
    matched_subjects: List[Dict[str, Any]] = Field(default_factory=list)
    matched_interests: List[str] = Field(default_factory=list)
    relevant_projects: List[Dict[str, Any]] = Field(default_factory=list)


class HonoursRecommendationResponse(BaseModel):
    program: str
    type: str
    match_score: float
    eligibility: bool
    required_cgpa: float
    career_paths: List[str] = Field(default_factory=list)
    explanation: str = ""
    skills_gained: List[str] = Field(default_factory=list)
    score_breakdown: Optional[HonoursScoreBreakdownSchema] = None


class CareerScoreBreakdownSchema(BaseModel):
    interest_score: float = 0.0
    project_score: float = 0.0
    cgpa_score: float = 0.0
    matched_interests: List[str] = Field(default_factory=list)
    relevant_projects: List[Dict[str, Any]] = Field(default_factory=list)


class CareerRecommendationResponse(BaseModel):
    career: str
    match_score: float
    cgpa_eligible: bool
    required_cgpa: float
    salary_range: str = ""
    growth_potential: str = ""
    top_companies: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    preparation_path: List[str] = Field(default_factory=list)
    required_certifications: List[str] = Field(default_factory=list)
    score_breakdown: Optional[CareerScoreBreakdownSchema] = None


class CumulativeRecommendationResponse(BaseModel):
    electives: List[ElectiveRecommendationResponse] = Field(default_factory=list)
    open_electives: List[OpenElectiveRecommendationResponse] = Field(default_factory=list)
    honours: List[HonoursRecommendationResponse] = Field(default_factory=list)
    careers: List[CareerRecommendationResponse] = Field(default_factory=list)
    model_info: Dict[str, Any] = Field(default_factory=dict)
    computation_time_ms: float = 0.0
    data_summary: Optional[Dict[str, Any]] = None


# ==================== PROJECT ANALYSIS RESPONSE ====================

class InferredInterestSchema(BaseModel):
    domain: str
    confidence: float
    matched_keywords: List[str] = Field(default_factory=list)
    source: str = "project_analysis"


class ProjectAnalysisResultSchema(BaseModel):
    extracted_skills: List[str] = Field(default_factory=list)
    complexity_score: float = 0.0
    inferred_interests: List[InferredInterestSchema] = Field(default_factory=list)


class ComprehensiveProjectAnalysisResponse(BaseModel):
    success: bool = True
    project_analysis: ProjectAnalysisResultSchema
    cumulative_recommendations: CumulativeRecommendationResponse
    data_summary: Dict[str, Any] = Field(default_factory=dict)
    model_info: Dict[str, Any] = Field(default_factory=dict)
    student_info: Dict[str, Any] = Field(default_factory=dict)
    generated_at: str = ""


class TrainingMetricsResponse(BaseModel):
    accuracy: float
    f1_macro: float
    f1_weighted: float
    per_class: Dict[str, Dict[str, float]]
    cross_val_mean: float
    cross_val_std: float
    confusion_matrix: List[List[int]]
    n_training_samples: int
    n_test_samples: int
    model_type: str
    timestamp: str


class ModelInfoResponse(BaseModel):
    is_trained: bool
    model_version: str
    models_available: List[str]
    last_trained: Optional[str] = None
    training_accuracy: Optional[float] = None