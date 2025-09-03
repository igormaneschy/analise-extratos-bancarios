# code_indexer_enhanced.py
# Sistema MCP melhorado com busca híbrida, auto-indexação e cache inteligente
from __future__ import annotations
import os, re, json, math, time, hashlib, threading, csv, datetime as dt
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Callable
import pathlib

import json

# Ensure a module-level CURRENT_DIR so defaults don't rely on external modules' variables
CURRENT_DIR = Path(__file__).parent.absolute()

# Try to import local deterministic cache for search/embeddings
try:
    from mcp_system.memory_store import get_cache, TTL_SEARCH_S, TTL_EMB_DAYS
except Exception:
    try:
        from .memory_store import get_cache, TTL_SEARCH_S, TTL_EMB_DAYS
    except Exception:
        get_cache = None
        TTL_SEARCH_S = 120
        TTL_EMB_DAYS = 14


_search_cache = get_cache("search") if callable(globals().get('get_cache')) else None
_emb_cache = get_cache("embeddings") if callable(globals().get('get_cache')) else None
_meta_cache = get_cache("metadata") if callable(globals().get('get_cache')) else None

# --- Métricas de contexto (arquivo CSV local, compatível com o servidor) ---
try:
    METRICS_CONTEXT_PATH = os.environ.get("MCP_METRICS_FILE", str(CURRENT_DIR / ".mcp_index/metrics_context.csv"))
except Exception:
    METRICS_CONTEXT_PATH = ".mcp_index/metrics_context.csv"

def _log_metrics(row: dict) -> None:
    """Anexa uma linha de métricas no CSV de contexto.
    Best-effort: qualquer exceção é suprimida para não impactar latência do pack.
    """
    try:
        os.makedirs(os.path.dirname(METRICS_CONTEXT_PATH), exist_ok=True)
        file_exists = os.path.exists(METRICS_CONTEXT_PATH)
        with open(METRICS_CONTEXT_PATH, "a", newline="", encoding="utf-8") as f:
            import csv as _csv
            w = _csv.DictWriter(f, fieldnames=list(row.keys()))
            if not file_exists:
                w.writeheader()
            w.writerow(row)
    except Exception:
        pass


# Função utilitária para obter timestamps UTC padronizados
def utc_timestamp() -> str:
    """Retorna timestamp UTC formatado em ISO 8601 segundos.

    Returns:
        str: Timestamp no formato 'YYYY-MM-DDTHH:MM:SS'
    """
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _normalize_query(q, opts):
    qn = " ".join((q or "").split()).lower()
    opts = opts or {}
    return {"q": qn, "opts": {k: opts[k] for k in sorted(opts) if opts[k] is not None}}


# Tenta importar recursos avançados
HAS_ENHANCED_FEATURES = True
try:
    from .embeddings.semantic_search import SemanticSearchEngine
    from .utils.file_watcher import create_file_watcher
except ImportError:
    HAS_ENHANCED_FEATURES = False
    SemanticSearchEngine = None
    create_file_watcher = None

# ========== CONSTANTES E UTILITÁRIOS BASE ==========

LANG_EXTS = {
    ".py", ".pyi",
    ".js", ".jsx", ".ts", ".tsx",
    ".java", ".go", ".rb", ".php",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rs", ".m", ".mm", ".swift", ".kt", ".kts",
    ".sql", ".sh", ".bash", ".zsh", ".ps1", ".psm1",
}

DEFAULT_INCLUDE = [
    "**/*.py","**/*.js","**/*.ts","**/*.tsx","**/*.jsx","**/*.java",
    "**/*.go","**/*.rb","**/*.php","**/*.c","**/*.cpp","**/*.cs",
    "**/*.rs","**/*.swift","**/*.kt","**/*.kts","**/*.sql","**/*.sh"
]
DEFAULT_EXCLUDE = [
    "**/.git/**",
    "**/.hg/**",
    "**/.svn/**",
    "**/__pycache__/**",
    "**/.mcp_index/**",
    "**/.mcp_memory/**",
    "**/.emb_cache/**",
    "**/node_modules/**",
    "**/dist/**",
    "**/build/**",
    "**/.venv/**",
    "**/venv/**",
    "**/.tox/**",
    "**/.cache/**",
]


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z_0-9]{1,}|[A-Za-z]{2,}")

def now_ts() -> float:
    return time.time()

def tokenize(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_PATTERN.findall(text)]

def est_tokens(text: str) -> int:
    # rough heuristic: ~4 chars per token
    try:
        if text is None:
            return 1
        return max(1, int(len(text) / 4))
    except Exception:
        # In case non-string types are passed, coerce to str and estimate
        try:
            return max(1, int(len(str(text)) / 4))
        except Exception:
            return 1

def hash_id(s: str) -> str:
    return hashlib.blake2s(s.encode("utf-8"), digest_size=12).hexdigest()

# ========== INDEXADOR BASE ==========

