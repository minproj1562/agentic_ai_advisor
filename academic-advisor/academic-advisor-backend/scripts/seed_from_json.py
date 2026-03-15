"""
Seed subject_units and update topic definitions from parsed_syllabi.json

Run: python -m scripts.seed_syllabus_units
"""

import asyncio
import json
import re
import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.environ.get("MONGODB_DATABASE", "academic_advisor")

# Map PDF filenames to semester ranges
PDF_SEMESTER_MAP = {
    "FY_R25_IT.pdf": [1, 2],
    "SY_R2024.1_IT.pdf": [3, 4],
    "TY_R2024.1_IT.pdf": [5, 6],
    "B_TECH_CSE_Scheme.pdf": [1, 2, 3, 4, 5, 6, 7, 8],
}


def parse_modules_from_pages(pages: list) -> list:
    """
    Parse module/unit info from page text.
    Extracts: module_number, title, contents, hours, learning_outcomes
    """
    modules = []
    all_text = "\n".join(p.get("text", "") for p in pages)

    # Pattern: "01." or "02." at line start, followed by title and hours
    # Matches: "01. Vector Space 07-09" or "02.\nLinear Mappings 06-08"
    module_pattern = re.compile(
        r'^(\d{2})\.\s*\n?(.*?)(?:\s+(\d{1,2}-\d{1,2}|\d{1,2})\s*$)',
        re.MULTILINE
    )

    matches = list(module_pattern.finditer(all_text))

    for i, match in enumerate(matches):
        mod_num = int(match.group(1))
        title = match.group(2).strip()
        hours = match.group(3) if match.group(3) else ""

        if mod_num == 0:  # Skip "00. Course Introduction"
            continue

        # Find content between this module and next
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(all_text)
        section = all_text[start:end]

        # Extract "Contents:" block
        contents_match = re.search(
            r'Contents:\s*\n(.*?)(?=\nSelf-Learning|Learning\s+Outcome|$)',
            section, re.DOTALL
        )
        contents_text = ""
        if contents_match:
            contents_text = contents_match.group(1).strip()

        # Parse individual topics from contents
        topics = []
        if contents_text:
            # Split by commas and newlines, clean up
            raw_topics = re.split(r'[,\n]', contents_text)
            for t in raw_topics:
                t = t.strip().rstrip('.')
                t = re.sub(r'\s+', ' ', t)
                if t and len(t) > 2 and not t.startswith('(') and not t.startswith('LO'):
                    topics.append(t)

        # Extract Learning Outcomes
        los = []
        lo_matches = re.finditer(r'LO\s+\d+\.\d+:\s*(.+?)(?=\n\s*LO|\n\s*$|$)', section)
        for lo in lo_matches:
            lo_text = lo.group(1).strip()
            lo_text = re.sub(r'\(P\.I\..*?\)', '', lo_text).strip()
            if lo_text:
                los.append(lo_text)

        if title:
            modules.append({
                "module_number": mod_num,
                "title": title,
                "hours": hours,
                "contents_raw": contents_text,
                "topics": topics[:20],  # Limit
                "learning_outcomes": los[:6],
            })

    return modules


def extract_course_info(pages: list) -> dict:
    """Extract course code and name from the first page of a course."""
    first_page_text = pages[0].get("text", "") if pages else ""
    tables = pages[0].get("tables", []) if pages else []

    code, name = "", ""

    # Try tables first
    for table in tables:
        for row in table:
            if len(row) >= 3:
                for cell in row:
                    if re.match(r'^[A-Z]{2,6}\d{3}', str(cell)):
                        code = str(cell).strip()
                    elif any(kw in str(cell).upper() for kw in
                             ["ENGINEERING", "COMPUTER", "DATA", "DATABASE",
                              "PROGRAMMING", "NETWORK", "OPERATING", "SOFTWARE",
                              "MATHEMATICS", "ALGORITHM", "DISCRETE"]):
                        candidate = str(cell).strip()
                        if len(candidate) > 5 and not candidate.startswith("LO"):
                            name = candidate

    # Fallback: regex on text
    if not code:
        code_match = re.search(r'([A-Z]{2,6}\d{3})', first_page_text)
        if code_match:
            code = code_match.group(1)

    if not name:
        name_match = re.search(
            r'(?:Course Name|ITPCC\d+|ITPCL\d+)\s+([A-Z][A-Z &\-]+)',
            first_page_text
        )
        if name_match:
            name = name_match.group(1).strip().title()

    return {"code": code, "name": name}


