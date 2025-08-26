import pytest
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, mock_open
from src.infrastructure.reports.text_report import TextReportGenerator, MarkdownReportGenerator
from src.domain.models import AnalysisResult, TransactionCategory

class TestTextReportGenerator:
    """Testes para o TextReportGenerator."""
    
    def test_generate_basic_report(self):
        """Testa a geração de um relatório básico."""
        generator = TextReportGenerator()
        
        analysis = AnalysisResult(
            statement_id="test123",
            total_income=Decimal("1000.00"),
            total_expenses=Decimal("500.00"),
            net_flow=Decimal("500.00"),
            currency="EUR",
            categories_summary={},
            monthly_summary={},
            alerts=[],
            insights=[],
            metadata={}
        )
        
        report = generator.generate(analysis)
        
        # Verifica que o relatório contém elementos básicos
        assert "RELATÓRIO DE ANÁLISE DE EXTRATO BANCÁRIO" in report
        assert "Total de Receitas" in report
        assert "Total de Despesas" in report
        assert "Saldo do Período" in report
        assert "€ 500,00" in report  # Verifica formatação de moeda (formato europeu)
    
    def test_generate_report_with_categories(self):
        """Testa a geração de um relatório com categorias."""
        generator = TextReportGenerator()
        
        analysis = AnalysisResult(
            statement_id="test123",
            total_income=Decimal("1000.00"),
            total_expenses=Decimal("600.00"),
            net_flow=Decimal("400.00"),
            currency="EUR",
            categories_summary={
                TransactionCategory.ALIMENTACAO: Decimal("200.00"),
                TransactionCategory.TRANSPORTE: Decimal("100.00"),
                TransactionCategory.MORADIA: Decimal("300.00")
            },
            monthly_summary={},
            alerts=[],
            insights=[],
            metadata={}
        )
        
        report = generator.generate(analysis)
        
        # Verifica que as categorias estão no relatório
        assert "DESPESAS POR CATEGORIA" in report
        assert "Alimentacao" in report
        assert "Transporte" in report
        assert "Moradia" in report
        assert "33.3%" in report  # Porcentagem de alimentação (200/600)
    
    def test_generate_report_with_monthly_summary(self):
        """Testa a geração de um relatório com resumo mensal."""
        generator = TextReportGenerator()
        
        analysis = AnalysisResult(
            statement_id="test123",
            total_income=Decimal("1000.00"),
            total_expenses=Decimal("500.00"),
            net_flow=Decimal("500.00"),
            currency="EUR",
            categories_summary={},
            monthly_summary={
                "2023-01": {
                    "income": Decimal("1000.00"),
                    "expenses": Decimal("500.00"),
                    "balance": Decimal("500.00")
                },
                "2023-02": {
                    "income": Decimal("1200.00"),
                    "expenses": Decimal("600.00"),
                    "balance": Decimal("600.00")
                }
            },
            alerts=[],
            insights=[],
            metadata={}
        )
        
        report = generator.generate(analysis)
        
        # Verifica que o resumo mensal está no relatório
        assert "RESUMO MENSAL" in report
        assert "Jan/2023" in report
        assert "Feb/2023" in report  # Verifica a formatação correta
    
    def test_generate_report_with_alerts_and_insights(self):
        """Testa a geração de um relatório com alertas e insights."""
        generator = TextReportGenerator()
        
        analysis = AnalysisResult(
            statement_id="test123",
            total_income=Decimal("1000.00"),
            total_expenses=Decimal("1200.00"),
            net_flow=Decimal("-200.00"),
            currency="EUR",
            categories_summary={},
            monthly_summary={},
            alerts=["Despesas maiores que receitas este mês"],
            insights=["Considere reduzir gastos com lazer"],
            metadata={}
        )
        
        report = generator.generate(analysis)
        
        # Verifica que alertas e insights estão no relatório
        assert "ALERTAS" in report
        assert "Despesas maiores que receitas este mês" in report
        assert "INSIGHTS E RECOMENDAÇÕES" in report
        assert "Considere reduzir gastos com lazer" in report
    
    def test_generate_report_with_metadata(self):
        """Testa a geração de um relatório com metadados."""
        generator = TextReportGenerator()
        
        analysis = AnalysisResult(
            statement_id="test123",
            total_income=Decimal("1000.00"),
            total_expenses=Decimal("500.00"),
            net_flow=Decimal("500.00"),
            currency="EUR",
            categories_summary={},
            monthly_summary={},
            alerts=[],
            insights=[],
            metadata={
                "transaction_count": 25,
                "period_days": 30
            }
        )
        
        report = generator.generate(analysis)
        
        # Verifica que metadados estão no relatório
        assert "INFORMAÇÕES ADICIONAIS" in report
        assert "Total de transações: 25" in report
        assert "Período analisado: 30 dias" in report
    
    @patch("pathlib.Path.write_text")
    def test_generate_report_with_output_path(self, mock_write_text):
        """Testa a geração de um relatório com caminho de saída."""
        generator = TextReportGenerator()
        
        analysis = AnalysisResult(
            statement_id="test123",
            total_income=Decimal("1000.00"),
            total_expenses=Decimal("500.00"),
            net_flow=Decimal("500.00"),
            currency="EUR",
            categories_summary={},
            monthly_summary={},
            alerts=[],
            insights=[],
            metadata={}
        )
        
        output_path = Path("test_report.txt")
        report = generator.generate(analysis, output_path)
        
        # Verifica que o método write_text foi chamado
        mock_write_text.assert_called_once()


