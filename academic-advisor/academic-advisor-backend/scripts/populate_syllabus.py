#!/usr/bin/env python3
"""
Populate MongoDB with syllabus data from JSON files.
Usage from the backend root:
    python scripts/populate_syllabus.py [--reset]
Or from inside scripts/:
    cd scripts && python populate_syllabus.py [--reset]
"""

import asyncio
import json
import re
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add backend root to path so that we can import app.models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import motor.motor_asyncio
from beanie import init_beanie
from pymongo.errors import DuplicateKeyError

from app.models.syllabus import (
    Department, Subject, SubjectUnit, ProgramElective, OpenElective,
    MDMCourse, LiberalLearningCourse, Abbreviation, CreditStructure
)

# ----------------------------------------------------------------------
# Configuration – adjust paths if needed
# ----------------------------------------------------------------------
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "academic_advisor"

# JSON files are stored in ../json_data/ relative to this script
BASE_DIR = os.path.dirname(__file__)
JSON_FILES = [
    (os.path.join(BASE_DIR, "..", "json_data", "FY_R25_IT.json"), 1),   # (filename, starting semester)
    (os.path.join(BASE_DIR, "..", "json_data", "SY_R2024.1_IT.json"), 3),
    (os.path.join(BASE_DIR, "..", "json_data", "TY_R2024.1_IT.json"), 5),
]

IT_DEPT_CODE = "IT"
IT_DEPT_NAME = "Information Technology"

# ----------------------------------------------------------------------
# Helper functions for parsing tables and text (unchanged from previous version)
# ----------------------------------------------------------------------
def parse_course_header(table: List[List]) -> Optional[Dict[str, Any]]:
    """Extract course type, code, name, credits from a header table."""
    if not table or len(table) < 2:
        return None
    header_row = None
    for row in table:
        if any("Course Type" in str(cell) for cell in row):
            header_row = row
            break
    if not header_row:
        return None
    data_row = None
    for row in table:
        if row and row != header_row and any(str(cell).strip() for cell in row):
            data_row = row
            break
    if not data_row:
        return None
    col_map = {}
    for idx, cell in enumerate(header_row):
        cell_str = str(cell).strip()
        if "Course Type" in cell_str:
            col_map["type"] = idx
        elif "Course Code" in cell_str:
            col_map["code"] = idx
        elif "Course Name" in cell_str:
            col_map["name"] = idx
        elif "Credits" in cell_str:
            col_map["credits"] = idx
    if len(col_map) < 4:
        return None
    try:
        credits = int(str(data_row[col_map["credits"]]).strip())
    except ValueError:
        credits = 0
    return {
        "type": str(data_row[col_map["type"]]).strip(),
        "code": str(data_row[col_map["code"]]).strip(),
        "name": str(data_row[col_map["name"]]).strip(),
        "credits": credits,
    }

def parse_examination_scheme(table: List[List]) -> Dict[str, Any]:
    cleaned = []
    for row in table:
        if not row:
            continue
        cleaned_row = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
        if cleaned_row:
            cleaned.append(cleaned_row)
    return {"scheme": cleaned}

def parse_teaching_scheme(table: List[List]) -> Dict[str, int]:
    l = p = t = 0
    for row in table:
        row_str = [str(cell).strip() for cell in row if cell is not None]
        if "L" in row_str or "P" in row_str or "T" in row_str:
            continue
        digits = [cell for cell in row_str if cell.replace('+', '').replace('*', '').isdigit()]
        if len(digits) >= 3:
            l = int(digits[0].split('+')[0].split('*')[0])
            p = int(digits[1].split('+')[0].split('*')[0])
            t = int(digits[2].split('+')[0].split('*')[0]) if len(digits) > 2 else 0
    return {"L": l, "P": p, "T": t}

def extract_course_intro(text: str) -> str:
    pattern = r"Course Introduction.*?\n(.*?)(?=\n\d+\.|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""

