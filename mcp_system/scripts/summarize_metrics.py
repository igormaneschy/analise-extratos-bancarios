#!/usr/bin/env python3
"""
Resumo de métricas do MCP (atualizado para o contexto atual)

- Consolida métricas de contexto e indexação: .mcp_index/metrics_context.csv e .mcp_index/metrics_index.csv
- Fallback para arquivo legado: .mcp_index/metrics.csv
- Suporta filtro por período, termo e fuso horário
- Saída JSON ou texto

Uso:
  python mcp_system/scripts/summarize_metrics.py                # lê apenas contexto por padrão
  python mcp_system/scripts/summarize_metrics.py --include-index # inclui métricas de indexação (em seção separada)
  python mcp_system/scripts/summarize_metrics.py --file mcp_system/.mcp_index/metrics_context.csv
  python mcp_system/scripts/summarize_metrics.py --since 7 --tz utc --json
  python -m mcp_system.scripts.summarize_metrics --since 7 --tz utc --json
"""

import os, sys, csv, argparse, datetime as dt, statistics as st, json
from math import floor
from typing import List, Dict, Any, Optional, Tuple
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
        return int(float(s))
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
    # 1) Tente ISO-8601 robusto (suporta timezone com dois-pontos e 'Z')
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        pass
    # 2) Tentar diferentes formatos comuns
    for fmt in [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S.%f",
    ]:
        try:
            d = dt.datetime.strptime(s, fmt)
            # Se não tem timezone, assume UTC para consistência
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


def _normalize_utilization(val: Any) -> float:
    """Normaliza budget_utilization para 0..100 (se vier 0..1, multiplica por 100)."""
    v = coerce_float(val, 0.0)
    if 0.0 <= v <= 1.0:
        v *= 100.0
    return v


def _read_csv(path: pathlib.Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    rows: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            rows.append(row)
    return rows, fieldnames


def _convert_index_to_context(row: Dict[str, Any]) -> Dict[str, Any]:
    chunks = coerce_int(row.get("chunks", 0))
    elapsed_s = coerce_float(row.get("elapsed_s", 0))
    estimated_tokens = chunks * 50  # Estimativa simples
    return {
        "ts": row.get("ts", ""),
        "query": f"index_{row.get('op', 'unknown')}",
        "chunk_count": str(chunks),
        "total_tokens": str(estimated_tokens),
        "budget_tokens": "8000",
        "budget_utilization": str(min(100.0, (estimated_tokens / 8000) * 100)),
        "latency_ms": str(elapsed_s * 1000),
    }


def load_context_rows(args) -> List[Dict[str, Any]]:
    # Se --file for informado, ler somente se for um CSV de contexto (tem coluna 'query')
    if args.file:
        p = _resolve_path(args.file)
        if not p.exists():
            print(f"[erro] CSV não encontrado: {p}")
            sys.exit(1)
        rows, fields = _read_csv(p)
        if "query" not in fields:
            return []
        out = []
        for r in rows:
            r = dict(r)
            # Fallback para total_tokens_sent quando total_tokens for 0/ausente
            try:
                tok = coerce_float(r.get("total_tokens"), 0.0)
            except Exception:
                tok = 0.0
            if tok <= 0 and "total_tokens_sent" in r:
                r["total_tokens"] = r.get("total_tokens_sent")
            r["budget_utilization"] = _normalize_utilization(r.get("budget_utilization"))
            out.append(r)
        return out

    # Caso padrão: procurar contexto e legado
    candidates = [DEFAULT_CONTEXT_PATH, LEGACY_METRICS_PATH]
    out: List[Dict[str, Any]] = []
    for c in candidates:
        if not c.exists():
            continue
        rows, fields = _read_csv(c)
        if "query" not in fields:
            # pular arquivos de indexação aqui
            continue
        for r in rows:
            r = dict(r)
            # Fallback para total_tokens_sent quando total_tokens for 0/ausente
            try:
                tok = coerce_float(r.get("total_tokens"), 0.0)
            except Exception:
                tok = 0.0
            if tok <= 0 and "total_tokens_sent" in r:
                r["total_tokens"] = r.get("total_tokens_sent")
            r["budget_utilization"] = _normalize_utilization(r.get("budget_utilization"))
            out.append(r)
    return out


def load_index_rows(args) -> List[Dict[str, Any]]:
    # Se --file for informado e não for de contexto, tratar como index
    if args.file:
        p = _resolve_path(args.file)
        if not p.exists():
            print(f"[erro] CSV não encontrado: {p}")
            sys.exit(1)
        rows, fields = _read_csv(p)
        if "query" in fields:
            return []
        out = []
        for r in rows:
            out.append(_convert_index_to_context(r))
        return out

    # Padrão: metrics_index.csv
    if not DEFAULT_INDEX_PATH.exists():
        return []
    rows, _ = _read_csv(DEFAULT_INDEX_PATH)
    return [_convert_index_to_context(r) for r in rows]


def filter_rows(rows: List[Dict], since_days: int = 0, query_filter: str = "") -> List[Dict]:
    # Anotar parsed timestamp para evitar re-parsing repetido
    parsed_cache = []
    cutoff = None
    if since_days > 0:
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=since_days)

    for r in rows:
        ts = r.get("ts")
        d = parse_dt(ts)
        # armazenar para uso posterior em _compute_stats
        if d:
            r["_parsed_ts"] = d
        else:
            r["_parsed_ts"] = None
        parsed_cache.append(r)

    out = parsed_cache
    if cutoff is not None:
        out = [r for r in out if r.get("_parsed_ts") and r.get("_parsed_ts") >= cutoff]

    if query_filter:
        out = [r for r in out if query_filter.lower() in str(r.get("query", "")).lower()]

    return out


