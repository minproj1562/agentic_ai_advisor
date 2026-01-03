#academic-advisor-backend/app/scripts/create_sample_data.py
import asyncio
from datetime import datetime, timedelta
from app.core.database import init_db
from app.models.student_profile import StudentProfile, SemesterRecord, SubjectScore, Branch, Grade
from app.models.elective import Elective, InstructorInfo, DifficultyLevel, ElectiveCategory

async def create_sample_data():
    await init_db()
    
    # Create sample instructor
    instructor = InstructorInfo(
        name="Dr. Sarah Johnson",
        email="sarah.johnson@university.edu",
        department="Computer Science",
        expertise=["Machine Learning", "Data Science", "AI"],
        rating=4.8,
        total_ratings=45,
        office_location="CS Building Room 301",
        office_hours="Mon, Wed 2-4 PM"
    )
    await instructor.insert()
    
    # Create sample electives
    electives = [
        Elective(
            code="CS501",
            name="Advanced Machine Learning",
            description="Deep dive into modern machine learning techniques and applications",
            category=ElectiveCategory.TECHNICAL,
            difficulty=DifficultyLevel.ADVANCED,
            credits=4,
            prerequisites=["CS201", "CS301"],
            skills_developed=["Python", "TensorFlow", "Neural Networks"],
            career_impact=["AI Engineer", "Data Scientist", "ML Researcher"],
            tags=["AI", "ML", "Deep Learning"],
            instructor=instructor,
            max_students=40,
            semester_offered=[5, 6, 7]
        )
    ]
    
    for elective in electives:
        await elective.insert()
    
    # Create sample student profile
    student = StudentProfile(
        user_id="student_001",
        roll_number="IT2021001",
        name="John Doe",
        email="john.doe@student.university.edu",
        branch=Branch.IT,
        admission_year=2021,
        current_semester=5,
        current_academic_year="2024-25",
        skills=["Python", "Java", "SQL", "Data Structures"],
        interests=["AI", "Web Development", "Cloud Computing"],
        career_goals=["Software Engineer", "AI Specialist"],
        phone="+1234567890"
    )
    await student.insert()
    
    print("Sample data created successfully!")

if __name__ == "__main__":
    asyncio.run(create_sample_data())