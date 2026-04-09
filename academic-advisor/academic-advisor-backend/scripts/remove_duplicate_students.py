# scripts/remove_duplicate_student.py
"""
Remove duplicate student records, keeping only Emily Rodrigues for roll number 5024052
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def remove_duplicate_students():
    """Remove duplicate students with roll number 5024052, keep only Emily Rodrigues"""
    
    # Connect to database
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    try:
        # Find all students with roll number 5024052
        roll_number = "5024052"
        students = []
        
        async for student in db.student_profiles.find({"roll_number": roll_number}):
            students.append(student)
        
        logger.info(f"Found {len(students)} students with roll number {roll_number}")
        
        if len(students) == 0:
            logger.info("No students found with this roll number")
            return
        
        if len(students) == 1:
            logger.info("Only one student found, no duplicates to remove")
            logger.info(f"Student: {students[0].get('name')}")
            return
        
        # Display all students found
        logger.info("Students found:")
        emily_student = None
        students_to_delete = []
        
        for i, student in enumerate(students):
            name = student.get('name', 'Unknown')
            student_id = str(student.get('_id'))
            email = student.get('email', 'No email')
            
            logger.info(f"  {i+1}. Name: {name}")
            logger.info(f"     ID: {student_id}")
            logger.info(f"     Email: {email}")
            logger.info(f"     Created: {student.get('created_at', 'Unknown')}")
            logger.info("")
            
            # Check if this is Emily Rodrigues (case-insensitive)
            if 'emily' in name.lower() and 'rodrigues' in name.lower():
                emily_student = student
                logger.info(f"  ✅ This is Emily Rodrigues - KEEPING this record")
            else:
                students_to_delete.append(student)
                logger.info(f"  ❌ This is NOT Emily Rodrigues - WILL DELETE")
            
            logger.info("-" * 50)
        
        # Confirm Emily was found
        if not emily_student:
            logger.error("❌ Emily Rodrigues not found! Please check the name manually.")
            logger.info("Available names:")
            for student in students:
                logger.info(f"  - {student.get('name')}")
            return
        
        # Confirm deletion
        if not students_to_delete:
            logger.info("✅ No duplicates to delete")
            return
        
        logger.info(f"📋 SUMMARY:")
        logger.info(f"  KEEPING: {emily_student.get('name')} (ID: {emily_student.get('_id')})")
        logger.info(f"  DELETING: {len(students_to_delete)} duplicate record(s)")
        
        # Ask for confirmation
        confirm = input("\n❓ Do you want to proceed with deletion? (type 'YES' to confirm): ")
        
        if confirm != "YES":
            logger.info("❌ Operation cancelled")
            return
        
        # Delete duplicates
        deletion_results = []
        for student in students_to_delete:
            try:
                result = await db.student_profiles.delete_one({"_id": student["_id"]})
                if result.deleted_count == 1:
                    logger.info(f"✅ Deleted: {student.get('name')} (ID: {student.get('_id')})")
                    deletion_results.append(True)
                else:
                    logger.error(f"❌ Failed to delete: {student.get('name')}")
                    deletion_results.append(False)
            except Exception as e:
                logger.error(f"❌ Error deleting {student.get('name')}: {e}")
                deletion_results.append(False)
        
        # Summary
        successful_deletions = sum(deletion_results)
        logger.info(f"\n📊 CLEANUP COMPLETE:")
        logger.info(f"  ✅ Successfully deleted: {successful_deletions} records")
        logger.info(f"  ❌ Failed deletions: {len(deletion_results) - successful_deletions}")
        logger.info(f"  🎯 Kept Emily Rodrigues: {emily_student.get('name')}")
        
        # Verify final state
        remaining_students = []
        async for student in db.student_profiles.find({"roll_number": roll_number}):
            remaining_students.append(student)
        
        logger.info(f"\n🔍 VERIFICATION:")
        logger.info(f"  Students remaining with roll {roll_number}: {len(remaining_students)}")
        if len(remaining_students) == 1:
            logger.info(f"  ✅ Only Emily Rodrigues remains: {remaining_students[0].get('name')}")
        else:
            logger.warning(f"  ⚠️ Expected 1 student, found {len(remaining_students)}")
    
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        raise
    
    finally:
        client.close()


async def create_unique_index():
    """Create a unique index on roll_number to prevent future duplicates"""
    
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    try:
        # Create unique index on roll_number
        await db.student_profiles.create_index("roll_number", unique=True, sparse=True)
        logger.info("✅ Created unique index on roll_number to prevent future duplicates")
        
    except Exception as e:
        if "duplicate key" in str(e).lower():
            logger.error("❌ Cannot create unique index - there are still duplicate roll numbers in the database")
        else:
            logger.error(f"❌ Error creating unique index: {e}")
    
    finally:
        client.close()


async def main():
    """Main function"""
    logger.info("🧹 Student Duplicate Cleanup Tool")
    logger.info("=" * 50)
    
    # Step 1: Remove duplicates
    await remove_duplicate_students()
    
    # Step 2: Create unique index to prevent future duplicates
    logger.info("\n🔒 Creating unique index to prevent future duplicates...")
    await create_unique_index()
    
    logger.info("\n✅ Cleanup complete!")


if __name__ == "__main__":
    asyncio.run(main())