def format_dt(d: dt.datetime) -> str:
    return d.strftime("%Y-%m-%d")


def _compute_stats(rows: List[Dict], tz_mode: str, ignore_zero_latency: bool) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    # Converter timestamps e ordenar
    parsed_rows = []
    for r in rows:
        # Reusar timestamp parseado se disponível (setado em filter_rows) para evitar reparsing
        d = r.get("_parsed_ts") if (r.get("_parsed_ts") is not None) else parse_dt(r.get("ts"))
        if not d:
            continue
        parsed_rows.append((r, d))
    parsed_rows.sort(key=lambda x: x[1])

    # Resumo geral
    total_rows = len(parsed_rows)
    first_ts = parsed_rows[0][1] if parsed_rows else None
    last_ts = parsed_rows[-1][1] if parsed_rows else None

    # Converter valores para números
    chunk_counts = [coerce_int(r[0].get("chunk_count")) for r in parsed_rows]
    total_tokens_list = [coerce_int(r[0].get("total_tokens")) for r in parsed_rows]
    budget_utilizations = [coerce_float(r[0].get("budget_utilization")) for r in parsed_rows]
    latencies_all = [coerce_float(r[0].get("latency_ms")) for r in parsed_rows]
    latencies_p = [v for v in latencies_all if v > 0] if ignore_zero_latency else latencies_all

    # Calcular estatísticas
    avg_chunks = st.mean(chunk_counts) if chunk_counts else 0
    avg_tokens = st.mean(total_tokens_list) if total_tokens_list else 0
    avg_util = st.mean(budget_utilizations) if budget_utilizations else 0
    avg_latency = st.mean(latencies_all) if latencies_all else 0

    p95_chunks = p95(chunk_counts)
    p95_tokens = p95(total_tokens_list)
    p95_util = p95(budget_utilizations)
    p95_latency = p95(latencies_p)

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
        daily_stats[day]["chunk_counts"].append(coerce_int(r.get("chunk_count")))
        daily_stats[day]["total_tokens"].append(coerce_int(r.get("total_tokens")))
        daily_stats[day]["budget_utilizations"].append(coerce_float(r.get("budget_utilization")))
        daily_stats[day]["latencies"].append(coerce_float(r.get("latency_ms")))

    daily_rows = []
    for day, stats in sorted(daily_stats.items()):
        lat_all = stats["latencies"]
        lat_p = [v for v in lat_all if v > 0] if ignore_zero_latency else lat_all
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
            "avg_latency": st.mean(lat_all) if lat_all else 0,
            "median_latency": st.median(lat_p) if lat_p else 0,
            "p95_latency": p95(lat_p),
        })

    summary = {
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
    }

    return summary, daily_rows


