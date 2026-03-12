# app/repositories/event_repository.py
"""
Event Repository - Fetches events and holidays from MongoDB
"""

import logging
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

logger = logging.getLogger(__name__)


class EventRepository:
    """Repository for events and calendar operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db
    
    def set_database(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    @property
    def events_collection(self):
        if self.db is None:
            raise ValueError("Database not initialized")
        return self.db["events"]
    
    @property
    def holidays_collection(self):
        if self.db is None:
            raise ValueError("Database not initialized")
        return self.db["holidays"]
    
    @property
    def calendar_collection(self):
        if self.db is None:
            raise ValueError("Database not initialized")
        return self.db["academic_calendar"]
    
    async def get_upcoming_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get upcoming events."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            cursor = self.events_collection.find({
                "date": {"$gte": today}
            }).sort("date", 1).limit(limit)
            
            events = await cursor.to_list(length=limit)
            
            for event in events:
                event["_id"] = str(event["_id"])
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            return []
    
    async def get_events_by_type(self, event_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get events by type (workshop, seminar, placement, etc.)."""
        try:
            cursor = self.events_collection.find({
                "type": {"$regex": event_type, "$options": "i"}
            }).sort("date", 1).limit(limit)
            
            events = await cursor.to_list(length=limit)
            
            for event in events:
                event["_id"] = str(event["_id"])
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting events by type: {e}")
            return []
    
    async def get_upcoming_holidays(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get upcoming holidays."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            cursor = self.holidays_collection.find({
                "date": {"$gte": today}
            }).sort("date", 1).limit(limit)
            
            holidays = await cursor.to_list(length=limit)
            
            for holiday in holidays:
                holiday["_id"] = str(holiday["_id"])
            
            return holidays
            
        except Exception as e:
            logger.error(f"Error getting upcoming holidays: {e}")
            return []
    
    async def get_exam_schedule(self, academic_year: str = "2024-25") -> List[Dict[str, Any]]:
        """Get exam schedule from academic calendar."""
        try:
            calendar = await self.calendar_collection.find_one({
                "academic_year": academic_year
            })
            
            if calendar and "events" in calendar:
                return [e for e in calendar["events"] if e.get("type") == "exam"]
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting exam schedule: {e}")
            return []