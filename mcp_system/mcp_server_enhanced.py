# mcp_server_enhanced.py
"""
Servidor MCP melhorado com busca semântica e auto-indexação
Usando FastMCP para API simplificada com decorators
"""

import os
import sys
import time

# === CodeLLM drop-in defaults ===
try:
    from pathlib import Path as _Path
    import os as _os, sys as _sys
    _THIS_DIR = _Path(__file__).resolve().parent
    _PROJECT_ROOT = _Path(_os.getenv("CODELLM_PROJECT_PATH", _THIS_DIR.parent))
    _os.environ.setdefault("INDEX_ROOT", str(_PROJECT_ROOT))
    _os.environ.setdefault("INDEX_DIR", str(_THIS_DIR / ".mcp_index"))
    _os.environ.setdefault("EMBEDDINGS_CACHE_DIR", str(_THIS_DIR / ".emb_cache"))
    # Garante imports absolutos (mcp_system.*) em diferentes configurações de PATH
    def _ensure_import_root(prj: _Path, pkg_name: str = "mcp_system") -> None:
        # Se prj for a própria pasta do pacote, adicione o pai ao sys.path
        if prj.name == pkg_name and str(prj.parent) not in _sys.path:
            _sys.path.insert(0, str(prj.parent))
        # Se prj contiver a pasta do pacote, adicione prj
        elif (prj / pkg_name).exists() and str(prj) not in _sys.path:
            _sys.path.insert(0, str(prj))
        # Como fallback, garanta ao menos a pasta do script
        if str(_THIS_DIR) not in _sys.path:
            _sys.path.insert(0, str(_THIS_DIR))
    _ensure_import_root(_PROJECT_ROOT)
except Exception:
    pass


from typing import Any, Dict, List
import pathlib
import threading
import csv
import datetime as dt
import threading

_tokens_lock = threading.Lock()
_tokens_sent_total = 0
_tokens_saved_total = 0
_cache_tokens_saved_total = 0
_compression_tokens_saved_total = 0
_last_query_tokens_sent = 0
_last_query_tokens_saved = 0


import logging

logger = logging.getLogger("mcp_server")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s"))
    logger.addHandler(h)
logger.setLevel(os.getenv("MCP_LOG_LEVEL", "INFO").upper())
logger.propagate = False


def set_log_level(level: str = "INFO"):
    import logging
    lvl = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(lvl)
    logging.getLogger("mcp_system.code_indexer_enhanced").setLevel(lvl)
    logger.info("Log level alterado para %s", level.upper())


def _update_metrics_from_pack(pack: dict):
    sent  = int(pack.get("total_tokens_sent", 0))
    saved = int(pack.get("tokens_saved_total", 0))
    cache_saved = int(pack.get("cache_tokens_saved", 0))
    compr_saved = int(pack.get("compression_tokens_saved", 0))
    global _last_query_tokens_sent, _last_query_tokens_saved
    with _tokens_lock:
        _last_query_tokens_sent = sent
        _last_query_tokens_saved = saved
        globals()["_tokens_sent_total"] += sent
        globals()["_tokens_saved_total"] += saved
        globals()["_cache_tokens_saved_total"] += cache_saved
        globals()["_compression_tokens_saved_total"] += compr_saved

# add subprocess for git fallback and filesystem ops
import subprocess
from pathlib import Path
# memória operacional mínima (opcional)
_HAS_MEMORY = False
import logging
logger = logging.getLogger(__name__)

try:
    # Preferir import absoluto para funcionar fora do contexto de pacote
    from mcp_system.memory_store import MemoryStore  # type: ignore
    _HAS_MEMORY = True
    try:
        logger.debug("[mcp_server_enhanced] 🧠 MemoryStore disponível")
    except Exception:
        pass
except Exception as e_abs:
    try:
        # Fallback para import relativo quando executado como pacote
        from .memory_store import MemoryStore  # type: ignore
        _HAS_MEMORY = True
        try:
            logger.debug("[mcp_server_enhanced] 🧠 MemoryStore disponível (import relativo)")
        except Exception:
            pass
    except Exception as e_rel:
        MemoryStore = None  # type: ignore
        _HAS_MEMORY = False
        try:
            logger.warning("[mcp_server_enhanced] ⚠️ MemoryStore indisponível: abs=%s; rel=%s", e_abs, e_rel)
        except Exception:
            pass

