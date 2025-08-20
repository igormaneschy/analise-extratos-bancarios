#!/usr/bin/env python3
"""
Resumo de métricas do MCP (context_pack) a partir de .mcp_index/metrics.csv

Campos esperados no CSV:
  ts, query, chunk_count, total_tokens, budget_tokens, budget_utilization, latency_ms

Uso básico:
  python summarize_metrics.py
  python summarize_metrics.py --file .mcp_index/metrics.csv
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
    except Exception:
        try:
            return int(float(s))
        except Exception:
            return default

def parse_args():
    parser = argparse.ArgumentParser(description="Resumo de métricas do MCP (CSV).")
    parser.add_argument("--file", "-f", default=os.environ.get("MCP_METRICS_FILE", ".mcp_index/metrics.csv"),
                        help="Caminho do CSV (default: .mcp_index/metrics.csv ou $MCP_METRICS_FILE)")
    parser.add_argument("--since", type=int, default=None,
                        help="Somente últimos N dias (ex.: --since 7)")
    parser.add_argument("--filter", type=str, default=None,
                        help="Filtra linhas cujo 'query' contém este texto (case-insensitive)")
    parser.add_argument("--json", action="store_true",
                        help="Imprime JSON ao invés de tabela")
    return parser.parse_args()

def load_rows(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        print(f"[erro] CSV não encontrado: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        print("[aviso] CSV está vazio.", file=sys.stderr)
    return rows

def within_since(ts_iso: str, since_days: int) -> bool:
    try:
        # suporta 'YYYY-MM-DDTHH:MM:SS' (com/sem timezone)
        d = dt.datetime.fromisoformat(ts_iso.replace("Z",""))
    except Exception:
        return True  # se não der pra parsear, não filtra
    return (dt.datetime.utcnow() - d) <= dt.timedelta(days=since_days)

def summarize(rows: List[Dict[str, Any]], args):
    # filtros
    if args.since is not None:
        rows = [r for r in rows if within_since(r.get("ts",""), args.since)]
    if args.filter:
        q = args.filter.lower()
        rows = [r for r in rows if q in (r.get("query","").lower())]

    if not rows:
        return {"overall": {}, "daily": []}

    # agrega por dia (YYYY-MM-DD)
    by_day: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        ts = r.get("ts","")
        day = ts[:10] if len(ts) >= 10 else "unknown"
        by_day.setdefault(day, []).append(r)

    # funções helpers
    def stats_for(values: List[float]) -> Dict[str, float]:
        if not values:
            return {"avg":0.0, "med":0.0, "p95":0.0, "min":0.0, "max":0.0}
        return {
            "avg": round(sum(values)/len(values), 2),
            "med": round(st.median(values), 2),
            "p95": round(p95(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
        }

    # diário
    daily = []
    all_tokens = []
    all_lat = []
    all_chunks = []
    period_start = None
    period_end = None

    for day in sorted(by_day.keys()):
        rs = by_day[day]
        toks = [coerce_int(r.get("total_tokens",0)) for r in rs]
        lat = [coerce_int(r.get("latency_ms",0)) for r in rs]
        chs = [coerce_int(r.get("chunk_count",0)) for r in rs]
        util = []
        for r in rs:
            try:
                util.append(float(r.get("budget_utilization", 0)))
            except Exception:
                pass

        all_tokens.extend(toks)
        all_lat.extend(lat)
        all_chunks.extend(chs)

        if period_start is None:
            try:
                period_start = day
            except Exception:
                pass
        period_end = day

        daily.append({
            "day": day,
            "n": len(rs),
            "tokens": stats_for(toks),
            "latency_ms": stats_for(lat),
            "chunk_count_avg": round(sum(chs)/len(chs), 2) if chs else 0.0,
            "budget_util_avg": round(sum(util)/len(util), 3) if util else 0.0,
        })

    overall = {
        "period": {"start": period_start, "end": period_end},
        "n": len(rows),
        "tokens": {
            "avg": round(sum(all_tokens)/len(all_tokens), 2) if all_tokens else 0.0,
            "med": round(st.median(all_tokens), 2) if all_tokens else 0.0,
            "p95": round(p95(all_tokens), 2) if all_tokens else 0.0,
            "min": min(all_tokens) if all_tokens else 0,
            "max": max(all_tokens) if all_tokens else 0,
            "sum": int(sum(all_tokens)) if all_tokens else 0,
        },
        "latency_ms": {
            "avg": round(sum(all_lat)/len(all_lat), 2) if all_lat else 0.0,
            "med": round(st.median(all_lat), 2) if all_lat else 0.0,
            "p95": round(p95(all_lat), 2) if all_lat else 0.0,
            "min": min(all_lat) if all_lat else 0,
            "max": max(all_lat) if all_lat else 0,
        },
        "chunk_count_avg": round(sum(all_chunks)/len(all_chunks), 2) if all_chunks else 0.0,
    }

    return {"overall": overall, "daily": daily}

def print_table(summary: Dict[str, Any]):
    overall = summary.get("overall", {})
    daily = summary.get("daily", [])

    print("\n=== OVERALL ===")
    if not overall:
        print("sem dados após filtros.")
        return

    per = overall["period"]
    print(f"Período: {per.get('start','?')} → {per.get('end','?')}")
    print(f"N linhas: {overall['n']}")
    print(f"Tokens  | avg: {overall['tokens']['avg']}, med: {overall['tokens']['med']}, p95: {overall['tokens']['p95']}, sum: {overall['tokens']['sum']}")
    print(f"Lat(ms) | avg: {overall['latency_ms']['avg']}, med: {overall['latency_ms']['med']}, p95: {overall['latency_ms']['p95']}")
    print(f"Chunk count médio: {overall['chunk_count_avg']}")
    print("\n=== DAILY ===")
    print(f"{'day':<12} {'n':>4}  {'tok_avg':>8} {'tok_med':>8} {'tok_p95':>8}   {'lat_avg':>8} {'lat_p95':>8}   {'chunks_avg':>10} {'budget_u_avg':>12}")
    for d in daily:
        print(f"{d['day']:<12} {d['n']:>4}  "
              f"{d['tokens']['avg']:>8} {d['tokens']['med']:>8} {d['tokens']['p95']:>8}   "
              f"{d['latency_ms']['avg']:>8} {d['latency_ms']['p95']:>8}   "
              f"{d['chunk_count_avg']:>10} {d['budget_util_avg']:>12}")

def main():
    args = parse_args()
    rows = load_rows(args.file)
    summary = summarize(rows, args)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print_table(summary)

if __name__ == "__main__":
    main()
