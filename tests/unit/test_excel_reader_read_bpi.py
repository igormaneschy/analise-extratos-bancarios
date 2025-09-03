import pandas as pd
from types import SimpleNamespace
from pathlib import Path
from decimal import Decimal

import pytest

from src.infrastructure.readers.excel_reader import ExcelStatementReader
from src.utils.currency_utils import CurrencyUtils
from src.domain.exceptions import ParsingError


# Fixtures for DataFrames
@pytest.fixture
def df_with_header_at_row():
    data = [
        ["preamble", "preamble", "preamble"],
        ["info", "info", "info"],
        ["Data", "Descrição", "Valor"],
        ["01/01/2020", "Compra A", "1.000,00"],
    ]
    return pd.DataFrame(data)


@pytest.fixture
def df_normalized():
    return pd.DataFrame({"Data": ["01/01/2020"], "Descrição": ["Compra A"], "Valor": ["1.000,00"]})


@pytest.fixture
def excelfile_movimentos():
    return SimpleNamespace(sheet_names=["Movimentos", "Outra"])


def test_read_bpi_initial_header_none_success(monkeypatch, df_with_header_at_row, df_normalized, excelfile_movimentos):
    reader = ExcelStatementReader()
    # Mock ExcelFile to report sheet names containing Movimentos
    monkeypatch.setattr(pd, "ExcelFile", lambda p: excelfile_movimentos)

    # Mock read_excel: when called for Movimentos with header=None return df_with_header_at_row
    def fake_read_excel(path, *args, **kwargs):
        if kwargs.get("sheet_name") == "Movimentos" and kwargs.get("header") is None:
            return df_with_header_at_row
        raise RuntimeError("Unexpected call")

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)

    # Ensure normalization returns a usable dataframe
    monkeypatch.setattr(ExcelStatementReader, "_normalize_dataframe", lambda self, d: df_normalized)
    monkeypatch.setattr(CurrencyUtils, "extract_currency_from_dataframe", lambda df: "EUR")
    monkeypatch.setattr(ExcelStatementReader, "_extract_transactions", lambda self, df: [])

    stmt = reader.read(Path("extrato_bpi.xlsx"))

    assert stmt is not None
    assert stmt.currency == "EUR"
    assert stmt.transactions == []
    assert any(a.get("strategy") == "movimentos_header_none_normalize" and a.get("ok") for a in reader._metrics["attempts"]) 
    assert reader._metrics["chosen_strategy"] == "movimentos_header_none_normalize"


def test_read_bpi_initial_header_none_raises_then_fallback_skiprows_succeeds(monkeypatch, df_normalized, excelfile_movimentos):
    reader = ExcelStatementReader()
    monkeypatch.setattr(pd, "ExcelFile", lambda p: excelfile_movimentos)

    # Side effect for read_excel to simulate initial failure then fallback success
    def fake_read_excel(path, *args, **kwargs):
        # initial attempt: sheet_name='Movimentos', header=None -> raise
        if kwargs.get("sheet_name") == "Movimentos" and kwargs.get("header") is None:
            raise Exception("boom initial")
        # fallback attempt: sheet_name='Movimentos', skiprows=11, header=0 -> return normalized df
        if kwargs.get("sheet_name") == "Movimentos" and kwargs.get("skiprows") == 11 and kwargs.get("header") == 0:
            # return a df already normalized (columns as header)
            return pd.DataFrame({"Data": ["01/01/2020"], "Descrição": ["Compra"], "Valor": ["100,00"]})
        # other calls: for simplicity raise
        raise Exception("unexpected read_excel call: %s" % (kwargs,))

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)
    monkeypatch.setattr(ExcelStatementReader, "_normalize_dataframe", lambda self, d: d)
    monkeypatch.setattr(CurrencyUtils, "extract_currency_from_dataframe", lambda df: None)
    monkeypatch.setattr(ExcelStatementReader, "_extract_transactions", lambda self, df: [])

    stmt = reader.read(Path("extrato_bpi.xlsx"))
    assert stmt is not None
    assert stmt.transactions == []
    # metrics should show the initial attempt failed and a fallback succeeded
    assert any(a.get("strategy") == "movimentos_header_none_normalize" and not a.get("ok") for a in reader._metrics["attempts"]) 
    assert any(str(a.get("strategy")).startswith("fallback_") and a.get("ok") for a in reader._metrics["attempts"]) 
    assert str(reader._metrics["chosen_strategy"]).startswith("fallback_")


def test_read_bpi_all_fallbacks_fail_then_first_sheet_header_none_success(monkeypatch):
    # Simulate that initial and fallback Movimentos attempts fail and final fallback (first sheet header=None) succeeds
    excelfile = SimpleNamespace(sheet_names=["PrimeiraAba", "Movimentos"])
    monkeypatch.setattr(pd, "ExcelFile", lambda p: excelfile)

    calls = []

    def fake_read_excel(path, *args, **kwargs):
        calls.append(kwargs.copy())
        # initial Movimentos header=None -> raise
        if kwargs.get("sheet_name") == "Movimentos" and kwargs.get("header") is None:
            raise Exception("initial fail")
        # fallback attempts for Movimentos -> raise
        if kwargs.get("sheet_name") == "Movimentos":
            raise Exception("fallback fail")
        # final attempt: sheet_name=excel_file.sheet_names[0] and header=None
        if kwargs.get("sheet_name") == "PrimeiraAba" and kwargs.get("header") is None:
            # return a df that will be normalized
            return pd.DataFrame([["Data", "Descrição", "Valor"], ["01/01/2020", "Compra", "10,00"]])
        raise Exception("unexpected")

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)
    # Make normalize_dataframe convert the returned df into a normalized one
    def norm(self, d):
        try:
            # if d has header row as first row, convert to df with columns
            if not isinstance(d.columns[0], str):
                header = d.iloc[0].tolist()
                df2 = d.iloc[1:].copy()
                df2.columns = header
                return df2.reset_index(drop=True)
        except Exception:
            pass
        return d

    monkeypatch.setattr(ExcelStatementReader, "_normalize_dataframe", norm)
    monkeypatch.setattr(CurrencyUtils, "extract_currency_from_dataframe", lambda df: "EUR")
    monkeypatch.setattr(ExcelStatementReader, "_extract_transactions", lambda self, df: [])

    reader = ExcelStatementReader()
    stmt = reader.read(Path("extrato_bpi.xlsx"))
    assert stmt is not None
    # The code may set the chosen strategy to the explicit fallback that used the first sheet
    # (i.e. "fallback_{'sheet_name': 'PrimeiraAba'}") or to "first_sheet_header_none_normalize".
    chosen = reader._metrics.get("chosen_strategy")
    assert chosen == "first_sheet_header_none_normalize" or (isinstance(chosen, str) and chosen.startswith("fallback_") and "PrimeiraAba" in chosen)
    assert any((a.get("strategy") == "first_sheet_header_none_normalize" and a.get("ok")) or (isinstance(a.get("strategy"), str) and a.get("strategy").startswith("fallback_") and a.get("ok")) for a in reader._metrics["attempts"]) 


def test_read_bpi_all_attempts_fail_raises_ParsingError(monkeypatch):
    excelfile = SimpleNamespace(sheet_names=["Movimentos", "Outra"])
    monkeypatch.setattr(pd, "ExcelFile", lambda p: excelfile)

    def fake_read_excel(path, *args, **kwargs):
        raise Exception("read always fails")

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)

    reader = ExcelStatementReader()
    with pytest.raises(ParsingError):
        reader.read(Path("extrato_bpi.xlsx"))