def extract_modules(page_text: str) -> List[Dict[str, Any]]:
    modules = []
    pattern = r"(\d+)\.\s+(.*?)(?:\s+(\d+(?:-\d+)?))?\n(.*?)(?=\n\d+\.|\Z)"
    matches = re.findall(pattern, page_text, re.DOTALL)
    for num, title, hours, body in matches:
        lecture_hours = None
        if hours:
            lecture_hours = int(hours.split('-')[0])
        obj_match = re.search(r"Learning Objective:?\s*(.*?)(?=Contents:|$)", body, re.DOTALL)
        content_match = re.search(r"Contents:\s*(.*?)(?=Self-Learning Topics:|$)", body, re.DOTALL)
        slt_match = re.search(r"Self-Learning Topics:\s*(.*?)(?=Learning Outcomes:|$)", body, re.DOTALL)
        outcome_match = re.search(r"Learning Outcomes:\s*(.*?)(?=$)", body, re.DOTALL)

        modules.append({
            "number": int(num),
            "title": title.strip(),
            "hours": lecture_hours,
            "objective": obj_match.group(1).strip() if obj_match else "",
            "content": content_match.group(1).strip() if content_match else "",
            "slt": slt_match.group(1).strip() if slt_match else "",
            "outcomes": [line.strip() for line in outcome_match.group(1).split("\n") if line.strip()] if outcome_match else [],
        })
    return modules

def extract_course_details(pages: List[Dict], start_idx: int) -> tuple:
    prereq = []
    outcomes = []
    text_books = []
    ref_books = []
    i = start_idx
    while i < len(pages):
        text = pages[i].get("text", "")
        if "Pre-requisite:" in text:
            match = re.search(r"Pre-requisite:\s*(.*?)(?=\n\d+\.|\Z)", text, re.DOTALL)
            if match:
                prereq = [line.strip() for line in match.group(1).split("\n") if line.strip()]
        if "Course Outcomes:" in text:
            match = re.search(r"Course Outcomes:\s*(.*?)(?=\n\d+\.|\Z)", text, re.DOTALL)
            if match:
                outcomes = [line.strip() for line in match.group(1).split("\n") if line.strip()]
        if "Text Books :" in text:
            match = re.search(r"Text Books :\s*(.*?)(?=\n\d+\.|\Z)", text, re.DOTALL)
            if match:
                text_books = [line.strip() for line in match.group(1).split("\n") if line.strip()]
        if "Reference Books :" in text:
            match = re.search(r"Reference Books :\s*(.*?)(?=\n\d+\.|\Z)", text, re.DOTALL)
            if match:
                ref_books = [line.strip() for line in match.group(1).split("\n") if line.strip()]
        tables = pages[i].get("tables", [])
        for table in tables:
            if isinstance(table, list) and parse_course_header(table):
                return prereq, outcomes, text_books, ref_books
        i += 1
    return prereq, outcomes, text_books, ref_books

def extract_abbreviations(page: Dict) -> List[Dict[str, str]]:
    abbr_list = []
    for table in page.get("tables", []):
        if isinstance(table, list) and len(table) > 1:
            for row in table:
                if len(row) == 2 and row[0] and row[1]:
                    abbr_list.append({"code": str(row[0]).strip(), "full_form": str(row[1]).strip()})
    return abbr_list

def extract_credit_structure(page: Dict) -> Optional[Dict]:
    for table in page.get("tables", []):
        if isinstance(table, list) and len(table) > 5:
            if any("Semester-wise" in str(cell) for cell in table[0]):
                return {"structure": table}
    return None

def extract_mdm_courses(page: Dict) -> List[Dict]:
    courses = []
    for table in page.get("tables", []):
        if isinstance(table, list) and len(table) > 3:
            if any("Course Code" in str(cell) for cell in table[0]):
                for row in table[1:]:
                    if len(row) >= 2 and row[0] and row[1]:
                        courses.append({
                            "code": str(row[0]).strip(),
                            "name": str(row[1]).strip(),
                        })
    return courses

