#!/usr/bin/env python3
# scripts/seed_all_chatbot_data.py
"""
Master script to seed ALL chatbot data:
- Career paths
- Syllabus data from JSON files
- Analytics initialization
- Database indexes

Run from project root:
    python -m scripts.seed_all_chatbot_data

Or:
    cd academic-advisor-backend
    python scripts/seed_all_chatbot_data.py
"""

import asyncio
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# ══════════════════════════════════════════════════════════
# PATH SETUP
# ══════════════════════════════════════════════════════════

current_file = Path(__file__).resolve()
backend_root = current_file.parent.parent
sys.path.insert(0, str(backend_root))

print("=" * 70)
print("ACADEMIC ADVISOR - COMPLETE DATA SEEDING")
print("=" * 70)
print(f"Backend root: {backend_root}")

# ══════════════════════════════════════════════════════════
# IMPORTS
# ══════════════════════════════════════════════════════════

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from beanie import init_beanie
    from app.config import settings
    print(f"✅ Database: {settings.MONGODB_DATABASE}")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Make sure you're in the backend directory and dependencies are installed")
    sys.exit(1)


# ══════════════════════════════════════════════════════════
# SYLLABUS PARSER
# ══════════════════════════════════════════════════════════

class SyllabusParser:
    """Parse JSON syllabus files and extract structured data."""

    def __init__(self, file_path: Path, dept_name: str, dept_code: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            self.pages = json.load(f)
        self.dept_name = dept_name
        self.dept_code = dept_code
        self.abbreviations: Dict[str, str] = {}
        self.subjects: Dict[str, Dict] = {}
        self.electives: Dict[str, Dict] = {}

    @staticmethod
    def roman_to_int(roman: str) -> int:
        """Convert Roman numeral to integer."""
        roman = roman.upper()
        values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        total = 0
        for i in range(len(roman)):
            if i > 0 and values.get(roman[i], 0) > values.get(roman[i-1], 0):
                total += values[roman[i]] - 2 * values[roman[i-1]]
            else:
                total += values.get(roman[i], 0)
        return total

    def parse_all(self):
        """Parse all sections of the syllabus."""
        self._parse_curriculum_tables()
        self._parse_detailed_syllabus()
        self._parse_elective_lists()

    def _parse_curriculum_tables(self):
        """Extract courses from curriculum structure tables."""
        for page in self.pages:
            text = page.get('text', '')
            tables = page.get('tables', [])
            
            # Determine semester
            sem_match = re.search(r'Semester[-\s]*([IVXLCDM]+|\d+)', text, re.IGNORECASE)
            semester = 1
            if sem_match:
                sem_str = sem_match.group(1)
                semester = self.roman_to_int(sem_str) if sem_str.isalpha() else int(sem_str)

            for table in tables:
                if not isinstance(table, list) or len(table) < 2:
                    continue
                    
                header_row = table[0] if table else []
                if not isinstance(header_row, list):
                    continue
                    
                header_str = ' '.join(str(c) for c in header_row).lower()
                if 'course code' not in header_str and 'code' not in header_str:
                    continue
                    
                for row in table[1:]:
                    if not isinstance(row, list) or len(row) < 2:
                        continue
                        
                    code = str(row[0]).strip().upper()
                    name = str(row[1]).strip() if len(row) > 1 else ''
                    
                    if not re.match(r'^[A-Z]{2,6}\d{3,4}$', code):
                        continue
                    
                    # Extract credits
                    credits = 3
                    for cell in row[2:]:
                        cell_str = str(cell).strip()
                        credit_match = re.match(r'(\d+)(?:\+\d+)?', cell_str)
                        if credit_match:
                            credits = int(credit_match.group(1))
                            break
                    
                    self.subjects[code] = {
                        'code': code,
                        'name': name,
                        'credits': credits,
                        'semester': semester,
                        'type': self._infer_type(code),
                        'teaching_scheme': {'L': 0, 'P': 0, 'T': 0},
                        'units': [],
                        'learning_outcomes': [],
                        'reference_books': [],
                        'prerequisites': [],
                        'examination_scheme': {},
                        'description': ''
                    }

    def _parse_detailed_syllabus(self):
        """Parse detailed module/unit information."""
        current_subject = None
        current_unit = None

        for page in self.pages:
            text = page.get('text', '')
            tables = page.get('tables', [])

            # Look for subject header
            header_match = re.search(
                r'([A-Z]{2,4})\s+([A-Z]+\d{3,4})\s+([A-Z][A-Z\s\-&]+?)\s+(\d+)',
                text
            )
            if header_match:
                code = header_match.group(2)
                if code in self.subjects:
                    current_subject = self.subjects[code]
                continue

            if not current_subject:
                continue

            # Parse module tables
            for table in tables:
                if not isinstance(table, list):
                    continue
                    
                for row in table:
                    if not isinstance(row, list) or len(row) < 2:
                        continue
                    
                    module_col = str(row[0]).strip()
                    details_col = str(row[1]) if len(row) > 1 else ''
                    hrs_col = str(row[2]) if len(row) > 2 else ''
                    
                    module_match = re.match(r'^(\d+)\.?$', module_col)
                    if module_match:
                        unit_num = int(module_match.group(1))
                        
                        lines = details_col.split('\n')
                        title = lines[0] if lines else f'Unit {unit_num}'
                        title = re.sub(
                            r'^(Contents|Learning\s+Objective).*?:',
                            '',
                            title,
                            flags=re.IGNORECASE
                        ).strip()[:200]
                        
                        hours = None
                        hrs_match = re.search(r'(\d+)', hrs_col)
                        if hrs_match:
                            hours = int(hrs_match.group(1))
                        
                        current_unit = {
                            'unit_number': unit_num,
                            'title': title,
                            'description': details_col[:1000],
                            'lecture_hours': hours,
                            'topics': [],
                            'keywords': []
                        }
                        current_subject['units'].append(current_unit)
                        
                        # Extract topics from bullet points
                        topics = re.findall(r'[•\-]\s*([^•\-\n]+)', details_col)
                        for topic in topics:
                            topic = topic.strip()
                            if topic and 3 < len(topic) < 200 and not topic.upper().startswith('LO '):
                                current_unit['topics'].append({
                                    'name': topic,
                                    'keywords': self._extract_keywords(topic),
                                    'key_points': [],
                                    'examples': []
                                })

            # Extract learning outcomes
            lo_matches = re.findall(r'LO\s*[\d.]+:\s*(.+?)(?=LO\s*[\d.]|$)', text, re.DOTALL)
            for lo in lo_matches:
                lo_clean = lo.strip()[:500]
                if lo_clean and lo_clean not in current_subject['learning_outcomes']:
                    current_subject['learning_outcomes'].append(lo_clean)

            # Extract reference books
            if 'Text Book' in text or 'Reference Book' in text:
                books = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\Z)', text, re.DOTALL)
                for book in books:
                    book_clean = book.strip()[:300]
                    if book_clean and 'http' not in book_clean.lower():
                        if book_clean not in current_subject['reference_books']:
                            current_subject['reference_books'].append(book_clean)

    def _parse_elective_lists(self):
        """Extract elective courses."""
        for page in self.pages:
            text = page.get('text', '')
            tables = page.get('tables', [])
            
            elective_type = None
            if 'Program Elective' in text:
                elective_type = 'PEC'
            elif 'Open Elective' in text:
                elective_type = 'OEC'
            elif 'Liberal Learning' in text:
                elective_type = 'LLC'
            elif 'Multidisciplinary' in text:
                elective_type = 'MDM'
            
            if elective_type:
                for table in tables:
                    if isinstance(table, list):
                        for row in table:
                            if isinstance(row, list) and len(row) >= 2:
                                code = str(row[0]).strip().upper()
                                name = str(row[1]).strip()
                                if re.match(r'^[A-Z]{2,6}\d{3,4}$', code):
                                    self.electives[code] = {
                                        'code': code,
                                        'name': name,
                                        'type': elective_type
                                    }

    def _infer_type(self, code: str) -> str:
        """Map course code to subject type."""
        type_map = {
            'BSC': 'BSC', 'ESC': 'ESC', 'PCC': 'PCC',
            'PEC': 'PEC', 'OEC': 'OEC', 'LLC': 'LLC',
            'MDM': 'MDM', 'SEC': 'SEC', 'HSS': 'HSS',
        }
        for prefix, typ in type_map.items():
            if prefix in code:
                return typ
        return 'PCC'

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        keywords = []
        patterns = [
            r'\b(algorithm|data structure|tree|graph|stack|queue|array)\b',
            r'\b(database|sql|query|normalization|transaction)\b',
            r'\b(network|protocol|tcp|udp|routing|http)\b',
            r'\b(process|thread|scheduling|memory|deadlock|mutex)\b',
            r'\b(machine learning|neural|classification|regression)\b',
            r'\b(vector|matrix|linear|eigenvalue)\b',
        ]
        text_lower = text.lower()
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            keywords.extend(matches)
        return list(set(keywords))[:10]

    async def save_to_db(self, dept_id) -> tuple:
        """Save parsed data to MongoDB."""
        from app.models.syllabus import Subject, SubjectUnit, Topic
        
        saved_subjects = 0
        saved_topics = 0

        for code, sub_data in self.subjects.items():
            existing = await Subject.find_one(Subject.code == code)
            if existing:
                continue

            subject = Subject(
                code=code,
                name=sub_data['name'],
                department=dept_id,
                semester=sub_data.get('semester', 1),
                credits=sub_data['credits'],
                subject_type=sub_data['type'],
                teaching_scheme=sub_data.get('teaching_scheme', {'L': 0, 'P': 0, 'T': 0}),
                description=sub_data.get('description', ''),
                learning_outcomes=sub_data.get('learning_outcomes', []),
                reference_books=sub_data.get('reference_books', []),
                prerequisites=sub_data.get('prerequisites', []),
                examination_scheme=sub_data.get('examination_scheme', {})
            )
            await subject.insert()
            saved_subjects += 1

            for unit_data in sub_data.get('units', []):
                unit = SubjectUnit(
                    subject=subject,
                    unit_number=unit_data['unit_number'],
                    title=unit_data.get('title', ''),
                    description=unit_data.get('description'),
                    lecture_hours=unit_data.get('lecture_hours'),
                    keywords=unit_data.get('keywords', [])
                )
                await unit.insert()
                
                for topic_data in unit_data.get('topics', []):
                    topic = Topic(
                        unit=unit,
                        name=topic_data['name'],
                        keywords=topic_data.get('keywords', []),
                        key_points=topic_data.get('key_points', []),
                        examples=topic_data.get('examples', []),
                        difficulty_level='medium'
                    )
                    await topic.insert()
                    saved_topics += 1

        return saved_subjects, saved_topics


