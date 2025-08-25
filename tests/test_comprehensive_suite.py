#!/usr/bin/env python3
"""
Suite de testes abrangente para o projeto de análise de extratos bancários
"""

import sys
import os
import pytest
from decimal import Decimal
from datetime import datetime
import uuid

# Adiciona o diretório raiz ao path para imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_domain_models():
    """Testa os modelos do domínio"""
    from src.domain.models import Transaction, TransactionType, BankStatement, AnalysisResult, TransactionCategory
    
    # Testa criação de transação
    transaction = Transaction(
        date=datetime.now(),
        description="Test transaction",
        amount=Decimal("100.50"),
        type=TransactionType.DEBIT
    )
    
    assert transaction.amount == Decimal("100.50")
    assert transaction.type == TransactionType.DEBIT
    
    # Testa criação de extrato bancário
    statement = BankStatement(
        bank_name="Test Bank",
        account_number="12345-6",
        period_start=datetime.now(),
        period_end=datetime.now(),
        initial_balance=Decimal("1000.00"),
        final_balance=Decimal("1100.50"),
        transactions=[transaction],
        currency="EUR"  # Testa novo campo de moeda
    )
    
    assert statement.bank_name == "Test Bank"
    assert statement.currency == "EUR"
    assert len(statement.transactions) == 1
    
    # Testa criação de resultado de análise
    analysis_result = AnalysisResult(
        statement_id=str(uuid.uuid4()),
        total_income=Decimal("1500.00"),
        total_expenses=Decimal("1200.00"),
        net_flow=Decimal("300.00"),
        currency="EUR",  # Testa novo campo de moeda
        categories_summary={TransactionCategory.NAO_CATEGORIZADO: Decimal("300.00")},
        monthly_summary={"2023-01": {"income": Decimal("1500.00"), "expenses": Decimal("1200.00")}},
        metadata={},
        alerts=[],
        insights=[]
    )
    
    assert analysis_result.total_income == Decimal("1500.00")
    assert analysis_result.currency == "EUR"

def test_pdf_reader_import():
    """Testa se o leitor PDF pode ser importado"""
    try:
        from src.infrastructure.readers.pdf_reader import PDFStatementReader
        reader = PDFStatementReader()
        assert reader is not None
    except Exception as e:
        pytest.fail(f"Falha ao importar ou instanciar PDFStatementReader: {e}")

def test_excel_reader_currency_detection():
    """Testa se o leitor Excel detecta moeda corretamente"""
    try:
        from src.infrastructure.readers.excel_reader import ExcelStatementReader
        reader = ExcelStatementReader()
        assert reader is not None
        # Testa que o leitor tem o atributo currency
        assert hasattr(reader, 'currency')
    except Exception as e:
        pytest.fail(f"Falha ao importar ou instanciar ExcelStatementReader: {e}")

def test_categorizer_import():
    """Testa se o categorizador pode ser importado"""
    try:
        from src.infrastructure.categorizers.keyword_categorizer import KeywordCategorizer
        categorizer = KeywordCategorizer()
        assert categorizer is not None
    except Exception as e:
        pytest.fail(f"Falha ao importar ou instanciar KeywordCategorizer: {e}")

def test_analyzer_currency_handling():
    """Testa se o analisador lida corretamente com moedas"""
    try:
        from src.infrastructure.analyzers.basic_analyzer import BasicStatementAnalyzer
        from src.domain.models import BankStatement, Transaction, TransactionType
        from datetime import datetime
        from decimal import Decimal
        
        analyzer = BasicStatementAnalyzer()
        assert analyzer is not None
        
        # Cria um extrato de teste com moeda
        statement = BankStatement(
            bank_name="Test Bank",
            account_number="12345-6",
            period_start=datetime.now(),
            period_end=datetime.now(),
            initial_balance=Decimal("1000.00"),
            final_balance=Decimal("1100.50"),
            transactions=[
                Transaction(
                    date=datetime.now(),
                    description="Test transaction",
                    amount=Decimal("100.50"),
                    type=TransactionType.DEBIT
                )
            ],
            currency="EUR"
        )
        
        # Executa a análise
        result = analyzer.analyze(statement)
        
        # Verifica se a moeda foi propagada corretamente
        assert result.currency == "EUR"
    except Exception as e:
        pytest.fail(f"Falha ao testar BasicStatementAnalyzer com moeda: {e}")

def test_report_generator_import():
    """Testa se o gerador de relatórios pode ser importado"""
    try:
        from src.infrastructure.reports.text_report import TextReportGenerator
        report_generator = TextReportGenerator()
        assert report_generator is not None
    except Exception as e:
        pytest.fail(f"Falha ao importar ou instanciar TextReportGenerator: {e}")

def test_use_case_import():
    """Testa se o caso de uso pode ser importado"""
    try:
        from src.application.use_cases import AnalyzeStatementUseCase
        assert AnalyzeStatementUseCase is not None
    except Exception as e:
        pytest.fail(f"Falha ao importar AnalyzeStatementUseCase: {e}")

def test_main_import():
    """Testa se o módulo principal pode ser importado"""
    try:
        import main
        assert main is not None
    except Exception as e:
        pytest.fail(f"Falha ao importar main: {e}")

if __name__ == "__main__":
    # Executa os testes
    pytest.main([__file__, "-v"])