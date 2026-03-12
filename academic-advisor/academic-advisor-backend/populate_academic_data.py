# populate_academic_data.py
"""
Academic calendar, events, holidays, and important dates
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime


async def populate_academic_data():
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client["fcrit_chatbot"]
    
    print("🔄 Populating academic calendar and events...")
    
    # Clear existing
    await db.academic_calendar.delete_many({})
    await db.holidays.delete_many({})
    await db.events.delete_many({})
    
    # Academic Calendar 2024-25
    academic_calendar = [
        {
            "academic_year": "2024-25",
            "semester": "Odd Semester",
            "events": [
                {"event": "Commencement of Odd Semester", "date": "2024-07-15", "type": "academic"},
                {"event": "Last Date for Admission (FE)", "date": "2024-08-15", "type": "admission"},
                {"event": "Unit Test 1", "date": "2024-08-19", "end_date": "2024-08-24", "type": "exam"},
                {"event": "Mid Semester Examination", "date": "2024-09-16", "end_date": "2024-09-21", "type": "exam"},
                {"event": "Unit Test 2", "date": "2024-10-14", "end_date": "2024-10-19", "type": "exam"},
                {"event": "Practical Examination", "date": "2024-11-04", "end_date": "2024-11-16", "type": "exam"},
                {"event": "End Semester Examination", "date": "2024-11-18", "end_date": "2024-12-07", "type": "exam"},
                {"event": "Winter Vacation", "date": "2024-12-23", "end_date": "2025-01-01", "type": "vacation"},
            ]
        },
        {
            "academic_year": "2024-25",
            "semester": "Even Semester",
            "events": [
                {"event": "Commencement of Even Semester", "date": "2025-01-06", "type": "academic"},
                {"event": "Unit Test 1", "date": "2025-02-10", "end_date": "2025-02-15", "type": "exam"},
                {"event": "Mid Semester Examination", "date": "2025-03-10", "end_date": "2025-03-15", "type": "exam"},
                {"event": "Unit Test 2", "date": "2025-04-07", "end_date": "2025-04-12", "type": "exam"},
                {"event": "Practical Examination", "date": "2025-04-28", "end_date": "2025-05-10", "type": "exam"},
                {"event": "End Semester Examination", "date": "2025-05-12", "end_date": "2025-05-31", "type": "exam"},
                {"event": "Summer Vacation", "date": "2025-06-01", "end_date": "2025-07-14", "type": "vacation"},
            ]
        }
    ]
    
    # Holidays 2024-25
    holidays = [
        {"name": "Independence Day", "date": "2024-08-15", "type": "national"},
        {"name": "Raksha Bandhan", "date": "2024-08-19", "type": "festival"},
        {"name": "Janmashtami", "date": "2024-08-26", "type": "festival"},
        {"name": "Ganesh Chaturthi", "date": "2024-09-07", "type": "festival"},
        {"name": "Anant Chaturdashi", "date": "2024-09-17", "type": "festival"},
        {"name": "Gandhi Jayanti", "date": "2024-10-02", "type": "national"},
        {"name": "Dussehra", "date": "2024-10-12", "type": "festival"},
        {"name": "Diwali Vacation", "date": "2024-10-31", "end_date": "2024-11-03", "type": "festival"},
        {"name": "Guru Nanak Jayanti", "date": "2024-11-15", "type": "festival"},
        {"name": "Christmas", "date": "2024-12-25", "type": "festival"},
        {"name": "Republic Day", "date": "2025-01-26", "type": "national"},
        {"name": "Maha Shivaratri", "date": "2025-02-26", "type": "festival"},
        {"name": "Holi", "date": "2025-03-14", "type": "festival"},
        {"name": "Good Friday", "date": "2025-04-18", "type": "festival"},
        {"name": "Maharashtra Day", "date": "2025-05-01", "type": "state"},
        {"name": "Buddha Purnima", "date": "2025-05-12", "type": "festival"},
    ]
    
    # College Events
    events = [
        {
            "name": "Orientation Program (FE)",
            "date": "2024-07-15",
            "end_date": "2024-07-17",
            "type": "orientation",
            "description": "Welcome and orientation for First Year students",
            "venue": "Main Auditorium",
            "organizer": "Student Affairs Office"
        },
        {
            "name": "Technical Workshop - Python for Data Science",
            "date": "2024-08-10",
            "type": "workshop",
            "description": "Hands-on workshop on Python libraries for data science",
            "venue": "Computer Lab 1",
            "organizer": "CSE Department",
            "target_audience": "SE, TE, BE students"
        },
        {
            "name": "Hackathon - Code Fiesta 2024",
            "date": "2024-09-07",
            "end_date": "2024-09-08",
            "type": "competition",
            "description": "24-hour coding hackathon",
            "venue": "CSE Department Labs",
            "organizer": "CSE Student Association",
            "registration_deadline": "2024-09-01"
        },
        {
            "name": "Industry Talk - AI in Healthcare",
            "date": "2024-09-20",
            "type": "seminar",
            "description": "Guest lecture by industry expert on AI applications in healthcare",
            "venue": "Seminar Hall",
            "organizer": "CSE Department",
            "speaker": "Dr. John Smith, Google Health"
        },
        {
            "name": "TECHTONIC - Annual Technical Festival",
            "date": "2024-10-04",
            "end_date": "2024-10-06",
            "type": "festival",
            "description": "Annual technical festival with competitions, workshops, and exhibitions",
            "venue": "Entire Campus",
            "organizer": "Student Council"
        },
        {
            "name": "Campus Placement Drive - TCS",
            "date": "2024-10-15",
            "type": "placement",
            "description": "Campus recruitment drive by TCS",
            "venue": "Placement Cell",
            "organizer": "Training and Placement Cell",
            "eligibility": "BE students with 60% aggregate"
        },
        {
            "name": "Workshop - Cloud Computing with AWS",
            "date": "2024-11-02",
            "type": "workshop",
            "description": "AWS certified workshop on cloud services",
            "venue": "Computer Lab 2",
            "organizer": "CSE Department",
            "certification": "AWS Participation Certificate"
        },
        {
            "name": "Sports Week - SPARDHA 2024",
            "date": "2024-12-09",
            "end_date": "2024-12-14",
            "type": "sports",
            "description": "Annual sports week with inter-departmental competitions",
            "venue": "Sports Ground",
            "organizer": "Sports Committee"
        },
        {
            "name": "Project Exhibition (BE)",
            "date": "2025-04-20",
            "end_date": "2025-04-21",
            "type": "exhibition",
            "description": "Final year project exhibition",
            "venue": "College Campus",
            "organizer": "All Departments"
        },
        {
            "name": "Alumni Meet 2025",
            "date": "2025-01-18",
            "type": "alumni",
            "description": "Annual alumni gathering",
            "venue": "Main Auditorium",
            "organizer": "Alumni Cell"
        },
        {
            "name": "Convocation Ceremony",
            "date": "2025-06-15",
            "type": "ceremony",
            "description": "Annual convocation for graduating students",
            "venue": "Main Auditorium",
            "organizer": "College Administration"
        }
    ]
    
    # Insert data
    await db.academic_calendar.insert_many(academic_calendar)
    await db.holidays.insert_many(holidays)
    await db.events.insert_many(events)
    
    print(f"✅ Inserted {len(academic_calendar)} academic calendar entries")
    print(f"✅ Inserted {len(holidays)} holidays")
    print(f"✅ Inserted {len(events)} events")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(populate_academic_data())