"""
Interfaces (protocolos) do domínio.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

from src.domain.models import BankStatement, Transaction, AnalysisResult


class StatementReader(ABC):
    """Interface para leitores de extratos."""
    
    @abstractmethod
    def can_read(self, file_path: Path) -> bool:
        """Verifica se pode ler o arquivo."""
        pass
    
    @abstractmethod
    def read(self, file_path: Path) -> BankStatement:
        """Lê o arquivo e retorna um extrato."""
        pass


class StatementAnalyzer(ABC):
    """Interface para analisadores de extratos."""
    
    @abstractmethod
    def analyze(self, statement: BankStatement) -> AnalysisResult:
        """Analisa um extrato e retorna resultados."""
        pass


class ReportGenerator(ABC):
    """Interface para geradores de relatórios."""
    
    @abstractmethod
    def generate(self, analysis: AnalysisResult, output_path: Optional[Path] = None) -> str:
        """Gera relatório a partir da análise."""
        pass


class TransactionCategorizer(ABC):
    """Interface para categorizadores de transações."""
    
    @abstractmethod
    def categorize(self, transaction: Transaction) -> Transaction:
        """Categoriza uma transação."""
        pass