from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict
import numpy as np

from app.models.research_area import ResearchArea, ResearchCategory
from app.models.publication import Publication
from app.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class ResearchAreaService:
    
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
                # Calculate slope
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
    
    async def analyze_area_relationships(
        self,
        area_id: str,
        user_id: str
    ):
        """Analyze relationships between research areas"""
        
        area = await ResearchArea.get(area_id)
        if not area:
            return
        
        # Find related areas based on keywords
        if area.keywords:
            related_areas = await ResearchArea.find({
                "user_id": user_id,
                "_id": {"$ne": area_id},
                "is_active": True,
                "keywords": {"$in": area.keywords}
            }).limit(5).to_list()
            
            area.related_areas = [str(r.id) for r in related_areas]
            await area.save()
    
    async def get_collaboration_network(
        self,
        area: ResearchArea
    ) -> Dict[str, Any]:
        """Get collaboration network for a research area"""
        
        nodes = []
        links = []
        
        # Add main area as central node
        nodes.append({
            "id": str(area.id),
            "name": area.name,
            "type": "main",
            "size": 30
        })
        
        # Add collaborators
        for collab in area.collaborators[:10]:
            node_id = f"collab_{collab.get('name', '').replace(' ', '_')}"
            nodes.append({
                "id": node_id,
                "name": collab.get("name", "Unknown"),
                "type": "collaborator",
                "size": 15
            })
            links.append({
                "source": str(area.id),
                "target": node_id,
                "value": 1
            })
        
        # Add related areas
        for related_id in area.related_areas[:5]:
            related = await ResearchArea.get(related_id)
            if related:
                nodes.append({
                    "id": str(related.id),
                    "name": related.name,
                    "type": "related",
                    "size": 20
                })
                links.append({
                    "source": str(area.id),
                    "target": str(related.id),
                    "value": 0.5
                })
        
        return {
            "nodes": nodes,
            "links": links
        }
    
    async def analyze_trends(
        self,
        area_id: str,
        user_id: str
    ):
        """Analyze trends for a research area"""
        
        area = await ResearchArea.get(area_id)
        if not area:
            return
        
        # Get publications for this area
        publications = await Publication.find({
            "user_id": user_id,
            "research_areas": {"$in": [area.name]},
            "is_active": True
        }).to_list()
        
        # Calculate trends
        year_data = defaultdict(lambda: {"publications": 0, "citations": 0})
        for pub in publications:
            year = pub.publication_date.year
            year_data[year]["publications"] += 1
            year_data[year]["citations"] += pub.citations
        
        # Update area with trends
        area.publication_trend = [
            {"year": year, "count": data["publications"]}
            for year, data in sorted(year_data.items())
        ]
        area.citation_trend = [
            {"year": year, "count": data["citations"]}
            for year, data in sorted(year_data.items())
        ]
        
        # Update metrics
        area.publications = len(publications)
        area.citations = sum(p.citations for p in publications)
        
        await area.save()
        
        # Clear cache
        await cache.delete(f"research_metrics:{user_id}")
        
        logger.info(f"Updated trends for research area {area_id}")
    
    async def calculate_expertise_matrix(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Calculate expertise matrix across research areas"""
        
        areas = await ResearchArea.find({
            "user_id": user_id,
            "is_active": True
        }).to_list()
        
        matrix = []
        for area in areas:
            # Calculate scores
            expertise_score = {
                "expert": 100,
                "advanced": 75,
                "intermediate": 50
            }.get(area.expertise.level.value, 50)
            
            # Impact score
            impact_score = (
                area.impact.academic_impact * 0.4 +
                area.impact.industry_impact * 0.3 +
                area.impact.societal_impact * 0.3
            )
            
            # Activity score (based on recent publications)
            current_year = datetime.now().year
            recent_pubs = sum(
                t.count for t in area.publication_trend
                if t.year >= current_year - 2
            )
            activity_score = min(100, recent_pubs * 10)
            
            matrix.append({
                "area": area.name,
                "category": area.category.value,
                "expertise": expertise_score,
                "impact": min(100, impact_score),
                "activity": activity_score,
                "years_experience": area.expertise.years_of_experience,
                "publications": area.publications,
                "citations": area.citations
            })
        
        # Sort by overall score
        for item in matrix:
            item["overall_score"] = (
                item["expertise"] * 0.3 +
                item["impact"] * 0.3 +
                item["activity"] * 0.4
            )
        
        matrix.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return matrix
    
    async def suggest_collaborators(
        self,
        area: ResearchArea
    ) -> List[Dict[str, Any]]:
        """Suggest potential collaborators for a research area"""
        
        # This is a simplified version
        # In production, you'd use ML models and external APIs
        
        suggestions = []
        
        # Find other users working in similar areas
        similar_areas = await ResearchArea.find({
            "name": {"$regex": area.name, "$options": "i"},
            "user_id": {"$ne": area.user_id},
            "is_active": True
        }).limit(10).to_list()
        
        for similar in similar_areas:
            # Calculate compatibility score
            keyword_overlap = len(set(area.keywords) & set(similar.keywords))
            tech_overlap = len(set(area.technologies) & set(similar.technologies))
            
            compatibility_score = (
                keyword_overlap * 10 +
                tech_overlap * 5 +
                min(similar.publications / 10, 10)
            )
            
            suggestions.append({
                "area_id": str(similar.id),
                "area_name": similar.name,
                "user_id": similar.user_id,
                "compatibility_score": round(compatibility_score, 1),
                "common_keywords": list(set(area.keywords) & set(similar.keywords)),
                "common_technologies": list(set(area.technologies) & set(similar.technologies)),
                "publications": similar.publications,
                "category": similar.category.value
            })
        
        # Sort by compatibility score
        suggestions.sort(key=lambda x: x["compatibility_score"], reverse=True)
        
        return suggestions[:5]
    
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