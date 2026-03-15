# Save as check_collections.py and run: python check_collections.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["academic_advisor"]
    
    # List all collections
    collections = await db.list_collection_names()
    print(f"Collections: {collections}")
    
    # Check subjects
    count = await db["subjects"].count_documents({})
    print(f"\nSubjects count: {count}")
    if count > 0:
        sample = await db["subjects"].find_one()
        print(f"Sample subject _id type: {type(sample.get('_id'))}")
        print(f"Sample subject _id: {sample.get('_id')}")
        print(f"Sample subject keys: {list(sample.keys())}")
        print(f"Sample: code={sample.get('code')}, name={sample.get('name')}, semester={sample.get('semester')} (type: {type(sample.get('semester'))})")
        
        # Check sem 3 specifically
        sem3 = await db["subjects"].count_documents({"semester": 3})
        sem3_str = await db["subjects"].count_documents({"semester": "3"})
        print(f"\nSemester 3 (int): {sem3}")
        print(f"Semester 3 (str): {sem3_str}")
    
    # Check faculty
    fac_count = await db["faculty"].count_documents({})
    print(f"\nFaculty count: {fac_count}")
    if fac_count > 0:
        sample_f = await db["faculty"].find_one()
        print(f"Sample faculty keys: {list(sample_f.keys())}")
        print(f"Name: {sample_f.get('name')}")
        print(f"teaching_subjects: {sample_f.get('teaching_subjects')}")
        print(f"specializations: {sample_f.get('specializations')}")
    
    # Check topics
    topic_count = await db["topics"].count_documents({})
    print(f"\nTopics count: {topic_count}")
    
    # Check faculty_members (alternative collection name)
    fac2 = await db["faculty_members"].count_documents({})
    print(f"faculty_members count: {fac2}")
    
    client.close()

asyncio.run(check())