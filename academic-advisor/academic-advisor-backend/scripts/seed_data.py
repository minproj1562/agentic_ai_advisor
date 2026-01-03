# scripts/seed_data.py
"""
Seed sample data for testing
"""

import asyncio
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from app.core.firebase_admin import firebase_manager
from app.utils.helpers import get_logger

logger = get_logger(__name__)


async def seed_students():
    """Seed sample students"""
    
    departments = ['CS', 'ECE', 'MECH', 'CIVIL', 'EEE']
    
    for i in range(50):
        student_id = f"STU{2021000 + i}"
        
        student_data = {
            'student_id': student_id,
            'name': f"Student {i+1}",
            'email': f"student{i+1}@university.edu",
            'department': random.choice(departments),
            'batch': random.randint(2020, 2024),
            'current_semester': random.randint(1, 8),
            'cgpa': round(random.uniform(5.0, 9.5), 2),
            'attendance': random.uniform(60, 100),
            'risk_level': random.choice(['low', 'medium', 'high']),
            'improvement_trend': random.choice(['improving', 'stable', 'declining']),
            'created_at': datetime.utcnow().isoformat()
        }
        
        await firebase_manager.create_document(
            collection='students',
            document_id=student_id,
            data=student_data
        )
        
        # Add performance data
        for sem in range(1, student_data['current_semester'] + 1):
            perf_data = {
                'semester': sem,
                'sgpa': round(random.uniform(5.0, 9.5), 2),
                'attendance': random.uniform(60, 100),
                'credits_earned': random.randint(20, 30),
                'created_at': datetime.utcnow().isoformat()
            }
            
            await firebase_manager.create_document(
                collection=f"students/{student_id}/performance",
                data=perf_data
            )
        
        logger.info(f"Created student: {student_id}")


async def seed_faculty():
    """Seed sample faculty"""
    
    departments = ['CS', 'ECE', 'MECH', 'CIVIL', 'EEE']
    
    for i in range(10):
        faculty_id = f"FAC{1000 + i}"
        
        faculty_data = {
            'faculty_id': faculty_id,
            'name': f"Dr. Faculty {i+1}",
            'email': f"faculty{i+1}@university.edu",
            'department': departments[i % 5],
            'designation': random.choice(['Assistant Professor', 'Associate Professor', 'Professor']),
            'experience_years': random.randint(2, 20),
            'created_at': datetime.utcnow().isoformat()
        }
        
        await firebase_manager.create_document(
            collection='faculty',
            document_id=faculty_id,
            data=faculty_data
        )
        
        logger.info(f"Created faculty: {faculty_id}")


async def seed_courses():
    """Seed sample courses"""
    
    course_types = ['core', 'elective', 'minor']
    departments = ['CS', 'ECE', 'MECH', 'CIVIL', 'EEE']
    
    for dept in departments:
        for i in range(10):
            course_id = f"{dept}_COURSE_{i+1}"
            
            course_data = {
                'course_id': course_id,
                'name': f"{dept} Course {i+1}",
                'department': dept,
                'type': random.choice(course_types),
                'credits': random.randint(2, 4),
                'semester': random.randint(1, 8),
                'min_cgpa': round(random.uniform(5.0, 7.0), 1),
                'created_at': datetime.utcnow().isoformat()
            }
            
            await firebase_manager.create_document(
                collection='courses',
                document_id=course_id,
                data=course_data
            )
            
            logger.info(f"Created course: {course_id}")


async def main():
    """Main seeding function"""
    logger.info("Starting data seeding...")
    
    # Initialize Firebase
    from app.core.firebase_admin import initialize_firebase
    initialize_firebase()
    
    # Seed data
    await seed_students()
    await seed_faculty()
    await seed_courses()
    
    logger.info("Data seeding completed!")


if __name__ == "__main__":
    asyncio.run(main())