def context_pack(query: str, token_budget: int = 800, max_chunks: int = 8, strategy: str = "mmr"):
    # `indexer` deve ser a instância global já inicializada nesse módulo
    pack = build_context_pack(
        indexer=indexer,
        query=query,
        budget_tokens=token_budget,
        max_chunks=max_chunks,
        strategy=strategy
    )
    _update_metrics_from_pack(pack)
    return {"status": "success", "data": pack}

from typing import Optional  # for safe Optional annotations
from pathlib import Path

# Obter o diretório do script atual
CURRENT_DIR = pathlib.Path(__file__).parent.absolute()

# Import FastMCP (agora obrigatório)
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    logger.error("[mcp_server_enhanced] ERROR: FastMCP não encontrado. Instale `mcp[fastmcp]`.")
    logger.error("[mcp_server_enhanced] Execute: pip install 'mcp[fastmcp]'")
    raise

# Import de componentes do indexador (base e enhanced) usando caminho absoluto
# Primeiro garantimos os componentes base
try:
    from mcp_system.code_indexer_enhanced import (
        BaseCodeIndexer,
        search_code,
        build_context_pack,
        index_repo_paths,
    )
except ImportError as e:
    logger.error("[mcp_server_enhanced] ❌ Componentes base do indexador indisponíveis: %s", e)
    raise

# Depois tentamos carregar as funcionalidades melhoradas (opcionais)
try:
    from mcp_system.code_indexer_enhanced import (
        EnhancedCodeIndexer,
        enhanced_search_code,
        enhanced_build_context_pack,
        enhanced_index_repo_paths,
    )
    HAS_ENHANCED_FEATURES = True
    logger.info("[mcp_server_enhanced] ✅ Funcionalidades melhoradas carregadas")
except Exception as e:
    logger.warning("[mcp_server_enhanced] ⚠️ Funcionalidades melhoradas indisponíveis: %s", e)
    HAS_ENHANCED_FEATURES = False

HAS_CONTEXT_MEMORY = False
# === Semantic Rerank Helpers (v4) ===
from typing import Optional
_SEM_MODEL = None
def _sem_embed(texts):
    """Return np.ndarray embeddings or None if unavailable."""
    try:
        import numpy as _np
    except Exception:
        return None
    try:
        global _SEM_MODEL
        if _SEM_MODEL is None:
            try:
                from semantic_search import SemanticSearchEngine as _SSE
                _SEM_MODEL = _SSE()
                def _emb_ss(txts):
                    if hasattr(_SEM_MODEL, 'encode'):
                        return _np.array(_SEM_MODEL.encode(txts))
                    if hasattr(_SEM_MODEL, 'embed'):
                        return _np.array(_SEM_MODEL.embed(txts))
                    return None
                _SEM_MODEL._encode = _emb_ss
            except Exception:
                from sentence_transformers import SentenceTransformer
                _SEM_MODEL = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                _SEM_MODEL._encode = lambda txts: _np.array(_SEM_MODEL.encode(txts))
        vecs = _SEM_MODEL._encode(texts if isinstance(texts, (list, tuple)) else [texts])
        return vecs
    except Exception:
        return None

def _cosine_sim(a, b):
    try:
        import numpy as _np
        a = _np.array(a); b = _np.array(b)
        if a.ndim == 1: a = a[None, :]
        if b.ndim == 1: b = b[None, :]
        a_norm = a / ( _np.linalg.norm(a, axis=1, keepdims=True) + 1e-9 )
        b_norm = b / ( _np.linalg.norm(b, axis=1, keepdims=True) + 1e-9 )
        return (a_norm @ b_norm.T).squeeze()
    except Exception:
        return None

# Removed stray except that caused SyntaxError

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

# Expose the global _indexer as indexer for external use
indexer = _indexer

