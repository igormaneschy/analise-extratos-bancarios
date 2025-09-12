"""
Classe base para leitores de extratos bancários.
"""
import re
import decimal
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional
import pandas as pd

from src.domain.models import BankStatement, Transaction, TransactionType
from src.domain.interfaces import StatementReader
from src.domain.exceptions import ParsingError
from src.utils.currency_utils import CurrencyUtils

logger = logging.getLogger(__name__)


class BaseStatementReader(StatementReader):
    """Classe base para leitores de extratos bancários."""
    
    def __init__(self):
        self.currency = "EUR"  # Será detectado automaticamente
        self.bank_name: Optional[str] = None
    
    def _parse_amount(self, value: str) -> Decimal:
        """Converte string para Decimal, tratando diferentes formatos."""
        if pd.isna(value) or value == '':
            logger.debug("Valor vazio ou nulo para parsing de amount")
            return Decimal("0.00")
        
        original_value = str(value).strip()
        if not original_value:
            logger.debug("Valor vazio após strip para parsing de amount")
            return Decimal("0.00")
        
        # Remove caracteres não numéricos exceto ponto, vírgula e sinal
        cleaned = re.sub(r'[^\d.,+-]', '', original_value)
        
        if not cleaned:
            logger.warning(f"Não foi possível extrair números do valor: '{original_value}'")
            return Decimal("0.00")
        
        # Trata vírgula como separador decimal (formato brasileiro/europeu)
        if ',' in cleaned and '.' in cleaned:
            # Formato: 1.234,56
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            # Formato: 1234,56
            cleaned = cleaned.replace(',', '.')
        
        try:
            result = Decimal(cleaned)
            logger.debug(f"Valor '{original_value}' convertido para {result}")
            return result
        except (ValueError, TypeError, decimal.InvalidOperation) as e:
            logger.warning(f"Erro ao converter valor '{original_value}' para Decimal: {e}")
            return Decimal("0.00")
    
    def _parse_date(self, date_str: str) -> datetime:
        """Converte string para datetime, tratando diferentes formatos."""
        if pd.isna(date_str) or date_str == '':
            logger.debug("Data vazia ou nula, usando data atual")
            return datetime.now()
        
        original_date = str(date_str).strip()
        if not original_date:
            logger.debug("Data vazia após strip, usando data atual")
            return datetime.now()
        
        # Formatos comuns
        formats = [
            '%d/%m/%Y',      # 01/01/2023
            '%d-%m-%Y',      # 01-01-2023
            '%Y-%m-%d',      # 2023-01-01
            '%d/%m/%y',      # 01/01/23
            '%d-%m-%y',      # 01-01-23
        ]
        
        for fmt in formats:
            try:
                result = datetime.strptime(original_date, fmt)
                logger.debug(f"Data '{original_date}' convertida para {result} usando formato {fmt}")
                return result
            except ValueError:
                continue
        
        # Se nenhum formato funcionar, tenta usar pandas
        try:
            result = pd.to_datetime(original_date).to_pydatetime()
            logger.debug(f"Data '{original_date}' convertida para {result} usando pandas")
            return result
        except Exception as e:
            logger.warning(f"Erro ao converter data '{original_date}': {e}, usando data atual")
            return datetime.now()
    
    def _determine_transaction_type(self, amount: Decimal, description: str = "") -> TransactionType:
        """Determina o tipo de transação baseado no valor e descrição."""
        # Se o valor é positivo, é crédito (receita)
        if amount > 0:
            return TransactionType.CREDIT
        
        # Se o valor é negativo, é débito (despesa)
        if amount < 0:
            return TransactionType.DEBIT
        
        # Para valor zero, tenta determinar pela descrição
        description_lower = description.lower()
        if any(word in description_lower for word in ['receita', 'entrada', 'deposito', 'credito']):
            return TransactionType.CREDIT
        elif any(word in description_lower for word in ['despesa', 'saida', 'pagamento', 'debito']):
            return TransactionType.DEBIT
        
        # Padrão: valor zero é débito
        return TransactionType.DEBIT
    
    def _extract_bank_name(self, df: pd.DataFrame) -> str:
        """Extrai o nome do banco do DataFrame."""
        # Procura por padrões comuns de nome de banco
        bank_patterns = [
            r'banco\s+(\w+)',
            r'(\w+)\s+banco',
            r'(\w+)\s+bank',
        ]
        
        for col in df.columns:
            for value in df[col].dropna().astype(str):
                for pattern in bank_patterns:
                    match = re.search(pattern, value.lower())
                    if match:
                        return match.group(1).title()
        
        return "Banco Desconhecido"
    
    def _extract_account_number(self, df: pd.DataFrame) -> str:
        """Extrai o número da conta do DataFrame."""
        # Procura por padrões de número de conta
        account_patterns = [
            r'conta[:\s]*(\d+[-.]?\d*)',
            r'account[:\s]*(\d+[-.]?\d*)',
            r'(\d{4,}[-.]?\d*)',  # Números com 4+ dígitos
        ]
        
        for col in df.columns:
            for value in df[col].dropna().astype(str):
                for pattern in account_patterns:
                    match = re.search(pattern, value.lower())
                    if match:
                        return match.group(1)
        
        return "N/A"
    
    def _extract_initial_balance(self, df: pd.DataFrame) -> Decimal:
        """Extrai o saldo inicial do DataFrame."""
        # Procura por padrões de saldo inicial
        balance_patterns = [
            r'saldo\s+inicial[:\s]*([\d.,+-]+)',
            r'initial\s+balance[:\s]*([\d.,+-]+)',
            r'saldo\s+anterior[:\s]*([\d.,+-]+)',
        ]
        
        for col in df.columns:
            for value in df[col].dropna().astype(str):
                for pattern in balance_patterns:
                    match = re.search(pattern, value.lower())
                    if match:
                        return self._parse_amount(match.group(1))
        
        return Decimal("0.00")
    
    def _extract_final_balance(self, df: pd.DataFrame) -> Decimal:
        """Extrai o saldo final do DataFrame."""
        # Procura por padrões de saldo final
        balance_patterns = [
            r'saldo\s+final[:\s]*([\d.,+-]+)',
            r'final\s+balance[:\s]*([\d.,+-]+)',
            r'saldo\s+atual[:\s]*([\d.,+-]+)',
        ]
        
        for col in df.columns:
            for value in df[col].dropna().astype(str):
                for pattern in balance_patterns:
                    match = re.search(pattern, value.lower())
                    if match:
                        return self._parse_amount(match.group(1))
        
        return Decimal("0.00")
    
    def _extract_start_date(self, transactions: List[Transaction]) -> datetime:
        """Extrai a data de início baseada nas transações."""
        if not transactions:
            return datetime.now()
        return min(transaction.date for transaction in transactions)
    
    def _extract_end_date(self, transactions: List[Transaction]) -> datetime:
        """Extrai a data de fim baseada nas transações."""
        if not transactions:
            return datetime.now()
        return max(transaction.date for transaction in transactions)
    
    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza o DataFrame para processamento."""
        if df is None or df.empty:
            logger.warning("DataFrame vazio ou nulo fornecido para normalização")
            return pd.DataFrame()
        
        logger.debug(f"Normalizando DataFrame com {len(df)} linhas e {len(df.columns)} colunas")
        
        # Remove linhas completamente vazias
        original_rows = len(df)
        df = df.dropna(how='all')
        removed_rows = original_rows - len(df)
        if removed_rows > 0:
            logger.debug(f"Removidas {removed_rows} linhas vazias")
        
        # Converte colunas para string para evitar problemas de tipo
        for col in df.columns:
            try:
                df[col] = df[col].astype(str)
            except Exception as e:
                logger.warning(f"Erro ao converter coluna '{col}' para string: {e}")
                # Se falhar, tenta converter para string de forma mais segura
                df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) else '')
        
        logger.debug(f"DataFrame normalizado com {len(df)} linhas e {len(df.columns)} colunas")
        return df
    
    def _extract_transactions(self, df: pd.DataFrame) -> List[Transaction]:
        """Extrai transações do DataFrame. Deve ser implementado pelas subclasses."""
        raise NotImplementedError("Subclasses devem implementar _extract_transactions")
