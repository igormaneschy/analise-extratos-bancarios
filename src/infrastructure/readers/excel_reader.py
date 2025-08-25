"""
Implementação de leitor de extratos em Excel.
"""
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List
import pandas as pd

from src.domain.models import BankStatement, Transaction, TransactionType
from src.domain.interfaces import StatementReader
from src.domain.exceptions import FileNotSupportedError, ParsingError
from src.utils.currency_utils import CurrencyUtils


class ExcelStatementReader(StatementReader):
    """Leitor de extratos bancários em formato Excel."""
    
    def __init__(self):
        self.currency = "EUR"  # Será detectado automaticamente
        
    def can_read(self, file_path: Path) -> bool:
        """Verifica se pode ler o arquivo Excel."""
        return file_path.suffix.lower() in ['.xlsx', '.xls']
    
    def read(self, file_path: Path) -> BankStatement:
        """Lê o arquivo Excel e retorna um extrato."""
        try:
            # Lê o arquivo Excel
            excel_file = pd.ExcelFile(file_path)
            
            # Assume que os dados estão na primeira aba
            df = pd.read_excel(file_path, sheet_name=excel_file.sheet_names[0])
            
            # Detecta a moeda automaticamente
            detected_currency = CurrencyUtils.extract_currency_from_dataframe(df)
            if not detected_currency:
                detected_currency = "EUR"
            self.currency = detected_currency

            # Extrai as transações do DataFrame
            transactions = self._extract_transactions(df)
            
            # Cria o extrato bancário
            statement = BankStatement(
                bank_name=self._extract_bank_name(df),
                account_number=self._extract_account_number(df),
                period_start=self._extract_start_date(transactions),
                period_end=self._extract_end_date(transactions),
                initial_balance=self._extract_initial_balance(df),
                final_balance=self._extract_final_balance(df),
                currency=self.currency,  # Usa a moeda detectada
                transactions=transactions
            )

            return statement

        except Exception as e:
            raise ParsingError(f"Erro ao ler o arquivo Excel: {str(e)}")
    
    def _extract_transactions(self, df) -> List[Transaction]:
        """Extrai transações do DataFrame."""
        transactions = []

        # Procura colunas comuns em extratos Excel
        date_col = None
        description_col = None
        amount_col = None

        # Normaliza os nomes das colunas para facilitar a busca
        normalized_columns = [str(col).strip().lower() for col in df.columns]

        # Define listas de possíveis nomes para cada coluna
        possible_date_cols = ['data mov.', 'data mov', 'data', 'date', 'data transacao', 'transaction date']
        possible_description_cols = ['descricao', 'description', 'descrição']
        possible_amount_cols = ['valor', 'amount', 'value', 'montante']

        # Encontra as colunas correspondentes
        for col_name in possible_date_cols:
            if col_name in normalized_columns:
                date_col = df.columns[normalized_columns.index(col_name)]
                break

        for col_name in possible_description_cols:
            if col_name in normalized_columns:
                description_col = df.columns[normalized_columns.index(col_name)]
                break

        for col_name in possible_amount_cols:
            if col_name in normalized_columns:
                amount_col = df.columns[normalized_columns.index(col_name)]
                break

        if not date_col or not description_col or not amount_col:
            raise ParsingError("Não foi possível identificar as colunas necessárias no Excel")

        for _, row in df.iterrows():
            try:
                # Extrai e converte a data
                date_str = str(row[date_col]).strip()
                date = self._parse_date(date_str)

                # Extrai a descrição
                description = str(row[description_col]).strip()

                # Extrai e converte o valor
                amount_str = str(row[amount_col]).strip()
                amount, transaction_type = self._parse_amount(amount_str)

                # Cria a transação
                transaction = Transaction(
                    date=date,
                    description=description,
                    amount=amount,
                    type=transaction_type
                )

                transactions.append(transaction)

            except Exception:
                # Ignora transações que não podem ser processadas
                continue

        return transactions
    
    def _parse_date(self, date_str: str) -> datetime:
        """Faz parsing de uma string de data."""
        # Formatos de data comuns
        date_formats = [
            '%d/%m/%Y',
            '%d/%m/%y',
            '%d-%m-%Y',
            '%d-%m-%y',
            '%Y-%m-%d',
            '%d.%m.%Y',
            '%d.%m.%y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Não foi possível parsear a data: {date_str}")
    
    def _parse_amount(self, amount_str: str) -> Decimal:
        """Faz parsing de uma string de valor."""
        # Remove espaços e caracteres especiais
        amount_str = amount_str.strip().replace(" ", "")
        
        # Substitui vírgula por ponto para decimais
        amount_str = amount_str.replace(",", ".")
        
        # Remove caracteres não numéricos exceto ponto, sinal de menos e dígitos
        amount_str = re.sub(r'[^\d.-]', '', amount_str)
        
        if amount_str == '':
            return Decimal('0.00')
            
        return Decimal(amount_str)
    
    def _extract_bank_name(self, df) -> str:
        """Extrai o nome do banco do DataFrame."""
        # Procura por padrões de nome de banco
        bank_patterns = [
            r'BPI.*',
            r'Caixa.*',
            r'Santander.*',
            r'BBVA.*',
            r'ING.*',
            r'Deutsche.*',
            r'BNP.*',
            r'Credit.*',
            r'UniCredit.*',
            r'Intesa.*',
            r'Sabadell.*',
            r'CGD.*',
            r'BCP.*',
            r'Novo.*'
        ]
        
        for idx, row in df.iterrows():
            for col in row:
                if pd.isna(col):
                    continue
                cell_value = str(col)
                for pattern in bank_patterns:
                    if re.search(pattern, cell_value, re.IGNORECASE):
                        return re.search(pattern, cell_value, re.IGNORECASE).group()
        
        return "Banco Desconhecido"
    
    def _extract_account_number(self, df) -> str:
        """Extrai o número da conta do DataFrame."""
        # Procura por padrões de número de conta
        for idx, row in df.iterrows():
            for col in row:
                if pd.isna(col):
                    continue
                cell_value = str(col)
                # Padrão genérico para números de conta
                if re.search(r'\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b', cell_value):
                    return re.search(r'\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b', cell_value).group()
                elif re.search(r'\b\d{20,}\b', cell_value):
                    return re.search(r'\b\d{20,}\b', cell_value).group()
        
        return "Conta Desconhecida"
    
    def _extract_start_date(self, transactions: List[Transaction]) -> datetime:
        """Extrai a data inicial das transações."""
        if not transactions:
            return datetime.now()
        return min(t.date for t in transactions)
    
    def _extract_end_date(self, transactions: List[Transaction]) -> datetime:
        """Extrai a data final das transações."""
        if not transactions:
            return datetime.now()
        return max(t.date for t in transactions)
    
    def _extract_initial_balance(self, df) -> Decimal:
        """Extrai o saldo inicial do DataFrame."""
        # Procura por padrões de saldo
        for idx, row in df.iterrows():
            for col in row:
                if pd.isna(col):
                    continue
                cell_value = str(col)
                if 'Saldo' in cell_value and 'Dispon' in cell_value:
                    # Procura o valor do saldo nas próximas linhas
                    for search_idx in range(idx + 1, min(idx + 5, len(df))):
                        search_row = df.iloc[search_idx]
                        for search_col in search_row:
                            if pd.isna(search_col):
                                continue
                            search_value = str(search_col)
                            # Padrão para valores monetários
                            match = re.search(r'[\d.,]+', search_value.replace(" ", ""))
                            if match:
                                try:
                                    return self._parse_amount(match.group())
                                except:
                                    continue
        return Decimal('0.00')
    
    def _extract_final_balance(self, df) -> Decimal:
        """Extrai o saldo final do DataFrame."""
        # Procura por padrões de saldo final nas últimas linhas
        for idx in range(len(df) - 1, max(0, len(df) - 10), -1):
            row = df.iloc[idx]
            for col in row:
                if pd.isna(col):
                    continue
                cell_value = str(col)
                if 'Saldo' in cell_value:
                    # Procura o valor do saldo
                    match = re.search(r'[\d.,]+', cell_value.replace(" ", ""))
                    if match:
                        try:
                            return self._parse_amount(match.group())
                        except:
                            continue
        return Decimal('0.00')