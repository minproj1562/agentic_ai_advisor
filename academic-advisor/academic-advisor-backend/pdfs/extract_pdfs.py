import pdfplumber
import json
from pathlib import Path
import os


def parse_pdf(file_path):
    """
    Extract text and tables from a PDF using pdfplumber.
    Returns a list of dictionaries, one per page.
    """
    pages = []

    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"Total pages in {file_path}: {len(pdf.pages)}")

            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""

                raw_tables = page.extract_tables() or []
                tables = []

                for table in raw_tables:
                    clean_table = []
                    for row in table:
                        if row:
                            clean_row = [
                                cell if cell is not None else "" for cell in row
                            ]
                            clean_table.append(clean_row)
                    tables.append(clean_table)

                pages.append({
                    "page": page_num,
                    "text": text,
                    "tables": tables
                })

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return pages


def main():
    print("===== PDF Extraction Started =====")
    print("Current folder:", os.getcwd())
    print("Files in folder:", os.listdir())

    pdf_files = [
        "SY_R2024.1_IT.pdf",
        "FY_R25_IT.pdf",
        "TY_R2024.1_IT.pdf",
        "B_TECH_CSE_Scheme.pdf"
    ]

    for pdf in pdf_files:
        print(f"\nChecking {pdf}...")

        path = Path(pdf)

        if path.exists():
            print("File found. Parsing...")

            data = parse_pdf(pdf)

            if data:
                output_file = path.stem + ".json"

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print(f"Successfully saved {output_file}")
            else:
                print("No data extracted.")

        else:
            print("File NOT found.")

    print("\n===== Extraction Finished =====")


if __name__ == "__main__":
    main()