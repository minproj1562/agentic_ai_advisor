"""
Tests for student analysis endpoints
"""

import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_get_students_list(client: TestClient, auth_headers):
    """Test getting students list"""
    response = client.get(
        "/api/v1/student-analysis/list",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_get_student_details(client: TestClient, auth_headers, test_student):
    """Test getting student details"""
    response = client.get(
        f"/api/v1/student-analysis/{test_student['student_id']}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == test_student["student_id"]

@pytest.mark.asyncio
async def test_trigger_weakness_analysis(client: TestClient, auth_headers, test_student):
    """Test triggering weakness analysis"""
    response = client.post(
        f"/api/v1/student-analysis/{test_student['student_id']}/weakness-analysis",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "initiated"

@pytest.mark.asyncio
async def test_department_trends(client: TestClient, auth_headers):
    """Test getting department trends"""
    response = client.get(
        "/api/v1/student-analysis/trends/department/CS",
        headers=auth_headers,
        params={"metric": "cgpa"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "trends" in data

@pytest.mark.asyncio
async def test_export_data(client: TestClient, auth_headers):
    """Test data export"""
    response = client.get(
        "/api/v1/student-analysis/export/csv",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"