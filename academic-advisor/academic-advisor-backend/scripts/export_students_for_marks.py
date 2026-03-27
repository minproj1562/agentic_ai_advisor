#academic-advisor/academic-advisor-backend/scripts/export_students_for_marks.py

"""
Export students to Excel using the SAME format as generate_marks_template.py
This ensures compatibility with the bulk upload parser.
"""

import argparse
import asyncio
import sys
import os
from datetime import datetime
import io
import json
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.student_profile import StudentProfile
from app.services.bulk_marks_service import bulk_marks_service
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

load_dotenv()

async def init_db():
    """Initialize database connection"""
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    db = client[os.getenv("DB_NAME", "academic_advisor")]
    await init_beanie(
        database=db,
        document_models=[StudentProfile]
    )

async def fetch_students(branch=None, admission_year=None):
    """Fetch students from database with filters"""
    query = {}
    
    if branch:
        query["branch"] = {"$regex": f"^{branch}$", "$options": "i"}
    if admission_year:
        query["admission_year"] = admission_year
    
    students = await StudentProfile.find(query).sort("roll_number").to_list()
    return students

async def create_marks_sheet_with_students(semester, branch, admission_year, students, output_file):
    """
    Create Excel using the EXACT template format from generate_marks_template
    then fill in student data
    """
    
    # Step 1: Generate the standard template using bulk_marks_service
    print("Generating template...")
    template_buffer = bulk_marks_service.generate_template(
        semester=semester,
        branch=branch,
        academic_year="2024-25",  # You can make this configurable
        admission_year=admission_year,
        elective_choices=None  # You can add elective handling later
    )
    
    # Step 2: Load the generated template
    wb = load_workbook(template_buffer)
    ws = wb["Marks Data"]  # Main sheet name from template
    
    # Step 3: Find where to insert student data
    # The template has this structure:
    # Row 1: Metadata
    # Row 2: Instructions
    # Row 3: Empty
    # Row 4: Subject headers
    # Row 5: Component headers (CA, MSE, ESE, etc.)
    # Row 6: Max marks
    # Row 7+: Student data starts here
    
    DATA_START_ROW = 7
    
    # Step 4: Read the hidden column map to understand the structure
    col_map_json = None
    try:
        marker = ws.cell(row=100, column=1).value
        if marker == "__COLUMN_MAP__":
            col_map_json = ws.cell(row=100, column=2).value
            col_map = json.loads(col_map_json)
    except:
        print("Warning: Could not find column map in template")
        col_map = []
    
    # Step 5: Fill in student data
    print(f"Adding {len(students)} students to template...")
    
    for idx, student in enumerate(students):
        row = DATA_START_ROW + idx
        
        # Sr. No (Column 1)
        ws.cell(row=row, column=1, value=idx + 1)
        ws.cell(row=row, column=1).alignment = Alignment(horizontal="center")
        
        # Seat No / Roll Number (Column 2)
        ws.cell(row=row, column=2, value=student.roll_number)
        ws.cell(row=row, column=2).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=2).font = Font(bold=True)
        
        # Name (Column 3)
        ws.cell(row=row, column=3, value=student.name)
        ws.cell(row=row, column=3).alignment = Alignment(horizontal="left")
        
        # Leave marks columns empty - they will be filled manually
        # The template already has borders and formatting for these cells
    
    # Step 6: Update the hidden metadata with student count
    try:
        meta_row = 101
        ws.cell(row=meta_row, column=1, value="__STUDENTS_META__")
        ws.cell(row=meta_row, column=2, value=json.dumps({
            "total_students": len(students),
            "branch": branch,
            "admission_year": admission_year,
            "prefilled": True,
            "generated_at": datetime.now().isoformat()
        }))
        ws.row_dimensions[meta_row].hidden = True
    except:
        pass
    
    # Step 7: Add a note in the Instructions sheet if it exists
    try:
        if "Subject Info" in wb.sheetnames:
            info_sheet = wb["Subject Info"]
            last_row = info_sheet.max_row + 2
            info_sheet.cell(row=last_row, column=1, value="Note:")
            info_sheet.cell(row=last_row, column=1).font = Font(bold=True)
            info_sheet.cell(row=last_row + 1, column=1, value=f"This template has been pre-filled with {len(students)} students from {branch} branch")
    except:
        pass
    
    # Save the file
    wb.save(output_file)
    print(f"✅ Excel file created: {output_file}")
    print(f"   - Students: {len(students)}")
    print(f"   - Format: University marks template (compatible with bulk upload)")
    print(f"   - Ready for marks entry!")

async def main():
    parser = argparse.ArgumentParser(
        description="Export students to marks template format"
    )
    parser.add_argument("-s", "--semester", type=int, required=True, help="Semester number (1-8)")
    parser.add_argument("-b", "--branch", required=True, help="Branch code (e.g., IT, COMP)")
    parser.add_argument("-a", "--admission", type=int, default=2022, help="Admission year")
    parser.add_argument("-o", "--output", help="Output filename")
    
    args = parser.parse_args()
    
    # Initialize database
    await init_db()
    
    # Fetch students
    print(f"Fetching students from branch {args.branch}...")
    students = await fetch_students(branch=args.branch, admission_year=args.admission)
    
    if not students:
        print("❌ No students found")
        return
    
    print(f"✅ Found {len(students)} students")
    
    # Generate output filename
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"marks_entry_sem{args.semester}_{args.branch}_{timestamp}.xlsx"
    
    # Create Excel file
    await create_marks_sheet_with_students(
        args.semester, 
        args.branch, 
        args.admission, 
        students, 
        output_file
    )
    
    print("\n📋 Next steps:")
    print("1. Open the Excel file")
    print("2. Fill in the marks for each student in the gray cells")
    print("3. Save the file")
    print("4. Upload through Admin Panel > Bulk Marks Upload")

if __name__ == "__main__":
    asyncio.run(main())