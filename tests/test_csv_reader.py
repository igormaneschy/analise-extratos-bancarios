"""
Testes para o leitor de extratos CSV.
"""
import sys
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import pytest
import pandas as pd

# Adiciona o diretório raiz ao path para importações
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.infrastructure.readers.csv_reader import CSVStatementReader
from src.domain.models import Transaction, TransactionType


def test_csv_reader_can_read():
    """Testa se o CSV reader pode identificar arquivos CSV."""
    reader = CSVStatementReader()
    
    # Deve retornar True para arquivos CSV
    assert reader.can_read(Path("test.csv")) == True
    assert reader.can_read(Path("test.CSV")) == True
    
    # Deve retornar False para outros formatos
    assert reader.can_read(Path("test.pdf")) == False
    assert reader.can_read(Path("test.xlsx")) == False
    
    # Testa com string também
    assert reader.can_read("test.csv") == True


def test_csv_reader_extract_transactions():
    """Testa a extração de transações de um DataFrame."""
    reader = CSVStatementReader()
    
    # Cria um DataFrame de exemplo
    data = {
        'data': ['01/01/2023', '02/01/2023', '03/01/2023'],
        'descricao': ['Salário', 'Supermercado', 'Conta de Luz'],
        'valor': ['2500.00', '-150.50', '-80.00']
    }
    df = pd.DataFrame(data)
    
    transactions = reader._extract_transactions(df)
    
    assert len(transactions) == 3
    
    # Verifica a primeira transação (receita)
    assert transactions[0].description == 'Salário'
    assert transactions[0].amount == Decimal('2500.00')
    assert transactions[0].type == TransactionType.CREDIT
    
    # Verifica a segunda transação (despesa)
    assert transactions[1].description == 'Supermercado'
    assert transactions[1].amount == Decimal('150.50')
    assert transactions[1].type == TransactionType.DEBIT
    
    # Verifica a terceira transação (despesa)
    assert transactions[2].description == 'Conta de Luz'
    assert transactions[2].amount == Decimal('80.00')
    assert transactions[2].type == TransactionType.DEBIT


def test_csv_reader_parse_date():
    """Testa o parsing de datas."""
    reader = CSVStatementReader()
    
    # Testa diferentes formatos de data
    assert reader._parse_date('01/01/2023') == datetime(2023, 1, 1)
    assert reader._parse_date('01-01-2023') == datetime(2023, 1, 1)
    assert reader._parse_date('2023-01-01') == datetime(2023, 1, 1)
    
    # Testa com pandas datetime parsing
    result = reader._parse_date('01/01/2023')
    assert isinstance(result, datetime)


def test_csv_reader_parse_amount():
    """Testa o parsing de valores monetários."""
    reader = CSVStatementReader()
    
    # Testa valores positivos
    amount, transaction_type = reader._parse_amount('2500.00')
    assert amount == Decimal('2500.00')
    assert transaction_type == TransactionType.CREDIT
    
    # Testa valores negativos
    amount, transaction_type = reader._parse_amount('-150.50')
    assert amount == Decimal('150.50')
    assert transaction_type == TransactionType.DEBIT
    
    # Testa valores com parênteses (formato comum para negativos)
    amount, transaction_type = reader._parse_amount('(80.00)')
    assert amount == Decimal('80.00')
    assert transaction_type == TransactionType.DEBIT
    
    # Testa valores com vírgula como separador decimal
    amount, transaction_type = reader._parse_amount('1.500,75')
    assert amount == Decimal('1500.75')
    assert transaction_type == TransactionType.CREDIT


def test_csv_reader_parse_balance():
    """Testa o parsing de saldos."""
    reader = CSVStatementReader()
    
    # Testa valores válidos
    balance = reader._parse_balance('2500.00')
    assert balance == Decimal('2500.00')
    
    # Testa valores com vírgula
    balance = reader._parse_balance('1.500,75')
    assert balance == Decimal('1500.75')
    
    # Testa valores inválidos
    balance = reader._parse_balance('invalid')
    assert balance is None
    
    # Testa valores vazios
    balance = reader._parse_balance('')
    assert balance is None


def test_csv_reader_find_column():
    """Testa a busca de colunas."""
    reader = CSVStatementReader()
    
    # Cria um DataFrame de exemplo
    data = {
        'Data': ['01/01/2023'],
        'Descrição': ['Salário'],
        'Valor': ['2500.00']
    }
    df = pd.DataFrame(data)
    
    # Deve encontrar colunas com nomes diferentes (case insensitive)
    assert reader._find_column(df, ['data', 'date']) == 'Data'
    assert reader._find_column(df, ['descricao', 'description']) == 'Descrição'
    assert reader._find_column(df, ['valor', 'amount']) == 'Valor'
    
    # Testa com acentos
    assert reader._find_column(df, ['descrição', 'description']) == 'Descrição'
    
    # Deve retornar None para colunas inexistentes
    assert reader._find_column(df, ['saldo', 'balance']) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])