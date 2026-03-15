# scripts/fix_faculty.py
"""
Run: python -m scripts.fix_faculty
Finds faculty in all possible collections, normalizes field names,
consolidates into the 'faculty' collection.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime


async def main():
    from app.config import settings
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]

    faculty_coll = db["faculty"]
    
    print("=" * 60)
    print("  FACULTY DATA FIX")
    print("=" * 60)

    # 1. Check current state
    current = await faculty_coll.count_documents({})
    print(f"\n📊 Current 'faculty' collection: {current} documents")

    # 2. Check ALL collections for faculty-like data
    all_colls = await db.list_collection_names()
    print(f"\n🔍 Scanning {len(all_colls)} collections...")
    
    faculty_sources = []
    for coll_name in all_colls:
        c = db[coll_name]
        sample = await c.find_one({})
        if sample and isinstance(sample, dict):
            keys = set(sample.keys())
            # Faculty-like if it has name + (department or designation or subjects)
            if "name" in keys and any(k in keys for k in ["department", "designation", "subjects", "teaching_subjects", "expertise"]):
                count = await c.count_documents({})
                if count > 0:
                    faculty_sources.append((coll_name, count, keys))
                    print(f"   ✅ '{coll_name}': {count} docs (fields: {', '.join(sorted(keys - {'_id'}))})")

    # 3. Show what's in the faculty collection
    print(f"\n📋 Current faculty data:")
    existing = await faculty_coll.find({}).to_list(length=100)
    existing_emails = set()
    existing_names = set()
    for f in existing:
        name = f.get("name", "?")
        email = f.get("email", "?")
        ts = f.get("teaching_subjects", f.get("subjects", []))
        existing_emails.add(email.lower() if email else "")
        existing_names.add(name.lower() if name else "")
        print(f"   • {name} | {email} | teaches: {ts}")

    # 4. Find and merge faculty from other collections
    if len(faculty_sources) > 1:
        print(f"\n🔄 Found {len(faculty_sources)} collections with faculty data")
        
        for coll_name, count, keys in faculty_sources:
            if coll_name == "faculty":
                continue
            
            print(f"\n   Processing '{coll_name}' ({count} docs)...")
            coll = db[coll_name]
            docs = await coll.find({}).to_list(length=200)
            
            merged = 0
            skipped = 0
            for doc in docs:
                name = doc.get("name", "").strip()
                email = doc.get("email", "").strip()
                
                if not name:
                    continue
                
                # Skip if already exists
                if email.lower() in existing_emails or name.lower() in existing_names:
                    skipped += 1
                    continue
                
                # Normalize field names
                faculty_doc = {
                    "user_id": doc.get("user_id", doc.get("employee_id", doc.get("faculty_id", f"fac_{name.replace(' ','_').lower()}"))),
                    "name": name,
                    "email": email or f"{name.lower().replace(' ', '.').replace('dr.', '').strip('.')}@fcrit.ac.in",
                    "department": doc.get("department", ""),
                    "designation": doc.get("designation", doc.get("position", "Assistant Professor")),
                    "teaching_subjects": doc.get("teaching_subjects", doc.get("subjects", doc.get("courses_taught", []))),
                    "specializations": doc.get("specializations", doc.get("expertise", doc.get("research_areas", []))),
                    "qualifications": doc.get("qualifications", []),
                    "years_of_experience": doc.get("years_of_experience", doc.get("experience", 0)),
                    "phone": doc.get("phone", doc.get("contact", None)),
                    "office_location": doc.get("office_location", doc.get("cabin", None)),
                    "profile_setup_complete": False,
                    "status": "active",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    # Keep these for Beanie compatibility
                    "cv_url": None, "cv_file_name": None, "cv_uploaded_at": None,
                    "cv_parsed_data": {}, "uniform_profile": None,
                    "skills": [], "mentee_ids": [], "max_mentees": 10,
                    "available_slots": [], "publications": [], "research_areas": [],
                }
                
                # Handle list-of-dict specializations
                specs = faculty_doc["specializations"]
                if specs and isinstance(specs[0], dict):
                    faculty_doc["specializations"] = [s.get("name", str(s)) for s in specs]
                
                try:
                    await faculty_coll.insert_one(faculty_doc)
                    merged += 1
                    existing_emails.add(email.lower())
                    existing_names.add(name.lower())
                except Exception as e:
                    print(f"      ⚠️ Skip {name}: {e}")
            
            print(f"      ✅ Merged {merged}, skipped {skipped} duplicates")

    # 5. Fix field names in existing faculty
    print(f"\n🔧 Fixing field names in faculty collection...")
    
    # Rename 'subjects' → 'teaching_subjects' if needed
    r1 = await faculty_coll.update_many(
        {"subjects": {"$exists": True}, "teaching_subjects": {"$exists": False}},
        {"$rename": {"subjects": "teaching_subjects"}}
    )
    if r1.modified_count:
        print(f"   ✅ Renamed 'subjects'→'teaching_subjects' in {r1.modified_count} docs")
    
    # Rename 'expertise' → 'specializations'
    r2 = await faculty_coll.update_many(
        {"expertise": {"$exists": True}, "specializations": {"$exists": False}},
        {"$rename": {"expertise": "specializations"}}
    )
    if r2.modified_count:
        print(f"   ✅ Renamed 'expertise'→'specializations' in {r2.modified_count} docs")

    # 6. Final check
    final_count = await faculty_coll.count_documents({})
    print(f"\n📊 Final faculty count: {final_count}")
    
    # Show department distribution
    pipeline = [{"$group": {"_id": "$department", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    depts = await faculty_coll.aggregate(pipeline).to_list(length=50)
    for d in depts:
        print(f"   • {d['_id'] or '(no dept)'}: {d['count']}")

    # 7. Test faculty search
    print(f"\n🔍 Faculty search test:")
    test_subjects = ["Machine Learning", "Operating System", "Physics", "Mathematics", "Data Science"]
    for subj in test_subjects:
        import re
        pat = re.compile(re.escape(subj), re.IGNORECASE)
        found = await faculty_coll.find_one({
            "$or": [
                {"teaching_subjects": {"$regex": pat}},
                {"specializations": {"$regex": pat}},
            ]
        })
        if found:
            print(f"   ✅ '{subj}' → {found['name']}")
        else:
            print(f"   ❌ '{subj}' → no match")

    print("\n" + "=" * 60)
    client.close()

if __name__ == "__main__":
    asyncio.run(main())