import pandas as pd
from decimal import Decimal

from src.infrastructure.readers.excel_reader import ExcelStatementReader
from src.domain.exceptions import ParsingError
from src.domain.models import TransactionType


def test_normalize_dataframe_header_detection():
    # Create a dataframe with preamble rows and a header row at index 2
    data = [
        ["preamble 1", "preamble x", "preamble y"],
        ["info a", "info b", "info c"],
        ["Data", "Descrição", "Valor"],
        ["01/01/2020", "Compra A", "1.000,00"],
        ["02/01/2020", "Compra B", "-200,00"],
    ]
    df = pd.DataFrame(data)
    reader = ExcelStatementReader()
    df_norm = reader._normalize_dataframe(df)
    # After normalization, columns should be the header row
    assert list(df_norm.columns) == ["Data", "Descrição", "Valor"]
    assert reader._metrics["header_detect_row"] == 2


def test_parse_amount_various_formats():
    reader = ExcelStatementReader()
    amt, ttype = reader._parse_amount("1.234,56")
    assert amt == Decimal("1234.56")
    assert ttype == TransactionType.CREDIT

    amt, ttype = reader._parse_amount("-1.234,56")
    assert amt == Decimal("1234.56")
    assert ttype == TransactionType.DEBIT

    amt, ttype = reader._parse_amount("(1.234,56)")
    assert amt == Decimal("1234.56")
    assert ttype == TransactionType.DEBIT


def test_parse_balance_none_and_values():
    reader = ExcelStatementReader()
    assert reader._parse_balance(None) is None
    assert reader._parse_balance("") is None
    assert reader._parse_balance("1.234,56") == Decimal("1234.56")
    assert reader._parse_balance("1234.56") == Decimal("1234.56")


def test_find_column_matching():
    df = pd.DataFrame({"Descricao Movimento": ["a"], "Data": ["01/01/2020"], "Valor": ["10"]})
    reader = ExcelStatementReader()
    found = reader._find_column(df, ["descricao", "description"])
    assert found == "Descricao Movimento"


def test_extract_transactions_with_credit_and_debit_columns():
    df = pd.DataFrame({
        "Data": ["01/01/2020", "02/01/2020", "03/01/2020"],
        "Descricao": ["A", "B", "C"],
        "credit": ["100,00", "", ""],
        "debit": ["", "50,00", "-25,00"],
    })
    reader = ExcelStatementReader()
    txs = reader._extract_transactions(df)
    # Expect three transactions: credit 100, debit 50, debit 25
    assert len(txs) == 3
    amounts = [t.amount for t in txs]
    types = [t.type for t in txs]
    assert Decimal("100.00") in amounts
    assert Decimal("50.00") in amounts
    assert Decimal("25.00") in amounts
    # types: first credit, others debit
    assert types[0] == TransactionType.CREDIT
    assert types[1] == TransactionType.DEBIT


def test_extract_transactions_missing_columns_raises():
    # Missing description column
    df = pd.DataFrame({"Data": ["01/01/2020"], "Valorzinho": ["10,00"]})
    reader = ExcelStatementReader()
    try:
        reader._extract_transactions(df)
        assert False, "Expected ParsingError"
    except ParsingError:
        pass
