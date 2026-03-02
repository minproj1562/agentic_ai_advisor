# cleanup_and_seed.py
"""
Step 1: Show all existing students
Step 2: YOU pick which ones to KEEP (your profile + friends)
Step 3: Delete the rest (wrong roll format)
Step 4: Seed fresh IT students with correct 50YYXXX format
"""

import asyncio
import random
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import re

load_dotenv()

# ==================== NAMES ====================

FIRST_NAMES_MALE = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Reyansh", "Sai", "Arnav",
    "Dhruv", "Kabir", "Ritvik", "Sahil", "Rohan", "Kunal", "Harsh", "Pranav",
    "Yash", "Atharva", "Tanmay", "Om", "Shubham", "Tejas", "Parth", "Aniket",
    "Siddharth", "Nikhil", "Gaurav", "Manish", "Akash", "Rahul", "Varun",
    "Karan", "Mayank", "Abhishek", "Vishal", "Tushar", "Chinmay", "Soham",
    "Pratik", "Aarush", "Dev", "Ishan", "Jay", "Krishna", "Laksh", "Mihir",
    "Neel", "Ojas", "Piyush", "Rajat", "Shreyas", "Vedant", "Yug", "Advait",
    "Darsh", "Hemant", "Jayesh", "Krish", "Moksh", "Nakul", "Pranjal",
    "Rishi", "Samar", "Utkarsh", "Viraj", "Ayaan", "Devansh", "Hriday",
    "Anshul", "Bhavesh", "Chirag", "Deepak", "Farhan", "Girish", "Hitesh",
    "Jagdish", "Kartik", "Lalit", "Mohan", "Naman", "Omkar", "Pushkar",
]

FIRST_NAMES_FEMALE = [
    "Ananya", "Saanvi", "Aanya", "Aadhya", "Aarohi", "Diya", "Myra", "Sara",
    "Ira", "Anika", "Prisha", "Riya", "Kavya", "Navya", "Shreya", "Tanvi",
    "Pooja", "Sneha", "Sakshi", "Nikita", "Priya", "Neha", "Anjali", "Divya",
    "Nisha", "Komal", "Swati", "Pallavi", "Bhavna", "Rashmi", "Sonal",
    "Mansi", "Gauri", "Kriti", "Meera", "Tanya", "Vrinda", "Aditi", "Ishita",
    "Kiara", "Mahi", "Nandini", "Pari", "Ridhi", "Siya", "Trisha", "Vanya",
    "Yashvi", "Zara", "Avni", "Charvi", "Esha", "Gargi", "Hiral", "Jiya",
    "Kashvi", "Lavanya", "Mahika", "Naina", "Oviya", "Pihu", "Radhika",
    "Saira", "Tara", "Urvi", "Vaidehi", "Yukta", "Zoya", "Bhumi", "Chhavi",
    "Damini", "Ekta", "Falguni", "Gitanjali", "Harshita", "Isha", "Juhi",
]

LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Kumar", "Gupta", "Verma", "Joshi", "Desai",
    "Mehta", "Shah", "Reddy", "Nair", "Iyer", "Rao", "Pillai", "Menon",
    "Bhat", "Kulkarni", "Patil", "Deshmukh", "Jain", "Agarwal", "Mishra",
    "Pandey", "Tiwari", "Dubey", "Srivastava", "Yadav", "Chauhan", "Thakur",
    "Rathore", "Rajput", "Saxena", "Bose", "Mukherjee", "Banerjee", "Das",
    "Ghosh", "Roy", "Sen", "Chatterjee", "Dutta", "Karmakar", "Naik",
    "Shenoy", "Kamath", "Hegde", "Pai", "Shetty", "Gowda", "Fernandes",
    "D'Souza", "Rodrigues", "Pereira", "Lobo", "Mane", "Pawar", "Jadhav",
    "More", "Sawant", "Shinde", "Bhosale", "Kamble", "Gaikwad", "Chavan",
    "Kale", "Deshpande", "Gokhale", "Apte", "Kelkar", "Phadke", "Tambe",
    "Wagh", "Salunkhe", "Dhage", "Bhise", "Thorat", "Sutar", "Dalvi",
]

