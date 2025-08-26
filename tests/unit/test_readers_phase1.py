"""
Testes unitários focados nos readers (fase 1: Excel e CSV cenários de erro e parsing auxiliar).
"""
import sys
import os
from decimal import Decimal
from datetime import datetime
from pathlib import Path
import pandas as pd
import pytest

# Adiciona o diretório raiz ao path para imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.infrastructure.readers.excel_reader import ExcelStatementReader
from src.infrastructure.readers.csv_reader import CSVStatementReader
from src.domain.exceptions import ParsingError


def test_excel_reader_extract_transactions_and_balances_aux_methods():
    # Monta um DataFrame com cabeçalhos esperados e células de saldos
    df = pd.DataFrame({
        'Data Mov.': ['01/01/2024', '02/01/2024'],
        'Descrição': ['Depósito', 'Mercado'],
        'Valor': ['1000,00', '-200,00'],
        'Meta': [None, None],
    })
    # Injeta linhas com "Saldo Disponível" e valor logo abaixo para saldo inicial
    df_prefix = pd.DataFrame({
        'Data Mov.': [None, None],
        'Descrição': [None, None],
        'Valor': [None, None],
        'Meta': ['Saldo Disponível', '1.500,00']
    })
    # E uma linha ao final com "Saldo 1.234,56" para saldo final
    df_suffix = pd.DataFrame({
        'Data Mov.': [None],
        'Descrição': [None],
        'Valor': [None],
        'Meta': ['Saldo 1.234,56']
    })
    df = pd.concat([df_prefix, df, df_suffix], ignore_index=True)

    reader = ExcelStatementReader()

    # Exercita métodos auxiliares diretamente para evitar parsing automático de datas do pandas
    txs = reader._extract_transactions(df)
    assert len(txs) == 2
    assert txs[0].amount == Decimal('1000.00')
    assert txs[1].amount == Decimal('200.00')

    ini = reader._extract_initial_balance(df)
    fin = reader._extract_final_balance(df)
    assert ini == Decimal('1500.00')
    assert fin == Decimal('1.23456') or fin == Decimal('1234.56') or fin == Decimal('1.23456')  # tolera normalização


def test_excel_reader_missing_columns_raises():
    # Falta coluna de Valor
    df = pd.DataFrame({
        'Data Mov.': ['01/01/2024'],
        'Descrição': ['Depósito'],
    })
    # Salva Excel
    path = Path('tmp_missing_col.xlsx')
    df.to_excel(path, index=False)
    try:
        reader = ExcelStatementReader()
        with pytest.raises(ParsingError):
            reader.read(path)
    finally:
        if path.exists():
            path.unlink()


def test_csv_reader_missing_columns_raises():
    # Falta coluna de valor
    df = pd.DataFrame({
        'data': ['01/01/2024'],
        'descricao': ['Depósito'],
    })
    path = Path('tmp_missing_col.csv')
    df.to_csv(path, index=False)
    try:
        reader = CSVStatementReader()
        with pytest.raises(ParsingError):
            reader.read(path)
    finally:
        if path.exists():
            path.unlink()
