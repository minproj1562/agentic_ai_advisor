# app/api/v1/endpoints/electives.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter()

# Define a Pydantic model for response (not Beanie document)
class ElectiveResponse(BaseModel):
    id: str
    title: str
    code: str
    prerequisites: List[str]
    difficulty: str
    semester: str
    credits: int
    instructor: Dict[str, Any]
    tags: List[str]
    career_impact: str
    industry_relevance: float
    syllabus: List[str]
    learning_outcomes: List[str]
    enrollment_count: int
    average_rating: float
    job_market_demand: float
    description: str
    skills_required: List[str]
    skills_gained: List[str]
    related_areas: List[str]
    department: str

# Mock data as dictionaries (not Beanie document instances)
mock_electives_data = [
    {
        "id": "1",
        "title": "Machine Learning",
        "code": "CS501",
        "prerequisites": ["CS301", "MATH202"],
        "difficulty": "Intermediate",
        "semester": "5",
        "credits": 4,
        "instructor": {
            "name": "Dr. Smith",
            "email": "smith@university.edu",
            "department": "Computer Science",
            "rating": 4.5,
            "expertise": ["AI", "Machine Learning"],
            "total_students": 150,
            "years_experience": 10
        },
        "tags": ["AI", "Data Science", "Python"],
        "career_impact": "High demand in tech industry",
        "industry_relevance": 0.9,
        "syllabus": ["Supervised Learning", "Neural Networks", "Deep Learning"],
        "learning_outcomes": ["Build ML models", "Understand AI concepts"],
        "enrollment_count": 45,
        "average_rating": 4.3,
        "job_market_demand": 0.85,
        "description": "Introduction to machine learning algorithms and applications",
        "skills_required": ["Python", "Statistics"],
        "skills_gained": ["TensorFlow", "Scikit-learn"],
        "related_areas": ["Data Science", "AI"],
        "department": "Computer Science"
    },
    {
        "id": "2",
        "title": "Cloud Computing",
        "code": "CS502",
        "prerequisites": ["CS302", "NET101"],
        "difficulty": "Intermediate",
        "semester": "6",
        "credits": 3,
        "instructor": {
            "name": "Dr. Johnson",
            "email": "johnson@university.edu",
            "department": "Computer Science",
            "rating": 4.2,
            "expertise": ["Cloud", "Distributed Systems"],
            "total_students": 120,
            "years_experience": 8
        },
        "tags": ["AWS", "Azure", "Cloud"],
        "career_impact": "Essential for modern software development",
        "industry_relevance": 0.95,
        "syllabus": ["Cloud Architecture", "Virtualization", "Containerization"],
        "learning_outcomes": ["Deploy cloud applications", "Manage cloud infrastructure"],
        "enrollment_count": 38,
        "average_rating": 4.4,
        "job_market_demand": 0.92,
        "description": "Fundamentals of cloud computing and deployment",
        "skills_required": ["Networking", "Linux"],
        "skills_gained": ["AWS", "Docker", "Kubernetes"],
        "related_areas": ["DevOps", "System Administration"],
        "department": "Computer Science"
    }
]

@router.get("/electives", response_model=List[ElectiveResponse])
async def get_electives():
    """Get all available electives"""
    return [ElectiveResponse(**data) for data in mock_electives_data]

@router.get("/electives/{elective_id}", response_model=ElectiveResponse)
async def get_elective(elective_id: str):
    """Get specific elective by ID"""
    elective_data = next((data for data in mock_electives_data if data["id"] == elective_id), None)
    if not elective_data:
        raise HTTPException(status_code=404, detail="Elective not found")
    return ElectiveResponse(**elective_data)

@router.get("/electives/branch/{branch}", response_model=List[ElectiveResponse])
async def get_electives_by_branch(branch: str):
    """Get electives by department/branch"""
    filtered_data = [data for data in mock_electives_data if data["department"].lower() == branch.lower()]
    return [ElectiveResponse(**data) for data in filtered_data]

@router.get("/electives/semester/{semester}", response_model=List[ElectiveResponse])
async def get_electives_by_semester(semester: str):
    """Get electives by semester"""
    filtered_data = [data for data in mock_electives_data if data["semester"] == semester]
    return [ElectiveResponse(**data) for data in filtered_data]