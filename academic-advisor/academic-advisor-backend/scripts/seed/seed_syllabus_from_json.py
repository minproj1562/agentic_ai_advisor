#!/usr/bin/env python3
"""
Load syllabus data from JSON files into MongoDB.
Run from project root: python -m scripts.seed.seed_syllabus_from_json
"""
# academic-advisor/academic-advisor-backend/scripts/seed/seed_syllabus_from_json.py

import json
import re
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# ----------------------------------------------------------------------
# Add backend root to Python path so we can import app.models
# ----------------------------------------------------------------------
current_file = Path(__file__).resolve()               # .../scripts/seed/seed_syllabus_from_json.py
backend_root = current_file.parent.parent.parent      # .../academic-advisor-backend/
sys.path.insert(0, str(backend_root))

# Debug: verify paths
print(f"Backend root: {backend_root}")
app_path = backend_root / "app"
models_path = app_path / "models"
syllabus_path = models_path / "syllabus.py"
if syllabus_path.exists():
    print(f"✅ syllabus.py found at {syllabus_path}")
else:
    print(f"❌ syllabus.py NOT found at {syllabus_path}")
    # List contents to help debug
    if app_path.exists():
        print(f"Contents of app: {[p.name for p in app_path.iterdir()]}")
    if models_path.exists():
        print(f"Contents of models: {[p.name for p in models_path.iterdir()]}")
    sys.exit(1)

# Now try imports
try:
    import motor.motor_asyncio
    from beanie import init_beanie, PydanticObjectId
    from app.models.syllabus import (
        Department, Subject, SubjectUnit, Topic, Abbreviation,
        ProgramElective, OpenElective, LiberalLearningCourse,
        MDMCourse, CreditStructure
    )
    print("✅ Imports succeeded")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


async def init_db():
    """Initialize Beanie with MongoDB connection."""
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(
        database=client.syllabus_db,
        document_models=[
            Department, Subject, SubjectUnit, Topic, Abbreviation,
            ProgramElective, OpenElective, LiberalLearningCourse,
            MDMCourse, CreditStructure
        ]
    )


