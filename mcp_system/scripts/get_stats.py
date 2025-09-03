#!/usr/bin/env python3
"""
Coleta e imprime estatísticas do indexador/servidor MCP em formato amigável.

- Chama diretamente _handle_get_stats do servidor
- Útil para integração em CI ou inspeção manual

Uso:
    
  python -m mcp_system.scripts.get_stats --json
"""

import os
import sys
import json
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_MCP_DIR = _THIS_DIR.parent
_PROJECT_ROOT = _MCP_DIR.parent

# Garante que o pacote mcp_system seja importável quando executado como script direto
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Defaults de ambiente
os.environ.setdefault("INDEX_DIR", str(_MCP_DIR / ".mcp_index"))
os.environ.setdefault("INDEX_ROOT", str(_PROJECT_ROOT))


def _coalesce(d: dict, *keys, default="n/a"):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


import argparse

def _print_stats_payload(res: dict) -> int:
    if not isinstance(res, dict) or res.get("status") != "success":
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 1

    data = res.get("data", {})
    caps = data.get("capabilities", {})

    files_indexed = _coalesce(data, "total_files", "files_indexed")
    total_chunks = _coalesce(data, "total_chunks", "chunks")
    index_size_mb = data.get("index_size_mb", "n/a")
    last_updated = data.get("last_updated", "n/a")

    print("=== MCP Stats ===")
    print(f"Arquivos indexados: {files_indexed}")
    print(f"Chunks:             {total_chunks}")
    print(f"Tamanho do índice:  {index_size_mb} MB")
    print(f"Última atualização:  {last_updated}")
    if isinstance(caps, dict):
        print("Capacidades:")
        print(f"  - Busca semântica disponível: {caps.get('semantic_search', False)}")

    # Novas métricas de tokens (uso seguro de .get)
    print(f"Tokens enviados (última query): {data.get('last_query_total_tokens', 'n/a')}")
    print(f"Tokens poupados (última query): {data.get('last_query_tokens_saved', 'n/a')}")
    print(f"Tokens enviados (acumulado): {data.get('tokens_sent_total', 'n/a')}")
    print(f"Tokens poupados (acumulado): {data.get('tokens_saved_total', 'n/a')}")
    print(f"Tokens poupados por cache: {data.get('cache_tokens_saved_total', 'n/a')}")
    print(f"Tokens poupados por compressão: {data.get('compression_tokens_saved_total', 'n/a')}")

    print(f"  - Auto-indexação disponível:  {caps.get('auto_indexing', False)}")
    print(f"  - FastMCP:                   {caps.get('fastmcp', True)}")
    print(f"  - Semântica habilitada:      {caps.get('semantic_enabled', data.get('semantic_enabled', False))}")
    print(f"  - Auto-index habilitado:     {caps.get('auto_indexing_enabled', data.get('auto_indexing_enabled', False))}")

    return 0



