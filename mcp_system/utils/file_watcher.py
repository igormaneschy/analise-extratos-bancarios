# src/utils/file_watcher.py
"""
Sistema de monitoramento de arquivos para auto-indexação
Detecta mudanças e reindexar automaticamente arquivos modificados
"""

from __future__ import annotations
import os
import time
import threading
from pathlib import Path
from typing import Set, Callable, Dict, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import hashlib

import sys

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    Observer = None
    FileSystemEventHandler = None

@dataclass
class IndexingTask:
    file_path: Path
    action: str  # 'created', 'modified', 'deleted'
    timestamp: float

class FileWatcher:
    """
    Sistema de monitoramento de arquivos que detecta mudanças
    e agenda reindexação automática
    """
    
    def __init__(self, 
                 watch_path: str = ".",
                 indexer_callback: Optional[Callable] = None,
                 debounce_seconds: float = 2.0,
                 include_extensions: Optional[Set[str]] = None):
        self.watch_path = Path(watch_path).resolve()
        self.indexer_callback = indexer_callback
        self.debounce_seconds = debounce_seconds
        self.include_extensions = include_extensions or {
            '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rb', '.php',
            '.c', '.cpp', '.h', '.hpp', '.cs', '.rs', '.swift', '.kt'
        }
        
        self.observer = None
        self.event_handler = None
        self.is_running = False
        
        # Sistema de debouncing
        self.pending_tasks: Dict[str, IndexingTask] = {}
        self.task_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="FileWatcher")
        self.debounce_timer = None
        
        # Estatísticas
        self.stats = {
            'files_monitored': 0,
            'events_processed': 0,
            'last_indexing': None,
            'errors': 0
        }
        
        if not HAS_WATCHDOG:
            print("⚠️  watchdog não encontrado. Auto-indexação desabilitada.", file=sys.stderr)
    
    def _should_process_file(self, file_path: Path) -> bool:
        """Verifica se arquivo deve ser processado"""
        if not file_path.is_file():
            return False
            
        # Verifica extensão
        if file_path.suffix not in self.include_extensions:
            return False
        
        # Ignora arquivos em diretórios específicos
        ignore_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'dist', 'build'}
        if any(part in ignore_dirs for part in file_path.parts):
            return False
            
        # Ignora arquivos temporários
        if file_path.name.startswith('.') and file_path.suffix in {'.tmp', '.swp', '.bak'}:
            return False
            
        return True
    
    def _add_indexing_task(self, file_path: Path, action: str):
        """Adiciona tarefa de indexação com debouncing"""
        if not self._should_process_file(file_path):
            return
            
        task = IndexingTask(
            file_path=file_path,
            action=action,
            timestamp=time.time()
        )
        
        # Usa caminho absoluto como chave para debouncing
        key = str(file_path.resolve())
        self.pending_tasks[key] = task
        
        # Agenda processamento com debounce
        self._schedule_processing()
    
    def _schedule_processing(self):
        """Agenda processamento das tarefas pendentes com debounce"""
        if self.debounce_timer:
            self.debounce_timer.cancel()
        
        self.debounce_timer = threading.Timer(
            self.debounce_seconds,
            self._process_pending_tasks
        )
        self.debounce_timer.daemon = True
        self.debounce_timer.start()
    
    def _process_pending_tasks(self):
        """Processa todas as tarefas pendentes"""
        if not self.pending_tasks:
            return
            
        # Agrupa tarefas por ação
        tasks_by_action = {'created': [], 'modified': [], 'deleted': []}
        
        for task in self.pending_tasks.values():
            if task.action in tasks_by_action:
                tasks_by_action[task.action].append(task.file_path)
        
        # Processa tarefas
        try:
            self._execute_indexing_tasks(tasks_by_action)
            self.stats['last_indexing'] = time.time()
        except Exception as e:
            print(f"❌ Erro no processamento de tarefas: {e}")
            self.stats['errors'] += 1
        finally:
            self.pending_tasks.clear()
    
    def _execute_indexing_tasks(self, tasks_by_action: Dict[str, list]):
        """Executa as tarefas de indexação agrupadas"""
        if not self.indexer_callback:
            return

        total_files = sum(len(files) for files in tasks_by_action.values())
        if total_files == 0:
            return

        print(f"🔄 Processando {total_files} arquivo(s) modificado(s)...", file=sys.stderr)

        # Processa arquivos criados/modificados
        files_to_index = tasks_by_action['created'] + tasks_by_action['modified']
        if files_to_index:
            try:
                result = self.indexer_callback(files_to_index)
                indexed_count = result.get('files_indexed', 0) if isinstance(result, dict) else len(files_to_index)
                print(f"✅ {indexed_count} arquivo(s) indexado(s)", file=sys.stderr)
                self.stats['events_processed'] += indexed_count
            except Exception as e:
                print(f"❌ Erro ao indexar arquivos: {e}", file=sys.stderr)
                self.stats['errors'] += 1

        # TODO: Implementar remoção de chunks para arquivos deletados
        deleted_files = tasks_by_action['deleted']
        if deleted_files:
            print(f"ℹ️  {len(deleted_files)} arquivo(s) deletado(s) (remoção de índice não implementada)", file=sys.stderr)

