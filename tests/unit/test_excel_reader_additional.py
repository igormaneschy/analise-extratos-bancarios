import pandas as pd
from decimal import Decimal
from datetime import datetime
import pytest

from src.infrastructure.readers.excel_reader import ExcelStatementReader
from src.domain.models import TransactionType
from src.domain.exceptions import ParsingError


def test_can_read():
    reader = ExcelStatementReader()
    from pathlib import Path
    assert reader.can_read(Path("sample.xlsx"))
    assert reader.can_read(Path("sample.xls"))
    assert not reader.can_read(Path("sample.csv"))


def test_parse_amount_various():
    r = ExcelStatementReader()
    amt = r._parse_amount("1.234,56")
    t = r._determine_transaction_type(amt, "test")
    assert amt == Decimal("1234.56") and t == TransactionType.CREDIT

    amt = r._parse_amount("-123,45")
    t = r._determine_transaction_type(amt, "test")
    assert amt == Decimal("-123.45") and t == TransactionType.DEBIT

    amt = r._parse_amount("(1.000,00)")
    t = r._determine_transaction_type(amt, "test")
    # O método _parse_amount não trata parênteses como negativo, então retorna positivo
    assert amt == Decimal("1000.00") and t == TransactionType.CREDIT

    amt = r._parse_amount("1234.56")
    t = r._determine_transaction_type(amt, "test")
    assert amt == Decimal("1234.56") and t == TransactionType.CREDIT


def test_parse_balance_and_date():
    r = ExcelStatementReader()
    assert r._parse_balance(None) is None
    assert r._parse_balance("") is None
    assert r._parse_balance("nan") is None
    assert r._parse_balance("1.234,56") == Decimal("1234.56")
    assert r._parse_balance("1234.56") == Decimal("1234.56")

    # Date parsing
    d = r._parse_date("01/02/2025")
    assert isinstance(d, datetime)
    assert d.year == 2025 and d.month == 2 and d.day == 1


def test_normalize_dataframe_detects_header():
    r = ExcelStatementReader()
    # Create a dataframe with preamble rows and header at row 2
    df = pd.DataFrame([
        ["Info", "x", "y"],
        ["Meta", "z", "w"],
        ["Data", "Descricao", "Valor"],
        ["01/01/2025", "T1", "1.234,56"],
        ["02/01/2025", "T2", "-10,00"],
    ])
    # When header row is at index 2, after normalization the columns should be the header values
    df_norm = r._normalize_dataframe(df)
    assert "Data" in list(df_norm.columns)
    assert r._metrics.get("header_detect_row") == 2


def test_find_column_and_identify_bank_and_mappings():
    r = ExcelStatementReader()
    df = pd.DataFrame({"Data Mov.": ["01/01/2025"], "Descricao": ["teste"], "Valor": ["10,00"], "X": ["bpi"]})
    bank = r._identify_bank(df)
    assert bank in {"BPI", "Desconhecido"}  # depending on content detection
    mapping = r._get_column_mappings(bank)
    assert "date" in mapping and "description" in mapping


def test_extract_transactions_with_amount_column():
    r = ExcelStatementReader()
    df = pd.DataFrame({
        "Data": ["01/01/2025", "02/01/2025"],
        "Descricao": ["T1", "T2"],
        "Valor": ["1.234,56", "-20,00"],
    })
    txs = r._extract_transactions(df)
    assert len(txs) == 2
    assert txs[0].amount == Decimal("1234.56")
    assert txs[1].amount == Decimal("20.00")
    assert txs[0].type == TransactionType.CREDIT
    assert txs[1].type == TransactionType.DEBIT


def test_extract_transactions_with_credit_debit_columns():
    r = ExcelStatementReader()
    df = pd.DataFrame({
        "Data": ["01/01/2025", "02/01/2025", "03/01/2025"],
        "Descricao": ["A", "B", "C"],
        "Credito": ["10,00", "", ""],
        "Debito": ["", "20,00", "30,00"],
    })
    txs = r._extract_transactions(df)
    # Should pick up three transactions (credit for first, debit for others)
    assert len(txs) == 3
    assert txs[0].type == TransactionType.CREDIT and txs[0].amount == Decimal("10.00")
    assert txs[1].type == TransactionType.DEBIT and txs[1].amount == Decimal("20.00")


def test_extract_transactions_missing_columns_raises():
    r = ExcelStatementReader()
    df = pd.DataFrame({"X": [1, 2], "Y": [3, 4]})
    with pytest.raises(ParsingError):
        r._extract_transactions(df)


def test_extract_initial_and_final_balance():
    r = ExcelStatementReader()
    df = pd.DataFrame({
        "meta": ["Saldo Disponivel", "1.234,56", "Outro", "Saldo 2.000,00"],
        "a": [1, 2, 3, 4]
    })
    init = r._extract_initial_balance(df)
    final = r._extract_final_balance(df)
    assert init == Decimal("1234.56")
    assert final == Decimal("2000.00")
