# app/models/analytics.py
class StudentResourceActivity(Document):
    student_id: str = Field(index=True)
    resource_id: str = Field(index=True)
    activity_type: str  # viewed, completed, bookmarked
    progress: float = 0.0
    time_spent: int = 0  # in seconds
    rating: Optional[float] = None
    feedback: Optional[str] = None
    is_bookmarked: bool = False
    last_accessed: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "student_resource_activity"
        indexes = [
            [("student_id", 1), ("resource_id", 1)],
            "activity_type",
            "last_accessed"
        ]

class WeaknessAnalysisResult(Document):
    student_id: str = Field(index=True)
    subject_code: str
    subject: str
    overall_score: float
    semester: str
    topics: List[Dict[str, Any]]
    ai_analysis: Dict[str, Any]
    generated_at: datetime = Field(default_factory=datetime.now)
    is_current: bool = True
    
    class Settings:
        name = "weakness_analysis"
        indexes = [
            [("student_id", 1), ("generated_at", -1)],
            "subject_code",
            "is_current"
        ]