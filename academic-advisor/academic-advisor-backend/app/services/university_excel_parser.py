# academic-advisor-backend/app/services/university_excel_parser.py
"""
University Marksheet Parser — Mumbai University Format
======================================================
Handles the specific multi-row-per-student Excel format used by
Fr. C. Rodrigues Institute of Technology (and similar MU-affiliated colleges).

Sheet structure:
  Row 0: Institute name
  Row 1: Department name  
  Row 2: Examination title
  Row 3: Subject headers (merged cells: e.g. "ITPCC509: Automata Theory")
  Row 4: Component headers (CIA, MSE, ESE, TOT  OR  CIA, ESE, TOT for labs)
  Row 5: Max marks row
  Row 6: Min marks row (often empty)
  Row 7+: Student data — 5 rows per student:
            MarksO  → raw marks obtained
            Grade   → letter grade (AA, AB, BB, ...)
            GP      → grade points
            C       → credits
            C*GP    → credits × grade points
  Last rows: footer (legend, signatures) — identified by Unnamed: 3 == NaN

Student identification columns:
  Col 0: Sr. No
  Col 1: Seat No  ← used as roll number identifier
  Col 2: Name of Student

Subject column identification:
  Unnamed: 3 = row type indicator ('Subject Name', 'Max Marks', 'Min Marks',
               'MarksO', 'Grade', 'GP', 'C', 'C*GP')
  Subject columns start at index 4+, grouped by subject.

Special mark values:
  ABS        → absent (treat as 0)
  <num>F     → failed (e.g. "23F" → 23, flagged fail)
  <num>+<n>  → grace marks (e.g. "37+3" → 40)
  ©<num>     → re-exam (e.g. "©2" → 2)
  !<num>     → re-exam type 2
  ~<num>     → re-exam type 3
  @<num>     → re-exam type 4
"""

import re
import io
import logging
from dataclasses import dataclass, field as dc_field
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def extract_semester_from_sheet_name(sheet_name: str) -> int | None:
    """
    Extract semester number from a sheet name.
    Examples:
        "IT-V-SH 2025"      → 5
        "IT SEM-IV FH-2025" → 4
        "IT SEM-III SH-2024" → 3
        "Semester 5"        → 5
        "S6"                → 6
    """
    s = sheet_name.strip().upper()

    # IMPORTANT: Check longest Roman numerals first to prevent
    # 'I' from matching inside 'III', 'IV', 'VI', 'VII', 'VIII' etc.
    roman_pairs = [
        ('VIII', 8), ('VII', 7), ('VI', 6), ('IV', 4),
        ('V', 5), ('III', 3), ('II', 2), ('I', 1),
    ]
    for roman, num in roman_pairs:
        # Use word-boundary-aware patterns:
        #   -ROMAN-  (e.g. "IT-V-SH")
        #   SEM-ROMAN followed by non-roman-letter (e.g. "SEM-III SH", "SEM-IV ")
        #   space ROMAN space (e.g. "IT III FH")
        if f"-{roman}-" in s:
            return num
        # For SEM- prefix, ensure the roman numeral is not a prefix of a longer one
        sem_pattern = re.compile(r'SEM-' + roman + r'(?![A-Z])')
        if sem_pattern.search(s):
            return num
        # Space-padded: ensure not part of a longer roman numeral
        space_pattern = re.compile(r'(?:^|\s)' + roman + r'(?:\s|$)')
        if space_pattern.search(s):
            return num

    match = re.search(r'SEM(?:ESTER)?\s*(\d)', s)
    if match:
        return int(match.group(1))
    match = re.search(r'S(\d)', s)
    if match:
        return int(match.group(1))
    match = re.search(r'\b(\d)\b', s)
    if match:
        return int(match.group(1))
    return None

# ══════════════════════════════════════════════════════════════
# GRADE TABLES (Mumbai University autonomous scheme)
# ══════════════════════════════════════════════════════════════

# MU autonomous grading (AA=10, AB=9, BB=8, BC=7, CC=6, CD=5, PP=4, FF=0, LL=0)
MU_GRADE_TO_GP: Dict[str, float] = {
    "AA": 10.0, "AB": 9.0, "BB": 8.0, "BC": 7.0,
    "CC": 6.0,  "CD": 5.0, "PP": 4.0, "FF": 0.0,
    "LL": 0.0,  "F": 0.0,
}

