# mcp_server_patched.py

# Compatível com SDK MCP "antigo" que usa métodos-gancho (list_tools / call_tool).
# Não imprime no stdout. Logs apenas no stderr se necessário.

import os
import sys
import asyncio
from typing import Any, Dict, List

try:
    from mcp.server import Server
    from mcp import types  # para pegar types.Tool se necessário
    from mcp.types import Tool  # pydantic model que exige inputSchema (camelCase)
except Exception:
    sys.stderr.write("[mcp_server] ERROR: MCP SDK não encontrado. Instale `mcp`.\n")
    raise

# ---- Suas funções do indexador ----
from code_indexer_patched import (
    CodeIndexer,
    index_repo_paths,
    search_code,
    build_context_pack,
    get_chunk_by_id,  # pode ser útil depois se formos expor resources
)

# ------------------------------------------------------------------------------------
# Config / instâncias
# ------------------------------------------------------------------------------------
INDEX_DIR = os.environ.get("INDEX_DIR", ".mcp_index")
INDEX_ROOT = os.environ.get("INDEX_ROOT", os.getcwd())
_indexer = CodeIndexer(index_dir=INDEX_DIR, repo_root=INDEX_ROOT)

# ------------------------------------------------------------------------------------
# Schemas das tools (camelCase: inputSchema) + handlers finos
# ------------------------------------------------------------------------------------
INDEX_PATH_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "path": {"type": "string"},
        "recursive": {"type": "boolean", "default": True},
        "include_globs": {"type": "array", "items": {"type": "string"}, "default": []},
        "exclude_globs": {
            "type": "array",
            "items": {"type": "string"},
            "default": ["**/.git/**", "**/node_modules/**"],
        },
    },
    "required": ["path"],
    "additionalProperties": False,
}

SEARCH_CODE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "top_k": {"type": "integer", "default": 30},
        "filters": {"type": "object"},
    },
    "required": ["query"],
    "additionalProperties": False,
}

CONTEXT_PACK_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "budget_tokens": {"type": "integer", "default": 3000},
        "max_chunks": {"type": "integer", "default": 10},
        "strategy": {"type": "string", "enum": ["mmr", "topk"], "default": "mmr"},
    },
    "required": ["query"],
    "additionalProperties": False,
}

# Definições Pydantic de Tool (inputSchema em camelCase!)
TOOL_INDEX_PATH = Tool(
    name="index_path",
    description="Indexa um arquivo ou diretório. Usa heurísticas por linguagem e persistência local.",
    inputSchema=INDEX_PATH_SCHEMA,
)

TOOL_SEARCH_CODE = Tool(
    name="search_code",
    description="Busca lexical (BM25-like) com boost de recência e diversificação MMR.",
    inputSchema=SEARCH_CODE_SCHEMA,
)

TOOL_CONTEXT_PACK = Tool(
    name="context_pack",
    description="Retorna pacote de contexto orçamentado em tokens. Inclui headers path:linhas e snippets comprimidos.",
    inputSchema=CONTEXT_PACK_SCHEMA,
)

# Handlers que chamam o indexador
def _handle_index_path(params: Dict[str, Any]) -> Dict[str, Any]:
    path = params["path"]
    recursive = bool(params.get("recursive", True))
    globs = params.get("include_globs", [])
    exclude = params.get("exclude_globs", [])
    res = index_repo_paths(
        _indexer,
        [path],
        recursive=recursive,
        include_globs=globs,
        exclude_globs=exclude,
    )
    return {
        "status": "ok",
        "indexed_files": res.get("files_indexed", 0),
        "chunks": res.get("chunks", 0),
    }

def _handle_search_code(params: Dict[str, Any]) -> Any:
    return search_code(
        _indexer,
        query=params["query"],
        top_k=int(params.get("top_k", 30)),
        filters=params.get("filters"),
    )

def _handle_context_pack(params: Dict[str, Any]) -> Any:
    return build_context_pack(
        _indexer,
        query=params["query"],
        budget_tokens=int(params.get("budget_tokens", 3000)),
        max_chunks=int(params.get("max_chunks", 10)),
        strategy=str(params.get("strategy", "mmr")),
    )

# ------------------------------------------------------------------------------------
# Servidor MCP compatível com API antiga (override de list_tools/call_tool)
# ------------------------------------------------------------------------------------
class CompatServer(Server):
    # Lista de tools que o cliente verá em `list_tools`
    def list_tools(self, *args, **kwargs) -> List[Tool]:
        return [TOOL_INDEX_PATH, TOOL_SEARCH_CODE, TOOL_CONTEXT_PACK]

    # Despacho da chamada de tool
    async def call_tool(self, name: str, arguments: Dict[str, Any] | None = None, *args, **kwargs):
        params = arguments or {}
        if name == "index_path":
            return _handle_index_path(params)
        if name == "search_code":
            return _handle_search_code(params)
        if name == "context_pack":
            return _handle_context_pack(params)
        raise ValueError(f"Unknown tool: {name}")

    # Se quiser expor resources no futuro, você pode sobrescrever:
    # def list_resource_templates(self, *args, **kwargs): ...
    # def read_resource(self, uri: str, *args, **kwargs): ...
    # Para simplificar, vamos deixar sem resources por enquanto.

# ------------------------------------------------------------------------------------
# Entrada
# ------------------------------------------------------------------------------------
if __name__ == "__main__":
    srv = CompatServer("code-indexer")
    asyncio.run(srv.run_stdio())
