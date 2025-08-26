#!/usr/bin/env python3
"""
Versão melhorada do summarize_metrics.py com visualizações mais intuitivas
Foco em simplicidade e comparações claras dos benefícios do MCP
"""

import os, sys, csv, argparse, datetime as dt, statistics as st, json
from math import floor
from typing import List, Dict, Any, Optional
import pathlib

# Diretórios de referência
CURRENT_DIR = pathlib.Path(__file__).parent.absolute()
ROOT_DIR = CURRENT_DIR.parent
INDEX_DIR = ROOT_DIR / ".mcp_index"
DEFAULT_CONTEXT_PATH = INDEX_DIR / "metrics_context.csv"
DEFAULT_INDEX_PATH = INDEX_DIR / "metrics_index.csv"
LEGACY_METRICS_PATH = INDEX_DIR / "metrics.csv"

# Configurações realistas para cálculo de economia
TOKENS_WITHOUT_MCP = 50000  # Cenário realista: arquivo completo sem MCP
COST_PER_1K_TOKENS = 0.002  # Custo por 1000 tokens (ajustar conforme modelo)
ESTIMATED_TOKENS_PER_CHUNK = 300  # Estimativa mais realista por chunk
TOKENS_WITHOUT_MCP = 15000  # Estimativa de tokens sem MCP
COST_PER_1K_TOKENS = 0.002  # Custo estimado por 1K tokens (GPT-4)

def create_progress_bar(percentage: float, width: int = 20) -> str:
    """Cria uma barra de progresso visual"""
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {percentage:.1f}%"

def format_number(num: float) -> str:
    """Formata números grandes de forma legível"""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return f"{num:.0f}"

def calculate_savings(mcp_tokens: float) -> Dict[str, Any]:
    """Calcula economias comparando com cenário sem MCP"""
    without_mcp = TOKENS_WITHOUT_MCP
    reduction_pct = ((without_mcp - mcp_tokens) / without_mcp) * 100
    
    cost_without = (without_mcp / 1000) * COST_PER_1K_TOKENS
    cost_with = (mcp_tokens / 1000) * COST_PER_1K_TOKENS
    cost_savings = cost_without - cost_with
    
    return {
        "tokens_without_mcp": without_mcp,
        "tokens_with_mcp": mcp_tokens,
        "reduction_pct": reduction_pct,
        "cost_without": cost_without,
        "cost_with": cost_with,
        "cost_savings": cost_savings,
        "cost_savings_pct": (cost_savings / cost_without) * 100
    }

def print_header():
    """Imprime cabeçalho estilizado"""
    print("🚀 " + "=" * 60)
    print("   RELATÓRIO DE PERFORMANCE DO SISTEMA MCP")
    print("   Análise de Eficiência e Economia de Tokens")
    print("=" * 62)
    print()

def print_summary_card(title: str, metrics: Dict[str, Any]):
    """Imprime um card de resumo estilizado"""
    print(f"📊 {title}")
    print("─" * (len(title) + 3))
    
    for key, value in metrics.items():
        if isinstance(value, float):
            if "pct" in key or "%" in key:
                print(f"   {key}: {value:.1f}%")
            elif "ms" in key:
                print(f"   {key}: {value:.0f}ms")
            else:
                print(f"   {key}: {format_number(value)}")
        else:
            print(f"   {key}: {value}")
    print()

def create_comparison_table(avg_tokens: float) -> str:
    """Cria tabela de comparação COM vs SEM MCP"""
    without_mcp = TOKENS_WITHOUT_MCP
    with_mcp = avg_tokens
    savings_pct = ((without_mcp - with_mcp) / without_mcp) * 100

    cost_without = (without_mcp / 1000) * COST_PER_1K_TOKENS
    cost_with = (with_mcp / 1000) * COST_PER_1K_TOKENS
    cost_savings_pct = ((cost_without - cost_with) / cost_without) * 100

    table = []
    table.append("💰 COMPARAÇÃO: COM vs SEM MCP")
    table.append("─" * 35)
    table.append(f"{'Métrica':<20} {'Sem MCP':<12} {'Com MCP':<12} {'Economia':<12}")
    table.append("─" * 60)
    table.append(f"{'Tokens por consulta':<20} {format_number(without_mcp):<12} {format_number(with_mcp):<12} {savings_pct:>6.1f}%")
    table.append(f"{'Custo por consulta':<20} ${cost_without:<11.3f} ${cost_with:<11.3f} {cost_savings_pct:>6.1f}%")
    table.append("")

    return "\n".join(table)
    cost_reduction = f"{savings['cost_savings_pct']:.1f}%"
    print(f"{'Custo por consulta':<20} {cost_without:<12} {cost_with:<12} {cost_reduction:<12}")
    
    print()

