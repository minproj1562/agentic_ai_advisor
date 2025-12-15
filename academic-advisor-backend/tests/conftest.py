"""
Test configuration and fixtures
"""

import asyncio
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.firebase_admin import firebase_manager
from app.config import settings

# Override settings for testing
settings.ENVIRONMENT = "testing"
settings.DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def init_firebase():
    """Initialize Firebase for testing"""
    # Use test Firebase project
    firebase_manager._initialize()
    yield
    # Cleanup if needed

@pytest.fixture
def client() -> Generator:
    """Create test client"""
    with TestClient(app) as c:
        yield c

@pytest.fixture
async def test_user():
    """Create test user"""
    user_data = {
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test User",
        "role": "student"
    }
    
    # Create user in Firebase
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
    """Get authentication headers"""
    from app.core.security import create_access_token
    
    token = create_access_token(data={"uid": test_user["uid"], "email": test_user["email"]})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def test_student():
    """Create test student"""
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
    
    await firebase_manager.create_document(
        collection="students",
        document_id=student_data["student_id"],
        data=student_data
    )
    
    yield student_data
    
    # Cleanup
    await firebase_manager.delete_document(
        collection="students",
        document_id=student_data["student_id"]
    )