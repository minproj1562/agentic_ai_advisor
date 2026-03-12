# populate_all_faculty.py
"""
Complete faculty data for FCRIT Computer Science Engineering Program
Covers ALL subjects across 8 semesters including electives
Email format: firstname.lastname@fcrit.ac.in
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime


async def populate_complete_faculty():
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client["fcrit_chatbot"]
    
    print("🔄 Populating COMPLETE faculty list for FCRIT...")
    
    # Clear existing
    await db.faculty.delete_many({})
    
    faculty_data = [
        # ==================== MATHEMATICS DEPARTMENT (6 Faculty) ====================
        {
            "name": "Dr. Ramesh Krishnan",
            "designation": "Professor & HOD",
            "department": "Mathematics",
            "email": "ramesh.krishnan@fcrit.ac.in",
            "phone": "+91-22-27771000",
            "cabin": "MATH-101",
            "subjects": ["Engineering Mathematics I", "Engineering Mathematics-II"],
            "expertise": ["Calculus", "Linear Algebra", "Differential Equations", "Vector Calculus"],
            "qualification": "Ph.D. Mathematics (IIT Bombay)",
            "experience": 25,
            "office_hours": "Monday-Friday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Sunita Deshmukh",
            "designation": "Professor",
            "department": "Mathematics",
            "email": "sunita.deshmukh@fcrit.ac.in",
            "phone": "+91-22-27771001",
            "cabin": "MATH-102",
            "subjects": ["Engineering Mathematics-III", "Engineering Mathematics-IV"],
            "expertise": ["Probability", "Statistics", "Numerical Methods", "Complex Analysis"],
            "qualification": "Ph.D. Applied Mathematics (University of Mumbai)",
            "experience": 22,
            "office_hours": "Monday-Friday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Prakash Nair",
            "designation": "Associate Professor",
            "department": "Mathematics",
            "email": "prakash.nair@fcrit.ac.in",
            "phone": "+91-22-27771002",
            "cabin": "MATH-103",
            "subjects": ["Engineering Mathematics-II", "Discrete Structure & Graph Theory"],
            "expertise": ["Discrete Mathematics", "Graph Theory", "Combinatorics"],
            "qualification": "Ph.D. Mathematics",
            "experience": 15,
            "office_hours": "Tuesday-Thursday: 11:00 AM - 1:00 PM"
        },
        {
            "name": "Dr. Kavita Sharma",
            "designation": "Associate Professor",
            "department": "Mathematics",
            "email": "kavita.sharma@fcrit.ac.in",
            "phone": "+91-22-27771003",
            "cabin": "MATH-104",
            "subjects": ["Engineering Mathematics-III", "Engineering Mathematics-IV"],
            "expertise": ["Transform Theory", "Laplace Transform", "Fourier Series"],
            "qualification": "Ph.D. Mathematics",
            "experience": 14,
            "office_hours": "Monday-Wednesday: 3:00 PM - 5:00 PM"
        },
        {
            "name": "Dr. Ashwin Kulkarni",
            "designation": "Assistant Professor",
            "department": "Mathematics",
            "email": "ashwin.kulkarni@fcrit.ac.in",
            "phone": "+91-22-27771004",
            "cabin": "MATH-105",
            "subjects": ["Engineering Mathematics I", "Discrete Structure & Graph Theory", "Operation Research"],
            "expertise": ["Optimization", "Linear Programming", "Number Theory"],
            "qualification": "Ph.D. Operations Research",
            "experience": 8,
            "office_hours": "Wednesday-Friday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Meghana Patil",
            "designation": "Assistant Professor",
            "department": "Mathematics",
            "email": "meghana.patil@fcrit.ac.in",
            "phone": "+91-22-27771005",
            "cabin": "MATH-106",
            "subjects": ["Engineering Mathematics I", "Engineering Mathematics-II"],
            "expertise": ["Applied Mathematics", "Mathematical Modeling"],
            "qualification": "Ph.D. Mathematics",
            "experience": 6,
            "office_hours": "Tuesday-Thursday: 2:00 PM - 4:00 PM"
        },
        
        # ==================== PHYSICS DEPARTMENT (4 Faculty) ====================
        {
            "name": "Dr. Vijay Bhosale",
            "designation": "Professor & HOD",
            "department": "Physics",
            "email": "vijay.bhosale@fcrit.ac.in",
            "phone": "+91-22-27771010",
            "cabin": "PHY-101",
            "subjects": ["Engineering Physics-I", "Engineering Physics-II"],
            "expertise": ["Quantum Physics", "Solid State Physics", "Optics"],
            "qualification": "Ph.D. Physics (TIFR Mumbai)",
            "experience": 24,
            "office_hours": "Monday-Friday: 11:00 AM - 1:00 PM"
        },
        {
            "name": "Dr. Snehal Joshi",
            "designation": "Associate Professor",
            "department": "Physics",
            "email": "snehal.joshi@fcrit.ac.in",
            "phone": "+91-22-27771011",
            "cabin": "PHY-102",
            "subjects": ["Engineering Physics-I", "Engineering Physics-I Laboratory"],
            "expertise": ["Electromagnetic Theory", "Laser Physics"],
            "qualification": "Ph.D. Physics",
            "experience": 16,
            "office_hours": "Tuesday-Thursday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Rahul Sawant",
            "designation": "Assistant Professor",
            "department": "Physics",
            "email": "rahul.sawant@fcrit.ac.in",
            "phone": "+91-22-27771012",
            "cabin": "PHY-103",
            "subjects": ["Engineering Physics-II", "Engineering Physics-II Laboratory"],
            "expertise": ["Modern Physics", "Semiconductor Physics"],
            "qualification": "Ph.D. Physics",
            "experience": 9,
            "office_hours": "Monday-Wednesday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Prachi Deshpande",
            "designation": "Assistant Professor",
            "department": "Physics",
            "email": "prachi.deshpande@fcrit.ac.in",
            "phone": "+91-22-27771013",
            "cabin": "PHY-104",
            "subjects": ["Engineering Physics-I Laboratory", "Engineering Physics-II Laboratory"],
            "expertise": ["Experimental Physics", "Nanotechnology", "Material Science"],
            "qualification": "Ph.D. Physics",
            "experience": 7,
            "office_hours": "Wednesday-Friday: 11:00 AM - 1:00 PM"
        },
        
        # ==================== CHEMISTRY DEPARTMENT (4 Faculty) ====================
        {
            "name": "Dr. Anand Kadam",
            "designation": "Professor & HOD",
            "department": "Chemistry",
            "email": "anand.kadam@fcrit.ac.in",
            "phone": "+91-22-27771020",
            "cabin": "CHEM-101",
            "subjects": ["Engineering Chemistry-I", "Engineering Chemistry-II"],
            "expertise": ["Organic Chemistry", "Polymer Chemistry", "Green Chemistry"],
            "qualification": "Ph.D. Chemistry (ICT Mumbai)",
            "experience": 23,
            "office_hours": "Monday-Friday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Swati Gokhale",
            "designation": "Associate Professor",
            "department": "Chemistry",
            "email": "swati.gokhale@fcrit.ac.in",
            "phone": "+91-22-27771021",
            "cabin": "CHEM-102",
            "subjects": ["Engineering Chemistry-I", "Engineering Chemistry-I Laboratory"],
            "expertise": ["Physical Chemistry", "Electrochemistry"],
            "qualification": "Ph.D. Chemistry",
            "experience": 15,
            "office_hours": "Tuesday-Thursday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Nilesh Pawar",
            "designation": "Assistant Professor",
            "department": "Chemistry",
            "email": "nilesh.pawar@fcrit.ac.in",
            "phone": "+91-22-27771022",
            "cabin": "CHEM-103",
            "subjects": ["Engineering Chemistry-II", "Engineering Chemistry-II Laboratory"],
            "expertise": ["Environmental Chemistry", "Corrosion Science"],
            "qualification": "Ph.D. Chemistry",
            "experience": 10,
            "office_hours": "Monday-Wednesday: 3:00 PM - 5:00 PM"
        },
        {
            "name": "Dr. Rashmi Karpe",
            "designation": "Assistant Professor",
            "department": "Chemistry",
            "email": "rashmi.karpe@fcrit.ac.in",
            "phone": "+91-22-27771023",
            "cabin": "CHEM-104",
            "subjects": ["Engineering Chemistry-I Laboratory", "Engineering Chemistry-II Laboratory"],
            "expertise": ["Analytical Chemistry", "Spectroscopy", "Instrumental Analysis"],
            "qualification": "Ph.D. Chemistry",
            "experience": 8,
            "office_hours": "Wednesday-Friday: 10:00 AM - 12:00 PM"
        },
        
        # ==================== MECHANICAL ENGINEERING DEPARTMENT (4 Faculty) ====================
        {
            "name": "Dr. Suresh Kamble",
            "designation": "Professor",
            "department": "Mechanical Engineering",
            "email": "suresh.kamble@fcrit.ac.in",
            "phone": "+91-22-27771030",
            "cabin": "MECH-101",
            "subjects": ["Engineering Mechanics", "Engineering Mechanics Laboratory"],
            "expertise": ["Solid Mechanics", "Dynamics", "Statics"],
            "qualification": "Ph.D. Mechanical Engineering (IIT Kharagpur)",
            "experience": 24,
            "office_hours": "Monday-Friday: 11:00 AM - 1:00 PM"
        },
        {
            "name": "Dr. Ganesh Jadhav",
            "designation": "Associate Professor",
            "department": "Mechanical Engineering",
            "email": "ganesh.jadhav@fcrit.ac.in",
            "phone": "+91-22-27771031",
            "cabin": "MECH-102",
            "subjects": ["Engineering Graphics Laboratory", "Basic Workshop Practice-I", "Basic Workshop Practice-II"],
            "expertise": ["CAD/CAM", "Manufacturing Processes", "Workshop Technology"],
            "qualification": "Ph.D. Mechanical Engineering",
            "experience": 17,
            "office_hours": "Tuesday-Thursday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Santosh More",
            "designation": "Assistant Professor",
            "department": "Mechanical Engineering",
            "email": "santosh.more@fcrit.ac.in",
            "phone": "+91-22-27771032",
            "cabin": "MECH-103",
            "subjects": ["Engineering Mechanics Laboratory", "Product Design", "Product Lifecycle Management"],
            "expertise": ["Product Development", "Industrial Design", "PLM"],
            "qualification": "Ph.D. Design Engineering",
            "experience": 9,
            "office_hours": "Monday-Wednesday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Vaibhav Shinde",
            "designation": "Assistant Professor",
            "department": "Mechanical Engineering",
            "email": "vaibhav.shinde@fcrit.ac.in",
            "phone": "+91-22-27771033",
            "cabin": "MECH-104",
            "subjects": ["Basic Workshop Practice-I", "Basic Workshop Practice-II", "Reliability Engineering"],
            "expertise": ["Reliability Analysis", "Quality Engineering"],
            "qualification": "Ph.D. Industrial Engineering",
            "experience": 7,
            "office_hours": "Wednesday-Friday: 11:00 AM - 1:00 PM"
        },
        
        # ==================== ELECTRICAL ENGINEERING DEPARTMENT (3 Faculty) ====================
        {
            "name": "Dr. Mahesh Gaikwad",
            "designation": "Professor",
            "department": "Electrical Engineering",
            "email": "mahesh.gaikwad@fcrit.ac.in",
            "phone": "+91-22-27771040",
            "cabin": "ELEC-101",
            "subjects": ["Basic Electrical Engineering", "Basic Electrical Engineering Laboratory"],
            "expertise": ["Power Systems", "Electrical Machines", "Power Electronics"],
            "qualification": "Ph.D. Electrical Engineering (IIT Delhi)",
            "experience": 23,
            "office_hours": "Monday-Friday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Rekha Patankar",
            "designation": "Associate Professor",
            "department": "Electrical Engineering",
            "email": "rekha.patankar@fcrit.ac.in",
            "phone": "+91-22-27771041",
            "cabin": "ELEC-102",
            "subjects": ["Basic Electrical Engineering", "Energy Audit and Management"],
            "expertise": ["Energy Management", "Renewable Energy", "Smart Grids"],
            "qualification": "Ph.D. Electrical Engineering",
            "experience": 16,
            "office_hours": "Tuesday-Thursday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Amol Dhage",
            "designation": "Assistant Professor",
            "department": "Electrical Engineering",
            "email": "amol.dhage@fcrit.ac.in",
            "phone": "+91-22-27771042",
            "cabin": "ELEC-103",
            "subjects": ["Basic Electrical Engineering Laboratory"],
            "expertise": ["Control Systems", "Instrumentation"],
            "qualification": "Ph.D. Electrical Engineering",
            "experience": 8,
            "office_hours": "Monday-Wednesday: 3:00 PM - 5:00 PM"
        },
        
        # ==================== ELECTRONICS ENGINEERING DEPARTMENT (3 Faculty) ====================
        {
            "name": "Dr. Sanjay Phadke",
            "designation": "Professor",
            "department": "Electronics Engineering",
            "email": "sanjay.phadke@fcrit.ac.in",
            "phone": "+91-22-27771050",
            "cabin": "EXTC-101",
            "subjects": ["Basic Electronics Engineering", "Basic Electronics Engineering Laboratory"],
            "expertise": ["Digital Electronics", "VLSI Design", "Embedded Systems"],
            "qualification": "Ph.D. Electronics Engineering (COEP Pune)",
            "experience": 22,
            "office_hours": "Monday-Friday: 11:00 AM - 1:00 PM"
        },
        {
            "name": "Dr. Priya Mhatre",
            "designation": "Associate Professor",
            "department": "Electronics Engineering",
            "email": "priya.mhatre@fcrit.ac.in",
            "phone": "+91-22-27771051",
            "cabin": "EXTC-102",
            "subjects": ["Basic Electronics Engineering", "Wireless Technology"],
            "expertise": ["Communication Systems", "Wireless Networks", "5G"],
            "qualification": "Ph.D. Electronics & Communication",
            "experience": 15,
            "office_hours": "Tuesday-Thursday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Rohan Kulkarni",
            "designation": "Assistant Professor",
            "department": "Electronics Engineering",
            "email": "rohan.kulkarni@fcrit.ac.in",
            "phone": "+91-22-27771052",
            "cabin": "EXTC-103",
            "subjects": ["Basic Electronics Engineering Laboratory", "Cyber Physical Systems"],
            "expertise": ["IoT", "Sensor Networks", "CPS"],
            "qualification": "Ph.D. Electronics Engineering",
            "experience": 8,
            "office_hours": "Monday-Wednesday: 2:00 PM - 4:00 PM"
        },
        
        # ==================== COMPUTER SCIENCE & ENGINEERING DEPARTMENT (35+ Faculty) ====================
        
        # HOD & Senior Faculty
        {
            "name": "Dr. Rajendra Sahu",
            "designation": "Professor & HOD",
            "department": "Computer Science & Engineering",
            "email": "rajendra.sahu@fcrit.ac.in",
            "phone": "+91-22-27771100",
            "cabin": "CSE-HOD",
            "subjects": ["Artificial Intelligence", "Artificial Intelligence Laboratory"],
            "expertise": ["Artificial Intelligence", "Expert Systems", "Knowledge Representation", "Machine Learning"],
            "qualification": "Ph.D. Computer Science (IIT Bombay)",
            "experience": 26,
            "office_hours": "Monday-Friday: 10:00 AM - 12:00 PM"
        },
        
        # Programming & Foundations Faculty
        {
            "name": "Dr. Vinay Thakur",
            "designation": "Professor",
            "department": "Computer Science & Engineering",
            "email": "vinay.thakur@fcrit.ac.in",
            "phone": "+91-22-27771101",
            "cabin": "CSE-101",
            "subjects": ["Programming Laboratory-I (C)", "Programming Laboratory-II (Java)"],
            "expertise": ["Programming Languages", "Software Development", "C", "Java"],
            "qualification": "Ph.D. Computer Science",
            "experience": 23,
            "office_hours": "Monday-Friday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Neha Bhagat",
            "designation": "Associate Professor",
            "department": "Computer Science & Engineering",
            "email": "neha.bhagat@fcrit.ac.in",
            "phone": "+91-22-27771102",
            "cabin": "CSE-102",
            "subjects": ["Programming Laboratory-II (Java)", "Python Laboratory"],
            "expertise": ["Object-Oriented Programming", "Python", "Java", "Scripting"],
            "qualification": "Ph.D. Computer Science",
            "experience": 14,
            "office_hours": "Tuesday-Thursday: 11:00 AM - 1:00 PM"
        },
        {
            "name": "Dr. Siddharth Kale",
            "designation": "Assistant Professor",
            "department": "Computer Science & Engineering",
            "email": "siddharth.kale@fcrit.ac.in",
            "phone": "+91-22-27771103",
            "cabin": "CSE-103",
            "subjects": ["Programming Laboratory-I (C)", "Python Laboratory"],
            "expertise": ["C Programming", "Python", "Competitive Programming", "DSA"],
            "qualification": "M.Tech Computer Science",
            "experience": 8,
            "office_hours": "Monday-Wednesday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Pooja Raut",
            "designation": "Assistant Professor",
            "department": "Computer Science & Engineering",
            "email": "pooja.raut@fcrit.ac.in",
            "phone": "+91-22-27771104",
            "cabin": "CSE-104",
            "subjects": ["Python Laboratory", "Full stack development Laboratory"],
            "expertise": ["Web Development", "Full Stack", "React", "Node.js"],
            "qualification": "Ph.D. Computer Science",
            "experience": 7,
            "office_hours": "Wednesday-Friday: 2:00 PM - 4:00 PM"
        },
        
        # Data Structures & Algorithms Faculty
        {
            "name": "Dr. Anil Chavan",
            "designation": "Professor",
            "department": "Computer Science & Engineering",
            "email": "anil.chavan@fcrit.ac.in",
            "phone": "+91-22-27771105",
            "cabin": "CSE-105",
            "subjects": ["Data Structures", "Data Structure Laboratory", "Data Structures and Algorithms"],
            "expertise": ["Data Structures", "Algorithm Design", "Advanced DS"],
            "qualification": "Ph.D. Computer Science (IIT Kanpur)",
            "experience": 24,
            "office_hours": "Monday-Friday: 11:00 AM - 1:00 PM"
        },
        {
            "name": "Dr. Smita Desai",
            "designation": "Professor",
            "department": "Computer Science & Engineering",
            "email": "smita.desai@fcrit.ac.in",
            "phone": "+91-22-27771106",
            "cabin": "CSE-106",
            "subjects": ["Design & Analysis of Algorithm", "Design & Analysis of Algorithm Laboratory"],
            "expertise": ["Algorithms", "Complexity Theory", "Dynamic Programming"],
            "qualification": "Ph.D. Computer Science",
            "experience": 21,
            "office_hours": "Tuesday-Thursday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Kiran Wagh",
            "designation": "Associate Professor",
            "department": "Computer Science & Engineering",
            "email": "kiran.wagh@fcrit.ac.in",
            "phone": "+91-22-27771107",
            "cabin": "CSE-107",
            "subjects": ["Data Structures", "Theory of Computer Science"],
            "expertise": ["Automata Theory", "Formal Languages", "Computability"],
            "qualification": "Ph.D. Computer Science",
            "experience": 16,
            "office_hours": "Monday-Wednesday: 3:00 PM - 5:00 PM"
        },
        {
            "name": "Dr. Tanvi Shah",
            "designation": "Assistant Professor",
            "department": "Computer Science & Engineering",
            "email": "tanvi.shah@fcrit.ac.in",
            "phone": "+91-22-27771108",
            "cabin": "CSE-108",
            "subjects": ["Data Structure Laboratory", "Design & Analysis of Algorithm Laboratory"],
            "expertise": ["Algorithm Implementation", "Problem Solving", "Coding"],
            "qualification": "Ph.D. Computer Science",
            "experience": 9,
            "office_hours": "Wednesday-Friday: 10:00 AM - 12:00 PM"
        },
        
        # Database Management Faculty
        {
            "name": "Dr. Sunil Patil",
            "designation": "Professor",
            "department": "Computer Science & Engineering",
            "email": "sunil.patil@fcrit.ac.in",
            "phone": "+91-22-27771109",
            "cabin": "CSE-109",
            "subjects": ["Database Management System", "SQL Laboratory", "Advanced Database System"],
            "expertise": ["Database Systems", "SQL", "NoSQL", "Database Design"],
            "qualification": "Ph.D. Computer Science (VJTI Mumbai)",
            "experience": 25,
            "office_hours": "Monday-Friday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Archana Shirke",
            "designation": "Associate Professor",
            "department": "Computer Science & Engineering",
            "email": "archana.shirke@fcrit.ac.in",
            "phone": "+91-22-27771110",
            "cabin": "CSE-110",
            "subjects": ["Database Management System", "Dataware housing & Mining"],
            "expertise": ["Data Warehousing", "Data Mining", "Business Intelligence", "ETL"],
            "qualification": "Ph.D. Information Technology",
            "experience": 17,
            "office_hours": "Tuesday-Thursday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Manasi Kelkar",
            "designation": "Assistant Professor",
            "department": "Computer Science & Engineering",
            "email": "manasi.kelkar@fcrit.ac.in",
            "phone": "+91-22-27771111",
            "cabin": "CSE-111",
            "subjects": ["SQL Laboratory", "Data Science Laboratory"],
            "expertise": ["Data Science", "SQL", "Data Analytics"],
            "qualification": "Ph.D. Data Science",
            "experience": 8,
            "office_hours": "Monday-Wednesday: 11:00 AM - 1:00 PM"
        },
        
        # Operating Systems Faculty
        {
            "name": "Dr. Pravin Bhise",
            "designation": "Professor",
            "department": "Computer Science & Engineering",
            "email": "pravin.bhise@fcrit.ac.in",
            "phone": "+91-22-27771112",
            "cabin": "CSE-112",
            "subjects": ["Operating System", "Linux Laboratory"],
            "expertise": ["Operating Systems", "Linux Kernel", "System Programming", "Unix"],
            "qualification": "Ph.D. Computer Science",
            "experience": 24,
            "office_hours": "Monday-Friday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Shweta Koparde",
            "designation": "Associate Professor",
            "department": "Computer Science & Engineering",
            "email": "shweta.koparde@fcrit.ac.in",
            "phone": "+91-22-27771113",
            "cabin": "CSE-113",
            "subjects": ["Operating System", "System Programming and Compiler Construction"],
            "expertise": ["System Software", "Compiler Design", "Language Processors"],
            "qualification": "Ph.D. Computer Engineering",
            "experience": 15,
            "office_hours": "Tuesday-Thursday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Abhijeet Sonawane",
            "designation": "Assistant Professor",
            "department": "Computer Science & Engineering",
            "email": "abhijeet.sonawane@fcrit.ac.in",
            "phone": "+91-22-27771114",
            "cabin": "CSE-114",
            "subjects": ["Linux Laboratory", "Devops Laboratory"],
            "expertise": ["DevOps", "Linux Administration", "Docker", "Kubernetes", "CI/CD"],
            "qualification": "Ph.D. Computer Science",
            "experience": 9,
            "office_hours": "Monday-Wednesday: 3:00 PM - 5:00 PM"
        },
        
        # Computer Networks & Security Faculty
        {
            "name": "Dr. Rajiv Mane",
            "designation": "Professor",
            "department": "Computer Science & Engineering",
            "email": "rajiv.mane@fcrit.ac.in",
            "phone": "+91-22-27771115",
            "cabin": "CSE-115",
            "subjects": ["Computer Network", "Network Laboratory"],
            "expertise": ["Computer Networks", "Network Protocols", "TCP/IP", "SDN"],
            "qualification": "Ph.D. Computer Networks (IIT Madras)",
            "experience": 23,
            "office_hours": "Monday-Friday: 11:00 AM - 1:00 PM"
        },
        {
            "name": "Dr. Deepa Mhatre",
            "designation": "Professor",
            "department": "Computer Science & Engineering",
            "email": "deepa.mhatre@fcrit.ac.in",
            "phone": "+91-22-27771116",
            "cabin": "CSE-116",
            "subjects": ["Cryptography & Network Security", "Cryptography & Network Security Laboratory"],
            "expertise": ["Cryptography", "Network Security", "Information Security"],
            "qualification": "Ph.D. Information Security",
            "experience": 20,
            "office_hours": "Tuesday-Thursday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Nikhil Dalvi",
            "designation": "Associate Professor",
            "department": "Computer Science & Engineering",
            "email": "nikhil.dalvi@fcrit.ac.in",
            "phone": "+91-22-27771117",
            "cabin": "CSE-117",
            "subjects": ["Computer Network", "Cyber Security"],
            "expertise": ["Cybersecurity", "Penetration Testing", "Vulnerability Assessment"],
            "qualification": "Ph.D. Cybersecurity",
            "experience": 14,
            "office_hours": "Monday-Wednesday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Pallavi Joshi",
            "designation": "Associate Professor",
            "department": "Computer Science & Engineering",
            "email": "pallavi.joshi@fcrit.ac.in",
            "phone": "+91-22-27771118",
            "cabin": "CSE-118",
            "subjects": ["Ethical Hacking", "Digital Forensics"],
            "expertise": ["Ethical Hacking", "Digital Forensics", "Incident Response"],
            "qualification": "Ph.D. Cyber Forensics",
            "experience": 12,
            "office_hours": "Wednesday-Friday: 11:00 AM - 1:00 PM"
        },
        {
            "name": "Dr. Akash Mehta",
            "designation": "Assistant Professor",
            "department": "Computer Science & Engineering",
            "email": "akash.mehta@fcrit.ac.in",
            "phone": "+91-22-27771119",
            "cabin": "CSE-119",
            "subjects": ["Network Laboratory", "Cyber Security and Laws"],
            "expertise": ["Network Security", "Cyber Laws", "Compliance"],
            "qualification": "Ph.D. Information Security",
            "experience": 8,
            "office_hours": "Tuesday-Thursday: 3:00 PM - 5:00 PM"
        },
        
        # Software Engineering Faculty
        {
            "name": "Dr. Mukund Rao",
            "designation": "Professor",
            "department": "Computer Science & Engineering",
            "email": "mukund.rao@fcrit.ac.in",
            "phone": "+91-22-27771120",
            "cabin": "CSE-120",
            "subjects": ["Software Engineering", "Software Development Laboratory"],
            "expertise": ["Software Engineering", "Agile Development", "SDLC", "Testing"],
            "qualification": "Ph.D. Software Engineering",
            "experience": 22,
            "office_hours": "Monday-Friday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Rashmi Phalke",
            "designation": "Associate Professor",
            "department": "Computer Science & Engineering",
            "email": "rashmi.phalke@fcrit.ac.in",
            "phone": "+91-22-27771121",
            "cabin": "CSE-121",
            "subjects": ["Software Engineering", "Human Computer Interaction"],
            "expertise": ["HCI", "UI/UX Design", "Usability Engineering"],
            "qualification": "Ph.D. Human Computer Interaction",
            "experience": 15,
            "office_hours": "Tuesday-Thursday: 11:00 AM - 1:00 PM"
        },
        {
            "name": "Dr. Varun Potdar",
            "designation": "Assistant Professor",
            "department": "Computer Science & Engineering",
            "email": "varun.potdar@fcrit.ac.in",
            "phone": "+91-22-27771122",
            "cabin": "CSE-122",
            "subjects": ["Software Development Laboratory", "Full stack development Laboratory"],
            "expertise": ["Full Stack Development", "MERN Stack", "REST APIs"],
            "qualification": "M.Tech Software Engineering",
            "experience": 8,
            "office_hours": "Monday-Wednesday: 2:00 PM - 4:00 PM"
        },
        
        # AI/ML Faculty
        {
            "name": "Dr. Vivek Kshirsagar",
            "designation": "Professor",
            "department": "Computer Science & Engineering",
            "email": "vivek.kshirsagar@fcrit.ac.in",
            "phone": "+91-22-27771123",
            "cabin": "CSE-123",
            "subjects": ["Machine Learning", "Machine Learning Laboratory"],
            "expertise": ["Machine Learning", "Deep Learning", "Neural Networks", "TensorFlow"],
            "qualification": "Ph.D. Machine Learning (IISc Bangalore)",
            "experience": 19,
            "office_hours": "Monday-Friday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Anagha Kulkarni",
            "designation": "Associate Professor",
            "department": "Computer Science & Engineering",
            "email": "anagha.kulkarni@fcrit.ac.in",
            "phone": "+91-22-27771124",
            "cabin": "CSE-124",
            "subjects": ["Natural Language Processing", "Information Retrieval System"],
            "expertise": ["NLP", "Text Mining", "Information Retrieval", "Search Engines"],
            "qualification": "Ph.D. Natural Language Processing",
            "experience": 14,
            "office_hours": "Tuesday-Thursday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Sachin Deshpande",
            "designation": "Associate Professor",
            "department": "Computer Science & Engineering",
            "email": "sachin.deshpande@fcrit.ac.in",
            "phone": "+91-22-27771125",
            "cabin": "CSE-125",
            "subjects": ["Soft Computing", "Artificial Intelligence"],
            "expertise": ["Fuzzy Logic", "Genetic Algorithms", "Swarm Intelligence"],
            "qualification": "Ph.D. Soft Computing",
            "experience": 13,
            "office_hours": "Monday-Wednesday: 11:00 AM - 1:00 PM"
        },
        {
            "name": "Dr. Sneha Gawande",
            "designation": "Assistant Professor",
            "department": "Computer Science & Engineering",
            "email": "sneha.gawande@fcrit.ac.in",
            "phone": "+91-22-27771126",
            "cabin": "CSE-126",
            "subjects": ["Foundation Models & Generative AI", "Responsible & Safe AI Systems"],
            "expertise": ["Generative AI", "LLMs", "GPT", "AI Ethics", "Responsible AI"],
            "qualification": "Ph.D. Artificial Intelligence",
            "experience": 6,
            "office_hours": "Wednesday-Friday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Tejas Parekh",
            "designation": "Assistant Professor",
            "department": "Computer Science & Engineering",
            "email": "tejas.parekh@fcrit.ac.in",
            "phone": "+91-22-27771127",
            "cabin": "CSE-127",
            "subjects": ["Artificial Intelligence Laboratory", "Recommender System"],
            "expertise": ["Recommendation Systems", "Collaborative Filtering", "Content-based Filtering"],
            "qualification": "Ph.D. Machine Learning",
            "experience": 7,
            "office_hours": "Tuesday-Thursday: 3:00 PM - 5:00 PM"
        },
        {
            "name": "Dr. Gauri Deshpande",
            "designation": "Assistant Professor",
            "department": "Computer Science & Engineering",
            "email": "gauri.deshpande@fcrit.ac.in",
            "phone": "+91-22-27771128",
            "cabin": "CSE-128",
            "subjects": ["Time Series Analysis", "Data analytics & Visualization Laboratory"],
            "expertise": ["Time Series", "Forecasting", "Statistical Learning"],
            "qualification": "Ph.D. Data Science",
            "experience": 6,
            "office_hours": "Monday-Wednesday: 10:00 AM - 12:00 PM"
        },
        
        # Cloud & Distributed Systems Faculty
        {
            "name": "Dr. Parag Bhosale",
            "designation": "Professor",
            "department": "Computer Science & Engineering",
            "email": "parag.bhosale@fcrit.ac.in",
            "phone": "+91-22-27771129",
            "cabin": "CSE-129",
            "subjects": ["Cloud Computing Services", "Cloud Computing Laboratory", "Cloud Computing"],
            "expertise": ["Cloud Computing", "AWS", "Azure", "GCP", "Distributed Systems"],
            "qualification": "Ph.D. Distributed Computing",
            "experience": 20,
            "office_hours": "Monday-Friday: 11:00 AM - 1:00 PM"
        },
        {
            "name": "Dr. Amruta Pansare",
            "designation": "Associate Professor",
            "department": "Computer Science & Engineering",
            "email": "amruta.pansare@fcrit.ac.in",
            "phone": "+91-22-27771130",
            "cabin": "CSE-130",
            "subjects": ["Cloud Computing", "Edge Computing"],
            "expertise": ["Edge Computing", "Fog Computing", "IoT Edge", "Serverless"],
            "qualification": "Ph.D. Computer Engineering",
            "experience": 13,
            "office_hours": "Tuesday-Thursday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Omkar Joshi",
            "designation": "Assistant Professor",
            "department": "Computer Science & Engineering",
            "email": "omkar.joshi@fcrit.ac.in",
            "phone": "+91-22-27771131",
            "cabin": "CSE-131",
            "subjects": ["Cloud Computing Laboratory", "High Performance Computing"],
            "expertise": ["HPC", "Parallel Computing", "MPI", "CUDA"],
            "qualification": "Ph.D. High Performance Computing",
            "experience": 8,
            "office_hours": "Monday-Wednesday: 3:00 PM - 5:00 PM"
        },
        
        # Big Data & Analytics Faculty
        {
            "name": "Dr. Rucha Deshpande",
            "designation": "Associate Professor",
            "department": "Computer Science & Engineering",
            "email": "rucha.deshpande@fcrit.ac.in",
            "phone": "+91-22-27771132",
            "cabin": "CSE-132",
            "subjects": ["Big Data Analytics", "Data analytics & Visualization Laboratory"],
            "expertise": ["Big Data", "Hadoop", "Spark", "Data Visualization"],
            "qualification": "Ph.D. Big Data Analytics",
            "experience": 12,
            "office_hours": "Tuesday-Thursday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Pranav Kulkarni",
            "designation": "Assistant Professor",
            "department": "Computer Science & Engineering",
            "email": "pranav.kulkarni@fcrit.ac.in",
            "phone": "+91-22-27771133",
            "cabin": "CSE-133",
            "subjects": ["Data Science Laboratory", "Big Data Analytics"],
            "expertise": ["Data Science", "Statistical Analysis", "R Programming"],
            "qualification": "Ph.D. Data Science",
            "experience": 7,
            "office_hours": "Monday-Wednesday: 11:00 AM - 1:00 PM"
        },
        
        # Computer Graphics Faculty
        {
            "name": "Dr. Nilesh Bansode",
            "designation": "Associate Professor",
            "department": "Computer Science & Engineering",
            "email": "nilesh.bansode@fcrit.ac.in",
            "phone": "+91-22-27771134",
            "cabin": "CSE-134",
            "subjects": ["Computer graphics", "Data analytics & Visualization Laboratory"],
            "expertise": ["Computer Graphics", "3D Modeling", "OpenGL", "Visualization"],
            "qualification": "Ph.D. Computer Graphics",
            "experience": 14,
            "office_hours": "Wednesday-Friday: 10:00 AM - 12:00 PM"
        },
        
        # Blockchain & Emerging Tech Faculty
        {
            "name": "Dr. Aniket Dhamane",
            "designation": "Assistant Professor",
            "department": "Computer Science & Engineering",
            "email": "aniket.dhamane@fcrit.ac.in",
            "phone": "+91-22-27771135",
            "cabin": "CSE-135",
            "subjects": ["Blockchain Technology", "Cryptography & Network Security Laboratory"],
            "expertise": ["Blockchain", "Smart Contracts", "Ethereum", "DApps", "Web3"],
            "qualification": "Ph.D. Blockchain Technology",
            "experience": 6,
            "office_hours": "Tuesday-Thursday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Chetan Agrawal",
            "designation": "Associate Professor",
            "department": "Computer Science & Engineering",
            "email": "chetan.agrawal@fcrit.ac.in",
            "phone": "+91-22-27771136",
            "cabin": "CSE-136",
            "subjects": ["Quantum Computing", "Theory of Computer Science"],
            "expertise": ["Quantum Computing", "Quantum Algorithms", "Qubits"],
            "qualification": "Ph.D. Quantum Computing",
            "experience": 11,
            "office_hours": "Monday-Wednesday: 2:00 PM - 4:00 PM"
        },
        
        # Projects Faculty
        {
            "name": "Dr. Hemant Kasturiwale",
            "designation": "Professor",
            "department": "Computer Science & Engineering",
            "email": "hemant.kasturiwale@fcrit.ac.in",
            "phone": "+91-22-27771137",
            "cabin": "CSE-137",
            "subjects": ["Mini Project-1A", "Mini Project-1B", "Major Project-A", "Major Project-B"],
            "expertise": ["Project Management", "Research Methodology", "Software Development"],
            "qualification": "Ph.D. Computer Science",
            "experience": 24,
            "office_hours": "Monday-Friday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Suchitra Patil",
            "designation": "Associate Professor",
            "department": "Computer Science & Engineering",
            "email": "suchitra.patil@fcrit.ac.in",
            "phone": "+91-22-27771138",
            "cabin": "CSE-138",
            "subjects": ["Mini Project-2A", "Mini Project-2B", "Major Project-A", "Major Project-B"],
            "expertise": ["Project Supervision", "Research Guidance", "Technical Writing"],
            "qualification": "Ph.D. Computer Science",
            "experience": 16,
            "office_hours": "Tuesday-Thursday: 11:00 AM - 1:00 PM"
        },
        {
            "name": "Dr. Jayant Gadge",
            "designation": "Associate Professor",
            "department": "Computer Science & Engineering",
            "email": "jayant.gadge@fcrit.ac.in",
            "phone": "+91-22-27771139",
            "cabin": "CSE-139",
            "subjects": ["Mini Project-1A", "Major Project-A", "Internship"],
            "expertise": ["Industry Collaboration", "Internship Coordination", "Project Development"],
            "qualification": "Ph.D. Computer Engineering",
            "experience": 15,
            "office_hours": "Monday-Wednesday: 3:00 PM - 5:00 PM"
        },
        
        # ==================== HUMANITIES & SOCIAL SCIENCES (8 Faculty) ====================
        {
            "name": "Dr. Meera Nair",
            "designation": "Professor & HOD",
            "department": "Humanities & Social Sciences",
            "email": "meera.nair@fcrit.ac.in",
            "phone": "+91-22-27771200",
            "cabin": "HSS-101",
            "subjects": ["Professional Communication and Ethics-I", "Professional Communication and Ethics-II"],
            "expertise": ["Technical Communication", "Business Communication", "Professional Ethics"],
            "qualification": "Ph.D. English (University of Mumbai)",
            "experience": 22,
            "office_hours": "Monday-Friday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Govind Sharma",
            "designation": "Associate Professor",
            "department": "Humanities & Social Sciences",
            "email": "govind.sharma@fcrit.ac.in",
            "phone": "+91-22-27771201",
            "cabin": "HSS-102",
            "subjects": ["Universal Human Values", "Indian Knowledge System"],
            "expertise": ["Indian Philosophy", "Ethics", "Human Values"],
            "qualification": "Ph.D. Philosophy",
            "experience": 18,
            "office_hours": "Tuesday-Thursday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Kavita Iyer",
            "designation": "Associate Professor",
            "department": "Humanities & Social Sciences",
            "email": "kavita.iyer@fcrit.ac.in",
            "phone": "+91-22-27771202",
            "cabin": "HSS-103",
            "subjects": ["Environment and Sustainability", "Environmental Management"],
            "expertise": ["Environmental Studies", "Sustainability", "Climate Change"],
            "qualification": "Ph.D. Environmental Science",
            "experience": 15,
            "office_hours": "Monday-Wednesday: 11:00 AM - 1:00 PM"
        },
        {
            "name": "Dr. Yogita Bhalerao",
            "designation": "Assistant Professor",
            "department": "Humanities & Social Sciences",
            "email": "yogita.bhalerao@fcrit.ac.in",
            "phone": "+91-22-27771203",
            "cabin": "HSS-104",
            "subjects": ["Research Methodology", "IPR and Patenting"],
            "expertise": ["Research Methods", "Intellectual Property", "Patent Law"],
            "qualification": "Ph.D. Law",
            "experience": 9,
            "office_hours": "Wednesday-Friday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Suresh Menon",
            "designation": "Assistant Professor",
            "department": "Humanities & Social Sciences",
            "email": "suresh.menon@fcrit.ac.in",
            "phone": "+91-22-27771204",
            "cabin": "HSS-105",
            "subjects": ["Professional Ethics and CSR", "Disaster Management and Mitigation Measures"],
            "expertise": ["Corporate Ethics", "CSR", "Disaster Management"],
            "qualification": "Ph.D. Social Sciences",
            "experience": 8,
            "office_hours": "Tuesday-Thursday: 3:00 PM - 5:00 PM"
        },
        
        # Liberal Learning Course Faculty
        {
            "name": "Dr. Asha Kulkarni",
            "designation": "Associate Professor",
            "department": "Humanities & Social Sciences",
            "email": "asha.kulkarni@fcrit.ac.in",
            "phone": "+91-22-27771205",
            "cabin": "HSS-106",
            "subjects": ["Art of Living", "Yoga and Meditation"],
            "expertise": ["Yoga", "Meditation", "Mindfulness", "Wellness"],
            "qualification": "Ph.D. Yoga Science",
            "experience": 16,
            "office_hours": "Monday-Wednesday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Rahul Pandit",
            "designation": "Assistant Professor",
            "department": "Humanities & Social Sciences",
            "email": "rahul.pandit@fcrit.ac.in",
            "phone": "+91-22-27771206",
            "cabin": "HSS-107",
            "subjects": ["Health and Wellness", "Diet and Nutrition"],
            "expertise": ["Health Science", "Nutrition", "Dietetics"],
            "qualification": "Ph.D. Health Sciences",
            "experience": 8,
            "office_hours": "Wednesday-Friday: 11:00 AM - 1:00 PM"
        },
        {
            "name": "Dr. Priyanka Deshpande",
            "designation": "Assistant Professor",
            "department": "Humanities & Social Sciences",
            "email": "priyanka.deshpande@fcrit.ac.in",
            "phone": "+91-22-27771207",
            "cabin": "HSS-108",
            "subjects": ["Personality Development", "Art of Living"],
            "expertise": ["Personality Development", "Soft Skills", "Leadership"],
            "qualification": "Ph.D. Psychology",
            "experience": 7,
            "office_hours": "Tuesday-Thursday: 10:00 AM - 12:00 PM"
        },
        
        # ==================== MANAGEMENT STUDIES (8 Faculty) ====================
        {
            "name": "Dr. Vinod Prabhu",
            "designation": "Professor",
            "department": "Management Studies",
            "email": "vinod.prabhu@fcrit.ac.in",
            "phone": "+91-22-27771210",
            "cabin": "MGMT-101",
            "subjects": ["Entrepreneurship", "Entrepreneurship Development and Management"],
            "expertise": ["Entrepreneurship", "Startup Ecosystem", "Innovation Management"],
            "qualification": "Ph.D. Management (JBIMS Mumbai)",
            "experience": 24,
            "office_hours": "Monday-Friday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Nandini Shah",
            "designation": "Associate Professor",
            "department": "Management Studies",
            "email": "nandini.shah@fcrit.ac.in",
            "phone": "+91-22-27771211",
            "cabin": "MGMT-102",
            "subjects": ["Financial Planning", "Finance Management"],
            "expertise": ["Financial Management", "Investment", "Corporate Finance"],
            "qualification": "Ph.D. Finance",
            "experience": 16,
            "office_hours": "Tuesday-Thursday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Ajay Mishra",
            "designation": "Associate Professor",
            "department": "Management Studies",
            "email": "ajay.mishra@fcrit.ac.in",
            "phone": "+91-22-27771212",
            "cabin": "MGMT-103",
            "subjects": ["Project Management", "Product Design"],
            "expertise": ["Project Management", "PMP", "Agile", "Scrum"],
            "qualification": "Ph.D. Management",
            "experience": 15,
            "office_hours": "Monday-Wednesday: 11:00 AM - 1:00 PM"
        },
        {
            "name": "Dr. Seema Deshmukh",
            "designation": "Associate Professor",
            "department": "Management Studies",
            "email": "seema.deshmukh@fcrit.ac.in",
            "phone": "+91-22-27771213",
            "cabin": "MGMT-104",
            "subjects": ["Human Resource Management", "Management Information System"],
            "expertise": ["HRM", "MIS", "Organizational Behavior", "Talent Management"],
            "qualification": "Ph.D. HRM",
            "experience": 14,
            "office_hours": "Wednesday-Friday: 10:00 AM - 12:00 PM"
        },
        {
            "name": "Dr. Rahul Thakkar",
            "designation": "Assistant Professor",
            "department": "Management Studies",
            "email": "rahul.thakkar@fcrit.ac.in",
            "phone": "+91-22-27771214",
            "cabin": "MGMT-105",
            "subjects": ["Digital Business Management", "Product Lifecycle Management"],
            "expertise": ["Digital Marketing", "E-commerce", "Digital Transformation"],
            "qualification": "Ph.D. Marketing",
            "experience": 8,
            "office_hours": "Tuesday-Thursday: 3:00 PM - 5:00 PM"
        },
        {
            "name": "Dr. Neelam Gupta",
            "designation": "Assistant Professor",
            "department": "Management Studies",
            "email": "neelam.gupta@fcrit.ac.in",
            "phone": "+91-22-27771215",
            "cabin": "MGMT-106",
            "subjects": ["Circular Economy", "Design of Experiments"],
            "expertise": ["Sustainability", "Circular Economy", "Green Business"],
            "qualification": "Ph.D. Sustainable Management",
            "experience": 7,
            "office_hours": "Monday-Wednesday: 2:00 PM - 4:00 PM"
        },
        {
            "name": "Dr. Sagar Patil",
            "designation": "Assistant Professor",
            "department": "Management Studies",
            "email": "sagar.patil@fcrit.ac.in",
            "phone": "+91-22-27771216",
            "cabin": "MGMT-107",
            "subjects": ["Operation Research", "Development Engineering"],
            "expertise": ["Operations Management", "Supply Chain", "Logistics"],
            "qualification": "Ph.D. Operations Management",
            "experience": 9,
            "office_hours": "Wednesday-Friday: 11:00 AM - 1:00 PM"
        },
    ]
    
    # Insert all faculty
    result = await db.faculty.insert_many(faculty_data)
    print(f"✅ Inserted {len(result.inserted_ids)} faculty members")
    
    # Print distribution
    print("\n📊 Faculty Distribution by Department:")
    dept_count = {}
    for faculty in faculty_data:
        dept = faculty["department"]
        dept_count[dept] = dept_count.get(dept, 0) + 1
    
    for dept, count in sorted(dept_count.items()):
        print(f"   • {dept}: {count}")
    
    print(f"\n✅ Total faculty: {len(faculty_data)}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(populate_complete_faculty())