def print_efficiency_bars(avg_tokens: float, avg_util: float, avg_latency: float):
    """Imprime barras de eficiência visual"""
    print("⚡ INDICADORES DE EFICIÊNCIA")
    print("─" * 28)
    
    # Economia de tokens (quanto menor, melhor)
    token_efficiency = min(100, (1 - avg_tokens / TOKENS_WITHOUT_MCP) * 100)
    print(f"Economia de Tokens:  {create_progress_bar(token_efficiency)}")
    
    # Utilização do orçamento (ideal: 60-80%)
    budget_color = "🟢" if 60 <= avg_util <= 80 else "🟡" if avg_util < 60 else "🔴"
    print(f"Uso do Orçamento:    {create_progress_bar(avg_util)} {budget_color}")
    
    # Performance (quanto menor latência, melhor - invertido para visualização)
    perf_score = max(0, min(100, 100 - (avg_latency / 10)))  # 1000ms = 0%, 0ms = 100%
    print(f"Performance:         {create_progress_bar(perf_score)}")
    print()

def print_daily_trends(daily_rows: List[Dict]):
    """Imprime tendências diárias simplificadas"""
    if len(daily_rows) <= 1:
        return
        
    print("📈 TENDÊNCIA DOS ÚLTIMOS DIAS")
    print("─" * 29)
    print(f"{'Data':<12} {'Tokens':<10} {'Economia':<10} {'Latência':<10}")
    print("─" * 45)
    
    for row in daily_rows[-7:]:  # Últimos 7 dias
        tokens = format_number(row['avg_tokens'])
        savings = calculate_savings(row['avg_tokens'])
        economy = f"{savings['reduction_pct']:.1f}%"
        latency = f"{row['avg_latency']:.0f}ms"
        
        print(f"{row['day']:<12} {tokens:<10} {economy:<10} {latency:<10}")
    print()

def print_insights(avg_tokens: float, avg_util: float, avg_latency: float, total_queries: int):
    """Imprime insights e recomendações"""
    print("💡 INSIGHTS E RECOMENDAÇÕES")
    print("─" * 27)

    # Análise de economia
    savings_pct = ((TOKENS_WITHOUT_MCP - avg_tokens) / TOKENS_WITHOUT_MCP) * 100
    if savings_pct > 90:
        print("   🎉 Excelente! Economia de tokens superior a 90%")
    elif savings_pct > 80:
        print("   ✅ Boa economia de tokens, sistema funcionando bem")
    elif savings_pct > 50:
        print("   ⚠️  Economia moderada, considere ajustar orçamento")
    else:
        print("   🔴 Economia baixa, revisar configurações urgentemente")

    # Análise de performance
    if avg_latency < 100:
        print("   ⚡ Performance excelente, buscas muito rápidas")
    elif avg_latency < 200:
        print("   ✅ Performance boa, latência aceitável")
    else:
        print("   ⚠️  Latência alta, considere otimizações")

    # Análise de utilização
    if 70 <= avg_util <= 90:
        print("   🎯 Utilização de orçamento ideal")
    elif avg_util < 70:
        print("   💡 Orçamento subutilizado, pode aumentar max_chunks")
    else:
        print("   ⚠️  Orçamento sobrecarregado, reduzir max_chunks")

    # Projeção de economia mensal
    monthly_queries = max(1000, total_queries * 30)  # Estimativa baseada em dados atuais
    monthly_savings = ((TOKENS_WITHOUT_MCP - avg_tokens) / 1000) * COST_PER_1K_TOKENS * monthly_queries
    print(f"   💰 Economia projetada mensal: ${monthly_savings:.2f}")
    print()
    print()

# Importar funções originais necessárias
def p95(vals: List[float]) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    return s[floor(0.95 * (len(s) - 1))]

def coerce_int(s, default=0):
    try:
        return int(s)
    except (ValueError, TypeError):
        return default

def coerce_float(s, default=0.0):
    try:
        return float(s)
    except (ValueError, TypeError):
        return default

