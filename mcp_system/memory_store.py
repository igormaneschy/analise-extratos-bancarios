"""
Minimal MemoryStore shim for mcp_system.
Provides:
- MemoryStore class with simple sqlite persistence for session summaries
- get_cache(name) returning a tiny in-memory Deterministic cache object
- TTL_SEARCH_S and TTL_EMB_DAYS constants

This shim is intentionally small and dependency-free; it is suitable for development and CI.
"""
from __future__ import annotations
import sqlite3
import threading
import time
import os
from pathlib import Path
from typing import Optional, Any, Dict
import json
from collections import OrderedDict

# TTL defaults
TTL_SEARCH_S = 120
TTL_EMB_DAYS = 14
TTL_META_DAYS = 30
TTL_CONTEXT_DAYS = 7

# helper: convert days to seconds
def _days_to_seconds(days: int) -> int:
    return days * 24 * 60 * 60

# default ttls per namespace (in seconds)
DEFAULT_TTLS: Dict[str, int] = {
    "search": TTL_SEARCH_S,
    "embeddings": _days_to_seconds(TTL_EMB_DAYS),
    "metadata": _days_to_seconds(TTL_META_DAYS),
    "context": _days_to_seconds(TTL_CONTEXT_DAYS),
}

# Simple thread-safe sqlite-backed MemoryStore
class MemoryStore:
    def __init__(self, db_path: Optional[str] = None, project_root: Optional[Path] = None, root: Optional[Path] = None):
        # determine db path
        if db_path:
            self.db_path = str(db_path)
        else:
            # Default to a package-local directory under mcp_system to keep memory self-contained.
            # Allow overriding with MCP_DATA_DIR env var for advanced setups.
            package_dir = Path(__file__).resolve().parent
            base = Path(os.environ.get("MCP_DATA_DIR", str(package_dir / ".mcp_memory")))
            base.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base / "session_store.sqlite3")
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS session_summaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project TEXT,
                        scope TEXT,
                        title TEXT,
                        details TEXT,
                        created_at REAL
                    )
                    """
                )
                # llm_usage: records per-LLM usage events (ts = unix epoch int)
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS llm_usage (
                        ts INTEGER,
                        model TEXT,
                        calls INTEGER,
                        tokens REAL
                    )
                    """
                )
                conn.commit()
            finally:
                conn.close()
    def add_session_summary(self, project: str, scope: str, title: str, details: str):
        """Insert a lightweight session summary into the DB."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO session_summaries (project, scope, title, details, created_at) VALUES (?,?,?,?,?)",
                    (project, scope, title, details, time.time()),
                )
                conn.commit()
            finally:
                conn.close()

    def record_llm_usage(self, model: str, tokens: float, calls: int = 1, ts: Optional[int] = None):
        """Record an LLM usage event in the llm_usage table.

        Parameters:
        - model: model name (string)
        - tokens: number of tokens (float)
        - calls: number of calls (int)
        - ts: unix epoch seconds (int). If None, now() is used.
        """
        if ts is None:
            ts = int(time.time())
        try:
            # Optional debug tracing: when MCP_LLM_DEBUG is truthy, write a small
            # debug record to a per-repo log file including stack trace so we can
            # attribute which code path invoked the recording. This is best-effort
            # and guarded to avoid impacting production runs.
            try:
                if os.getenv('MCP_LLM_DEBUG', '').lower() in ('1', 'true', 'yes'):
                    try:
                        import traceback as _tb
                        dbg_path = Path(os.environ.get('MCP_DATA_DIR', Path(__file__).resolve().parent / '.mcp_memory'))
                        dbg_path.mkdir(parents=True, exist_ok=True)
                        with open(dbg_path / 'llm_record_debug.log', 'a', encoding='utf-8') as _fh:
                            _fh.write(f"TS={int(ts)} MODEL={model!r} TOKENS={tokens} CALLS={calls}\n")
                            for ln in _tb.format_stack(limit=6):
                                _fh.write(ln)
                            _fh.write("---\n")
                    except Exception:
                        # swallow debug failures
                        pass
            except Exception:
                pass

            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO llm_usage (ts, model, calls, tokens) VALUES (?,?,?,?)",
                        (int(ts), str(model), int(calls), float(tokens)),
                    )
                    conn.commit()
                finally:
                    conn.close()
        except Exception:
            # best-effort: swallow to avoid impacting main flow
            return

    def get_llm_usage_agg(self, start_ts: Optional[int] = None, end_ts: Optional[int] = None) -> Dict[str, Dict[str, float]]:
        """Return aggregated LLM usage grouped by model.

        Returns a dict of the form:
          { model_name: { 'calls': int, 'tokens': float, 'pc_calls': float, 'pc_tokens': float } }

        start_ts/end_ts are unix epoch seconds. If None, they are unbounded on that side.
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                try:
                    cur = conn.cursor()
                    # Build where clause
                    params: list = []
                    where_clauses: list = []
                    if start_ts is not None:
                        where_clauses.append("ts >= ?")
                        params.append(int(start_ts))
                    if end_ts is not None:
                        where_clauses.append("ts <= ?")
                        params.append(int(end_ts))
                    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
                    q = f"SELECT model, SUM(calls) as calls, SUM(tokens) as tokens FROM llm_usage {where_sql} GROUP BY model"
                    cur.execute(q, params)
                    rows = cur.fetchall()
                    total_calls = 0
                    total_tokens = 0.0
                    out: Dict[str, Dict[str, float]] = {}
                    for r in rows:
                        model = r[0] or ""
                        calls = int(r[1] or 0)
                        tokens = float(r[2] or 0.0)
                        out[model] = {"calls": calls, "tokens": tokens}
                        total_calls += calls
                        total_tokens += tokens

                    # compute percentages
                    for model, stats in out.items():
                        stats["pc_calls"] = (stats["calls"] / total_calls * 100.0) if total_calls > 0 else 0.0
                        stats["pc_tokens"] = (stats["tokens"] / total_tokens * 100.0) if total_tokens > 0 else 0.0

                    return out
                finally:
                    conn.close()
        except Exception:
            return {}

    def recent_summaries(self, project: str, limit: int = 20):
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT project, scope, title, details, created_at FROM session_summaries WHERE project = ? ORDER BY created_at DESC LIMIT ?",
                    (project, limit),
                )
                rows = cur.fetchall()
                return [dict(project=r[0], scope=r[1], title=r[2], details=r[3], created_at=r[4]) for r in rows]
            finally:
                conn.close()


