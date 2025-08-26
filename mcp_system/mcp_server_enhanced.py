# mcp_server_enhanced.py
"""
Servidor MCP melhorado com busca semântica e auto-indexação
Usando FastMCP para API simplificada com decorators
"""

import os
import sys
from typing import Any, Dict, List
import pathlib
import threading
import csv
import datetime as dt

# Obter o diretório do script atual
CURRENT_DIR = pathlib.Path(__file__).parent.absolute()

try:
    from mcp.server.fastmcp import FastMCP
    HAS_MCP = True
    HAS_FASTMCP = True
except ImportError:
    try:
        # Fallback para versões mais antigas
        from mcp.server import Server
        from mcp import types
        HAS_MCP = True
        HAS_FASTMCP = False
    except ImportError:
        sys.stderr.write("[mcp_server_enhanced] ERROR: MCP SDK não encontrado. Instale `mcp`.\n")
        raise

# Importa funcionalidades melhoradas
try:
    from .code_indexer_enhanced import (
        EnhancedCodeIndexer,
        enhanced_search_code,
        enhanced_build_context_pack,
        enhanced_index_repo_paths,
        BaseCodeIndexer,
        search_code,
        build_context_pack,
        index_repo_paths
    )
    HAS_ENHANCED = True
    sys.stderr.write("[mcp_server_enhanced] ✅ Funcionalidades melhoradas carregadas\n")
except ImportError as e:
    sys.stderr.write(f"[mcp_server_enhanced] ⚠️ Funcionalidades melhoradas não disponíveis: {e}\n")
    sys.stderr.write("[mcp_server_enhanced] 🔄 Usando versão base integrada\n")

    # Fallback para versão base integrada
    try:
        from .code_indexer_enhanced import (
            BaseCodeIndexer,
            search_code,
            build_context_pack,
            index_repo_paths
        )
        HAS_ENHANCED = False
    except ImportError as e2:
        sys.stderr.write(f"[mcp_server_enhanced] ❌ Erro crítico: {e2}\n")
        raise

HAS_ENHANCED_FEATURES = HAS_ENHANCED

# Config / instâncias - agora usando caminhos relativos à pasta mcp_system
INDEX_DIR = os.environ.get("INDEX_DIR", str(CURRENT_DIR / ".mcp_index"))
INDEX_ROOT = os.environ.get("INDEX_ROOT", str(CURRENT_DIR.parent))

if HAS_ENHANCED_FEATURES:
    _indexer = EnhancedCodeIndexer(
        index_dir=INDEX_DIR,
        repo_root=INDEX_ROOT
    )
else:
    _indexer = BaseCodeIndexer(index_dir=INDEX_DIR)

# ===== CONFIG DE AUTO-INDEXAÇÃO NO START =====

def _truthy(env_val: str, default: bool = False) -> bool:
    if env_val is None:
        return default
    return str(env_val).strip().lower() in {"1", "true", "yes", "on"}

AUTO_INDEX_ON_START = _truthy(os.environ.get("AUTO_INDEX_ON_START", "1"), True)
AUTO_INDEX_PATHS = [p.strip() for p in os.environ.get("AUTO_INDEX_PATHS", ".").split(os.pathsep) if p.strip()]
AUTO_INDEX_RECURSIVE = _truthy(os.environ.get("AUTO_INDEX_RECURSIVE", "1"), True)
AUTO_ENABLE_SEMANTIC = _truthy(os.environ.get("AUTO_ENABLE_SEMANTIC", "1"), True)
AUTO_START_WATCHER = _truthy(os.environ.get("AUTO_START_WATCHER", "1"), True)


