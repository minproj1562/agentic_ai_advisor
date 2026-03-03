# app/services/student_projects_service.py
"""
Student Projects Service
Fixed: Removed non-existent import, uses inline skill extraction
"""

import os
import aiofiles
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from collections import Counter, defaultdict
import numpy as np

from app.models.student_projects import (
    StudentProject,
    StudentInterestProfile,
    ProjectFile
)

logger = logging.getLogger(__name__)


class StudentProjectsService:
    def __init__(self):
        self.upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

    async def save_project_file(self, file, student_id: str) -> ProjectFile:
        """Save uploaded file and return file metadata"""
        try:
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{student_id}_{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(self.upload_dir, unique_filename)

            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)

            return ProjectFile(
                filename=file.filename,
                file_type=file.content_type,
                file_size=len(content),
                storage_path=file_path
            )
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise

    async def delete_project_file(self, file_path: str):
        """Delete project file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Error deleting file: {e}")

    def extract_skills(self, project_data: Dict[str, Any]) -> List[str]:
        """Extract skills from project data"""
        skills = set()

        skills.update(project_data.get('programming_languages', []))
        skills.update(project_data.get('frameworks', []))
        skills.update(project_data.get('tools', []))
        skills.update(project_data.get('technologies', []))

        text = ' '.join([
            project_data.get('description', ''),
            project_data.get('detailed_description', '')
        ]).lower()

        skill_patterns = {
            "api": "API Development",
            "database": "Database Management",
            "testing": "Testing",
            "deployment": "Deployment",
            "optimization": "Optimization",
            "design": "System Design",
            "architecture": "Architecture",
            "security": "Security",
            "machine learning": "Machine Learning",
            "deep learning": "Deep Learning",
            "docker": "Docker",
            "kubernetes": "Kubernetes",
            "aws": "AWS",
            "react": "React",
        }

        for pattern, skill_name in skill_patterns.items():
            if pattern in text:
                skills.add(skill_name)

        return list(skills)

    def calculate_complexity(self, project_data: Dict[str, Any]) -> float:
        """Calculate project complexity score"""
        score = 0.0

        tech_count = (
            len(project_data.get('programming_languages', [])) +
            len(project_data.get('frameworks', [])) +
            len(project_data.get('tools', []))
        )
        score += min(tech_count * 0.05, 0.3)

        if project_data.get('is_team_project'):
            team_size = project_data.get('team_size', 1)
            score += min(team_size * 0.05, 0.2)

        if project_data.get('start_date') and project_data.get('end_date'):
            try:
                start = datetime.fromisoformat(str(project_data['start_date']))
                end = datetime.fromisoformat(str(project_data['end_date']))
                duration_months = (end - start).days / 30
                score += min(duration_months * 0.05, 0.25)
            except Exception:
                pass

        achievements = len(project_data.get('key_achievements', []))
        score += min(achievements * 0.05, 0.15)

        challenges = len(project_data.get('challenges_faced', []))
        score += min(challenges * 0.03, 0.1)

        return min(score, 1.0)

    def infer_interests(self, project_data: Dict[str, Any], skills: List[str]) -> List[Dict[str, Any]]:
        """Infer interests from project data - replaces broken InterestInferenceEngine"""
        from app.services.enhanced_ml_inference import INTEREST_PATTERNS

        text_blob = " ".join([
            project_data.get('title', ''),
            project_data.get('description', ''),
            project_data.get('detailed_description', ''),
            " ".join(skills),
        ]).lower()

        results = []
        for domain, info in INTEREST_PATTERNS.items():
            matches = [kw for kw in info["keywords"] if kw in text_blob]
            if not matches:
                continue
            confidence = min(len(matches) / 4.0, 1.0)
            if confidence < 0.2:
                continue
            results.append({
                "domain": domain,
                "confidence": round(confidence, 2),
                "matched_keywords": matches[:8],
                "relatedSkills": info["related_skills"],
                "careerPaths": info["career_paths"],
                "industryRelevance": info["industry_relevance"],
            })

        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results[:4]

    async def update_interest_profile(
        self,
        student_id: str,
        new_interests: List[Dict[str, Any]]
    ):
        """Update student's interest profile"""
        try:
            profile = await StudentInterestProfile.find_one(
                StudentInterestProfile.student_id == student_id
            )

            if not profile:
                profile = StudentInterestProfile(student_id=student_id)

            projects = await StudentProject.find(
                StudentProject.student_id == student_id
            ).to_list()

            profile.total_projects = len(projects)

            project_types = Counter(
                p.project_type.value if hasattr(p.project_type, 'value') else str(p.project_type)
                for p in projects
            )
            profile.projects_by_type = dict(project_types)

            complexities = [p.complexity_score for p in projects if p.complexity_score]
            profile.average_project_complexity = float(np.mean(complexities)) if complexities else 0.0

            # Aggregate all skills
            all_skills = Counter()
            for project in projects:
                all_skills.update(project.extracted_skills or [])

            profile.technical_skills = {
                skill: count / max(len(projects), 1)
                for skill, count in all_skills.most_common(20)
            }

            profile.consistency_score = self._calculate_consistency(projects)
            profile.last_updated = datetime.now()

            await profile.save()

        except Exception as e:
            logger.error(f"Error updating interest profile: {e}")

    def _calculate_consistency(self, projects: List[StudentProject]) -> float:
        """Calculate consistency score across projects"""
        if len(projects) < 2:
            return 1.0

        project_domains = []
        for project in projects:
            domains = set()
            for i in (project.inferred_interests or []):
                if hasattr(i, 'domain'):
                    domains.add(i.domain)
                elif isinstance(i, dict):
                    domains.add(i.get('domain', ''))
            project_domains.append(domains)

        total_overlap = 0
        comparisons = 0

        for i in range(len(project_domains)):
            for j in range(i + 1, len(project_domains)):
                if project_domains[i] and project_domains[j]:
                    overlap = len(project_domains[i] & project_domains[j])
                    total = len(project_domains[i] | project_domains[j])
                    total_overlap += overlap / total if total > 0 else 0
                    comparisons += 1

        return total_overlap / comparisons if comparisons > 0 else 0.5

    async def calculate_statistics(self, student_id: str) -> Dict[str, Any]:
        """Calculate detailed statistics for student projects"""
        try:
            projects = await StudentProject.find(
                StudentProject.student_id == student_id
            ).to_list()

            if not projects:
                return {
                    "total_projects": 0,
                    "languages_used": [],
                    "frameworks_used": [],
                    "average_complexity": 0,
                    "total_achievements": 0,
                    "project_timeline": []
                }

            all_languages = Counter()
            all_frameworks = Counter()
            all_tools = Counter()
            total_achievements = 0

            for project in projects:
                all_languages.update(project.programming_languages or [])
                all_frameworks.update(project.frameworks or [])
                all_tools.update(project.tools or [])
                total_achievements += len(project.key_achievements or [])

            timeline = [
                {
                    "date": project.created_at.isoformat(),
                    "title": project.title,
                    "type": project.project_type.value if hasattr(project.project_type, 'value') else str(project.project_type),
                }
                for project in sorted(projects, key=lambda p: p.created_at)
            ]

            complexities = [p.complexity_score for p in projects if p.complexity_score]

            return {
                "total_projects": len(projects),
                "languages_used": list(all_languages.most_common(10)),
                "frameworks_used": list(all_frameworks.most_common(10)),
                "tools_used": list(all_tools.most_common(10)),
                "average_complexity": float(np.mean(complexities)) if complexities else 0.0,
                "total_achievements": total_achievements,
                "project_timeline": timeline,
                "projects_by_type": dict(
                    Counter(
                        p.project_type.value if hasattr(p.project_type, 'value') else str(p.project_type)
                        for p in projects
                    )
                ),
                "total_team_projects": sum(1 for p in projects if p.is_team_project),
            }

        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}


# Singleton
student_projects_service = StudentProjectsService()