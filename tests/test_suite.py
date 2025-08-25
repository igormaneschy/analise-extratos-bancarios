#!/usr/bin/env python3
"""
Suite de testes básica para o projeto de análise de extratos bancários
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

def test_imports():
    """Testa se os principais módulos podem ser importados"""
    try:
        import main
        assert True
    except Exception as e:
        pytest.fail(f"Falha ao importar main: {e}")
    
    try:
        from src.domain import models
        assert True
    except Exception as e:
        pytest.fail(f"Falha ao importar src.domain.models: {e}")
    
    try:
        from src.infrastructure.readers.pdf_reader import PDFStatementReader
        assert True
    except Exception as e:
        pytest.fail(f"Falha ao importar PDFStatementReader: {e}")

def test_model_creation():
    """Testa a criação de modelos básicos"""
    try:
        from src.domain.models import Transaction, TransactionType, BankStatement, AnalysisResult, TransactionCategory
        from decimal import Decimal
        from datetime import datetime
        
        # Testa criação de uma transação simples
        transaction = Transaction(
            date=datetime.now(),
            description="Test transaction",
            amount=Decimal("100.50"),
            type=TransactionType.DEBIT
        )
        
        assert transaction.amount == Decimal("100.50")
        assert transaction.type == TransactionType.DEBIT
        
        # Testa criação de um extrato bancário com moeda
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
        
        # Testa criação de um resultado de análise com moeda
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
    except Exception as e:
        pytest.fail(f"Falha ao criar modelo: {e}")

if __name__ == "__main__":
    # Executa os testes
    pytest.main([__file__, "-v"])