# Após inicializar o indexer global, adicionar bloco de pré-aquecimento
try:
    if callable(globals().get("context_pack")):
        _ = context_pack(query="__warmup__", token_budget=8, max_chunks=1, strategy="mmr")
        logger.info("[warmup] Pré-aquecimento concluído com sucesso")
except Exception as e:
    logger.debug("[warmup] Ignorado: %s", e)

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

        # Inicializa memória e registra um resumo da indexação inicial
        try:
            mem = _get_memory()
            if mem is not None:
                files = int(result.get('files_indexed', 0)) if isinstance(result, dict) else 0
                chunks = int(result.get('chunks', 0)) if isinstance(result, dict) else 0
                title = f"Indexação inicial concluída: {files} arquivos, {chunks} chunks"
                details = (
                    f"paths={os.pathsep.join(AUTO_INDEX_PATHS)} | recursive={AUTO_INDEX_RECURSIVE} | "
                    f"semantic={AUTO_ENABLE_SEMANTIC} | watcher={AUTO_START_WATCHER} | index_dir={INDEX_DIR}"
                )
                mem.add_session_summary(project=str(Path(INDEX_ROOT).name), title=title, details=details, scope="index")
        except Exception as e:
            sys.stderr.write(f"[mcp_server_enhanced] ⚠️ Falha ao inicializar memória ou registrar resumo: {e}\n")
    except Exception as e:
        sys.stderr.write(f"[mcp_server_enhanced] ⚠️ Falha na indexação inicial: {e}\n")

# ===== HANDLERS IMPLEMENTATION =====

import threading

# Global counters for token statistics
_tokens_avoided_lock = threading.Lock()
_tokens_avoided_total = 0

# Helper function to add tokens avoided

def add_tokens_avoided(tokens: int):
    global _tokens_avoided_total
    with _tokens_avoided_lock:
        _tokens_avoided_total += tokens

# Helper function to get tokens avoided

def get_tokens_avoided() -> int:
    with _tokens_avoided_lock:
        return _tokens_avoided_total

# Inicialização preguiçosa da memória, baseada em INDEX_ROOT
_memory: Optional['MemoryStore'] = None
_MEMORY_WARNED: bool = False

def _get_memory() -> Optional['MemoryStore']:
    global _memory, _MEMORY_WARNED
    if not _HAS_MEMORY:
        if not _MEMORY_WARNED:
            try:
                sys.stderr.write("[mcp_server_enhanced] ℹ️ MemoryStore desativado (_HAS_MEMORY=False). Nenhum resumo será persistido.\n")
            except Exception:
                pass
            _MEMORY_WARNED = True
        return None
    try:
        if _memory is None:
            root = Path(INDEX_ROOT)
            _memory = MemoryStore(root)  # type: ignore[name-defined]
            try:
                # Loga caminho do DB de memória para visibilidade
                db_path = getattr(_memory, 'db_path', None)
                if db_path:
                    sys.stderr.write(f"[mcp_server_enhanced] 🧠 Memory DB em uso: {db_path}\n")
            except Exception:
                pass
        return _memory
    except Exception:
        return None

