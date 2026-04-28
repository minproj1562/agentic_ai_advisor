# parse_excel_complete.py
import pandas as pd
import os
import json
from pathlib import Path
from typing import Dict, List, Any
import openpyxl

def parse_excel_sheet_complete(file_path: str) -> Dict[str, Any]:
    """
    Completely parse an Excel file and return all information
    """
    result = {
        "file_name": os.path.basename(file_path),
        "file_path": file_path,
        "sheets": {}
    }
    
    try:
        # Load workbook to get sheet names
        wb = openpyxl.load_workbook(file_path, data_only=True)
        
        # Parse each sheet
        for sheet_name in wb.sheetnames:
            print(f"\n{'='*80}")
            print(f"SHEET: {sheet_name}")
            print(f"{'='*80}")
            
            # Read with pandas
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            sheet_info = {
                "sheet_name": sheet_name,
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": list(df.columns),
                "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "sample_data": df.head(10).to_dict('records'),
                "null_counts": df.isnull().sum().to_dict(),
                "unique_values": {}
            }
            
            # Print structure
            print(f"\nTotal Rows: {len(df)}")
            print(f"Total Columns: {len(df.columns)}")
            print(f"\nColumn Names and Types:")
            print("-" * 80)
            for col in df.columns:
                dtype = df[col].dtype
                non_null = df[col].count()
                null_count = df[col].isnull().sum()
                unique_count = df[col].nunique()
                print(f"  {col:40s} | Type: {str(dtype):15s} | Non-Null: {non_null:5d} | Null: {null_count:5d} | Unique: {unique_count:5d}")
            
            # Print first 5 rows
            print(f"\nFirst 5 Rows:")
            print("-" * 80)
            print(df.head(5).to_string())
            
            # Print last 3 rows
            print(f"\nLast 3 Rows:")
            print("-" * 80)
            print(df.tail(3).to_string())
            
            # Get unique values for categorical columns
            for col in df.columns:
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) <= 20:  # Only show if reasonable number
                    sheet_info["unique_values"][col] = list(unique_vals)
                    print(f"\nUnique values in '{col}': {list(unique_vals)}")
            
            result["sheets"][sheet_name] = sheet_info
        
        wb.close()
        
    except Exception as e:
        result["error"] = str(e)
        print(f"ERROR parsing {file_path}: {e}")
        import traceback
        traceback.print_exc()
    
    return result

def parse_all_marks_files(directory: str = "exported_marks") -> Dict[str, Any]:
    """
    Parse all Excel files in the exported_marks directory
    """
    all_results = {}
    
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist!")
        return all_results
    
    excel_files = [f for f in os.listdir(directory) if f.endswith('.xlsx') and not f.startswith('~$')]
    
    print(f"Found {len(excel_files)} Excel files in {directory}")
    print("="*80)
    
    for excel_file in sorted(excel_files):
        file_path = os.path.join(directory, excel_file)
        print(f"\n\n{'#'*80}")
        print(f"# Processing: {excel_file}")
        print(f"{'#'*80}")
        
        result = parse_excel_sheet_complete(file_path)
        all_results[excel_file] = result
    
    return all_results

def save_parsed_data(results: Dict[str, Any], output_file: str = "excel_structure_complete.json"):
    """
    Save parsed results to JSON file
    """
    # Convert numpy types to native Python types
    def convert_types(obj):
        if isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(item) for item in obj]
        elif pd.isna(obj):
            return None
        elif hasattr(obj, 'item'):  # numpy types
            return obj.item()
        else:
            return obj
    
    clean_results = convert_types(results)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(clean_results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n\nResults saved to: {output_file}")

def analyze_marks_structure(results: Dict[str, Any]):
    """
    Analyze the overall structure across all files
    """
    print("\n\n" + "="*80)
    print("OVERALL ANALYSIS")
    print("="*80)
    
    all_columns = set()
    file_patterns = {}
    
    for file_name, file_data in results.items():
        if 'error' in file_data:
            continue
            
        for sheet_name, sheet_data in file_data.get('sheets', {}).items():
            cols = sheet_data.get('columns', [])
            all_columns.update(cols)
            
            # Extract pattern from filename
            pattern = file_name.replace('.xlsx', '')
            if pattern not in file_patterns:
                file_patterns[pattern] = {
                    'columns': cols,
                    'sample_file': file_name
                }
    
    print(f"\nTotal unique columns across all files: {len(all_columns)}")
    print("\nAll unique column names:")
    for col in sorted(all_columns):
        print(f"  - {col}")
    
    print("\n\nFile Patterns:")
    for pattern, data in file_patterns.items():
        print(f"\n  {pattern}:")
        print(f"    Columns ({len(data['columns'])}): {data['columns']}")

if __name__ == "__main__":
    # Parse all files
    results = parse_all_marks_files("exported_marks")
    
    # Save to JSON
    save_parsed_data(results, "excel_structure_complete.json")
    
    # Analyze structure
    analyze_marks_structure(results)
    
    print("\n\n" + "="*80)
    print("PARSING COMPLETE!")
    print("="*80)
    print("\nPlease share the following files:")
    print("  1. excel_structure_complete.json")
    print("  2. Console output from this script")
    print("  3. One sample Excel file (e.g., marks_sem5_IT_2022_2024_25.xlsx)")