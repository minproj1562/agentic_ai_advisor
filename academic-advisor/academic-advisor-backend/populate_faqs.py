# populate_faqs.py
"""
Frequently Asked Questions and College Information
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os


async def populate_faqs():
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client["fcrit_chatbot"]
    
    print("🔄 Populating FAQs and college information...")
    
    # Clear existing
    await db.faqs.delete_many({})
    await db.college_info.delete_many({})
    
    # FAQs
    faqs = [
        # Admission Related
        {
            "category": "Admission",
            "question": "What is the admission process for FCRIT?",
            "answer": "Admission to FCRIT is through the Centralized Admission Process (CAP) conducted by DTE Maharashtra. Students need to appear for MHT-CET or JEE Main and participate in CAP rounds. For details, visit the DTE Maharashtra website.",
            "keywords": ["admission", "cap", "process", "dte", "mht-cet", "jee"]
        },
        {
            "category": "Admission",
            "question": "What are the eligibility criteria for B.Tech/B.E. admission?",
            "answer": "Eligibility: 1) Passed HSC or equivalent with Physics, Chemistry, and Mathematics. 2) Minimum 50% marks (45% for reserved categories). 3) Valid MHT-CET or JEE Main score. 4) Domicile of Maharashtra (for state quota seats).",
            "keywords": ["eligibility", "criteria", "hsc", "marks", "percentage"]
        },
        {
            "category": "Admission",
            "question": "What are the documents required for admission?",
            "answer": "Required documents: 1) 10th Mark Sheet and Passing Certificate, 2) 12th Mark Sheet and Passing Certificate, 3) MHT-CET/JEE Score Card, 4) Domicile Certificate, 5) Caste Certificate (if applicable), 6) Income Certificate (for EWS/scholarship), 7) Passport size photographs, 8) Aadhar Card, 9) Gap Certificate (if applicable).",
            "keywords": ["documents", "required", "certificates", "admission"]
        },
        
        # Fee Related
        {
            "category": "Fees",
            "question": "What is the fee structure for B.Tech CSE?",
            "answer": "The approximate annual fee for B.Tech CSE is around ₹1,50,000 to ₹1,80,000 (subject to change as per DTE norms). This includes tuition fee, development fee, and other charges. Scholarships are available for eligible students.",
            "keywords": ["fee", "structure", "cost", "tuition", "annual"]
        },
        {
            "category": "Fees",
            "question": "What scholarships are available?",
            "answer": "Available scholarships: 1) Government of India Post-Matric Scholarship, 2) State Government Freeship/Scholarship for SC/ST/OBC, 3) EBC Freeship, 4) Minority Scholarship, 5) Merit-based institutional scholarships. Apply through MahaDBT portal.",
            "keywords": ["scholarship", "freeship", "financial", "aid", "mahadbt"]
        },
        
        # Examination Related
        {
            "category": "Examination",
            "question": "How is the grading system in Mumbai University?",
            "answer": "Mumbai University follows a 10-point CGPA system. Grades: O (Outstanding) - 10 points, A+ - 9, A - 8, B+ - 7, B - 6, C - 5, P (Pass) - 4, F (Fail) - 0. CGPA is calculated as weighted average of grade points.",
            "keywords": ["grading", "cgpa", "marks", "grade", "points"]
        },
        {
            "category": "Examination",
            "question": "What is the passing criteria?",
            "answer": "Passing criteria: 1) Minimum 40% in each theory subject, 2) Minimum 40% in each practical/oral exam, 3) Minimum 40% aggregate in semester, 4) 75% attendance mandatory for exam eligibility. ATKT rules apply as per university norms.",
            "keywords": ["passing", "criteria", "marks", "atkt", "minimum"]
        },
        {
            "category": "Examination",
            "question": "What is the ATKT rule?",
            "answer": "ATKT (Allowed To Keep Terms) rules: FE to SE - No ATKT allowed (must clear all subjects). SE to TE - Maximum 4 backlog subjects allowed. TE to BE - Maximum 8 backlog subjects allowed (including SE backlogs). Check latest university circulars for updates.",
            "keywords": ["atkt", "backlog", "promotion", "kt", "rules"]
        },
        
        # Academic Related
        {
            "category": "Academic",
            "question": "What is the credit system?",
            "answer": "Each subject has assigned credits based on teaching hours. Theory: 3-4 credits, Lab: 1-2 credits, Projects: 1-4 credits. Total program credits: approximately 160-170. CGPA is calculated using credit-weighted formula.",
            "keywords": ["credit", "system", "hours", "weightage"]
        },
        {
            "category": "Academic",
            "question": "How many electives can I choose?",
            "answer": "In CSE program: 5 Program Elective Courses (PEC) from Sem 5-8, 2 Open Elective Courses (OEC) in Sem 7-8, 1 Liberal Learning Course (LLC) in Sem 6, 4 Multidisciplinary Minor Courses (MDM) from Sem 3-6.",
            "keywords": ["elective", "choice", "optional", "subjects"]
        },
        {
            "category": "Academic",
            "question": "What are the mini project and major project requirements?",
            "answer": "Mini Projects: 4 across Sem 3-6 (Mini Project 1A, 1B, 2A, 2B). Major Project: 2 parts in Sem 7-8 (Major Project A and B). Projects are done in groups of 3-4 students under faculty guidance. Final presentation and documentation required.",
            "keywords": ["project", "mini", "major", "final", "year"]
        },
        
        # Placement Related
        {
            "category": "Placement",
            "question": "What is the placement record of FCRIT CSE?",
            "answer": "CSE department has excellent placement records with top recruiters like TCS, Infosys, Wipro, Cognizant, Capgemini, L&T Infotech, Accenture, and many product companies. Average package: 4-6 LPA. Highest packages reach 15+ LPA for select students.",
            "keywords": ["placement", "package", "salary", "companies", "recruiters"]
        },
        {
            "category": "Placement",
            "question": "What is the eligibility for campus placements?",
            "answer": "Eligibility criteria: 1) No active backlogs at the time of placement, 2) Minimum 60% aggregate (varies by company), 3) Good communication skills, 4) Registered with T&P Cell. Some companies may have additional criteria.",
            "keywords": ["placement", "eligibility", "criteria", "campus"]
        },
        
        # Infrastructure Related
        {
            "category": "Infrastructure",
            "question": "What are the lab facilities in CSE department?",
            "answer": "CSE labs: Programming Lab, Data Structures Lab, Database Lab, Network Lab, Cloud Computing Lab, AI/ML Lab, Project Lab. All labs have latest hardware with high-speed internet, licensed software, and adequate systems for each student.",
            "keywords": ["lab", "facilities", "computer", "infrastructure"]
        },
        {
            "category": "Infrastructure",
            "question": "Does the college have a library?",
            "answer": "Yes, FCRIT has a central library with: 50,000+ books, Digital library with IEEE, ACM, Springer access, E-journals and e-books, Previous year question papers, Separate reading rooms, Open 8 AM to 8 PM on working days.",
            "keywords": ["library", "books", "digital", "resources"]
        },
        {
            "category": "Infrastructure",
            "question": "Is hostel facility available?",
            "answer": "Yes, separate hostels for boys and girls are available on campus with: Single/double/triple occupancy rooms, Mess facility with vegetarian and non-vegetarian options, Wi-Fi connectivity, 24x7 security, Recreational facilities.",
            "keywords": ["hostel", "accommodation", "mess", "rooms"]
        },
        
        # General
        {
            "category": "General",
            "question": "What are the college timings?",
            "answer": "Regular college hours: 9:00 AM to 5:00 PM. Library: 8:00 AM to 8:00 PM. Labs: 9:00 AM to 6:00 PM (extended hours during practicals). Office: 10:00 AM to 5:00 PM. Saturday: Half day (alternate).",
            "keywords": ["timing", "hours", "schedule", "working"]
        },
        {
            "category": "General",
            "question": "How to reach FCRIT?",
            "answer": "FCRIT is located in Vashi, Navi Mumbai. Nearest railway station: Vashi (1 km). Bus routes available from Vashi station. Auto/cab services available. Address: Sector 9A, Vashi, Navi Mumbai - 400703.",
            "keywords": ["location", "address", "reach", "transport", "vashi"]
        },
        {
            "category": "General",
            "question": "What are the contact details?",
            "answer": "Phone: +91-22-27771000, Email: info@fcrit.ac.in, Website: www.fcrit.ac.in, Admission Enquiry: admission@fcrit.ac.in, Training & Placement: tnp@fcrit.ac.in.",
            "keywords": ["contact", "phone", "email", "website"]
        },
    ]
    
    # College Information
    college_info = {
        "name": "Fr. Conceicao Rodrigues Institute of Technology",
        "short_name": "FCRIT",
        "established": 1984,
        "type": "Private Aided Engineering College",
        "affiliation": "University of Mumbai",
        "approval": ["AICTE", "DTE Maharashtra"],
        "accreditation": ["NBA (Selected Programs)", "NAAC"],
        "address": {
            "street": "Sector 9A, Vashi",
            "city": "Navi Mumbai",
            "state": "Maharashtra",
            "pincode": "400703",
            "country": "India"
        },
        "contact": {
            "phone": ["+91-22-27771000", "+91-22-27661780"],
            "fax": "+91-22-27662533",
            "email": "info@fcrit.ac.in",
            "website": "www.fcrit.ac.in"
        },
        "departments": [
            {"name": "Computer Science & Engineering", "code": "CSE", "intake": 120},
            {"name": "Information Technology", "code": "IT", "intake": 60},
            {"name": "Electronics & Telecommunication Engineering", "code": "EXTC", "intake": 60},
            {"name": "Mechanical Engineering", "code": "MECH", "intake": 60},
            {"name": "Civil Engineering", "code": "CIVIL", "intake": 60},
            {"name": "Electrical Engineering", "code": "ELEC", "intake": 60}
        ],
        "facilities": [
            "Central Library with Digital Resources",
            "Well-equipped Laboratories",
            "Computer Center with High-Speed Internet",
            "Seminar Halls and Auditorium",
            "Sports Ground and Indoor Games",
            "Cafeteria",
            "Boys and Girls Hostel",
            "Medical Facility",
            "Transportation",
            "Wi-Fi Campus"
        ],
        "leadership": {
            "principal": "Dr. [Principal Name]",
            "hod_cse": "Dr. Rajendra Sahu",
            "registrar": "[Registrar Name]"
        },
        "timings": {
            "college": "9:00 AM - 5:00 PM",
            "library": "8:00 AM - 8:00 PM",
            "office": "10:00 AM - 5:00 PM"
        }
    }
    
    # Insert data
    await db.faqs.insert_many(faqs)
    await db.college_info.insert_one(college_info)
    
    print(f"✅ Inserted {len(faqs)} FAQs")
    print(f"✅ Inserted college information")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(populate_faqs())