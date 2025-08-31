# utils/file_watcher.py
# File watcher simples com fallback por polling
from __future__ import annotations
import os
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

# Tipo do callback: recebe lista de Paths modificados/criados
WatcherCallback = Callable[[List[Path]], Dict[str, int] | None]

# Filtros essenciais para ignorar artefatos internos e diretórios pesados
ESSENTIAL_FILTERS = (
    "/.mcp_index/",
    "/.mcp_memory/",
    "/.emb_cache/",
    "/.git/",
    "/.venv/",
    "/__pycache__/",
    "/node_modules/",
    "/dist/",
    "/build/",
)


class SimpleFileWatcher:
    """
    Watcher por polling que varre recursivamente um diretório e detecta novos/alterados.
    - Foco em robustez e zero dependências externas
    - Detecção de deleção é ignorada (indexador deve tratar tombstones se necessário)
    """

    def __init__(self, watch_path: str, indexer_callback: WatcherCallback, debounce_seconds: float = 2.0) -> None:
        self.watch_path = Path(watch_path)
        self.indexer_callback = indexer_callback
        self.debounce_seconds = max(0.5, float(debounce_seconds))
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._mtimes: Dict[str, float] = {}
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="SimpleFileWatcher", daemon=True)
        self._thread.start()
        self._is_running = True

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        self._is_running = False

    def _iter_files(self) -> List[Path]:
        files: List[Path] = []
        root = self.watch_path
        if not root.exists():
            return files
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune diretórios indesejados para performance
            prune = {'.git', '.mcp_index', '.mcp_memory', '.emb_cache', '.venv', '__pycache__', 'node_modules', 'dist', 'build'}
            dirnames[:] = [d for d in dirnames if d not in prune and not d.startswith('.')]
            for fn in filenames:
                p = Path(dirpath) / fn
                sp = str(p).replace("\\", "/")
                # Ignorar arquivos dentro de artefatos internos
                if "/.mcp_index/" in sp or "/.mcp_memory/" in sp or "/.emb_cache/" in sp:
                    continue
                files.append(p)
        return files

    def _loop(self) -> None:
        try:
            while not self._stop_event.is_set():
                changed: List[Path] = []
                for f in self._iter_files():
                    try:
                        mtime = f.stat().st_mtime
                    except Exception:
                        continue
                    key = str(f)
                    old = self._mtimes.get(key)
                    if old is None or mtime > old:
                        self._mtimes[key] = mtime
                        changed.append(f)
                if changed:
                    try:
                        self.indexer_callback(changed)
                    except Exception:
                        # Não interrompe o watcher por erro do callback
                        pass
                # Limpa entradas para arquivos que sumiram do FS
                to_delete = [k for k in list(self._mtimes.keys()) if not Path(k).exists()]
                for k in to_delete:
                    self._mtimes.pop(k, None)
                time.sleep(self.debounce_seconds)
        finally:
            self._is_running = False


def _contains_filtered_path(path_str: str) -> bool:
    sp = path_str.replace("\\", "/")
    return any(f in sp for f in ESSENTIAL_FILTERS)


def create_file_watcher(watch_path: str, indexer_callback: WatcherCallback, debounce_seconds: float = 2.0):
    """
    Factory de watcher: tenta watchdog se disponível; senão, usa SimpleFileWatcher.
    """
    try:
        from watchdog.observers import Observer  # type: ignore
        from watchdog.events import FileSystemEventHandler  # type: ignore

        class _Handler(FileSystemEventHandler):
            def __init__(self, cb: WatcherCallback) -> None:
                self.cb = cb
                self._pending: Dict[str, float] = {}
                self._lock = threading.Lock()

            def on_any_event(self, event):  # type: ignore
                if event.is_directory:
                    return
                # Ignora eventos dentro de artefatos internos do MCP
                sp = str(event.src_path).replace("\\", "/")
                if _contains_filtered_path(sp):
                    return
                with self._lock:
                    self._pending[event.src_path] = time.time()

            def flush(self):
                with self._lock:
                    if not self._pending:
                        return
                    files = [Path(p) for p in self._pending.keys()]
                    self._pending.clear()
                try:
                    self.cb(files)
                except Exception:
                    pass

        class WatchdogWrapper:
            def __init__(self, path: str, cb: WatcherCallback, debounce: float) -> None:
                self.path = path
                self.cb = cb
                self.debounce = debounce
                self.observer = Observer()
                self.handler = _Handler(cb)
                self._thread: Optional[threading.Thread] = None
                self._stop = threading.Event()
                self._is_running = False

            @property
            def is_running(self) -> bool:
                return self._is_running

            def start(self):
                self.observer.schedule(self.handler, self.path, recursive=True)
                self.observer.start()
                self._stop.clear()
                self._thread = threading.Thread(target=self._loop, daemon=True)
                self._thread.start()
                self._is_running = True

            def _loop(self):
                try:
                    while not self._stop.is_set():
                        time.sleep(self.debounce)
                        self.handler.flush()
                finally:
                    self._is_running = False

            def stop(self):
                self._stop.set()
                try:
                    self.observer.stop()
                    self.observer.join(timeout=3)
                except Exception:
                    pass

        return WatchdogWrapper(watch_path, indexer_callback, debounce_seconds)
    except Exception:
        return SimpleFileWatcher(watch_path, indexer_callback, debounce_seconds)

