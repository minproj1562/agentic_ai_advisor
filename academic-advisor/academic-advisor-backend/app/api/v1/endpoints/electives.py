# app/api/v1/endpoints/electives.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from beanie import PydanticObjectId
from datetime import datetime

from app.models.elective import Elective, ElectiveCategory, DifficultyLevel
from app.core.deps import get_current_user
from app.services.catalogue_loader import CatalogueLoader
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Response Models
class InstructorInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    rating: float = 0.0
    expertise: List[str] = []
    total_students: int = 0
    years_experience: int = 0

class ElectiveResponse(BaseModel):
    id: str = Field(description="Unique identifier")
    code: str = Field(description="Course code")
    name: str = Field(description="Course name")
    title: str = Field(description="Course title (same as name)")  # For backward compatibility
    description: str = Field(description="Course description")
    category: str = Field(description="Elective category")
    department: str = Field(description="Department offering the course")
    semester: int = Field(description="Semester when offered")
    credits: int = Field(description="Credit hours")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisite courses")
    min_cgpa_required: Optional[float] = Field(default=None, description="Minimum CGPA required")
    
    # Content and Skills
    topics: List[str] = Field(default_factory=list, description="Topics covered")
    skills_covered: List[str] = Field(default_factory=list, description="Skills covered")
    skills_gained: List[str] = Field(default_factory=list, description="Skills gained (alias)")
    career_paths: List[str] = Field(default_factory=list, description="Career opportunities")
    
    # Instructor
    instructor: InstructorInfo = Field(default_factory=InstructorInfo)
    instructor_name: Optional[str] = None
    instructor_email: Optional[str] = None
    
    # Difficulty and Recommendations
    difficulty: str = Field(description="Difficulty level")
    difficulty_level: str = Field(description="Difficulty level enum")
    recommended_for: List[str] = Field(default_factory=list)
    
    # Enrollment
    max_students: int = Field(default=60)
    current_enrollment: int = Field(default=0)
    enrollment_count: int = Field(default=0, description="Alias for current_enrollment")
    
    # Resources
    textbooks: List[str] = Field(default_factory=list)
    online_resources: List[str] = Field(default_factory=list)
    lab_requirements: List[str] = Field(default_factory=list)
    syllabus: List[str] = Field(default_factory=list, description="Syllabus topics")
    learning_outcomes: List[str] = Field(default_factory=list)
    
    # Honours/Minor Track
    is_honours_track: bool = Field(default=False)
    honours_track_name: Optional[str] = None
    
    # Analytics
    average_rating: float = Field(default=0.0)
    completion_rate: float = Field(default=0.0)
    industry_relevance: float = Field(default=0.85)
    job_market_demand: float = Field(default=0.8)
    career_impact: str = Field(default="High demand in industry")
    
    # Administrative
    is_available: bool = Field(default=True)
    academic_year: str = Field(default="2024-25")
    
    # Additional fields for compatibility
    tags: List[str] = Field(default_factory=list)
    skills_required: List[str] = Field(default_factory=list)
    related_areas: List[str] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "code": "CSE5011",
                "name": "Cloud Computing Services",
                "title": "Cloud Computing Services",
                "description": "Introduction to cloud computing concepts and services",
                "category": "Program Elective",
                "department": "Computer Science",
                "semester": 5,
                "credits": 3,
                "prerequisites": ["Computer Networks", "Operating Systems"],
                "topics": ["Virtualization", "AWS", "Azure", "Docker", "Kubernetes"],
                "skills_covered": ["Cloud Architecture", "DevOps", "Containerization"],
                "career_paths": ["Cloud Architect", "DevOps Engineer", "Site Reliability Engineer"],
                "difficulty": "Intermediate",
                "max_students": 60,
                "current_enrollment": 45,
                "is_available": True,
                "average_rating": 4.3
            }
        }

class ElectiveCreateRequest(BaseModel):
    code: str
    name: str
    description: str
    category: ElectiveCategory
    department: str = "Computer Science"
    semester: int = Field(ge=3, le=8)
    credits: int = Field(default=3, ge=1, le=8)
    prerequisites: List[str] = []
    topics: List[str] = []
    skills_covered: List[str] = []
    career_paths: List[str] = []
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    max_students: int = Field(default=60, ge=1)
    min_cgpa_required: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    is_honours_track: bool = False
    honours_track_name: Optional[str] = None
    instructor_name: Optional[str] = None
    instructor_email: Optional[str] = None

class ElectiveUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    skills_covered: Optional[List[str]] = None
    career_paths: Optional[List[str]] = None
    max_students: Optional[int] = None
    current_enrollment: Optional[int] = None
    is_available: Optional[bool] = None
    instructor_name: Optional[str] = None
    instructor_email: Optional[str] = None

# Helper function to convert Elective document to response
def elective_to_response(elective: Elective) -> ElectiveResponse:
    """Convert Elective document to ElectiveResponse"""
    # Create instructor info
    instructor = InstructorInfo(
        name=elective.instructor_name or "TBD",
        email=elective.instructor_email or "tbd@university.edu",
        department=elective.department,
        rating=elective.average_rating,
        expertise=elective.skills_covered[:3] if elective.skills_covered else [],
        total_students=elective.current_enrollment,
        years_experience=5  # Default value
    )
    
    return ElectiveResponse(
        id=str(elective.id),
        code=elective.code,
        name=elective.name,
        title=elective.name,  # For backward compatibility
        description=elective.description,
        category=elective.category.value,
        department=elective.department,
        semester=elective.semester,
        credits=elective.credits,
        prerequisites=elective.prerequisites,
        min_cgpa_required=elective.min_cgpa_required,
        topics=elective.topics,
        skills_covered=elective.skills_covered,
        skills_gained=elective.skills_covered,  # Alias
        career_paths=elective.career_paths,
        instructor=instructor,
        instructor_name=elective.instructor_name,
        instructor_email=elective.instructor_email,
        difficulty=elective.difficulty_level.value,
        difficulty_level=elective.difficulty_level.value,
        recommended_for=elective.recommended_for,
        max_students=elective.max_students,
        current_enrollment=elective.current_enrollment,
        enrollment_count=elective.current_enrollment,  # Alias
        textbooks=elective.textbooks,
        online_resources=elective.online_resources,
        lab_requirements=elective.lab_requirements,
        syllabus=elective.topics,  # Using topics as syllabus
        learning_outcomes=[f"Understand {topic}" for topic in elective.topics[:3]],
        is_honours_track=elective.is_honours_track,
        honours_track_name=elective.honours_track_name,
        average_rating=elective.average_rating,
        completion_rate=elective.completion_rate,
        industry_relevance=0.85,  # Default value
        job_market_demand=0.8,  # Default value
        career_impact="High demand in industry" if elective.category == ElectiveCategory.PROGRAM_ELECTIVE else "Good for overall development",
        is_available=elective.is_available,
        academic_year=elective.academic_year,
        tags=elective.topics[:3] if elective.topics else [],
        skills_required=elective.prerequisites[:2] if elective.prerequisites else [],
        related_areas=elective.career_paths[:2] if elective.career_paths else []
    )

