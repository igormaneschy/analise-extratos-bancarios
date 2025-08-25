"""
Testes abrangentes para o sistema de análise de extratos.
"""
import sys
import os
from datetime import datetime
from decimal import Decimal
import pytest
import uuid

# Adiciona o diretório raiz ao path para importações
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Testes de modelos de domínio
def test_domain_models():
    """Testa a criação de modelos de domínio."""
    from src.domain.models import Transaction, BankStatement, AnalysisResult, TransactionType, TransactionCategory
    
    # Testa criação de transação
    transaction = Transaction(
        id=str(uuid.uuid4()),
        date=datetime.now(),
        description="Test transaction",
        amount=Decimal("100.50"),
        type=TransactionType.CREDIT,
        category=TransactionCategory.SALARIO
    )
    
    assert transaction.description == "Test transaction"
    assert transaction.amount == Decimal("100.50")
    assert transaction.type == TransactionType.CREDIT
    assert transaction.category == TransactionCategory.SALARIO
    assert transaction.is_income == True
    assert transaction.is_expense == False
    
    # Testa criação de extrato bancário
    statement = BankStatement(
        id=str(uuid.uuid4()),
        bank_name="Banco Teste",
        account_number="12345-6",
        period_start=datetime.now(),
        period_end=datetime.now(),
        initial_balance=Decimal("1000.00"),
        final_balance=Decimal("1500.00"),
        currency="EUR",
        transactions=[transaction]
    )
    
    assert statement.bank_name == "Banco Teste"
    assert statement.account_number == "12345-6"
    assert statement.currency == "EUR"
    assert len(statement.transactions) == 1
    
    # Testa cálculo de totais
    assert statement.total_income == Decimal("100.50")
    assert statement.total_expenses == Decimal("0.00")

def test_pdf_reader_import():
    """Testa a importação do leitor de PDF."""
    try:
        from src.infrastructure.readers.pdf_reader import PDFStatementReader
        reader = PDFStatementReader()
        assert reader is not None
    except ImportError:
        pytest.fail("Não foi possível importar PDFStatementReader")

def test_excel_reader_currency_detection():
    """Testa a detecção de moeda no leitor de Excel."""
    try:
        from src.infrastructure.readers.excel_reader import ExcelStatementReader
        reader = ExcelStatementReader()
        assert hasattr(reader, 'currency')
    except ImportError:
        pytest.fail("Não foi possível importar ExcelStatementReader")

def test_csv_reader_import():
    """Testa a importação do leitor de CSV."""
    try:
        from src.infrastructure.readers.csv_reader import CSVStatementReader
        reader = CSVStatementReader()
        assert reader is not None
        # Testa se o leitor pode ler arquivos CSV
        from pathlib import Path
        assert reader.can_read(Path("test.csv")) == True
        assert reader.can_read(Path("test.xlsx")) == False
    except ImportError:
        pytest.fail("Não foi possível importar CSVStatementReader")

def test_categorizer_import():
    """Testa a importação do categorizador."""
    try:
        from src.infrastructure.categorizers.keyword_categorizer import KeywordCategorizer
        categorizer = KeywordCategorizer()
        assert categorizer is not None
    except ImportError:
        pytest.fail("Não foi possível importar KeywordCategorizer")

def test_analyzer_currency_handling():
    """Testa o tratamento de moeda no analisador."""
    try:
        from src.infrastructure.analyzers.basic_analyzer import BasicStatementAnalyzer
        from src.domain.models import BankStatement, Transaction, TransactionType, AnalysisResult
        
        analyzer = BasicStatementAnalyzer()
        
        # Cria um extrato de exemplo com moeda
        statement = BankStatement(
            currency="USD",
            transactions=[
                Transaction(
                    amount=Decimal("100.00"),
                    type=TransactionType.CREDIT
                )
            ]
        )
        
        # Analisa o extrato
        result = analyzer.analyze(statement)
        
        # Verifica se a moeda foi preservada
        assert result.currency == "USD"
        
    except ImportError:
        pytest.fail("Não foi possível importar BasicStatementAnalyzer")

def test_report_generator_import():
    """Testa a importação do gerador de relatórios."""
    try:
        from src.infrastructure.reports.text_report import TextReportGenerator
        generator = TextReportGenerator()
        assert generator is not None
    except ImportError:
        pytest.fail("Não foi possível importar TextReportGenerator")

def test_use_case_import():
    """Testa a importação do caso de uso."""
    try:
        from src.application.use_cases import AnalyzeStatementUseCase
        assert AnalyzeStatementUseCase is not None
    except ImportError:
        pytest.fail("Não foi possível importar AnalyzeStatementUseCase")

def test_main_import():
    """Testa a importação do módulo principal."""
    try:
        import main
        assert main is not None
    except ImportError:
        pytest.fail("Não foi possível importar main")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])