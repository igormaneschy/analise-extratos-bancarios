#!/usr/bin/env python3
"""
Gerador de gráficos visuais para métricas do MCP
Cria visualizações em ASCII e opcionalmente em HTML
"""

import os, sys, csv, datetime as dt, statistics as st
from typing import List, Dict, Any, Optional
import pathlib

CURRENT_DIR = pathlib.Path(__file__).parent.absolute()
ROOT_DIR = CURRENT_DIR.parent
INDEX_DIR = ROOT_DIR / ".mcp_index"

def create_ascii_chart(data: List[float], title: str, width: int = 50, height: int = 10) -> str:
    """Cria um gráfico ASCII simples"""
    if not data:
        return f"{title}: Sem dados"

    min_val = min(data)
    max_val = max(data)

    if max_val == min_val:
        max_val = min_val + 1

    chart_lines = []
    chart_lines.append(f"📊 {title}")
    chart_lines.append("─" * (len(title) + 3))

    # Criar escala
    for i in range(height, 0, -1):
        threshold = min_val + (max_val - min_val) * i / height
        line = f"{threshold:6.0f} │"

        for val in data:
            if val >= threshold:
                line += "█"
            else:
                line += " "

        chart_lines.append(line)

    # Linha base
    base_line = "       └" + "─" * len(data)
    chart_lines.append(base_line)

    return "\n".join(chart_lines)

# Configurações realistas para cálculo de economia
TOKENS_WITHOUT_MCP = 50000  # Cenário realista: arquivo completo sem MCP
COST_PER_1K_TOKENS = 0.002  # Custo por 1000 tokens
ESTIMATED_TOKENS_PER_CHUNK = 300  # Estimativa mais realista por chunk

def create_comparison_chart(mcp_tokens: float, without_mcp: float = None) -> str:
    """Cria gráfico de comparação visual"""
    chart = []
    chart.append("📊 COMPARAÇÃO VISUAL DE TOKENS")
    if without_mcp is None:
        without_mcp = TOKENS_WITHOUT_MCP

    chart = []
    chart.append("📊 COMPARAÇÃO VISUAL DE TOKENS")
    chart.append("─" * 30)
    chart.append("")

    # Sem MCP
    without_bars = int(without_mcp / 2500)  # 1 barra = 2500 tokens (ajustado)
    chart.append(f"Sem MCP ({without_mcp:,.0f} tokens):")
    chart.append("█" * min(without_bars, 60))
    chart.append("")

    # Com MCP
    with_bars = int(mcp_tokens / 2500)
    chart.append(f"Com MCP ({mcp_tokens:,.0f} tokens):")
    chart.append("█" * max(1, with_bars))
    chart.append("")

    # Economia
    savings_pct = ((without_mcp - mcp_tokens) / without_mcp) * 100
    chart.append(f"💰 Economia: {savings_pct:.1f}%")

    return "\n".join(chart)

def create_trend_chart(daily_data: List[Dict]) -> str:
    """Cria gráfico de tendência dos últimos dias"""
    if len(daily_data) < 2:
        return "📈 Tendência: Dados insuficientes"
    
    tokens_data = [d['avg_tokens'] for d in daily_data[-7:]]  # Últimos 7 dias
    dates = [d['day'][-5:] for d in daily_data[-7:]]  # MM-DD
    
    chart = []
    chart.append("📈 TENDÊNCIA DE TOKENS (Últimos 7 dias)")
    chart.append("─" * 40)
    
    if not tokens_data:
        return "\n".join(chart + ["Sem dados"])
    
    min_val = min(tokens_data)
    max_val = max(tokens_data)
    
    if max_val == min_val:
        max_val = min_val + 100
    
    # Normalizar para altura de 8 linhas
    height = 8
    for i in range(height, 0, -1):
        threshold = min_val + (max_val - min_val) * i / height
        line = f"{threshold:5.0f} │"
        
        for val in tokens_data:
            if val >= threshold:
                line += "██"
            else:
                line += "  "
        
        chart.append(line)
    
    # Linha base com datas
    base_line = "      └" + "──" * len(tokens_data)
    chart.append(base_line)
    
    # Datas
    date_line = "       "
    for date in dates:
        date_line += f"{date}"
    chart.append(date_line)
    
    return "\n".join(chart)