class SyllabusParser:
    """Parse a single JSON file and prepare data for insertion."""

    def __init__(self, file_path: Path, dept_name: str, dept_code: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            self.pages = json.load(f)
        self.dept_name = dept_name
        self.dept_code = dept_code
        self.abbreviations = {}
        self.subjects = {}          # code -> dict
        self.electives = {}          # code -> dict
        self.semester_courses = {}   # semester -> list of codes

    @staticmethod
    def roman_to_int(roman: str) -> int:
        """Convert Roman numeral (e.g., 'III') to integer."""
        roman = roman.upper()
        values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        total = 0
        for i in range(len(roman)):
            if i > 0 and values[roman[i]] > values[roman[i-1]]:
                total += values[roman[i]] - 2 * values[roman[i-1]]
            else:
                total += values[roman[i]]
        return total

    def parse_abbreviations(self):
        """Find abbreviation tables and store them."""
        for page in self.pages:
            text = page.get('text', '')
            if 'A. Abbreviations' in text or 'Abbreviations' in text:
                tables = page.get('tables', [])
                for table in tables:
                    if isinstance(table, list):
                        for row in table:
                            if isinstance(row, list) and len(row) >= 2:
                                code = row[0].strip() if isinstance(row[0], str) else ''
                                full = row[1].strip() if isinstance(row[1], str) else ''
                                if code and full and len(code) < 15:
                                    self.abbreviations[code] = full

    def parse_credit_structure(self):
        """Store credit structure raw data (can be extended later)."""
        for page in self.pages:
            text = page.get('text', '')
            if 'B. Credit Structure' in text:
                # We just note it; actual parsing can be done later if needed
                self.credit_structure_raw = text
                break

    def parse_curriculum_tables(self):
        """Extract courses from curriculum structure tables."""
        for page in self.pages:
            text = page.get('text', '')
            if 'Curriculum Structure' in text and 'Semester' in text:
                # Determine semester number
                sem_match = re.search(r'Semester[-\s]*([IVXLCDM]+|\d+)', text, re.IGNORECASE)
                if sem_match:
                    sem_str = sem_match.group(1)
                    semester = self.roman_to_int(sem_str) if sem_str.isalpha() else int(sem_str)
                else:
                    semester = 1

                tables = page.get('tables', [])
                for table in tables:
                    if isinstance(table, list) and len(table) > 1:
                        header_row = table[0]
                        if isinstance(header_row, list) and any('Course Code' in str(cell) for cell in header_row):
                            for row in table[1:]:
                                if isinstance(row, list) and len(row) >= 2:
                                    code = row[0].strip() if isinstance(row[0], str) else ''
                                    name = row[1].strip() if len(row) > 1 and isinstance(row[1], str) else ''
                                    if re.match(r'^[A-Z]{2,4}\d{3,4}$', code):
                                        # Determine credits (look for digits)
                                        credits = 0
                                        L = P = T = 0
                                        for cell in row[2:]:
                                            if isinstance(cell, str) and cell.isdigit():
                                                credits = int(cell)
                                                break
                                        # Store
                                        subject_type = self._infer_type(code)
                                        self.subjects[code] = {
                                            'code': code,
                                            'name': name,
                                            'credits': credits,
                                            'semester': semester,
                                            'type': subject_type,
                                            'teaching_scheme': {'L': L, 'P': P, 'T': T},
                                            'units': [],
                                            'learning_outcomes': [],
                                            'reference_books': [],
                                            'prerequisites': [],
                                            'examination_scheme': {}
                                        }
                                        self.semester_courses.setdefault(semester, []).append(code)

    def parse_elective_lists(self):
        """Extract Program Elective, Open Elective, Liberal Learning, MDM courses."""
        for page in self.pages:
            text = page.get('text', '')
            tables = page.get('tables', [])
            if 'Program Elective Course' in text:
                for table in tables:
                    if isinstance(table, list):
                        for row in table:
                            if isinstance(row, list) and len(row) >= 2:
                                code = row[0].strip() if isinstance(row[0], str) else ''
                                name = row[1].strip() if isinstance(row[1], str) else ''
                                if re.match(r'^[A-Z]{2,4}\d{3,4}$', code):
                                    self.electives[code] = {'code': code, 'name': name, 'type': 'PEC'}
            if 'Open Elective Course' in text:
                for table in tables:
                    if isinstance(table, list):
                        for row in table:
                            if isinstance(row, list) and len(row) >= 2:
                                code = row[0].strip() if isinstance(row[0], str) else ''
                                name = row[1].strip() if isinstance(row[1], str) else ''
                                if re.match(r'^[A-Z]{2,4}\d{3,4}$', code):
                                    self.electives[code] = {'code': code, 'name': name, 'type': 'OEC'}
            if 'Liberal Learning Course' in text:
                for table in tables:
                    if isinstance(table, list):
                        for row in table:
                            if isinstance(row, list) and len(row) >= 2:
                                code = row[0].strip() if isinstance(row[0], str) else ''
                                name = row[1].strip() if isinstance(row[1], str) else ''
                                if re.match(r'^[A-Z]{2,4}\d{3,4}$', code):
                                    self.electives[code] = {'code': code, 'name': name, 'type': 'LLC'}
            if 'Multidisciplinary Minor Courses' in text:
                for table in tables:
                    if isinstance(table, list):
                        for row in table:
                            if isinstance(row, list) and len(row) >= 2:
                                code = row[0].strip() if isinstance(row[0], str) else ''
                                name = row[1].strip() if isinstance(row[1], str) else ''
                                if re.match(r'^[A-Z]{2,4}\d{3,4}$', code):
                                    self.electives[code] = {'code': code, 'name': name, 'type': 'MDM'}

    def parse_detailed_syllabus(self):
        """Parse detailed module tables for subjects."""
        current_subject = None
        current_unit = None

        for page in self.pages:
            text = page.get('text', '')
            tables = page.get('tables', [])

            # Look for subject header (e.g., "PCC ITPCC301 ENGINEERING MATHEMATICS-III 03+01*")
            header_match = re.search(r'([A-Z]{2,4})\s+([A-Z]+\d{3,4})\s+([A-Z\s&]+?)\s+(\d+(?:\+\d+)?)', text)
            if header_match:
                code = header_match.group(2)
                # If we already have this subject from curriculum, update it; otherwise create new
                if code in self.subjects:
                    current_subject = self.subjects[code]
                else:
                    # Might be an elective not in curriculum table
                    current_subject = {
                        'code': code,
                        'name': header_match.group(3).strip(),
                        'credits': int(header_match.group(4).split('+')[0]),
                        'semester': 0,  # unknown
                        'type': self._infer_type(code),
                        'teaching_scheme': {},
                        'units': [],
                        'learning_outcomes': [],
                        'reference_books': [],
                        'prerequisites': [],
                        'examination_scheme': {}
                    }
                    self.subjects[code] = current_subject
                continue

            if not current_subject:
                continue

            # Parse examination scheme
            if 'Examination Scheme' in text and tables:
                for table in tables:
                    if isinstance(table, list):
                        for row in table:
                            if isinstance(row, list):
                                row_str = ' '.join(str(c) for c in row)
                                numbers = re.findall(r'\d+\.?\d*', row_str)
                                if len(numbers) >= 6:
                                    current_subject['examination_scheme'] = {
                                        'continuous_assessment': numbers[0],
                                        'mid_sem': numbers[1],
                                        'end_sem': numbers[2],
                                        'mse_duration': numbers[3],
                                        'ese_duration': numbers[4],
                                        'total_marks': numbers[5]
                                    }
                                    break

            # Parse module table
            if 'Module' in text and 'Details' in text and 'Hrs' in text and tables:
                module_table = tables[0]  # assume first table is module list
                if isinstance(module_table, list):
                    for row in module_table:
                        if isinstance(row, list) and len(row) >= 3:
                            module_num = str(row[0]).strip()
                            details = str(row[1]) if len(row) > 1 else ''
                            hrs = str(row[2]) if len(row) > 2 else ''

                            # If module_num looks like a number (e.g., "01."), it's a new unit
                            if re.match(r'^\d+\.?$', module_num):
                                unit_num = int(module_num.replace('.', ''))
                                # Extract title from details (first line)
                                title_lines = details.split('\n')
                                title = title_lines[0] if title_lines else ''
                                # Remove common prefixes
                                title = re.sub(r'Learning\s+Objective.*?:?', '', title, flags=re.IGNORECASE).strip()
                                current_unit = {
                                    'unit_number': unit_num,
                                    'title': title,
                                    'description': details,
                                    'lecture_hours': int(hrs) if hrs.isdigit() else None,
                                    'topics': []
                                }
                                current_subject['units'].append(current_unit)
                            elif current_unit:
                                # Continuation – extract bullet points as topics
                                bullets = re.findall(r'[•\-]\s*(.*?)(?=\n[•\-]|\Z)', details, re.DOTALL)
                                if bullets:
                                    for bullet in bullets:
                                        bullet = bullet.strip()
                                        if bullet and len(bullet) < 200 and not bullet.startswith('LO'):
                                            current_unit['topics'].append({
                                                'name': bullet,
                                                'key_points': [],
                                                'examples': []
                                            })
                                        elif 'LO' in bullet:
                                            # Might be learning outcome
                                            current_subject['learning_outcomes'].append(bullet)

            # Parse reference books
            if 'Text Books :' in text or 'Reference Books :' in text:
                books = re.findall(r'\d+\.\s*(.*?)(?=\n\d+\.|\Z)', text, re.DOTALL)
                current_subject['reference_books'].extend(books)

            # Parse prerequisites
            if 'Pre-requisite' in text:
                pre = re.findall(r'Pre-requisite:\s*(.*?)(?=\n)', text, re.DOTALL)
                if pre:
                    current_subject['prerequisites'].append(pre[0])

    def _infer_type(self, code: str) -> str:
        """Map course code prefix to subject type."""
        prefix_map = {
            'BSC': 'BSC', 'BSL': 'BSL', 'ESC': 'ESC', 'ESL': 'ESL',
            'PCC': 'PCC', 'LBC': 'LBC', 'PEC': 'PEC', 'OEC': 'OEC',
            'SEC': 'SEC', 'SBL': 'SBL', 'AEC': 'AEC', 'HSS': 'HSS',
            'IKS': 'IKS', 'VEC': 'VEC', 'ELC': 'ELC', 'MNP': 'MNP',
            'MJP': 'MJP', 'INT': 'INT', 'LLC': 'LLC', 'MDM': 'MDM',
            'MDL': 'MDL'
        }
        for prefix, typ in prefix_map.items():
            if code.startswith(prefix):
                return typ
        return 'PCC'

    async def save_to_db(self, dept_id: PydanticObjectId):
        """Insert all collected data into MongoDB."""
        # Insert abbreviations
        for code, full in self.abbreviations.items():
            if not await Abbreviation.find_one(Abbreviation.code == code):
                await Abbreviation(code=code, full_form=full).insert()

        # Insert subjects
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
                description=sub_data.get('description'),
                learning_outcomes=sub_data.get('learning_outcomes', []),
                reference_books=sub_data.get('reference_books', []),
                prerequisites=sub_data.get('prerequisites', []),
                examination_scheme=sub_data.get('examination_scheme', {})
            )
            await subject.insert()

            # Insert units and topics
            for unit_data in sub_data.get('units', []):
                unit = SubjectUnit(
                    subject=subject,
                    unit_number=unit_data['unit_number'],
                    title=unit_data.get('title', ''),
                    description=unit_data.get('description'),
                    lecture_hours=unit_data.get('lecture_hours')
                )
                await unit.insert()
                for topic_data in unit_data.get('topics', []):
                    topic = Topic(
                        unit=unit,
                        name=topic_data['name'],
                        key_points=topic_data.get('key_points', []),
                        examples=topic_data.get('examples', [])
                    )
                    await topic.insert()

        # Insert electives
        for code, elec_data in self.electives.items():
            typ = elec_data['type']
            if typ == 'PEC':
                if not await ProgramElective.find_one(ProgramElective.code == code):
                    await ProgramElective(
                        code=code,
                        name=elec_data['name'],
                        department=dept_id,
                        semester=6,  # default, can be refined
                        description=""
                    ).insert()
            elif typ == 'OEC':
                if not await OpenElective.find_one(OpenElective.code == code):
                    await OpenElective(
                        code=code,
                        name=elec_data['name'],
                        semester=7,
                        description=""
                    ).insert()
            elif typ == 'LLC':
                if not await LiberalLearningCourse.find_one(LiberalLearningCourse.code == code):
                    await LiberalLearningCourse(
                        code=code,
                        name=elec_data['name'],
                        description=""
                    ).insert()
            elif typ == 'MDM':
                if not await MDMCourse.find_one(MDMCourse.code == code):
                    await MDMCourse(
                        code=code,
                        name=elec_data['name'],
                        department=dept_id,
                        semester=3,
                        credits=3,
                        teaching_scheme={'L': 3, 'T': 0, 'P': 0}
                    ).insert()