def main():
    import argparse
    # Garantir que `res` exista mesmo se ocorrerem exceções durante a coleta de stats
    res = {}
    parser = argparse.ArgumentParser(description="Exibe estatísticas do servidor MCP e opcionalmente indexa um caminho antes.")
    parser.add_argument("--index", help="Caminho a indexar antes de exibir estatísticas")
    parser.add_argument("--recursive", dest="recursive", action="store_true", default=True, help="Indexar recursivamente (padrão)")
    parser.add_argument("--no-recursive", dest="recursive", action="store_false", help="Não indexar recursivamente")
    parser.add_argument("--semantic", dest="enable_semantic", action="store_true", default=True, help="Habilitar busca semântica (padrão)")
    parser.add_argument("--no-semantic", dest="enable_semantic", action="store_false", help="Desabilitar busca semântica")
    parser.add_argument("--watcher", dest="auto_start_watcher", action="store_true", default=True, help="Iniciar auto-indexação/watch (padrão)")
    parser.add_argument("--no-watcher", dest="auto_start_watcher", action="store_false", help="Não iniciar auto-indexação/watch")
    parser.add_argument("--exclude", default="", help="Padrões glob para excluir, separados por ';'")
    parser.add_argument("--debug", action="store_true", help="Ativa log detalhado (DEBUG)")
    parser.add_argument("--quiet", action="store_true", help="Mostra apenas erros (WARNING+)")
    parser.add_argument("--warmup", action="store_true", help="Executa warmup para inicializar contadores de tokens")
    parser.add_argument("--json", action="store_true", help="Imprime payload bruto JSON retornado pelo handler get_stats")
    # NOVO: permitir fixar MCP_DATA_DIR explicitamente
    parser.add_argument("--data-dir", help="Diretório de dados do MCP (override MCP_DATA_DIR)")
    args = parser.parse_args()

    # permitir timeout via env var (segundos) para chamadas longas, se desejar usar posteriormente
    try:
        DEFAULT_HANDLER_TIMEOUT = int(os.getenv("MCP_GET_STATS_TIMEOUT", "0"))
    except Exception:
        DEFAULT_HANDLER_TIMEOUT = 0

    # Aplicar override do MCP_DATA_DIR, se fornecido
    try:
        if args.data_dir:
            os.environ["MCP_DATA_DIR"] = str(Path(args.data_dir).expanduser().resolve())
            sys.stderr.write(f"[get_stats] MCP_DATA_DIR definido para: {os.environ['MCP_DATA_DIR']}\n")
    except Exception:
        pass

    try:
        from mcp_system.mcp_server_enhanced import _handle_get_stats, _handle_index_path  # type: ignore
    except Exception as e:
        print(f"[erro] Falha ao importar servidor MCP: {e}", file=sys.stderr)
        print("Dica: execute via módulo: python -m mcp_system.scripts.get_stats", file=sys.stderr)
        sys.exit(1)

    try:
        import mcp_system.mcp_server_enhanced as server

        if args.debug:
            if hasattr(server, "set_log_level"):
                server.set_log_level("DEBUG")
        elif args.quiet:
            if hasattr(server, "set_log_level"):
                server.set_log_level("WARNING")
        else:
            if hasattr(server, "set_log_level"):
                server.set_log_level("INFO")

        if args.warmup:
            if hasattr(server, "context_pack"):
                # Small token budget for fast warmup
                server.context_pack(query="__warmup__", token_budget=16, max_chunks=1, strategy="mmr")

        if hasattr(server, "ensure_ready"):
            server.ensure_ready()

        # Optional index before stats (ajustado para antes de coletar stats)
        if args.index:
            exclude_globs = [g.strip() for g in args.exclude.split(";") if g.strip()]
            sys.stderr.write(f"[get_stats] Indexando '{args.index}' (recursive={args.recursive}, semantic={args.enable_semantic}, watcher={args.auto_start_watcher})...\n")
            res_idx = _handle_index_path(
                path=args.index,
                recursive=bool(args.recursive),
                enable_semantic=bool(args.enable_semantic),
                auto_start_watcher=bool(args.auto_start_watcher),
                exclude_globs=exclude_globs
            )
            if not isinstance(res_idx, dict) or res_idx.get('status') != 'success':
                print("❌ Falha na indexação:")
                print(json.dumps(res_idx, indent=2, ensure_ascii=False))
                sys.exit(1)
            data_idx = res_idx.get('data', {}) if isinstance(res_idx, dict) else {}
            files = int(data_idx.get('files_indexed', 0)) if isinstance(data_idx, dict) else 0
            chunks = int(data_idx.get('chunks', 0)) if isinstance(data_idx, dict) else 0
            sys.stderr.write(f"[get_stats] ✅ Indexação concluída: {files} arquivos, {chunks} chunks\n")

        # Chamar handler de estatísticas com timeout opcional (não-blocking se handler implementar)
        # Se o servidor expor uma função que aceite timeout, preferi usá-la; caso contrário, chamamos direto.
        try:
            if hasattr(server, "_handle_get_stats"):
                res = server._handle_get_stats()
            else:
                res = {}
        except Exception as e:
            # Capturar erro específico da chamada e manter res vazio para impressão posterior
            res = {"status": "error", "error": str(e)}

        # Fallback: se acumuladores do servidor estiverem zerados, agregar a partir do CSV de métricas local
        try:
            if isinstance(res, dict) and isinstance(res.get('data'), dict):
                data_tmp = res.get('data')
                if int(data_tmp.get('tokens_sent_total', 0)) == 0:
                    metrics_path = os.environ.get('MCP_METRICS_FILE')
                    if not metrics_path:
                        metrics_path = str(_THIS_DIR / '.mcp_index' / 'metrics_context.csv')
                    # Logar caminho do CSV de métricas usado no fallback
                    try:
                        sys.stderr.write(f"[get_stats] metrics_context.csv: {metrics_path}\n")
                    except Exception:
                        pass
                    if metrics_path and os.path.exists(metrics_path):
                        import csv as _csv
                        s_sent = 0.0
                        s_saved = 0.0
                        with open(metrics_path, newline='', encoding='utf-8') as mf:
                            reader = _csv.DictReader(mf)
                            for row in reader:
                                try:
                                    tok = float(row.get('total_tokens', row.get('total_tokens_sent', 0)) or 0)
                                except Exception:
                                    tok = 0.0
                                s_sent += tok
                                try:
                                    saved_r = float(row.get('tokens_saved_total', 0) or 0)
                                except Exception:
                                    saved_r = 0.0
                                s_saved += saved_r
                        if s_sent > 0:
                            data_tmp['tokens_sent_total'] = s_sent
                        if s_saved > 0:
                            data_tmp['tokens_saved_total'] = s_saved
                        res['data'] = data_tmp
        except Exception:
            pass

        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
            sys.exit(0 if isinstance(res, dict) and res.get('status') == 'success' else 1)

        data = res.get("data", {})

        if hasattr(server, "logger"):
            import logging
            level_name = logging.getLevelName(server.logger.level)
            print(f"Nível de log atual: {level_name} ({server.logger.level})")

        # Removed local header print to avoid conflict with handler data

        print(f"Arquivos indexados: {data.get('total_files', 0)}")
        print(f"Chunks indexados: {data.get('total_chunks', 0)}")
        print(f"Tamanho do índice (MB): {data.get('index_size_mb', 0.0)}")
        print(f"Última atualização: {data.get('last_updated', '')}")
        print(f"Busca semântica habilitada: {data.get('semantic_enabled', False)}")
        print(f"Auto-indexação habilitada: {data.get('auto_indexing_enabled', False)}")
        print(f"Tokens enviados no total: {data.get('tokens_sent_total', 0)}")
        print(f"Tokens evitados no total: {data.get('tokens_saved_total', 0)}")
        print(f"Tokens evitados no cache: {data.get('cache_tokens_saved_total', 0)}")
        print(f"Tokens evitados na compressão: {data.get('compression_tokens_saved_total', 'n/a')}")

        # --- Cache / MemoryStore inspection (opcional) ---
        try:
            ms = None
            try:
                import mcp_system.memory_store as ms
            except Exception:
                try:
                    import memory_store as ms
                except Exception:
                    try:
                        from . import memory_store as ms
                    except Exception:
                        ms = None

            if ms is not None:
                get_all_cache_stats = getattr(ms, 'get_all_cache_stats', None)
                get_memory_store_stats = getattr(ms, 'get_memory_store_stats', None)
                MemoryStore = getattr(ms, 'MemoryStore', None)
            else:
                get_all_cache_stats = None
                get_memory_store_stats = None
                MemoryStore = None

            # Print cache stats if available
            if callable(get_all_cache_stats):
                try:
                    stats = get_all_cache_stats()
                    if isinstance(stats, dict):
                        print("--- Cache stats ---")
                        for ns, m in stats.items():
                            try:
                                hits = m.get('hits', 0)
                                misses = m.get('misses', 0)
                                ev = m.get('evictions', 0)
                            except Exception:
                                hits = misses = ev = 0
                            print(f"[{ns}] hits={hits} misses={misses} evictions={ev}")
                except Exception:
                    # best-effort: don't fail if cache introspection errors
                    pass

            # Print MemoryStore stats and LLM usage if available
            if MemoryStore and callable(get_memory_store_stats):
                try:
                    store = MemoryStore()
                    # Mostrar caminho do DB em uso para evitar confusão de diretórios/ambientes
                    try:
                        dbp = getattr(store, 'db_path', None)
                        if dbp:
                            print(f"[MemoryStore] DB: {dbp}")
                    except Exception:
                        pass
                    ms_stats = get_memory_store_stats(store)
                    print("--- MemoryStore stats ---")
                    print(ms_stats)
                except Exception as e:
                    print(f"[warning] Falha ao inspecionar MemoryStore: {e}", file=sys.stderr)
                    store = None

                # Best-effort LLM usage reporting
                try:
                    if store is not None and hasattr(store, 'get_llm_usage_agg'):
                        import time as _time
                        now = int(_time.time())
                        week_ago = now - 7 * 24 * 60 * 60

                        agg_all = store.get_llm_usage_agg()
                        agg_7d = store.get_llm_usage_agg(start_ts=week_ago, end_ts=now)

                        def _print_agg(title: str, agg: dict):
                            print(title)
                            if not agg:
                                print("  (no data)")
                                return
                            total_calls = sum(v.get('calls', 0) for v in agg.values())
                            total_tokens = sum(v.get('tokens', 0.0) for v in agg.values())
                            for model, stats in sorted(agg.items(), key=lambda x: x[1].get('tokens', 0), reverse=True):
                                calls = stats.get('calls', 0)
                                tokens = stats.get('tokens', 0.0)
                                pc_calls = stats.get('pc_calls', 0.0)
                                pc_tokens = stats.get('pc_tokens', 0.0)
                                print(f"{model:20s} calls={calls} ({pc_calls:.1f}%)  tokens={tokens:.1f} ({pc_tokens:.1f}%)")
                            print(f"TOTAL calls={total_calls}  tokens={total_tokens:.1f}")
                            print()

                        total_recorded_calls = sum(v.get('calls', 0) for v in (agg_all or {}).values())
                        if total_recorded_calls > 0:
                            print('--- LLM usage (all time) ---')
                            _print_agg('All time', agg_all)
                            print('--- LLM usage (last 7d) ---')
                            _print_agg('Last 7 days', agg_7d)
                        else:
                            # fallback: infer LLM usage from metrics_context.csv
                            try:
                                metrics_path = os.environ.get('MCP_METRICS_FILE')
                                if not metrics_path:
                                    metrics_path = str(Path(__file__).resolve().parent / '.mcp_index' / 'metrics_context.csv')
                                # Logar caminho do CSV de métricas usado no fallback
                                try:
                                    sys.stderr.write(f"[get_stats] metrics_context.csv (LLM usage fallback): {metrics_path}\n")
                                except Exception:
                                    pass
                                if metrics_path and os.path.exists(metrics_path):
                                    import csv as _csv
                                    from datetime import datetime as _dt
                                    agg_all_fb = {}
                                    agg_7d_fb = {}
                                    now_ts = int(_time.time())
                                    week_ago_ts = now_ts - 7 * 24 * 60 * 60
                                    with open(metrics_path, newline='', encoding='utf-8') as mf:
                                        reader = _csv.DictReader(mf)
                                        for row in reader:
                                            ts_str = row.get('ts')
                                            if not ts_str:
                                                continue
                                            try:
                                                ts = int(_dt.fromisoformat(ts_str).timestamp())
                                            except Exception:
                                                try:
                                                    ts = int(_dt.fromisoformat(ts_str.replace('Z', '+00:00')).timestamp())
                                                except Exception:
                                                    continue
                                            try:
                                                tok = float(row.get('total_tokens', row.get('total_tokens_sent', 0)) or 0)
                                            except Exception:
                                                tok = 0.0
                                            model_name = os.environ.get('MCP_DEFAULT_MODEL', 'unknown')
                                            s = agg_all_fb.setdefault(model_name, {'calls': 0, 'tokens': 0.0})
                                            s['calls'] += 1
                                            s['tokens'] += tok
                                            if week_ago_ts <= ts <= now_ts:
                                                s7 = agg_7d_fb.setdefault(model_name, {'calls': 0, 'tokens': 0.0})
                                                s7['calls'] += 1
                                                s7['tokens'] += tok

                                    def _compute_pc(dct):
                                        tc = sum(v['calls'] for v in dct.values())
                                        tt = sum(v['tokens'] for v in dct.values())
                                        out = {}
                                        for k, v in dct.items():
                                            out[k] = {
                                                'calls': v['calls'],
                                                'tokens': v['tokens'],
                                                'pc_calls': (v['calls']/tc*100.0) if tc>0 else 0.0,
                                                'pc_tokens': (v['tokens']/tt*100.0) if tt>0 else 0.0,
                                            }
                                        return out

                                    print('--- LLM usage (inferred from metrics_context.csv) ---')
                                    _print_agg('All time', _compute_pc(agg_all_fb))
                                    print('--- LLM usage (last 7d, inferred) ---')
                                    _print_agg('Last 7 Days', _compute_pc(agg_7d_fb))
                                else:
                                    print('--- LLM usage ---\n  (no recorded LLM usage found)')
                            except Exception:
                                print('--- LLM usage ---\n  (no recorded LLM usage found)')
                except Exception:
                    # best-effort: don't let LLM usage reporting break the script
                    pass

        except Exception:
            # Falhou ao tentar inspecionar caches; não interromper a execução
            pass

    except Exception as e:
        # Log mais detalhado quando --debug ativo não disponível neste escopo; simplesmente warn e continuar
        import traceback
        print(f"[warning] Falha ao ajustar nível de log ou coletar estatísticas: {e}", file=sys.stderr)
        # Print full traceback to stderr to help debugging recursion or other unexpected errors
        traceback.print_exc(file=sys.stderr)

    # Imprime resumo legível baseado no payload final
    rc = _print_stats_payload(res)

    sys.exit(rc)


if __name__ == "__main__":
    main()
