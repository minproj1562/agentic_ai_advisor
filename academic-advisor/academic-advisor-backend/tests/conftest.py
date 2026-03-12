"""
Test configuration and fixtures using MongoDB (Beanie) and Firebase.
"""

import asyncio
import pytest
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.main import app
from app.core.firebase_admin import firebase_manager
from app.config import settings
from app.models import (  # Import all Beanie document models
    Department, Subject, SubjectUnit, Topic, Abbreviation,
    ProgramElective, OpenElective, LiberalLearningCourse,
    MDMCourse, CreditStructure, Student, Faculty, etc
)

# Override settings for testing
settings.ENVIRONMENT = "testing"
settings.MONGODB_URL = "mongodb://localhost:27017"
settings.MONGODB_DB_NAME = "test_syllabus_db"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def init_firebase():
    """Initialize Firebase for testing."""
    firebase_manager._initialize()
    yield
    # Optional: cleanup after session


@pytest.fixture(scope="session")
async def init_db():
    """
    Initialize Beanie with test database.
    Creates a clean test database for the entire test session.
    """
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    # Drop database if it exists to start fresh
    await client.drop_database(settings.MONGODB_DB_NAME)

    # List all Beanie document models
    document_models = [
        Department, Subject, SubjectUnit, Topic, Abbreviation,
        ProgramElective, OpenElective, LiberalLearningCourse,
        MDMCourse, CreditStructure, Student, Faculty,
        # ... add any other models you have
    ]

    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=document_models
    )
    yield
    # Cleanup after all tests
    await client.drop_database(settings.MONGODB_DB_NAME)
    client.close()


@pytest.fixture
def client() -> Generator:
    """Create FastAPI test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def test_user(init_firebase):
    """Create test user in Firebase."""
    user_data = {
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test User",
        "role": "student"
    }
    user_id = await firebase_manager.create_user(
        email=user_data["email"],
        password=user_data["password"],
        display_name=user_data["name"]
    )
    user_data["uid"] = user_id
    yield user_data
    # Cleanup
    await firebase_manager.delete_user(user_id)


@pytest.fixture
async def auth_headers(test_user):
    """Get authentication headers for test user."""
    from app.core.security import create_access_token
    token = create_access_token(data={
        "uid": test_user["uid"],
        "email": test_user["email"]
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_student(init_db):
    """
    Create a test student document in MongoDB.
    Requires the Student model to be defined.
    """
    from app.models.student import Student

    student_data = {
        "student_id": "TEST001",
        "name": "Test Student",
        "email": "student@test.com",
        "department": "CS",
        "batch": 2024,
        "current_semester": 5,
        "cgpa": 7.5,
        "attendance": 85.0
    }
    student = Student(**student_data)
    await student.insert()
    yield student
    # Cleanup
    await student.delete()


@pytest.fixture
async def test_faculty(init_db):
    """
    Create a test faculty document in MongoDB.
    Requires the Faculty model to be defined.
    """
    from app.models.faculty import Faculty

    faculty_data = {
        "employee_id": "FAC001",
        "name": "Test Faculty",
        "email": "faculty@test.com",
        "department": "CS",
        "designation": "Professor"
    }
    faculty = Faculty(**faculty_data)
    await faculty.insert()
    yield faculty
    await faculty.delete()