async def main():
    await init_db()

    json_dir = backend_root / "json_data"
    files = [
        (json_dir / "B_TECH_CSE_Scheme.json", "Computer Science & Engineering", "CSE"),
        (json_dir / "FY_R25_IT.json", "Information Technology", "IT"),
        (json_dir / "SY_R2024.1_IT.json", "Information Technology", "IT"),
        (json_dir / "TY_R2024.1_IT.json", "Information Technology", "IT"),
    ]

    for file_path, dept_name, dept_code in files:
        if not file_path.exists():
            print(f"Warning: {file_path} not found, skipping.")
            continue
        print(f"Processing {file_path.name}...")
        parser = SyllabusParser(file_path, dept_name, dept_code)
        parser.parse_abbreviations()
        parser.parse_credit_structure()
        parser.parse_curriculum_tables()
        parser.parse_elective_lists()
        parser.parse_detailed_syllabus()

        # Get or create department
        dept = await Department.find_one(Department.code == dept_code)
        if not dept:
            dept = Department(code=dept_code, name=dept_name)
            await dept.insert()
            print(f"Created department: {dept_name}")

        await parser.save_to_db(dept.id)
        print(f"Finished {file_path.name}")

    print("All files processed.")


if __name__ == "__main__":
    asyncio.run(main())