def create_efficiency_dashboard(avg_tokens: float, avg_latency: float, avg_util: float) -> str:
    """Cria dashboard de eficiência visual"""
    dashboard = []
    dashboard.append("🎯 DASHBOARD DE EFICIÊNCIA")
    dashboard.append("─" * 26)
    dashboard.append("")
    
    # Economia de tokens
    savings_pct = min(100, max(0, (1 - avg_tokens / TOKENS_WITHOUT_MCP) * 100))
    savings_bar = "█" * int(savings_pct / 5) + "░" * (20 - int(savings_pct / 5))
    dashboard.append(f"💰 Economia de Tokens: [{savings_bar}] {savings_pct:.1f}%")

    # Performance (latência invertida)
    perf_score = max(0, min(100, 100 - (avg_latency / 10)))
    perf_bar = "█" * int(perf_score / 5) + "░" * (20 - int(perf_score / 5))
    dashboard.append(f"⚡ Performance:        [{perf_bar}] {perf_score:.1f}%")

    # Utilização do orçamento
    util_bar = "█" * int(min(avg_util, 100) / 5) + "░" * (20 - int(min(avg_util, 100) / 5))
    util_color = "🟢" if 70 <= avg_util <= 90 else "🟡" if avg_util < 70 else "🔴"
    dashboard.append(f"📊 Uso do Orçamento:   [{util_bar}] {avg_util:.1f}% {util_color}")

    dashboard.append("")

    # Status geral
    if savings_pct > 90 and perf_score > 80:
        status = "🎉 EXCELENTE - Sistema otimizado!"
    elif savings_pct > 80 and perf_score > 70:
        status = "✅ BOM - Funcionando bem"
    elif savings_pct > 50:
        status = "⚠️  ATENÇÃO - Pode ser melhorado"
    else:
        status = "🔴 CRÍTICO - Revisar configurações"

    dashboard.append(f"Status: {status}")

    return "\n".join(dashboard)
    
    # Utilização do orçamento
    util_bar = "█" * int(avg_util / 5) + "░" * (20 - int(avg_util / 5))
    util_color = "🟢" if 60 <= avg_util <= 80 else "🟡" if avg_util < 60 else "🔴"
    dashboard.append(f"📊 Uso do Orçamento:   [{util_bar}] {avg_util:.1f}% {util_color}")
    
    dashboard.append("")
    
    # Status geral
    if savings_pct > 90 and perf_score > 80:
        status = "🎉 EXCELENTE - Sistema otimizado!"
    elif savings_pct > 80 and perf_score > 70:
        status = "✅ BOM - Funcionando bem"
    else:
        status = "⚠️  ATENÇÃO - Pode ser melhorado"
    
    dashboard.append(f"Status: {status}")
    
    return "\n".join(dashboard)

def generate_visual_report(metrics_file: str = None):
    """Gera relatório visual completo"""
    # Carregar dados (simplificado)
    if not metrics_file:
        metrics_file = str(INDEX_DIR / "metrics_context.csv")
    
    if not os.path.exists(metrics_file):
        print("❌ Arquivo de métricas não encontrado!")
        print(f"Procurado em: {metrics_file}")
        return
    
    # Ler dados básicos
    rows = []
    with open(metrics_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rows.append({
                    'tokens': float(row.get('total_tokens', 0)),
                    'latency': float(row.get('latency_ms', 0)),
                    'utilization': float(row.get('budget_utilization', 0)),
                    'date': row.get('ts', '')[:10]  # YYYY-MM-DD
                })
            except (ValueError, TypeError):
                continue
    
    if not rows:
        print("❌ Nenhum dado válido encontrado!")
        return
    
    # Calcular médias
    avg_tokens = st.mean([r['tokens'] for r in rows])
    avg_latency = st.mean([r['latency'] for r in rows])
    avg_util = st.mean([r['utilization'] for r in rows])
    
    # Agrupar por dia
    daily_data = {}
    for row in rows:
        date = row['date']
        if date not in daily_data:
            daily_data[date] = []
        daily_data[date].append(row)
    
    daily_summary = []
    for date, day_rows in sorted(daily_data.items()):
        daily_summary.append({
            'day': date,
            'avg_tokens': st.mean([r['tokens'] for r in day_rows])
        })
    
    # Gerar relatório visual
    print("🚀 " + "=" * 60)
    print("   RELATÓRIO VISUAL DE PERFORMANCE MCP")
    print("=" * 62)
    print()
    
    # Dashboard de eficiência
    print(create_efficiency_dashboard(avg_tokens, avg_latency, avg_util))
    print()
    
    # Comparação visual
    print(create_comparison_chart(avg_tokens))
    print()
    
    # Tendência
    if len(daily_summary) > 1:
        print(create_trend_chart(daily_summary))
        print()
    
    # Resumo final
    print("📋 RESUMO EXECUTIVO")
    print("─" * 19)
    print(f"   • Consultas analisadas: {len(rows)}")
    print(f"   • Tokens médios: {avg_tokens:.0f}")
    print(f"   • Economia vs sem MCP: {((15000 - avg_tokens) / 15000) * 100:.1f}%")
    print(f"   • Latência média: {avg_latency:.0f}ms")
    print(f"   • Utilização orçamento: {avg_util:.1f}%")
    print()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gerador de gráficos visuais para métricas MCP")
    parser.add_argument("--file", help="Arquivo CSV de métricas específico")
    
    args = parser.parse_args()
    generate_visual_report(args.file)