# Deterministic in-memory cache with normalization, LRU, persistence and basic stats
def _normalize_key(key: Any) -> str:
    """Normalize keys to a deterministic string representation.

    - If key is a string: lowercased.
    - Otherwise: JSON-dumped with sorted keys.

    This makes keys case-insensitive and order-insensitive for dict-like keys.
    """
    if isinstance(key, str):
        return key.lower()
    try:
        # use separators to keep representation compact and consistent
        return json.dumps(key, sort_keys=True, separators=(",", ":"))
    except Exception:
        # fallback to str()
        return str(key)


class DeterministicCache:
    """A small thread-safe in-memory cache with TTL, optional LRU size limit, optional disk persistence and simple metrics.

    Parameters:
    - namespace: optional name used to select default TTL
    - max_size: optional int to enable LRU eviction when number of keys exceeds max_size
    - persist_path: optional path to JSON file where cache entries will be stored/loaded
    """

    def __init__(self, namespace: Optional[str] = None, max_size: Optional[int] = None, persist_path: Optional[str] = None, default_ttl: Optional[int] = None):
        self._data: "OrderedDict[str, tuple[float, Any]]" = OrderedDict()
        self._lock = threading.Lock()
        # simple counters
        self._sets = 0
        self._gets = 0
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        # configuration
        self.namespace = namespace
        self.max_size = max_size
        self.persist_path = persist_path
        # default ttl in seconds for this cache (applied when set called with ttl=None)
        if default_ttl is None and namespace is not None:
            self.default_ttl = DEFAULT_TTLS.get(namespace)
        else:
            self.default_ttl = default_ttl
        # attempt to restore from disk if persistence enabled
        if self.persist_path:
            try:
                self._load_from_disk()
            except Exception:
                # ignore failures to keep shim robust
                pass

    def _persist_to_disk(self):
        if not self.persist_path:
            return
        try:
            dump: Dict[str, Any] = {}
            # only persist entries that are JSON-serializable
            with self._lock:
                for k, (expire, v) in self._data.items():
                    # skip expired
                    if time.time() > expire:
                        continue
                    try:
                        json.dumps(v)
                        dump[k] = (expire, v)
                    except Exception:
                        # skip non-serializable values
                        continue
            Path(self.persist_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.persist_path, "w", encoding="utf-8") as fh:
                json.dump(dump, fh, ensure_ascii=False)
        except Exception:
            # persist best-effort; swallow exceptions
            pass

    def _load_from_disk(self):
        p = Path(self.persist_path)
        if not p.exists():
            return
        try:
            with open(p, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            now = time.time()
            with self._lock:
                for k, (expire, v) in data.items():
                    # only load non-expired
                    if expire > now:
                        self._data[k] = (expire, v)
        except Exception:
            # ignore malformed files
            pass

    def _apply_default_ttl(self, ttl: Optional[int]) -> Optional[int]:
        if ttl is None and self.default_ttl is not None:
            return self.default_ttl
        return ttl

    def set(self, key: Any, value: Any, ttl: Optional[int] = None):
        ttl = self._apply_default_ttl(ttl)
        expire = time.time() + ttl if ttl is not None else float("inf")
        nkey = _normalize_key(key)
        with self._lock:
            # update / move to end for LRU semantics
            if nkey in self._data:
                try:
                    del self._data[nkey]
                except KeyError:
                    pass
            self._data[nkey] = (expire, value)
            self._data.move_to_end(nkey)
            self._sets += 1
            # evict if needed
            if self.max_size is not None and len(self._data) > self.max_size:
                # pop least-recently-used (first item)
                try:
                    popped_key, _ = self._data.popitem(last=False)
                    self._evictions += 1
                except Exception:
                    pass
        # persist asynchronously best-effort (synchronous here for simplicity)
        self._persist_to_disk()

    def get(self, key: Any, default: Any = None):
        nkey = _normalize_key(key)
        with self._lock:
            self._gets += 1
            v = self._data.get(nkey)
            if not v:
                self._misses += 1
                return default
            expire, val = v
            if time.time() > expire:
                try:
                    del self._data[nkey]
                except KeyError:
                    pass
                self._misses += 1
                return default
            # move to end to mark recent use
            try:
                self._data.move_to_end(nkey)
            except Exception:
                pass
            self._hits += 1
            return val

    def delete(self, key: Any):
        nkey = _normalize_key(key)
        with self._lock:
            try:
                del self._data[nkey]
            except KeyError:
                pass
        self._persist_to_disk()

    def clear(self):
        with self._lock:
            self._data.clear()
        self._persist_to_disk()

    def reset_metrics(self):
        """Reset internal counters (sets, gets, hits, misses, evictions) to zero."""
        with self._lock:
            prev = {"sets": self._sets, "gets": self._gets, "hits": self._hits, "misses": self._misses, "evictions": self._evictions}
            self._sets = 0
            self._gets = 0
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            return prev

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "size": len(self._data),
                "sets": self._sets,
                "gets": self._gets,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "max_size": self.max_size,
                "namespace": self.namespace,
                "persist_path": self.persist_path,
                "default_ttl": self.default_ttl,
                # don't expose raw keys by default - just list count and a sample
                "sample_keys": list(self._data.keys())[:10],
            }


