"""
Testes unitários para o BasicStatementAnalyzer.
"""
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import pytest

# Adiciona o diretório raiz ao path para imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.infrastructure.analyzers.basic_analyzer import BasicStatementAnalyzer
from src.domain.models import BankStatement, Transaction, TransactionType, TransactionCategory


def make_tx(date, desc, amount, ttype, category):
    return Transaction(
        date=date,
        description=desc,
        amount=Decimal(str(amount)),
        type=ttype,
        category=category,
    )


def test_basic_analyzer_summaries_and_currency():
    analyzer = BasicStatementAnalyzer()

    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 31)

    txs = [
        make_tx(start + timedelta(days=1), "Salário", 2000, TransactionType.CREDIT, TransactionCategory.SALARIO),
        make_tx(start + timedelta(days=2), "Mercado", 300, TransactionType.DEBIT, TransactionCategory.ALIMENTACAO),
        make_tx(start + timedelta(days=3), "Transporte", 150, TransactionType.DEBIT, TransactionCategory.TRANSPORTE),
    ]

    statement = BankStatement(
        period_start=start,
        period_end=end,
        initial_balance=Decimal("1000.00"),
        final_balance=Decimal("2550.00"),
        currency="EUR",
        transactions=txs,
    )

    result = analyzer.analyze(statement)

    assert result.currency == "EUR"
    assert result.total_income == Decimal("2000")
    assert result.total_expenses == Decimal("450")
    assert result.net_flow == Decimal("1550")

    # categories_summary deve conter apenas despesas, somadas por categoria
    assert result.categories_summary.get(TransactionCategory.ALIMENTACAO) == Decimal("300")
    assert result.categories_summary.get(TransactionCategory.TRANSPORTE) == Decimal("150")

    # monthly_summary deve conter chaves no formato YYYY-MM e saldos
    key = start.strftime("%Y-%m")
    assert key in result.monthly_summary
    assert result.monthly_summary[key]["income"] == Decimal("2000")
    assert result.monthly_summary[key]["expenses"] == Decimal("450")
    assert result.monthly_summary[key]["balance"] == Decimal("1550")


def test_basic_analyzer_alerts_conditions():
    analyzer = BasicStatementAnalyzer()

    start = datetime(2024, 2, 1)
    end = datetime(2024, 2, 28)

    # Despesas superam receitas (gera alerta de déficit)
    expenses = [
        make_tx(start + timedelta(days=i+1), f"Despesa {i}", amt, TransactionType.DEBIT, TransactionCategory.ALIMENTACAO)
        for i, amt in enumerate([100, 200, 300, 400])
    ]
    income = [make_tx(start + timedelta(days=10), "Salário", 500, TransactionType.CREDIT, TransactionCategory.SALARIO)]

    # Uma despesa muito alta para disparar alerta > 3x média
    expenses.append(make_tx(start + timedelta(days=15), "Compra cara", 2000, TransactionType.DEBIT, TransactionCategory.COMPRAS))

    # Muitas não categorizadas para disparar alerta >30%
    uncategorized = [
        make_tx(start + timedelta(days=20+i), f"NC {i}", 10, TransactionType.DEBIT, TransactionCategory.NAO_CATEGORIZADO)
        for i in range(5)
    ]

    statement = BankStatement(
        period_start=start,
        period_end=end,
        currency="BRL",
        transactions=income + expenses + uncategorized,
    )

    result = analyzer.analyze(statement)

    # Deve haver pelo menos 3 tipos de alertas distintos
    joined = "\n".join(result.alerts)
    assert any("Despesas superaram receitas" in a for a in result.alerts)
    assert any("representam" in a for a in result.alerts)  # alta concentração em ALIMENTACAO ou COMPRAS
    assert any("Transação de alto valor" in a for a in result.alerts)
    assert any("não foram categorizadas" in a for a in result.alerts)


def test_basic_analyzer_insights_conditions():
    analyzer = BasicStatementAnalyzer()

    start = datetime(2024, 3, 1)
    end = datetime(2024, 3, 31)

    # Muitas despesas para habilitar insight de mediana/distribuição
    expenses = [
        make_tx(start + timedelta(days=i+1), f"Despesa {i}", 50 + i, TransactionType.DEBIT, TransactionCategory.ALIMENTACAO)
        for i in range(12)
    ]
    income = [make_tx(start + timedelta(days=1), "Salário", 5000, TransactionType.CREDIT, TransactionCategory.SALARIO)]

    statement = BankStatement(
        period_start=start,
        period_end=end,
        currency="USD",
        transactions=income + expenses,
    )

    result = analyzer.analyze(statement)

    # Deve conter insights sobre: maior categoria, média diária, distribuição mediana, frequência e potencial de economia
    joined = "\n".join(result.insights)
    assert any("Maior categoria de gastos" in i for i in result.insights)
    assert any("Média diária de gastos" in i for i in result.insights)
    assert any("são menores que" in i for i in result.insights)
    assert any("transações por dia" in i for i in result.insights)
    assert any("Potencial de economia" in i for i in result.insights)
