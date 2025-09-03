#!/usr/bin/env python3
"""
Gerador de gráficos visuais para métricas do MCP (atualizado)

- Lê .mcp_index/metrics_context.csv (ou caminho informado)
- ASCII charts de comparação e tendência
- Dashboard executivo com médias e economia estimada

Uso:
  python mcp_system/scripts/visual_metrics.py --file mcp_system/.mcp_index/metrics_context.csv --baseline 15000
  python -m mcp_system.scripts.visual_metrics --file .mcp_index/metrics_context.csv

Env vars suportadas:
  MCP_BASELINE_TOKENS: baseline de tokens "sem MCP" (default 15000)
"""

import os, sys, csv, datetime as dt, statistics as st
from typing import List, Dict, Any, Optional
import pathlib
import argparse
import json
import shutil

CURRENT_DIR = pathlib.Path(__file__).parent.absolute()
ROOT_DIR = CURRENT_DIR.parent
INDEX_DIR = ROOT_DIR / ".mcp_index"

# Garante que o pacote mcp_system seja importável quando executado diretamente pelo caminho do arquivo
try:
    _PROJECT_ROOT = ROOT_DIR.parent
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
except Exception:
    pass


def _normalize_utilization(val: Any) -> float:
    try:
        v = float(val or 0)
    except (ValueError, TypeError):
        v = 0.0
    if 0.0 <= v <= 1.0:
        v *= 100.0
    return v


