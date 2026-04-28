# scripts/generate_student_roster_xlsx.py
"""
Generate Student Roster XLSX from IT_COPY.xlsx
==============================================
Reads student names from 'IT - Copy.xlsx' (any semester sheet),
assigns roll numbers 5023101–5023174 (skipping 5023147 & 5023159),
and produces a clean roster file for admin portal upload.

Output columns:
  - Name
  - Roll Number
  - Email  (auto-generated: firstname.lastname@fcrit.ac.in)
  - Branch (IT)
  - Admission Year (2023)

Usage:
    python -m scripts.generate_student_roster_xlsx
"""

import os
import sys
import pandas as pd
import re

# ── Configuration ─────────────────────────────────────────────────
EXCEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "exported_marks",
    "IT - Copy.xlsx",
)
OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "exported_marks",
)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "IT_Student_Roster.xlsx")

BRANCH = "IT"
ADMISSION_YEAR = 2023

# Roll numbers: 5023101 → 5023174, skip 5023147 & 5023159
ROLL_START = 5023101
ROLL_END   = 5023174
SKIP_ROLLS = {5023147, 5023159}


def _generate_roll_numbers():
    """Generate the valid roll number list."""
    rolls = []
    for r in range(ROLL_START, ROLL_END + 1):
        if r not in SKIP_ROLLS:
            rolls.append(str(r))
    return rolls


def _extract_student_names(excel_path: str) -> list[str]:
    """
    Extract unique student names from IT_COPY.xlsx.
    Uses the Sem-V sheet first, then Sem-IV, then Sem-III as fallback.
    
    The Excel structure has:
      - Row with "Sr. No" / "Seat No" / "Name of Student" headers
      - Then sub-headers (CIA, MSE, ESE, etc.)
      - Then "Max Marks" / "Min Marks" rows  
      - Then student data rows where col[3] == "MarksO"
    """
    sheet_names = pd.ExcelFile(excel_path).sheet_names
    print(f"  Available sheets: {sheet_names}")
    
    # Try sheets in order of preference
    preferred_order = [
        "IT-V-SH 2025",
        "IT SEM-IV FH-2025",
        "IT SEM-III SH-2024",
    ]
    
    target_sheet = None
    for name in preferred_order:
        if name in sheet_names:
            target_sheet = name
            break
    
    if not target_sheet:
        target_sheet = sheet_names[0]
    
    print(f"  Reading names from sheet: '{target_sheet}'")
    
    # Read with no header — the Excel has merged cells at top
    df = pd.read_excel(excel_path, sheet_name=target_sheet, header=None)
    
    # Find the header row containing "Sr. No" / "Seat No" / "Name of Student"
    header_row_idx = None
    for idx, row in df.iterrows():
        vals = [str(v).strip() for v in row.values if pd.notna(v)]
        if "Sr. No" in vals and "Name of Student" in vals:
            header_row_idx = idx
            break
    
    if header_row_idx is None:
        raise ValueError("Could not find header row with 'Sr. No' and 'Name of Student'")
    
    print(f"  Header row found at index: {header_row_idx}")
    
    # Column indices (0-based):
    # Col 0 = Sr. No, Col 1 = Seat No, Col 2 = Name of Student, Col 3 = Subject/type
    sr_col   = 0
    name_col = 2
    type_col = 3  # This column has "MarksO", "Grade", "GP", "C", "C*GP"
    
    # Extract student names: rows where col[3] == "MarksO" and col[0] is a valid Sr. No
    names = []
    seen = set()
    
    for idx in range(header_row_idx + 1, len(df)):
        row = df.iloc[idx]
        sr_val   = row.iloc[sr_col]
        name_val = row.iloc[name_col]
        type_val = str(row.iloc[type_col]).strip() if pd.notna(row.iloc[type_col]) else ""
        
        # Skip header/sub-header rows and non-data rows
        if type_val != "MarksO":
            continue
        
        # Validate Sr. No is numeric
        try:
            sr_num = int(float(sr_val))
        except (ValueError, TypeError):
            continue
        
        if pd.isna(name_val) or not str(name_val).strip():
            continue
        
        name = str(name_val).strip()
        
        # Normalize: title case
        name = name.title()
        
        if name not in seen:
            seen.add(name)
            names.append(name)
    
    return names


def _generate_email(name: str) -> str:
    """Generate college email from student name."""
    parts = name.strip().split()
    if len(parts) >= 2:
        first = re.sub(r'[^a-z]', '', parts[0].lower())
        last  = re.sub(r'[^a-z]', '', parts[-1].lower())
        return f"{first}.{last}@fcrit.ac.in"
    else:
        clean = re.sub(r'[^a-z]', '', name.lower())
        return f"{clean}@fcrit.ac.in"


def main():
    print("=" * 70)
    print("  GENERATE STUDENT ROSTER XLSX")
    print("=" * 70)
    
    if not os.path.exists(EXCEL_PATH):
        print(f"\n  ❌ Excel file not found: {EXCEL_PATH}")
        sys.exit(1)
    
    # Step 1: Extract names
    print(f"\n  📄 Reading from: {EXCEL_PATH}")
    names = _extract_student_names(EXCEL_PATH)
    print(f"  ✅ Found {len(names)} unique students")
    
    # Step 2: Generate roll numbers
    rolls = _generate_roll_numbers()
    print(f"  🔢 Generated {len(rolls)} roll numbers ({rolls[0]} → {rolls[-1]})")
    
    # Validate counts match
    if len(names) > len(rolls):
        print(f"\n  ⚠️  Warning: More students ({len(names)}) than roll numbers ({len(rolls)})")
        print(f"      Only the first {len(rolls)} students will be assigned roll numbers.")
        names = names[:len(rolls)]
    elif len(names) < len(rolls):
        print(f"\n  ⚠️  Warning: Fewer students ({len(names)}) than roll numbers ({len(rolls)})")
        rolls = rolls[:len(names)]
    
    # Step 3: Build roster DataFrame
    roster_data = []
    for i, (name, roll) in enumerate(zip(names, rolls)):
        roster_data.append({
            "Name":           name,
            "Roll Number":    roll,
            "Email":          _generate_email(name),
            "Branch":         BRANCH,
            "Admission Year": ADMISSION_YEAR,
            "Current Semester": 5,  # They are currently in sem 5
        })
    
    df_roster = pd.DataFrame(roster_data)
    
    # Step 4: Write to Excel
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df_roster.to_excel(writer, index=False, sheet_name="Students")
        
        # Add instructions sheet
        instructions = pd.DataFrame({
            "Field": ["Name", "Roll Number", "Email", "Branch", "Admission Year", "Current Semester"],
            "Description": [
                "Full name of the student (from university records)",
                "7-digit roll number (5023101–5023174, skipping 5023147 & 5023159)",
                "Auto-generated FCRIT email (firstname.lastname@fcrit.ac.in)",
                "Department code (IT)",
                "Year of admission (2023)",
                "Current semester (5)",
            ]
        })
        instructions.to_excel(writer, index=False, sheet_name="Instructions")
    
    print(f"\n  📦 Roster saved to: {OUTPUT_FILE}")
    print(f"  📊 Total students: {len(df_roster)}")
    print(f"\n  Preview (first 10):")
    print(df_roster.head(10).to_string(index=False))
    
    print(f"\n  ✅ Done! Upload this file via the Admin Portal → Student Management → Bulk Upload")


if __name__ == "__main__":
    main()
