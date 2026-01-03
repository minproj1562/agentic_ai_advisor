# app/services/student_projects_service.py
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
from app.services.ml_interest_inference import InterestInferenceEngine

logger = logging.getLogger(__name__)

class StudentProjectsService:
    def __init__(self):
        self.upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        self.inference_engine = InterestInferenceEngine()
        
        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def save_project_file(self, file, student_id: str) -> ProjectFile:
        """Save uploaded file and return file metadata"""
        try:
            # Generate unique filename
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{student_id}_{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(self.upload_dir, unique_filename)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Create file metadata
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
        
        # Add programming languages
        skills.update(project_data.get('programming_languages', []))
        
        # Add frameworks
        skills.update(project_data.get('frameworks', []))
        
        # Add tools
        skills.update(project_data.get('tools', []))
        
        # Extract skills from text using NLP
        text = ' '.join([
            project_data.get('description', ''),
            project_data.get('detailed_description', '')
        ])
        
        # Common skill patterns
        skill_patterns = [
            "api", "database", "testing", "deployment", "optimization",
            "design", "architecture", "security", "performance", "debugging"
        ]
        
        for pattern in skill_patterns:
            if pattern in text.lower():
                skills.add(pattern.title())
        
        return list(skills)
    
    def calculate_complexity(self, project_data: Dict[str, Any]) -> float:
        """Calculate project complexity score"""
        score = 0.0
        
        # Technical stack complexity
        tech_count = (
            len(project_data.get('programming_languages', [])) +
            len(project_data.get('frameworks', [])) +
            len(project_data.get('tools', []))
        )
        score += min(tech_count * 0.05, 0.3)
        
        # Team complexity
        if project_data.get('is_team_project'):
            team_size = project_data.get('team_size', 1)
            score += min(team_size * 0.05, 0.2)
        
        # Duration complexity
        if project_data.get('start_date') and project_data.get('end_date'):
            # Calculate duration in months
            start = datetime.fromisoformat(project_data['start_date'])
            end = datetime.fromisoformat(project_data['end_date'])
            duration_months = (end - start).days / 30
            score += min(duration_months * 0.05, 0.25)
        
        # Achievement complexity
        achievements = len(project_data.get('key_achievements', []))
        score += min(achievements * 0.05, 0.15)
        
        # Challenge complexity
        challenges = len(project_data.get('challenges_faced', []))
        score += min(challenges * 0.03, 0.1)
        
        return min(score, 1.0)
    
    async def update_interest_profile(
        self,
        student_id: str,
        new_interests: List[Dict[str, Any]]
    ):
        """Update student's interest profile"""
        try:
            # Get existing profile or create new
            profile = await StudentInterestProfile.find_one(
                StudentInterestProfile.student_id == student_id
            )
            
            if not profile:
                profile = StudentInterestProfile(student_id=student_id)
            
            # Get all projects
            projects = await StudentProject.find(
                StudentProject.student_id == student_id
            ).to_list()
            
            # Update statistics
            profile.total_projects = len(projects)
            
            # Count projects by type
            project_types = Counter(p.project_type for p in projects)
            profile.projects_by_type = dict(project_types)
            
            # Calculate average complexity
            complexities = [p.complexity_score for p in projects if p.complexity_score]
            profile.average_project_complexity = np.mean(complexities) if complexities else 0.0
            
            # Aggregate all interests
            all_interests = []
            for project in projects:
                all_interests.extend(project.inferred_interests)
            
            # Update profile with aggregated interests
            updated_profile = self.inference_engine.update_interest_profile(
                student_id,
                all_interests,
                profile.dict()
            )
            
            # Update profile fields
            for key, value in updated_profile.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            
            # Extract all skills
            all_skills = Counter()
            for project in projects:
                all_skills.update(project.extracted_skills)
            
            # Update technical skills
            profile.technical_skills = {
                skill: count / len(projects)
                for skill, count in all_skills.most_common(20)
            }
            
            # Calculate consistency score
            profile.consistency_score = self._calculate_consistency(projects)
            
            # Update timestamp
            profile.last_updated = datetime.now()
            
            await profile.save()
        
        except Exception as e:
            logger.error(f"Error updating interest profile: {e}")
    
    def _calculate_consistency(self, projects: List[StudentProject]) -> float:
        """Calculate consistency score across projects"""
        if len(projects) < 2:
            return 1.0
        
        # Get domains from all projects
        project_domains = []
        for project in projects:
            domains = [i['domain'] for i in project.inferred_interests[:2]]
            project_domains.append(set(domains))
        
        # Calculate overlap
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
    
    async def generate_interest_profile(self, student_id: str) -> StudentInterestProfile:
        """Generate interest profile from scratch"""
        try:
            profile = StudentInterestProfile(student_id=student_id)
            
            # Get all projects
            projects = await StudentProject.find(
                StudentProject.student_id == student_id
            ).to_list()
            
            if not projects:
                await profile.save()
                return profile
            
            # Process all projects
            await self.update_interest_profile(student_id, [])
            
            # Reload profile
            profile = await StudentInterestProfile.find_one(
                StudentInterestProfile.student_id == student_id
            )
            
            return profile
        
        except Exception as e:
            logger.error(f"Error generating interest profile: {e}")
            return StudentInterestProfile(student_id=student_id)
    
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
            
            # Aggregate statistics
            all_languages = Counter()
            all_frameworks = Counter()
            all_tools = Counter()
            total_achievements = 0
            
            for project in projects:
                all_languages.update(project.programming_languages)
                all_frameworks.update(project.frameworks)
                all_tools.update(project.tools)
                total_achievements += len(project.key_achievements)
            
            # Create timeline
            timeline = [
                {
                    "date": project.created_at.isoformat(),
                    "title": project.title,
                    "type": project.project_type
                }
                for project in sorted(projects, key=lambda p: p.created_at)
            ]
            
            return {
                "total_projects": len(projects),
                "languages_used": list(all_languages.most_common(10)),
                "frameworks_used": list(all_frameworks.most_common(10)),
                "tools_used": list(all_tools.most_common(10)),
                "average_complexity": np.mean([p.complexity_score for p in projects if p.complexity_score]),
                "total_achievements": total_achievements,
                "project_timeline": timeline,
                "projects_by_type": dict(Counter(p.project_type for p in projects)),
                "total_team_projects": sum(1 for p in projects if p.is_team_project),
                "most_common_domains": self._get_most_common_domains(projects)
            }
        
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
    
    def _get_most_common_domains(self, projects: List[StudentProject]) -> List[Dict[str, Any]]:
        """Get most common domains from projects"""
        domain_counter = Counter()
        
        for project in projects:
            for interest in project.inferred_interests:
                domain_counter[interest['domain']] += interest['confidence']
        
        return [
            {"domain": domain, "score": round(score, 2)}
            for domain, score in domain_counter.most_common(5)
        ]