def create_ascii_chart(data: List[float], title: str, width: int = 50, height: int = 10) -> str:
    if not data:
        return f"{title}: Sem dados"
    min_val = min(data)
    max_val = max(data)
    if max_val == min_val:
        max_val = min_val + 1
    # Ajustar largura ao terminal se possível
    try:
        cols = shutil.get_terminal_size((80, 20)).columns
        width = min(width, max(20, cols - 20))
    except Exception:
        pass
    # Amostragem para séries longas para caber em width
    step = max(1, len(data) // max(1, width))
    data_sampled = data[::step]
    chart_lines = [f"📊 {title}", "─" * (len(title) + 3)]
    for i in range(height, 0, -1):
        threshold = min_val + (max_val - min_val) * i / height
        line = f"{threshold:6.0f} │"
        for val in data_sampled:
            line += "█" if val >= threshold else " "
        chart_lines.append(line)
    base_line = "       └" + "─" * len(data_sampled)
    chart_lines.append(base_line)
    return "\n".join(chart_lines)

# Parâmetros para comparação
TOKENS_WITHOUT_MCP = float(os.getenv("MCP_BASELINE_TOKENS", "15000"))
COST_PER_1K_TOKENS = 0.002


def create_comparison_chart(mcp_tokens: float, without_mcp: Optional[float] = None) -> str:
    chart = ["📊 COMPARAÇÃO VISUAL DE TOKENS"]
    chart.append("─" * 30)
    chart.append("")
    if without_mcp is None:
        without_mcp = TOKENS_WITHOUT_MCP
    without_bars = max(1, int(without_mcp / 2500))
    chart.append(f"Sem MCP ({without_mcp:,.0f} tokens):")
    chart.append("█" * min(without_bars, 60))
    chart.append("")
    with_bars = max(1, int(max(mcp_tokens, 1) / 2500))
    chart.append(f"Com MCP ({mcp_tokens:,.0f} tokens):")
    chart.append("█" * min(with_bars, 60))
    chart.append("")
    savings_pct = ((without_mcp - mcp_tokens) / without_mcp) * 100 if without_mcp else 0
    chart.append(f"💰 Economia: {savings_pct:.1f}%")
    return "\n".join(chart)


def create_trend_chart(daily_data: List[Dict]) -> str:
    if len(daily_data) < 2:
        # fallback: gráfico simples das últimas N consultas
        return "📈 Tendência: Dados insuficientes"
    tokens_data = [d['avg_tokens'] for d in daily_data[-7:]]
    dates = [d['day'][-5:] for d in daily_data[-7:]]
    chart = ["📈 TENDÊNCIA DE TOKENS (Últimos 7 dias)", "─" * 40]
    if not tokens_data:
        return "\n".join(chart + ["Sem dados"])
    min_val = min(tokens_data)
    max_val = max(tokens_data)
    if max_val == min_val:
        max_val = min_val + 100
    height = 8
    for i in range(height, 0, -1):
        threshold = min_val + (max_val - min_val) * i / height
        line = f"{threshold:5.0f} │"
        for val in tokens_data:
            line += "██" if val >= threshold else "  "
        chart.append(line)
    base_line = "      └" + "──" * len(tokens_data)
    chart.append(base_line)
    date_line = "       " + "".join(dates)
    chart.append(date_line)
    return "\n".join(chart)


def create_efficiency_dashboard(avg_tokens: float, avg_latency: float, avg_util: float, baseline_tokens: float) -> str:
    dashboard = ["🎯 DASHBOARD DE EFICIÊNCIA", "─" * 26, ""]
    savings_pct = min(100, max(0, (1 - avg_tokens / baseline_tokens) * 100)) if baseline_tokens > 0 else 0
    savings_bar = "█" * int(savings_pct / 5) + "░" * (20 - int(savings_pct / 5))
    dashboard.append(f"💰 Economia de Tokens: [{savings_bar}] {savings_pct:.1f}%")
    perf_score = max(0, min(100, 100 - (avg_latency / 10)))
    perf_bar = "█" * int(perf_score / 5) + "░" * (20 - int(perf_score / 5))
    dashboard.append(f"⚡ Performance:        [{perf_bar}] {perf_score:.1f}%")
    util_bar = "█" * int(min(avg_util, 100) / 5) + "░" * (20 - int(min(avg_util, 100) / 5))
    util_color = "🟢" if 70 <= avg_util <= 90 else "🟡" if avg_util < 70 else "🔴"
    dashboard.append(f"📊 Uso do Orçamento:   [{util_bar}] {avg_util:.1f}% {util_color}")
    dashboard.append("")
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


def _read_metrics(metrics_file: Optional[str]) -> List[Dict[str, Any]]:
    if not metrics_file:
        metrics_file = str(INDEX_DIR / "metrics_context.csv")
    if not os.path.exists(metrics_file):
        print("❌ Arquivo de métricas não encontrado!", file=sys.stderr)
        print(f"Procurado em: {metrics_file}", file=sys.stderr)
        return []
    rows: List[Dict[str, Any]] = []
    with open(metrics_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                tokens = float(row.get('total_tokens', 0) or 0)
                if tokens <= 0:
                    # Fallback para total_tokens_sent quando presente
                    tokens = float(row.get('total_tokens_sent', tokens) or 0)
                rows.append({
                    'tokens': tokens,
                    'latency': float(row.get('latency_ms', 0) or 0),
                    'utilization': _normalize_utilization(row.get('budget_utilization', 0)),
                    'date': (row.get('ts', '') or '')[:10],
                    'query': row.get('query', '') or ''
                })
            except (ValueError, TypeError):
                continue
    return rows

# Expor uma função utilitária para testes/integração que retorna objeto estruturado
def generate_visual_report_structured(metrics_file: Optional[str] = None, baseline_tokens: Optional[float] = None) -> Dict[str, Any]:
    rows = _read_metrics(metrics_file)

    if not rows:
        return {"summary": {}, "daily_summary": [], "rows": []}

    if baseline_tokens is None:
        try:
            baseline_tokens = float(os.getenv("MCP_BASELINE_TOKENS", "15000"))
        except ValueError:
            baseline_tokens = 15000.0

    avg_tokens = st.mean([r['tokens'] for r in rows])
    avg_latency = st.mean([r['latency'] for r in rows])
    avg_util = st.mean([r['utilization'] for r in rows])

    daily_data: Dict[str, List[Dict[str, float]]] = {}
    for row in rows:
        daily_data.setdefault(row['date'], []).append(row)

    daily_summary = []
    for date, day_rows in sorted(daily_data.items()):
        daily_summary.append({
            'day': date,
            'avg_tokens': st.mean([r['tokens'] for r in day_rows]),
            'avg_latency': st.mean([r['latency'] for r in day_rows]),
        })

    output = {
        "summary": {
            "num_queries": len(rows),
            "avg_tokens": avg_tokens,
            "avg_latency_ms": avg_latency,
            "avg_utilization_pct": avg_util,
            "baseline_tokens": baseline_tokens,
            "cost_estimated": (avg_tokens / 1000.0) * COST_PER_1K_TOKENS,
        },
        "daily_summary": daily_summary,
        "rows": rows,
    }
    return output


def generate_visual_report(metrics_file: Optional[str] = None, baseline_tokens: Optional[float] = None):
    rows = _read_metrics(metrics_file)

    if not rows:
        print("❌ Nenhum dado válido encontrado!")
        return

    if baseline_tokens is None:
        try:
            baseline_tokens = float(os.getenv("MCP_BASELINE_TOKENS", "15000"))
        except ValueError:
            baseline_tokens = 15000.0

    avg_tokens = st.mean([r['tokens'] for r in rows])
    avg_latency = st.mean([r['latency'] for r in rows])
    avg_util = st.mean([r['utilization'] for r in rows])

    daily_data: Dict[str, List[Dict[str, float]]] = {}
    for row in rows:
        daily_data.setdefault(row['date'], []).append(row)

    daily_summary = []
    for date, day_rows in sorted(daily_data.items()):
        daily_summary.append({
            'day': date,
            'avg_tokens': st.mean([r['tokens'] for r in day_rows]),
            'avg_latency': st.mean([r['latency'] for r in day_rows]),
        })

    print("🚀 " + "=" * 60)
    print("   RELATÓRIO VISUAL DE PERFORMANCE MCP")
    print("=" * 62)
    print()

    print(create_efficiency_dashboard(avg_tokens, avg_latency, avg_util, baseline_tokens))
    print()
    print(create_comparison_chart(avg_tokens, without_mcp=baseline_tokens))
    print()
    if len(daily_summary) > 1:
        print(create_trend_chart(daily_summary))
        print()
    print("📋 RESUMO EXECUTIVO")
    print("─" * 19)
    print(f"   • Consultas analisadas: {len(rows)}")
    print(f"   • Tokens médios: {avg_tokens:.0f}")
    if baseline_tokens:
        print(f"   • Economia vs sem MCP: {((baseline_tokens - avg_tokens) / baseline_tokens) * 100:.1f}%")
        # Custo estimado com e sem MCP
        cost_mcp = (avg_tokens / 1000.0) * COST_PER_1K_TOKENS
        cost_base = (baseline_tokens / 1000.0) * COST_PER_1K_TOKENS
        print(f"   • Custo estimado: ${cost_mcp:.4f} (baseline: ${cost_base:.4f})")
    else:
        print("   • Economia vs sem MCP: N/D (baseline 0)")
        cost_mcp = (avg_tokens / 1000.0) * COST_PER_1K_TOKENS
        print(f"   • Custo estimado: ${cost_mcp:.4f}")
    print(f"   • Latência média: {avg_latency:.0f}ms")
    print(f"   • Utilização orçamento: {avg_util:.1f}%")
    print()

    # Se houver poucos dias, mostrar últimas N consultas
    if len(daily_summary) <= 1 and rows:
        print("📝 Últimas consultas")
        print("─" * 18)
        for r in rows[-5:]:
            q = (r.get('query') or '')[:60]
            print(f"   - {r['date']} | tokens={r['tokens']:.0f} | lat={r['latency']:.0f}ms | util={r['utilization']:.1f}% | {q}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Gerador de gráficos visuais para métricas MCP (atualizado)")
    parser.add_argument("--file", help="Arquivo CSV de métricas específico")
    parser.add_argument("--baseline", type=float, default=None, help="Baseline de tokens sem MCP (default 15000 ou MCP_BASELINE_TOKENS)")
    parser.add_argument("--json", action="store_true", help="Saída em JSON estruturado -- útil para pipelines")
    args = parser.parse_args()
    if args.json:
        import json
        out = generate_visual_report_structured(args.file, baseline_tokens=args.baseline)
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        generate_visual_report(args.file, baseline_tokens=args.baseline)


if __name__ == "__main__":
    main()