class BaseCodeIndexer:
    def __init__(self, index_dir: Optional[str] = None, repo_root: Optional[str] = None) -> None:
        # Delay default evaluation to runtime to avoid NameError when modules import each other
        idx_dir = index_dir or str(CURRENT_DIR / ".mcp_index")
        rp_root = repo_root or str(CURRENT_DIR.parent)
        self.index_dir = Path(idx_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.repo_root = Path(rp_root)
        self.chunks: Dict[str, Dict] = {}             # chunk_id -> data
        self.inverted: Dict[str, Dict[str, int]] = {} # term -> {chunk_id: tf}
        self.doc_len: Dict[str, int] = {}             # chunk_id -> token count
        self.file_mtime: Dict[str, float] = {}        # file_path -> mtime
        self.last_updated: Optional[str] = None       # ISO8601 (UTC)
        self._load()

    # ---------- persistence ----------
    def _paths(self):
        return (
            self.index_dir / "chunks.jsonl",
            self.index_dir / "inverted_index.json",
            self.index_dir / "doclen.json",
            self.index_dir / "file_mtime.json",
            self.index_dir / "meta.json",
        )

    def _load(self):
        """Load index from disk"""
        chunks_p = self.index_dir / "chunks.jsonl"
        inv_p = self.index_dir / "inverted_index.json"
        doclen_p = self.index_dir / "doclen.json"
        mtimes_p = self.index_dir / "file_mtime.json"
        meta_p = self.index_dir / "meta.json"

        # Initialize with default empty structures
        self.chunks = {}
        self.inverted = {}
        self.doc_len = {}
        self.file_mtime = {}
        self.last_updated = None

        # Check if index directory exists
        if not self.index_dir.exists():
            self.index_dir.mkdir(parents=True, exist_ok=True)
            return

        # Load chunks if file exists and is not empty
        if chunks_p.exists() and chunks_p.stat().st_size > 0:
            try:
                with open(chunks_p, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():  # Skip empty lines
                            chunk = json.loads(line)
                            self.chunks[chunk["chunk_id"]] = chunk
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not load chunks file: {e}")
                self.chunks = {}

        # Load inverted index if file exists and is not empty
        if inv_p.exists() and inv_p.stat().st_size > 0:
            try:
                self.inverted = json.loads(inv_p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not load inverted index file: {e}")
                self.inverted = {}

        # Load document lengths if file exists and is not empty
        if doclen_p.exists() and doclen_p.stat().st_size > 0:
            try:
                self.doc_len = {k: int(v) for k, v in json.loads(doclen_p.read_text(encoding="utf-8")).items()}
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not load document lengths file: {e}")
                self.doc_len = {}

        # Load file modification times if file exists and is not empty
        if mtimes_p.exists() and mtimes_p.stat().st_size > 0:
            try:
                self.file_mtime = {k: float(v) for k, v in json.loads(mtimes_p.read_text(encoding="utf-8")).items()}
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not load file mtimes file: {e}")
                self.file_mtime = {}

        # Load meta (last_updated)
        if meta_p.exists() and meta_p.stat().st_size > 0:
            try:
                meta = json.loads(meta_p.read_text(encoding="utf-8"))
                self.last_updated = meta.get("last_updated")
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not load meta file: {e}")
                self.last_updated = None

    def _save(self):
        chunks_p, inv_p, dl_p, mt_p, meta_p = self._paths()
        with chunks_p.open("w", encoding="utf-8") as f:
            for c in self.chunks.values():
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        inv_p.write_text(json.dumps(self.inverted), encoding="utf-8")
        dl_p.write_text(json.dumps(self.doc_len), encoding="utf-8")
        mt_p.write_text(json.dumps(self.file_mtime), encoding="utf-8")
        # Update last_updated and persist meta
        try:
            self.last_updated = utc_timestamp()
        except Exception:
            self.last_updated = self.last_updated or None
        meta_p.write_text(json.dumps({"last_updated": self.last_updated}, ensure_ascii=False), encoding="utf-8")

    # ---------- métricas e estatísticas ----------
    def get_stats(self) -> Dict[str, Any]:
        try:
            index_size_bytes = sum(len(json.dumps(c)) for c in self.chunks.values())
        except Exception:
            index_size_bytes = 0
        return {
            "total_chunks": len(self.chunks),
            "total_files": len(set(c.get("file_path") for c in self.chunks.values())),
            "index_size_mb": round(index_size_bytes / (1024 * 1024), 3),
            "last_updated": self.last_updated,
        }

    # ---------- chunking ----------
    def _read_text(self, path: Path) -> Optional[str]:
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            try:
                return path.read_text(errors="ignore")
            except Exception:
                return None

    def _split_chunks(self, path: Path, text: str, max_lines: int = 80, overlap: int = 12) -> List[Tuple[int,int,str]]:
        """
        Heuristic chunking: break at def/class for Python; else line windows with overlap.
        Returns list of (start_line, end_line, content)
        """
        lines = text.splitlines()
        boundaries = set()
        if path.suffix == ".py":
            for i, ln in enumerate(lines):
                if ln.lstrip().startswith("def ") or ln.lstrip().startswith("class "):
                    boundaries.add(i)
        boundaries.add(0)
        i = 0
        while i < len(lines):
            boundaries.add(i)
            i += max_lines - overlap
        sorted_bounds = sorted(boundaries)
        chunks = []
        for i in range(len(sorted_bounds)):
            start = sorted_bounds[i]
            end = min(len(lines), start + max_lines)
            content = "\n".join(lines[start:end])
            if content.strip():
                chunks.append((start+1, end, content))
        return chunks

    def _index_file(self, file_path: Path) -> Tuple[int,int]:
        text = self._read_text(file_path)
        if text is None:
            return (0,0)
        mtime = file_path.stat().st_mtime
        # Salvar path relativo ao repo_root para estabilidade
        try:
            rel_path = file_path.resolve().relative_to(self.repo_root.resolve())
        except Exception:
            rel_path = file_path.name
        self.file_mtime[str(rel_path)] = mtime

        chunks = self._split_chunks(file_path, text)
        new_chunks = 0
        new_tokens = 0
        for (start, end, content) in chunks:
            chunk_key = f"{rel_path}|{start}|{end}|{mtime}"
            cid = hash_id(chunk_key)
            toks = tokenize(content)
            if not toks:
                continue
            self.chunks[cid] = {
                "chunk_id": cid,
                "file_path": str(rel_path),
                "start_line": start,
                "end_line": end,
                "content": content,
                "mtime": mtime,
                "terms": toks[:2000],
            }
            self.doc_len[cid] = len(toks)
            new_chunks += 1
            new_tokens += len(toks)
        self._rebuild_inverted()
        return (new_chunks, new_tokens)

    def _rebuild_inverted(self):
        inverted: Dict[str, Dict[str,int]] = {}
        for cid, c in self.chunks.items():
            seen = {}
            for t in c["terms"]:
                seen[t] = seen.get(t, 0) + 1
            for t, tf in seen.items():
                inverted.setdefault(t, {})[cid] = tf
        self.inverted = inverted
        self._save()

# ========== FUNÇÕES DE INDEXAÇÃO ==========

import fnmatch
import sys
import re
import math
from collections import Counter

def _glob_match(path: Path, pattern: str) -> bool:
    s = path.as_posix()
    # Normaliza padrões comuns para cobrir casos onde Path.match falha
    candidates = {pattern}
    if pattern.startswith("**/"):
        candidates.add(pattern[3:])
    if pattern.endswith("/**"):
        # cobre um nível e múltiplos níveis
        base = pattern[:-3]
        candidates.add(base + "/*")
        candidates.add(base + "/**/*")
    return any(fnmatch.fnmatch(s, pat) for pat in candidates)


def is_excluded(path: Path, exclude_globs: List[str]) -> bool:
    # Filtro rápido por nome de diretório (não depende de glob)
    deny_dirs = {
        "venv", ".venv", "node_modules", "dist", "build",
        "__pycache__", ".git", ".mcp_index", ".mcp_memory",
        ".emb_cache", ".tox", ".cache"
    }
    if any(part in deny_dirs for part in path.parts):
        import logging
        logging.getLogger(__name__).debug(f"[is_excluded] Excluindo por nome de pasta: {path}")
        return True
    # Fallback para padrões glob
    if exclude_globs:
        if any(_glob_match(path, pat) for pat in exclude_globs):
            import logging
            logging.getLogger(__name__).debug(f"[is_excluded] Excluindo por padrão glob: {path}")
            return True
    return False


def index_repo_paths(
    indexer: BaseCodeIndexer,
    paths: list,
    recursive: bool = True,
    include_globs: list = None,
    exclude_globs: list = None
) -> dict:
    import logging
    logger = logging.getLogger(__name__)

    include = include_globs or DEFAULT_INCLUDE
    exclude = set(exclude_globs or DEFAULT_EXCLUDE)
    files_indexed = 0
    total_chunks = 0

    for p in paths:
        pth = Path(p)
        if not pth.is_absolute():
            pth = (indexer.repo_root / pth).resolve()

        # Caminho relativo para comparação com glob patterns
        try:
            rel_path = pth.relative_to(indexer.repo_root)
        except ValueError:
            rel_path = pth

        logger.debug(f"[index_repo_paths] Verificando arquivo: {pth} (relativo: {rel_path})")

        if pth.is_file():
            if any(fnmatch.fnmatch(str(rel_path), gl) for gl in include) and not is_excluded(rel_path, exclude):
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"[index_repo_paths] Indexando arquivo: {pth}")
                c, _ = indexer._index_file(pth)
                # Invalida estado BM25 para recalculo posterior
                if hasattr(indexer, "_bm25_ready"):
                    indexer._bm25_ready = False
                files_indexed += 1 if c > 0 else 0
                total_chunks += c
        elif pth.is_dir():
            base = pth
            for gl in include:
                iter_paths = base.rglob(gl) if recursive else base.glob(gl)
                for fp in iter_paths:
                    try:
                        rel_fp = fp.relative_to(indexer.repo_root)
                    except ValueError:
                        rel_fp = fp
                    if is_excluded(rel_fp, exclude):
                        logger.debug(f"[index_repo_paths] Arquivo excluído: {fp}")
                        continue
                    if not fp.is_file():
                        continue
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"[index_repo_paths] Indexando arquivo: {fp}")
                    c, _ = indexer._index_file(fp)
                    # Invalida estado BM25 para recalculo posterior
                    if hasattr(indexer, "_bm25_ready"):
                        indexer._bm25_ready = False
                    files_indexed += 1 if c > 0 else 0
                    total_chunks += c
        else:
            # caminho inexistente: ignora
            pass

    indexer._save()

    # Compute and persist index version. If the version changed, invalidate search/context/emb caches.
    try:
        old_ver = None
        if globals().get('_meta_cache') is not None:
            try:
                old_ver = _meta_cache.get('index_version')
            except Exception:
                old_ver = None
        new_ver = compute_index_version(indexer)

        # persist index_version into in-memory meta cache when available
        if globals().get('_meta_cache') is not None:
            try:
                _meta_cache.set('index_version', new_ver, ttl=None)
            except Exception:
                pass

        # Also persist the index_version into the index_dir/meta.json so it survives process restarts
        try:
            meta_path = getattr(indexer, 'index_dir', None)
            if meta_path is not None:
                try:
                    meta_p = Path(meta_path) / 'meta.json'
                    meta_obj = {}
                    if meta_p.exists():
                        try:
                            meta_obj = json.loads(meta_p.read_text(encoding='utf-8') or '{}') or {}
                        except Exception:
                            meta_obj = {}
                    meta_obj['index_version'] = new_ver
                    # preserve last_updated if available
                    try:
                        meta_obj['last_updated'] = getattr(indexer, 'last_updated', meta_obj.get('last_updated'))
                    except Exception:
                        pass
                    meta_p.write_text(json.dumps(meta_obj, ensure_ascii=False), encoding='utf-8')
                except Exception:
                    # Do not fail the whole indexing if persisting meta.json fails
                    pass
        except Exception:
            pass

        if new_ver != old_ver:
            logger.info(f"[index_repo_paths] index_version changed {old_ver} -> {new_ver}; clearing search/context/emb caches")
            try:
                if globals().get('_search_cache') is not None:
                    try:
                        _search_cache.clear()
                    except Exception:
                        pass
                # clear generic context cache if exists
                if callable(globals().get('get_cache')):
                    try:
                        ctx = get_cache('context')
                        if ctx is not None:
                            try:
                                ctx.clear()
                            except Exception:
                                pass
                    except Exception:
                        pass
                # clear embeddings cache if present
                try:
                    if globals().get('_emb_cache') is not None:
                        try:
                            _emb_cache.clear()
                        except Exception:
                            pass
                    elif callable(globals().get('get_cache')):
                        try:
                            emb = get_cache('embeddings')
                            if emb is not None:
                                try:
                                    emb.clear()
                                except Exception:
                                    pass
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"[index_repo_paths] falha ao limpar caches: {e}")
    except Exception as e:
        logger.debug(f"[index_repo_paths] compute_index_version failed: {e}")

    return {"files_indexed": files_indexed, "chunks": total_chunks}