MU_GP_TO_GRADE: Dict[float, str] = {v: k for k, v in MU_GRADE_TO_GP.items()}

# Percentage → MU grade mapping
def pct_to_mu_grade(pct: float) -> Tuple[str, float]:
    """Convert percentage to MU autonomous grade and grade point."""
    if pct >= 85:  return "AA", 10.0
    if pct >= 80:  return "AB",  9.0
    if pct >= 75:  return "BB",  8.0
    if pct >= 65:  return "BC",  7.0
    if pct >= 55:  return "CC",  6.0
    if pct >= 45:  return "CD",  5.0
    if pct >= 40:  return "PP",  4.0
    return "FF", 0.0


# ══════════════════════════════════════════════════════════════
# MARK VALUE PARSER
# ══════════════════════════════════════════════════════════════

# Regex for special mark notations
_RE_GRACE   = re.compile(r'^(\d+(?:\.\d+)?)\s*\+\s*(\d+(?:\.\d+)?)$')
_RE_FAIL    = re.compile(r'^(\d+(?:\.\d+)?)F$', re.IGNORECASE)
_RE_SPECIAL = re.compile(r'^[©!~@#]\s*(\d+(?:\.\d+)?)$')
_RE_NUMERIC = re.compile(r'^(\d+(?:\.\d+)?)$')


@dataclass
class ParsedMark:
    value: float = 0.0
    is_absent: bool = False
    is_fail: bool = False        # F suffix
    has_grace: bool = False
    grace_amount: float = 0.0
    is_reexam: bool = False
    raw: str = ""


def parse_mark_value(cell_value: Any) -> ParsedMark:
    """
    Parse a single mark cell that may contain special notations.

    Returns a ParsedMark with numeric value extracted.
    """
    pm = ParsedMark(raw=str(cell_value) if cell_value is not None else "")

    if cell_value is None or (isinstance(cell_value, float) and np.isnan(cell_value)):
        return pm

    s = str(cell_value).strip()

    # Absent
    if s.upper() in ("ABS", "AB", "ABSENT", "-", ""):
        pm.is_absent = True
        return pm

    # Pure numeric (most common)
    m = _RE_NUMERIC.match(s)
    if m:
        pm.value = float(m.group(1))
        return pm

    # Grace marks: "37+3"
    m = _RE_GRACE.match(s)
    if m:
        base = float(m.group(1))
        grace = float(m.group(2))
        pm.value = base + grace
        pm.has_grace = True
        pm.grace_amount = grace
        return pm

    # Fail mark: "23F"
    m = _RE_FAIL.match(s)
    if m:
        pm.value = float(m.group(1))
        pm.is_fail = True
        return pm

    # Re-exam special: ©2, !0.04, ~0.1, @7, #3
    m = _RE_SPECIAL.match(s)
    if m:
        pm.value = float(m.group(1))
        pm.is_reexam = True
        return pm

    # Try extracting any leading number as fallback
    leading = re.match(r'^(\d+(?:\.\d+)?)', s)
    if leading:
        pm.value = float(leading.group(1))
        pm.is_reexam = True   # assume special if unrecognised suffix
        return pm

    # Could not parse — treat as 0 / absent
    pm.is_absent = True
    logger.debug(f"Unparseable mark value: '{s}'")
    return pm


# ══════════════════════════════════════════════════════════════
# SUBJECT BLOCK DEFINITION
# ══════════════════════════════════════════════════════════════

@dataclass
class SubjectBlock:
    """Represents one subject's column group in the sheet."""
    raw_header: str               # e.g. "ITPCC509: Automata Theory"
    extracted_code: str           # e.g. "ITPCC509"
    extracted_name: str           # e.g. "Automata Theory"
    component_cols: Dict[str, int] = dc_field(default_factory=dict)
    # component name → 0-based column index
    # component names: CIA, CIA(T), MSE, ESE, TOT
    # for labs: CIA, ESE, TOT
    # for projects: CIA, TOT
    max_marks: Dict[str, float] = dc_field(default_factory=dict)
    total_col: Optional[int] = None
    credits: int = 0              # filled from C row


