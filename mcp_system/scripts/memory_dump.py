#!/usr/bin/env python3
"""
Dump simples dos últimos resumos de sessão (session_summaries) da memória do MCP.

- Não requer sqlite3 CLI; usa a API do MemoryStore
- Saída em JSON (default) ou formato tabular
- Filtros opcionais por projeto, escopo e texto contido

Uso básico:
  python -m mcp_system.scripts.memory_dump --limit 20 --json
  python -m mcp_system.scripts.memory_dump --limit 20 --table
"""
from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Configura caminho de import para mcp_system quando executado de locais variados
_THIS = Path(__file__).resolve()
_PKG_DIR = _THIS.parent.parent  # mcp_system/
_ROOT_DIR = _PKG_DIR.parent     # raiz do projeto
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

try:
    from mcp_system.memory_store import MemoryStore
except Exception as e:
    sys.stderr.write(f"[memory_dump] ❌ Falha ao importar MemoryStore: {e}\n")
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lista registros recentes do MemoryStore (session_summaries)")
    p.add_argument("--limit", type=int, default=20, help="Quantidade de registros (default: 20)")
    p.add_argument("--json", dest="as_json", action="store_true", help="Saída em JSON (default)")
    p.add_argument("--table", dest="as_table", action="store_true", help="Saída em tabela legível")
    p.add_argument("--project", type=str, default="", help="Filtra por nome do projeto")
    p.add_argument("--scope", type=str, default="", help="Filtra por escopo (ex.: index)")
    p.add_argument("--contains", type=str, default="", help="Filtra registros que contenham o texto (title/details)")
    p.add_argument("--memory-dir", type=str, default="", help="Diretório da memória (opcional); padrão: mcp_system/.mcp_memory")
    p.add_argument("--pretty", action="store_true", help="Ao imprimir JSON, truncar campos longos e mostrar somente campos essenciais")
    p.add_argument("--limit-fields", type=int, default=1000, help="Ao usar --pretty, limitar tamanho de campos (chars)")
    p.add_argument("--reverse", action="store_true", help="Exibe em ordem reversa (mais antigos primeiro)")
    return p.parse_args()


def filter_rows(rows: List[Dict[str, Any]], project: str, scope: str, contains: str) -> List[Dict[str, Any]]:
    def ok(r: Dict[str, Any]) -> bool:
        if project and (r.get("project") or "") != project:
            return False
        if scope and (r.get("scope") or "") != scope:
            return False
        if contains:
            hay = ((r.get("title") or "") + "\n" + (r.get("details") or "")).lower()
            if contains.lower() not in hay:
                return False
        return True
    return [r for r in rows if ok(r)]


def to_table(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return "(sem registros)"
    cols = ["ts", "project", "scope", "title"]
    widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in rows)) for c in cols}
    def fmt_row(r: Dict[str, Any]) -> str:
        return " | ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols)
    header = " | ".join(c.ljust(widths[c]) for c in cols)
    sep = "-+-".join("-" * widths[c] for c in cols)
    body = "\n".join(fmt_row(r) for r in rows)
    return f"{header}\n{sep}\n{body}"


def main() -> None:
    args = parse_args()

    # Inicializa MemoryStore apontando para o diretório do pacote (auto-contido)
    try:
        # Se --memory-dir for informado, validar e ajustar antes de inicializar
        if args.memory_dir:
            import os
            candidate = os.path.expanduser(os.path.expandvars(args.memory_dir))
            if not os.path.exists(candidate):
                sys.stderr.write(f"[memory_dump] ❌ Diretório de memória informado não existe: {candidate}\n")
                sys.exit(2)
            os.environ["MEMORY_DIR"] = candidate
        # project_root é ignorado internamente; o MemoryStore resolve relativo a mcp_system
        ms = MemoryStore(project_root=_ROOT_DIR)
    except Exception as e:
        sys.stderr.write(f"[memory_dump] ❌ Falha ao inicializar MemoryStore: {e}\n")
        sys.exit(2)

    try:
        rows = list(ms.recent_summaries(limit=max(1, int(args.limit))))
        rows = filter_rows(rows, args.project.strip(), args.scope.strip(), args.contains.strip())
    except Exception as e:
        sys.stderr.write(f"[memory_dump] ❌ Erro ao ler registros: {e}\n")
        sys.exit(3)

    if args.reverse:
        rows = list(reversed(rows))

    if args.as_table:
        print(to_table(rows))
        return

    # default JSON
    if args.pretty:
        # Campos a manter para saída reduzida
        keep_fields = {"ts", "project", "scope", "title", "details"}
        limit = max(1, args.limit_fields)

        def truncate_field(value: str) -> str:
            if len(value) > limit:
                return value[:limit] + "…"
            return value

        truncated_rows = []
        for r in rows:
            nr = {}
            for k in keep_fields:
                v = r.get(k, "")
                if isinstance(v, str):
                    nr[k] = truncate_field(v)
                else:
                    nr[k] = v
            truncated_rows.append(nr)
        print(json.dumps(truncated_rows, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