async def seed_from_parsed_json():
    """Main seed function."""
    json_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "json_data")
    json_path = os.path.join(json_dir, "parsed_syllabi.json")

    if not os.path.exists(json_path):
        logger.error(f"❌ File not found: {json_path}")
        logger.info("Looking in alternate locations...")
        alt_paths = [
            "json_data/parsed_syllabi.json",
            "academic-advisor-backend/json_data/parsed_syllabi.json",
            "../json_data/parsed_syllabi.json",
        ]
        for alt in alt_paths:
            if os.path.exists(alt):
                json_path = alt
                break
        else:
            logger.error("Cannot find parsed_syllabi.json")
            return

    logger.info(f"📖 Loading {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    units_col = db["subject_units"]
    topics_col = db["topics"]
    subjects_col = db["subjects"]

    total_units = 0
    total_topics_updated = 0

    for pdf_name, pages in data.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"📄 Processing: {pdf_name}")

        # Split pages into courses (each course starts with "Course Type")
        course_pages = []
        current_course = []

        for page in pages:
            text = page.get("text", "")
            if "Course Type" in text and "Course Code" in text and current_course:
                course_pages.append(current_course)
                current_course = [page]
            else:
                current_course.append(page)
        if current_course:
            course_pages.append(current_course)

        for course_group in course_pages:
            info = extract_course_info(course_group)
            code = info["code"]
            name = info["name"]

            if not code and not name:
                continue

            logger.info(f"\n  📚 Course: {code} - {name}")

            # Find matching subject in DB
            subject_doc = None
            if code:
                subject_doc = await subjects_col.find_one(
                    {"code": {"$regex": re.escape(code), "$options": "i"}}
                )
            if not subject_doc and name:
                subject_doc = await subjects_col.find_one(
                    {"name": {"$regex": re.escape(name[:20]), "$options": "i"}}
                )

            if subject_doc:
                logger.info(f"     ✅ Matched to DB subject: {subject_doc.get('name')} ({subject_doc.get('code')})")
                code = subject_doc.get("code", code)
                name = subject_doc.get("name", name)
            else:
                logger.info(f"     ⚠️ No DB match for {code}/{name}")

            # Parse modules
            modules = parse_modules_from_pages(course_group)
            logger.info(f"     Found {len(modules)} modules")

            for mod in modules:
                # Create/update subject_unit
                unit_doc = {
                    "subject_code": code,
                    "subject_name": name,
                    "unit_number": mod["module_number"],
                    "title": mod["title"],
                    "description": mod["contents_raw"][:500] if mod["contents_raw"] else "",
                    "topics": [{"name": t} for t in mod["topics"]],
                    "learning_outcomes": mod["learning_outcomes"],
                    "hours": mod["hours"],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }

                await units_col.update_one(
                    {"subject_code": code, "unit_number": mod["module_number"]},
                    {"$set": unit_doc},
                    upsert=True,
                )
                total_units += 1

                # Update existing topics with content
                for topic_name in mod["topics"]:
                    if not topic_name or len(topic_name) < 3:
                        continue

                    # Find matching topic in DB
                    existing = await topics_col.find_one({
                        "name": {"$regex": re.escape(topic_name[:30]), "$options": "i"},
                        "$or": [
                            {"subject_code": {"$regex": re.escape(code), "$options": "i"}} if code else {"_id": {"$exists": True}},
                            {"subject_name": {"$regex": re.escape(name[:15]), "$options": "i"}} if name else {"_id": {"$exists": True}},
                        ]
                    })

                    if existing:
                        # Update with unit context if definition is empty
                        update_fields = {
                            "unit_number": mod["module_number"],
                            "unit_title": mod["title"],
                            "updated_at": datetime.utcnow(),
                        }
                        if not (existing.get("definition") or "").strip():
                            update_fields["definition"] = (
                                f"{topic_name} is a concept covered in {name}, "
                                f"Unit {mod['module_number']}: {mod['title']}."
                            )
                        if not existing.get("key_points"):
                            # Generate key points from nearby topics
                            context_topics = [t for t in mod["topics"] if t != topic_name][:4]
                            if context_topics:
                                update_fields["key_points"] = [
                                    f"Part of {mod['title']} in {name}",
                                    f"Related concepts: {', '.join(context_topics[:3])}",
                                ]

                        await topics_col.update_one(
                            {"_id": existing["_id"]},
                            {"$set": update_fields}
                        )
                        total_topics_updated += 1

                logger.info(f"     Unit {mod['module_number']}: {mod['title']} ({len(mod['topics'])} topics)")

    # Also create topics for units that don't have matching topics yet
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 Summary:")
    logger.info(f"   Subject units created/updated: {total_units}")
    logger.info(f"   Topics updated: {total_topics_updated}")

    # Verify
    unit_count = await units_col.count_documents({})
    topic_count = await topics_col.count_documents({"definition": {"$ne": ""}})
    logger.info(f"   Total subject_units in DB: {unit_count}")
    logger.info(f"   Topics with definitions: {topic_count}")

    client.close()
    logger.info("\n✅ Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed_from_parsed_json())