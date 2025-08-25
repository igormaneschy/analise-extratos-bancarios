# mcp_server_enhanced.py
"""
Servidor MCP melhorado com busca semântica e auto-indexação
Usando FastMCP para API simplificada com decorators
"""

import os
import sys
from typing import Any, Dict, List

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
    from code_indexer_enhanced import (
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
        from code_indexer_enhanced import (
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

# Config / instâncias
INDEX_DIR = os.environ.get("INDEX_DIR", ".mcp_index")
INDEX_ROOT = os.environ.get("INDEX_ROOT", os.getcwd())

if HAS_ENHANCED_FEATURES:
    _indexer = EnhancedCodeIndexer(
        index_dir=INDEX_DIR,
        repo_root=INDEX_ROOT
    )
else:
    _indexer = BaseCodeIndexer(index_dir=INDEX_DIR)

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
                _indexer.start_auto_indexing(paths=[path], recursive=recursive)
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
            _indexer.start_auto_indexing(paths=paths or [INDEX_ROOT], recursive=recursive)
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
                     token_budget: int = 8000, 
                     max_chunks: int = 20,
                     strategy: str = "mmr") -> dict:
        """Cria pacote de contexto otimizado para LLMs"""
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

else:
    # Fallback para MCP tradicional
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    
    server = Server(name="code-indexer-enhanced")

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
                        "exclude_globs": {"type": "array", "items": {"type": "string"}}
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
                        "token_budget": {"type": "integer", "default": 8000},
                        "max_chunks": {"type": "integer", "default": 20},
                        "strategy": {"type": "string", "default": "mmr"}
                    },
                    "required": ["query"]
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
                    },
                }
            ),
            Tool(
                name="auto_index",
                description="Controla sistema de auto-indexação (start/stop/status)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "default": "status"},
                        "paths": {"type": "array", "items": {"type": "string"}},
                        "recursive": {"type": "boolean", "default": True}
                    }
                }
            ),
            Tool(
                name="get_stats",
                description="Obtém estatísticas do indexador",
                inputSchema={"type": "object", "properties": {}}
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "index_path":
            result = _handle_index_path(
                arguments.get("path", "."),
                arguments.get("recursive", True),
                arguments.get("enable_semantic", True),
                arguments.get("auto_start_watcher", False),
                arguments.get("exclude_globs")
            )
        elif name == "search_code":
            result = _handle_search_code(
                arguments["query"],
                arguments.get("limit", 10),
                arguments.get("semantic_weight", 0.3),
                arguments.get("use_mmr", True)
            )
        elif name == "context_pack":
            result = _handle_context_pack(
                arguments["query"],
                arguments.get("token_budget", 8000),
                arguments.get("max_chunks", 20),
                arguments.get("strategy", "mmr")
            )
        elif name == "auto_index":
            result = _handle_auto_index(
                arguments.get("action", "status"),
                arguments.get("paths"),
                arguments.get("recursive", True)
            )
        elif name == "get_stats":
            result = _handle_get_stats()
        elif name == "cache_management":
            result = _handle_cache_management(
                arguments.get("action", "status"),
                arguments.get("cache_type", "all")
            )
        else:
            result = {"status": "error", "error": f"Tool {name} not found"}

        return [TextContent(type="text", text=str(result))]

# ===== INICIALIZAÇÃO DO SERVIDOR =====

if __name__ == "__main__":
    # Log de inicialização
    sys.stderr.write("🔄 Iniciando servidor MCP melhorado...\n")

    # Mostra status das funcionalidades
    if HAS_ENHANCED_FEATURES:
        sys.stderr.write("✅ Sistema de busca semântica ativado\n")
        sys.stderr.write("✅ Sistema de auto-indexação ativado\n")
    else:
        sys.stderr.write("⚠️  [mcp_server_enhanced] Recursos básicos apenas\n")
        sys.stderr.write("   💡 Instale sentence-transformers e watchdog para recursos completos\n")

    sys.stderr.write("✅ [mcp_server_enhanced] Servidor MCP melhorado iniciado\n")
    sys.stderr.write(f"   📍 Índice: {INDEX_DIR}\n")
    sys.stderr.write(f"   📁 Repositório: {INDEX_ROOT}\n")
    sys.stderr.write(f"   🧠 Busca semântica: {'Disponível' if HAS_ENHANCED_FEATURES else 'Indisponível'}\n")
    sys.stderr.write(f"   👁️  Auto-indexação: {'Disponível' if HAS_ENHANCED_FEATURES else 'Indisponível'}\n")

    # ===== INDEXAÇÃO AUTOMÁTICA NA INICIALIZAÇÃO =====
    def check_needs_initial_indexing():
        """Verifica se precisa fazer indexação inicial"""
        index_path = os.path.join(INDEX_DIR, "chunks.jsonl")
        inverted_path = os.path.join(INDEX_DIR, "inverted.json")

        # Se não existem arquivos de índice, precisa indexar
        if not os.path.exists(index_path) or not os.path.exists(inverted_path):
            return True

        # Se os arquivos existem mas estão vazios, precisa indexar
        try:
            if os.path.getsize(index_path) == 0 or os.path.getsize(inverted_path) == 0:
                return True
        except OSError:
            return True

        return False

    def perform_initial_indexing():
        """Executa indexação inicial do repositório"""
        sys.stderr.write("🔍 [startup] Executando indexação inicial do repositório...\n")

        try:
            # Define padrões de exclusão padrão
            default_exclude_globs = [
                "**/.git/**",
                "**/node_modules/**",
                "**/__pycache__/**",
                "**/dist/**",
                "**/build/**",
                "**/.venv/**",
                "**/venv/**",
                "**/.env",
                "**/.*cache/**",
                "**/*.pyc",
                "**/*.pyo",
                "**/*.pyd",
                "**/.*"
            ]

            # Executa indexação usando a função handler
            result = _handle_index_path(
                path=".",
                recursive=True,
                enable_semantic=HAS_ENHANCED_FEATURES,
                auto_start_watcher=HAS_ENHANCED_FEATURES,
                exclude_globs=default_exclude_globs
            )

            if result.get("status") == "success":
                indexed_files = result.get("indexed_files", 0)
                total_chunks = result.get("total_chunks", 0)
                sys.stderr.write(f"✅ [startup] Indexação inicial concluída!\n")
                sys.stderr.write(f"   📄 Arquivos indexados: {indexed_files}\n")
                sys.stderr.write(f"   🧩 Chunks criados: {total_chunks}\n")

                if HAS_ENHANCED_FEATURES and result.get("auto_indexing") == "started":
                    sys.stderr.write("   👁️  Auto-indexação iniciada para mudanças futuras\n")
            else:
                sys.stderr.write(f"⚠️  [startup] Indexação inicial com problemas: {result.get('error', 'Erro desconhecido')}\n")

        except Exception as e:
            sys.stderr.write(f"❌ [startup] Erro na indexação inicial: {str(e)}\n")
            sys.stderr.write("   💡 O servidor continuará funcionando, mas será necessário indexar manualmente\n")

    # Verifica se precisa fazer indexação inicial
    if check_needs_initial_indexing():
        sys.stderr.write("🔍 [startup] Índice não encontrado ou vazio - iniciando indexação automática\n")
        perform_initial_indexing()
    else:
        sys.stderr.write("✅ [startup] Índice existente encontrado - carregando dados\n")

        # Mesmo com índice existente, inicia auto-indexação se disponível
        if HAS_ENHANCED_FEATURES and hasattr(_indexer, 'start_auto_indexing'):
            try:
                _indexer.start_auto_indexing()
                sys.stderr.write("👁️  [startup] Auto-indexação iniciada para mudanças futuras\n")
            except Exception as e:
                sys.stderr.write(f"⚠️  [startup] Não foi possível iniciar auto-indexação: {str(e)}\n")

    # Executa servidor com a API correta
    if HAS_FASTMCP:
        # FastMCP não usa stdio=True, executa diretamente
        mcp.run()
    else:
        # MCP tradicional usa stdio_server
        import asyncio
        asyncio.run(stdio_server(server))