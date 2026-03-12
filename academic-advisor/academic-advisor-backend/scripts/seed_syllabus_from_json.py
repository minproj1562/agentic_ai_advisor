# scripts/seed_syllabus_from_json.py
"""
Seed syllabus data from JSON files into MongoDB
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.syllabus import Subject, Topic, Department


async def load_json_file(filepath: str) -> dict:
    """Load a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


async def seed_from_parsed_syllabi(json_path: str):
    """Seed subjects and topics from parsed_syllabi.json."""
    print(f"📂 Loading {json_path}...")
    
    data = await load_json_file(json_path)
    
    if isinstance(data, list):
        subjects_data = data
    elif isinstance(data, dict):
        subjects_data = data.get('subjects', data.get('data', [data]))
    else:
        print("❌ Unknown data format")
        return
    
    print(f"  Found {len(subjects_data)} subject entries")
    
    subjects_created = 0
    topics_created = 0
    
    for subj_data in subjects_data:
        try:
            # Create subject
            code = subj_data.get('code', subj_data.get('subject_code', ''))
            name = subj_data.get('name', subj_data.get('subject_name', ''))
            
            if not code or not name:
                continue
            
            # Check if exists
            existing = await Subject.find_one(Subject.code == code)
            if existing:
                print(f"  ⏭️ Subject {code} already exists")
                continue
            
            # Build units with topics
            units = []
            units_data = subj_data.get('units', [])
            
            for unit_data in units_data:
                unit_topics = []
                topics_data = unit_data.get('topics', [])
                
                for topic_data in topics_data:
                    if isinstance(topic_data, str):
                        unit_topics.append({
                            "name": topic_data,
                            "definition": "",
                            "key_points": [],
                        })
                    elif isinstance(topic_data, dict):
                        unit_topics.append({
                            "name": topic_data.get('name', ''),
                            "definition": topic_data.get('definition', ''),
                            "explanation": topic_data.get('explanation', ''),
                            "key_points": topic_data.get('key_points', []),
                            "examples": topic_data.get('examples', []),
                            "difficulty_level": topic_data.get('difficulty_level', 'medium'),
                            "exam_frequency": topic_data.get('exam_frequency', 'medium'),
                        })
                        
                        # Also create standalone topic
                        topic_doc = Topic(
                            name=topic_data.get('name', ''),
                            subject_code=code,
                            unit_number=unit_data.get('number'),
                            unit_title=unit_data.get('title', ''),
                            definition=topic_data.get('definition', ''),
                            explanation=topic_data.get('explanation', ''),
                            key_points=topic_data.get('key_points', []),
                            examples=topic_data.get('examples', []),
                            difficulty_level=topic_data.get('difficulty_level', 'medium'),
                            exam_frequency=topic_data.get('exam_frequency', 'medium'),
                        )
                        await topic_doc.insert()
                        topics_created += 1
                
                units.append({
                    "number": unit_data.get('number', unit_data.get('unit_number')),
                    "title": unit_data.get('title', unit_data.get('unit_title', '')),
                    "hours": unit_data.get('hours', 0),
                    "topics": unit_topics,
                })
            
            # Create subject
            subject = Subject(
                code=code,
                name=name,
                semester=subj_data.get('semester', 0),
                credits=subj_data.get('credits', 0),
                department=subj_data.get('department', ''),
                description=subj_data.get('description', ''),
                units=units,
                learning_outcomes=subj_data.get('learning_outcomes', []),
                prerequisites=subj_data.get('prerequisites', []),
            )
            
            await subject.insert()
            subjects_created += 1
            print(f"  ✅ Created subject: {code} - {name}")
            
        except Exception as e:
            print(f"  ❌ Error processing subject: {e}")
    
    print(f"\n📊 Summary: {subjects_created} subjects, {topics_created} topics created")


async def main():
    """Main seeding function."""
    print("=" * 60)
    print("🌱 Seeding Syllabus Data from JSON")
    print("=" * 60)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    await init_beanie(
        database=db,
        document_models=[Subject, Topic, Department]
    )
    
    # Find JSON files
    json_dir = Path(__file__).parent.parent / "json_data"
    
    if not json_dir.exists():
        print(f"❌ JSON directory not found: {json_dir}")
        return
    
    print(f"📂 Looking for JSON files in: {json_dir}")
    
    json_files = list(json_dir.glob("*.json"))
    print(f"  Found {len(json_files)} JSON files")
    
    for json_file in json_files:
        print(f"\n📄 Processing: {json_file.name}")
        try:
            await seed_from_parsed_syllabi(str(json_file))
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Final count
    subject_count = await Subject.find().count()
    topic_count = await Topic.find().count()
    
    print("\n" + "=" * 60)
    print(f"✅ Seeding complete!")
    print(f"   Subjects in DB: {subject_count}")
    print(f"   Topics in DB: {topic_count}")
    print("=" * 60)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(main())