class WatchdogHandler(FileSystemEventHandler):
    """Handler para eventos do watchdog"""
    
    def __init__(self, watcher: FileWatcher):
        self.watcher = watcher
        super().__init__()
    
    def on_created(self, event):
        if not event.is_directory:
            self.watcher._add_indexing_task(Path(event.src_path), 'created')
    
    def on_modified(self, event):
        if not event.is_directory:
            self.watcher._add_indexing_task(Path(event.src_path), 'modified')
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.watcher._add_indexing_task(Path(event.src_path), 'deleted')

class FileWatcher(FileWatcher):
    """Extensão da classe FileWatcher com watchdog"""
    
    def start(self) -> bool:
        """Inicia o monitoramento de arquivos"""
        if not HAS_WATCHDOG:
            print("❌ watchdog não disponível. Auto-indexação não pode ser iniciada.", file=sys.stderr)
            return False

        if self.is_running:
            print("⚠️  File watcher já está rodando", file=sys.stderr)
            return True
            
        try:
            self.event_handler = WatchdogHandler(self)
            self.observer = Observer()
            self.observer.schedule(
                self.event_handler, 
                str(self.watch_path), 
                recursive=True
            )
            self.observer.start()
            self.is_running = True
            
            # Conta arquivos monitorados
            self._count_monitored_files()
            
            print(f"✅ File watcher iniciado em: {self.watch_path}", file=sys.stderr)
            print(f"📊 Monitorando {self.stats['files_monitored']} arquivos", file=sys.stderr)
            return True

        except Exception as e:
            print(f"❌ Erro ao iniciar file watcher: {e}", file=sys.stderr)
            return False
    
    def stop(self):
        """Para o monitoramento de arquivos"""
        if not self.is_running:
            return
            
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
            
        if self.debounce_timer:
            self.debounce_timer.cancel()
            
        self.task_executor.shutdown(wait=True)
        self.is_running = False
        
        print("✅ File watcher parado", file=sys.stderr)
    
    def _count_monitored_files(self):
        """Conta arquivos que estão sendo monitorados"""
        count = 0
        try:
            for file_path in self.watch_path.rglob("*"):
                if self._should_process_file(file_path):
                    count += 1
            self.stats['files_monitored'] = count
        except Exception as e:
            print(f"⚠️  Erro ao contar arquivos: {e}", file=sys.stderr)

    def get_stats(self) -> Dict:
        """Retorna estatísticas do file watcher"""
        return {
            'enabled': HAS_WATCHDOG,
            'running': self.is_running,
            'watch_path': str(self.watch_path),
            'debounce_seconds': self.debounce_seconds,
            'pending_tasks': len(self.pending_tasks),
            **self.stats
        }

