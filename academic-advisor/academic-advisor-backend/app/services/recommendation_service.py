# app/services/recommendation_service.py
"""
Recommendation Service - Unified orchestrator
Fetches student data → calls ML engine → stores results → handles feedback
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.ml.models.recommendation_engine import recommendation_engine
from app.models.student_profile import StudentProfile
from app.models.student_projects import StudentProject, StudentInterestProfile
from app.models.recommendation import (
    RecommendationRecord, RecommendationFeedback,
    ElectiveDetail, HonoursDetail, CareerDetail, RecommendationType
)
from app.schemas.recommendation_schemas import (
    CumulativeRecommendationResponse,
    ElectiveRecommendationResponse,
    HonoursRecommendationResponse,
    CareerRecommendationResponse,
    RecommendationBasisResponse,
)

logger = logging.getLogger(__name__)


class RecommendationService:
    """Orchestrates recommendation generation from all data sources."""

    def __init__(self):
        self.engine = recommendation_engine

    async def get_student_data(self, student_id: str) -> Dict[str, Any]:
        """Fetch all student data needed for recommendations."""
        data = {
            'marks': {},
            'interests': [],
            'projects': [],
            'cgpa': 0.0,
            'semester': 4,
            'project_skills': [],
        }

        try:
            # 1. Get academic profile
            profile = await StudentProfile.find_one(
                StudentProfile.user_id == student_id
            )
            if profile:
                data['cgpa'] = profile.cgpa or 0.0
                data['semester'] = profile.current_semester or 4
                data['interests'] = list(profile.interests or [])

                # Extract marks from semester records
                for sem_record in (profile.semester_records or []):
                    for subj in (sem_record.subjects or []):
                        current = data['marks'].get(subj.subject_name, 0)
                        data['marks'][subj.subject_name] = max(current, subj.total_marks)

            # 2. Get interest profile (separate collection)
            try:
                interest_profile = await StudentInterestProfile.find_one(
                    StudentInterestProfile.student_id == student_id
                )
                if interest_profile:
                    primary = []
                    for domain in (getattr(interest_profile, 'primary_domains', []) or []):
                        if isinstance(domain, dict):
                            primary.append(domain.get('domain', domain.get('name', '')))
                        elif isinstance(domain, str):
                            primary.append(domain)
                    secondary = getattr(interest_profile, 'secondary_interests', []) or []
                    data['interests'] = list(set(data['interests'] + primary + secondary))
            except Exception as e:
                logger.warning(f"Could not fetch interest profile: {e}")

            # 3. Get projects
            projects = await StudentProject.find(
                StudentProject.student_id == student_id
            ).to_list()

            all_project_skills = []
            data['projects'] = []
            for p in projects:
                proj_dict = {
                    'title': p.title,
                    'description': p.description or '',
                    'programming_languages': p.programming_languages or [],
                    'frameworks': p.frameworks or [],
                    'tools': p.tools or [],
                    'technologies': p.technologies or [],
                    'extracted_skills': p.extracted_skills or [],
                    'is_team_project': p.is_team_project,
                    'complexity_score': p.complexity_score or 0.5,
                    'github_url': p.github_url,
                    'demo_url': p.demo_url,
                }
                data['projects'].append(proj_dict)
                all_project_skills.extend(p.extracted_skills or [])
                all_project_skills.extend(p.programming_languages or [])
                all_project_skills.extend(p.frameworks or [])

            data['project_skills'] = list(set(all_project_skills))

            logger.info(
                f"Fetched data for {student_id}: {len(data['marks'])} subjects, "
                f"{len(data['interests'])} interests, {len(data['projects'])} projects"
            )

        except Exception as e:
            logger.error(f"Error fetching student data: {e}", exc_info=True)

        return data

    async def generate_recommendations(
        self,
        student_id: str,
        include_electives: bool = True,
        include_honours: bool = True,
        include_career: bool = True,
        force_refresh: bool = False,
    ) -> CumulativeRecommendationResponse:
        """Generate cumulative recommendations from all sources."""
        start_time = time.time()

        # Check for cached recommendations (unless force refresh)
        if not force_refresh:
            try:
                cached = await RecommendationRecord.find_one(
                    RecommendationRecord.student_id == student_id,
                    RecommendationRecord.is_active == True,
                ).sort(-RecommendationRecord.created_at)

                if cached:
                    age = (datetime.utcnow() - cached.created_at).total_seconds()
                    if age < 3600:
                        return self._format_cached(cached)
            except Exception as e:
                logger.warning(f"Could not check cache: {e}")

        # Fetch fresh data
        student_data = await self.get_student_data(student_id)

        electives_resp: List[ElectiveRecommendationResponse] = []
        honours_resp: List[HonoursRecommendationResponse] = []
        careers_resp: List[CareerRecommendationResponse] = []
        models_used = ['Rule-Based']

        # Generate elective recommendations
        if include_electives:
            raw_electives = self.engine.recommend_electives(
                marks=student_data['marks'],
                interests=student_data['interests'],
                projects=student_data['projects'],
                cgpa=student_data['cgpa'],
                use_ml=self.engine.is_trained,
            )
            for e in raw_electives:
                electives_resp.append(ElectiveRecommendationResponse(
                    elective_code=e['elective_code'],
                    elective_name=e['elective_name'],
                    credits=e['credits'],
                    match_score=e['match_score'],
                    match_explanation=e.get('match_explanation', ''),
                    prerequisites_met=e.get('prerequisites_met', True),
                    skill_alignment=e.get('skill_alignment', []),
                    career_relevance=e.get('career_relevance', []),
                    recommendation_basis=RecommendationBasisResponse(
                        interests_weight=e.get('recommendation_basis', {}).get('interests_weight', 0),
                        performance_weight=e.get('recommendation_basis', {}).get('performance_weight', 0),
                        projects_weight=e.get('recommendation_basis', {}).get('projects_weight', 0),
                    ),
                    pair=e.get('pair'),
                    skill_gaps=e.get('skill_gaps', []),
                    score_breakdown=e.get('score_breakdown'),
                    ranking_explanation=e.get('ranking_explanation'),
                    confidence=e.get('confidence'),
                ))
            if self.engine.is_trained:
                models_used = ['RandomForest', 'KNN', 'Rule-Based']

        # Generate honours recommendations
        if include_honours:
            raw_honours = self.engine.recommend_honours(
                marks=student_data['marks'],
                interests=student_data['interests'],
                projects=student_data['projects'],
                cgpa=student_data['cgpa'],
            )

            # Apply branch-specific classification
            from app.core.subject_mappings import get_programme_type_for_branch

            # Get student branch
            student_branch = 'IT'  # Default
            try:
                profile = await StudentProfile.find_one(
                    StudentProfile.user_id == student_id
                )
                if profile and profile.branch:
                    student_branch = profile.branch.upper()
            except:
                pass

            for h in raw_honours:
                # Override type based on branch-specific rules
                programme_name = h.get('program', '')
                correct_type = get_programme_type_for_branch(programme_name, student_branch)
                h['type'] = correct_type

                honours_resp.append(HonoursRecommendationResponse(**h))

        # Generate career recommendations
        if include_career:
            raw_careers = self.engine.recommend_careers(
                marks=student_data['marks'],
                interests=student_data['interests'],
                projects=student_data['projects'],
                cgpa=student_data['cgpa'],
            )
            for c in raw_careers:
                careers_resp.append(CareerRecommendationResponse(**c))

        computation_time = (time.time() - start_time) * 1000

        # Store recommendation record
        try:
            record = RecommendationRecord(
                student_id=student_id,
                input_marks=student_data['marks'],
                input_interests=student_data['interests'],
                input_project_count=len(student_data['projects']),
                cgpa=student_data['cgpa'],
                semester=student_data['semester'],
                electives=[ElectiveDetail(**e.model_dump()) for e in electives_resp],
                honours=[HonoursDetail(**h.model_dump()) for h in honours_resp],
                careers=[CareerDetail(**c.model_dump()) for c in careers_resp],
                models_used=models_used,
                computation_time_ms=computation_time,
            )
            await record.insert()
        except Exception as e:
            logger.error(f"Failed to store recommendation record: {e}")

        return CumulativeRecommendationResponse(
            electives=electives_resp,
            honours=honours_resp,
            careers=careers_resp,
            model_info={
                'models_used': models_used,
                'is_ml_trained': self.engine.is_trained,
                'version': '2.0.0',
            },
            computation_time_ms=computation_time,
            data_summary={
                'total_marks_subjects': len(student_data['marks']),
                'total_interests': len(student_data['interests']),
                'total_projects': len(student_data['projects']),
                'cgpa': student_data['cgpa'],
            },
        )

    def _format_cached(self, cached: RecommendationRecord) -> CumulativeRecommendationResponse:
        """Format cached record as response."""
        electives = []
        for e in (cached.electives or []):
            basis = e.recommendation_basis or {}
            electives.append(ElectiveRecommendationResponse(
                elective_code=e.elective_code,
                elective_name=e.elective_name,
                credits=e.credits,
                match_score=e.match_score,
                match_explanation=e.match_explanation or '',
                prerequisites_met=e.prerequisites_met,
                skill_alignment=e.skill_alignment,
                career_relevance=e.career_relevance,
                recommendation_basis=RecommendationBasisResponse(
                    interests_weight=basis.get('interests_weight', 0),
                    performance_weight=basis.get('performance_weight', 0),
                    projects_weight=basis.get('projects_weight', 0),
                ),
                pair=e.pair,
                skill_gaps=e.skill_gaps or [],
                score_breakdown=e.score_breakdown,
                ranking_explanation=e.ranking_explanation,
                confidence=e.confidence,
            ))

        honours = [HonoursRecommendationResponse(**h.model_dump()) for h in (cached.honours or [])]
        careers = [CareerRecommendationResponse(**c.model_dump()) for c in (cached.careers or [])]

        return CumulativeRecommendationResponse(
            electives=electives,
            honours=honours,
            careers=careers,
            model_info={
                'models_used': cached.models_used,
                'cached': True,
                'cached_at': cached.created_at.isoformat(),
                'is_ml_trained': self.engine.is_trained,
                'version': '2.0.0',
            },
            computation_time_ms=cached.computation_time_ms,
        )

    async def record_feedback(
        self,
        student_id: str,
        recommendation_type: str,
        recommendation_id: str,
        rating: int,
        feedback_text: str = "",
    ) -> None:
        """Record user feedback WITH full student context for real retraining."""
        try:
            # Fetch current student data for context
            student_data = await self.get_student_data(student_id)

            feedback = RecommendationFeedback(
                student_id=student_id,
                recommendation_type=RecommendationType(recommendation_type),
                recommendation_id=recommendation_id,
                item_name=recommendation_id,
                rating=rating,
                feedback_text=feedback_text,
                student_cgpa=student_data['cgpa'],
                student_semester=student_data['semester'],
                student_marks=student_data['marks'],
                student_interests=student_data['interests'],
                student_project_skills=student_data.get('project_skills', []),
                student_project_count=len(student_data['projects']),
            )
            await feedback.insert()
            logger.info(f"Recorded feedback for {student_id}: {recommendation_type} - rating {rating}")
        except Exception as e:
            logger.error(f"Failed to record feedback: {e}")
            raise

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the recommendation model."""
        feedback_count = 0
        try:
            feedback_count = await RecommendationFeedback.count()
        except Exception:
            pass

        return {
            'is_trained': self.engine.is_trained,
            'model_version': '2.0.0',
            'models_available': ['Rule-Based', 'RandomForest', 'KNN'],
            'feature_dimension': 35,
            'electives_supported': ['ML', 'WT', 'DWM', 'CCS'],
            'total_feedback_collected': feedback_count,
        }


# Singleton
recommendation_service = RecommendationService()