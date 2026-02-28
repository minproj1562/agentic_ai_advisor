# academic-advisor-backend/app/repositories/career_repository.py
"""
Career data access layer — with smart keyword search
"""

import re
import logging
from typing import List, Optional, Dict
from app.models.career import CareerPath, CareerCategory

logger = logging.getLogger(__name__)

# Words to ignore when searching
_STOP_WORDS = {
    "how", "to", "become", "a", "an", "the", "what", "is", "are", "can",
    "i", "do", "does", "should", "would", "could", "about", "tell", "me",
    "want", "like", "need", "help", "career", "in", "for", "of", "as",
    "be", "get", "into", "path", "options", "opportunities", "job", "jobs",
    "work", "after", "with", "my", "which", "best", "good", "salary",
}


def _extract_keywords(query: str) -> List[str]:
    """Extract meaningful keywords from a query, removing stop words."""
    # Remove punctuation and split
    cleaned = re.sub(r'[^\w\s]', '', query.lower())
    words = cleaned.split()
    # Remove stop words and short words
    keywords = [w for w in words if w not in _STOP_WORDS and len(w) > 1]
    return keywords


class CareerRepository:

    async def get_all(self, active_only: bool = True) -> List[CareerPath]:
        filt = {"is_active": True} if active_only else {}
        return await CareerPath.find(filt).to_list()

    async def get_by_id(self, career_id: str) -> Optional[CareerPath]:
        return await CareerPath.find_one(CareerPath.id == career_id)

    async def get_by_category(self, cat: CareerCategory) -> List[CareerPath]:
        return await CareerPath.find(
            CareerPath.category == cat, CareerPath.is_active == True
        ).to_list()

    async def search(self, query: str, limit: int = 10) -> List[CareerPath]:
        """
        Smart search — extracts keywords from query and matches against
        title, description, keywords, skills, and job_titles.
        """
        keywords = _extract_keywords(query)
        if not keywords:
            return []

        # Build OR conditions for each keyword
        or_conditions = []
        for kw in keywords:
            escaped = re.escape(kw)
            or_conditions.extend([
                {"title": {"$regex": escaped, "$options": "i"}},
                {"description": {"$regex": escaped, "$options": "i"}},
                {"keywords": {"$regex": escaped, "$options": "i"}},
                {"required_skills": {"$regex": escaped, "$options": "i"}},
                {"job_titles": {"$regex": escaped, "$options": "i"}},
                {"category": {"$regex": escaped, "$options": "i"}},
            ])

        if not or_conditions:
            return []

        results = await CareerPath.find(
            {"is_active": True, "$or": or_conditions}
        ).limit(limit * 3).to_list()  # Over-fetch for scoring

        # Score results by keyword match count
        scored: List[tuple] = []
        for career in results:
            score = 0
            searchable = (
                f"{career.title} {career.description} "
                f"{' '.join(career.keywords)} "
                f"{' '.join(career.required_skills)} "
                f"{' '.join(career.job_titles)} "
                f"{career.category.value}"
            ).lower()

            for kw in keywords:
                # Title match is worth more
                if kw in career.title.lower():
                    score += 10
                # Keyword array match
                if kw in [k.lower() for k in career.keywords]:
                    score += 5
                # Description/skills match
                if kw in searchable:
                    score += 2

            if score > 0:
                scored.append((career, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:limit]]

    async def find_by_title(self, title: str) -> Optional[CareerPath]:
        """Find a career by exact or close title match."""
        # Exact match first
        career = await CareerPath.find_one(
            {"title": {"$regex": f"^{re.escape(title)}$", "$options": "i"},
             "is_active": True}
        )
        if career:
            return career

        # Partial match
        career = await CareerPath.find_one(
            {"title": {"$regex": re.escape(title), "$options": "i"},
             "is_active": True}
        )
        return career

    async def find_by_skills(
        self, skills: List[str], limit: int = 5
    ) -> List[CareerPath]:
        low = [s.lower() for s in skills]
        careers = await CareerPath.find(CareerPath.is_active == True).to_list()
        scored = []
        for c in careers:
            cs = [s.lower() for s in c.required_skills]
            overlap = len(set(low) & set(cs))
            if overlap:
                scored.append((c, overlap / max(len(cs), 1)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:limit]]

    async def find_by_interests(
        self, interests: List[str], limit: int = 5
    ) -> List[CareerPath]:
        low = [i.lower() for i in interests]
        careers = await CareerPath.find(CareerPath.is_active == True).to_list()
        scored = []
        for c in careers:
            kw = [k.lower() for k in c.keywords]
            score = 0
            for i in low:
                if i in kw:
                    score += 2
                if i in c.title.lower():
                    score += 3
                if i in c.description.lower():
                    score += 1
            if score:
                scored.append((c, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:limit]]

    async def get_count(self) -> int:
        return await CareerPath.find(CareerPath.is_active == True).count()

    async def create(self, career: CareerPath) -> CareerPath:
        await career.insert()
        return career

    async def create_many(self, careers: List[CareerPath]) -> int:
        if careers:
            await CareerPath.insert_many(careers)
        return len(careers)

    async def delete_all(self) -> int:
        result = await CareerPath.find().delete()
        return result.deleted_count if result else 0