def _tokenize_for_bm25(text: str) -> List[str]:
    return [t.lower() for t in re.findall(r"[A-Za-z0-9_]+", text or "")]

def _ensure_chunks(indexer) -> List[Dict]:
    chunks = getattr(indexer, "chunks", None)
    if chunks is None or not chunks:
        try:
            if hasattr(indexer, "load_index"):
                indexer.load_index()
            chunks = getattr(indexer, "chunks", []) or []
        except Exception:
            chunks = []
        indexer.chunks = chunks
    return chunks

def _ensure_bm25_state(indexer):
    if getattr(indexer, "_bm25_ready", False) and getattr(indexer, "chunks", None):
        return
    chunks = _ensure_chunks(indexer)
    doc_len = {}
    for ch in chunks:
        cid = ch.get("chunk_id") or ch.get("id") or id(ch)
        text = ch.get("text") or ch.get("content") or ch.get("content_snippet") or ""
        toks = _tokenize_for_bm25(text)
        doc_len[cid] = max(1, len(toks))

    N = len(chunks)
    avgdl = (sum(doc_len.values()) / N) if N > 0 else 1.0

    term_df = {}
    for ch in chunks:
        text = ch.get("text") or ch.get("content") or ch.get("content_snippet") or ""
        uniq = set(_tokenize_for_bm25(text))
        for t in uniq:
            term_df[t] = term_df.get(t, 0) + 1

    idf = {}
    for t, df in term_df.items():
        idf[t] = math.log(1 + (N - df + 0.5) / (df + 0.5)) if N > 0 else 0.0

    indexer.doc_len = doc_len
    indexer.avgdl = avgdl
    indexer.N = N
    indexer.idf = idf
    indexer._bm25_ready = True

def _bm25_scores(indexer, q_tokens, k1=1.5, b=0.75) -> List[Tuple[str, float]]:
    _ensure_bm25_state(indexer)
    chunks = _ensure_chunks(indexer)
    N = max(1, getattr(indexer, "N", len(chunks)))
    avgdl = getattr(indexer, "avgdl", 1.0) or 1.0
    idf = getattr(indexer, "idf", {})
    q_terms = [t.lower() for t in q_tokens or []]
    scores: List[Tuple[str, float]] = []

    for ch in chunks:
        cid = ch.get("chunk_id") or ch.get("id") or id(ch)
        text = ch.get("text") or ch.get("content") or ch.get("content_snippet") or ""
        doc_tokens = _tokenize_for_bm25(text)
        dl = indexer.doc_len.get(cid, max(1, len(doc_tokens)))
        tf_counts = Counter(doc_tokens)
        score = 0.0
        for qt in q_terms:
            f = tf_counts.get(qt, 0)
            if f == 0:
                continue
            idf_val = idf.get(qt, 0.0)
            denom = f + k1 * (1 - b + b * (dl / avgdl))
            score += idf_val * ((f * (k1 + 1)) / denom)
        scores.append((cid, score))

    return scores

def search_code(indexer, query, limit=50):
    q_tokens = _tokenize_for_bm25(query)
    _ensure_bm25_state(indexer)
    bm25 = _bm25_scores(indexer, q_tokens)

    cid_to_chunk = {}
    for ch in _ensure_chunks(indexer):
        cid = ch.get("chunk_id") or ch.get("id") or id(ch)
        cid_to_chunk[cid] = ch

    bm25.sort(key=lambda x: x[1], reverse=True)

    results = []
    for cid, sc in bm25[:limit]:
        ch = cid_to_chunk.get(cid)
        if ch:
            preview_lines = ch.get("content", "").splitlines()[:12]
            results.append({
                "chunk_id": cid,
                "file_path": ch.get("file_path", ""),
                "start_line": ch.get("start_line", 0),
                "end_line": ch.get("end_line", 0),
                "score": sc,
                "preview": "\n".join(preview_lines)
            })

    return results

# ========== FUNÇÕES DE CONTEXTO ==========

def get_chunk_by_id(indexer: BaseCodeIndexer, chunk_id: str) -> Optional[Dict]:
    return indexer.chunks.get(chunk_id)

def _summarize_chunk(c: Dict, query_tokens: List[str], max_lines: int = 18) -> str:
    """
    Sumariza o chunk pegando linhas que contenham termos da query.
    Se nada casar, usa as primeiras `max_lines` linhas.
    """
    try:
        # defensivo: content pode ser None ou estar ausente
        lines = (c.get("content") or "").splitlines()
    except Exception:
        lines = []
    header = f"{c.get('file_path', '')}:{c.get('start_line', 0)}-{c.get('end_line', 0)}"
    qset = set(query_tokens or [])

    picked: List[str] = []
    for ln in lines:
        try:
            tks = tokenize(ln)
        except Exception:
            tks = []
        if qset and (set(tks) & qset):
            picked.append(ln)
        if len(picked) >= max_lines:
            break

    if not picked:
        picked = lines[:max_lines]

    summary = header + "\n" + "\n".join(picked)
    return summary

# --- Index version utilities ---

