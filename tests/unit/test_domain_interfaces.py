"""
Testes para as interfaces do domínio.
"""
import pytest
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

# Importando os modelos necessários
from src.domain.models import BankStatement, Transaction, AnalysisResult, TransactionCategory

# Importando as interfaces
from src.domain.interfaces import (
    StatementReader,
    TransactionParser,
    StatementAnalyzer,
    ReportGenerator,
    TransactionCategorizer
)

# Importando implementações concretas para testar as interfaces
from src.infrastructure.readers.pdf_reader import PDFStatementReader
from src.infrastructure.readers.excel_reader import ExcelStatementReader
from src.infrastructure.readers.csv_reader import CSVStatementReader
from src.infrastructure.analyzers.basic_analyzer import BasicStatementAnalyzer
from src.infrastructure.reports.text_report import TextReportGenerator
from src.infrastructure.categorizers.keyword_categorizer import KeywordCategorizer


# Implementações de teste simples para melhorar a cobertura
class TestStatementReaderImpl(StatementReader):
    """Implementação de teste para StatementReader."""
    
    def can_read(self, file_path: Path) -> bool:
        return True
    
    def read(self, file_path: Path) -> BankStatement:
        return BankStatement(transactions=[])


class TestTransactionParserImpl(TransactionParser):
    """Implementação de teste para TransactionParser."""
    
    def parse(self, raw_data: str) -> List[Transaction]:
        return []


class TestStatementAnalyzerImpl(StatementAnalyzer):
    """Implementação de teste para StatementAnalyzer."""
    
    def analyze(self, statement: BankStatement) -> AnalysisResult:
        return AnalysisResult(
            statement_id=statement.id,
            total_income=Decimal("0.00"),
            total_expenses=Decimal("0.00"),
            net_flow=Decimal("0.00"),
            currency="EUR",
            categories_summary={},
            monthly_summary={}
        )


class TestReportGeneratorImpl(ReportGenerator):
    """Implementação de teste para ReportGenerator."""
    
    def generate(self, analysis: AnalysisResult, output_path: Optional[Path] = None) -> str:
        return "Test report"


class TestTransactionCategorizerImpl(TransactionCategorizer):
    """Implementação de teste para TransactionCategorizer."""
    
    def categorize(self, transaction: Transaction) -> Transaction:
        return transaction


class TestStatementReaderInterface:
    """Testes para a interface StatementReader."""
    
    def test_statement_reader_is_abstract(self):
        """Verifica se StatementReader é uma classe abstrata."""
        # Verifica se é uma classe abstrata
        assert hasattr(StatementReader, '__abstractmethods__')
        # Verifica se tem os métodos abstratos esperados
        assert 'can_read' in StatementReader.__abstractmethods__
        assert 'read' in StatementReader.__abstractmethods__
    
    def test_statement_reader_implementation(self):
        """Verifica se a implementação de teste funciona."""
        impl = TestStatementReaderImpl()
        assert impl.can_read(Path("test.txt")) == True
        assert isinstance(impl.read(Path("test.txt")), BankStatement)
    
    def test_pdf_statement_reader_implements_interface(self):
        """Verifica se PDFStatementReader implementa StatementReader."""
        # Verifica se é subclasse de StatementReader
        assert issubclass(PDFStatementReader, StatementReader)
        # Verifica se não é abstrata (pode ser instanciada)
        reader = PDFStatementReader()
        assert isinstance(reader, StatementReader)
    
    def test_excel_statement_reader_implements_interface(self):
        """Verifica se ExcelStatementReader implementa StatementReader."""
        # Verifica se é subclasse de StatementReader
        assert issubclass(ExcelStatementReader, StatementReader)
        # Verifica se não é abstrata (pode ser instanciada)
        reader = ExcelStatementReader()
        assert isinstance(reader, StatementReader)
    
    def test_csv_statement_reader_implements_interface(self):
        """Verifica se CSVStatementReader implementa StatementReader."""
        # Verifica se é subclasse de StatementReader
        assert issubclass(CSVStatementReader, StatementReader)
        # Verifica se não é abstrata (pode ser instanciada)
        reader = CSVStatementReader()
        assert isinstance(reader, StatementReader)


