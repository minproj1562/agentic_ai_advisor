# app/models/elective.py
class InstructorInfo(BaseModel):
    id: str
    name: str
    rating: float
    expertise: List[str]
    total_students: int = 0
    years_experience: int = 0

class Elective(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    code: str
    prerequisites: List[str] = Field(default_factory=list)
    difficulty: str  # Beginner, Intermediate, Advanced
    semester: str
    credits: int
    instructor: InstructorInfo
    tags: List[str] = Field(default_factory=list)
    career_impact: str
    industry_relevance: float
    syllabus: List[str] = Field(default_factory=list)
    learning_outcomes: List[str] = Field(default_factory=list)
    enrollment_count: int = 0
    average_rating: float = 0.0
    job_market_demand: float = 0.0
    
    # For ML matching
    description: str
    skills_required: List[str] = Field(default_factory=list)
    skills_gained: List[str] = Field(default_factory=list)
    related_areas: List[str] = Field(default_factory=list)
    
    # Metadata
    department: str
    is_active: bool = True
    max_students: int = 60
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "electives"
        indexes = [
            "code",
            "semester",
            "difficulty",
            "tags",
            "is_active"
        ]