def compute_index_version(indexer: BaseCodeIndexer) -> str:
    """
    Computa uma versão do índice baseado no hash dos chunks.
    """
    try:
        chunks = getattr(indexer, "chunks", []) or []
        # Considera id e texto
        hasher = hashlib.sha256()
        for ch in chunks:
            cid = str(ch.get("chunk_id") or ch.get("id") or "")
            text = ch.get("text") or ch.get("content") or ""
            hasher.update(cid.encode("utf-8"))
            hasher.update(text.encode("utf-8"))
        return hasher.hexdigest()
    except Exception:
        return ""

import json

def search_code(indexer, query, limit=50, filters=None, use_semantic=None, semantic_weight=None, use_mmr=None):
    # attempt to use search cache
    cache_key = None
    try:
        if _search_cache is not None:
            norm = _normalize_query(query, {})
            # Prefer a robust index signature (hash of chunks) when available
            try:
                idx_version = compute_index_version(indexer)
            except Exception:
                idx_version = getattr(indexer, 'last_updated_iso', getattr(indexer, 'last_updated', None))

            cache_payload = {
                "idx": idx_version,
                "q": norm,
                "filters": filters or {},
                "limit": int(limit) if limit is not None else None,
                "semantic": bool(use_semantic) if use_semantic is not None else None,
                "semantic_weight": float(semantic_weight) if semantic_weight is not None else None,
                "use_mmr": bool(use_mmr) if use_mmr is not None else None,
            }
            cache_key = json.dumps(cache_payload, sort_keys=True, default=str, separators=(",", ":"))
            cached = _search_cache.get(cache_key)
            if cached is not None:
                # Ensure sorting before returning
                try:
                    cached_sorted = sorted(cached, key=lambda r: (-r.get('score', 0.0), r.get('file_path', ''), r.get('chunk_id', '')))
                    return cached_sorted[:limit]
                except Exception:
                    return cached[:limit]
    except Exception:
        cache_key = None

    q_tokens = _tokenize_for_bm25(query)
    _ensure_bm25_state(indexer)
    bm25 = _bm25_scores(indexer, q_tokens)

    cid_to_chunk = {}
    for ch in _ensure_chunks(indexer):
        cid = ch.get("chunk_id") or ch.get("id") or id(ch)
        cid_to_chunk[cid] = ch

    bm25.sort(key=lambda x: x[1], reverse=True)

    results = []
    for cid, sc in bm25[:limit]:
        ch = cid_to_chunk.get(cid)
        if ch:
            preview_lines = ch.get("content", "").splitlines()[:12]
            results.append({
                "chunk_id": cid,
                "file_path": ch.get("file_path", ""),
                "start_line": ch.get("start_line", 0),
                "end_line": ch.get("end_line", 0),
                "score": sc,
                "preview": "\n".join(preview_lines)
            })

    # Order results deterministically by (score DESC, file_path ASC, chunk_id ASC)
    try:
        results = sorted(results, key=lambda r: (-r.get('score', 0.0), r.get('file_path', ''), r.get('chunk_id', '')))
    except Exception:
        pass

    # store in cache
    try:
        if _search_cache is not None and cache_key is not None:
            _search_cache.set(cache_key, results)
    except Exception:
        pass

    return results

def _l2norm(v: List[float]) -> List[float]:
    s = math.sqrt(sum(x*x for x in v)) or 1.0
    return [x/s for x in v]

def _cos_sim(a: List[float], b: List[float]) -> float:
    # a e b normalizados
    return sum(x*y for x,y in zip(a,b))

def _get_chunk_text(ch: Dict) -> str:
    return ch.get("text") or ch.get("content") or ch.get("content_snippet") or ch.get("summary") or ch.get("header") or ""

def _embed_chunk(embed_fn: Callable[[str], List[float]], ch: Dict) -> Optional[List[float]]:
    txt = _get_chunk_text(ch)
    # Normalize text for stable keys
    text_key = " ".join(str(txt).split()).strip().lower()

    # Try to use embeddings cache if available
    try:
        _local_emb_cache = _emb_cache if '_emb_cache' in globals() and _emb_cache is not None else None
        ttl_days = TTL_EMB_DAYS if 'TTL_EMB_DAYS' in globals() else 14

        cache_idx = None
        try:
            # If chunk provides an index_version field use it; otherwise try indexer-level last_updated
            if isinstance(ch, dict):
                cache_idx = ch.get('index_version') or ch.get('index_dir') or ch.get('index_hash')
            else:
                cache_idx = getattr(ch, 'index_version', None)
        except Exception:
            cache_idx = None

        cache_key = json.dumps({"idx": cache_idx, "text": text_key}, sort_keys=True, separators=(',', ':'))

        if _local_emb_cache is not None:
            try:
                cached = _local_emb_cache.get(cache_key)
            except Exception:
                cached = None
            if cached is not None:
                # Ensure a list of floats and L2-normalize
                try:
                    vec = list(cached)
                    return _l2norm(vec) if vec else None
                except Exception:
                    # fallback to recompute
                    pass
    except Exception:
        # Any cache-related error should not break embedding computation
        pass

    # Compute embedding
    emb = None
    try:
        emb = embed_fn(txt) if embed_fn else None
    except Exception:
        emb = None

    if emb:
        # coerce to plain list of floats (in case of numpy/torch)
        try:
            vec = list(map(float, emb))
        except Exception:
            try:
                vec = [float(x) for x in emb]
            except Exception:
                vec = None

        if vec is not None:
            # persist to cache if available
            try:
                if _local_emb_cache is not None and cache_key:
                    try:
                        _local_emb_cache.set(cache_key, vec, ttl=ttl_days * 86400)
                    except Exception:
                        pass
            except Exception:
                pass

            try:
                return _l2norm(vec)
            except Exception:
                return None

    return None