class TestTransactionParserInterface:
    """Testes para a interface TransactionParser."""
    
    def test_transaction_parser_is_abstract(self):
        """Verifica se TransactionParser é uma classe abstrata."""
        # Verifica se é uma classe abstrata
        assert hasattr(TransactionParser, '__abstractmethods__')
        # Verifica se tem o método abstrato esperado
        assert 'parse' in TransactionParser.__abstractmethods__
    
    def test_transaction_parser_implementation(self):
        """Verifica se a implementação de teste funciona."""
        impl = TestTransactionParserImpl()
        result = impl.parse("test data")
        assert isinstance(result, list)
        assert len(result) == 0


class TestStatementAnalyzerInterface:
    """Testes para a interface StatementAnalyzer."""
    
    def test_statement_analyzer_is_abstract(self):
        """Verifica se StatementAnalyzer é uma classe abstrata."""
        # Verifica se é uma classe abstrata
        assert hasattr(StatementAnalyzer, '__abstractmethods__')
        # Verifica se tem o método abstrato esperado
        assert 'analyze' in StatementAnalyzer.__abstractmethods__
    
    def test_statement_analyzer_implementation(self):
        """Verifica se a implementação de teste funciona."""
        impl = TestStatementAnalyzerImpl()
        statement = BankStatement(transactions=[])
        result = impl.analyze(statement)
        assert isinstance(result, AnalysisResult)
        assert result.statement_id == statement.id
    
    def test_basic_statement_analyzer_implements_interface(self):
        """Verifica se BasicStatementAnalyzer implementa StatementAnalyzer."""
        # Verifica se é subclasse de StatementAnalyzer
        assert issubclass(BasicStatementAnalyzer, StatementAnalyzer)
        # Verifica se não é abstrata (pode ser instanciada)
        analyzer = BasicStatementAnalyzer()
        assert isinstance(analyzer, StatementAnalyzer)


class TestReportGeneratorInterface:
    """Testes para a interface ReportGenerator."""
    
    def test_report_generator_is_abstract(self):
        """Verifica se ReportGenerator é uma classe abstrata."""
        # Verifica se é uma classe abstrata
        assert hasattr(ReportGenerator, '__abstractmethods__')
        # Verifica se tem o método abstrato esperado
        assert 'generate' in ReportGenerator.__abstractmethods__
    
    def test_report_generator_implementation(self):
        """Verifica se a implementação de teste funciona."""
        impl = TestReportGeneratorImpl()
        statement = BankStatement(transactions=[])
        analysis = AnalysisResult(
            statement_id=statement.id,
            total_income=Decimal("0.00"),
            total_expenses=Decimal("0.00"),
            net_flow=Decimal("0.00"),
            currency="EUR",
            categories_summary={},
            monthly_summary={}
        )
        result = impl.generate(analysis)
        assert isinstance(result, str)
        assert result == "Test report"
    
    def test_text_report_generator_implements_interface(self):
        """Verifica se TextReportGenerator implementa ReportGenerator."""
        # Verifica se é subclasse de ReportGenerator
        assert issubclass(TextReportGenerator, ReportGenerator)
        # Verifica se não é abstrata (pode ser instanciada)
        generator = TextReportGenerator()
        assert isinstance(generator, ReportGenerator)


class TestTransactionCategorizerInterface:
    """Testes para a interface TransactionCategorizer."""
    
    def test_transaction_categorizer_is_abstract(self):
        """Verifica se TransactionCategorizer é uma classe abstrata."""
        # Verifica se é uma classe abstrata
        assert hasattr(TransactionCategorizer, '__abstractmethods__')
        # Verifica se tem o método abstrato esperado
        assert 'categorize' in TransactionCategorizer.__abstractmethods__
    
    def test_transaction_categorizer_implementation(self):
        """Verifica se a implementação de teste funciona."""
        impl = TestTransactionCategorizerImpl()
        transaction = Transaction(
            date=datetime.now(),
            description="Test transaction",
            amount=Decimal("100.00")
        )
        result = impl.categorize(transaction)
        assert isinstance(result, Transaction)
        assert result == transaction
    
    def test_keyword_categorizer_implements_interface(self):
        """Verifica se KeywordCategorizer implementa TransactionCategorizer."""
        # Verifica se é subclasse de TransactionCategorizer
        assert issubclass(KeywordCategorizer, TransactionCategorizer)
        # Verifica se não é abstrata (pode ser instanciada)
        categorizer = KeywordCategorizer()
        assert isinstance(categorizer, TransactionCategorizer)