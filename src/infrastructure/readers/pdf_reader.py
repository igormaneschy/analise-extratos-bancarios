"""
Implementação de leitor de extratos em PDF.
"""
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Tuple
import pdfplumber

from src.domain.models import BankStatement, Transaction, TransactionType
from src.domain.interfaces import StatementReader
from src.domain.exceptions import FileNotSupportedError, ParsingError


class PDFStatementReader(StatementReader):
    """Leitor de extratos bancários em PDF."""
    
    def __init__(self):
        self.date_patterns = [
            r'(\d{2})/(\d{2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{2})-(\d{2})-(\d{4})',  # DD-MM-YYYY
            r'(\d{2})/(\d{2})',           # DD/MM (ano atual)
        ]
        
        self.amount_patterns = [
            r'R\$\s*([\d.,]+)',           # R$ 1.234,56
            r'([\d.,]+)\s*[CD]',          # 1.234,56 C ou D
            r'([-]?[\d.,]+)',             # -1.234,56 ou 1.234,56
        ]
    
    def can_read(self, file_path: Path) -> bool:
        """Verifica se pode ler o arquivo."""
        return file_path.suffix.lower() == '.pdf'
    
    def read(self, file_path: Path) -> BankStatement:
        """Lê o PDF e extrai as informações do extrato."""
        if not self.can_read(file_path):
            raise FileNotSupportedError(f"Arquivo {file_path} não é um PDF")
        
        try:
            text = self._extract_text(file_path)
            statement = BankStatement()
            
            # Extrair informações básicas
            statement.bank_name = self._extract_bank_name(text)
            statement.account_number = self._extract_account_number(text)
            
            # Extrair período
            period = self._extract_period(text)
            if period:
                statement.period_start, statement.period_end = period
            
            # Extrair saldos
            statement.initial_balance = self._extract_initial_balance(text)
            statement.final_balance = self._extract_final_balance(text)
            
            # Extrair transações
            transactions = self._extract_transactions(text)
            statement.transactions = transactions
            
            return statement
            
        except Exception as e:
            raise ParsingError(f"Erro ao processar PDF: {str(e)}")
    
    def _extract_text(self, file_path: Path) -> str:
        """Extrai todo o texto do PDF."""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    
    def _extract_bank_name(self, text: str) -> str:
        """Tenta identificar o nome do banco."""
        # Padrões comuns de bancos brasileiros
        bank_patterns = {
            'Banco do Brasil': r'banco\s+do\s+brasil',
            'Bradesco': r'bradesco',
            'Itaú': r'ita[uú]',
            'Santander': r'santander',
            'Caixa': r'caixa\s+econ[oô]mica',
            'Nubank': r'nubank',
            'Inter': r'banco\s+inter',
        }
        
        text_lower = text.lower()
        for bank_name, pattern in bank_patterns.items():
            if re.search(pattern, text_lower):
                return bank_name
        
        return "Banco não identificado"
    
    def _extract_account_number(self, text: str) -> str:
        """Extrai número da conta."""
        # Padrões comuns: Conta: 12345-6, Ag/Conta: 1234/12345-6
        patterns = [
            r'conta[:\s]+(\d+[-]?\d*)',
            r'ag[/\s]+conta[:\s]+\d+[/\s]+(\d+[-]?\d*)',
            r'c/c[:\s]+(\d+[-]?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_period(self, text: str) -> Optional[Tuple[datetime, datetime]]:
        """Extrai período do extrato."""
        # Procura por padrões como "Período: 01/01/2024 a 31/01/2024"
        period_pattern = r'per[ií]odo[:\s]+(\d{2}/\d{2}/\d{4})\s+[aà]\s+(\d{2}/\d{2}/\d{4})'
        match = re.search(period_pattern, text, re.IGNORECASE)
        
        if match:
            start_str = match.group(1)
            end_str = match.group(2)
            
            start = datetime.strptime(start_str, '%d/%m/%Y')
            end = datetime.strptime(end_str, '%d/%m/%Y')
            
            return start, end
        
        return None
    
    def _extract_initial_balance(self, text: str) -> Decimal:
        """Extrai saldo inicial."""
        patterns = [
            r'saldo\s+anterior[:\s]+R\$\s*([\d.,]+)',
            r'saldo\s+inicial[:\s]+R\$\s*([\d.,]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_amount(match.group(1))
        
        return Decimal('0.00')
    
    def _extract_final_balance(self, text: str) -> Decimal:
        """Extrai saldo final."""
        patterns = [
            r'saldo\s+final[:\s]+R\$\s*([\d.,]+)',
            r'saldo\s+atual[:\s]+R\$\s*([\d.,]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_amount(match.group(1))
        
        return Decimal('0.00')
    
    def _extract_transactions(self, text: str) -> List[Transaction]:
        """Extrai transações do texto."""
        transactions = []
        lines = text.split('\n')
        
        for line in lines:
            transaction = self._parse_transaction_line(line)
            if transaction:
                transactions.append(transaction)
        
        return transactions
    
    def _parse_transaction_line(self, line: str) -> Optional[Transaction]:
        """Tenta fazer parse de uma linha como transação."""
        # Pula linhas muito curtas ou cabeçalhos
        if len(line.strip()) < 10:
            return None
            
        # Procura por data
        date_match = None
        for pattern in self.date_patterns:
            date_match = re.search(pattern, line)
            if date_match:
                break
        
        if not date_match:
            return None
        
        # Procura por valor
        amount_match = None
        for pattern in self.amount_patterns:
            amount_match = re.search(pattern, line)
            if amount_match:
                break
        
        if not amount_match:
            return None
        
        try:
            # Parse da data
            if len(date_match.groups()) == 3:
                day, month, year = date_match.groups()
                date = datetime(int(year), int(month), int(day))
            else:
                day, month = date_match.groups()
                date = datetime(datetime.now().year, int(month), int(day))
            
            # Parse do valor
            amount = self._parse_amount(amount_match.group(1))

            # Determina tipo (débito/crédito)
            # Verifica se há indicação explícita de C (crédito) ou D (débito)
            if ' C ' in line or ' C' in line or 'C ' in amount_match.group(0):
                trans_type = TransactionType.CREDIT
            elif ' D ' in line or ' D' in line or 'D ' in amount_match.group(0):
                trans_type = TransactionType.DEBIT
            else:
                # Se não há indicação explícita, usa o sinal do valor
                trans_type = TransactionType.DEBIT if amount < 0 else TransactionType.CREDIT

            # Garante que o valor seja sempre positivo
            amount = abs(amount)
            
            # Extrai descrição (remove data e valor)
            description = line
            description = description.replace(date_match.group(0), '')
            description = description.replace(amount_match.group(0), '')
            description = ' '.join(description.split())
            
            return Transaction(
                date=date,
                description=description,
                amount=amount,
                type=trans_type
            )
            
        except Exception:
            return None
    
    def _parse_amount(self, amount_str: str) -> Decimal:
        """Converte string de valor para Decimal."""
        # Remove espaços e R$
        amount_str = amount_str.strip().replace('R$', '').replace(' ', '')
        
        # Troca vírgula por ponto
        amount_str = amount_str.replace('.', '').replace(',', '.')
        
        try:
            return Decimal(amount_str)
        except:
            return Decimal('0.00')