def _print_text(summary: Dict[str, Any], daily_rows: List[Dict[str, Any]], section_title: str = "RESUMO DE MÉTRICAS DO MCP"):
    print(f"=== {section_title} ===")
    print(
        f"Período: {summary['period_start'] or 'N/A'} a {summary['period_end'] or 'N/A'} ({summary['total_queries']} entradas)"
    )
    print()
    print("Média Geral:")
    print(f"  Chunks:     {summary['avg_chunks']:.1f} (p95: {summary['p95_chunks']:.1f})")
    print(f"  Tokens:     {summary['avg_tokens']:.0f} (p95: {summary['p95_tokens']:.0f})")
    print(f"  Utilização: {summary['avg_budget_utilization_pct']:.1f}% (p95: {summary['p95_budget_utilization_pct']:.1f}%)")
    print(f"  Latência:   {summary['avg_latency_ms']:.1f}ms (p95: {summary['p95_latency_ms']:.1f}ms)")
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
    parser = argparse.ArgumentParser(description="Resumo de métricas do MCP (atualizado)")
    parser.add_argument(
        "--file",
        default="",
        help="Arquivo CSV de métricas específico. Se omitido, lê contexto (.mcp_index/metrics_context.csv) e permite incluir index com --include-index.",
    )
    parser.add_argument("--since", type=int, default=0, help="Filtrar por dias recentes")
    parser.add_argument("--filter", default="", help="Filtrar por termo na query")
    parser.add_argument("--tz", choices=["local", "utc"], default="local", help="Fuso horário para agrupamento diário")
    parser.add_argument("--json", action="store_true", help="Saída em JSON")
    parser.add_argument("--include-index", action="store_true", help="Incluir métricas de indexação em seção separada")
    parser.add_argument("--ignore-zero-latency", action="store_true", help="Ignorar latências 0 apenas para mediana/p95")

    args = parser.parse_args()

    try:
        # Carregar contexto
        context_rows = load_context_rows(args)
        context_rows = filter_rows(context_rows, args.since, args.filter)

        # Opcional: carregar index
        index_rows: List[Dict[str, Any]] = []
        if args.include_index:
            index_rows = load_index_rows(args)
            index_rows = filter_rows(index_rows, args.since, args.filter)

        if args.json:
            ctx_summary, ctx_daily = _compute_stats(context_rows, args.tz, args.ignore_zero_latency)
            output: Dict[str, Any] = {"context": {"summary": ctx_summary, "daily": ctx_daily}}
            if args.include_index:
                idx_summary, idx_daily = _compute_stats(index_rows, args.tz, args.ignore_zero_latency)
                output["index"] = {"summary": idx_summary, "daily": idx_daily}
            # Normalize numeric types for JSON
            print(json.dumps(output, indent=2, ensure_ascii=False))
            return

        # Saída em texto
        if context_rows:
            ctx_summary, ctx_daily = _compute_stats(context_rows, args.tz, args.ignore_zero_latency)
            _print_text(ctx_summary, ctx_daily, section_title="RESUMO (CONTEXTO)")
        else:
            print("Nenhum dado de CONTEXTO encontrado.")

        if args.include_index:
            print()  # separador
            if index_rows:
                idx_summary, idx_daily = _compute_stats(index_rows, args.tz, args.ignore_zero_latency)
                _print_text(idx_summary, idx_daily, section_title="RESUMO (INDEXAÇÃO)")
            else:
                print("Nenhum dado de INDEXAÇÃO encontrado.")

    except SystemExit:
        raise
    except Exception as e:
        print(f"[erro] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
