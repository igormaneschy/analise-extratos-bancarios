"""
Implementação de gerador de relatórios em texto.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.domain.models import AnalysisResult, TransactionCategory
from src.domain.interfaces import ReportGenerator
from src.utils.currency_utils import CurrencyUtils


class TextReportGenerator(ReportGenerator):
    """Gerador de relatórios em formato texto."""

    def generate(self, analysis: AnalysisResult, output_path: Optional[Path] = None) -> str:
        """Gera relatório em texto a partir da análise."""
        
        def format_currency(value: float) -> str:
            """Formata valor com a moeda correta."""
            return CurrencyUtils.format_currency(value, analysis.currency)

        report_lines = []

        # Cabeçalho
        report_lines.append("=" * 80)
        report_lines.append("RELATÓRIO DE ANÁLISE DE EXTRATO BANCÁRIO".center(80))
        report_lines.append("=" * 80)
        report_lines.append(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        report_lines.append("")

        # Resumo Financeiro
        report_lines.append("RESUMO FINANCEIRO")
        report_lines.append("-" * 40)
        report_lines.append(f"Total de Receitas:  {format_currency(analysis.total_income):>12}")
        report_lines.append(f"Total de Despesas:  {format_currency(analysis.total_expenses):>12}")
        report_lines.append(f"Saldo do Período:   {format_currency(analysis.net_flow):>12}")
        report_lines.append("")

        # Análise por Categoria
        if analysis.categories_summary:
            report_lines.append("DESPESAS POR CATEGORIA")
            report_lines.append("-" * 40)

            total_categorized = sum(analysis.categories_summary.values())

            for category, amount in analysis.categories_summary.items():
                percentage = (amount / analysis.total_expenses * 100) if analysis.total_expenses > 0 else 0
                category_name = category.value.title()
                report_lines.append(
                    f"{category_name:<25} {format_currency(amount):>10} ({percentage:>5.1f}%)"
                )

            report_lines.append("-" * 40)
            report_lines.append(f"{'Total Categorizado:':<25} {format_currency(total_categorized):>10}")
            report_lines.append("")

        # Resumo Mensal
        if analysis.monthly_summary:
            report_lines.append("RESUMO MENSAL")
            report_lines.append("-" * 60)
            report_lines.append(f"{'Mês':<10} {'Receitas':>15} {'Despesas':>15} {'Saldo':>15}")
            report_lines.append("-" * 60)

            for month, data in sorted(analysis.monthly_summary.items()):
                month_name = datetime.strptime(month, '%Y-%m').strftime('%b/%Y')
                report_lines.append(
                    f"{month_name:<10} "
                    f"{format_currency(data['income']):>15} "
                    f"{format_currency(data['expenses']):>15} "
                    f"{format_currency(data['balance']):>15}"
                )

            report_lines.append("")

        # Alertas
        if analysis.alerts:
            report_lines.append("ALERTAS")
            report_lines.append("-" * 40)
            for alert in analysis.alerts:
                report_lines.append(f"  {alert}")
            report_lines.append("")

        # Insights
        if analysis.insights:
            report_lines.append("INSIGHTS E RECOMENDAÇÕES")
            report_lines.append("-" * 40)
            for insight in analysis.insights:
                report_lines.append(f"  {insight}")
            report_lines.append("")

        # Metadados
        if analysis.metadata:
            report_lines.append("INFORMAÇÕES ADICIONAIS")
            report_lines.append("-" * 40)
            if 'transaction_count' in analysis.metadata:
                report_lines.append(f"Total de transações: {analysis.metadata['transaction_count']}")
            if 'period_days' in analysis.metadata:
                report_lines.append(f"Período analisado: {analysis.metadata['period_days']} dias")
            report_lines.append("")

        # Rodapé
        report_lines.append("=" * 80)
        report_lines.append("Fim do Relatório")
        report_lines.append("=" * 80)

        report_content = "\n".join(report_lines)

        # Salva o arquivo se especificado
        if output_path:
            output_path.write_text(report_content, encoding='utf-8')

        return report_content


class MarkdownReportGenerator(ReportGenerator):
    """Gerador de relatórios em formato Markdown."""

    def generate(self, analysis: AnalysisResult, output_path: Optional[Path] = None) -> str:
        """Gera relatório em Markdown a partir da análise."""
        
        def format_currency(value: float) -> str:
            """Formata valor com a moeda correta."""
            return CurrencyUtils.format_currency(value, analysis.currency)

        report_lines = []

        # Cabeçalho
        report_lines.append("# Relatório de Análise de Extrato Bancário")
        report_lines.append("")
        report_lines.append(f"**Gerado em:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        report_lines.append("")

        # Resumo Financeiro
        report_lines.append("## 💰 Resumo Financeiro")
        report_lines.append("")
        report_lines.append("| Item | Valor |")
        report_lines.append("|------|-------|")
        report_lines.append(f"| Total de Receitas | {format_currency(analysis.total_income)} |")
        report_lines.append(f"| Total de Despesas | {format_currency(analysis.total_expenses)} |")
        report_lines.append(f"| **Saldo do Período** | **{format_currency(analysis.net_flow)}** |")
        report_lines.append("")

        # Análise por Categoria
        if analysis.categories_summary:
            report_lines.append("## 📊 Despesas por Categoria")
            report_lines.append("")
            report_lines.append("| Categoria | Valor | Percentual |")
            report_lines.append("|-----------|-------|------------|")

            for category, amount in analysis.categories_summary.items():
                percentage = (amount / analysis.total_expenses * 100) if analysis.total_expenses > 0 else 0
                category_name = category.value.replace('_', ' ').title()
                report_lines.append(
                    f"| {category_name} | {format_currency(amount)} | {percentage:.1f}% |"
                )
            report_lines.append("")

        # Resumo Mensal
        if analysis.monthly_summary:
            report_lines.append("## 📅 Resumo Mensal")
            report_lines.append("")
            report_lines.append("| Mês | Receitas | Despesas | Saldo |")
            report_lines.append("|-----|----------|----------|-------|")

            for month, data in sorted(analysis.monthly_summary.items()):
                month_name = datetime.strptime(month, '%Y-%m').strftime('%b/%Y')
                report_lines.append(
                    f"| {month_name} | "
                    f"{format_currency(data['income'])} | "
                    f"{format_currency(data['expenses'])} | "
                    f"{format_currency(data['balance'])} |"
                )
            report_lines.append("")

        # Alertas
        if analysis.alerts:
            report_lines.append("## ⚠️ Alertas")
            report_lines.append("")
            for alert in analysis.alerts:
                report_lines.append(f"- {alert}")
            report_lines.append("")

        # Insights
        if analysis.insights:
            report_lines.append("## 💡 Insights e Recomendações")
            report_lines.append("")
            for insight in analysis.insights:
                report_lines.append(f"- {insight}")
            report_lines.append("")

        # Metadados
        if analysis.metadata:
            report_lines.append("## ℹ️ Informações Adicionais")
            report_lines.append("")
            if 'transaction_count' in analysis.metadata:
                report_lines.append(f"- **Total de transações:** {analysis.metadata['transaction_count']}")
            if 'period_days' in analysis.metadata:
                report_lines.append(f"- **Período analisado:** {analysis.metadata['period_days']} dias")
            report_lines.append("")

        report_content = "\n".join(report_lines)

        # Salva o arquivo se especificado
        if output_path:
            output_path.write_text(report_content, encoding='utf-8')

        return report_content