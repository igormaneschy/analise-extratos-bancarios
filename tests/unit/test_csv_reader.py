import pytest
import pandas as pd
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

from src.infrastructure.readers.csv_reader import CSVStatementReader
from src.domain.models import BankStatement, Transaction, TransactionType
from src.domain.exceptions import ParsingError

class TestCSVStatementReader:
    """Testes para o CSVStatementReader."""
    
    def test_can_read_csv_file(self):
        """Testa se o leitor pode ler arquivos CSV."""
        reader = CSVStatementReader()
        csv_path = Path("test_file.csv")
        assert reader.can_read(csv_path) == True
    
    def test_cannot_read_non_csv_file(self):
        """Testa se o leitor não pode ler arquivos não-CSV."""
        reader = CSVStatementReader()
        txt_path = Path("test_file.txt")
        assert reader.can_read(txt_path) == False
    
    def test_normalize_text(self):
        """Testa a normalização de texto."""
        reader = CSVStatementReader()
        assert reader._normalize_text("Data Transação") == "data transacao"
        assert reader._normalize_text("Descrição") == "descricao"
        assert reader._normalize_text("Valor") == "valor"
    
    def test_find_column_found(self):
        """Testa a busca de coluna quando encontrada."""
        reader = CSVStatementReader()
        df = pd.DataFrame(columns=["Data", "Descrição", "Valor"])
        column = reader._find_column(df, ["data", "date", "data transacao"])
        assert column == "Data"
    
    def test_find_column_not_found(self):
        """Testa a busca de coluna quando não encontrada."""
        reader = CSVStatementReader()
        df = pd.DataFrame(columns=["Coluna1", "Coluna2", "Coluna3"])
        column = reader._find_column(df, ["data", "date", "data transacao"])
        assert column is None
    
    def test_parse_date_success(self):
        """Testa o parsing de data com sucesso."""
        reader = CSVStatementReader()
        
        # Testa formato DD/MM/YYYY
        date1 = reader._parse_date("01/01/2024")
        assert date1.strftime("%d/%m/%Y") == "01/01/2024"
        
        # Testa formato DD-MM-YYYY
        date2 = reader._parse_date("01-01-2024")
        assert date2.strftime("%d/%m/%Y") == "01/01/2024"
        
        # Testa formato YYYY-MM-DD
        date3 = reader._parse_date("2024-01-01")
        assert date3.strftime("%d/%m/%Y") == "01/01/2024"
    
    def test_parse_date_failure(self):
        """Testa o parsing de data com falha."""
        reader = CSVStatementReader()
        
        with pytest.raises(ParsingError):
            reader._parse_date("data invalida")
    
    def test_parse_amount_positive(self):
        """Testa o parsing de valor positivo."""
        reader = CSVStatementReader()
        amount, transaction_type = reader._parse_amount("150,50")
        assert amount == Decimal("150.50")
        assert transaction_type == TransactionType.CREDIT
    
    def test_parse_amount_negative(self):
        """Testa o parsing de valor negativo."""
        reader = CSVStatementReader()
        amount, transaction_type = reader._parse_amount("-150,50")
        assert amount == Decimal("150.50")
        assert transaction_type == TransactionType.DEBIT
    
    def test_parse_amount_parentheses_negative(self):
        """Testa o parsing de valor negativo com parênteses."""
        reader = CSVStatementReader()
        amount, transaction_type = reader._parse_amount("(150,50)")
        assert amount == Decimal("150.50")
        assert transaction_type == TransactionType.DEBIT
    
    def test_parse_amount_with_currency_symbol(self):
        """Testa o parsing de valor com símbolo de moeda."""
        reader = CSVStatementReader()
        amount, transaction_type = reader._parse_amount("R$ 150,50")
        assert amount == Decimal("150.50")
    
    def test_parse_amount_failure(self):
        """Testa o parsing de valor com falha."""
        reader = CSVStatementReader()
        
        with pytest.raises(ParsingError):
            reader._parse_amount("valor invalido")
    
    def test_parse_balance_valid(self):
        """Testa o parsing de saldo válido."""
        reader = CSVStatementReader()
        balance = reader._parse_balance("1500,50")
        assert balance == Decimal("1500.50")
    
    def test_parse_balance_empty(self):
        """Testa o parsing de saldo vazio."""
        reader = CSVStatementReader()
        balance = reader._parse_balance("")
        assert balance is None
    
    def test_parse_balance_nan(self):
        """Testa o parsing de saldo NaN."""
        reader = CSVStatementReader()
        balance = reader._parse_balance("nan")
        assert balance is None
    
    @patch("pandas.read_csv")
    @patch("src.utils.currency_utils.CurrencyUtils.extract_currency_from_dataframe")
    def test_read_success(self, mock_extract_currency, mock_read_csv):
        """Testa a leitura completa de um CSV com sucesso."""
        # Configura os mocks
        mock_extract_currency.return_value = "EUR"
        
        # Cria um DataFrame diretamente em vez de usar StringIO
        df = pd.DataFrame({
            "data": ["01/01/2024", "02/01/2024"],
            "descricao": ["Supermercado", "Salário"],
            "valor": ["-150,50", "2500,00"],
            "saldo": ["850,00", "3350,00"]
        })
        mock_read_csv.return_value = df
        
        reader = CSVStatementReader()
        statement = reader.read(Path("test.csv"))
        
        assert isinstance(statement, BankStatement)
        assert len(statement.transactions) == 2
        assert statement.currency == "EUR"
    
    @patch("pandas.read_csv")
    def test_read_missing_columns(self, mock_read_csv):
        """Testa a leitura de CSV com colunas faltando."""
        # Configura o mock
        df = pd.DataFrame(columns=["data", "valor"])  # Falta a coluna 'descricao'
        mock_read_csv.return_value = df
        
        reader = CSVStatementReader()
        
        with pytest.raises(ParsingError):
            reader.read(Path("test.csv"))
    
    @patch("pandas.read_csv", side_effect=Exception("Erro de leitura"))
    def test_read_failure(self, mock_read_csv):
        """Testa a falha na leitura de um CSV."""
        reader = CSVStatementReader()
        
        with pytest.raises(ParsingError):
            reader.read(Path("test.csv"))
    
    def test_extract_transactions_success(self):
        """Testa a extração de transações com sucesso."""
        reader = CSVStatementReader()
        
        df = pd.DataFrame({
            "data": ["01/01/2024", "02/01/2024"],
            "descricao": ["Supermercado", "Salário"],
            "valor": ["-150,50", "2500,00"],
            "saldo": ["850,00", "3350,00"]
        })
        
        transactions = reader._extract_transactions(df)
        assert len(transactions) == 2
        assert transactions[0].description == "Supermercado"
        assert transactions[0].amount == Decimal("150.50")
        assert transactions[0].type == TransactionType.DEBIT
        assert transactions[1].description == "Salário"
        assert transactions[1].amount == Decimal("2500.00")
        assert transactions[1].type == TransactionType.CREDIT
    
    def test_extract_transactions_with_invalid_row(self):
        """Testa a extração de transações com linha inválida."""
        reader = CSVStatementReader()
        
        df = pd.DataFrame({
            "data": ["01/01/2024", "data invalida"],
            "descricao": ["Supermercado", "Salário"],
            "valor": ["-150,50", "valor invalido"],
            "saldo": ["850,00", "3350,00"]
        })
        
        transactions = reader._extract_transactions(df)
        # Apenas a primeira linha válida deve ser processada
        assert len(transactions) == 1
        assert transactions[0].description == "Supermercado"