# ══════════════════════════════════════════════════════════
# MAIN SEEDING FUNCTION
# ══════════════════════════════════════════════════════════

async def main():
    """Main seeding function."""
    
    # Connect to database
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    # Import all models
    from app.models.chatbot import ChatSession, ChatMessage, ChatFeedback, ChatbotAnalyticsDoc
    from app.models.career import CareerPath
    from app.models.syllabus import (
        Department, Subject, SubjectUnit, Topic, Abbreviation,
        ProgramElective, OpenElective, LiberalLearningCourse,
        MDMCourse, CreditStructure
    )
    
    # Initialize Beanie
    await init_beanie(
        database=db,
        document_models=[
            ChatSession, ChatMessage, ChatFeedback, ChatbotAnalyticsDoc, CareerPath,
            Department, Subject, SubjectUnit, Topic, Abbreviation,
            ProgramElective, OpenElective, LiberalLearningCourse,
            MDMCourse, CreditStructure
        ]
    )
    print(f"✅ Connected to MongoDB: {settings.MONGODB_DATABASE}")
    
    # ─────────────────────────────────────────────────────
    # Step 1: Seed Career Data
    # ─────────────────────────────────────────────────────
    print("\n📊 Step 1: Seeding Career Data...")
    try:
        career_count = await CareerPath.find().count()
        if career_count == 0:
            from scripts.seed_career_data import seed_careers
            career_count = await seed_careers()
            print(f"   ✅ {career_count} career paths seeded")
        else:
            print(f"   ✅ Career data exists ({career_count} paths)")
    except Exception as e:
        print(f"   ⚠️ Career seeding: {e}")
    
    # ─────────────────────────────────────────────────────
    # Step 2: Seed Syllabus Data
    # ─────────────────────────────────────────────────────
    print("\n📚 Step 2: Seeding Syllabus Data...")
    
    json_dir = backend_root / "json_data"
    files = [
        (json_dir / "FY_R25_IT.json", "Information Technology", "IT"),
        (json_dir / "SY_R2024.1_IT.json", "Information Technology", "IT"),
        (json_dir / "TY_R2024.1_IT.json", "Information Technology", "IT"),
        (json_dir / "B_TECH_CSE_Scheme.json", "Computer Science & Engineering", "CSE"),
    ]
    
    total_subjects = 0
    total_topics = 0
    
    for file_path, dept_name, dept_code in files:
        if not file_path.exists():
            print(f"   ⚠️ {file_path.name} not found")
            continue
        
        print(f"   📄 Processing {file_path.name}...")
        
        # Get or create department
        dept = await Department.find_one(Department.code == dept_code)
        if not dept:
            dept = Department(code=dept_code, name=dept_name)
            await dept.insert()
            print(f"      Created department: {dept_name}")
        
        # Parse and save
        try:
            parser = SyllabusParser(file_path, dept_name, dept_code)
            parser.parse_all()
            subjects, topics = await parser.save_to_db(dept.id)
            total_subjects += subjects
            total_topics += topics
            print(f"      ✅ {subjects} subjects, {topics} topics")
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    print(f"   📊 Total: {total_subjects} subjects, {total_topics} topics")
    
    # ─────────────────────────────────────────────────────
    # Step 3: Initialize Analytics
    # ─────────────────────────────────────────────────────
    print("\n📈 Step 3: Initializing Analytics...")
    try:
        from app.repositories.analytics_repository import AnalyticsRepository
        repo = AnalyticsRepository()
        await repo.get_or_create_today()
        print("   ✅ Analytics document initialized")
    except Exception as e:
        print(f"   ⚠️ Analytics: {e}")
    
    # ─────────────────────────────────────────────────────
    # Step 4: Create Database Indexes
    # ─────────────────────────────────────────────────────
    print("\n🔧 Step 4: Creating Database Indexes...")
    try:
        # Subjects
        await db.subjects.create_index("code", unique=True, sparse=True)
        await db.subjects.create_index("semester")
        
        # Topics
        await db.topics.create_index("name")
        
        # Sessions
        await db.chat_sessions.create_index("user_id")
        await db.chat_sessions.create_index("session_token", unique=True, sparse=True)
        
        # Careers
        await db.career_paths.create_index("category")
        
        print("   ✅ Indexes created")
    except Exception as e:
        print(f"   ⚠️ Index creation: {e}")
    
    # ─────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("✅ SEEDING COMPLETE!")
    print("=" * 70)
    
    # Get final counts
    subject_count = await Subject.find().count()
    topic_count = await Topic.find().count()
    career_count = await CareerPath.find().count()
    dept_count = await Department.find().count()
    
    print(f"""
📊 Database Statistics:
   - Departments: {dept_count}
   - Subjects: {subject_count}
   - Topics: {topic_count}
   - Career Paths: {career_count}

🚀 Next Steps:
   1. Start the backend:
      uvicorn app.main:app --reload
   
   2. Test chatbot health:
      curl http://localhost:8000/api/v1/chatbot/health
   
   3. Test a query:
      curl -X POST http://localhost:8000/api/v1/chatbot/chat \\
        -H "Content-Type: application/json" \\
        -d '{{"message": "Explain deadlock in Operating Systems"}}'
""")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(main())