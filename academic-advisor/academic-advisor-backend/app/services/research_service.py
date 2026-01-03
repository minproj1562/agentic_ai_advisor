# academic-advisor-backend/app/services/research_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict
import logging

from app.models.research_area import ResearchArea, ResearchCategory
from app.core.cache import cache
from app.services.skill_extractor import SkillExtractor

logger = logging.getLogger(__name__)

class ResearchAreaService:
    
    def __init__(self):
        self.skill_extractor = SkillExtractor()
    
    async def extract_research_areas_from_cv(self, cv_text: str, user_id: str) -> List[ResearchArea]:
        """
        Extract and create research areas from CV text
        """
        try:
            # Use skill extractor to get comprehensive research analysis
            analysis = await self.skill_extractor.extract_comprehensive(cv_text)
            
            research_areas = []
            
            for area_data in analysis.get('research_areas', []):
                # Create research area from extracted data
                research_area = await self._create_research_area_from_data(area_data, user_id, cv_text)
                if research_area:
                    research_areas.append(research_area)
            
            return research_areas
            
        except Exception as e:
            logger.error(f"Error extracting research areas from CV: {e}")
            return []
    
    async def _create_research_area_from_data(self, area_data: Dict[str, Any], user_id: str, cv_text: str) -> Optional[ResearchArea]:
        """
        Create ResearchArea object from extracted data
        """
        try:
            # Calculate initial metrics based on CV content
            publications = await self._estimate_publications(area_data, cv_text)
            citations = await self._estimate_citations(area_data, cv_text)
            
            research_area = ResearchArea(
                user_id=user_id,
                name=area_data['name'],
                category=ResearchCategory.PRIMARY if area_data.get('relevance_score', 0) > 70 else ResearchCategory.SECONDARY,
                description=f"Automatically extracted from CV: {area_data.get('matched_text', '')}",
                keywords=await self._generate_keywords(area_data, cv_text),
                publications=publications,
                citations=citations,
                grants=await self._estimate_grants(area_data, cv_text),
                grant_amount=0.0,  # Would need specific extraction
                collaborators=[],
                related_areas=[],
                publication_trend=[],
                citation_trend=[],
                technologies=await self._extract_technologies(area_data, cv_text),
                is_active=True
            )
            
            return research_area
            
        except Exception as e:
            logger.error(f"Error creating research area from data: {e}")
            return None
    
    async def analyze_cv_for_research_potential(self, cv_text: str) -> Dict[str, Any]:
        """
        Analyze CV for research potential and compatibility
        """
        analysis = await self.skill_extractor.extract_comprehensive(cv_text)
        research_profile = analysis.get('research_profile', {})
        
        return {
            "research_potential_score": research_profile.get('overall_score', 0),
            "primary_domains": research_profile.get('primary_domains', []),
            "technical_competencies": research_profile.get('technical_competencies', []),
            "research_maturity": research_profile.get('maturity_level', 'emerging'),
            "skill_gaps": await self._identify_skill_gaps(analysis),
            "recommendations": await self._generate_research_recommendations(analysis),
            "compatibility_analysis": await self._analyze_research_compatibility(analysis)
        }
    
    async def _estimate_publications(self, area_data: Dict[str, Any], cv_text: str) -> int:
        """
        Estimate publication count based on CV content
        """
        # Look for publication indicators
        publication_indicators = ['published', 'paper', 'journal', 'conference', 'proceedings']
        indicator_count = sum(1 for indicator in publication_indicators if indicator in cv_text.lower())
        
        # Simple estimation based on indicators and expertise
        base_estimate = indicator_count * 2
        expertise_boost = area_data.get('relevance_score', 0) / 10
        
        return int(base_estimate + expertise_boost)
    
    async def _estimate_citations(self, area_data: Dict[str, Any], cv_text: str) -> int:
        """
        Estimate citation count (very rough estimate)
        """
        publications = await self._estimate_publications(area_data, cv_text)
        return publications * 5  # Rough average
    
    async def _estimate_grants(self, area_data: Dict[str, Any], cv_text: str) -> int:
        """
        Estimate grant count
        """
        grant_indicators = ['grant', 'funding', 'award', 'fellowship', 'scholarship']
        indicator_count = sum(1 for indicator in grant_indicators if indicator in cv_text.lower())
        
        return indicator_count
    
    async def _generate_keywords(self, area_data: Dict[str, Any], cv_text: str) -> List[str]:
        """
        Generate relevant keywords for research area
        """
        keywords = [area_data['name'].lower()]
        
        # Extract additional keywords from context
        context_keywords = await self._extract_context_keywords(area_data, cv_text)
        keywords.extend(context_keywords)
        
        return list(set(keywords))[:10]  # Limit to 10 keywords
    
    async def _extract_context_keywords(self, area_data: Dict[str, Any], cv_text: str) -> List[str]:
        """
        Extract additional keywords from context around the research area
        """
        # This would be more sophisticated in production
        area_name = area_data['name'].lower()
        sentences = cv_text.split('.')
        
        keywords = []
        for sentence in sentences:
            if area_name in sentence.lower():
                # Extract nouns and important terms from the sentence
                words = sentence.split()
                keywords.extend([w.lower() for w in words if len(w) > 4 and w.isalpha()])
        
        return keywords[:5]
    
    async def _extract_technologies(self, area_data: Dict[str, Any], cv_text: str) -> List[str]:
        """
        Extract relevant technologies for the research area
        """
        # This would map research areas to typical technologies
        technology_mapping = {
            'machine learning': ['python', 'tensorflow', 'pytorch', 'scikit-learn'],
            'data science': ['python', 'r', 'sql', 'pandas', 'numpy'],
            'computer vision': ['python', 'opencv', 'tensorflow', 'pytorch'],
            'natural language processing': ['python', 'nltk', 'spacy', 'transformers'],
            'cybersecurity': ['python', 'c++', 'java', 'wireshark', 'metasploit'],
            'cloud computing': ['aws', 'azure', 'gcp', 'docker', 'kubernetes']
        }
        
        area_name = area_data['name'].lower()
        for domain, techs in technology_mapping.items():
            if domain in area_name:
                return techs
        
        return []
    
    async def _identify_skill_gaps(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify potential skill gaps for research
        """
        gaps = []
        research_profile = analysis.get('research_profile', {})
        skills = analysis.get('skills', [])
        
        # Check for essential research skills
        essential_skills = {
            'Research Design': 'research_methods',
            'Data Analysis': 'data_science',
            'Statistical Analysis': 'data_science',
            'Academic Writing': 'academic_skills'
        }
        
        for skill, category in essential_skills.items():
            if not any(s['name'].lower() == skill.lower() for s in skills):
                gaps.append({
                    'skill': skill,
                    'category': category,
                    'importance': 'high',
                    'reason': 'Essential for academic research'
                })
        
        return gaps
    
    async def _generate_research_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate research recommendations based on CV analysis
        """
        recommendations = []
        research_profile = analysis.get('research_profile', {})
        maturity = research_profile.get('maturity_level', 'emerging')
        
        if maturity == 'emerging':
            recommendations.extend([
                {
                    'type': 'skill_development',
                    'priority': 'high',
                    'recommendation': 'Develop foundational research methodology skills',
                    'action_items': ['Take research methods courses', 'Participate in research projects']
                },
                {
                    'type': 'networking',
                    'priority': 'medium',
                    'recommendation': 'Connect with researchers in your field',
                    'action_items': ['Attend academic conferences', 'Join research groups']
                }
            ])
        elif maturity == 'developing':
            recommendations.extend([
                {
                    'type': 'publication',
                    'priority': 'high',
                    'recommendation': 'Focus on publishing in reputable venues',
                    'action_items': ['Identify target journals/conferences', 'Develop publication strategy']
                }
            ])
        
        return recommendations
    
    async def _analyze_research_compatibility(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze compatibility with different research domains
        """
        research_profile = analysis.get('research_profile', {})
        skills = analysis.get('skills', [])
        
        # Score compatibility with major research domains
        domains = ['computer_science', 'engineering', 'sciences', 'social_sciences']
        compatibility_scores = {}
        
        for domain in domains:
            domain_skills = [s for s in skills if self._is_domain_skill(s, domain)]
            score = len(domain_skills) * 10
            compatibility_scores[domain] = min(100, score)
        
        return {
            'domain_compatibility': compatibility_scores,
            'recommended_domains': sorted(compatibility_scores.items(), key=lambda x: x[1], reverse=True)[:2],
            'overall_fit': sum(compatibility_scores.values()) / len(compatibility_scores) if compatibility_scores else 0
        }
    
    def _is_domain_skill(self, skill: Dict[str, Any], domain: str) -> bool:
        """
        Check if skill is relevant to a specific research domain
        """
        domain_mapping = {
            'computer_science': ['programming', 'data_science', 'web', 'cloud', 'database'],
            'engineering': ['programming', 'data_science'],
            'sciences': ['data_science', 'research_methods'],
            'social_sciences': ['research_methods', 'academic_skills']
        }
        
        skill_category = skill.get('category', '')
        return skill_category in domain_mapping.get(domain, [])
    
    # Original methods from your research_area_service.py
    async def get_user_research_areas(
        self,
        user_id: str,
        category: Optional[ResearchCategory] = None,
        search: Optional[str] = None
    ) -> List[ResearchArea]:
        """Get user's research areas"""
        
        query = {"user_id": user_id, "is_active": True}
        
        if category:
            query["category"] = category
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"keywords": {"$in": [search.lower()]}}
            ]
        
        areas = await ResearchArea.find(query).to_list()
        return areas
    
    async def calculate_metrics(self, user_id: str) -> Dict[str, Any]:
        """Calculate research area metrics"""
        
        # Try cache first
        cache_key = f"research_metrics:{user_id}"
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        # Get all research areas
        areas = await ResearchArea.find({
            "user_id": user_id,
            "is_active": True
        }).to_list()
        
        if not areas:
            return self._empty_metrics()
        
        # Basic metrics
        total_areas = len(areas)
        primary_areas = sum(1 for a in areas if a.category == ResearchCategory.PRIMARY)
        total_publications = sum(a.publications for a in areas)
        total_citations = sum(a.citations for a in areas)
        total_grants = sum(a.grants for a in areas)
        total_grant_amount = sum(a.grant_amount for a in areas)
        
        # Area distribution
        category_counts = defaultdict(int)
        for area in areas:
            category_counts[area.category] += 1
        
        area_distribution = [
            {
                "category": category.value.capitalize(),
                "count": count,
                "percentage": round((count / total_areas) * 100, 1)
            }
            for category, count in category_counts.items()
        ]
        
        # Top areas by citations
        top_areas = sorted(areas, key=lambda x: x.citations, reverse=True)[:5]
        
        # Expertise matrix
        expertise_matrix = []
        for area in areas[:6]:  # Top 6 for visualization
            expertise_level = area.expertise.level
            level_score = {
                "expert": 100,
                "advanced": 75,
                "intermediate": 50
            }.get(expertise_level.value, 50)
            
            total_impact = (
                area.impact.academic_impact +
                area.impact.industry_impact +
                area.impact.societal_impact
            ) / 3
            
            # Calculate growth
            growth = 0
            if len(area.publication_trend) >= 2:
                recent = area.publication_trend[-1].count
                previous = area.publication_trend[-2].count
                if previous > 0:
                    growth = ((recent - previous) / previous) * 100
            
            expertise_matrix.append({
                "area": area.name[:20],
                "expertise": level_score,
                "impact": min(100, total_impact),
                "growth": min(100, max(0, growth + 50))
            })
        
        # Trend analysis
        trend_analysis = await self._analyze_trends(areas)
        
        metrics = {
            "total_areas": total_areas,
            "primary_areas": primary_areas,
            "total_publications": total_publications,
            "total_citations": total_citations,
            "total_grants": total_grants,
            "total_grant_amount": total_grant_amount,
            "avg_citations_per_area": round(total_citations / total_areas, 1) if total_areas else 0,
            "top_areas": [a.dict() for a in top_areas],
            "area_distribution": area_distribution,
            "expertise_matrix": expertise_matrix,
            "trend_analysis": trend_analysis
        }
        
        # Cache for 1 hour
        await cache.set(cache_key, metrics, ttl=3600)
        
        return metrics
    
    async def _analyze_trends(self, areas: List[ResearchArea]) -> Dict[str, List[str]]:
        """Analyze research area trends"""
        
        growing = []
        stable = []
        declining = []
        
        for area in areas:
            if len(area.publication_trend) < 3:
                stable.append(area.name)
                continue
            
            # Calculate trend using simple linear regression
            years = [t.year for t in area.publication_trend[-5:]]
            counts = [t.count for t in area.publication_trend[-5:]]
            
            if len(years) > 1:
                # Calculate slope without numpy
                n = len(years)
                x_mean = sum(years) / n
                y_mean = sum(counts) / n
                
                numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(years, counts))
                denominator = sum((x - x_mean) ** 2 for x in years)
                
                if denominator > 0:
                    slope = numerator / denominator
                    
                    if slope > 0.5:
                        growing.append(area.name)
                    elif slope < -0.5:
                        declining.append(area.name)
                    else:
                        stable.append(area.name)
                else:
                    stable.append(area.name)
            else:
                stable.append(area.name)
        
        return {
            "growing": growing[:5],
            "stable": stable[:5],
            "declining": declining[:5]
        }
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            "total_areas": 0,
            "primary_areas": 0,
            "total_publications": 0,
            "total_citations": 0,
            "total_grants": 0,
            "total_grant_amount": 0,
            "avg_citations_per_area": 0,
            "top_areas": [],
            "area_distribution": [],
            "expertise_matrix": [],
            "trend_analysis": {
                "growing": [],
                "stable": [],
                "declining": []
            }
        }
    
    # New methods to add
    async def analyze_area_relationships(self, area_id: str, user_id: str):
        """Analyze relationships between research areas"""
        try:
            # Get the current area
            current_area = await ResearchArea.get(area_id)
            if not current_area:
                return
            
            # Get all other active areas for the user
            other_areas = await ResearchArea.find({
                "user_id": user_id,
                "is_active": True,
                "_id": {"$ne": area_id}
            }).to_list()
            
            # Analyze relationships based on keywords and descriptions
            relationships = []
            for area in other_areas:
                similarity_score = self._calculate_similarity(current_area, area)
                if similarity_score > 0.3:  # Threshold for meaningful relationship
                    relationships.append({
                        "area_id": str(area.id),
                        "area_name": area.name,
                        "similarity_score": similarity_score,
                        "relationship_type": self._determine_relationship_type(similarity_score)
                    })
            
            # Update the current area with related areas
            current_area.related_areas = [
                rel["area_name"] for rel in sorted(relationships, key=lambda x: x["similarity_score"], reverse=True)[:5]
            ]
            await current_area.save()
            
        except Exception as e:
            logger.error(f"Error analyzing area relationships: {e}")

    def _calculate_similarity(self, area1: ResearchArea, area2: ResearchArea) -> float:
        """Calculate similarity between two research areas"""
        # Simple keyword-based similarity
        keywords1 = set(area1.keywords)
        keywords2 = set(area2.keywords)
        
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0

    def _determine_relationship_type(self, similarity_score: float) -> str:
        """Determine the type of relationship based on similarity score"""
        if similarity_score >= 0.7:
            return "strong"
        elif similarity_score >= 0.5:
            return "moderate"
        elif similarity_score >= 0.3:
            return "weak"
        else:
            return "minimal"

    async def get_collaboration_network(self, area: ResearchArea) -> Dict[str, Any]:
        """Get collaboration network for a research area"""
        try:
            network = {
                "nodes": [],
                "links": []
            }
            
            # Add the main area as central node
            network["nodes"].append({
                "id": str(area.id),
                "name": area.name,
                "type": "research_area",
                "value": area.publications,
                "group": 1
            })
            
            # Add collaborators as nodes
            for i, collaborator in enumerate(area.collaborators):
                network["nodes"].append({
                    "id": f"collaborator_{i}",
                    "name": collaborator.get("name", "Unknown"),
                    "type": "collaborator",
                    "value": 1,
                    "group": 2
                })
                
                # Add links between area and collaborator
                network["links"].append({
                    "source": str(area.id),
                    "target": f"collaborator_{i}",
                    "value": 1
                })
            
            return network
            
        except Exception as e:
            logger.error(f"Error getting collaboration network: {e}")
            return {"nodes": [], "links": []}

    async def analyze_trends(self, area_id: str, user_id: str):
        """Analyze trends for a research area"""
        try:
            area = await ResearchArea.get(area_id)
            if not area:
                return
            
            # Simulate trend analysis - in production, this would use real data
            current_year = datetime.now().year
            
            # Publication trend (last 5 years)
            publication_trend = []
            for year in range(current_year - 4, current_year + 1):
                publication_trend.append({
                    "year": year,
                    "count": max(0, area.publications - (current_year - year) * 2 + (year % 3))  # Simulated data
                })
            
            # Citation trend
            citation_trend = []
            for year in range(current_year - 4, current_year + 1):
                citation_trend.append({
                    "year": year,
                    "count": max(0, area.citations - (current_year - year) * 10 + (year % 5) * 3)  # Simulated data
                })
            
            # Update the area with trends
            area.publication_trend = publication_trend
            area.citation_trend = citation_trend
            await area.save()
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")

    async def calculate_expertise_matrix(self, user_id: str) -> List[Dict[str, Any]]:
        """Calculate expertise matrix across research areas"""
        areas = await ResearchArea.find({
            "user_id": user_id,
            "is_active": True
        }).to_list()
        
        matrix = []
        for area in areas:
            expertise_levels = {
                "expert": 100,
                "advanced": 75,
                "intermediate": 50,
                "beginner": 25
            }
            
            matrix.append({
                "area": area.name,
                "expertise_level": area.expertise.level.value if hasattr(area.expertise, 'level') else "intermediate",
                "expertise_score": expertise_levels.get(area.expertise.level.value if hasattr(area.expertise, 'level') else "intermediate", 50),
                "publications": area.publications,
                "citations": area.citations,
                "impact_score": (area.impact.academic_impact + area.impact.industry_impact + area.impact.societal_impact) / 3
            })
        
        return matrix

    async def suggest_collaborators(self, area: ResearchArea) -> List[Dict[str, Any]]:
        """Suggest potential collaborators for a research area"""
        # This would typically integrate with external APIs or internal database
        # For now, return mock suggestions based on area keywords
        suggestions = []
        
        keyword_mapping = {
            "machine learning": ["Dr. AI Researcher", "Prof. Data Scientist", "Dr. Neural Networks"],
            "data science": ["Dr. Analytics Expert", "Prof. Statistics", "Dr. Big Data"],
            "computer vision": ["Dr. Image Processing", "Prof. Computer Graphics", "Dr. Pattern Recognition"],
            "natural language processing": ["Dr. Linguistics", "Prof. Text Mining", "Dr. Chatbot Expert"]
        }
        
        for keyword in area.keywords[:3]:  # Top 3 keywords
            if keyword.lower() in keyword_mapping:
                suggestions.extend([
                    {
                        "name": name,
                        "expertise": keyword,
                        "institution": "University Example",
                        "match_score": 85,
                        "reason": f"Expert in {keyword}"
                    }
                    for name in keyword_mapping[keyword.lower()]
                ])
        
        return suggestions[:5]  # Return top 5 suggestions

    async def match_opportunities(self, user_id: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """Match research opportunities based on expertise"""
        # This would typically integrate with grant databases, conference CFPs, etc.
        # For now, return mock opportunities
        opportunities = []
        
        opportunity_templates = [
            {
                "title": "Research Grant in {field}",
                "description": "Funding opportunity for innovative research in {field}",
                "deadline": "2024-12-31",
                "funding_amount": "50000",
                "type": "grant"
            },
            {
                "title": "Conference CFP: {field} Symposium",
                "description": "Call for papers for the annual {field} symposium",
                "deadline": "2024-08-15",
                "funding_amount": "0",
                "type": "conference"
            },
            {
                "title": "{field} Research Fellowship",
                "description": "Postdoctoral fellowship in {field} research",
                "deadline": "2024-10-01",
                "funding_amount": "75000",
                "type": "fellowship"
            }
        ]
        
        for keyword in keywords[:2]:  # Use top 2 keywords
            for template in opportunity_templates:
                opportunities.append({
                    **template,
                    "title": template["title"].format(field=keyword),
                    "description": template["description"].format(field=keyword),
                    "match_score": 90 - (len(opportunities) * 5),  # Decreasing score
                    "keywords": [keyword]
                })
        
        return opportunities[:6]  # Return top 6 opportunities