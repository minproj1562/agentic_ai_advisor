import asyncio
import json
import logging
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.database.connection import get_database

logger = logging.getLogger(__name__)

async def seed_departments(dry_run: bool = False, json_path: Path = None):
    db = await get_database()
    collection = db.departments

    if not json_path:
        json_path = Path(__file__).parent / "data" / "departments.json"

    with open(json_path, "r") as f:
        departments = json.load(f)

    logger.info(f"Loaded {len(departments)} departments from {json_path}")

    if dry_run:
        logger.info("Dry run - would insert departments")
        return

    for dept in departments:
        result = await collection.update_one(
            {"code": dept["code"]},
            {"$set": dept},
            upsert=True
        )
        if result.upserted_id:
            logger.info(f"Inserted new department: {dept['code']}")
        elif result.modified_count:
            logger.info(f"Updated department: {dept['code']}")

    # Create indexes
    await collection.create_index("code", unique=True)
    await collection.create_index("name")
    logger.info("Indexes created on departments collection")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json-path", type=str)
    args = parser.parse_args()
    asyncio.run(seed_departments(dry_run=args.dry_run, json_path=args.json_path))