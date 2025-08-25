"""
Modelos de domínio para o sistema de análise de extratos bancários.
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import uuid4


class TransactionType(Enum):
    """Tipos de transação bancária."""
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
    
    
class TransactionCategory(Enum):
    """Categorias de transação."""
    ALIMENTACAO = "ALIMENTACAO"
    TRANSPORTE = "TRANSPORTE"
    MORADIA = "MORADIA"
    SAUDE = "SAUDE"
    EDUCACAO = "EDUCACAO"
    LAZER = "LAZER"
    COMPRAS = "COMPRAS"
    SERVICOS = "SERVICOS"
    TRANSFERENCIA = "TRANSFERENCIA"
    INVESTIMENTO = "INVESTIMENTO"
    SALARIO = "SALARIO"
    OUTROS = "OUTROS"
    NAO_CATEGORIZADO = "NAO_CATEGORIZADO"


@dataclass
class Transaction:
    """Representa uma transação bancária."""
    id: str = field(default_factory=lambda: str(uuid4()))
    date: datetime = field(default_factory=datetime.now)
    description: str = ""
    amount: Decimal = Decimal("0.00")
    type: TransactionType = TransactionType.DEBIT
    category: TransactionCategory = TransactionCategory.NAO_CATEGORIZADO
    balance_after: Optional[Decimal] = None
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validações após inicialização."""
        if isinstance(self.amount, (int, float)):
            self.amount = Decimal(str(self.amount))
        if self.balance_after and isinstance(self.balance_after, (int, float)):
            self.balance_after = Decimal(str(self.balance_after))
            
    @property
    def is_income(self) -> bool:
        """Verifica se é uma receita."""
        return self.type == TransactionType.CREDIT
    
    @property
    def is_expense(self) -> bool:
        """Verifica se é uma despesa."""
        return self.type == TransactionType.DEBIT


@dataclass
class BankStatement:
    """Representa um extrato bancário."""
    id: str = field(default_factory=lambda: str(uuid4()))
    bank_name: str = ""
    account_number: str = ""
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
    initial_balance: Decimal = Decimal("0.00")
    final_balance: Decimal = Decimal("0.00")
    currency: str = "EUR"  # Moeda padrão
    transactions: List[Transaction] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validações após inicialização."""
        if isinstance(self.initial_balance, (int, float)):
            self.initial_balance = Decimal(str(self.initial_balance))
        if isinstance(self.final_balance, (int, float)):
            self.final_balance = Decimal(str(self.final_balance))
    
    @property
    def total_income(self) -> Decimal:
        """Calcula o total de receitas."""
        return sum(
            t.amount for t in self.transactions 
            if t.is_income
        )
    
    @property
    def total_expenses(self) -> Decimal:
        """Calcula o total de despesas."""
        return sum(
            t.amount for t in self.transactions 
            if t.is_expense
        )
    
    @property
    def net_flow(self) -> Decimal:
        """Calcula o fluxo líquido (receitas - despesas)."""
        return self.total_income - self.total_expenses
    
    @property
    def transaction_count(self) -> int:
        """Retorna o número de transações."""
        return len(self.transactions)
    
    def add_transaction(self, transaction: Transaction) -> None:
        """Adiciona uma transação ao extrato."""
        self.transactions.append(transaction)
        
    def get_transactions_by_category(self, category: TransactionCategory) -> List[Transaction]:
        """Retorna transações de uma categoria específica."""
        return [t for t in self.transactions if t.category == category]
    
    def get_transactions_by_date_range(self, start: datetime, end: datetime) -> List[Transaction]:
        """Retorna transações em um período específico."""
        return [
            t for t in self.transactions 
            if start <= t.date <= end
        ]


@dataclass
class AnalysisResult:
    """Resultado da análise de um extrato."""
    statement_id: str
    total_income: Decimal
    total_expenses: Decimal
    net_flow: Decimal
    currency: str  # Moeda do extrato
    categories_summary: dict[TransactionCategory, Decimal]
    monthly_summary: dict[str, dict[str, Decimal]]
    alerts: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)