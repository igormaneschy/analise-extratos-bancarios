"""
Implementação de leitor de extratos em PDF.
"""
import re
import json
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Tuple
import pdfplumber

from src.domain.models import BankStatement, Transaction, TransactionType
from src.domain.interfaces import StatementReader
from src.domain.exceptions import FileNotSupportedError, ParsingError


class PDFStatementReader(StatementReader):
    # Load configuration from a JSON file
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'pdf_reader_config.json')

    with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
        config = json.load(config_file)

    date_patterns = [
        r"\d{2}/\d{2}/\d{4}",
        r"\d{2}-\d{2}-\d{4}",
        r"\d{4}-\d{2}-\d{2}",
    ]

    amount_patterns = [
        r"-?\d{1,3}(?:\.\d{3})*,\d{2}",  # e.g. 1.234,56 or -1.234,56
        r"-?\d+,\d{2}",  # e.g. 1234,56 or -1234,56
        r"-?\d+\.\d{2}",  # e.g. 1234.56 or -1234.56
    ]

    # Use config for bank names
    bank_name_patterns = config.get('bank_name_patterns', [])

    def __init__(self):
        self.currency = self.config.get('currency', 'EUR')
        self.credit_pattern = self.config.get('credit_pattern', r'\+?\d+(?:[.,]\d+)?')
        self.debit_pattern = self.config.get('debit_pattern', r'-?\d+(?:[.,]\d+)?')

    def can_read(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.pdf'

    def read(self, file_path: Path) -> BankStatement:
        try:
            text = self._extract_text(file_path)
            bank_name = self._extract_bank_name(text)
            account_number = self._extract_account_number(text)
            period = self._extract_period(text)
            initial_balance = self._extract_initial_balance(text)
            final_balance = self._extract_final_balance(text)
            transactions = self._extract_transactions(text)

            # Ajuste para passar period_start e period_end em vez de period
            return BankStatement(
                bank_name=bank_name,
                account_number=account_number,
                period_start=period[0] if period else None,
                period_end=period[1] if period else None,
                initial_balance=initial_balance,
                final_balance=final_balance,
                transactions=transactions
            )
        except Exception as e:
            raise ParsingError(f"Error reading PDF file: {e}")

    def _extract_text(self, file_path: Path) -> str:
        with pdfplumber.open(file_path) as pdf:
            text = '\n'.join(page.extract_text() for page in pdf.pages if page.extract_text())
        return text

    def _extract_bank_name(self, text: str) -> str:
        for pattern in self.bank_name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return "Unknown Bank"

    def _extract_account_number(self, text: str) -> str:
        # Basic pattern, but could be adapted for European format if needed
        patterns = [
            r'account[:\s]+(\w+[-/]?\w*)',
            r'acc[:\s]+(\w+[-/]?\w*)',
            r'iban[:\s]+([A-Z0-9]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""

    def _extract_period(self, text: str) -> Optional[Tuple[datetime, datetime]]:
        # European date period pattern, e.g. "Period: 01.01.2024 - 31.01.2024"
        period_pattern = r'period[:\s]+(\d{2}[./-]\d{2}[./-]\d{4})\s*[-aà]\s*(\d{2}[./-]\d{2}[./-]\d{4})'
        match = re.search(period_pattern, text, re.IGNORECASE)
        if match:
            fmt_guess = '%d.%m.%Y' if '.' in match.group(1) else '%d/%m/%Y'
            try:
                start = datetime.strptime(match.group(1), fmt_guess)
                end = datetime.strptime(match.group(2), fmt_guess)
                return start, end
            except Exception:
                return None
        return None

    def _extract_initial_balance(self, text: str) -> Decimal:
        patterns = [
            rf'opening\s+balance[:\s]+{self.currency}\s*([\d.,]+)',
            rf'balance\s+start[:\s]+{self.currency}\s*([\d.,]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_amount(match.group(1))
        return Decimal('0.00')

    def _extract_final_balance(self, text: str) -> Decimal:
        patterns = [
            rf'closing\s+balance[:\s]+{self.currency}\s*([\d.,]+)',
            rf'balance\s+end[:\s]+{self.currency}\s*([\d.,]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_amount(match.group(1))
        return Decimal('0.00')

    def _extract_transactions(self, text: str) -> List[Transaction]:
        transactions = []
        lines = text.splitlines()
        for line in lines:
            transaction = self._parse_transaction_line(line)
            if transaction:
                transactions.append(transaction)
        return transactions

    def _parse_transaction_line(self, line: str) -> Optional[Transaction]:
        # Skip short lines or headers
        if len(line.strip()) < 10:
            return None

        date_match = None
        for pattern in self.date_patterns:
            date_match = re.search(pattern, line)
            if date_match:
                break
        if not date_match:
            return None

        amount_match = None
        for pattern in self.amount_patterns:
            amount_match = re.search(pattern, line)
            if amount_match:
                break
        if not amount_match:
            return None

        amount_str = amount_match.group(0)
        amount = self._parse_amount(amount_str)

        # Determine credit or debit using config patterns
        if re.match(self.credit_pattern, amount_str):
            transaction_type = TransactionType.CREDIT
        elif re.match(self.debit_pattern, amount_str):
            transaction_type = TransactionType.DEBIT
        else:
            transaction_type = TransactionType.DEBIT if amount < 0 else TransactionType.CREDIT

        # Extract description (remove date and amount)
        description = line.replace(date_match.group(0), '').replace(amount_str, '').strip()

        # Parse date to datetime object
        try:
            date_str = date_match.group(0)
            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                date_obj = datetime.now()
        except Exception:
            date_obj = datetime.now()

        return Transaction(
            date=date_obj,
            description=description,
            amount=abs(amount),
            type=transaction_type
        )

    def _parse_amount(self, amount_str: str) -> Decimal:
        # Normalize European format: remove thousand separator '.', replace decimal ',' with '.'
        normalized = amount_str.replace('.', '').replace(',', '.').replace(' ', '')
        try:
            return Decimal(normalized)
        except Exception:
            return Decimal('0.0')