# factory
_caches: Dict[str, DeterministicCache] = {}

def get_cache(name: str, *, max_size: Optional[int] = None, persist_path: Optional[str] = None, default_ttl: Optional[int] = None) -> DeterministicCache:
    """Return a named DeterministicCache instance (created on demand).

    Optional parameters allow enabling LRU (max_size) and simple disk persistence (persist_path).
    If default_ttl is not provided, a namespace-based default is applied when available.
    """
    global _caches
    if name not in _caches:
        # apply default TTL for known namespaces
        dt = default_ttl if default_ttl is not None else DEFAULT_TTLS.get(name)
        _caches[name] = DeterministicCache(namespace=name, max_size=max_size, persist_path=persist_path, default_ttl=dt)
        return _caches[name]

    # If already exists, gently update config if new values are provided
    cache = _caches[name]
    try:
        if max_size is not None and (cache.max_size is None or cache.max_size < max_size):
            cache.max_size = max_size
        if persist_path and not cache.persist_path:
            cache.persist_path = persist_path
            try:
                cache._load_from_disk()
            except Exception:
                pass
        if default_ttl is not None:
            cache.default_ttl = default_ttl
        elif cache.default_ttl is None and name in DEFAULT_TTLS:
            cache.default_ttl = DEFAULT_TTLS.get(name)
    except Exception:
        pass
    return cache


def get_all_cache_stats() -> Dict[str, Dict[str, Any]]:
    """Return stats for all named caches as a dict keyed by namespace."""
    out: Dict[str, Dict[str, Any]] = {}
    for name, cache in _caches.items():
        try:
            out[name] = cache.stats()
        except Exception as e:
            out[name] = {"error": str(e)}
    return out


# Expose a convenience function to create the MemoryStore from env/config
def create_default_store() -> MemoryStore:
    # Default to a package-local directory under the mcp_system package to keep the memory DB self-contained.
    package_dir = Path(__file__).resolve().parent
    data_dir = Path(os.environ.get("MCP_DATA_DIR", str(package_dir / ".mcp_memory")))
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = str(data_dir / "session_store.sqlite3")
    return MemoryStore(db_path=db_path)


def get_memory_store_stats(store: Optional[MemoryStore] = None) -> Dict[str, Any]:
    """Return basic stats about the memory store (session summaries count).

    If a store instance is not provided, create a temporary default store.
    Errors are caught and returned as an 'error' field.
    """
    try:
        s = store or create_default_store()
        with s._lock:
            conn = sqlite3.connect(s.db_path, check_same_thread=False)
            try:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(1) FROM session_summaries")
                row = cur.fetchone()
                count = int(row[0]) if row and row[0] is not None else 0
                return {"session_summaries_count": count}
            finally:
                conn.close()
    except Exception as e:
        return {"error": str(e)}