def _mmr_select(
    indexer_or_scored: object,
    ordered_ids_or_scored: List[str],
    query_tokens_or_none: Optional[List[str]] = None,
    k: int = 10,
    lambda_diverse: float = 0.7,
) -> List[str]:
    """
    Seleção MMR para diversidade estável com fallback

    Pode ser chamado de duas formas:
    1) (_mmr_select(scored, cid_to_chunk, embed_fn, k, lambda))
       - scored: lista de (chunk_id, score) - lista de tuplas
       - cid_to_chunk: dict {chunk_id: chunk_data}
       - embed_fn: função embed(texto) opcional (None para fallback)
    2) (_mmr_select(indexer, ordered_ids, query_tokens, k, lambda))
       - indexer: EnhancedCodeIndexer ou BaseCodeIndexer com índice carregado
       - ordered_ids: lista de chunk_ids ordenados por relevância (ex: BM25)
       - query_tokens: tokens da consulta para gerar embedding
    """
    # Detectar o modo (simplificado): se primeiro argumento for objeto com attribute chunks -> modo 2
    # modo 2: indexer, ordered_ids, query_tokens
    if hasattr(indexer_or_scored, 'chunks'):
        indexer = indexer_or_scored
        ordered_ids = ordered_ids_or_scored
        q_tokens = query_tokens_or_none or []
        scored_list = []
        cid_to_chunk = {}
        for cid in ordered_ids:
            ch = None
            if hasattr(indexer, "chunks"):
                # indexer.chunks pode ser list ou dict
                chunks = getattr(indexer, "chunks")
                if isinstance(chunks, dict):
                    ch = chunks.get(cid)
                elif isinstance(chunks, list):
                    ch = next((c for c in chunks if c.get("chunk_id") == cid), None)
            if not ch:
                continue
            cid_to_chunk[cid] = ch
            # Usar BM25 score inicial (default 1.0)
            scored_list.append((cid, 1.0))
        # Função para extrair embedding
        if hasattr(indexer, "semantic_engine") and getattr(indexer, "semantic_engine", None):
            embed_fn = getattr(indexer.semantic_engine, "embed_text", None)
        else:
            embed_fn = None
        scored = scored_list
    else:
        scored = indexer_or_scored
        cid_to_chunk = ordered_ids_or_scored
        embed_fn = None
        q_tokens = query_tokens_or_none or []

    if not scored:
        return []

    actual_k = max(1, min(k, len(scored)))

    # Tentar pré-calcular embeddings
    embs = {}
    use_embeddings = embed_fn is not None
    if use_embeddings:
        for cid, _ in scored:
            ch = cid_to_chunk.get(cid)
            if not ch:
                continue
            e = _embed_chunk(embed_fn, ch)
            if e:
                embs[cid] = e
            else:
                use_embeddings = False
                break

    # Fallback: Jaccard por tokens se não tem embeddings
    def _tokset(cid: str) -> set:
        import re
        ch = cid_to_chunk.get(cid) or {}
        s = _get_chunk_text(ch)
        return set(t.lower() for t in re.findall(r"[A-Za-z0-9_]+", s))

    selected: List[str] = []
    candidate_ids = [cid for cid, _ in scored]

    # pega top-1 por relevância diretamente
    selected.append(candidate_ids[0])

    while len(selected) < actual_k and candidate_ids:
        best_cid = None
        best_score = float("-inf")

        for cid in candidate_ids:
            if cid in selected:
                continue
            rel = next((s for (c, s) in scored if c == cid), 0.0)

            if use_embeddings:
                cand = embs.get(cid)
                if not cand:
                    div = 1.0
                else:
                    max_sim = 0.0
                    for sid in selected:
                        sv = embs.get(sid)
                        if sv:
                            sim = _cos_sim(cand, sv)
                            if sim > max_sim:
                                max_sim = sim
                    div = 1.0 - max_sim
            else:
                # diversidade via Jaccard
                cand_set = _tokset(cid)
                max_j = 0.0
                for sid in selected:
                    sset = _tokset(sid)
                    inter = len(cand_set & sset)
                    union = len(cand_set | sset) or 1
                    j = inter / union
                    if j > max_j:
                        max_j = j
                div = 1.0 - max_j

            mmr_score = lambda_diverse * rel + (1.0 - lambda_diverse) * div
            if mmr_score > best_score:
                best_score = mmr_score
                best_cid = cid

        if best_cid is None:
            break
        selected.append(best_cid)

    return selected[:actual_k]

def build_context_pack(
    indexer: BaseCodeIndexer,
    query: str,
    budget_tokens: int = 3000,
    max_chunks: int = 10,
    strategy: str = "mmr"
) -> Dict:
    """
    Retorna um "pacote de contexto" pronto para injeção no prompt:
      {
        "query": ...,
        "total_tokens": ...,
        "chunks": [
          {
            "chunk_id": ...,
            "header": "path:start-end",
            "summary": "<linhas mais relevantes>",
            "content_snippet": "<trecho comprimido dentro do orçamento>"
          },
          ...
        ]
      }
    """
    t0 = time.perf_counter()  # <-- start para medir latência

    q_tokens = tokenize(query)
    search_res = search_code(indexer, query, limit=max_chunks * 3)
    # supondo que você já tem: bm25 = [(cid, score), ...] ordenado desc
    bm25 = [(r["chunk_id"], r.get("score", 1.0)) for r in search_res]
    all_chunks = []
    if hasattr(indexer, "chunks"):
        if isinstance(indexer.chunks, dict):
            all_chunks = list(indexer.chunks.values())
        else:
            all_chunks = indexer.chunks

    cid_to_chunk = { ch["chunk_id"]: ch for ch in all_chunks if "chunk_id" in ch }
    embed_fn = None
    if hasattr(indexer, "semantic_engine") and indexer.semantic_engine and hasattr(indexer.semantic_engine, "embed_text"):
        embed_fn = indexer.semantic_engine.embed_text

    ordered_ids = None
    try:
        ordered_ids = _mmr_select(
            scored=bm25,
            cid_to_chunk=cid_to_chunk,
            embed_fn=embed_fn,
            k=max_chunks,
            lambda_diverse=0.7
        )
    except Exception:
        # fallback para top-k puro
        ordered_ids = [cid for cid, _ in bm25[:max_chunks]]

    if not ordered_ids:
        ordered_ids = [cid for cid, _ in bm25[:max_chunks]]

    pack = {"query": query, "total_tokens": 0, "chunks": []}
    remaining = max(1, budget_tokens)

    total_tokens_sent = 0
    tokens_saved_total = 0
    cache_tokens_saved = 0
    compression_tokens_saved = 0

    for cid in ordered_ids:
        c = cid_to_chunk.get(cid)
        if not c:
            # fallback para chunks não encontrados
            if hasattr(indexer.chunks, "get"):
                c = indexer.chunks.get(cid)
            else:
                c = next((item for item in indexer.chunks if item.get("chunk_id") == cid), None)
        if not c:
            continue

        header = f"{c['file_path']}:{c['start_line']}-{c['end_line']}"
        # summary may occasionally be None due to upstream issues; coerce to string
        summary = _summarize_chunk(c, q_tokens, max_lines=18) or ""

        raw_text = c.get('content', '')
        tokens_raw = est_tokens(raw_text)

        snippet = summary or ""
        tokens_sent = est_tokens(snippet)

        from_cache = c.get('from_cache', False)
        if from_cache:
            tokens_sent = 0  # ou custo mínimo do placeholder

        tokens_saved = max(0, tokens_raw - tokens_sent)

        pack["chunks"].append({
            "chunk_id": cid,
            "header": header,
            "summary": summary,
            "content_snippet": snippet,
            "tokens_raw": tokens_raw,
            "estimated_tokens": tokens_sent,
            "tokens_saved": tokens_saved,
            "from_cache": from_cache,
        })

        total_tokens_sent += tokens_sent
        tokens_saved_total += tokens_saved
        if from_cache:
            cache_tokens_saved += tokens_saved
        else:
            compression_tokens_saved += tokens_saved

        pack["total_tokens"] = total_tokens_sent
        remaining = max(0, remaining - tokens_sent)

        if len(pack["chunks"]) >= max_chunks or remaining <= 0:
            break

    pack["total_tokens_sent"] = total_tokens_sent
    pack["tokens_saved_total"] = tokens_saved_total
    pack["cache_tokens_saved"] = cache_tokens_saved
    pack["compression_tokens_saved"] = compression_tokens_saved

    if total_tokens_sent == 0 and pack["chunks"]:
        pack["total_tokens_sent"] = 1  # garantir > 0

    # --- LOG MÉTRICAS CSV ---
    try:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        # incluir campos adicionais sobre tokens enviados/poupados para facilitar agregação
        _log_metrics({
            "ts": utc_timestamp(),
            "query": query[:160],
            "chunk_count": len(pack["chunks"]),
            "total_tokens": pack.get("total_tokens", 0),
            "total_tokens_sent": pack.get("total_tokens_sent", 0),
            "tokens_saved_total": pack.get("tokens_saved_total", 0),
            "cache_tokens_saved": pack.get("cache_tokens_saved", 0),
            "compression_tokens_saved": pack.get("compression_tokens_saved", 0),
            "budget_tokens": budget_tokens,
            "budget_utilization": round(pack.get("total_tokens", 0) / max(1, budget_tokens), 3),
            "latency_ms": latency_ms,
        })
    except Exception:
        pass  # não quebra o fluxo se log falhar

    return pack


