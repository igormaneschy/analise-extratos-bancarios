from pathlib import Path
import sys
import builtins
from types import SimpleNamespace

import pytest

# Import the script function under test
import scripts.test_excel_reader as script


def test_test_excel_reader_no_file(monkeypatch, capsys, tmp_path):
    # Make the example file path point to a non-existent file
    sample_path = Path("data/samples/extmovs_bpi2108102947.xlsx")

    # Patch Path.exists to return False for this path
    original_exists = Path.exists

    def fake_exists(self):
        if str(self) == str(sample_path):
            return False
        return original_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)

    # Run the test function
    script.test_excel_reader()
    out = capsys.readouterr().out
    assert "Arquivo não encontrado" in out


def test_test_excel_reader_reads_file(monkeypatch, tmp_path, capsys):
    # Create a fake statement object with minimal attributes
    fake_statement = SimpleNamespace(
        bank_name="Fake Bank",
        account_number="12345",
        period_start="2025-01-01",
        period_end="2025-01-31",
        initial_balance=100.0,
        final_balance=200.0,
        transactions=[
            SimpleNamespace(date=__import__('datetime').date(2025,1,2), description="Tx1", type=0, amount=10.0),
            SimpleNamespace(date=__import__('datetime').date(2025,1,3), description="Tx2", type=1, amount=20.0),
        ]
    )

    class FakeReader:
        def can_read(self, path):
            return True
        def read(self, path):
            return fake_statement

    # Patch the ExcelStatementReader class in the script module to our FakeReader
    # scripts.test_excel_reader imported ExcelStatementReader at module import time,
    # so we must replace the reference in the script module namespace.
    monkeypatch.setattr(script, "ExcelStatementReader", FakeReader, raising=False)

    # Ensure the sample path exists
    sample_path = Path("data/samples/extmovs_bpi2108102947.xlsx")
    monkeypatch.setattr(Path, "exists", lambda self: True)

    # Run the script
    script.test_excel_reader()
    out = capsys.readouterr().out

    assert "Extrato lido com sucesso" in out
    assert "Fake Bank" in out
    assert "Total de transações" in out
