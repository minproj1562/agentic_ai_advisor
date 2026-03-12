# scripts/seed_faculty_data.py
"""
Complete Seed Script for Academic Advisor
Based on FCRIT B.Tech CSE/IT Curriculum (R2024.1 / R25)

Run: python scripts/seed_data.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.models.faculty import (
    Faculty, FacultyStatus, UniformFacultyProfile,
    PersonalInfo, AcademicQualifications, CurrentPosition,
    ResearchExpertise, TeachingInfo, FacultyAvailability,
    PublicationSummary, Degree, MeetingSlot
)
from app.models.student_performance import StudentPerformance, Subject, StudentInfo
from app.models.student_profile import StudentProfile, SemesterRecord, SubjectScore, Branch
from app.models.student_projects import StudentProject, ProjectType
from app.models.meeting_request import MeetingRequest, MeetingRequestStatus, ScheduledMeeting
from app.models.elective import Elective, ElectiveCategory, DifficultyLevel
from app.config import settings


# ==================== FCRIT CURRICULUM DATA ====================

DEPARTMENTS = {
    "CSE": "Computer Science & Engineering",
    "IT": "Information Technology",
    "EXTC": "Electronics & Telecommunication",
    "MECH": "Mechanical Engineering",
    "CIVIL": "Civil Engineering"
}

# Subjects per semester (CSE/IT based on FCRIT curriculum)
SEMESTER_SUBJECTS = {
    1: [
        {"code": "FEC101", "name": "Engineering Mathematics-I", "credits": 4, "type": "BSC"},
        {"code": "FEC102", "name": "Engineering Physics-I", "credits": 3, "type": "BSC"},
        {"code": "FEC103", "name": "Engineering Chemistry-I", "credits": 3, "type": "BSC"},
        {"code": "FEC104", "name": "Engineering Mechanics", "credits": 4, "type": "ESC"},
        {"code": "FEC105", "name": "Basic Electrical Engineering", "credits": 3, "type": "ESC"},
        {"code": "FEL101", "name": "Programming Laboratory (C)", "credits": 2, "type": "LBC"},
    ],
    2: [
        {"code": "FEC201", "name": "Engineering Mathematics-II", "credits": 4, "type": "BSC"},
        {"code": "FEC202", "name": "Engineering Physics-II", "credits": 3, "type": "BSC"},
        {"code": "FEC203", "name": "Engineering Chemistry-II", "credits": 3, "type": "BSC"},
        {"code": "FEC204", "name": "Professional Communication", "credits": 2, "type": "AEC"},
        {"code": "FEC205", "name": "Basic Electronics Engineering", "credits": 3, "type": "ESC"},
        {"code": "FEL201", "name": "Programming Laboratory (Java)", "credits": 2, "type": "LBC"},
    ],
    3: [
        {"code": "CSC301", "name": "Engineering Mathematics-III", "credits": 4, "type": "PCC"},
        {"code": "CSC302", "name": "Discrete Structures & Graph Theory", "credits": 3, "type": "PCC"},
        {"code": "CSC303", "name": "Data Structures", "credits": 3, "type": "PCC"},
        {"code": "CSC304", "name": "Database Management Systems", "credits": 3, "type": "PCC"},
        {"code": "CSL301", "name": "Data Structures Laboratory", "credits": 1, "type": "LBC"},
        {"code": "CSL302", "name": "SQL Laboratory", "credits": 1, "type": "LBC"},
        {"code": "CSS301", "name": "Python Laboratory", "credits": 2, "type": "SBL"},
    ],
    4: [
        {"code": "CSC401", "name": "Engineering Mathematics-IV", "credits": 4, "type": "PCC"},
        {"code": "CSC402", "name": "Analysis of Algorithms", "credits": 3, "type": "PCC"},
        {"code": "CSC403", "name": "Operating Systems", "credits": 3, "type": "PCC"},
        {"code": "CSC404", "name": "Computer Networks", "credits": 3, "type": "PCC"},
        {"code": "CSC405", "name": "Software Engineering", "credits": 3, "type": "PCC"},
        {"code": "CSL401", "name": "Networks Laboratory", "credits": 1, "type": "LBC"},
        {"code": "CSS401", "name": "Full Stack Development Lab", "credits": 2, "type": "SBL"},
    ],
    5: [
        {"code": "CSC501", "name": "Theory of Computation", "credits": 3, "type": "PCC"},
        {"code": "CSC502", "name": "Computer Networks", "credits": 3, "type": "PCC"},
        {"code": "CSC503", "name": "Multidisciplinary Minor", "credits": 3, "type": "MDM"},
        {"code": "CSE501", "name": "Program Elective-I", "credits": 3, "type": "PEC"},
        {"code": "CSL501", "name": "Cloud Computing Lab", "credits": 1, "type": "LBC"},
        {"code": "CSL502", "name": "Mobile App Development Lab", "credits": 1, "type": "LBC"},
    ],
    6: [
        {"code": "CSC601", "name": "Cryptography & Network Security", "credits": 3, "type": "PCC"},
        {"code": "CSC602", "name": "Multidisciplinary Minor", "credits": 4, "type": "MDM"},
        {"code": "CSE601", "name": "Program Elective-II", "credits": 3, "type": "PEC"},
        {"code": "CSO601", "name": "Open Elective-I", "credits": 3, "type": "OEC"},
        {"code": "CSL601", "name": "Data Science Laboratory", "credits": 1, "type": "LBC"},
        {"code": "CSS601", "name": "DevOps Laboratory", "credits": 2, "type": "SBL"},
    ],
    7: [
        {"code": "CSC701", "name": "Artificial Intelligence", "credits": 3, "type": "PCC"},
        {"code": "CSE701", "name": "Program Elective-III", "credits": 3, "type": "PEC"},
        {"code": "CSE702", "name": "Program Elective-IV", "credits": 3, "type": "PEC"},
        {"code": "CSO701", "name": "Open Elective-II", "credits": 3, "type": "OEC"},
        {"code": "CSL701", "name": "AI & Data Analytics Lab", "credits": 2, "type": "LBC"},
        {"code": "CSP701", "name": "Major Project-A", "credits": 2, "type": "MJP"},
    ],
    8: [
        {"code": "CSE801", "name": "Program Elective-V", "credits": 3, "type": "PEC"},
        {"code": "CSO801", "name": "Open Elective-III", "credits": 3, "type": "OEC"},
        {"code": "CSP801", "name": "Major Project-B", "credits": 4, "type": "MJP"},
        {"code": "CSI801", "name": "Internship", "credits": 8, "type": "INT"},
    ],
}

# Program Electives (PEC) - FCRIT curriculum
PROGRAM_ELECTIVES = [
    {"code": "CSE5011", "name": "Cloud Computing Services", "semester": 5, "domain": "Cloud"},
    {"code": "CSE5012", "name": "Data Warehousing & Mining", "semester": 5, "domain": "Data Science"},
    {"code": "CSE5013", "name": "Machine Learning", "semester": 5, "domain": "AI/ML"},
    {"code": "CSE5014", "name": "Image Processing", "semester": 5, "domain": "AI/ML"},
    {"code": "CSE6021", "name": "IT Infrastructure Management", "semester": 6, "domain": "Infrastructure"},
    {"code": "CSE6022", "name": "Deep Learning", "semester": 6, "domain": "AI/ML"},
    {"code": "CSE6023", "name": "Wireless Technologies", "semester": 6, "domain": "Networks"},
    {"code": "CSE6024", "name": "Natural Language Processing", "semester": 6, "domain": "AI/ML"},
    {"code": "CSE7031", "name": "Big Data Analytics", "semester": 7, "domain": "Data Science"},
    {"code": "CSE7032", "name": "Blockchain Technology", "semester": 7, "domain": "Blockchain"},
    {"code": "CSE7033", "name": "Internet of Things", "semester": 7, "domain": "IoT"},
    {"code": "CSE7034", "name": "Quantum Computing", "semester": 7, "domain": "Emerging Tech"},
    {"code": "CSE7035", "name": "Ethical Hacking", "semester": 7, "domain": "Security"},
    {"code": "CSE8041", "name": "Augmented & Virtual Reality", "semester": 8, "domain": "Emerging Tech"},
    {"code": "CSE8042", "name": "Reinforcement Learning", "semester": 8, "domain": "AI/ML"},
    {"code": "CSE8043", "name": "Edge Computing", "semester": 8, "domain": "Cloud"},
]

# Open Electives (OEC)
OPEN_ELECTIVES = [
    {"code": "OEC601", "name": "Project Management", "credits": 3},
    {"code": "OEC602", "name": "Financial Planning & Analysis", "credits": 3},
    {"code": "OEC603", "name": "Entrepreneurship Development", "credits": 3},
    {"code": "OEC604", "name": "Intellectual Property Rights", "credits": 3},
    {"code": "OEC701", "name": "Environmental Management", "credits": 3},
    {"code": "OEC702", "name": "Professional Ethics", "credits": 3},
]

# Honours/Minor Tracks
HONOURS_TRACKS = [
    {"name": "Cybersecurity", "credits": 18, "min_cgpa": 7.5},
    {"name": "Artificial Intelligence & Machine Learning", "credits": 18, "min_cgpa": 7.5},
    {"name": "Internet of Things", "credits": 18, "min_cgpa": 7.5},
    {"name": "Data Science", "credits": 18, "min_cgpa": 7.5},
]

# Research Areas for Faculty
RESEARCH_AREAS = [
    "Machine Learning", "Deep Learning", "Natural Language Processing",
    "Computer Vision", "Data Science", "Cybersecurity", "Cloud Computing",
    "Internet of Things", "Blockchain", "Artificial Intelligence",
    "Software Engineering", "Database Systems", "Distributed Systems",
    "Big Data Analytics", "Edge Computing", "Quantum Computing"
]

# Skills
TECHNICAL_SKILLS = [
    "Python", "Java", "C++", "JavaScript", "TypeScript", "React", "Node.js",
    "TensorFlow", "PyTorch", "Scikit-learn", "SQL", "MongoDB", "PostgreSQL",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "Linux",
    "Flask", "Django", "FastAPI", "Spring Boot", "Angular", "Vue.js"
]

# Sample Names
FIRST_NAMES_MALE = ["Rahul", "Amit", "Vikram", "Arjun", "Rohan", "Siddharth", "Aditya", "Karan", "Pranav", "Yash"]
FIRST_NAMES_FEMALE = ["Priya", "Sneha", "Neha", "Kavya", "Ananya", "Meera", "Divya", "Riya", "Shreya", "Pooja"]
LAST_NAMES = ["Sharma", "Patel", "Gupta", "Singh", "Kumar", "Verma", "Joshi", "Agarwal", "Mehta", "Reddy", "Nair", "Iyer", "Malhotra", "Bose", "Das"]

# Universities for Faculty
UNIVERSITIES = ["IIT Delhi", "IIT Bombay", "IIT Madras", "IISc Bangalore", "NIT Trichy", "NIT Warangal", "BITS Pilani", "VIT Vellore"]


async def init_database():
    """Initialize database connection"""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    await init_beanie(
        database=client[settings.MONGODB_DATABASE],
        document_models=[
            Faculty,
            StudentPerformance,
            StudentProfile,
            StudentProject,
            MeetingRequest,
            Elective,
            Subject,
            StudentInfo,
        ]
    )
    
    print(f"✅ Connected to MongoDB: {settings.MONGODB_DATABASE}")
    return client


def generate_name():
    """Generate a random Indian name"""
    if random.random() > 0.5:
        first_name = random.choice(FIRST_NAMES_MALE)
    else:
        first_name = random.choice(FIRST_NAMES_FEMALE)
    last_name = random.choice(LAST_NAMES)
    return first_name, last_name


async def create_electives():
    """Create elective courses from curriculum"""
    print("\n📚 Creating electives...")
    
    electives_created = 0
    
    # Create Program Electives
    for elective in PROGRAM_ELECTIVES:
        elec = Elective(
            code=elective["code"],
            name=elective["name"],
            description=f"Program elective course in {elective['domain']} for semester {elective['semester']}",
            category=ElectiveCategory.PROGRAM_ELECTIVE,
            credits=3,
            semester=elective["semester"],
            department="Computer Science",
            prerequisites=[],
            topics=[elective["domain"], "Advanced Concepts", "Practical Applications"],
            skills_covered=[elective["domain"], "Problem Solving", "Critical Thinking"],
            career_paths=[f"{elective['domain']} Engineer", f"{elective['domain']} Specialist", f"{elective['domain']} Consultant"],
            is_available=True,
            max_students=60,
            current_enrollment=random.randint(20, 55),
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            recommended_for=["CSE", "IT"],
        )
        await elec.insert()
        electives_created += 1
    
    # Create Open Electives
    for elective in OPEN_ELECTIVES:
        elec = Elective(
            code=elective["code"],
            name=elective["name"],
            description=f"Open elective course for holistic development",
            category=ElectiveCategory.OPEN_ELECTIVE,
            credits=elective["credits"],
            semester=6,  # Available from sem 6
            department="General",
            prerequisites=[],
            topics=["Professional Development", "Management", "Ethics"],
            skills_covered=["Leadership", "Communication", "Critical Thinking"],
            career_paths=["Management", "Entrepreneurship", "Consulting"],
            is_available=True,
            max_students=100,
            current_enrollment=random.randint(30, 80),
            difficulty_level=DifficultyLevel.BEGINNER,
            recommended_for=["All Branches"],
        )
        await elec.insert()
        electives_created += 1
    
    print(f"  ✅ Created {electives_created} electives")


async def create_faculty(count: int = 5) -> List[Faculty]:
    """Create sample faculty members"""
    print("\n👨‍🏫 Creating faculty members...")
    
    faculty_list = []
    designations = ["Professor", "Associate Professor", "Assistant Professor", "Assistant Professor", "Assistant Professor"]
    
    faculty_specializations = [
        {
            "name": "Dr. Rajesh Kumar",
            "research": ["Machine Learning", "Deep Learning", "Computer Vision"],
            "subjects": ["Machine Learning", "Artificial Intelligence", "Deep Learning"],
            "experience": 18
        },
        {
            "name": "Dr. Priya Sharma",
            "research": ["Data Science", "Big Data Analytics", "Data Mining"],
            "subjects": ["Data Structures", "Database Management", "Data Science"],
            "experience": 12
        },
        {
            "name": "Dr. Amit Verma",
            "research": ["Cybersecurity", "Cryptography", "Network Security"],
            "subjects": ["Cryptography & Network Security", "Operating Systems", "Computer Networks"],
            "experience": 15
        },
        {
            "name": "Dr. Sneha Patel",
            "research": ["Cloud Computing", "Distributed Systems", "IoT"],
            "subjects": ["Cloud Computing", "Operating Systems", "Software Engineering"],
            "experience": 10
        },
        {
            "name": "Dr. Vikram Singh",
            "research": ["Natural Language Processing", "Artificial Intelligence", "Neural Networks"],
            "subjects": ["Artificial Intelligence", "Theory of Computation", "Algorithms"],
            "experience": 14
        }
    ]
    
    for i, fac_data in enumerate(faculty_specializations[:count]):
        name = fac_data["name"]
        first_name = name.split()[1]
        last_name = name.split()[-1]
        department = "Computer Science & Engineering"
        designation = designations[i]
        experience = fac_data["experience"]
        
        # Create uniform profile
        uniform_profile = UniformFacultyProfile(
            personal_info=PersonalInfo(
                name=name,
                email=f"{first_name.lower()}.{last_name.lower()}@fcrit.ac.in",
                phone=f"+91 98765{random.randint(10000, 99999)}",
                photo_url=None
            ),
            academic_qualifications=AcademicQualifications(
                highest_degree="Ph.D.",
                specialization=fac_data["research"][0],
                university=random.choice(UNIVERSITIES),
                graduation_year=datetime.now().year - experience - 3,
                all_degrees=[
                    Degree(
                        degree="Ph.D.",
                        field=fac_data["research"][0],
                        institution=random.choice(UNIVERSITIES),
                        year=datetime.now().year - experience - 3
                    ),
                    Degree(
                        degree="M.Tech",
                        field="Computer Science",
                        institution=random.choice(UNIVERSITIES),
                        year=datetime.now().year - experience - 5
                    ),
                    Degree(
                        degree="B.Tech",
                        field="Computer Science",
                        institution=random.choice(UNIVERSITIES),
                        year=datetime.now().year - experience - 7
                    )
                ]
            ),
            current_position=CurrentPosition(
                designation=designation,
                department=department,
                institution="Fr. C. Rodrigues Institute of Technology",
                years_of_experience=experience,
                joining_year=datetime.now().year - experience
            ),
            research_expertise=ResearchExpertise(
                primary_areas=fac_data["research"],
                secondary_interests=random.sample(RESEARCH_AREAS, 2),
                keywords=random.sample(TECHNICAL_SKILLS, 6)
            ),
            teaching=TeachingInfo(
                current_subjects=fac_data["subjects"],
                past_subjects=random.sample([s["name"] for s in SEMESTER_SUBJECTS[3] + SEMESTER_SUBJECTS[4]], 3),
                preferred_areas=fac_data["research"][:2]
            ),
            availability=FacultyAvailability(
                office_location=f"Room {300 + i*10}, CSE Building",
                office_hours="Mon-Wed 10:00 AM - 12:00 PM",
                available_slots=[
                    MeetingSlot(
                        day="Monday",
                        start_time="10:00",
                        end_time="11:00",
                        venue=f"Room {300 + i*10}",
                        is_available=True
                    ),
                    MeetingSlot(
                        day="Wednesday",
                        start_time="14:00",
                        end_time="15:00",
                        venue=f"Room {300 + i*10}",
                        is_available=True
                    ),
                    MeetingSlot(
                        day="Friday",
                        start_time="11:00",
                        end_time="12:00",
                        venue=f"Room {300 + i*10}",
                        is_available=True
                    )
                ],
                preferred_meeting_duration=30
            ),
            publications=PublicationSummary(
                total_count=random.randint(15, 50),
                journal_papers=random.randint(8, 25),
                conference_papers=random.randint(7, 25),
                notable_works=[
                    f"A Novel Approach to {fac_data['research'][0]}",
                    f"Survey on {fac_data['research'][1]} Techniques"
                ],
                h_index=random.randint(5, 15),
                citations=random.randint(100, 500)
            ),
            others={
                "awards": random.sample([
                    "Best Paper Award - IEEE Conference 2023",
                    "Outstanding Faculty Award 2022",
                    "Research Excellence Award",
                    "Teaching Excellence Award"
                ], random.randint(1, 2)),
                "certifications": random.sample([
                    "AWS Certified Solutions Architect",
                    "Google Cloud Professional",
                    "NVIDIA Deep Learning",
                    "Microsoft Azure Certified"
                ], random.randint(1, 2)),
                "languages": ["English", "Hindi", "Marathi"],
                "professional_memberships": ["IEEE", "ACM", "CSI"]
            },
            profile_completeness=random.randint(90, 100),
            last_updated=datetime.utcnow()
        )
        
        faculty = Faculty(
            user_id=f"faculty_{i+1:03d}",
            name=name,
            email=uniform_profile.personal_info.email,
            department=department,
            designation=designation,
            phone=uniform_profile.personal_info.phone,
            office_location=uniform_profile.availability.office_location,
            years_of_experience=experience,
            teaching_subjects=fac_data["subjects"],
            specializations=fac_data["research"],
            skills=random.sample(TECHNICAL_SKILLS, 8),
            uniform_profile=uniform_profile,
            profile_setup_complete=True,
            status=FacultyStatus.ACTIVE,
            mentee_ids=[],
            max_mentees=15,
            available_slots=uniform_profile.availability.available_slots,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await faculty.insert()
        faculty_list.append(faculty)
        print(f"  ✅ {name} ({designation})")
    
    return faculty_list


async def create_students(faculty_list: List[Faculty], count_per_faculty: int = 4) -> List[StudentProfile]:
    """Create sample students"""
    print("\n👨‍🎓 Creating students...")
    
    students = []
    batch_years = [2021, 2022, 2023, 2024]
    
    for faculty in faculty_list:
        for i in range(count_per_faculty):
            first_name, last_name = generate_name()
            name = f"{first_name} {last_name}"
            
            # Determine semester based on batch
            batch = random.choice(batch_years)
            current_year = datetime.now().year
            years_in_college = current_year - batch
            semester = min(years_in_college * 2 + (1 if datetime.now().month > 6 else 0), 8)
            semester = max(semester, 3)  # Minimum semester 3
            
            # Generate CGPA and determine risk level
            cgpa = round(random.uniform(5.5, 9.8), 2)
            if cgpa >= 8.0:
                risk_level = "low"
                improvement_trend = random.choice(["improving", "stable"])
            elif cgpa >= 6.5:
                risk_level = "medium"
                improvement_trend = random.choice(["stable", "improving", "stable"])
            else:
                risk_level = "high"
                improvement_trend = random.choice(["stable", "declining", "improving"])
            
            # Generate semester records
            semester_records = []
            sgpa_values = []
            
            for sem in range(1, semester + 1):
                subjects_for_sem = SEMESTER_SUBJECTS.get(sem, [])
                subject_scores = []
                
                for subj in subjects_for_sem:
                    # Generate marks based on CGPA (with some variation)
                    base_marks = int(cgpa * 10 + random.uniform(-15, 15))
                    marks = max(35, min(100, base_marks))
                    
                    # Determine grade
                    if marks >= 75:
                        grade = random.choice(["O", "A+", "A"])
                    elif marks >= 60:
                        grade = random.choice(["A", "B+", "B"])
                    elif marks >= 50:
                        grade = random.choice(["B", "C+", "C"])
                    elif marks >= 40:
                        grade = random.choice(["C", "D"])
                    else:
                        grade = "F"
                    
                    grade_points_map = {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C+": 5, "C": 4, "D": 3, "F": 0}
                    
                    subject_scores.append(SubjectScore(
                        subject_code=subj["code"],
                        subject_name=subj["name"],
                        credits=subj["credits"],
                        internal_marks=marks * 0.3,
                        external_marks=marks * 0.7,
                        total_marks=marks,
                        grade=grade,
                        grade_points=grade_points_map.get(grade, 0),
                        is_elective=subj["type"] in ["PEC", "OEC"],
                        is_practical=subj["type"] in ["LBC", "SBL"]
                    ))
                
                # Calculate SGPA
                total_credits = sum(s.credits for s in subject_scores)
                total_grade_points = sum(s.grade_points * s.credits for s in subject_scores)
                sgpa = round(total_grade_points / total_credits, 2) if total_credits > 0 else 0
                sgpa_values.append(sgpa)
                
                semester_records.append(SemesterRecord(
                    semester_number=sem,
                    sgpa=sgpa,
                    total_credits=total_credits,
                    credits_earned=total_credits,
                    subjects=subject_scores,
                    academic_year=f"{batch + (sem-1)//2}-{batch + (sem-1)//2 + 1}",
                    is_complete=True,
                    created_at=datetime(batch + (sem-1)//2, 6 if sem % 2 == 0 else 12, 15)
                ))
            
            roll_number = f"{batch}{faculty.department[:2].upper()}{random.randint(100, 999)}"
            
            # Create StudentProfile
            student = StudentProfile(
                user_id=f"student_{roll_number}",
                name=name,
                email=f"{first_name.lower()}.{last_name.lower()}{random.randint(1,99)}@student.fcrit.ac.in",
                roll_number=roll_number,
                branch="IT" if "IT" in faculty.department else "COMP",
                current_semester=semester,
                admission_year=batch,
                current_academic_year=f"{datetime.now().year}-{datetime.now().year + 1}",
                cgpa=cgpa,
                total_credits_earned=sum(sr.credits_earned for sr in semester_records),
                total_credits_required=160,
                semester_records=semester_records,
                skills=random.sample(TECHNICAL_SKILLS, random.randint(4, 8)),
                interests=random.sample(RESEARCH_AREAS[:10], random.randint(2, 4)),
                career_goals=random.sample([
                    "Software Engineer", "Data Scientist", "ML Engineer",
                    "Cloud Architect", "Full Stack Developer", "DevOps Engineer"
                ], random.randint(2, 3)),
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            
            await student.insert()
            
            # Create StudentInfo document
            student_info = StudentInfo(
                uid=student.user_id,
                year=f"Year {(semester + 1) // 2}",
                semester=f"Semester {semester}",
                branch=faculty.department,
                roll_number=roll_number
            )
            await student_info.insert()
            
            # Create Subject documents
            subjects_list = []
            for sem_record in semester_records:
                for subj_score in sem_record.subjects:
                    subject_obj = Subject(
                        code=subj_score.subject_code,
                        name=subj_score.subject_name,
                        score=subj_score.total_marks,
                        credits=subj_score.credits,
                        trend=random.choice(["up", "stable", "down"]),
                        weaknesses=[],
                        semester=sem_record.semester_number,
                        grade=subj_score.grade,
                        grade_points=subj_score.grade_points
                    )
                    await subject_obj.insert()
                    subjects_list.append(subject_obj)
            
            # Identify weak and strong subjects
            latest_semester = semester_records[-1] if semester_records else None
            weak_subjects = []
            strong_subjects = []
            
            if latest_semester:
                for subj in latest_semester.subjects:
                    if subj.grade_points >= 8:
                        strong_subjects.append(subj.subject_name)
                    elif subj.grade_points < 6:
                        weak_subjects.append(subj.subject_name)
            
            # Create corresponding StudentPerformance
            performance = StudentPerformance(
                student_info=student_info,
                subjects=subjects_list,
                overall_cgpa=cgpa,
                semester_sgpa=sgpa_values[-1] if sgpa_values else cgpa,
                strong_subjects=strong_subjects,
                weak_subjects=weak_subjects,
                completed_credits=sum(sr.credits_earned for sr in semester_records),
                total_credits=160,
                interests=student.interests,
                career_goals=student.career_goals,
                skills_matrix={
                    "programming": random.randint(60, 95),
                    "algorithms": random.randint(55, 90),
                    "databases": random.randint(60, 85),
                    "web_development": random.randint(50, 90)
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            await performance.insert()
            
            # Add to faculty's mentee list
            faculty.mentee_ids.append(student.user_id)
            
            students.append(student)
        
        # Save faculty with updated mentee list
        await faculty.save()
        print(f"  ✅ Created {count_per_faculty} students for {faculty.name}")
    
    return students


# Replace the create_projects function in scripts/seed_faculty_data.py

async def create_projects(students: List[StudentProfile]):
    """Create sample projects for students"""
    print("\n📁 Creating student projects...")
    
    project_ideas = [
        {
            "title": "AI-Powered Plagiarism Detector",
            "tech": ["Python", "TensorFlow", "NLP", "Flask"],
            "type": ProjectType.RESEARCH,
            "domain": "AI/ML"
        },
        {
            "title": "Smart Traffic Management System",
            "tech": ["Python", "OpenCV", "IoT", "React"],
            "type": ProjectType.ACADEMIC,
            "domain": "IoT"
        },
        {
            "title": "Blockchain-based Voting System",
            "tech": ["Solidity", "Web3.js", "React", "Node.js"],
            "type": ProjectType.HACKATHON,
            "domain": "Blockchain"
        },
        {
            "title": "Health Monitoring Wearable App",
            "tech": ["Flutter", "Firebase", "TensorFlow Lite"],
            "type": ProjectType.PERSONAL,
            "domain": "Mobile"
        },
        {
            "title": "E-Commerce Recommendation Engine",
            "tech": ["Python", "Scikit-learn", "Django", "PostgreSQL"],
            "type": ProjectType.INTERNSHIP,
            "domain": "Data Science"
        },
        {
            "title": "Real-time Chat Application",
            "tech": ["Node.js", "Socket.io", "React", "MongoDB"],
            "type": ProjectType.ACADEMIC,
            "domain": "Web Dev"
        },
        {
            "title": "Image Classification using CNN",
            "tech": ["Python", "TensorFlow", "Keras", "OpenCV"],
            "type": ProjectType.COMPETITION,
            "domain": "AI/ML"
        },
        {
            "title": "Student Performance Predictor",
            "tech": ["Python", "Scikit-learn", "Flask", "React"],
            "type": ProjectType.RESEARCH,
            "domain": "Data Science"
        },
        {
            "title": "Open Source CLI Tool",
            "tech": ["Python", "Click", "Rich", "GitHub Actions"],
            "type": ProjectType.OPEN_SOURCE,
            "domain": "DevOps"
        },
        {
            "title": "Portfolio Website for Client",
            "tech": ["React", "Next.js", "Tailwind CSS", "Vercel"],
            "type": ProjectType.FREELANCE,
            "domain": "Web Dev"
        },
        {
            "title": "Smart India Hackathon Project",
            "tech": ["Python", "Django", "PostgreSQL", "Docker"],
            "type": ProjectType.HACKATHON,
            "domain": "Full Stack"
        },
        {
            "title": "Company Internship Project",
            "tech": ["Java", "Spring Boot", "MySQL", "AWS"],
            "type": ProjectType.INTERNSHIP,
            "domain": "Backend"
        }
    ]
    
    projects_created = 0
    
    for student in students:
        num_projects = random.randint(1, 3)
        selected_projects = random.sample(project_ideas, min(num_projects, len(project_ideas)))
        
        for proj_data in selected_projects:
            project = StudentProject(
                student_id=student.user_id,
                title=proj_data["title"],
                description=f"A {proj_data['domain']} project implementing {', '.join(proj_data['tech'][:2])}.",
                project_type=proj_data["type"],
                technologies=proj_data["tech"],
                github_url=f"https://github.com/{student.name.lower().replace(' ', '')}/{proj_data['title'].lower().replace(' ', '-')}",
                status=random.choice(["completed", "in_progress", "completed"]),
                start_date=datetime.utcnow() - timedelta(days=random.randint(60, 300)),
                created_at=datetime.utcnow()
            )
            
            await project.insert()
            projects_created += 1
    
    print(f"  ✅ Created {projects_created} projects for {len(students)} students")
    
async def create_meeting_requests(faculty_list: List[Faculty], students: List[StudentProfile]):
    """Create sample meeting requests"""
    print("\n📅 Creating meeting requests...")
    
    subjects = [
        "Guidance on Final Year Project",
        "Career counseling discussion",
        "Help with research paper",
        "Clarification on ML concepts",
        "Internship recommendation letter",
        "Project guidance for Data Science",
        "Query about Cloud Computing elective",
        "Academic performance review"
    ]
    
    requests_created = 0
    
    for faculty in faculty_list:
        faculty_students = [s for s in students if s.user_id in faculty.mentee_ids]
        
        # Create pending requests
        for i in range(random.randint(2, 4)):
            if not faculty_students:
                continue
            
            student = random.choice(faculty_students)
            
            request = MeetingRequest(
                request_id=f"req_pending_{faculty.user_id}_{i}_{random.randint(1000, 9999)}",
                student_id=student.user_id,
                student_name=student.name,
                student_email=student.email,
                student_department=student.branch,
                student_semester=student.current_semester,
                faculty_id=faculty.user_id,
                faculty_name=faculty.name,
                subject=random.choice(subjects),
                message=f"Dear Professor, I would like to discuss {random.choice(subjects).lower()}. Please let me know your available slots. Thank you.",
                urgency=random.choice(["low", "normal", "normal", "high"]),
                status=MeetingRequestStatus.PENDING,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 5), hours=random.randint(0, 23))
            )
            
            await request.insert()
            requests_created += 1
        
        # Create accepted requests with scheduled meetings
        for i in range(random.randint(1, 2)):
            if not faculty_students:
                continue
            
            student = random.choice(faculty_students)
            meeting_date = datetime.utcnow() + timedelta(days=random.randint(1, 7))
            
            request = MeetingRequest(
                request_id=f"req_accepted_{faculty.user_id}_{i}_{random.randint(1000, 9999)}",
                student_id=student.user_id,
                student_name=student.name,
                student_email=student.email,
                student_department=student.branch,
                student_semester=student.current_semester,
                faculty_id=faculty.user_id,
                faculty_name=faculty.name,
                subject=random.choice(subjects),
                message="I need your guidance regarding my academic progress and project work.",
                urgency="normal",
                status=MeetingRequestStatus.ACCEPTED,
                scheduled_meeting=ScheduledMeeting(
                    date=meeting_date.isoformat(),
                    start_time=random.choice(["10:00", "11:00", "14:00", "15:00"]),
                    end_time=random.choice(["10:30", "11:30", "14:30", "15:30"]),
                    venue=faculty.office_location or "Faculty Office"
                ),
                faculty_response="Looking forward to our meeting. Please bring your project documents.",
                created_at=datetime.utcnow() - timedelta(days=random.randint(3, 10)),
                updated_at=datetime.utcnow() - timedelta(days=random.randint(1, 3))
            )
            
            await request.insert()
            requests_created += 1
    
    print(f"  ✅ Created {requests_created} meeting requests")


async def main():
    """Main seed function"""
    print("\n" + "="*60)
    print("🌱 FCRIT Academic Advisor - Database Seeding")
    print("="*60)
    
    try:
        # Initialize database
        client = await init_database()
        
        # Clear existing data
        print("\n🗑️  Clearing existing data...")
        await Faculty.delete_all()
        await StudentProfile.delete_all()
        await StudentPerformance.delete_all()
        await StudentProject.delete_all()
        await MeetingRequest.delete_all()
        await Elective.delete_all()
        await Subject.delete_all()
        await StudentInfo.delete_all()
        print("  ✅ Cleared all collections")
        
        # Create data
        await create_electives()
        faculty_list = await create_faculty(count=5)
        students = await create_students(faculty_list, count_per_faculty=4)
        await create_projects(students)
        await create_meeting_requests(faculty_list, students)
        
        # Summary
        print("\n" + "="*60)
        print("✅ DATABASE SEEDING COMPLETED!")
        print("="*60)
        
        print(f"\n📊 Summary:")
        print(f"  - Faculty members: {len(faculty_list)}")
        print(f"  - Students: {len(students)}")
        print(f"  - Electives: {len(PROGRAM_ELECTIVES) + len(OPEN_ELECTIVES)}")
        print(f"  - Average students per faculty: {len(students) // len(faculty_list)}")
        
        print("\n📋 Faculty Login IDs:")
        for faculty in faculty_list:
            print(f"  - {faculty.name}: {faculty.user_id} ({faculty.email})")
        
        print("\n📋 Sample Student Login IDs:")
        for student in students[:5]:
            print(f"  - {student.name}: {student.user_id} (CGPA: {student.cgpa})")
        
        print("\n🎓 Departments: CSE, IT")
        print("📚 Curriculum: FCRIT B.Tech R2024.1 / R25")
        
        client.close()
        print("\n✅ Done!")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())