def _handle_index_path(path, recursive, enable_semantic, auto_start_watcher, exclude_globs):
    """Handler para indexar um caminho"""
    # Validação de entrada
    if not path or not isinstance(path, str) or not path.strip():
        return {
            'status': 'error',
            'error': 'Parâmetro "path" é obrigatório e deve ser uma string não vazia'
        }

    # Validação de recursive
    if recursive is not None and not isinstance(recursive, bool):
        return {
            'status': 'error',
            'error': 'Parâmetro "recursive" deve ser um booleano'
        }

    # Validação de enable_semantic
    if enable_semantic is not None and not isinstance(enable_semantic, bool):
        return {
            'status': 'error',
            'error': 'Parâmetro "enable_semantic" deve ser um booleano'
        }

    # Validação de auto_start_watcher
    if auto_start_watcher is not None and not isinstance(auto_start_watcher, bool):
        return {
            'status': 'error',
            'error': 'Parâmetro "auto_start_watcher" deve ser um booleano'
        }

    # Validação de exclude_globs
    if exclude_globs is not None and not isinstance(exclude_globs, list):
        return {
            'status': 'error',
            'error': 'Parâmetro "exclude_globs" deve ser uma lista'
        }

    path = path.strip()  # Remove espaços extras
    sys.stderr.write(f"🔍 [index_path] {path} (recursive={recursive}, semantic={enable_semantic}, watcher={auto_start_watcher})\n")
    sys.stderr.write(f"[mcp_server_enhanced] exclude_globs recebido: {exclude_globs}\n")

    try:
        # Converte path relativo para absoluto
        if not os.path.isabs(path):
            path = os.path.join(INDEX_ROOT, path)

        t0 = time.perf_counter()
        if HAS_ENHANCED_FEATURES:
            sys.stderr.write(f"[mcp_server_enhanced] Passando exclude_globs para enhanced_index_repo_paths: {exclude_globs}\n")
            result = enhanced_index_repo_paths(
                _indexer,
                [path],
                recursive=recursive,
                enable_semantic=enable_semantic,
                exclude_globs=exclude_globs  # Passar None diretamente para usar padrão
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
        elapsed = round(time.perf_counter() - t0, 3)
        try:
            if isinstance(result, dict):
                result['elapsed_s'] = elapsed
        except Exception:
            pass

        # Após indexação, registrar um session_summary mínimo (se memória disponível)
        try:
            mem = _get_memory()
            if mem is not None:
                files = int(result.get('files_indexed', 0)) if isinstance(result, dict) else 0
                chunks = int(result.get('chunks', 0)) if isinstance(result, dict) else 0
                title = f"Indexação concluída: {files} arquivos, {chunks} chunks"
                details = f"Path: {path} | recursive={recursive} | semantic={enable_semantic} | watcher={auto_start_watcher}"
                mem.add_session_summary(project=str(Path(INDEX_ROOT).name), title=title, details=details, scope="index")
        except Exception:
            pass

        # Registrar métricas desta operação em metrics_index.csv
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
                "op": "index_path",
                "path": str(path),
                "index_dir": index_dir_str,
                "files_indexed": int(result.get("files_indexed", 0)) if isinstance(result, dict) else 0,
                "chunks": int(result.get("chunks", 0)) if isinstance(result, dict) else 0,
                "recursive": bool(recursive),
                "include_globs": "",
                "exclude_globs": ";".join(exclude_globs) if exclude_globs else "",
                "elapsed_s": elapsed,
            }

            file_exists = metrics_path.exists()
            with open(metrics_path, "a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(row.keys()))
                if not file_exists:
                    w.writeheader()
                w.writerow(row)
        except Exception as e:
            sys.stderr.write(f"[mcp_server_enhanced] ⚠️ Falha ao logar métricas de index_path: {e}\n")

        # Padroniza o retorno para consistência
        return {
            'status': 'success',
            'data': result
        }

    except Exception as e:
        sys.stderr.write(f"❌ [index_path] Erro: {str(e)}\n")
        return {'status': 'error', 'error': str(e)}

def _handle_search_code(query, limit, semantic_weight, use_mmr):
    """Handler para buscar código"""
    # Validação de entrada
    if not query or not isinstance(query, str) or not query.strip():
        return {
            'status': 'error',
            'error': 'Parâmetro "query" é obrigatório e deve ser uma string não vazia'
        }

    # Validação de limit
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        return {
            'status': 'error',
            'error': 'Parâmetro "limit" deve ser um inteiro positivo'
        }

    # Validação de semantic_weight
    if semantic_weight is not None and not isinstance(semantic_weight, (int, float)):
        return {
            'status': 'error',
            'error': 'Parâmetro "semantic_weight" deve ser um número'
        }

    # Validação de use_mmr
    if use_mmr is not None and not isinstance(use_mmr, bool):
        return {
            'status': 'error',
            'error': 'Parâmetro "use_mmr" deve ser um booleano'
        }

    query = query.strip()  # Remove espaços extras
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

import threading

_tokens_lock = threading.Lock()
_tokens_sent_total = 0
_tokens_saved_total = 0
_cache_tokens_saved_total = 0
_compression_tokens_saved_total = 0
_last_query_tokens_sent = 0
_last_query_tokens_saved = 0


def _update_metrics_from_pack(pack: dict):
    sent  = int(pack.get("total_tokens_sent", 0))
    saved = int(pack.get("tokens_saved_total", 0))
    cache_saved = int(pack.get("cache_tokens_saved", 0))
    compr_saved = int(pack.get("compression_tokens_saved", 0))
    global _last_query_tokens_sent, _last_query_tokens_saved
    with _tokens_lock:
        _last_query_tokens_sent = sent
        _last_query_tokens_saved = saved
        globals()["_tokens_sent_total"] += sent
        globals()["_tokens_saved_total"] += saved
        globals()["_cache_tokens_saved_total"] += cache_saved
        globals()["_compression_tokens_saved_total"] += compr_saved


def context_pack(query: str, token_budget: int = 800, max_chunks: int = 8, strategy: str = "mmr"):
    # `indexer` deve ser a instância global já inicializada neste módulo
    pack = build_context_pack(indexer=indexer, query=query, budget_tokens=token_budget, max_chunks=max_chunks, strategy=strategy)
    _update_metrics_from_pack(pack)
    return {"status": "success", "data": pack}


def ensure_ready():
    """
    Garante que o indexador e capacidades estejam prontos para consulta de stats.
    - Carrega índice do disco se necessário
    - Inicializa contadores de BM25 se for lazy
    - Seta flags de capacidades
    """
    global indexer
    # carregar índice se o indexer expõe load_index()
    if hasattr(indexer, "load_index"):
        try:
            indexer.load_index()
        except Exception:
            pass
    # garantir chunks em memória
    if not getattr(indexer, "chunks", None):
        if hasattr(indexer, "get_all_chunks"):
            try:
                _ = indexer.get_all_chunks()
            except Exception:
                pass
    # capacidades
    semantic_ok = bool(getattr(indexer, "embed_text", None) or getattr(indexer, "embed", None))
    globals()["semantic_enabled"] = semantic_ok
    globals()["auto_indexing_enabled"] = bool(globals().get("AUTO_INDEX_ON_START", True))
    globals()["fastmcp"] = True


def _handle_get_stats():
    ensure_ready()
    data = {}

    # métricas do índice com preenchimento garantido
    try:
        data["total_files"] = int(getattr(indexer, "total_files", lambda: 0)())
    except Exception:
        data["total_files"] = 0

    try:
        data["total_chunks"] = int(getattr(indexer, "total_chunks", lambda: 0)())
    except Exception:
        data["total_chunks"] = 0

    try:
        size_bytes = float(getattr(indexer, "index_size_bytes", lambda: 0)())
        data["index_size_mb"] = round(size_bytes / (1024 * 1024), 2)
    except Exception:
        data["index_size_mb"] = 0.0

    try:
        data["last_updated"] = getattr(indexer, "last_updated_iso", lambda: "")()
    except Exception:
        data["last_updated"] = ""

    # capacidades
    data["semantic_enabled"] = bool(globals().get("semantic_enabled", False))
    data["auto_indexing_enabled"] = bool(globals().get("auto_indexing_enabled", False))
    data["has_enhanced_features"] = True
    data["capabilities"] = {
        "semantic_search": data["semantic_enabled"],
        "auto_indexing": data["auto_indexing_enabled"],
        "fastmcp": bool(globals().get("fastmcp", True)),
        "semantic_enabled": data["semantic_enabled"],
        "auto_indexing_enabled": data["auto_indexing_enabled"],
        "has_enhanced_features": True,
    }

    # tokens (assumindo que os acumuladores já existem)
    data["last_query_total_tokens"] = globals().get("_last_query_tokens_sent", 0)
    data["last_query_tokens_saved"] = globals().get("_last_query_tokens_saved", 0)
    data["tokens_sent_total"] = globals().get("_tokens_sent_total", 0)
    data["tokens_saved_total"] = globals().get("_tokens_saved_total", 0)
    data["cache_tokens_saved_total"] = globals().get("_cache_tokens_saved_total", 0)
    data["compression_tokens_saved_total"] = globals().get("_compression_tokens_saved_total", 0)

    return {"status": "success", "action": "get_stats", "data": data}

def _handle_cache_management(action, cache_type):
    """Handler para gestão de cache"""
    # Validação de entrada
    if not action or not isinstance(action, str) or not action.strip():
        return {
            'status': 'error',
            'action': 'cache_management',
            'error': 'Parâmetro "action" é obrigatório e deve ser uma string não vazia'
        }

    action = action.strip().lower()

    # Validação de ações permitidas
    if action not in ['clear', 'status']:
        return {
            'status': 'error',
            'action': 'cache_management',
            'error': 'Parâmetro "action" deve ser "clear" ou "status"'
        }

    # Validação de cache_type
    if cache_type is not None and (not isinstance(cache_type, str) or not cache_type.strip()):
        return {
            'status': 'error',
            'action': 'cache_management',
            'error': 'Parâmetro "cache_type" deve ser uma string não vazia'
        }

    cache_type = cache_type or 'all'  # Valor padrão
    cache_type = cache_type.strip().lower()

    # Validação de tipos de cache permitidos
    if cache_type not in ['embeddings', 'all']:
        return {
            'status': 'error',
            'error': 'Parâmetro "cache_type" deve ser "embeddings" ou "all"'
        }

    sys.stderr.write(f"🗄️  [cache_management] {action} ({cache_type})\n")

    try:
        if action == 'clear':
            if cache_type == 'embeddings' and hasattr(_indexer, 'semantic_engine') and _indexer.semantic_engine:
                _indexer.semantic_engine.clear_cache()
                return {
                    'status': 'success',
                    'action': 'clear',
                    'data': {
                        'message': 'Cache de embeddings limpo',
                        'cache_type': 'embeddings'
                    }
                }
            elif cache_type == 'all':
                if hasattr(_indexer, 'semantic_engine') and _indexer.semantic_engine:
                    _indexer.semantic_engine.clear_cache()
                # Aqui você pode adicionar limpeza de outros caches se existirem
                return {
                    'status': 'success',
                    'action': 'clear',
                    'data': {
                        'message': 'Todos os caches limpos',
                        'cache_type': 'all'
                    }
                }
        elif action == 'status':
            result = {
                'status': 'success',
                'action': 'status'
            }
            if hasattr(_indexer, 'semantic_engine') and _indexer.semantic_engine:
                result['data'] = {
                    'embeddings_cache': _indexer.semantic_engine.get_cache_stats()
                }
            else:
                result['data'] = {
                    'embeddings_cache': {
                        'enabled': False,
                        'message': 'Semantic engine não disponível'
                    }
                }
            return result

    except Exception as e:
        return {'status': 'error', 'error': str(e)}

# ===== SERVIDOR MCP COM FASTMCP =====

# Cria servidor FastMCP (agora padrão)
mcp = FastMCP(name="code-indexer-enhanced")

# Dispara indexação inicial em background para não bloquear o initialize
try:
    threading.Thread(target=_initial_index, daemon=True).start()
except Exception as e:
    logger.warning("[mcp_server_enhanced] ⚠️ Não foi possível iniciar thread de indexação inicial: %s", e)

# Implementação mínima para where_we_stopped (context memory não disponível neste build)
def _handle_where_we_stopped(project: str, scope: str | None = None, days: int = 7, max_items: int = 20, excerpt_budget_chars: int = 1800, query: Optional[str] = None, focus: Optional[str] = None, semantic: bool = True):
    # Fallback leve sem memória operacional dedicada: usa git + TODO scan + context pack
    last_done = _git_recent_activity(days, max_items) or _read_dev_history_head(50) or "Sem histórico recente disponível."

    todo_hits = _scan_todos(limit=min(8, max_items))
    if todo_hits:
        todo_list = []
        for r in todo_hits:
            path = r.get('file_path'); sl = r.get('start_line'); el = r.get('end_line')
            prev = r.get('preview', '').splitlines()[:2]
            prev_str = (" ".join(prev)).strip()
            todo_list.append(f"- {path}:{sl}-{el} — {prev_str}")
        next_step = "Revisar itens pendentes (TODO/FIXME/blocked):\n" + "\n".join(todo_list)
    else:
        next_step = "Mapear próximas ações a partir dos arquivos-chave do projeto (nenhum TODO/FIXME encontrado)."

    blockers = "Sem bloqueios explícitos detectados. Considere verificar falhas recentes nos logs de CI ou exceções no runtime."

    hints = "Dica: use search_code para localizar módulos críticos e context_pack para preparar o contexto para uma tarefa específica."

    ctx = _mini_context_for(query, focus, excerpt_budget_chars, max_chunks=6)

    return {
        'status': 'success',
        'project': project,
        'scope': scope,
        'last_done': last_done,
        'next_step': next_step,
        'blockers': blockers,
        'hints': hints,
        'context': ctx or {'note': 'contexto não gerado'}
    }


def _read_dev_history_head(max_lines: int = 60) -> str | None:
    try:
        dev_hist = CURRENT_DIR.parent / 'dev_history.md'
        if dev_hist.exists():
            lines = dev_hist.read_text(encoding='utf-8', errors='ignore').splitlines()
            return "\n".join(lines[:max_lines])
    except Exception:
        pass
    return None


def _git_recent_activity(days: int, max_items: int) -> str | None:
    try:
        # Usa git para obter commits recentes
        since = f"--since={days}.days" if days and days > 0 else None
        cmd = ["git", "-C", str(INDEX_ROOT), "log", "--pretty=format:%h %ad %s", "--date=short", f"-n{max_items}"]
        if since:
            cmd.insert(5, since)
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        text = out.decode('utf-8', errors='ignore').strip()
        return text if text else None
    except Exception:
        return None


def _normalize_hit(hit) -> dict:
    try:
        if isinstance(hit, dict):
            return hit
        return {
            'file_path': getattr(hit, 'file_path', getattr(hit, 'path', '')),
            'start_line': getattr(hit, 'start_line', getattr(hit, 'line_start', None)),
            'end_line': getattr(hit, 'end_line', getattr(hit, 'line_end', None)),
            'preview': getattr(hit, 'preview', ''),
            'score': getattr(hit, 'score', getattr(hit, 'combined_score', None)),
        }
    except Exception:
        return {'file_path': '', 'start_line': None, 'end_line': None, 'preview': '', 'score': None}


def _scan_todos(limit: int = 5) -> list[dict]:
    try:
        q = "TODO FIXME blocked"
        if HAS_ENHANCED_FEATURES:
            results = enhanced_search_code(_indexer, q, limit=limit)
        else:
            results = search_code(_indexer, q, limit=limit)
        norm = [_normalize_hit(r) for r in (results or [])]
        # filtra entradas sem caminho
        return [r for r in norm if r.get('file_path')]
    except Exception:
        return []


def _mini_context_for(query: str | None, focus: str | None, excerpt_budget_chars: int, max_chunks: int = 6) -> dict | None:
    if not query and not focus:
        return None
    q = query or focus or ""
    try:
        budget_tokens = max(1, int(excerpt_budget_chars / 4))  # heurística ~4 chars/token
        if HAS_ENHANCED_FEATURES:
            return enhanced_build_context_pack(_indexer, q, budget_tokens=budget_tokens, max_chunks=max_chunks, strategy="mmr")
        else:
            return build_context_pack(_indexer, q, budget_tokens=budget_tokens, max_chunks=max_chunks, strategy="mmr")
    except Exception:
        return None

# ===== TOOLS BÁSICAS =====

@mcp.tool()
def where_we_stopped(project: str,
                     scope: str = None,
                     days: int = 7,
                     max_items: int = 20, excerpt_budget_chars: int = 1800, query: str = None, focus: str = None, semantic: bool = True) -> dict:
    """Resumo em 4 blocos: Último feito, Próximo passo, Bloqueios e Pistas"""
    return _handle_where_we_stopped(project, scope, days, max_items, excerpt_budget_chars, query, focus, semantic)

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
    # Use explicit facade instead of _handle_context_pack
    return context_pack(query, token_budget, max_chunks, strategy)

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

# ===== EXECUÇÃO DO SERVIDOR =====

if __name__ == "__main__":
    # Executa o servidor FastMCP apenas quando chamado diretamente
    mcp.run()