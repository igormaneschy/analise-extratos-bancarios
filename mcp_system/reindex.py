#!/usr/bin/env python3
"""
Reindexador simples para o MCP Code Indexer.

- Remove (opcional) o diretório de índice.
- Reindexa arquivos conforme include/exclude globs.
- Mede tempo e grava linha no CSV de métricas (MCP_METRICS_FILE ou .mcp_index/metrics.csv).
- (Opcional) Calcula baseline aproximada de tokens do repositório.

Exemplos:
  python reindex.py --clean
  python reindex.py --path src --include "**/*.py" --exclude "**/tests/**"
  python reindex.py --baseline-estimate
  MCP_METRICS_FILE=".mcp_index/metrics.csv" python reindex.py --clean

Requer:
  - code_indexer_enhanced.py com CodeIndexer e index_repo_paths
"""

import os
import sys
import csv
import json
import shutil
import time
import argparse
import datetime as dt
from pathlib import Path
from typing import List, Dict, Any
import pathlib

# Obter o diretório do script atual
CURRENT_DIR = pathlib.Path(__file__).parent.absolute()

# ---- Config métricas (mesmo padrão do context_pack) - agora usando caminho relativo à pasta mcp_system
METRICS_PATH = os.environ.get("MCP_METRICS_FILE", str(CURRENT_DIR / ".mcp_index/metrics.csv"))

def _log_metrics(row: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(METRICS_PATH), exist_ok=True)
    file_exists = os.path.exists(METRICS_PATH)
    with open(METRICS_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            w.writeheader()
        w.writerow(row)

def _est_tokens_from_len(n_chars: int) -> int:
    # heurística compatível com o indexador (~4 chars por token)
    return max(1, n_chars // 4)

def parse_args():
    p = argparse.ArgumentParser(description="Reindexa o projeto para o MCP Code Indexer.")
    p.add_argument("--path", default=".", help="Pasta ou arquivo inicial (default: .)")
    p.add_argument("--index-dir", default=str(CURRENT_DIR / ".mcp_index"), help="Diretório de índice (default: .mcp_index)")
    p.add_argument("--clean", action="store_true", help="Remove o índice antes de reindexar")
    p.add_argument("--recursive", action="store_true", default=True, help="Busca recursiva (default: True)")
    p.add_argument("--no-recursive", dest="recursive", action="store_false", help="Desabilita busca recursiva")
    p.add_argument("--include", action="append", default=None,
                   help='Glob de inclusão (pode repetir). Ex: --include "**/*.py"')
    p.add_argument("--exclude", action="append", default=None,
                   help='Glob de exclusão (pode repetir). Ex: --exclude "**/tests/**"')
    p.add_argument("--baseline-estimate", action="store_true",
                   help="Após indexar, calcula baseline aproximada de tokens do repo")
    p.add_argument("--topn-baseline", type=int, default=0,
                   help="Se >0, considera apenas os N maiores chunks na baseline (0 = todos)")
    p.add_argument("--quiet", action="store_true", help="Menos saída no stdout")
    return p.parse_args()

def main():
    args = parse_args()
    base_dir = Path.cwd()
    index_dir = Path(args.index_dir)  # Agora usa o caminho absoluto

    # Importa o indexador do seu projeto
    try:
        from code_indexer_enhanced import CodeIndexer, index_repo_paths  # type: ignore
    except Exception as e:
        print("[erro] Não foi possível importar CodeIndexer/index_repo_paths de code_indexer_enhanced.py", file=sys.stderr)
        raise

    if args.clean and index_dir.exists():
        if not args.quiet:
            print(f"🔄 Limpando índice anterior em: {index_dir}")
        shutil.rmtree(index_dir)

    index_dir.mkdir(parents=True, exist_ok=True)

    # Instancia o indexador com o mesmo diretório de índice
    try:
        indexer = CodeIndexer(index_dir=str(index_dir), repo_root=str(base_dir))
    except TypeError:
        # compat: se sua assinatura for diferente
        indexer = CodeIndexer(index_dir=str(index_dir))

    include_globs = args.include
    exclude_globs = args.exclude

    t0 = time.perf_counter()
    res = index_repo_paths(
        indexer,
        paths=[args.path],
        recursive=bool(args.recursive),
        include_globs=include_globs,
        exclude_globs=exclude_globs,
    )
    elapsed = round(time.perf_counter() - t0, 3)

    files_indexed = int(res.get("files_indexed", 0))
    chunks = int(res.get("chunks", 0))

    baseline_tokens = None
    if args.baseline_estimate:
        # Lê o índice persistido e soma tokens estimados por chunk
        chunks_file = index_dir / "chunks.jsonl"
        total_chars = 0
        n_chunks = 0
        if chunks_file.exists():
            with chunks_file.open("r", encoding="utf-8") as f:
                # se --topn-baseline > 0, carregamos tudo para ordenar; senão, stream
                if args.topn_baseline and args.topn_baseline > 0:
                    all_chunks: List[Dict[str, Any]] = [json.loads(line) for line in f if line.strip()]
                    all_chunks.sort(key=lambda c: len(c.get("content", "")), reverse=True)
                    all_chunks = all_chunks[:args.topn_baseline]
                    for c in all_chunks:
                        total_chars += len(c.get("content", ""))
                        n_chunks += 1
                else:
                    for line in f:
                        if not line.strip():
                            continue
                        c = json.loads(line)
                        total_chars += len(c.get("content", ""))
                        n_chunks += 1
        baseline_tokens = _est_tokens_from_len(total_chars)
        if not args.quiet:
            print(f"📊 Baseline (aprox.) de tokens do repo: {baseline_tokens} (chunks: {n_chunks})")

    if not args.quiet:
        print(f"✅ Reindex concluída: files={files_indexed}, chunks={chunks}, tempo={elapsed}s, index_dir={index_dir}")

    # Loga linha no CSV de métricas
    row = {
        "ts": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "op": "reindex",
        "path": str(args.path),
        "index_dir": str(index_dir),
        "files_indexed": files_indexed,
        "chunks": chunks,
        "recursive": bool(args.recursive),
        "include_globs": ";".join(include_globs) if include_globs else "",
        "exclude_globs": ";".join(exclude_globs) if exclude_globs else "",
        "elapsed_s": elapsed,
    }
    if baseline_tokens is not None:
        row["baseline_tokens_est"] = baseline_tokens
        row["topn_baseline"] = int(args.topn_baseline or 0)

    try:
        _log_metrics(row)
    except Exception:
        # não interrompe em caso de falha de log
        pass

    return 0

if __name__ == "__main__":
    sys.exit(main())