def compute_index_version(indexer: BaseCodeIndexer) -> str:
    """Computes a deterministic version/hash for the current index content.

    Strategy:
    - Collect a stable list of files (file paths) and their chunk ids + content digests
    - Build a canonical JSON structure with sorted keys and compute sha256
    - Return short hex digest
    """
    try:
        chunks = getattr(indexer, "chunks", {}) or {}
        items = []
        for cid in sorted(chunks.keys()):
            ch = chunks[cid]
            fp = ch.get("file_path", "")
            start = ch.get("start_line", 0)
            end = ch.get("end_line", 0)
            text = ch.get("content", ch.get("text", ""))
            # small digest of content for stability and performance
            h = hashlib.sha256((str(text) or "").encode("utf-8")).hexdigest()
            items.append({"chunk_id": cid, "file_path": fp, "start": start, "end": end, "digest": h})
        canonical = json.dumps(items, ensure_ascii=False, sort_keys=True)
        ver = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
        return ver
    except Exception:
        # fallback to last_updated timestamp if present
        try:
            if getattr(indexer, "last_updated", None):
                return hashlib.sha256(str(indexer.last_updated).encode("utf-8")).hexdigest()[:16]
        except Exception:
            pass
        return "unknown"


def get_current_index_version() -> str:
    """Return current index version stored in metadata cache, meta.json on disk, or 'unknown'.

    Search order:
    1) in-memory _meta_cache (fast)
    2) meta.json in default index_dir (if present)
    3) fallback 'unknown'
    """
    # 1) Try meta cache
    try:
        if globals().get('_meta_cache') is not None:
            try:
                v = _meta_cache.get('index_version')
                if v:
                    return v
            except Exception:
                pass
    except Exception:
        # defensive: if globals() or _meta_cache access fails
        pass

    # 2) Try meta.json file in a default index_dir (scan common paths)
    try:
        possible_dirs = []
        if globals().get('CURRENT_DIR') is not None:
            possible_dirs.append(str(Path(CURRENT_DIR) / '.mcp_index'))
        # Check common working directories
        possible_dirs.extend(['.mcp_index', str(Path(__file__).parent / '.mcp_index')])
        for d in possible_dirs:
            try:
                p = Path(d) / 'meta.json'
                if p.exists():
                    try:
                        obj = json.loads(p.read_text(encoding='utf-8') or '{}') or {}
                        if obj.get('index_version'):
                            return obj.get('index_version')
                    except Exception:
                        continue
            except Exception:
                continue
    except Exception:
        # ignore any unexpected errors while scanning filesystem
        pass

    return 'unknown'


# ========== INDEXADOR MELHORADO ==========