def extract_liberal_learning_courses(page: Dict) -> List[Dict]:
    courses = []
    for table in page.get("tables", []):
        if isinstance(table, list) and len(table) > 3:
            if any("Liberal Learning Courses" in str(cell) for cell in table[0]):
                for row in table[1:]:
                    if len(row) >= 2 and row[0] and row[1]:
                        courses.append({
                            "code": str(row[0]).strip(),
                            "name": str(row[1]).strip(),
                        })
    return courses

# ----------------------------------------------------------------------
# Database operations (unchanged)
# ----------------------------------------------------------------------
async def ensure_department() -> Department:
    dept = await Department.find_one(Department.code == IT_DEPT_CODE)
    if not dept:
        dept = Department(
            code=IT_DEPT_CODE,
            name=IT_DEPT_NAME,
            description="Department of Information Technology"
        )
        await dept.insert()
    return dept

async def upsert_subject(dept: Department, course_data: Dict, semester: int,
                         description: str = "", prerequisites: List[str] = None,
                         outcomes: List[str] = None, ref_books: List[str] = None,
                         teaching_scheme: Dict = None, exam_scheme: Dict = None) -> Subject:
    existing = await Subject.find_one(Subject.code == course_data["code"])
    if existing:
        existing.name = course_data["name"]
        existing.department = dept
        existing.semester = semester
        existing.credits = course_data["credits"]
        existing.subject_type = course_data["type"]
        existing.category = course_data["type"]
        if description:
            existing.description = description
        if prerequisites:
            existing.prerequisites = prerequisites
        if outcomes:
            existing.learning_outcomes = outcomes
        if ref_books:
            existing.reference_books = ref_books
        if teaching_scheme:
            existing.teaching_scheme = teaching_scheme
        if exam_scheme:
            existing.examination_scheme = exam_scheme
        existing.updated_at = datetime.utcnow()
        await existing.save()
        return existing
    else:
        subject = Subject(
            code=course_data["code"],
            name=course_data["name"],
            department=dept,
            semester=semester,
            credits=course_data["credits"],
            subject_type=course_data["type"],
            category=course_data["type"],
            teaching_scheme=teaching_scheme or {},
            examination_scheme=exam_scheme or {},
            description=description,
            prerequisites=prerequisites or [],
            learning_outcomes=outcomes or [],
            reference_books=ref_books or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await subject.insert()
        return subject

async def upsert_subject_units(subject: Subject, modules: List[Dict]):
    for mod in modules:
        existing = await SubjectUnit.find_one(
            SubjectUnit.subject.id == subject.id,
            SubjectUnit.unit_number == mod["number"]
        )
        if existing:
            existing.title = mod["title"]
            existing.description = mod["content"]
            existing.lecture_hours = mod["hours"]
            existing.learning_outcomes = mod["outcomes"]
            existing.updated_at = datetime.utcnow()
            await existing.save()
        else:
            unit = SubjectUnit(
                subject=subject,
                unit_number=mod["number"],
                title=mod["title"],
                description=mod["content"],
                lecture_hours=mod["hours"],
                learning_outcomes=mod["outcomes"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await unit.insert()

async def populate_abbreviations(pages: List[Dict]):
    for page in pages:
        for abbr in extract_abbreviations(page):
            try:
                await Abbreviation(
                    code=abbr["code"],
                    full_form=abbr["full_form"],
                    created_at=datetime.utcnow()
                ).insert()
            except DuplicateKeyError:
                pass

async def populate_credit_structure(pages: List[Dict]):
    for page in pages:
        struct = extract_credit_structure(page)
        if struct:
            await CreditStructure.delete_all()
            await CreditStructure(
                program="B.Tech Information Technology",
                total_credits=166,
                min_credits_per_semester=160,
                max_credits_per_semester=176,
                semester_wise_distribution={},
                category_wise_total={},
                created_at=datetime.utcnow()
            ).insert()
            break

async def populate_mdm_courses(pages: List[Dict], dept: Department):
    for page in pages:
        for c in extract_mdm_courses(page):
            try:
                await MDMCourse(
                    code=c["code"],
                    name=c["name"],
                    department=dept,
                    semester=0,
                    credits=3,
                    subject_type="core",
                    teaching_scheme={},
                    created_at=datetime.utcnow()
                ).insert()
            except DuplicateKeyError:
                pass

async def populate_liberal_learning_courses(pages: List[Dict]):
    for page in pages:
        for c in extract_liberal_learning_courses(page):
            try:
                await LiberalLearningCourse(
                    code=c["code"],
                    name=c["name"],
                    semester=6,
                    credits=2,
                    created_at=datetime.utcnow()
                ).insert()
            except DuplicateKeyError:
                pass

# ----------------------------------------------------------------------
# Main parsing logic for a single JSON file
# ----------------------------------------------------------------------
async def parse_file(filename: str, semester: int, dept: Department):
    print(f"Processing {filename} for semester {semester}...")
    with open(filename, 'r', encoding='utf-8') as f:
        pages = json.load(f)

    # First pass: collect abbreviations, credit structure, MDM, LLC
    await populate_abbreviations(pages)
    await populate_credit_structure(pages)
    await populate_mdm_courses(pages, dept)
    await populate_liberal_learning_courses(pages)

    # Second pass: courses
    i = 0
    while i < len(pages):
        page = pages[i]
        tables = page.get("tables", [])
        course_header = None
        exam_scheme = {}
        teach_scheme = {}
        for table in tables:
            if isinstance(table, list):
                header = parse_course_header(table)
                if header:
                    course_header = header
                if any("Examination Scheme" in str(cell) for cell in table):
                    exam_scheme = parse_examination_scheme(table)
                if any("Teaching Scheme" in str(cell) for cell in table):
                    teach_scheme = parse_teaching_scheme(table)
        if course_header:
            print(f"  Found course {course_header['code']} - {course_header['name']}")
            intro = extract_course_intro(page.get("text", ""))
            prereq, outcomes, text_books, ref_books = extract_course_details(pages, i)

            subject = await upsert_subject(
                dept, course_header, semester,
                description=intro,
                prerequisites=prereq,
                outcomes=outcomes,
                ref_books=text_books + ref_books,
                teaching_scheme=teach_scheme,
                exam_scheme=exam_scheme
            )

            # Collect modules from subsequent pages until next course header
            modules = []
            j = i + 1
            while j < len(pages):
                next_page = pages[j]
                next_header = False
                for t in next_page.get("tables", []):
                    if isinstance(t, list) and parse_course_header(t):
                        next_header = True
                        break
                if next_header:
                    break
                mods = extract_modules(next_page.get("text", ""))
                modules.extend(mods)
                j += 1

            if modules:
                await upsert_subject_units(subject, modules)

            i = j
        else:
            i += 1

# ----------------------------------------------------------------------
# Reset collections
# ----------------------------------------------------------------------
async def reset_collections():
    await Department.delete_all()
    await Subject.delete_all()
    await SubjectUnit.delete_all()
    await ProgramElective.delete_all()
    await OpenElective.delete_all()
    await MDMCourse.delete_all()
    await LiberalLearningCourse.delete_all()
    await Abbreviation.delete_all()
    await CreditStructure.delete_all()
    print("All collections cleared.")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
async def main(reset: bool = False):
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    await init_beanie(
        client[DB_NAME],
        document_models=[
            Department, Subject, SubjectUnit, ProgramElective,
            OpenElective, MDMCourse, LiberalLearningCourse,
            Abbreviation, CreditStructure
        ]
    )

    if reset:
        await reset_collections()

    dept = await ensure_department()

    for fname, sem in JSON_FILES:
        if not os.path.exists(fname):
            print(f"Warning: File {fname} does not exist. Skipping.")
            continue
        await parse_file(fname, sem, dept)

    print("Done.")

if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    asyncio.run(main(reset=reset_flag))