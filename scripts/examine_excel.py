#!/usr/bin/env python3
"""
Script to examine the structure of the sample Excel file.
"""
import pandas as pd
from pathlib import Path

def examine_excel_file(file_path):
    """Examine the structure of an Excel file."""
    print(f"Examining file: {file_path}")
    
    # Read all sheets
    excel_file = pd.ExcelFile(file_path)
    print(f"Sheet names: {excel_file.sheet_names}")
    
    # Read each sheet
    for sheet_name in excel_file.sheet_names:
        print(f"\n--- Sheet: {sheet_name} ---")
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        print(f"Shape: {df.shape}")
        print("Columns:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}. {col}")
        print("\nFirst 20 rows:")
        print(df.head(20))
        print("\nData types:")
        print(df.dtypes)
        
        # Check for non-empty rows
        print("\nNon-empty rows:")
        non_empty = df.dropna(how='all')
        print(f"Total non-empty rows: {len(non_empty)}")
        print("First 10 non-empty rows:")
        print(non_empty.head(10))

if __name__ == "__main__":
    # Path to the sample Excel file
    excel_path = Path("data/samples/extmovs_bpi2108102947.xlsx")
    if excel_path.exists():
        examine_excel_file(excel_path)
    else:
        print(f"File not found: {excel_path}")