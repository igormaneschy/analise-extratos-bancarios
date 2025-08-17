"""
Implementação do analisador básico de extratos.
"""
from collections import defaultdict
from decimal import Decimal
from typing import Dict

from src.domain.models import BankStatement, AnalysisResult, TransactionCategory
from src.domain.interfaces import StatementAnalyzer


class BasicStatementAnalyzer(StatementAnalyzer):
    """Analisador básico de extratos bancários."""
    
    def analyze(self, statement: BankStatement) -> AnalysisResult:
        """Analisa um extrato e retorna resultados."""
        # Calcula totais
        total_income = statement.total_income
        total_expenses = statement.total_expenses
        net_flow = statement.net_flow
        
        # Resumo por categoria
        categories_summary = self._calculate_categories_summary(statement)
        
        # Resumo mensal
        monthly_summary = self._calculate_monthly_summary(statement)
        
        # Gera alertas
        alerts = self._generate_alerts(statement, categories_summary)
        
        # Gera insights
        insights = self._generate_insights(statement, categories_summary)
        
        return AnalysisResult(
            statement_id=statement.id,
            total_income=total_income,
            total_expenses=total_expenses,
            net_flow=net_flow,
            categories_summary=categories_summary,
            monthly_summary=monthly_summary,
            alerts=alerts,
            insights=insights,
            metadata={
                'transaction_count': statement.transaction_count,
                'period_days': (statement.period_end - statement.period_start).days if statement.period_end and statement.period_start else 0
            }
        )
    
    def _calculate_categories_summary(self, statement: BankStatement) -> Dict[TransactionCategory, Decimal]:
        """Calcula resumo de gastos por categoria."""
        summary = defaultdict(Decimal)
        
        for transaction in statement.transactions:
            if transaction.is_expense:
                summary[transaction.category] += transaction.amount
        
        # Converte para dict normal e ordena por valor
        return dict(sorted(summary.items(), key=lambda x: x[1], reverse=True))
    
    def _calculate_monthly_summary(self, statement: BankStatement) -> Dict[str, Dict[str, Decimal]]:
        """Calcula resumo mensal de receitas e despesas."""
        monthly = defaultdict(lambda: {'income': Decimal('0'), 'expenses': Decimal('0')})
        
        for transaction in statement.transactions:
            month_key = transaction.date.strftime('%Y-%m')
            
            if transaction.is_income:
                monthly[month_key]['income'] += transaction.amount
            else:
                monthly[month_key]['expenses'] += transaction.amount
        
        # Calcula saldo mensal
        for month_data in monthly.values():
            month_data['balance'] = month_data['income'] - month_data['expenses']
        
        return dict(monthly)
    
    def _generate_alerts(self, statement: BankStatement, categories_summary: Dict) -> list[str]:
        """Gera alertas baseados na análise."""
        alerts = []
        
        # Alerta de saldo negativo
        if statement.net_flow < 0:
            deficit = abs(statement.net_flow)
            alerts.append(f"⚠️ Atenção: Despesas superaram receitas em R$ {deficit:.2f}")
        
        # Alerta de muitas transações não categorizadas
        uncategorized = sum(
            1 for t in statement.transactions 
            if t.category == TransactionCategory.NAO_CATEGORIZADO
        )
        if uncategorized > len(statement.transactions) * 0.3:
            alerts.append(f"⚠️ {uncategorized} transações não foram categorizadas automaticamente")
        
        # Alerta de gastos altos em categorias específicas
        total_expenses = statement.total_expenses
        if total_expenses > 0:
            for category, amount in categories_summary.items():
                percentage = (amount / total_expenses) * 100
                if percentage > 40:
                    alerts.append(
                        f"⚠️ Gastos com {category.value} representam {percentage:.1f}% do total"
                    )
        
        # Alerta de transações de alto valor
        avg_expense = (
            total_expenses / len([t for t in statement.transactions if t.is_expense])
            if any(t.is_expense for t in statement.transactions) else Decimal('0')
        )
        
        for transaction in statement.transactions:
            if transaction.is_expense and transaction.amount > avg_expense * 3:
                alerts.append(
                    f"⚠️ Transação de alto valor: {transaction.description[:50]} - R$ {transaction.amount:.2f}"
                )
        
        return alerts[:5]  # Limita a 5 alertas mais importantes
    
    def _generate_insights(self, statement: BankStatement, categories_summary: Dict) -> list[str]:
        """Gera insights sobre os gastos."""
        insights = []
        
        # Insight sobre categoria com maior gasto
        if categories_summary:
            top_category = list(categories_summary.keys())[0]
            top_amount = categories_summary[top_category]
            percentage = (top_amount / statement.total_expenses * 100) if statement.total_expenses > 0 else 0
            
            insights.append(
                f"💡 Maior categoria de gastos: {top_category.value} (R$ {top_amount:.2f} - {percentage:.1f}%)"
            )
        
        # Insight sobre média diária de gastos
        if statement.period_end is not None and statement.period_start is not None and statement.period_end > statement.period_start:
            days = (statement.period_end - statement.period_start).days
            if days > 0:
                daily_avg = statement.total_expenses / days
                insights.append(f"💡 Média diária de gastos: R$ {daily_avg:.2f}")
        
        # Insight sobre padrão de gastos
        expense_transactions = [t for t in statement.transactions if t.is_expense]
        if len(expense_transactions) > 10:
            amounts = [t.amount for t in expense_transactions]
            amounts.sort()
            median_idx = len(amounts) // 2
            median = amounts[median_idx]
            
            small_transactions = sum(1 for a in amounts if a < median)
            percentage = (small_transactions / len(amounts)) * 100
            
            insights.append(
                f"💡 {percentage:.0f}% das suas despesas são menores que R$ {median:.2f}"
            )
        
        # Insight sobre frequência de transações
        if (statement.transaction_count > 0 and
            statement.period_end and statement.period_start and
            statement.period_end > statement.period_start):
            days = (statement.period_end - statement.period_start).days if statement.period_end and statement.period_start else 0
            if days > 0:
                trans_per_day = statement.transaction_count / days
                insights.append(
                    f"💡 Média de {trans_per_day:.1f} transações por dia"
                )
        
        # Insight sobre economia potencial
        if categories_summary:
            # Identifica categorias com potencial de economia
            discretionary = [
                TransactionCategory.LAZER,
                TransactionCategory.COMPRAS,
                TransactionCategory.ALIMENTACAO
            ]
            
            potential_savings = Decimal('0')
            for cat in discretionary:
                if cat in categories_summary:
                    potential_savings += categories_summary[cat] * Decimal('0.2')  # 20% de economia
            
            if potential_savings > 0:
                insights.append(
                    f"💡 Potencial de economia: R$ {potential_savings:.2f} reduzindo 20% em gastos discricionários"
                )
        
        return insights[:5]  # Limita a 5 insights mais relevantes