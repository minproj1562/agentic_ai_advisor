# app/repositories/faculty_repository.py
"""
Faculty Repository - Fetches faculty data from MongoDB
COMPLETE VERSION - ALL METHODS INCLUDED
"""

import logging
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import re

logger = logging.getLogger(__name__)


class FacultyRepository:
    """Repository for faculty data operations - COMPLETE."""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db
        self.collection_name = "faculty"
    
    def set_database(self, db: AsyncIOMotorDatabase):
        """Set database connection."""
        self.db = db
    
    @property
    def collection(self):
        """Get the faculty collection."""
        if self.db is None:
            raise ValueError("Database not initialized. Call set_database() first.")
        return self.db[self.collection_name]
    
    async def find_by_subject(self, subject_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find faculty members who teach a specific subject.
        
        Args:
            subject_name: Name of the subject (partial match supported)
            limit: Maximum number of results
            
        Returns:
            List of faculty dictionaries
        """
        try:
            # Create case-insensitive regex pattern
            pattern = re.compile(re.escape(subject_name), re.IGNORECASE)
            
            cursor = self.collection.find({
                "subjects": {"$regex": pattern}
            }).limit(limit)
            
            faculty_list = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for faculty in faculty_list:
                faculty["_id"] = str(faculty["_id"])
            
            logger.info(f"Found {len(faculty_list)} faculty for subject: {subject_name}")
            return faculty_list
            
        except Exception as e:
            logger.error(f"Error finding faculty by subject: {e}")
            return []
    
    async def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find faculty by name (partial match).
        
        Args:
            name: Faculty name to search
            
        Returns:
            Faculty dictionary or None
        """
        try:
            pattern = re.compile(re.escape(name), re.IGNORECASE)
            
            faculty = await self.collection.find_one({
                "name": {"$regex": pattern}
            })
            
            if faculty:
                faculty["_id"] = str(faculty["_id"])
            
            return faculty
            
        except Exception as e:
            logger.error(f"Error finding faculty by name: {e}")
            return None
    
    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find faculty by email."""
        try:
            faculty = await self.collection.find_one({"email": email})
            if faculty:
                faculty["_id"] = str(faculty["_id"])
            return faculty
        except Exception as e:
            logger.error(f"Error finding faculty by email: {e}")
            return None
    
    async def find_by_department(self, department: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Find all faculty in a department.
        
        Args:
            department: Department name (partial match)
            limit: Maximum results
            
        Returns:
            List of faculty dictionaries
        """
        try:
            pattern = re.compile(re.escape(department), re.IGNORECASE)
            
            cursor = self.collection.find({
                "department": {"$regex": pattern}
            }).sort("designation", 1).limit(limit)
            
            faculty_list = await cursor.to_list(length=limit)
            
            for faculty in faculty_list:
                faculty["_id"] = str(faculty["_id"])
            
            return faculty_list
            
        except Exception as e:
            logger.error(f"Error finding faculty by department: {e}")
            return []
    
    async def find_hod(self, department: str) -> Optional[Dict[str, Any]]:
        """
        Find HOD of a department.
        
        Args:
            department: Department name
            
        Returns:
            HOD faculty dictionary or None
        """
        try:
            pattern = re.compile(re.escape(department), re.IGNORECASE)
            
            faculty = await self.collection.find_one({
                "department": {"$regex": pattern},
                "designation": {"$regex": "HOD", "$options": "i"}
            })
            
            if faculty:
                faculty["_id"] = str(faculty["_id"])
            
            return faculty
            
        except Exception as e:
            logger.error(f"Error finding HOD: {e}")
            return None
    
    async def find_by_expertise(self, expertise: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find faculty by expertise area.
        
        Args:
            expertise: Expertise area to search
            limit: Maximum results
            
        Returns:
            List of faculty dictionaries
        """
        try:
            pattern = re.compile(re.escape(expertise), re.IGNORECASE)
            
            cursor = self.collection.find({
                "expertise": {"$regex": pattern}
            }).limit(limit)
            
            faculty_list = await cursor.to_list(length=limit)
            
            for faculty in faculty_list:
                faculty["_id"] = str(faculty["_id"])
            
            return faculty_list
            
        except Exception as e:
            logger.error(f"Error finding faculty by expertise: {e}")
            return []
    
    async def search_faculty(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        General search across faculty data.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching faculty
        """
        try:
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            
            cursor = self.collection.find({
                "$or": [
                    {"name": {"$regex": pattern}},
                    {"subjects": {"$regex": pattern}},
                    {"expertise": {"$regex": pattern}},
                    {"department": {"$regex": pattern}}
                ]
            }).limit(limit)
            
            faculty_list = await cursor.to_list(length=limit)
            
            for faculty in faculty_list:
                faculty["_id"] = str(faculty["_id"])
            
            return faculty_list
            
        except Exception as e:
            logger.error(f"Error searching faculty: {e}")
            return []
    
    async def get_all_faculty(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all faculty with pagination."""
        try:
            cursor = self.collection.find({}).skip(skip).limit(limit).sort("name", 1)
            faculty_list = await cursor.to_list(length=limit)
            
            for faculty in faculty_list:
                faculty["_id"] = str(faculty["_id"])
            
            return faculty_list
            
        except Exception as e:
            logger.error(f"Error getting all faculty: {e}")
            return []
    
    async def count_faculty(self, department: Optional[str] = None) -> int:
        """Count total faculty, optionally filtered by department."""
        try:
            query = {}
            if department:
                query["department"] = {"$regex": department, "$options": "i"}
            
            return await self.collection.count_documents(query)
            
        except Exception as e:
            logger.error(f"Error counting faculty: {e}")
            return 0
    
    async def find_by_id(self, faculty_id: str) -> Optional[Dict[str, Any]]:
        """Find faculty by MongoDB ObjectId."""
        try:
            faculty = await self.collection.find_one({"_id": ObjectId(faculty_id)})
            if faculty:
                faculty["_id"] = str(faculty["_id"])
            return faculty
        except Exception as e:
            logger.error(f"Error finding faculty by ID: {e}")
            return None
    
    async def get_faculty_by_designation(
        self, 
        designation: str, 
        department: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get faculty filtered by designation."""
        try:
            query = {"designation": {"$regex": designation, "$options": "i"}}
            if department:
                query["department"] = {"$regex": department, "$options": "i"}
            
            cursor = self.collection.find(query).limit(limit).sort("name", 1)
            faculty_list = await cursor.to_list(length=limit)
            
            for faculty in faculty_list:
                faculty["_id"] = str(faculty["_id"])
            
            return faculty_list
            
        except Exception as e:
            logger.error(f"Error getting faculty by designation: {e}")
            return []