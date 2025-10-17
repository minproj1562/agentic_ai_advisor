from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from beanie import PydanticObjectId
import pandas as pd
import json
from collections import defaultdict

from app.models.publication import Publication, PublicationType, PublicationStatus
from app.utils.metrics import calculate_h_index, calculate_i10_index
from app.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class PublicationService:
    
    async def get_user_publications(
        self,
        user_id: str,
        publication_type: Optional[PublicationType] = None,
        status: Optional[PublicationStatus] = None,
        search: Optional[str] = None,
        year: Optional[int] = None,
        sort_by: str = "date",
        skip: int = 0,
        limit: int = 20
    ) -> List[Publication]:
        """Get user publications with filters"""
        
        # Build query
        query = {"user_id": user_id, "is_active": True}
        
        if publication_type:
            query["publication_type"] = publication_type
        
        if status:
            query["status"] = status
        
        if year:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31, 23, 59, 59)
            query["publication_date"] = {"$gte": start_date, "$lte": end_date}
        
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"abstract": {"$regex": search, "$options": "i"}},
                {"keywords": {"$in": [search.lower()]}}
            ]
        
        # Determine sort order
        sort_field = "-publication_date"
        if sort_by == "citations":
            sort_field = "-citations"
        elif sort_by == "impact":
            sort_field = "-impact_factor"
        
        # Execute query
        publications = await Publication.find(query).sort(sort_field).skip(skip).limit(limit).to_list()
        
        return publications
    
    async def calculate_metrics(self, user_id: str) -> Dict[str, Any]:
        """Calculate publication metrics"""
        
        # Try cache first
        cache_key = f"pub_metrics:{user_id}"
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        # Get all publications
        publications = await Publication.find({
            "user_id": user_id,
            "is_active": True,
            "status": PublicationStatus.PUBLISHED
        }).to_list()
        
        if not publications:
            return self._empty_metrics()
        
        current_year = datetime.now().year
        
        # Basic metrics
        total_publications = len(publications)
        total_citations = sum(p.citations for p in publications)
        
        # Calculate h-index and i10-index
        citation_counts = [p.citations for p in publications]
        h_index = calculate_h_index(citation_counts)
        i10_index = calculate_i10_index(citation_counts)
        
        # Publications this year
        publications_this_year = sum(
            1 for p in publications
            if p.publication_date.year == current_year
        )
        
        # Citations this year
        citations_this_year = sum(
            sum(t.count for t in p.citation_trend if str(current_year) in t.month)
            for p in publications
        )
        
        # Publications by type
        type_counts = defaultdict(int)
        for pub in publications:
            type_counts[pub.publication_type] += 1
        
        publications_by_type = [
            {
                "type": ptype.value,
                "count": count,
                "percentage": round((count / total_publications) * 100, 1)
            }
            for ptype, count in type_counts.items()
        ]
        
        # Citation trend
        year_data = defaultdict(lambda: {"publications": 0, "citations": 0})
        for pub in publications:
            year = pub.publication_date.year
            year_data[year]["publications"] += 1
            year_data[year]["citations"] += pub.citations
        
        citation_trend = [
            {
                "year": year,
                "publications": data["publications"],
                "citations": data["citations"]
            }
            for year, data in sorted(year_data.items())
        ][-10:]  # Last 10 years
        
        # Top cited papers
        top_cited_papers = sorted(publications, key=lambda x: x.citations, reverse=True)[:10]
        
        # Collaboration network
        collaborator_map = defaultdict(lambda: {"publications": 0, "citations": 0})
        for pub in publications:
            for collab in pub.collaborators:
                key = collab.email or collab.name
                collaborator_map[key]["name"] = collab.name
                collaborator_map[key]["publications"] += 1
                collaborator_map[key]["citations"] += pub.citations
        
        collaboration_network = sorted(
            [
                {
                    "name": data["name"],
                    "publications": data["publications"],
                    "citations": data["citations"]
                }
                for data in collaborator_map.values()
            ],
            key=lambda x: x["publications"],
            reverse=True
        )[:20]
        
        # Impact metrics
        publications_with_if = [p for p in publications if p.impact_factor]
        avg_impact_factor = (
            sum(p.impact_factor for p in publications_with_if) / len(publications_with_if)
            if publications_with_if else 0
        )
        
        q1_publications = sum(1 for p in publications if p.quartile == "Q1")
        open_access_count = sum(1 for p in publications if p.is_open_access)
        open_access_percentage = round((open_access_count / total_publications) * 100, 1)
        
        metrics = {
            "total_publications": total_publications,
            "total_citations": total_citations,
            "h_index": h_index,
            "i10_index": i10_index,
            "avg_citations_per_paper": round(total_citations / total_publications, 1),
            "publications_this_year": publications_this_year,
            "citations_this_year": citations_this_year,
            "top_cited_papers": [p.dict() for p in top_cited_papers],
            "publications_by_type": publications_by_type,
            "citation_trend": citation_trend,
            "collaboration_network": collaboration_network,
            "impact_metrics": {
                "avg_impact_factor": round(avg_impact_factor, 2),
                "q1_publications": q1_publications,
                "open_access_percentage": open_access_percentage
            }
        }
        
        # Cache for 1 hour
        await cache.set(cache_key, metrics, ttl=3600)
        
        return metrics
    
    async def bulk_import(
        self,
        user_id: str,
        publications_data: List[dict]
    ) -> Dict[str, Any]:
        """Bulk import publications"""
        
        success_ids = []
        failures = []
        
        for pub_data in publications_data:
            try:
                # Check for duplicate DOI
                if pub_data.get("doi"):
                    existing = await Publication.find_one({
                        "doi": pub_data["doi"],
                        "user_id": user_id
                    })
                    if existing:
                        failures.append({
                            "data": pub_data,
                            "error": "Duplicate DOI"
                        })
                        continue
                
                # Create publication
                publication = Publication(
                    user_id=user_id,
                    **pub_data
                )
                await publication.create()
                success_ids.append(str(publication.id))
                
            except Exception as e:
                failures.append({
                    "data": pub_data,
                    "error": str(e)
                })
        
        # Clear cache
        await cache.delete(f"pub_metrics:{user_id}")
        
        return {
            "success": len(success_ids),
            "failed": len(failures),
            "success_ids": success_ids,
            "failures": failures
        }
    
    async def export_to_csv(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Export publications to CSV"""
        
        query = {"user_id": user_id, "is_active": True}
        
        if start_date and end_date:
            query["publication_date"] = {
                "$gte": start_date,
                "$lte": end_date
            }
        
        publications = await Publication.find(query).to_list()
        
        # Convert to DataFrame
        data = []
        for pub in publications:
            data.append({
                "Title": pub.title,
                "Authors": ", ".join(pub.authors),
                "Journal": pub.journal,
                "Year": pub.publication_date.year,
                "Type": pub.publication_type,
                "Citations": pub.citations,
                "DOI": pub.doi or "",
                "Status": pub.status,
                "Impact Factor": pub.impact_factor or "",
                "Quartile": pub.quartile or ""
            })
        
        df = pd.DataFrame(data)
        return df.to_csv(index=False)
    
    async def export_to_bibtex(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Export publications to BibTeX format"""
        
        query = {"user_id": user_id, "is_active": True}
        
        if start_date and end_date:
            query["publication_date"] = {
                "$gte": start_date,
                "$lte": end_date
            }
        
        publications = await Publication.find(query).to_list()
        
        bibtex_entries = []
        for pub in publications:
            entry_type = "article" if pub.publication_type == PublicationType.JOURNAL else "inproceedings"
            
            # Generate BibTeX key
            first_author = pub.authors[0].split()[-1] if pub.authors else "Unknown"
            year = pub.publication_date.year
            key = f"{first_author}{year}"
            
            entry = f"@{entry_type}{{{key},\n"
            entry += f"  title = {{{pub.title}}},\n"
            entry += f"  author = {{{' and '.join(pub.authors)}}},\n"
            entry += f"  journal = {{{pub.journal}}},\n"
            entry += f"  year = {{{year}}},\n"
            
            if pub.volume:
                entry += f"  volume = {{{pub.volume}}},\n"
            if pub.issue:
                entry += f"  number = {{{pub.issue}}},\n"
            if pub.pages:
                entry += f"  pages = {{{pub.pages}}},\n"
            if pub.doi:
                entry += f"  doi = {{{pub.doi}}},\n"
            
            entry += "}"
            bibtex_entries.append(entry)
        
        return "\n\n".join(bibtex_entries)
    
    async def analyze_trends(self, user_id: str) -> Dict[str, Any]:
        """Analyze publication trends"""
        
        publications = await Publication.find({
            "user_id": user_id,
            "is_active": True
        }).to_list()
        
        if not publications:
            return {"message": "No publications to analyze"}
        
        # Yearly trends
        yearly_stats = defaultdict(lambda: {
            "count": 0,
            "citations": 0,
            "journals": set(),
            "collaborators": set()
        })
        
        for pub in publications:
            year = pub.publication_date.year
            yearly_stats[year]["count"] += 1
            yearly_stats[year]["citations"] += pub.citations
            yearly_stats[year]["journals"].add(pub.journal)
            for collab in pub.collaborators:
                yearly_stats[year]["collaborators"].add(collab.name)
        
        # Convert sets to counts
        trends = []
        for year in sorted(yearly_stats.keys()):
            trends.append({
                "year": year,
                "publications": yearly_stats[year]["count"],
                "citations": yearly_stats[year]["citations"],
                "unique_journals": len(yearly_stats[year]["journals"]),
                "unique_collaborators": len(yearly_stats[year]["collaborators"])
            })
        
        # Publication growth rate
        if len(trends) > 1:
            recent = trends[-1]["publications"]
            previous = trends[-2]["publications"]
            growth_rate = ((recent - previous) / previous * 100) if previous > 0 else 0
        else:
            growth_rate = 0
        
        # Most productive period
        most_productive = max(trends, key=lambda x: x["publications"]) if trends else None
        
        return {
            "yearly_trends": trends,
            "growth_rate": round(growth_rate, 1),
            "most_productive_year": most_productive,
            "total_years_active": len(yearly_stats)
        }
    
    async def recommend_journals(
        self,
        abstract: str,
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """Recommend journals based on paper content"""
        
        # This is a simplified version - in production, you'd use ML models
        # and journal databases for better recommendations
        
        # Get all journals from user's publications
        all_publications = await Publication.find({
            "is_active": True,
            "status": PublicationStatus.PUBLISHED
        }).to_list()
        
        journal_stats = defaultdict(lambda: {
            "count": 0,
            "avg_citations": 0,
            "impact_factors": [],
            "keywords": set()
        })
        
        for pub in all_publications:
            journal = pub.journal
            journal_stats[journal]["count"] += 1
            journal_stats[journal]["avg_citations"] += pub.citations
            if pub.impact_factor:
                journal_stats[journal]["impact_factors"].append(pub.impact_factor)
            journal_stats[journal]["keywords"].update(pub.keywords)
        
        # Calculate relevance scores
        recommendations = []
        for journal, stats in journal_stats.items():
            if stats["count"] == 0:
                continue
            
            # Calculate keyword overlap
            keyword_overlap = len(set(keywords) & stats["keywords"])
            
            # Calculate average metrics
            avg_citations = stats["avg_citations"] / stats["count"]
            avg_if = (
                sum(stats["impact_factors"]) / len(stats["impact_factors"])
                if stats["impact_factors"] else 0
            )
            
            # Simple relevance score
            relevance_score = (
                keyword_overlap * 10 +
                min(stats["count"], 10) +
                min(avg_citations / 10, 10) +
                avg_if
            )
            
            recommendations.append({
                "journal": journal,
                "relevance_score": round(relevance_score, 2),
                "publication_count": stats["count"],
                "avg_citations": round(avg_citations, 1),
                "avg_impact_factor": round(avg_if, 2),
                "matching_keywords": keyword_overlap
            })
        
        # Sort by relevance score
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return recommendations[:10]
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            "total_publications": 0,
            "total_citations": 0,
            "h_index": 0,
            "i10_index": 0,
            "avg_citations_per_paper": 0,
            "publications_this_year": 0,
            "citations_this_year": 0,
            "top_cited_papers": [],
            "publications_by_type": [],
            "citation_trend": [],
            "collaboration_network": [],
            "impact_metrics": {
                "avg_impact_factor": 0,
                "q1_publications": 0,
                "open_access_percentage": 0
            }
        }