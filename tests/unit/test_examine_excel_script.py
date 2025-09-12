import pandas as pd
from scripts.examine_excel import examine_excel_file


def test_examine_excel_file_outputs(tmp_path, capsys):
    # Create a temporary Excel file with two sheets
    file = tmp_path / "sample.xlsx"
    with pd.ExcelWriter(file) as writer:
        pd.DataFrame({'A': [1, None], 'B': ['x', 'y']}).to_excel(writer, sheet_name='Sheet1', index=False)
        pd.DataFrame({'C': [10, 20], 'D': [None, 'z']}).to_excel(writer, sheet_name='Other', index=False)

    # Run the script function and capture stdout
    examine_excel_file(file)
    out = capsys.readouterr().out

    assert "Examining file" in out
    assert "Sheet names:" in out
    assert "Sheet1" in out and "Other" in out
    assert "Total non-empty rows" in out
