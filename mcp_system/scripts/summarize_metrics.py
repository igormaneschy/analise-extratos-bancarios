
#!/usr/bin/env python3
"""
Resumo de métricas do MCP a partir de arquivos CSV na pasta mcp_system/.mcp_index

Agora com suporte a múltiplas fontes por padrão:
- metrics_context.csv (consultas/context_pack)
- metrics_index.csv (indexações)
- metrics.csv (legado)

Campos esperados nos CSVs:
  Contexto: ts, query, chunk_count, total_tokens, budget_tokens, budget_utilization, latency_ms
  Indexação: ts, op, path, index_dir, files_indexed, chunks, recursive, include_globs, exclude_globs, elapsed_s

Uso básico:
  python summarize_metrics.py                # lê todas as fontes acima automaticamente
  python summarize_metrics.py --file mcp_system/.mcp_index/metrics_context.csv
  python summarize_metrics.py --since 7
  python summarize_metrics.py --filter "minha funcao"
  python summarize_metrics.py --json
  python summarize_metrics.py --tz local|utc  # agrupamento por dia no fuso desejado (default: local)
"""

import os, sys, csv, argparse, datetime as dt, statistics as st, json
from math import floor
from typing import List, Dict, Any, Optional
import pathlib

# Diretórios de referência
CURRENT_DIR = pathlib.Path(__file__).parent.absolute()  # mcp_system/scripts
ROOT_DIR = CURRENT_DIR.parent  # mcp_system
INDEX_DIR = ROOT_DIR / ".mcp_index"
DEFAULT_CONTEXT_PATH = INDEX_DIR / "metrics_context.csv"
DEFAULT_INDEX_PATH = INDEX_DIR / "metrics_index.csv"
LEGACY_METRICS_PATH = INDEX_DIR / "metrics.csv"


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
    # Tentar diferentes formatos de data
    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"]:
        try:
            d = dt.datetime.strptime(s, fmt)
            # Se não tem timezone (%z), assume UTC para manter consistência
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
    # Local
    try:
        local_tz = dt.datetime.now().astimezone().tzinfo
        return d.astimezone(local_tz)
    except Exception:
        return d  # fallback


def _resolve_path(path_arg: str) -> pathlib.Path:
    expanded = os.path.expandvars(os.path.expanduser(path_arg))
    p = pathlib.Path(expanded)
    if not p.is_absolute():
        # Tentar relativo ao ROOT_DIR e ao CWD
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
        # Valida presença de coluna "query" para confirmar tipo
        has_query = "query" in (reader.fieldnames or [])
        for row in reader:
            if not has_query:
                # Converter métrica de indexação para formato de contexto
                rows.append({
                    "ts": row.get("ts", ""),
                    "query": f"index_{row.get('op', 'unknown')}",
                    "chunk_count": str(coerce_int(row.get("chunks", 0))),
                    "total_tokens": str(coerce_int(row.get("chunks", 0)) * 50),  # Estimativa
                    "budget_tokens": "8000",
                    "budget_utilization": str(coerce_float(row.get("chunks", 0)) * 50 / 8000 * 100),
                    "latency_ms": str(coerce_float(row.get("elapsed_s", 0)) * 1000),
                })
            else:
                rows.append(row)
    return rows


def load_rows(args) -> List[Dict[str, Any]]:
    # Se --file for informado, lê apenas aquele arquivo
    if args.file:
        p = _resolve_path(args.file)
        if not p.exists():
            print(f"[erro] CSV não encontrado: {p}")
            sys.exit(1)
        return _load_context_csv(p)

    # Sem --file: tentar múltiplas fontes (contexto, index e legado) tanto em mcp_system quanto na raiz
    candidates = [
        DEFAULT_CONTEXT_PATH,
        DEFAULT_INDEX_PATH,
        LEGACY_METRICS_PATH,
        # Fallbacks na raiz do projeto
        ROOT_DIR.parent / ".mcp_index" / "metrics_context.csv",
        ROOT_DIR.parent / ".mcp_index" / "metrics_index.csv",
        ROOT_DIR.parent / ".mcp_index" / "metrics.csv",
    ]

    found = [p for p in candidates if p.exists()]
    if not found:
        print("[erro] Nenhum CSV de métricas encontrado. Locais esperados:")
        for c in candidates:
            print(f"  - {c}")
        print("\nDica: gere métricas executando consultas (context_pack) ou reindexações; ou informe o caminho via --file.")
        sys.exit(1)

    all_rows: List[Dict[str, Any]] = []
    for p in found:
        try:
            all_rows.extend(_load_context_csv(p))
        except Exception as e:
            print(f"[aviso] Falha ao ler {p}: {e}")

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


