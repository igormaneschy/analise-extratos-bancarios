"""
Testes unitários para o TextReportGenerator (relatório de texto).
"""
import sys
import os
from decimal import Decimal
from datetime import datetime
from pathlib import Path

# Adiciona o diretório raiz ao path para imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.infrastructure.reports.text_report import TextReportGenerator
from src.domain.models import AnalysisResult, TransactionCategory


def make_analysis_result():
    categories = {
        TransactionCategory.ALIMENTACAO: Decimal("300.00"),
        TransactionCategory.TRANSPORTE: Decimal("150.00"),
    }
    monthly = {
        "2024-01": {"income": Decimal("2000.00"), "expenses": Decimal("450.00"), "balance": Decimal("1550.00")}
    }
    alerts = [
        "⚠️ Atenção: Despesas superaram receitas em € 100.00",
        "⚠️ Gastos com ALIMENTACAO representam 66.7% do total",
    ]
    insights = [
        "💡 Maior categoria de gastos: ALIMENTACAO (€ 300.00 - 66.7%)",
        "💡 Média diária de gastos: € 15.00",
    ]

    return AnalysisResult(
        statement_id="abc",
        total_income=Decimal("2000.00"),
        total_expenses=Decimal("450.00"),
        net_flow=Decimal("1550.00"),
        currency="EUR",
        categories_summary=categories,
        monthly_summary=monthly,
        alerts=alerts,
        insights=insights,
        metadata={"transaction_count": 3, "period_days": 30},
    )


def test_text_report_contains_sections_and_values(tmp_path):
    generator = TextReportGenerator()
    analysis = make_analysis_result()

    content = generator.generate(analysis)

    # Cabeçalho e seções principais
    assert "RELATÓRIO DE ANÁLISE DE EXTRATO BANCÁRIO" in content
    assert "RESUMO FINANCEIRO" in content
    assert "DESPESAS POR CATEGORIA" in content
    assert "RESUMO MENSAL" in content
    assert "ALERTAS" in content
    assert "INSIGHTS E RECOMENDAÇÕES" in content
    assert "INFORMAÇÕES ADICIONAIS" in content
    assert "Fim do Relatório" in content

    # Valores formatados com moeda
    assert "€" in content
    assert "Total de Receitas:" in content
    assert "Total de Despesas:" in content
    assert "Saldo do Período:" in content

    # Categorias aparecem legíveis
    assert "Alimentacao" in content or "Alimentação" in content
    assert "Transporte" in content

    # Resumo mensal formatado
    assert "Jan/2024" in content  # strftime('%b/%Y') pode retornar 'Jan/2024'

    # Alertas e insights propagados
    for a in analysis.alerts:
        assert a in content
    for i in analysis.insights:
        assert i in content

    # Metadados
    assert "Total de transações: 3" in content
    assert "Período analisado: 30 dias" in content


def test_text_report_writes_to_file(tmp_path):
    generator = TextReportGenerator()
    analysis = make_analysis_result()

    out = tmp_path / "report.txt"
    content = generator.generate(analysis, output_path=out)

    assert out.exists()
    saved = out.read_text(encoding="utf-8")
    assert content == saved
