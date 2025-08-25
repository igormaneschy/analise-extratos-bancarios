"""
Implementação de leitor de extratos em CSV.
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


class CSVStatementReader(StatementReader):
    """Leitor de extratos bancários em formato CSV."""
    
    def __init__(self):
        self.currency = "EUR"  # Será detectado automaticamente
        
    def can_read(self, file_path: Path) -> bool:
        """Verifica se pode ler o arquivo CSV."""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        return file_path.suffix.lower() == '.csv'
    
    def read(self, file_path: Path) -> BankStatement:
        """Lê o arquivo CSV e retorna um extrato."""
        try:
            # Lê o arquivo CSV
            df = pd.read_csv(file_path, encoding='utf-8')

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
            raise ParsingError(f"Erro ao ler o arquivo CSV: {str(e)}")

    def _extract_transactions(self, df: pd.DataFrame) -> List[Transaction]:
        """Extrai as transações do DataFrame."""
        transactions = []

        # Procura colunas comuns em extratos CSV
        date_col = self._find_column(df, ['data', 'date', 'data transacao', 'transaction date'])
        description_col = self._find_column(df, ['descricao', 'description', 'descrição'])
        amount_col = self._find_column(df, ['valor', 'amount', 'value', 'montante'])
        balance_col = self._find_column(df, ['saldo', 'balance', 'saldo após', 'balance after'])

        if not date_col or not description_col or not amount_col:
            raise ParsingError("Não foi possível identificar as colunas necessárias no CSV")
        
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
                
                # Extrai o saldo após a transação, se disponível
                balance_after = None
                if balance_col and balance_col in df.columns:
                    balance_str = str(row[balance_col]).strip()
                    balance_after = self._parse_balance(balance_str)
                
                # Cria a transação
                transaction = Transaction(
                    date=date,
                    description=description,
                    amount=amount,
                    type=transaction_type,
                    balance_after=balance_after
                )
                
                transactions.append(transaction)
                
            except Exception as e:
                # Ignora transações que não podem ser processadas
                continue
                
        return transactions
    
    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> str:
        """Encontra uma coluna pelo nome (case insensitive)."""
        columns_lower = [self._normalize_text(col) for col in df.columns]
        for name in possible_names:
            normalized_name = self._normalize_text(name)
            if normalized_name in columns_lower:
                # Retorna o nome original da coluna
                return df.columns[columns_lower.index(normalized_name)]
        return None
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para comparação (remove acentos e converte para minúsculo)."""
        import unicodedata
        # Remove acentos
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        # Converte para minúsculo
        return text.lower()
    
    def _parse_date(self, date_str: str) -> datetime:
        """Faz parsing de uma string de data."""
        # Tenta diferentes formatos de data
        date_formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d/%m/%y",
            "%d-%m-%y"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        # Se nenhum formato funcionar, tenta usar o parser automático
        try:
            return pd.to_datetime(date_str).to_pydatetime()
        except:
            raise ParsingError(f"Não foi possível fazer parsing da data: {date_str}")
    
    def _parse_amount(self, amount_str: str) -> tuple:
        """Faz parsing de um valor monetário e determina o tipo de transação."""
        # Remove espaços e caracteres especiais
        cleaned = amount_str.strip().replace(' ', '')
        
        # Verifica se é um valor negativo
        is_negative = False
        if cleaned.startswith('-') or cleaned.startswith('(') and cleaned.endswith(')'):
            is_negative = True
            cleaned = cleaned.replace('-', '').replace('(', '').replace(')', '')
        
        # Remove símbolos de moeda e outros caracteres não numéricos
        cleaned = re.sub(r'[^\d,.\-]', '', cleaned)
        
        # Normaliza o formato decimal (substitui vírgula por ponto se necessário)
        if ',' in cleaned and '.' in cleaned:
            # Formato 1.234,56
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            # Formato 1234,56
            cleaned = cleaned.replace(',', '.')
        
        try:
            amount = Decimal(cleaned)
            if is_negative:
                amount = -amount
                
            # Determina o tipo de transação
            transaction_type = TransactionType.CREDIT if amount >= 0 else TransactionType.DEBIT
            amount = abs(amount)
            
            return amount, transaction_type
            
        except Exception as e:
            raise ParsingError(f"Não foi possível fazer parsing do valor: {amount_str}")
    
    def _parse_balance(self, balance_str: str) -> Decimal:
        """Faz parsing de um saldo."""
        if not balance_str or balance_str.lower() in ['nan', 'none', 'null', '']:
            return None
            
        # Remove espaços e caracteres especiais
        cleaned = balance_str.strip().replace(' ', '')
        
        # Remove símbolos de moeda e outros caracteres não numéricos
        cleaned = re.sub(r'[^\d,.\-]', '', cleaned)
        
        # Normaliza o formato decimal
        if ',' in cleaned and '.' in cleaned:
            # Formato 1.234,56
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            # Formato 1234,56
            cleaned = cleaned.replace(',', '.')
        
        try:
            return Decimal(cleaned)
        except:
            return None
    
    def _extract_bank_name(self, df: pd.DataFrame) -> str:
        """Extrai o nome do banco do DataFrame."""
        # Procura em metadados ou cabeçalhos
        return "Banco Desconhecido"
    
    def _extract_account_number(self, df: pd.DataFrame) -> str:
        """Extrai o número da conta do DataFrame."""
        # Procura colunas que possam conter o número da conta
        account_col = self._find_column(df, ['conta', 'account', 'número conta', 'account number'])
        if account_col:
            # Retorna o primeiro valor não nulo
            for _, row in df.iterrows():
                value = str(row[account_col]).strip()
                if value and value.lower() not in ['nan', 'none', 'null', '']:
                    return value
        return "Conta Desconhecida"
    
    def _extract_start_date(self, transactions: List[Transaction]) -> datetime:
        """Extrai a data de início do período."""
        if not transactions:
            return datetime.now()
        return min(t.date for t in transactions)
    
    def _extract_end_date(self, transactions: List[Transaction]) -> datetime:
        """Extrai a data de fim do período."""
        if not transactions:
            return datetime.now()
        return max(t.date for t in transactions)
    
    def _extract_initial_balance(self, df: pd.DataFrame) -> Decimal:
        """Extrai o saldo inicial do DataFrame."""
        # Procura colunas que possam conter o saldo inicial
        initial_balance_col = self._find_column(df, ['saldo inicial', 'initial balance', 'opening balance'])
        if initial_balance_col:
            for _, row in df.iterrows():
                value = str(row[initial_balance_col]).strip()
                if value and value.lower() not in ['nan', 'none', 'null', '']:
                    try:
                        _, _ = self._parse_amount(value)  # _parse_amount returns (amount, transaction_type)
                        return Decimal(str(value).replace(',', '.'))
                    except:
                        continue
        return Decimal("0.00")
    
    def _extract_final_balance(self, df: pd.DataFrame) -> Decimal:
        """Extrai o saldo final do DataFrame."""
        # Procura colunas que possam conter o saldo final
        final_balance_col = self._find_column(df, ['saldo final', 'final balance', 'closing balance', 'saldo'])
        if final_balance_col:
            # Pega o último valor não nulo
            for i in range(len(df) - 1, -1, -1):
                row = df.iloc[i]
                value = str(row[final_balance_col]).strip()
                if value and value.lower() not in ['nan', 'none', 'null', '']:
                    try:
                        _, _ = self._parse_amount(value)  # _parse_amount returns (amount, transaction_type)
                        return Decimal(str(value).replace(',', '.'))
                    except:
                        continue
        return Decimal("0.00")