#!/usr/bin/env python3
"""
Coleta e imprime estatísticas do indexador/servidor MCP em formato amigável.

- Chama diretamente _handle_get_stats do servidor
- Útil para integração em CI ou inspeção manual

Uso:
  python mcp_system/scripts/get_stats.py --pretty
  python -m mcp_system.scripts.get_stats --pretty
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
    args = parser.parse_args()

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

        res = server._handle_get_stats()
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
        print(f"Tokens evitados na compressão: {data.get('compression_tokens_saved_total', 0)}")

    except Exception as e:
        print(f"[warning] Falha ao ajustar nível de log ou coletar estatísticas: {e}", file=sys.stderr)

    # Optional index before stats
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

    rc = _print_stats_payload(res)

    sys.exit(rc)


if __name__ == "__main__":
    main()