# Endpoints
@router.get("/electives", response_model=List[ElectiveResponse])
async def get_electives(
    category: Optional[ElectiveCategory] = None,
    semester: Optional[int] = Query(None, ge=3, le=8),
    department: Optional[str] = None,
    is_available: Optional[bool] = None,
    honours_track: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get all available electives with optional filters"""
    try:
        # Build query
        query = {}
        if category:
            query["category"] = category
        if semester:
            query["semester"] = semester
        if department:
            query["department"] = department
        if is_available is not None:
            query["is_available"] = is_available
        if honours_track:
            query["honours_track_name"] = honours_track
        
        # Fetch from database
        electives = await Elective.find(query).skip(skip).limit(limit).to_list()
        
        # Convert to response format
        return [elective_to_response(elective) for elective in electives]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching electives: {str(e)}")

@router.get("/electives/{elective_id}", response_model=ElectiveResponse)
async def get_elective(elective_id: str):
    """Get specific elective by ID or code"""
    try:
        # Try to find by ID first
        elective = None
        try:
            elective = await Elective.get(PydanticObjectId(elective_id))
        except:
            # If not a valid ObjectId, try finding by code
            elective = await Elective.find_one(Elective.code == elective_id.upper())
        
        if not elective:
            raise HTTPException(status_code=404, detail="Elective not found")
        
        return elective_to_response(elective)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching elective: {str(e)}")

@router.get("/electives/branch/{branch}", response_model=List[ElectiveResponse])
async def get_electives_by_branch(branch: str, is_available: Optional[bool] = True):
    """Get electives by department/branch"""
    try:
        # Map branch aliases
        branch_map = {
            "cse": "Computer Science",
            "it": "Information Technology",
            "ece": "Electronics",
            "mech": "Mechanical",
            "civil": "Civil",
            "general": "General"
        }
        
        department = branch_map.get(branch.lower(), branch)
        
        query = {"department": department}
        if is_available is not None:
            query["is_available"] = is_available
        
        electives = await Elective.find(query).to_list()
        return [elective_to_response(elective) for elective in electives]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching electives by branch: {str(e)}")

@router.get("/electives/semester/{semester}", response_model=List[ElectiveResponse])
async def get_electives_by_semester(
    semester: int,
    category: Optional[ElectiveCategory] = None
):
    """Get electives by semester"""
    try:
        if semester < 3 or semester > 8:
            raise HTTPException(status_code=400, detail="Invalid semester. Must be between 3 and 8")
        
        query = {"semester": semester}
        if category:
            query["category"] = category
        
        electives = await Elective.find(query).to_list()
        return [elective_to_response(elective) for elective in electives]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching electives by semester: {str(e)}")

@router.get("/electives/honours/{track_name}", response_model=List[ElectiveResponse])
async def get_honours_electives(track_name: str):
    """Get electives for a specific honours track"""
    try:
        electives = await Elective.find({
            "is_honours_track": True,
            "honours_track_name": track_name
        }).to_list()
        
        if not electives:
            raise HTTPException(status_code=404, detail=f"No electives found for honours track: {track_name}")
        
        return [elective_to_response(elective) for elective in electives]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching honours electives: {str(e)}")

@router.get("/electives/recommended/{student_id}", response_model=List[ElectiveResponse])
async def get_recommended_electives(
    student_id: str,
    semester: Optional[int] = None,
    limit: int = 10
):
    """Get AI-powered elective recommendations for a student"""
    try:
        # This would integrate with the recommendation engine
        # For now, return top-rated electives
        query = {"is_available": True}
        if semester:
            query["semester"] = semester
        
        electives = await Elective.find(query).sort("-average_rating").limit(limit).to_list()
        
        # You can add more sophisticated recommendation logic here
        # based on student's interests, performance, career goals, etc.
        
        return [elective_to_response(elective) for elective in electives]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recommendations: {str(e)}")

@router.post("/electives", response_model=ElectiveResponse)
async def create_elective(
    elective_data: ElectiveCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new elective (admin only)"""
    try:
        # Check if user is admin/faculty
        if current_user.get("role") not in ["admin", "faculty"]:
            raise HTTPException(status_code=403, detail="Not authorized to create electives")
        
        # Check if elective with same code exists
        existing = await Elective.find_one(Elective.code == elective_data.code)
        if existing:
            raise HTTPException(status_code=400, detail=f"Elective with code {elective_data.code} already exists")
        
        # Create new elective
        elective = Elective(
            **elective_data.dict(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await elective.insert()
        
        # Invalidate recommendation engine cache so new elective is picked up
        CatalogueLoader.invalidate_cache()
        logger.info(f"✅ Elective {elective.code} created — catalogue cache invalidated")
        
        return elective_to_response(elective)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating elective: {str(e)}")

@router.put("/electives/{elective_id}", response_model=ElectiveResponse)
async def update_elective(
    elective_id: str,
    update_data: ElectiveUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing elective (admin only)"""
    try:
        # Check if user is admin/faculty
        if current_user.get("role") not in ["admin", "faculty"]:
            raise HTTPException(status_code=403, detail="Not authorized to update electives")
        
        # Find elective
        elective = await Elective.get(PydanticObjectId(elective_id))
        if not elective:
            raise HTTPException(status_code=404, detail="Elective not found")
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(elective, field, value)
        
        elective.updated_at = datetime.utcnow()
        await elective.save()
        
        # Invalidate recommendation engine cache
        CatalogueLoader.invalidate_cache()
        logger.info(f"✅ Elective {elective.code} updated — catalogue cache invalidated")
        
        return elective_to_response(elective)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating elective: {str(e)}")

@router.delete("/electives/{elective_id}")
async def delete_elective(
    elective_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an elective (admin only)"""
    try:
        # Check if user is admin
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to delete electives")
        
        # Find and delete elective
        elective = await Elective.get(PydanticObjectId(elective_id))
        if not elective:
            raise HTTPException(status_code=404, detail="Elective not found")
        
        await elective.delete()
        
        # Invalidate recommendation engine cache
        CatalogueLoader.invalidate_cache()
        logger.info(f"✅ Elective {elective.code} deleted — catalogue cache invalidated")
        
        return {"message": f"Elective {elective.code} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting elective: {str(e)}")

@router.post("/electives/{elective_id}/enroll")
async def enroll_in_elective(
    elective_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Enroll a student in an elective"""
    try:
        # Check if user is a student
        if current_user.get("role") != "student":
            raise HTTPException(status_code=403, detail="Only students can enroll in electives")
        
        # Find elective
        elective = await Elective.get(PydanticObjectId(elective_id))
        if not elective:
            raise HTTPException(status_code=404, detail="Elective not found")
        
        # Check availability
        if not elective.is_available:
            raise HTTPException(status_code=400, detail="Elective is not available for enrollment")
        
        # Check capacity
        if elective.current_enrollment >= elective.max_students:
            raise HTTPException(status_code=400, detail="Elective is full")
        
        # Check CGPA requirement
        if elective.min_cgpa_required:
            # You would need to fetch student's CGPA from student profile
            # For now, we'll skip this check
            pass
        
        # Increment enrollment count
        elective.current_enrollment += 1
        await elective.save()
        
        return {
            "message": f"Successfully enrolled in {elective.name}",
            "elective_code": elective.code,
            "current_enrollment": elective.current_enrollment
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enrolling in elective: {str(e)}")

@router.get("/electives/stats/summary")
async def get_electives_summary():
    """Get summary statistics of all electives"""
    try:
        total_electives = await Elective.count()
        
        # Get counts by category
        categories = {}
        for category in ElectiveCategory:
            count = await Elective.find({"category": category}).count()
            categories[category.value] = count
        
        # Get counts by semester
        semesters = {}
        for sem in range(3, 9):
            count = await Elective.find({"semester": sem}).count()
            semesters[f"Semester {sem}"] = count
        
        # Get honours tracks
        honours_tracks = await Elective.find({"is_honours_track": True}).distinct("honours_track_name")
        
        # Get average enrollment rate
        all_electives = await Elective.find({"is_available": True}).to_list()
        if all_electives:
            avg_enrollment = sum(e.current_enrollment for e in all_electives) / sum(e.max_students for e in all_electives) * 100
        else:
            avg_enrollment = 0
        
        return {
            "total_electives": total_electives,
            "categories": categories,
            "semesters": semesters,
            "honours_tracks": honours_tracks,
            "average_enrollment_rate": round(avg_enrollment, 2),
            "available_electives": await Elective.find({"is_available": True}).count(),
            "total_seats": sum(e.max_students for e in all_electives),
            "occupied_seats": sum(e.current_enrollment for e in all_electives)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")


# ══════════════════════════════════════════════════════════════════
#  ADMIN: Retrain Recommendation Engine
# ══════════════════════════════════════════════════════════════════

@router.post("/electives/admin/retrain")
async def retrain_recommendation_engine(
    current_user: dict = Depends(get_current_user)
):
    """
    Force-refresh the recommendation engine with latest DB electives.
    Admin only. Call this after bulk elective changes.
    """
    try:
        if current_user.get("role") not in ["admin", "faculty"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        from app.ml.models.recommendation_engine import refresh_engine
        engine = await refresh_engine()

        return {
            "success": True,
            "message": "Recommendation engine refreshed with latest elective data",
            "engine_trained": engine.is_trained,
            "elective_meta_count": len(engine.ELECTIVE_META),
            "open_elective_meta_count": len(engine.OPEN_ELECTIVE_META),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retrain error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Retrain failed: {str(e)}")


# ══════════════════════════════════════════════════════════════════
#  ADMIN: Seed Existing Hardcoded Electives into MongoDB
# ══════════════════════════════════════════════════════════════════

@router.post("/electives/admin/seed")
async def seed_electives_to_db(
    current_user: dict = Depends(get_current_user)
):
    """
    One-time seed: copies the hardcoded ELECTIVE_META and OPEN_ELECTIVE_META
    from the recommendation engine into MongoDB as Elective documents.
    
    This bootstraps the dynamic system. After this, admins can manage
    electives through the portal and they'll automatically update the engine.
    
    Skips electives that already exist (by code).
    """
    try:
        if current_user.get("role") not in ["admin", "faculty"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        from app.ml.models.recommendation_engine import (
            ELECTIVE_META, OPEN_ELECTIVE_META,
            SUBJECT_WEIGHTS, OE_SUBJECT_WEIGHTS,
            INTEREST_ELECTIVE_MAP, OE_INTEREST_MAP,
            PROJECT_SKILL_MAP, OE_PROJECT_SKILL_MAP,
            CONCEPT_MAP, OE_CONCEPT_MAP,
        )

        created = 0
        skipped = 0

        # Seed Program Electives
        for key, meta in ELECTIVE_META.items():
            code = meta.get("code", key)
            existing = await Elective.find_one(Elective.code == code)
            if existing:
                skipped += 1
                continue

            elective = Elective(
                code=code,
                name=meta.get("name", key),
                description=meta.get("description", ""),
                category=ElectiveCategory.PROGRAM_ELECTIVE,
                department="Information Technology",
                semester=5,
                credits=meta.get("credits", 3),
                prerequisites=[],
                topics=[],
                skills_covered=meta.get("skills", []),
                career_paths=meta.get("career_paths", []),
                difficulty_level=DifficultyLevel.INTERMEDIATE,
                engine_key=key,
                subject_weights=SUBJECT_WEIGHTS.get(key, {}),
                interest_mappings=[
                    {"area": area, "weight": weight}
                    for area, weight in INTEREST_ELECTIVE_MAP.get(key, [])
                ],
                project_keywords=PROJECT_SKILL_MAP.get(key, []),
                concept_prefixes=[
                    {"prefix": prefix, "weight": weight}
                    for prefix, weight in CONCEPT_MAP.get(key, [])
                ],
                modules=meta.get("modules", []),
                is_available=True,
            )
            await elective.insert()
            created += 1

        # Seed Open Electives
        for key, meta in OPEN_ELECTIVE_META.items():
            code = meta.get("code", key)
            existing = await Elective.find_one(Elective.code == code)
            if existing:
                skipped += 1
                continue

            elective = Elective(
                code=code,
                name=meta.get("name", key),
                description=meta.get("description", ""),
                category=ElectiveCategory.OPEN_ELECTIVE,
                department="Information Technology",
                semester=meta.get("semester", 7),
                credits=meta.get("credits", 3),
                prerequisites=[],
                topics=[],
                skills_covered=meta.get("skills", []),
                career_paths=meta.get("career_paths", []),
                difficulty_level=DifficultyLevel.INTERMEDIATE,
                engine_key=key,
                subject_weights=OE_SUBJECT_WEIGHTS.get(key, {}),
                interest_mappings=[
                    {"area": area, "weight": weight}
                    for area, weight in OE_INTEREST_MAP.get(key, [])
                ],
                project_keywords=OE_PROJECT_SKILL_MAP.get(key, []),
                concept_prefixes=[
                    {"prefix": prefix, "weight": weight}
                    for prefix, weight in OE_CONCEPT_MAP.get(key, [])
                ],
                modules=meta.get("modules", []),
                is_available=True,
            )
            await elective.insert()
            created += 1

        # Invalidate cache so engine picks up new data
        CatalogueLoader.invalidate_cache()

        # Refresh engine
        from app.ml.models.recommendation_engine import refresh_engine
        await refresh_engine()

        return {
            "success": True,
            "message": f"Seeded {created} electives, skipped {skipped} existing",
            "created": created,
            "skipped": skipped,
            "total_in_db": await Elective.count(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Seed error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Seed failed: {str(e)}")