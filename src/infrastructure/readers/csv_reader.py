"""
Implementação de leitor de extratos em CSV.
"""
from pathlib import Path
from typing import List
import pandas as pd

from src.domain.models import BankStatement, Transaction, TransactionType
from src.domain.exceptions import FileNotSupportedError, ParsingError
from src.utils.currency_utils import CurrencyUtils
from src.infrastructure.readers.base_reader import BaseStatementReader


class CSVStatementReader(BaseStatementReader):
    """Leitor de extratos bancários em formato CSV."""
        
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
            df = self._normalize_dataframe(df)

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
                amount = self._parse_amount(amount_str)
                transaction_type = self._determine_transaction_type(amount, description)
                
                # Armazena o valor absoluto na transação
                amount = abs(amount)

                # Extrai o saldo após a transação, se disponível
                balance_after = None
                if balance_col and balance_col in df.columns:
                    balance_str = str(row[balance_col]).strip()
                    balance_after = self._parse_amount(balance_str)

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