IT_CURRICULUM = {
    1: {
        "subjects": [
            ("FEC101", "Engineering Mathematics-I", 4, False, False),
            ("FEC102", "Engineering Physics-I", 3, False, False),
            ("FEC103", "Engineering Chemistry-I", 3, False, False),
            ("FEC104", "Engineering Mechanics", 4, False, False),
            ("FEC105", "Basic Electrical Engineering", 3, False, False),
            ("FEL101", "Programming Laboratory (C)", 2, True, False),
        ],
        "total_credits": 19,
    },
    2: {
        "subjects": [
            ("FEC201", "Engineering Mathematics-II", 4, False, False),
            ("FEC202", "Engineering Physics-II", 3, False, False),
            ("FEC203", "Engineering Chemistry-II", 3, False, False),
            ("FEC204", "Professional Communication", 2, False, False),
            ("FEC205", "C++ & Object Oriented Programming", 3, False, False),
            ("FEL201", "Programming Laboratory (Python)", 2, True, False),
        ],
        "total_credits": 17,
    },
    3: {
        "subjects": [
            ("ITC301", "Engineering Mathematics-III", 4, False, False),
            ("ITC302", "Discrete Structures & Graph Theory", 3, False, False),
            ("ITC303", "Data Structures", 3, False, False),
            ("ITC304", "Database Management Systems", 3, False, False),
            ("ITC305", "Digital Logic Design", 3, False, False),
            ("ITL301", "Data Structures Laboratory", 1, True, False),
            ("ITL302", "SQL Laboratory", 1, True, False),
        ],
        "total_credits": 18,
    },
    4: {
        "subjects": [
            ("ITC401", "Engineering Mathematics-IV", 4, False, False),
            ("ITC402", "Analysis of Algorithms", 3, False, False),
            ("ITC403", "Operating Systems", 3, False, False),
            ("ITC404", "Computer Networks", 3, False, False),
            ("ITC405", "Software Engineering", 3, False, False),
            ("ITL401", "OS Laboratory", 1, True, False),
            ("ITS401", "Full Stack Development Lab", 2, True, False),
        ],
        "total_credits": 19,
    },
    5: {
        "subjects": [
            ("ITC501", "Theory of Computation", 3, False, False),
            ("ITC502", "Cloud Computing", 3, False, False),
            ("ITC503", "Data Warehousing & Mining", 3, False, False),
            ("ITE501", "Program Elective-I", 3, False, True),
            ("ITL501", "Cloud Computing Lab", 1, True, False),
            ("ITL502", "Mobile App Development Lab", 1, True, False),
        ],
        "total_credits": 14,
    },
    6: {
        "subjects": [
            ("ITC601", "Cryptography & Network Security", 3, False, False),
            ("ITC602", "Machine Learning", 4, False, False),
            ("ITE601", "Program Elective-II", 3, False, True),
            ("ITO601", "Open Elective-I", 3, False, True),
            ("ITL601", "Data Science Laboratory", 1, True, False),
            ("ITS601", "DevOps Laboratory", 2, True, False),
        ],
        "total_credits": 16,
    },
    7: {
        "subjects": [
            ("ITC701", "Artificial Intelligence", 3, False, False),
            ("ITE701", "Program Elective-III", 3, False, True),
            ("ITE702", "Program Elective-IV", 3, False, True),
            ("ITO701", "Open Elective-II", 3, False, True),
            ("ITL701", "AI & Data Analytics Lab", 2, True, False),
            ("ITP701", "Major Project-A", 2, False, False),
        ],
        "total_credits": 16,
    },
    8: {
        "subjects": [
            ("ITE801", "Program Elective-V", 3, False, True),
            ("ITO801", "Open Elective-III", 3, False, True),
            ("ITP801", "Major Project-B", 4, False, False),
            ("ITI801", "Internship", 8, False, False),
        ],
        "total_credits": 18,
    },
}

SKILLS_POOL = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C", "Go", "Rust",
    "React", "Angular", "Vue.js", "Node.js", "Express.js", "Django", "Flask",
    "Spring Boot", "FastAPI", "Next.js", "HTML", "CSS", "Tailwind CSS",
    "MongoDB", "PostgreSQL", "MySQL", "Redis", "Firebase", "SQL",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Linux", "Git",
    "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
    "REST API", "GraphQL", "Microservices", "CI/CD", "Jenkins",
    "Figma", "Selenium", "JUnit", "MATLAB", "R", "Tableau", "Power BI",
    "Blockchain", "Solidity", "Flutter", "React Native", "Kotlin", "Swift",
]

