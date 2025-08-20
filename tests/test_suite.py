#!/usr/bin/env python3
"""
Suite de testes básica para o projeto de análise de extratos bancários
"""

import sys
import os
import pytest

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
        from src.domain.models import Transaction, TransactionType
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
    except Exception as e:
        pytest.fail(f"Falha ao criar modelo: {e}")

if __name__ == "__main__":
    # Executa os testes
    pytest.main([__file__, "-v"])