def summarize(rows: List[Dict], args):
    if not rows:
        print("Nenhum dado encontrado.")
        return

    # Converter timestamps e ordenar
    tz_mode = args.tz
    parsed_rows = []
    for r in rows:
        d = parse_dt(r.get("ts"))
        if not d:
            continue
        parsed_rows.append((r, d))
    parsed_rows.sort(key=lambda x: x[1])

    # Resumo geral
    total_rows = len(parsed_rows)
    first_ts = parsed_rows[0][1] if parsed_rows else None
    last_ts = parsed_rows[-1][1] if parsed_rows else None

    # Converter valores para números
    chunk_counts = [coerce_int(r[0]["chunk_count"]) for r in parsed_rows]
    total_tokens_list = [coerce_int(r[0]["total_tokens"]) for r in parsed_rows]
    budget_utilizations = [coerce_float(r[0]["budget_utilization"]) for r in parsed_rows]
    latencies = [coerce_float(r[0]["latency_ms"]) for r in parsed_rows]

    # Calcular estatísticas
    avg_chunks = st.mean(chunk_counts) if chunk_counts else 0
    avg_tokens = st.mean(total_tokens_list) if total_tokens_list else 0
    avg_util = st.mean(budget_utilizations) if budget_utilizations else 0
    avg_latency = st.mean(latencies) if latencies else 0

    p95_chunks = p95(chunk_counts)
    p95_tokens = p95(total_tokens_list)
    p95_util = p95(budget_utilizations)
    p95_latency = p95(latencies)

    # Agrupar por dia (no fuso escolhido)
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
                "period_start": format_dt(_as_tz(first_ts, tz_mode)) if first_ts else "",
                "period_end": format_dt(_as_tz(last_ts, tz_mode)) if last_ts else "",
                "total_queries": total_rows,
                "avg_chunks": avg_chunks,
                "avg_tokens": avg_tokens,
                "avg_budget_utilization_pct": avg_util,
                "avg_latency_ms": avg_latency,
                "p95_chunks": p95_chunks,
                "p95_tokens": p95_tokens,
                "p95_budget_utilization_pct": p95_util,
                "p95_latency_ms": p95_latency,
            },
            "daily": daily_rows,
        }
        print(json.dumps(output, indent=2))
        return

    # Saída em texto formatado
    print("=== RESUMO DE MÉTRICAS DO MCP ===")
    print(
        f"Período: {format_dt(_as_tz(first_ts, tz_mode)) if first_ts else 'N/A'} a {format_dt(_as_tz(last_ts, tz_mode)) if last_ts else 'N/A'} ({total_rows} entradas)"
    )
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
    parser.add_argument(
        "--file",
        default="",
        help="Arquivo CSV de métricas específico. Se omitido, lê todas as fontes padrões (context, index e legado).",
    )
    parser.add_argument("--since", type=int, default=0, help="Filtrar por dias recentes")
    parser.add_argument("--filter", default="", help="Filtrar por termo na query")
    parser.add_argument("--tz", choices=["local", "utc"], default="local", help="Fuso horário para agrupamento diário")
    parser.add_argument("--json", action="store_true", help="Saída em JSON")

    args = parser.parse_args()

    try:
        rows = load_rows(args)
        rows = filter_rows(rows, args.since, args.filter)
        summarize(rows, args)
    except SystemExit:
        raise
    except Exception as e:
        print(f"[erro] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