class EnhancedCodeIndexer:
    """
    Indexador de código mejorado que combina:
    - BM25 search (do indexador original)
    - Busca semântica com embeddings
    - Auto-indexação com file watcher
    - Cache inteligente
    """

    def __init__(self,
                 index_dir: str = ".mcp_index",
                 repo_root: str = ".",
                 enable_semantic: bool = True,
                 enable_auto_indexing: bool = True,
                 semantic_weight: float = 0.3):

        # Inicializa indexador base
        self.base_indexer = BaseCodeIndexer(index_dir=index_dir, repo_root=repo_root)

        # Configurações
        self.index_dir = Path(index_dir)
        self.repo_root = Path(repo_root)
        self.enable_semantic = enable_semantic and HAS_ENHANCED_FEATURES
        self.enable_auto_indexing = enable_auto_indexing and HAS_ENHANCED_FEATURES
        self.semantic_weight = semantic_weight

        # Inicializa componentes opcionais
        self.semantic_engine = None
        self.file_watcher = None

        # Inicializar chunks e estado BM25
        self.chunks: List[Dict] = getattr(self, "chunks", [])
        self.doc_len: Dict[str, int] = getattr(self, "doc_len", {})
        self.avgdl: float = getattr(self, "avgdl", 1.0)
        self.N: int = getattr(self, "N", 0)
        self.idf: Dict[str, float] = getattr(self, "idf", {})
        self._bm25_ready: bool = getattr(self, "_bm25_ready", False)

        # Flag de carregamento do índice
        self._index_loaded = False

        # Métricas da última indexação (descoberta/embedding/delta/cache)
        self._last_index_metrics: Dict[str, int] = {
            "index_discovery_ms": 0,
            "index_embed_ms": 0,
            "updated_files": 0,
            "updated_chunks": 0,
            "embeddings_hit": 0,
        }

        if self.enable_semantic:
            try:
                self.semantic_engine = SemanticSearchEngine(cache_dir=str(self.index_dir))
                # Mensagem será enviada pelo mcp_server_enhanced.py
            except Exception as e:
                import logging
                logging.getLogger(__name__).info(f"⚠️  Erro ao inicializar busca semântica: {e}")
                self.enable_semantic = False

        if self.enable_auto_indexing:
            try:
                self.file_watcher = create_file_watcher(
                    watch_path=str(self.repo_root),
                    indexer_callback=self._auto_index_callback,
                    debounce_seconds=2.0
                )
                # Mensagem será enviada pelo mcp_server_enhanced.py
            except Exception as e:
                import logging
                logging.getLogger(__name__).info(f"⚠️  Erro ao inicializar auto-indexação: {e}")
                self.enable_auto_indexing = False

        # Lock para thread safety
        self._lock = threading.RLock()

    def total_files(self) -> int:
        try:
            base_chunks = getattr(self.base_indexer, "chunks", {})
            if isinstance(base_chunks, dict):
                files = set()
                for c in base_chunks.values():
                    fp = c.get("file_path")
                    if fp:
                        files.add(fp)
                return len(files)
            elif isinstance(base_chunks, list):
                files = set()
                for c in base_chunks:
                    fp = c.get("file_path")
                    if fp:
                        files.add(fp)
                return len(files)
            else:
                return 0
        except Exception:
            return 0

    def total_chunks(self) -> int:
        try:
            base_chunks = getattr(self.base_indexer, "chunks", {})
            if isinstance(base_chunks, dict):
                return len(base_chunks)
            elif isinstance(base_chunks, list):
                return len(base_chunks)
            else:
                return 0
        except Exception:
            return 0

    def index_size_bytes(self) -> int:
        import os
        try:
            paths = []
            if hasattr(self, "index_dir"):
                d = getattr(self, "index_dir")
                if d and os.path.isdir(d):
                    for root, _, files in os.walk(d):
                        for f in files:
                            paths.append(os.path.join(root, f))
            return sum(os.path.getsize(p) for p in paths)
        except Exception:
            return 0

    def last_updated_iso(self) -> str:
        import datetime as dt
        try:
            # Try to get last_updated from base_indexer if possible
            if hasattr(self.base_indexer, "last_updated") and self.base_indexer.last_updated:
                # Attempt to parse ISO8601 string to datetime and reformat
                last_updated = self.base_indexer.last_updated
                try:
                    dt_obj = dt.datetime.fromisoformat(last_updated)
                    return dt_obj.isoformat(timespec="seconds")
                except Exception:
                    return last_updated
            ts = getattr(self, "_last_updated_ts", None)
            if isinstance(ts, (int, float)):
                return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).isoformat(timespec="seconds")
            return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        except Exception:
            return ""

    def _auto_index_callback(self, changed_files: List[Path]) -> Dict[str, Any]:
        """Callback para reindexação automática de arquivos modificados"""
        with self._lock:
            try:
                # Converte paths para strings
                file_paths = [str(f) for f in changed_files]

                # Reindexar usando indexador base
                result = self.index_files(file_paths, show_progress=False)

                # Mensagens de debug via stderr para não interferir com protocolo MCP
                import sys
                try:
                    files = int(result.get('files_indexed', 0)) if isinstance(result, dict) else 0
                    chunks = int(result.get('chunks', 0)) if isinstance(result, dict) else 0
                except Exception:
                    files, chunks = 0, 0
                # Só loga quando houver mudanças para evitar warnings ruidosos
                if files > 0 or chunks > 0:
                    sys.stderr.write(f"🔄 Auto-reindexação: {files} arquivos, {chunks} chunks\n")

                return result

            except Exception as e:
                import logging
                logging.getLogger(__name__).info(f"❌ Erro na auto-indexação: {e}")
                return {"files_indexed": 0, "chunks": 0, "error": str(e)}

    def is_auto_indexing_running(self) -> bool:
        """Verifica se o auto-indexing está em execução"""
        if hasattr(self, 'file_watcher'):
            return self.file_watcher is not None
        return False

    def index_files(self,
                   paths: List[str],
                   recursive: bool = True,
                   include_globs: List[str] = None,
                   exclude_globs: List[str] = None,
                   show_progress: bool = True) -> Dict[str, Any]:
        """
        Indexa arquivos usando o indexador base

        Args:
            paths: Lista de caminhos para indexar
            recursive: Se deve indexar recursivamente
            include_globs: Padrões de arquivos para incluir
            exclude_globs: Padrões de arquivos para excluir
            show_progress: Se deve mostrar progresso

        Returns:
            Dicionário com estatísticas da indexação
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.debug("[index_files] Tentando adquirir lock para indexar arquivos...")
        with self._lock:
            logger.debug("[index_files] Lock adquirido. Iniciando indexação...")
            try:
                if show_progress:
                    logger.info(f"📁 Indexando {len(paths)} caminhos...")

                # Aplica padrão DEFAULT_EXCLUDE se exclude_globs for None ou lista vazia
                effective_exclude = exclude_globs if exclude_globs else DEFAULT_EXCLUDE

                import time, json, hashlib

                # Métrica: início da descoberta
                t_disc_start = time.time()

                # Snapshot pré-indexação: assinatura por arquivo baseada nos chunks atuais
                def _build_file_signatures(chunks_any) -> Dict[str, Dict[str, Any]]:
                    file_map: Dict[str, Dict[str, Any]] = {}
                    try:
                        if isinstance(chunks_any, dict):
                            values = chunks_any.values()
                        elif isinstance(chunks_any, list):
                            values = chunks_any
                        else:
                            values = []
                        tmp: Dict[str, List[str]] = {}
                        for c in values:
                            fp = c.get("file_path") or ""
                            if not fp:
                                continue
                            cid = str(c.get("chunk_id") or c.get("id") or id(c))
                            text = (c.get("content") or c.get("text") or "")[:2000]
                            h = hashlib.sha256((cid + "|" + text).encode()).hexdigest()
                            tmp.setdefault(fp, []).append(h)
                        for fp, hashes in tmp.items():
                            hashes.sort()
                            sig = hashlib.sha256("".join(hashes).encode()).hexdigest()
                            file_map[fp] = {"sig": sig, "chunks": len(hashes)}
                    except Exception:
                        pass
                    return file_map

                # snapshot antes de indexar
                pre_map = _build_file_signatures(getattr(self.base_indexer, "chunks", {}))
                meta_path = Path(self.index_dir) / "index_meta.json"

                # Executa indexação base
                result = index_repo_paths(
                    self.base_indexer,
                    paths=paths,
                    recursive=recursive,
                    include_globs=include_globs,
                    exclude_globs=list(effective_exclude) if isinstance(effective_exclude, (list, set, tuple)) else DEFAULT_EXCLUDE,
                )

                t_index_end = time.time()

                if show_progress:
                    logger.info(f"✅ Indexação concluída: {result.get('files_indexed', 0)} arquivos, {result.get('chunks', 0)} chunks")

                # Sincronizar self.chunks com base_indexer.chunks
                try:
                    base_chunks = getattr(self.base_indexer, "chunks", {})
                    if isinstance(base_chunks, dict):
                        self.chunks = list(base_chunks.values())
                    elif isinstance(base_chunks, list):
                        self.chunks = base_chunks
                    else:
                        self.chunks = []
                    self._index_loaded = True
                except Exception:
                    pass

                # Snapshot pós-indexação e delta
                post_map = _build_file_signatures(getattr(self.base_indexer, "chunks", {}))

                updated_files = 0
                updated_chunks = 0
                embeddings_hit = 0
                all_files = set(pre_map.keys()) | set(post_map.keys())
                for fp in all_files:
                    pre = pre_map.get(fp)
                    post = post_map.get(fp)
                    if not post:
                        continue
                    if not pre or pre.get("sig") != post.get("sig"):
                        updated_files += 1
                        updated_chunks += int(post.get("chunks", 0))
                    else:
                        embeddings_hit += int(post.get("chunks", 0))

                # Métricas de fase
                t_disc_end = time.time()
                index_discovery_ms = int((t_disc_end - t_disc_start) * 1000)
                total_ms = int((t_index_end - t_disc_start) * 1000)
                index_embed_ms = max(0, total_ms - index_discovery_ms)

                # Persistir meta simples para próxima execução
                try:
                    meta_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(meta_path, "w", encoding="utf-8") as f:
                        json.dump({"files": post_map}, f)
                except Exception:
                    pass

                # Atualizar métricas locais
                self._last_index_metrics = {
                    "index_discovery_ms": index_discovery_ms,
                    "index_embed_ms": index_embed_ms,
                    "updated_files": updated_files,
                    "updated_chunks": updated_chunks,
                    "embeddings_hit": embeddings_hit,
                }

                # Enriquecer resultado retornado com métricas e deltas
                result = dict(result or {})
                result.setdefault("updated_files", updated_files)
                result.setdefault("updated_chunks", updated_chunks)
                result.setdefault("index_discovery_ms", index_discovery_ms)
                result.setdefault("index_embed_ms", index_embed_ms)
                result.setdefault("embeddings_hit", embeddings_hit)
                # garantir index_dir como string serializável
                try:
                    result.setdefault("index_dir", str(self.index_dir))
                except Exception:
                    result.setdefault("index_dir", "")

                result.setdefault("updated_files", updated_files)
                result.setdefault("updated_chunks", updated_chunks)
                result.setdefault("index_discovery_ms", index_discovery_ms)
                result.setdefault("index_embed_ms", index_embed_ms)
                result.setdefault("embeddings_hit", embeddings_hit)
                # garantir index_dir como string serializável
                try:
                    result.setdefault("index_dir", str(self.index_dir))
                except Exception:
                    result.setdefault("index_dir", "")

                return result

            except Exception as e:
                logger.info(f"❌ Erro na indexação: {e}")
                try:
                    index_dir_str = str(self.index_dir)
                except Exception:
                    index_dir_str = ""
                return {"files_indexed": 0, "chunks": 0, "error": str(e), "index_dir": index_dir_str}

    def load_index(self):
        """Carrega o índice e atualiza self.chunks"""
        try:
            base_chunks = getattr(self.base_indexer, "chunks", {})
            if isinstance(base_chunks, dict):
                self.chunks = list(base_chunks.values())
            elif isinstance(base_chunks, list):
                self.chunks = base_chunks
            else:
                self.chunks = []
            self._index_loaded = True
        except Exception:
            self.chunks = []
            self._index_loaded = False

    def get_all_chunks(self) -> List[Dict]:
        """Retorna todos os chunks carregados, carregando se necessário"""
        if not getattr(self, "_index_loaded", False):
            try:
                self.load_index()
            except Exception:
                self.chunks = []
        return self.chunks or []

    def search_code(self,
                   query: str,
                   limit: int = 30,
                   use_semantic: Optional[bool] = None,
                   semantic_weight: Optional[float] = None,
                   use_mmr: bool = True,
                   filters: Optional[Dict] = None) -> List[Dict]:
        """
        Busca híbrida combinando BM25 e busca semântica

        Args:
            query: Consulta de busca
            limit: Número máximo de resultados
            use_semantic: Se True, usa busca híbrida. Se None, usa configuração padrão
            semantic_weight: Peso da similaridade semântica (sobrescreve padrão)
            use_mmr: Se True, usa MMR para diversidade
            filters: Filtros adicionais

        Returns:
            Lista de resultados ordenados por relevância
        """
        # Manter compatibilidade interna convertendo limit para top_k
        top_k = limit
        # Define se usar busca semântica
        use_semantic = use_semantic if use_semantic is not None else self.enable_semantic
        semantic_weight = semantic_weight if semantic_weight is not None else self.semantic_weight

        # Busca BM25 base
        bm25_results = []
        try:
            # Busca BM25 expandida (2x mais resultados para seleção MMR)
            bm25_results = search_code(self.base_indexer, query, limit=limit * 2, filters=filters)
        except Exception as e:
            import sys
            sys.stderr.write(f"❌ Erro na busca BM25: {e}\n")
            return []

        # Se busca semântica não habilitada, retorna apenas BM25
        if not use_semantic or not self.semantic_engine:
            return bm25_results[:limit]

        # Busca híbrida
        try:
            semantic_results = self.semantic_engine.hybrid_search(
                query=query,
                bm25_results=bm25_results,
                chunk_data=self.base_indexer.chunks,
                semantic_weight=semantic_weight,
                top_k=limit,
                use_mmr=use_mmr
            )
        except TypeError as te:
            if "unexpected keyword argument 'use_mmr'" in str(te):
                # fallback sem o parâmetro
                semantic_results = self.semantic_engine.hybrid_search(
                    query=query,
                    bm25_results=bm25_results,
                    chunk_data=self.base_indexer.chunks,
                    semantic_weight=semantic_weight,
                    top_k=limit
                )
            else:
                print(f"⚠️ Erro na busca semântica, usando apenas BM25: {te}")
                return bm25_results
        except Exception as e:
            print(f"⚠️ Erro na busca semântica, usando apenas BM25: {e}")
            return bm25_results

        return semantic_results

    def build_context_pack(self,
                          query: str,
                          budget_tokens: int = 3000,
                          limit: int = 10,
                          strategy: str = "mmr",
                          use_semantic: Optional[bool] = None) -> Dict:
        """
        Constrói pacote de contexto otimizado

        Args:
            query: Consulta de busca
            budget_tokens: Orçamento máximo de tokens
            limit: Número máximo de chunks
            strategy: Estratégia de seleção ("mmr" ou "topk")
            use_semantic: Se usar busca semântica

        Returns:
            Pacote de contexto formatado
        """
        # Busca chunks relevantes
        search_results = self.search_code(
            query=query,
            limit=limit * 3,  # Busca mais para melhor seleção
            use_semantic=use_semantic
        )

        # Usa função de construção de contexto base integrada
        try:
            # Removido bloco de mock dos resultados para evitar suposições de tipo
            # e manter a construção de contexto baseada no indexador base.
            pack = build_context_pack(
                self.base_indexer,
                query=query,
                budget_tokens=budget_tokens,
                max_chunks=limit,
                strategy=strategy
            )

            # Adiciona informações sobre tipo de busca usada
            pack['search_type'] = 'hybrid' if (use_semantic and self.enable_semantic) else 'bm25'
            pack['semantic_enabled'] = self.enable_semantic
            pack['auto_indexing_enabled'] = self.enable_auto_indexing

            return pack

        except Exception as e:
            import logging
            logging.getLogger(__name__).info(f"❌ Erro ao construir contexto: {e}")
            return {"query": query, "total_tokens": 0, "chunks": [], "error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do indexador"""
        try:
            index_size_mb = sum(len(json.dumps(c)) for c in self.base_indexer.chunks.values()) / (1024 * 1024)
        except Exception:
            index_size_mb = 0.0
        # Tentar obter last_updated do indexador base, se existir
        last_updated = getattr(self.base_indexer, "last_updated", None)
        return {
            "total_chunks": len(self.base_indexer.chunks),
            "total_files": len(set(c["file_path"] for c in self.base_indexer.chunks.values())),
            "index_size_mb": round(index_size_mb, 3),
            "last_updated": last_updated,
            "semantic_enabled": self.enable_semantic,
            "auto_indexing_enabled": self.enable_auto_indexing,
            "has_enhanced_features": HAS_ENHANCED_FEATURES
        }

    def start_auto_indexing(self) -> bool:
        """Inicia o file watcher para auto-indexação"""
        if not self.enable_auto_indexing or not self.file_watcher:
            return False
        # Evita tentar iniciar novamente se já estiver rodando
        try:
            if hasattr(self.file_watcher, 'is_running') and self.file_watcher.is_running:
                return True
        except Exception:
            pass
        try:
            self.file_watcher.start()
            return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).info(f"❌ Erro ao iniciar auto-indexação: {e}")
            return False

    def stop_auto_indexing(self) -> bool:
        """Para o file watcher"""
        if not self.file_watcher:
            return False
        try:
            self.file_watcher.stop()
            return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).info(f"❌ Erro ao parar auto-indexação: {e}")
            return False

    def embed_text(self, text: str):
        """
        Retorna vetor de embedding (list[float]) para o texto.
        Se não houver modelo carregado, retorna None.
        """
        fn = None
        if self.semantic_engine and hasattr(self.semantic_engine, "embed_text"):
            fn = getattr(self.semantic_engine, "embed_text")
        elif hasattr(self, "_embed_fn") and callable(getattr(self, "_embed_fn")):
            fn = getattr(self, "_embed_fn")
        elif hasattr(self, "embed") and callable(getattr(self, "embed")):
            fn = getattr(self, "embed")
        if fn is None:
            return None
        try:
            return fn(text)
        except Exception:
            return None