def _initial_index():
    if not AUTO_INDEX_ON_START:
        return
    try:
        sys.stderr.write("[mcp_server_enhanced] 🚀 Iniciando indexação automática inicial...\n")
        abs_paths: List[str] = []
        for p in AUTO_INDEX_PATHS:
            abs_paths.append(p if os.path.isabs(p) else os.path.join(INDEX_ROOT, p))

        # Executa indexação inicial e captura resultado
        if HAS_ENHANCED_FEATURES:
            result = enhanced_index_repo_paths(
                _indexer,
                abs_paths,
                recursive=AUTO_INDEX_RECURSIVE,
                enable_semantic=AUTO_ENABLE_SEMANTIC,
                exclude_globs=[]
            )
            if AUTO_START_WATCHER and hasattr(_indexer, 'start_auto_indexing'):
                _indexer.start_auto_indexing()
        else:
            result = index_repo_paths(
                _indexer,
                abs_paths,
                recursive=AUTO_INDEX_RECURSIVE
            )
        sys.stderr.write("[mcp_server_enhanced] ✅ Indexação inicial concluída\n")

        # Registrar métricas da indexação inicial em metrics_index.csv
        try:
            index_dir = getattr(_indexer, 'index_dir', None)
            if not index_dir and hasattr(_indexer, 'base_indexer'):
                index_dir = getattr(_indexer.base_indexer, 'index_dir', None)
            index_dir_str = str(index_dir) if index_dir else str(CURRENT_DIR / ".mcp_index")

            metrics_dir = pathlib.Path(index_dir_str)
            metrics_dir.mkdir(parents=True, exist_ok=True)
            metrics_path = metrics_dir / "metrics_index.csv"

            row = {
                "ts": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                "op": "initial_index",
                "path": os.pathsep.join(AUTO_INDEX_PATHS),
                "index_dir": index_dir_str,
                "files_indexed": int(result.get("files_indexed", 0)) if isinstance(result, dict) else 0,
                "chunks": int(result.get("chunks", 0)) if isinstance(result, dict) else 0,
                "recursive": bool(AUTO_INDEX_RECURSIVE),
                "include_globs": "",
                "exclude_globs": "",
                "elapsed_s": float(result.get("elapsed_s", 0.0)) if isinstance(result, dict) else 0.0,
            }

            file_exists = metrics_path.exists()
            with open(metrics_path, "a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(row.keys()))
                if not file_exists:
                    w.writeheader()
                w.writerow(row)
        except Exception as e:
            sys.stderr.write(f"[mcp_server_enhanced] ⚠️ Falha ao logar métricas de indexação inicial: {e}\n")
    except Exception as e:
        sys.stderr.write(f"[mcp_server_enhanced] ⚠️ Falha na indexação inicial: {e}\n")

# ===== HANDLERS IMPLEMENTATION =====

def _handle_index_path(path, recursive, enable_semantic, auto_start_watcher, exclude_globs):
    """Handler para indexar um caminho"""
    sys.stderr.write(f"🔍 [index_path] {path} (recursive={recursive}, semantic={enable_semantic}, watcher={auto_start_watcher})\n")

    try:
        # Converte path relativo para absoluto
        if not os.path.isabs(path):
            path = os.path.join(INDEX_ROOT, path)

        if HAS_ENHANCED_FEATURES:
            result = enhanced_index_repo_paths(
                _indexer,
                [path],
                recursive=recursive,
                enable_semantic=enable_semantic,
                exclude_globs=exclude_globs or []
            )

            if auto_start_watcher and hasattr(_indexer, 'start_auto_indexing'):
                _indexer.start_auto_indexing()
                result['auto_indexing'] = 'started'
        else:
            result = index_repo_paths(
                _indexer,
                [path],
                recursive=recursive
            )

        return result

    except Exception as e:
        sys.stderr.write(f"❌ [index_path] Erro: {str(e)}\n")
        return {'status': 'error', 'error': str(e)}

def _handle_search_code(query, limit, semantic_weight, use_mmr):
    """Handler para buscar código"""
    sys.stderr.write(f"🔍 [search_code] '{query}' (limit={limit}, weight={semantic_weight}, mmr={use_mmr})\n")
    
    try:
        if HAS_ENHANCED_FEATURES:
            results = enhanced_search_code(
                _indexer, 
                query, 
                limit=limit,
                semantic_weight=semantic_weight,
                use_mmr=use_mmr
            )
        else:
            results = search_code(_indexer, query, limit=limit)
        
        return {
            'status': 'success',
            'results': results,
            'count': len(results)
        }
        
    except Exception as e:
        sys.stderr.write(f"❌ [search_code] Erro: {str(e)}\n")
        return {'status': 'error', 'error': str(e)}

def _handle_context_pack(query, token_budget, max_chunks, strategy):
    """Handler para criar pacote de contexto"""
    sys.stderr.write(f"📦 [context_pack] '{query}' (budget={token_budget}, chunks={max_chunks}, strategy={strategy})\n")
    
    try:
        if HAS_ENHANCED_FEATURES:
            context_data = enhanced_build_context_pack(
                _indexer, 
                query, 
                token_budget=token_budget,
                max_chunks=max_chunks,
                strategy=strategy
            )
        else:
            context_data = build_context_pack(
                _indexer, 
                query, 
                token_budget=token_budget
            )
        
        return {
            'status': 'success',
            'context_data': context_data,
            'total_tokens': sum(chunk.get('estimated_tokens', 0) for chunk in context_data.get('chunks', []))
        }
        
    except Exception as e:
        sys.stderr.write(f"❌ [context_pack] Erro: {str(e)}\n")
        return {'status': 'error', 'error': str(e)}

def _handle_auto_index(action, paths, recursive):
    """Handler para controle de auto-indexação"""
    sys.stderr.write(f"👁️  [auto_index] {action} (paths={paths}, recursive={recursive})\n")
    
    try:
        if not HAS_ENHANCED_FEATURES or not hasattr(_indexer, 'start_auto_indexing'):
            return {
                'status': 'not_available',
                'message': 'Auto-indexação não disponível. Instale watchdog e use EnhancedCodeIndexer.'
            }
        
        if action == 'start':
            _indexer.start_auto_indexing()
            return {'status': 'started', 'paths': paths}
        elif action == 'stop':
            _indexer.stop_auto_indexing()
            return {'status': 'stopped'}
        elif action == 'status':
            is_running = _indexer.is_auto_indexing_running()
            return {'status': 'running' if is_running else 'stopped', 'is_running': is_running}
        else:
            return {'status': 'error', 'error': f'Ação inválida: {action}'}
            
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def _handle_get_stats():
    """Handler para obter estatísticas"""
    sys.stderr.write("📊 [get_stats] Coletando estatísticas...\n")
    
    try:
        stats = _indexer.get_stats()
        
        # Adiciona informações sobre capacidades
        stats['capabilities'] = {
            'semantic_search': HAS_ENHANCED_FEATURES,
            'auto_indexing': HAS_ENHANCED_FEATURES,
            'fastmcp': HAS_FASTMCP
        }
        
        return {
            'status': 'success',
            'stats': stats
        }
        
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def _handle_cache_management(action, cache_type):
    """Handler para gestão de cache"""
    sys.stderr.write(f"🗄️  [cache_management] {action} ({cache_type})\n")
    
    try:
        if action == 'clear':
            if cache_type == 'embeddings' and hasattr(_indexer, 'semantic_engine'):
                _indexer.semantic_engine.clear_cache()
                return {'status': 'success', 'message': 'Cache de embeddings limpo'}
            elif cache_type == 'all':
                if hasattr(_indexer, 'semantic_engine'):
                    _indexer.semantic_engine.clear_cache()
                # Aqui você pode adicionar limpeza de outros caches se existirem
                return {'status': 'success', 'message': 'Todos os caches limpos'}
        elif action == 'status':
            result = {'status': 'success'}
            if hasattr(_indexer, 'semantic_engine'):
                result['embeddings_cache'] = _indexer.semantic_engine.get_cache_stats()
            return result
            
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

# ===== SERVIDOR MCP COM FASTMCP =====

if HAS_FASTMCP:
    # Cria servidor FastMCP
    mcp = FastMCP(name="code-indexer-enhanced")

    # Dispara indexação inicial em background para não bloquear o initialize
    try:
        threading.Thread(target=_initial_index, daemon=True).start()
    except Exception as e:
        sys.stderr.write(f"[mcp_server_enhanced] ⚠️ Não foi possível iniciar thread de indexação inicial: {e}\n")

    # ===== TOOLS BÁSICAS =====

    @mcp.tool()
    def index_path(path: str = ".",
                   recursive: bool = True,
                   enable_semantic: bool = True,
                   auto_start_watcher: bool = False,
                   exclude_globs: list = None) -> dict:
        """Indexa arquivos de código no caminho especificado"""
        return _handle_index_path(path, recursive, enable_semantic, auto_start_watcher, exclude_globs)

    @mcp.tool()
    def search_code(query: str,
                    limit: int = 10,
                    semantic_weight: float = 0.3,
                    use_mmr: bool = True) -> dict:
        """Busca código usando busca híbrida (BM25 + semântica)"""
        return _handle_search_code(query, limit, semantic_weight, use_mmr)

    @mcp.tool()
    def context_pack(query: str,
                     token_budget: int = 2000,  # Reduzido de 8000 para 2000
                     max_chunks: int = 5,       # Reduzido de 20 para 5
                     strategy: str = "mmr") -> dict:
        """Cria pacote de contexto otimizado para LLMs"""
        # Validações de entrada
        token_budget = max(500, min(token_budget, 5000))  # Entre 500 e 5000
        max_chunks = max(1, min(max_chunks, 10))          # Entre 1 e 10
        return _handle_context_pack(query, token_budget, max_chunks, strategy)

    @mcp.tool()
    def auto_index(action: str = "status", paths: list = None, recursive: bool = True) -> dict:
        """Controla sistema de auto-indexação (start/stop/status)"""
        return _handle_auto_index(action, paths, recursive)

    @mcp.tool()
    def get_stats() -> dict:
        """Obtém estatísticas do indexador"""
        return _handle_get_stats()

    @mcp.tool()
    def cache_management(action: str = "status", cache_type: str = "all") -> dict:
        """Gerencia caches (clear/status)"""
        return _handle_cache_management(action, cache_type)

    # Removido helper duplicado e chamada imediata; já iniciamos a thread acima
    # def _start_initial_indexing_thread():
    #     thread = threading.Thread(target=_initial_index, daemon=True)
    #     thread.start()
    # _start_initial_indexing_thread()

else:
    # Fallback para MCP tradicional
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent

    server = Server(name="code-indexer-enhanced")

    # Dispara indexação inicial em background
    try:
        threading.Thread(target=_initial_index, daemon=True).start()
    except Exception as e:
        sys.stderr.write(f"[mcp_server_enhanced] ⚠️ Não foi possível iniciar thread de indexação inicial: {e}\n")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="index_path",
                description="Indexa arquivos de código no caminho especificado",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "default": "."},
                        "recursive": {"type": "boolean", "default": True},
                        "enable_semantic": {"type": "boolean", "default": True},
                        "auto_start_watcher": {"type": "boolean", "default": False},
                        "exclude_globs": {"type": "array", "items": {"type": "string"}, "default": []}
                    }
                }
            ),
            Tool(
                name="search_code",
                description="Busca código usando busca híbrida (BM25 + semântica)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "default": 10},
                        "semantic_weight": {"type": "number", "default": 0.3},
                        "use_mmr": {"type": "boolean", "default": True}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="context_pack",
                description="Cria pacote de contexto otimizado para LLMs",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "token_budget": {"type": "integer", "default": 2000, "minimum": 500, "maximum": 5000},
                        "max_chunks": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10},
                        "strategy": {"type": "string", "default": "mmr"}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="auto_index",
                description="Controla sistema de auto-indexação (start/stop/status)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "default": "status"},
                        "paths": {"type": "array", "items": {"type": "string"}, "default": None},
                        "recursive": {"type": "boolean", "default": True}
                    }
                }
            ),
            Tool(
                name="get_stats",
                description="Obtém estatísticas do indexador",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="cache_management",
                description="Gerencia caches (clear/status)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "default": "status"},
                        "cache_type": {"type": "string", "default": "all"}
                    }
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any] = None):
        arguments = arguments or {}
        try:
            if name == "index_path":
                return _handle_index_path(
                    arguments.get("path", "."),
                    arguments.get("recursive", True),
                    arguments.get("enable_semantic", True),
                    arguments.get("auto_start_watcher", False),
                    arguments.get("exclude_globs", None)
                )
            elif name == "search_code":
                return _handle_search_code(
                    arguments.get("query"),
                    arguments.get("limit", 10),
                    arguments.get("semantic_weight", 0.3),
                    arguments.get("use_mmr", True)
                )
            elif name == "context_pack":
                return _handle_context_pack(
                    arguments.get("query"),
                    arguments.get("token_budget", 2000),
                    arguments.get("max_chunks", 5),
                    arguments.get("strategy", "mmr")
                )
            elif name == "auto_index":
                return _handle_auto_index(
                    arguments.get("action", "status"),
                    arguments.get("paths", None),
                    arguments.get("recursive", True)
                )
            elif name == "get_stats":
                return _handle_get_stats()
            elif name == "cache_management":
                return _handle_cache_management(
                    arguments.get("action", "status"),
                    arguments.get("cache_type", "all")
                )
            else:
                return {"status": "error", "error": f"Ferramenta desconhecida: {name}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # Iniciar servidor
    async def main():
        # Removido: já iniciamos a thread antes
        # threading.Thread(target=_initial_index, daemon=True).start()
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server_name="code-indexer-enhanced")

    if __name__ == "__main__":
        import asyncio
        asyncio.run(main())

if HAS_FASTMCP and __name__ == "__main__":
    # Executa o servidor FastMCP quando disponível
    mcp.run()