# Regex to extract subject code and name from header
_RE_SUBJ_HEADER = re.compile(
    r'^([A-Z][A-Z0-9_\-]{2,})\s*:\s*(.+)$',
    re.IGNORECASE,
)

def _parse_subject_header(text: str) -> Tuple[str, str]:
    """
    Parse 'ITPCC509: Automata Theory' → ('ITPCC509', 'Automata Theory').
    Also handles 'TPCC510: Artificial Intelligence' (missing I prefix).
    """
    text = str(text).strip()
    m = _RE_SUBJ_HEADER.match(text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    # Fallback: return whole text as name, empty code
    return "", text


# ══════════════════════════════════════════════════════════════
# PARSED STUDENT RESULT
# ══════════════════════════════════════════════════════════════

@dataclass
class UniversityStudentResult:
    seat_number: str
    student_name: str
    serial_number: Optional[int] = None
    subjects: List[Dict[str, Any]] = dc_field(default_factory=list)
    """
    Each subject dict:
      subject_code, subject_name,
      components: {CIA: float, MSE: float, ESE: float, TOT: float},
      credits: int,
      grade: str,  grade_points: float,
      total_marks: float, max_marks: float,
      is_practical: bool
    """
    total_semester_marks: Optional[float] = None
    sgpa: Optional[float] = None
    earned_credits: Optional[int] = None
    remark: Optional[str] = None          # Pass / Fail / RE codes
    parse_warnings: List[str] = dc_field(default_factory=list)


# ══════════════════════════════════════════════════════════════
# SHEET PARSER
# ══════════════════════════════════════════════════════════════

# Row type identifiers (in Unnamed: 3 column)
_ROW_TYPES = {
    "MarksO":       "marks",
    "Grade":        "grade",
    "GP":           "gp",
    "C":            "credits",
    "C*GP":         "cgp",
    "Subject Name": "header",
    "Max Marks":    "max",
    "Min Marks":    "min",
}

# Summary column header keywords
_SUMMARY_KEYWORDS = {
    "total marks",
    "total c*gp",
    "earned credits",
    "sgpi",
    "sgpa",
    "prev c*gp",
    "earned credits of sem",
    "cgpi",
    "cgpa",
    "remark",
}


def _is_summary_header(text: str) -> bool:
    t = str(text).strip().lower()
    return any(kw in t for kw in _SUMMARY_KEYWORDS)


class UniversitySheetParser:
    """
    Parses ONE sheet from a Mumbai University marksheet Excel file.
    """

    def __init__(self, df: pd.DataFrame, sheet_name: str = ""):
        self.df = df
        self.sheet_name = sheet_name
        self._results: List[UniversityStudentResult] = []
        self._subject_blocks: List[SubjectBlock] = []
        self._meta: Dict[str, Any] = {}

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def parse(self) -> Tuple[List[UniversityStudentResult], Dict[str, Any]]:
        """
        Main entry point. Returns (results, meta).
        """
        self._detect_structure()
        if not self._subject_blocks:
            logger.warning(
                f"[{self.sheet_name}] No subject blocks detected"
            )
            return [], self._meta

        self._parse_student_rows()
        self._meta["sheet_name"] = self.sheet_name
        self._meta["subject_count"] = len(self._subject_blocks)
        self._meta["student_count"] = len(self._results)
        return self._results, self._meta

    # ─────────────────────────────────────────────
    # Structure detection
    # ─────────────────────────────────────────────

    def _detect_structure(self):
        """
        Locate:
          - subject_header_row  (where Unnamed: 3 == 'Subject Name')
          - component_row       (where Unnamed: 3 == 'Max Marks')
          - data_start_row      (first row where Unnamed: 3 == 'MarksO')
          - summary_start_col   (first column that is a summary column)

        Builds self._subject_blocks.
        """
        df = self.df
        n_rows, n_cols = df.shape

        # The row-type indicator is always in column index 3 (Unnamed: 3)
        row_type_col = 3

        # ── Find key rows ──
        subject_header_row = None
        max_marks_row = None
        first_marks_row = None

        for i in range(min(n_rows, 20)):
            cell = str(df.iloc[i, row_type_col]).strip() if not pd.isna(df.iloc[i, row_type_col]) else ""
            if cell == "Subject Name":
                subject_header_row = i
            elif cell == "Max Marks" and subject_header_row is not None:
                max_marks_row = i
            elif cell == "MarksO" and max_marks_row is not None:
                first_marks_row = i
                break

        if subject_header_row is None or max_marks_row is None or first_marks_row is None:
            logger.warning(
                f"[{self.sheet_name}] Could not locate structure rows: "
                f"header={subject_header_row}, max={max_marks_row}, data={first_marks_row}"
            )
            return

        self._meta.update({
            "subject_header_row": subject_header_row,
            "max_marks_row": max_marks_row,
            "first_marks_row": first_marks_row,
        })

        # ── Find examination title (row 1 or 2) ──
        for r in range(min(3, n_rows)):
            cell = df.iloc[r, 0]
            if pd.notna(cell) and str(cell).strip():
                title = str(cell).strip()
                if "examination" in title.lower() or "semester" in title.lower():
                    self._meta["examination_title"] = title
                    break

        # ── Component row (row between subject header and max marks) ──
        # It's the row immediately after subject_header_row
        component_row = subject_header_row + 1
        self._meta["component_row"] = component_row

        # ── Build subject blocks ──
        # Columns 4+ are subject/summary columns
        # We read the subject header row to find merged spans
        # Since pandas reads merged cells with value only in the first cell
        # and NaN in the rest, we track spans by looking at non-NaN values.

        # Fixed columns: 0=Sr.No, 1=Seat No, 2=Name, 3=row-type
        FIXED_COLS = 4   # subject columns start here

        # Summary columns: find them by header text
        summary_start_col = n_cols  # default: no summary cols

        # Read subject names from subject_header_row
        subject_col_starts: List[Tuple[int, str]] = []  # (col_idx, header_text)

        col = FIXED_COLS
        while col < n_cols:
            cell = df.iloc[subject_header_row, col]
            if pd.isna(cell):
                col += 1
                continue

            header_text = str(cell).strip()

            # Check if this is a summary column
            if _is_summary_header(header_text):
                summary_start_col = col
                break

            subject_col_starts.append((col, header_text))
            col += 1

        self._meta["summary_start_col"] = summary_start_col

        # ── For each subject block, find its component columns ──
        for idx, (start_col, header_text) in enumerate(subject_col_starts):
            code, name = _parse_subject_header(header_text)

            # Determine end of this subject's columns
            # = start of next subject OR summary start
            if idx + 1 < len(subject_col_starts):
                end_col = subject_col_starts[idx + 1][0]
            else:
                end_col = summary_start_col

            block = SubjectBlock(
                raw_header=header_text,
                extracted_code=code,
                extracted_name=name,
            )

            # Read components from component_row
            for c in range(start_col, end_col):
                comp_cell = df.iloc[component_row, c]
                if pd.isna(comp_cell):
                    comp_cell = df.iloc[subject_header_row, c]
                if pd.isna(comp_cell):
                    continue
                comp_name = str(comp_cell).strip().upper()
                if comp_name in ("CIA", "CIA(T)", "MSE", "ESE", "TOT"):
                    block.component_cols[comp_name] = c
                    # Read max marks
                    max_val = df.iloc[max_marks_row, c]
                    if pd.notna(max_val):
                        try:
                            block.max_marks[comp_name] = float(max_val)
                        except (ValueError, TypeError):
                            pass

            if block.component_cols:
                # TOT is the last component col if not explicitly found
                if "TOT" not in block.component_cols:
                    # Last column in range is usually TOT
                    last_col = end_col - 1
                    comp_cell = df.iloc[component_row, last_col]
                    if pd.notna(comp_cell) and str(comp_cell).strip().upper() == "TOT":
                        block.component_cols["TOT"] = last_col
                        max_val = df.iloc[max_marks_row, last_col]
                        if pd.notna(max_val):
                            try:
                                block.max_marks["TOT"] = float(max_val)
                            except (ValueError, TypeError):
                                pass

                self._subject_blocks.append(block)
            else:
                logger.debug(
                    f"[{self.sheet_name}] No components found for subject "
                    f"'{header_text}' (cols {start_col}-{end_col})"
                )

        logger.info(
            f"[{self.sheet_name}] Detected {len(self._subject_blocks)} subjects, "
            f"data starts at row {first_marks_row}"
        )

    # ─────────────────────────────────────────────
    # Student row parsing
    # ─────────────────────────────────────────────

    def _parse_student_rows(self):
        """
        Parse student data rows.
        Each student = 5 consecutive rows: MarksO, Grade, GP, C, C*GP
        """
        df = self.df
        first_marks_row = self._meta["first_marks_row"]
        row_type_col = 3
        summary_start_col = self._meta.get("summary_start_col", df.shape[1])

        # Collect all student row groups
        # Strategy: find all 'MarksO' rows, then read the 4 rows after each
        marks_rows: List[int] = []

        for i in range(first_marks_row, df.shape[0]):
            rt = str(df.iloc[i, row_type_col]).strip() if pd.notna(df.iloc[i, row_type_col]) else ""
            if rt == "MarksO":
                # Validate: col 1 (Seat No) should be non-empty
                seat_val = df.iloc[i, 1]
                if pd.notna(seat_val) and str(seat_val).strip() not in ("", "nan"):
                    marks_rows.append(i)

        logger.info(f"[{self.sheet_name}] Found {len(marks_rows)} student MarksO rows")

        for marks_row_idx in marks_rows:
            try:
                result = self._parse_one_student(df, marks_row_idx, summary_start_col)
                if result:
                    self._results.append(result)
            except Exception as e:
                seat = df.iloc[marks_row_idx, 1]
                logger.warning(
                    f"[{self.sheet_name}] Failed to parse student at row "
                    f"{marks_row_idx} (seat={seat}): {e}"
                )

    def _parse_one_student(
        self, df: pd.DataFrame, marks_row: int, summary_start_col: int
    ) -> Optional[UniversityStudentResult]:
        """
        Parse 5 rows for one student:
          marks_row+0: MarksO
          marks_row+1: Grade
          marks_row+2: GP
          marks_row+3: C (credits)
          marks_row+4: C*GP
        """
        n_rows = df.shape[0]

        # Validate we have enough rows
        if marks_row + 4 >= n_rows:
            return None

        row_marks  = marks_row
        row_grade  = marks_row + 1
        row_gp     = marks_row + 2
        row_c      = marks_row + 3
        row_cgp    = marks_row + 4

        # ── Fixed columns ──
        seat_raw  = df.iloc[row_marks, 1]
        name_raw  = df.iloc[row_marks, 2]
        sr_raw    = df.iloc[row_marks, 0]

        seat = str(seat_raw).strip() if pd.notna(seat_raw) else ""
        name = str(name_raw).strip() if pd.notna(name_raw) else ""

        # Strip leading slash (female indicator)
        if name.startswith("/"):
            name = name[1:].strip()

        if not seat or seat.lower() in ("nan", "none", ""):
            return None

        try:
            sr_no = int(float(str(sr_raw))) if pd.notna(sr_raw) else None
        except (ValueError, TypeError):
            sr_no = None

        result = UniversityStudentResult(
            seat_number=seat,
            student_name=name,
            serial_number=sr_no,
        )

        # ── Subject blocks ──
        for block in self._subject_blocks:
            subj_data = self._parse_subject_for_student(
                df, block, row_marks, row_grade, row_gp, row_c, row_cgp
            )
            if subj_data:
                result.subjects.append(subj_data)

        # ── Summary columns ──
        # Read total marks, SGPA, earned credits, remark
        # These are in the columns AFTER summary_start_col
        # The row type for summary columns is in the MarksO row (they only appear once)
        # We identify by header text stored in self._meta
        self._read_summary_cols(df, result, row_marks, summary_start_col)

        return result

    def _parse_subject_for_student(
        self,
        df: pd.DataFrame,
        block: SubjectBlock,
        row_marks: int,
        row_grade: int,
        row_gp: int,
        row_c: int,
        row_cgp: int,
    ) -> Optional[Dict[str, Any]]:
        """Extract subject data from the 5 student rows for one subject block."""

        components: Dict[str, float] = {}
        for comp_name, col_idx in block.component_cols.items():
            if comp_name == "TOT":
                continue  # calculate TOT ourselves
            pm = parse_mark_value(df.iloc[row_marks, col_idx])
            components[comp_name] = pm.value

        # Read TOT (may be in sheet or we calculate)
        total_marks: float = 0.0
        if "TOT" in block.component_cols:
            pm_tot = parse_mark_value(df.iloc[row_marks, block.component_cols["TOT"]])
            total_marks = pm_tot.value
        else:
            total_marks = sum(components.values())

        # Read grade
        grade = "FF"
        if "TOT" in block.component_cols:
            grade_cell = df.iloc[row_grade, block.component_cols["TOT"]]
        elif block.component_cols:
            # Use last component column
            last_col = max(block.component_cols.values())
            grade_cell = df.iloc[row_grade, last_col]
        else:
            grade_cell = None

        if pd.notna(grade_cell):
            grade = str(grade_cell).strip().upper()
            if grade not in MU_GRADE_TO_GP:
                grade = "FF"

        # Read grade points
        gp: float = MU_GRADE_TO_GP.get(grade, 0.0)
        if "TOT" in block.component_cols:
            gp_cell = df.iloc[row_gp, block.component_cols["TOT"]]
            if pd.notna(gp_cell):
                try:
                    gp = float(gp_cell)
                except (ValueError, TypeError):
                    pass

        # Read credits
        credits: int = 0
        # Credits appear in same column for all components of a subject (they merge)
        # Usually the first non-TOT component column holds the credit value
        first_comp_col = (
            block.component_cols.get("CIA")
            or block.component_cols.get("CIA(T)")
            or block.component_cols.get("ESE")
            or (min(block.component_cols.values()) if block.component_cols else None)
        )
        if first_comp_col is not None:
            c_cell = df.iloc[row_c, first_comp_col]
            if pd.notna(c_cell):
                try:
                    credits = int(float(str(c_cell)))
                except (ValueError, TypeError):
                    pass

        # Determine if practical (no MSE column = lab/project)
        is_practical = "MSE" not in block.component_cols

        # Map components → internal/external for our DB schema
        # Theory: CIA = internal, MSE+ESE = external
        # Lab: CIA = internal, ESE = external
        # Project/SBL: CIA = internal (only)
        cia_t = components.get("CIA(T)", 0.0)
        cia   = components.get("CIA", 0.0)
        mse   = components.get("MSE", 0.0)
        ese   = components.get("ESE", 0.0)

        internal_marks = cia + cia_t  # CIA(T) is tutorial, part of internal
        external_marks = mse + ese

        # Max marks for percentage calculation
        max_tot = block.max_marks.get("TOT", 0.0)
        if max_tot == 0:
            max_cia_t = block.max_marks.get("CIA(T)", 0.0)
            max_cia   = block.max_marks.get("CIA", 0.0)
            max_mse   = block.max_marks.get("MSE", 0.0)
            max_ese   = block.max_marks.get("ESE", 0.0)
            max_tot   = max_cia_t + max_cia + max_mse + max_ese

        # Internal max / external max
        internal_max = block.max_marks.get("CIA(T)", 0) + block.max_marks.get("CIA", 0)
        external_max = block.max_marks.get("MSE", 0) + block.max_marks.get("ESE", 0)

        if not block.extracted_code and not block.extracted_name:
            return None

        return {
            "subject_code": block.extracted_code,
            "subject_name": block.extracted_name,
            "credits": credits,
            "internal_marks": round(internal_marks, 2),
            "external_marks": round(external_marks, 2),
            "total_marks": round(total_marks, 2),
            "grade": grade,
            "grade_points": gp,
            "is_practical": is_practical,
            "components": dict(components),  # raw components kept for reference
            "internal_max": internal_max,
            "external_max": external_max,
            "max_total": max_tot,
        }

    def _read_summary_cols(
        self,
        df: pd.DataFrame,
        result: UniversityStudentResult,
        row_marks: int,
        summary_start_col: int,
    ):
        """Read total marks, SGPA, earned credits, remark from summary columns."""
        n_cols = df.shape[0]
        subject_header_row = self._meta.get("subject_header_row", 2)

        col = summary_start_col
        while col < df.shape[1]:
            header_cell = df.iloc[subject_header_row, col]
            if pd.isna(header_cell):
                col += 1
                continue

            header = str(header_cell).strip().lower()
            val = df.iloc[row_marks, col]

            if "total marks" in header and pd.notna(val):
                try:
                    result.total_semester_marks = float(val)
                except (ValueError, TypeError):
                    pass

            elif ("sgpi" in header or "sgpa" in header) and pd.notna(val):
                try:
                    result.sgpa = float(val)
                except (ValueError, TypeError):
                    pass

            elif "earned credits" in header and "prev" not in header and pd.notna(val):
                try:
                    result.earned_credits = int(float(str(val)))
                except (ValueError, TypeError):
                    pass

            elif "remark" in header and pd.notna(val):
                result.remark = str(val).strip()

            col += 1


# ══════════════════════════════════════════════════════════════
# MULTI-SHEET WORKBOOK PARSER
# ══════════════════════════════════════════════════════════════

class UniversityExcelParser:
    """
    Parses an entire Mumbai University marksheet Excel workbook.
    Handles multiple sheets (different semesters in same file).
    """

    def __init__(self, file_bytes: bytes):
        self.file_bytes = file_bytes
        self._all_results: Dict[str, List[UniversityStudentResult]] = {}
        self._all_meta: Dict[str, Dict[str, Any]] = {}

    def parse_all_sheets(self) -> Dict[str, Any]:
        """
        Parse all sheets in the workbook.

        Returns:
          {
            "sheets": {
              "IT-V-SH 2025": {
                "results": [...],
                "meta": {...}
              },
              ...
            },
            "total_students": int,
            "total_sheets": int,
          }
        """
        try:
            xl = pd.ExcelFile(io.BytesIO(self.file_bytes))
        except Exception as e:
            raise ValueError(f"Cannot open Excel file: {e}")

        output = {}

        for sheet_name in xl.sheet_names:
            try:
                df = pd.read_excel(
                    io.BytesIO(self.file_bytes),
                    sheet_name=sheet_name,
                    header=None,     # CRITICAL: don't interpret any row as header
                    dtype=object,    # keep everything as raw object
                )

                parser = UniversitySheetParser(df, sheet_name)
                results, meta = parser.parse()

                self._all_results[sheet_name] = results
                self._all_meta[sheet_name] = meta

                output[sheet_name] = {
                    "results": [self._result_to_dict(r) for r in results],
                    "meta": meta,
                }

                logger.info(
                    f"Sheet '{sheet_name}': "
                    f"{len(results)} students, "
                    f"{meta.get('subject_count', 0)} subjects"
                )

            except Exception as e:
                logger.error(f"Failed to parse sheet '{sheet_name}': {e}", exc_info=True)
                output[sheet_name] = {"error": str(e), "results": [], "meta": {}}

        total_students = sum(
            len(v.get("results", [])) for v in output.values()
        )

        return {
            "sheets": output,
            "total_students": total_students,
            "total_sheets": len(xl.sheet_names),
            "sheet_names": xl.sheet_names,
        }

    def parse_single_sheet(
        self, sheet_name: Optional[str] = None, sheet_index: int = 0
    ) -> Tuple[List[UniversityStudentResult], Dict[str, Any]]:
        """Parse a single sheet. Returns (results, meta)."""
        try:
            xl = pd.ExcelFile(io.BytesIO(self.file_bytes))
            if sheet_name is None:
                sheet_name = xl.sheet_names[sheet_index]

            df = pd.read_excel(
                io.BytesIO(self.file_bytes),
                sheet_name=sheet_name,
                header=None,
                dtype=object,
            )

            parser = UniversitySheetParser(df, sheet_name)
            return parser.parse()

        except Exception as e:
            raise ValueError(f"Failed to parse sheet: {e}")

    @staticmethod
    def _result_to_dict(r: UniversityStudentResult) -> Dict[str, Any]:
        return {
            "seat_number": r.seat_number,
            "student_name": r.student_name,
            "serial_number": r.serial_number,
            "subjects": r.subjects,
            "total_semester_marks": r.total_semester_marks,
            "sgpa": r.sgpa,
            "earned_credits": r.earned_credits,
            "remark": r.remark,
            "parse_warnings": r.parse_warnings,
        }

    def get_results_for_sheet(
        self, sheet_name: str
    ) -> List[UniversityStudentResult]:
        return self._all_results.get(sheet_name, [])