INTERESTS_POOL = [
    "Machine Learning", "Artificial Intelligence", "Deep Learning",
    "Data Science", "Computer Vision", "Natural Language Processing",
    "Web Development", "Full Stack Development", "Backend Development",
    "Frontend Development", "Mobile App Development", "Cloud Computing",
    "DevOps", "Cybersecurity", "Blockchain", "IoT",
    "Competitive Programming", "Open Source", "Game Development",
    "Embedded Systems", "Robotics", "Quantum Computing",
    "AR/VR", "UI/UX Design", "Data Engineering", "MLOps",
]

CAREER_GOALS_POOL = [
    "Software Engineer", "Full Stack Developer", "Backend Developer",
    "Frontend Developer", "Data Scientist", "ML Engineer",
    "DevOps Engineer", "Cloud Architect", "Security Analyst",
    "Mobile Developer", "AI Researcher", "Product Manager",
    "System Architect", "Database Administrator", "Network Engineer",
    "Tech Lead", "Engineering Manager", "Startup Founder",
]


# ==================== HELPERS ====================

def is_valid_roll(roll: str) -> bool:
    """Check if roll matches 50YYXXX format"""
    if not roll:
        return False
    return bool(re.match(r'^50\d{5}$', roll))


def generate_roll_number(admission_year: int, index: int) -> str:
    yy = str(admission_year)[-2:]
    return f"50{yy}{index:03d}"


def generate_grade(score: float) -> tuple:
    if score >= 90: return "O", 10.0
    elif score >= 80: return "A+", 9.0
    elif score >= 70: return "A", 8.0
    elif score >= 60: return "B+", 7.0
    elif score >= 55: return "B", 6.0
    elif score >= 50: return "C", 5.0
    elif score >= 45: return "D", 4.0
    else: return "F", 0.0


def generate_subject_score(base_cgpa, is_practical, is_elective):
    base = (base_cgpa / 10.0) * 100
    variation = random.gauss(0, 12)
    if is_practical: base += random.uniform(3, 10)
    if is_elective: base += random.uniform(0, 5)
    return max(30, min(100, round(base + variation)))


def generate_student(admission_year, index):
    is_female = random.random() < 0.4
    first = random.choice(FIRST_NAMES_FEMALE if is_female else FIRST_NAMES_MALE)
    last = random.choice(LAST_NAMES)

    roll = generate_roll_number(admission_year, index)
    email_clean = f"{first.lower()}.{last.lower()}".replace("'", "").replace(" ", "")
    email = f"{email_clean}{random.randint(1, 99)}@student.fcrit.ac.in"

    current_semester = min(max((2026 - admission_year) * 2, 1), 8)
    base_cgpa = max(4.5, min(9.8, random.gauss(7.5, 1.2)))

    semester_records = []
    total_gp = 0
    total_cr = 0

    for sem in range(1, current_semester + 1):
        if sem not in IT_CURRICULUM:
            continue

        year_offset = (sem - 1) // 2
        academic_year = f"{admission_year + year_offset}-{admission_year + year_offset + 1}"

        subjects = []
        sem_gp = 0
        sem_cr = 0

        for code, name, credits, is_prac, is_elec in IT_CURRICULUM[sem]["subjects"]:
            score = generate_subject_score(base_cgpa, is_prac, is_elec)
            grade, gp = generate_grade(score)
            subjects.append({
                "subject_code": code,
                "subject_name": name,
                "credits": credits,
                "internal_marks": round(score * 0.3, 1),
                "external_marks": round(score * 0.7, 1),
                "total_marks": round(score),
                "grade": grade,
                "grade_points": gp,
                "is_elective": is_elec,
                "is_practical": is_prac,
            })
            sem_gp += gp * credits
            sem_cr += credits

        sgpa = round(sem_gp / sem_cr, 2) if sem_cr else 0
        total_gp += sem_gp
        total_cr += sem_cr

        if sem % 2 == 1:
            created = f"{admission_year + (sem-1)//2}-12-15 00:00:00"
        else:
            created = f"{admission_year + sem//2}-06-15 00:00:00"

        semester_records.append({
            "semester_number": sem,
            "academic_year": academic_year,
            "subjects": subjects,
            "sgpa": sgpa,
            "total_credits": sem_cr,
            "credits_earned": sem_cr,
            "is_complete": True,
            "created_at": created,
        })

    cgpa = round(total_gp / total_cr, 2) if total_cr else 0
    year_offset = (current_semester - 1) // 2
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")

    return {
        "user_id": f"student_{roll}",
        "roll_number": roll,
        "name": f"{first} {last}",
        "email": email,
        "branch": "IT",
        "admission_year": admission_year,
        "current_semester": current_semester,
        "current_academic_year": f"{admission_year + year_offset}-{admission_year + year_offset + 1}",
        "cgpa": cgpa,
        "total_credits_earned": total_cr,
        "total_credits_required": 160,
        "semester_records": semester_records,
        "skills": random.sample(SKILLS_POOL, random.randint(3, 8)),
        "interests": random.sample(INTERESTS_POOL, random.randint(2, 5)),
        "career_goals": random.sample(CAREER_GOALS_POOL, random.randint(1, 3)),
        "created_at": now,
        "last_updated": now,
    }