def parse_dt(s: str) -> Optional[dt.datetime]:
    if not s:
        return None
    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"]:
        try:
            d = dt.datetime.strptime(s, fmt)
            if "%z" not in fmt:
                d = d.replace(tzinfo=dt.timezone.utc)
            return d
        except ValueError:
            continue
    return None

def _as_tz(d: dt.datetime, tz_mode: str) -> dt.datetime:
    if not d:
        return d
    if tz_mode == "utc":
        return d.astimezone(dt.timezone.utc)
    try:
        local_tz = dt.datetime.now().astimezone().tzinfo
        return d.astimezone(local_tz)
    except Exception:
        return d

def _resolve_path(path_arg: str) -> pathlib.Path:
    expanded = os.path.expandvars(os.path.expanduser(path_arg))
    p = pathlib.Path(expanded)
    if not p.is_absolute():
        candidates = [ROOT_DIR / p, pathlib.Path.cwd() / p]
        for c in candidates:
            if c.exists():
                return c
        return candidates[0]
    return p

def _load_context_csv(path: pathlib.Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        has_query = "query" in (reader.fieldnames or [])
        for row in reader:
            if not has_query:
                # Dados de indexação - converter para formato de métricas
                chunks = coerce_int(row.get("chunks", 0))
                estimated_tokens = chunks * ESTIMATED_TOKENS_PER_CHUNK  # Usar estimativa realista
                rows.append({
                    "ts": row.get("ts", ""),
                    "query": f"index_{row.get('op', 'unknown')}",
                    "chunk_count": str(chunks),
                    "total_tokens": str(estimated_tokens),
                    "budget_tokens": "2000",  # Novo orçamento padrão
                    "budget_utilization": str(min(100, estimated_tokens / 2000 * 100)),  # Limitar a 100%
                    "latency_ms": str(coerce_float(row.get("elapsed_s", 0)) * 1000),
                })
            else:
                rows.append(row)
    return rows

def load_rows(args) -> List[Dict[str, Any]]:
    if args.file:
        p = _resolve_path(args.file)
        if not p.exists():
            print(f"❌ CSV não encontrado: {p}")
            sys.exit(1)
        return _load_context_csv(p)
    else:
        # Procurar automaticamente apenas arquivos de contexto
        default_path = INDEX_DIR / "metrics_context.csv"
        if default_path.exists():
            return _load_context_csv(default_path)
        else:
            print("❌ Nenhum arquivo de métricas de contexto encontrado.")
            print(f"💡 Procure por: {default_path}")
            return []

    candidates = [
        DEFAULT_CONTEXT_PATH,
        DEFAULT_INDEX_PATH,
        LEGACY_METRICS_PATH,
        ROOT_DIR.parent / ".mcp_index" / "metrics_context.csv",
        ROOT_DIR.parent / ".mcp_index" / "metrics_index.csv",
        ROOT_DIR.parent / ".mcp_index" / "metrics.csv",
    ]

    found = [p for p in candidates if p.exists()]
    if not found:
        print("❌ Nenhum CSV de métricas encontrado.")
        print("\n💡 Dica: Execute algumas consultas primeiro para gerar métricas!")
        sys.exit(1)

    all_rows: List[Dict[str, Any]] = []
    for p in found:
        try:
            all_rows.extend(_load_context_csv(p))
        except Exception as e:
            print(f"⚠️  Falha ao ler {p}: {e}")

    return all_rows

def filter_rows(rows: List[Dict], since_days: int = 0, query_filter: str = "") -> List[Dict]:
    if since_days > 0:
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=since_days)
        rows = [r for r in rows if parse_dt(r.get("ts")) and parse_dt(r.get("ts")) >= cutoff]

    if query_filter:
        rows = [r for r in rows if query_filter.lower() in str(r.get("query", "")).lower()]

    return rows

def format_dt(d: dt.datetime) -> str:
    return d.strftime("%Y-%m-%d")