# ========== FUNÇÕES PÚBLICAS PARA COMPATIBILIDADE ==========

def enhanced_index_repo_paths(
    indexer: EnhancedCodeIndexer,
    paths: List[str],
    recursive: bool = True,
    include_globs: List[str] = None,
    exclude_globs: List[str] = None,
    enable_semantic: bool = True  # Adicionado para compatibilidade com o servidor
) -> Dict[str,int]:
    """Wrapper para compatibilidade com API antiga"""
    result = indexer.index_files(
        paths=paths,
        recursive=recursive,
        include_globs=include_globs,
        exclude_globs=exclude_globs
    )
    # Atualizar contadores após indexação bem-sucedida
    try:
        indexer._total_files = result.get("files_indexed", 0)
        import time
        indexer._last_updated_ts = time.time()
    except Exception:
        pass
    return result

def enhanced_search_code(
    indexer: EnhancedCodeIndexer,
    query: str,
    limit: int = 30,
    filters: Optional[Dict] = None,
    semantic_weight: float = None,
    use_mmr: bool = True
) -> List[Dict]:
    """Wrapper para compatibilidade com API antiga"""
    # Os parâmetros semantic_weight e use_mmr são mantidos para compatibilidade
    # mas podem não ser usados dependendo da implementação do indexer
    return indexer.search_code(query=query, limit=limit, filters=filters, semantic_weight=semantic_weight, use_mmr=use_mmr)

def enhanced_build_context_pack(
    indexer: EnhancedCodeIndexer,
    query: str,
    budget_tokens: int = 3000,
    max_chunks: int = 10,
    strategy: str = "mmr"
) -> Dict:
    """Wrapper para compatibilidade com API antiga"""
    return indexer.build_context_pack(
        query=query,
        budget_tokens=budget_tokens,
        limit=max_chunks,
        strategy=strategy
    )

import logging
logging.basicConfig(level=logging.INFO)

# Alias para compatibilidade com código existente
CodeIndexer = BaseCodeIndexer