class SimpleFileWatcher:
    """
    Fallback simples para quando watchdog não está disponível
    Usa polling para detectar mudanças
    """
    
    def __init__(self, 
                 watch_path: str = ".",
                 indexer_callback: Optional[Callable] = None,
                 poll_interval: float = 30.0,
                 include_extensions: Optional[Set[str]] = None):
        self.watch_path = Path(watch_path).resolve()
        self.indexer_callback = indexer_callback
        self.poll_interval = poll_interval
        self.include_extensions = include_extensions or {
            '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rb', '.php',
            '.c', '.cpp', '.h', '.hpp', '.cs', '.rs', '.swift', '.kt'
        }
        
        self.file_hashes: Dict[str, str] = {}
        self.is_running = False
        self.poll_thread = None
        
        self.stats = {
            'files_monitored': 0,
            'polls_completed': 0,
            'changes_detected': 0,
            'last_poll': None
        }
    
    def _get_file_hash(self, file_path: Path) -> Optional[str]:
        """Calcula hash do arquivo para detectar mudanças"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None
    
    def _scan_for_changes(self):
        """Escaneia diretório em busca de mudanças"""
        changed_files = []
        current_files = {}
        
        # Escaneia todos os arquivos relevantes
        for file_path in self.watch_path.rglob("*"):
            if not file_path.is_file():
                continue
                
            if file_path.suffix not in self.include_extensions:
                continue
                
            str_path = str(file_path)
            file_hash = self._get_file_hash(file_path)
            
            if file_hash:
                current_files[str_path] = file_hash
                
                # Verifica se arquivo mudou
                if str_path in self.file_hashes:
                    if self.file_hashes[str_path] != file_hash:
                        changed_files.append(file_path)
                else:
                    # Arquivo novo
                    changed_files.append(file_path)
        
        # Atualiza cache de hashes
        self.file_hashes = current_files
        self.stats['files_monitored'] = len(current_files)
        
        return changed_files
    
    def _poll_loop(self):
        """Loop principal de polling"""
        while self.is_running:
            try:
                changed_files = self._scan_for_changes()
                self.stats['polls_completed'] += 1
                self.stats['last_poll'] = time.time()
                
                if changed_files:
                    self.stats['changes_detected'] += len(changed_files)
                    print(f"🔄 Detectadas mudanças em {len(changed_files)} arquivo(s)", file=sys.stderr)

                    if self.indexer_callback:
                        try:
                            result = self.indexer_callback(changed_files)
                            indexed_count = result.get('files_indexed', 0) if isinstance(result, dict) else len(changed_files)
                            print(f"✅ {indexed_count} arquivo(s) reindexado(s)", file=sys.stderr)
                        except Exception as e:
                            print(f"❌ Erro ao reindexar: {e}", file=sys.stderr)

            except Exception as e:
                print(f"❌ Erro no polling: {e}", file=sys.stderr)

            # Aguarda próximo poll
            time.sleep(self.poll_interval)
    
    def start(self) -> bool:
        """Inicia o polling de arquivos"""
        if self.is_running:
            print("⚠️  Simple file watcher já está rodando")
            return True
            
        # Scan inicial
        self._scan_for_changes()
        
        self.is_running = True
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()
        
        print(f"✅ Simple file watcher iniciado (polling a cada {self.poll_interval}s)")
        print(f"📊 Monitorando {self.stats['files_monitored']} arquivos")
        return True
    
    def stop(self):
        """Para o polling"""
        self.is_running = False
        if self.poll_thread and self.poll_thread.is_alive():
            self.poll_thread.join(timeout=5)
        print("✅ Simple file watcher parado")
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do simple file watcher"""
        return {
            'enabled': True,
            'running': self.is_running,
            'watch_path': str(self.watch_path),
            'poll_interval': self.poll_interval,
            'type': 'simple_polling',
            **self.stats
        }

def create_file_watcher(watch_path: str = ".", **kwargs) -> FileWatcher | SimpleFileWatcher:
    """
    Factory function que cria o melhor file watcher disponível
    """
    if HAS_WATCHDOG:
        return FileWatcher(watch_path=watch_path, **kwargs)
    else:
        print("📝 Usando fallback SimpleFileWatcher (instale watchdog para melhor performance)", file=sys.stderr)
        return SimpleFileWatcher(watch_path=watch_path, **kwargs)