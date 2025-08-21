#!/usr/bin/env python3
"""
Resumo de métricas do MCP (context_pack) a partir de mcp_system/.mcp_index/metrics.csv

Campos esperados no CSV:
  ts, query, chunk_count, total_tokens, budget_tokens, budget_utilization, latency_ms

Uso básico:
  python summarize_metrics.py
  python summarize_metrics.py --file mcp_system/.mcp_index/metrics.csv
  python summarize_metrics.py --since 7
  python summarize_metrics.py --filter "minha funcao"
  python summarize_metrics.py --json

Saída:
- Resumo geral (período, N linhas, tokens médios, p95, etc.)
- Tabela diária com avg/median/p95 de tokens e latência
"""

import os, sys, csv, argparse, datetime as dt, statistics as st, json
from math import floor
from typing import List, Dict, Any

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

def parse_dt(s):
    if not s:
        return None
    # Tentar diferentes formatos de data
    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"]:
        try:
            if fmt.endswith("%z"):
                return dt.datetime.strptime(s, fmt)
            else:
                return dt.datetime.strptime(s, fmt).replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
    return None

def load_csv(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        print(f"[erro] CSV não encontrado: {path}")
        sys.exit(1)
    
    with open(path) as f:
        # Detectar se é o arquivo de métricas de indexação ou de context pack
        first_line = f.readline()
        f.seek(0)
        
        if "query" in first_line:
            # Arquivo de métricas de context pack
            reader = csv.DictReader(f)
            return [row for row in reader]
        else:
            # Arquivo de métricas de indexação - converter para o formato esperado
            reader = csv.DictReader(f)
            converted_rows = []
            
            for row in reader:
                # Converter métricas de indexação para o formato de context pack
                converted_row = {
                    "ts": row.get("ts", ""),
                    "query": f"index_{row.get('op', 'unknown')}",
                    "chunk_count": str(coerce_int(row.get("chunks", 0))),
                    "total_tokens": str(coerce_int(row.get("chunks", 0)) * 50),  # Estimativa de tokens
                    "budget_tokens": "8000",  # Valor padrão
                    "budget_utilization": str(coerce_float(row.get("chunks", 0)) * 50 / 8000 * 100),  # Estimativa
                    "latency_ms": str(coerce_float(row.get("elapsed_s", 0)) * 1000)
                }
                converted_rows.append(converted_row)
            
            return converted_rows

def filter_rows(rows: List[Dict], since_days: int = 0, query_filter: str = "") -> List[Dict]:
    if since_days > 0:
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=since_days)
        rows = [r for r in rows if parse_dt(r["ts"]) and parse_dt(r["ts"]) >= cutoff]
    
    if query_filter:
        rows = [r for r in rows if query_filter.lower() in r["query"].lower()]
    
    return rows

def format_dt(d: dt.datetime) -> str:
    return d.strftime("%Y-%m-%d")