class TestMarkdownReportGenerator:
    """Testes para o MarkdownReportGenerator."""
    
    def test_generate_basic_markdown_report(self):
        """Testa a geração de um relatório básico em Markdown."""
        generator = MarkdownReportGenerator()
        
        analysis = AnalysisResult(
            statement_id="test123",
            total_income=Decimal("1000.00"),
            total_expenses=Decimal("500.00"),
            net_flow=Decimal("500.00"),
            currency="EUR",
            categories_summary={},
            monthly_summary={},
            alerts=[],
            insights=[],
            metadata={}
        )
        
        report = generator.generate(analysis)
        
        # Verifica que o relatório contém elementos básicos em Markdown
        assert "# Relatório de Análise de Extrato Bancário" in report
        assert "| Total de Receitas |" in report  # Verifica que a tabela contém a coluna
        assert "| **Saldo do Período** |" in report  # Verifica que o saldo está em negrito
    
    def test_generate_markdown_report_with_categories(self):
        """Testa a geração de um relatório em Markdown com categorias."""
        generator = MarkdownReportGenerator()
        
        analysis = AnalysisResult(
            statement_id="test123",
            total_income=Decimal("1000.00"),
            total_expenses=Decimal("600.00"),
            net_flow=Decimal("400.00"),
            currency="EUR",
            categories_summary={
                TransactionCategory.ALIMENTACAO: Decimal("200.00"),
                TransactionCategory.TRANSPORTE: Decimal("100.00"),
                TransactionCategory.MORADIA: Decimal("300.00")
            },
            monthly_summary={},
            alerts=[],
            insights=[],
            metadata={}
        )
        
        report = generator.generate(analysis)
        
        # Verifica que as categorias estão no relatório em Markdown
        assert "## 📊 Despesas por Categoria" in report
        assert "| Alimentacao | € 200,00 | 33.3% |" in report
        assert "| Transporte | € 100,00 | 16.7% |" in report
        assert "| Moradia | € 300,00 | 50.0% |" in report
    
    def test_generate_markdown_report_with_monthly_summary(self):
        """Testa a geração de um relatório em Markdown com resumo mensal."""
        generator = MarkdownReportGenerator()
        
        analysis = AnalysisResult(
            statement_id="test123",
            total_income=Decimal("1000.00"),
            total_expenses=Decimal("500.00"),
            net_flow=Decimal("500.00"),
            currency="EUR",
            categories_summary={},
            monthly_summary={
                "2023-01": {
                    "income": Decimal("1000.00"),
                    "expenses": Decimal("500.00"),
                    "balance": Decimal("500.00")
                }
            },
            alerts=[],
            insights=[],
            metadata={}
        )
        
        report = generator.generate(analysis)
        
        # Verifica que o resumo mensal está no relatório em Markdown
        assert "## 📅 Resumo Mensal" in report
        assert "| Jan/2023 | € 1.000,00 | € 500,00 | € 500,00 |" in report
    
    @patch("pathlib.Path.write_text")
    def test_generate_markdown_report_with_output_path(self, mock_write_text):
        """Testa a geração de um relatório em Markdown com caminho de saída."""
        generator = MarkdownReportGenerator()
        
        analysis = AnalysisResult(
            statement_id="test123",
            total_income=Decimal("1000.00"),
            total_expenses=Decimal("500.00"),
            net_flow=Decimal("500.00"),
            currency="EUR",
            categories_summary={},
            monthly_summary={},
            alerts=[],
            insights=[],
            metadata={}
        )
        
        output_path = Path("test_report.md")
        report = generator.generate(analysis, output_path)
        
        # Verifica que o método write_text foi chamado
        mock_write_text.assert_called_once()