def summarize_enhanced(rows: List[Dict], args):
    """Versão melhorada da função summarize com visualizações intuitivas"""
    if not rows:
        print("❌ Nenhum dado encontrado.")
        print("💡 Execute algumas consultas MCP primeiro para gerar métricas!")
        return

    print_header()

    # Converter timestamps e ordenar
    tz_mode = args.tz
    parsed_rows = []
    for r in rows:
        d = parse_dt(r.get("ts"))
        if not d:
            continue
        parsed_rows.append((r, d))
    parsed_rows.sort(key=lambda x: x[1])

    # Calcular estatísticas
    total_rows = len(parsed_rows)
    first_ts = parsed_rows[0][1] if parsed_rows else None
    last_ts = parsed_rows[-1][1] if parsed_rows else None

    chunk_counts = [coerce_int(r[0]["chunk_count"]) for r in parsed_rows]
    total_tokens_list = [coerce_int(r[0]["total_tokens"]) for r in parsed_rows]
    budget_utilizations = [coerce_float(r[0]["budget_utilization"]) for r in parsed_rows]
    latencies = [coerce_float(r[0]["latency_ms"]) for r in parsed_rows]

    avg_chunks = st.mean(chunk_counts) if chunk_counts else 0
    avg_tokens = st.mean(total_tokens_list) if total_tokens_list else 0
    avg_util = st.mean(budget_utilizations) if budget_utilizations else 0
    avg_latency = st.mean(latencies) if latencies else 0

    # Agrupar por dia
    daily_stats: Dict[str, Dict[str, List[float]]] = {}
    for r, d in parsed_rows:
        ts_local = _as_tz(d, tz_mode)
        day = format_dt(ts_local)
        if day not in daily_stats:
            daily_stats[day] = {
                "chunk_counts": [],
                "total_tokens": [],
                "budget_utilizations": [],
                "latencies": [],
            }
        daily_stats[day]["chunk_counts"].append(coerce_int(r["chunk_count"]))
        daily_stats[day]["total_tokens"].append(coerce_int(r["total_tokens"]))
        daily_stats[day]["budget_utilizations"].append(coerce_float(r["budget_utilization"]))
        daily_stats[day]["latencies"].append(coerce_float(r["latency_ms"]))

    daily_rows = []
    for day, stats in sorted(daily_stats.items()):
        daily_rows.append({
            "day": day,
            "avg_chunks": st.mean(stats["chunk_counts"]) if stats["chunk_counts"] else 0,
            "avg_tokens": st.mean(stats["total_tokens"]) if stats["total_tokens"] else 0,
            "avg_util": st.mean(stats["budget_utilizations"]) if stats["budget_utilizations"] else 0,
            "avg_latency": st.mean(stats["latencies"]) if stats["latencies"] else 0,
        })

    # Saída JSON se solicitado
    if args.json:
        savings = calculate_savings(avg_tokens)
        output = {
            "summary": {
                "period_start": format_dt(_as_tz(first_ts, tz_mode)) if first_ts else "",
                "period_end": format_dt(_as_tz(last_ts, tz_mode)) if last_ts else "",
                "total_queries": total_rows,
                "avg_tokens": avg_tokens,
                "avg_latency_ms": avg_latency,
                "savings": savings,
            },
            "daily": daily_rows,
        }
        print(json.dumps(output, indent=2))
        return

    # Exibir resumo geral
    period = f"{format_dt(_as_tz(first_ts, tz_mode)) if first_ts else 'N/A'} a {format_dt(_as_tz(last_ts, tz_mode)) if last_ts else 'N/A'}"
    
    print_summary_card("RESUMO GERAL", {
        "Período": period,
        "Total de consultas": total_rows,
        "Tokens médios por consulta": f"{avg_tokens:.0f}",
        "Latência média": f"{avg_latency:.0f}ms",
        "Chunks médios": f"{avg_chunks:.1f}",
    })

    # Comparação com/sem MCP
    savings = calculate_savings(avg_tokens)
    print(create_comparison_table(avg_tokens))
    print()

    # Barras de eficiência
    print_efficiency_bars(avg_tokens, avg_util, avg_latency)

    # Tendências diárias
    if len(daily_rows) > 1:
        print_daily_trends(daily_rows)

    # Insights e recomendações
    print_insights(avg_tokens, avg_util, avg_latency, total_rows)

def main():
    parser = argparse.ArgumentParser(description="Relatório de Performance do MCP - Versão Melhorada")
    parser.add_argument("--file", default="", help="Arquivo CSV específico")
    parser.add_argument("--since", type=int, default=0, help="Filtrar por dias recentes")
    parser.add_argument("--filter", default="", help="Filtrar por termo na query")
    parser.add_argument("--tz", choices=["local", "utc"], default="local", help="Fuso horário")
    parser.add_argument("--json", action="store_true", help="Saída em JSON")

    args = parser.parse_args()

    try:
        rows = load_rows(args)
        rows = filter_rows(rows, args.since, args.filter)
        summarize_enhanced(rows, args)
    except SystemExit:
        raise
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()