# app/repositories/faq_repository.py
"""
FAQ Repository - Fetches FAQs from MongoDB
"""

import logging
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import re

logger = logging.getLogger(__name__)


class FAQRepository:
    """Repository for FAQ operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db
    
    def set_database(self, db: AsyncIOMotorDatabase):
        """Set database connection."""
        self.db = db
    
    @property
    def collection(self):
        if self.db is None:
            raise ValueError("Database not initialized")
        return self.db["faqs"]
    
    async def find_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Find FAQs by category."""
        try:
            cursor = self.collection.find({
                "category": {"$regex": category, "$options": "i"}
            })
            
            faqs = await cursor.to_list(length=50)
            
            for faq in faqs:
                faq["_id"] = str(faq["_id"])
            
            return faqs
            
        except Exception as e:
            logger.error(f"Error finding FAQs by category: {e}")
            return []
    
    async def search_faqs(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search FAQs by keywords or question content."""
        try:
            words = query.lower().split()
            
            cursor = self.collection.find({
                "$or": [
                    {"keywords": {"$in": words}},
                    {"question": {"$regex": query, "$options": "i"}},
                    {"answer": {"$regex": query, "$options": "i"}}
                ]
            }).limit(limit)
            
            faqs = await cursor.to_list(length=limit)
            
            for faq in faqs:
                faq["_id"] = str(faq["_id"])
            
            return faqs
            
        except Exception as e:
            logger.error(f"Error searching FAQs: {e}")
            return []
    
    async def find_best_match(self, query: str) -> Optional[Dict[str, Any]]:
        """Find the best matching FAQ for a query."""
        try:
            faqs = await self.search_faqs(query, limit=1)
            return faqs[0] if faqs else None
        except Exception as e:
            logger.error(f"Error finding best FAQ match: {e}")
            return None
    
    async def get_all_categories(self) -> List[str]:
        """Get all FAQ categories."""
        try:
            categories = await self.collection.distinct("category")
            return categories
        except Exception as e:
            logger.error(f"Error getting FAQ categories: {e}")
            return []