# ==================== MAIN ====================

async def main():
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DATABASE", "academic_advisor")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    collection = db.student_profiles

    # ========== STEP 1: SHOW ALL EXISTING ==========
    all_docs = await collection.find().to_list(length=1000)

    print("=" * 80)
    print("  STEP 1: ALL EXISTING STUDENTS IN DATABASE")
    print("=" * 80)

    valid_format = []
    invalid_format = []

    for i, doc in enumerate(all_docs):
        roll = doc.get("roll_number", "MISSING")
        name = doc.get("name", "Unknown")
        branch = doc.get("branch", "?")
        cgpa = doc.get("cgpa", 0)
        _id = str(doc.get("_id", ""))
        valid = is_valid_roll(roll)

        status = "✅" if valid else "❌"
        print(f"  {i+1:3d}. {status}  Roll: {roll:15s}  |  {name:25s}  |  {branch:6s}  |  CGPA: {cgpa:.2f}")

        if valid:
            valid_format.append(doc)
        else:
            invalid_format.append(doc)

    print(f"\n  ✅ Valid format (50YYXXX): {len(valid_format)}")
    print(f"  ❌ Invalid format:        {len(invalid_format)}")

    if not invalid_format:
        print("\n  🎉 All roll numbers are valid! Skipping cleanup.")
    else:
        # ========== STEP 2: PICK WHICH TO KEEP ==========
        print(f"\n{'=' * 80}")
        print("  STEP 2: STUDENTS WITH WRONG ROLL FORMAT")
        print("  Choose which ones to KEEP (your profile + friends)")
        print("=" * 80)

        keep_ids = []
        delete_ids = []

        for i, doc in enumerate(invalid_format):
            roll = doc.get("roll_number", "MISSING")
            name = doc.get("name", "Unknown")
            email = doc.get("email", "?")
            branch = doc.get("branch", "?")
            _id = doc.get("_id")

            print(f"\n  Student {i+1}/{len(invalid_format)}:")
            print(f"    Roll:   {roll}")
            print(f"    Name:   {name}")
            print(f"    Email:  {email}")
            print(f"    Branch: {branch}")

            choice = input("    KEEP this student? (y/n): ").strip().lower()

            if choice == "y" or choice == "yes":
                keep_ids.append(_id)
                # Ask if they want to fix the roll number
                new_roll = input(f"    Fix roll number? Enter new roll (or press Enter to keep '{roll}'): ").strip()
                if new_roll:
                    await collection.update_one(
                        {"_id": _id},
                        {"$set": {"roll_number": new_roll, "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")}}
                    )
                    print(f"    ✅ Roll updated: {roll} → {new_roll}")
                else:
                    print(f"    ✅ Keeping as-is")
            else:
                delete_ids.append(_id)

        # ========== STEP 3: DELETE BAD ONES ==========
        if delete_ids:
            print(f"\n{'=' * 80}")
            print(f"  STEP 3: DELETING {len(delete_ids)} students with bad roll numbers")
            print(f"  KEEPING {len(keep_ids)} students you selected")
            print("=" * 80)

            confirm = input(f"  Delete {len(delete_ids)} students? (yes/no): ").strip().lower()
            if confirm == "yes":
                result = await collection.delete_many({"_id": {"$in": delete_ids}})
                print(f"  ✅ Deleted {result.deleted_count} students")
            else:
                print("  ⏭️  Skipped deletion")
        else:
            print(f"\n  ✅ No students to delete — all kept!")

    # ========== STEP 4: SEED NEW STUDENTS ==========
    print(f"\n{'=' * 80}")
    print("  STEP 4: SEEDING NEW IT STUDENTS (70-75 per year)")
    print("  Roll format: 50YYXXX")
    print("=" * 80)

    # Get current roll numbers to avoid duplicates
    current_docs = await collection.find({}, {"roll_number": 1}).to_list(length=10000)
    existing_rolls = {doc.get("roll_number", "") for doc in current_docs}

    remaining = await collection.count_documents({})
    print(f"\n  Students currently in DB: {remaining}")
    print(f"  Existing roll numbers:    {len(existing_rolls)}")

    all_new = []
    admission_years = [2021, 2022, 2023, 2024, 2025]

    for year in admission_years:
        count = random.randint(70, 75)
        year_students = []
        skipped = 0

        for i in range(1, count + 1):
            roll = generate_roll_number(year, i)
            if roll in existing_rolls:
                skipped += 1
                continue
            student = generate_student(year, i)
            year_students.append(student)
            existing_rolls.add(roll)

        all_new.extend(year_students)

        if year_students:
            avg = round(sum(s["cgpa"] for s in year_students) / len(year_students), 2)
            print(f"\n  📚 {year}: {len(year_students)} new students (skipped {skipped} existing)")
            print(f"     Avg CGPA: {avg}  |  Semester: {year_students[0]['current_semester']}")
            print(f"     Rolls: {year_students[0]['roll_number']} ... {year_students[-1]['roll_number']}")
        else:
            print(f"\n  📚 {year}: All {skipped} rolls already exist, 0 new")

    if not all_new:
        print("\n  ⚠️  No new students to add!")
        client.close()
        return

    print(f"\n  Total new students to insert: {len(all_new)}")
    confirm = input("  Proceed with seeding? (yes/no): ").strip().lower()

    if confirm != "yes":
        print("  Cancelled.")
        client.close()
        return

    result = await collection.insert_many(all_new)
    print(f"\n  ✅ Inserted {len(result.inserted_ids)} new students!")

    # ========== FINAL SUMMARY ==========
    print(f"\n{'=' * 80}")
    print("  FINAL DATABASE SUMMARY")
    print("=" * 80)

    final_total = await collection.count_documents({})
    final_it = await collection.count_documents({"branch": "IT"})
    final_other = final_total - final_it

    print(f"  Total students:    {final_total}")
    print(f"  IT students:       {final_it}")
    print(f"  Other branches:    {final_other}")

    for year in admission_years:
        c = await collection.count_documents({"branch": "IT", "admission_year": year})
        print(f"  IT {year}:  {c:3d} students")

    # Verify all IT roll numbers are valid now
    print(f"\n  🔍 Roll Number Validation:")
    it_docs = await collection.find({"branch": "IT"}).to_list(length=1000)
    valid_count = sum(1 for d in it_docs if is_valid_roll(d.get("roll_number", "")))
    invalid_count = len(it_docs) - valid_count
    print(f"     Valid (50YYXXX): {valid_count}")
    print(f"     Invalid:        {invalid_count}")

    if invalid_count > 0:
        print(f"\n  ⚠️  Students with non-standard rolls (kept by you):")
        for d in it_docs:
            r = d.get("roll_number", "")
            if not is_valid_roll(r):
                print(f"     {r:15s}  |  {d.get('name', '?')}")

    # CGPA distribution
    print(f"\n  📊 CGPA Distribution (IT):")
    ranges = [
        ("Outstanding ≥9.0", {"$gte": 9.0}),
        ("Excellent 8.0-8.9", {"$gte": 8.0, "$lt": 9.0}),
        ("Good 7.0-7.9", {"$gte": 7.0, "$lt": 8.0}),
        ("Average 6.0-6.9", {"$gte": 6.0, "$lt": 7.0}),
        ("Below Avg <6.0", {"$lt": 6.0}),
    ]
    for label, q in ranges:
        c = await collection.count_documents({"branch": "IT", "cgpa": q})
        bar = "█" * (c // 3)
        print(f"     {label:20s}: {c:3d}  {bar}")

    # Sample rolls
    print(f"\n  📋 Sample Roll Numbers:")
    samples = await collection.find({"branch": "IT"}).sort("roll_number", 1).limit(5).to_list(5)
    for s in samples:
        print(f"     {s['roll_number']}  |  {s['name']:25s}  |  Sem {s['current_semester']}  |  CGPA {s['cgpa']:.2f}")
    print(f"     ...")
    samples = await collection.find({"branch": "IT"}).sort("roll_number", -1).limit(3).to_list(3)
    for s in reversed(samples):
        print(f"     {s['roll_number']}  |  {s['name']:25s}  |  Sem {s['current_semester']}  |  CGPA {s['cgpa']:.2f}")

    client.close()
    print(f"\n  ✅ All done! Restart backend:")
    print(f"     python -m uvicorn app.main:app --reload --port 8000")


if __name__ == "__main__":
    asyncio.run(main())