def summarize(rows: List[Dict], args):
    if not rows:
        print("Nenhum dado encontrado.")
        return

    # Resumo geral
    total_rows = len(rows)
    first_ts = min(parse_dt(r["ts"]) for r in rows if parse_dt(r["ts"]))
    last_ts = max(parse_dt(r["ts"]) for r in rows if parse_dt(r["ts"]))
    
    # Converter valores para números
    chunk_counts = [coerce_int(r["chunk_count"]) for r in rows]
    total_tokens_list = [coerce_int(r["total_tokens"]) for r in rows]
    budget_utilizations = [coerce_float(r["budget_utilization"]) for r in rows]
    latencies = [coerce_float(r["latency_ms"]) for r in rows]
    
    # Calcular estatísticas
    avg_chunks = st.mean(chunk_counts) if chunk_counts else 0
    avg_tokens = st.mean(total_tokens_list) if total_tokens_list else 0
    avg_util = st.mean(budget_utilizations) if budget_utilizations else 0
    avg_latency = st.mean(latencies) if latencies else 0
    
    p95_chunks = p95(chunk_counts)
    p95_tokens = p95(total_tokens_list)
    p95_util = p95(budget_utilizations)
    p95_latency = p95(latencies)
    
    # Agrupar por dia
    daily_stats = {}
    for row in rows:
        ts = parse_dt(row["ts"])
        if not ts:
            continue
        day = format_dt(ts)
        if day not in daily_stats:
            daily_stats[day] = {
                "chunk_counts": [],
                "total_tokens": [],
                "budget_utilizations": [],
                "latencies": []
            }
        daily_stats[day]["chunk_counts"].append(coerce_int(row["chunk_count"]))
        daily_stats[day]["total_tokens"].append(coerce_int(row["total_tokens"]))
        daily_stats[day]["budget_utilizations"].append(coerce_float(row["budget_utilization"]))
        daily_stats[day]["latencies"].append(coerce_float(row["latency_ms"]))
    
    # Converter para formato de tabela
    daily_rows = []
    for day, stats in sorted(daily_stats.items()):
        daily_rows.append({
            "day": day,
            "avg_chunks": st.mean(stats["chunk_counts"]) if stats["chunk_counts"] else 0,
            "median_chunks": st.median(stats["chunk_counts"]) if stats["chunk_counts"] else 0,
            "p95_chunks": p95(stats["chunk_counts"]),
            "avg_tokens": st.mean(stats["total_tokens"]) if stats["total_tokens"] else 0,
            "median_tokens": st.median(stats["total_tokens"]) if stats["total_tokens"] else 0,
            "p95_tokens": p95(stats["total_tokens"]),
            "avg_util": st.mean(stats["budget_utilizations"]) if stats["budget_utilizations"] else 0,
            "median_util": st.median(stats["budget_utilizations"]) if stats["budget_utilizations"] else 0,
            "p95_util": p95(stats["budget_utilizations"]),
            "avg_latency": st.mean(stats["latencies"]) if stats["latencies"] else 0,
            "median_latency": st.median(stats["latencies"]) if stats["latencies"] else 0,
            "p95_latency": p95(stats["latencies"]),
        })
    
    # Saída JSON se solicitado
    if args.json:
        output = {
            "summary": {
                "period_start": format_dt(first_ts) if first_ts else "",
                "period_end": format_dt(last_ts) if last_ts else "",
                "total_queries": total_rows,
                "avg_chunks": avg_chunks,
                "avg_tokens": avg_tokens,
                "avg_budget_utilization_pct": avg_util,
                "avg_latency_ms": avg_latency,
                "p95_chunks": p95_chunks,
                "p95_tokens": p95_tokens,
                "p95_budget_utilization_pct": p95_util,
                "p95_latency_ms": p95_latency
            },
            "daily": daily_rows
        }
        print(json.dumps(output, indent=2))
        return
    
    # Saída em texto formatado
    print("=== RESUMO DE MÉTRICAS DO MCP ===")
    print(f"Período: {format_dt(first_ts) if first_ts else 'N/A'} a {format_dt(last_ts) if last_ts else 'N/A'} ({total_rows} consultas)")
    print()
    print("Média Geral:")
    print(f"  Chunks:     {avg_chunks:.1f} (p95: {p95_chunks:.1f})")
    print(f"  Tokens:     {avg_tokens:.0f} (p95: {p95_tokens:.0f})")
    print(f"  Utilização: {avg_util:.1f}% (p95: {p95_util:.1f}%)")
    print(f"  Latência:   {avg_latency:.1f}ms (p95: {p95_latency:.1f}ms)")
    print()
    print("Diário:")
    print(f"{'Dia':<12} {'Chunks':<24} {'Tokens':<24} {'Utilização':<24} {'Latência (ms)':<24}")
    print(f"{'':<12} {'avg/median/p95':<24} {'avg/median/p95':<24} {'avg/median/p95':<24} {'avg/median/p95':<24}")
    print("-" * 100)
    
    for row in daily_rows:
        chunks_str = f"{row['avg_chunks']:.1f}/{row['median_chunks']:.1f}/{row['p95_chunks']:.1f}"
        tokens_str = f"{row['avg_tokens']:.0f}/{row['median_tokens']:.0f}/{row['p95_tokens']:.0f}"
        util_str = f"{row['avg_util']:.1f}/{row['median_util']:.1f}/{row['p95_util']:.1f}"
        latency_str = f"{row['avg_latency']:.1f}/{row['median_latency']:.1f}/{row['p95_latency']:.1f}"
        
        print(f"{row['day']:<12} {chunks_str:<24} {tokens_str:<24} {util_str:<24} {latency_str:<24}")

def main():
    parser = argparse.ArgumentParser(description="Resumo de métricas do MCP")
    parser.add_argument("--file", default="mcp_system/.mcp_index/metrics.csv", help="Arquivo CSV de métricas")
    parser.add_argument("--since", type=int, default=0, help="Filtrar por dias recentes")
    parser.add_argument("--filter", default="", help="Filtrar por termo na query")
    parser.add_argument("--json", action="store_true", help="Saída em JSON")
    
    args = parser.parse_args()
    
    try:
        rows = load_csv(args.file)
        rows = filter_rows(rows, args.since, args.filter)
        summarize(rows, args)
    except Exception as e:
        print(f"[erro] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()