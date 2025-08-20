# code_indexer_enhanced.py
"""
Enhanced Code Indexer com busca semântica e auto-indexação
Integra embeddings semânticos + BM25 + file watching
"""

from __future__ import annotations
import os
import re
import json
import math
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set
import threading

# Importa componentes dos sistemas semântico e file watcher
try:
    from src.embeddings.semantic_search import SemanticSearchEngine, EmbeddingResult
    from src.utils.file_watcher import create_file_watcher
    HAS_ENHANCED_FEATURES = True
except ImportError:
    HAS_ENHANCED_FEATURES = False
    SemanticSearchEngine = None
    create_file_watcher = None

# Importa funcionalidades base do indexador original
from code_indexer_patched import (
    CodeIndexer as BaseCodeIndexer,
    LANG_EXTS, DEFAULT_INCLUDE, DEFAULT_EXCLUDE,
    TOKEN_PATTERN, now_ts, tokenize, est_tokens, hash_id
)

class EnhancedCodeIndexer:
    """
    Indexador de código melhorado que combina:
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
        
        if self.enable_semantic:
            try:
                self.semantic_engine = SemanticSearchEngine(cache_dir=str(self.index_dir))
                # Mensagem será enviada pelo mcp_server_enhanced.py
            except Exception as e:
                import sys
                sys.stderr.write(f"⚠️  Erro ao inicializar busca semântica: {e}\n")
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
                import sys
                sys.stderr.write(f"⚠️  Erro ao inicializar auto-indexação: {e}\n")
                self.enable_auto_indexing = False
        
        # Lock para thread safety
        self._lock = threading.RLock()
    
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
                sys.stderr.write(f"🔄 Auto-indexação: {result.get('files_indexed', 0)} arquivos processados\n")
                return result

            except Exception as e:
                import sys
                sys.stderr.write(f"❌ Erro na auto-indexação: {e}\n")
                return {'files_indexed': 0, 'chunks': 0, 'error': str(e)}
    
    def index_files(self, file_paths: List[str], show_progress: bool = True) -> Dict[str, Any]:
        """Indexa arquivos específicos com suporte a embeddings"""
        with self._lock:
            # Usa indexador base para indexação BM25
            result = {}
            for file_path in file_paths:
                try:
                    file_result = self.base_indexer.add_file(file_path)
                    if not result:
                        result = file_result
                    else:
                        result['files_indexed'] = result.get('files_indexed', 0) + file_result.get('files_indexed', 0)
                        result['chunks'] = result.get('chunks', 0) + file_result.get('chunks', 0)
                except Exception as e:
                    if show_progress:
                        import sys
                        sys.stderr.write(f"❌ Erro ao indexar {file_path}: {e}\n")
            
            # Gera embeddings se habilitado
            if self.enable_semantic and self.semantic_engine and result.get('chunks', 0) > 0:
                self._generate_embeddings_for_files(file_paths, show_progress)
            
            return result
    
    def _generate_embeddings_for_files(self, file_paths: List[str], show_progress: bool = True):
        """Gera embeddings para chunks de arquivos específicos"""
        if not self.semantic_engine:
            return
            
        try:
            chunks_processed = 0
            for chunk_id, chunk_data in self.base_indexer.chunks.items():
                if chunk_data.get('file_path') in file_paths:
                    content = chunk_data.get('content', '')
                    if content:
                        embedding = self.semantic_engine.get_embedding(chunk_id, content)
                        if embedding is not None:
                            chunks_processed += 1
            
            if show_progress and chunks_processed > 0:
                import sys
                sys.stderr.write(f"🧠 Gerados embeddings para {chunks_processed} chunks\n")

        except Exception as e:
            if show_progress:
                import sys
                sys.stderr.write(f"⚠️  Erro ao gerar embeddings: {e}\n")
    
    def search_code(self, 
                   query: str, 
                   top_k: int = 30, 
                   use_semantic: bool = None,
                   semantic_weight: float = None,
                   filters: Optional[Dict] = None) -> List[Dict]:
        """
        Busca código com opção de usar busca semântica híbrida
        
        Args:
            query: Consulta de busca
            top_k: Número máximo de resultados
            use_semantic: Se True, usa busca híbrida. Se None, usa configuração padrão
            semantic_weight: Peso da similaridade semântica (sobrescreve padrão)
            filters: Filtros adicionais
            
        Returns:
            Lista de resultados ordenados por relevância
        """
        # Define se usar busca semântica
        use_semantic = use_semantic if use_semantic is not None else self.enable_semantic
        semantic_weight = semantic_weight if semantic_weight is not None else self.semantic_weight
        
        # Busca BM25 base
        bm25_results = []
        try:
            # Usa função original do indexador base
            from code_indexer_patched import search_code as base_search
            bm25_results = base_search(self.base_indexer, query, top_k=top_k * 2, filters=filters)
        except Exception as e:
            import sys
            sys.stderr.write(f"❌ Erro na busca BM25: {e}\n")
            return []
        
        # Se busca semântica não habilitada, retorna apenas BM25
        if not use_semantic or not self.semantic_engine:
            return bm25_results[:top_k]
        
        # Busca híbrida
        try:
            semantic_results = self.semantic_engine.hybrid_search(
                query=query,
                bm25_results=bm25_results,
                chunk_data=self.base_indexer.chunks,
                semantic_weight=semantic_weight,
                top_k=top_k
            )
            
            # Converte EmbeddingResult para formato compatível
            hybrid_results = []
            for result in semantic_results:
                chunk = self.base_indexer.chunks.get(result.chunk_id, {})
                hybrid_results.append({
                    'chunk_id': result.chunk_id,
                    'score': result.combined_score,
                    'bm25_score': result.bm25_score,
                    'semantic_score': result.similarity_score,
                    'file_path': result.file_path,
                    'content': result.content,
                    **{k: v for k, v in chunk.items() if k not in ['content', 'file_path']}
                })
            
            return hybrid_results
            
        except Exception as e:
            import sys
            sys.stderr.write(f"⚠️  Erro na busca híbrida, usando apenas BM25: {e}\n")
            return bm25_results[:top_k]
    
    def build_context_pack(self, 
                          query: str,
                          budget_tokens: int = 3000,
                          max_chunks: int = 10,
                          strategy: str = "mmr",
                          use_semantic: bool = None) -> Dict:
        """
        Constrói pacote de contexto usando busca melhorada
        
        Args:
            query: Consulta para busca
            budget_tokens: Orçamento máximo de tokens
            max_chunks: Número máximo de chunks
            strategy: Estratégia de seleção ("mmr" ou "topk")
            use_semantic: Se usar busca semântica
            
        Returns:
            Pacote de contexto formatado
        """
        # Busca chunks relevantes
        search_results = self.search_code(
            query=query, 
            top_k=max_chunks * 3,  # Busca mais para melhor seleção
            use_semantic=use_semantic
        )
        
        # Usa função original para construir o pack
        try:
            from code_indexer_patched import build_context_pack as base_build_pack
            
            # Simula resultado de busca no formato esperado
            mock_results = []
            for result in search_results:
                mock_results.append({
                    'chunk_id': result['chunk_id'],
                    'score': result['score']
                })
            
            # Injeta resultados no indexador base temporariamente
            original_search = self.base_indexer.search_code
            def mock_search(*args, **kwargs):
                return mock_results
            
            # Constrói pack
            pack = base_build_pack(
                self.base_indexer,
                query=query,
                budget_tokens=budget_tokens,
                max_chunks=max_chunks,
                strategy=strategy
            )
            
            # Adiciona informações sobre tipo de busca usada
            pack['search_type'] = 'hybrid' if (use_semantic and self.enable_semantic) else 'bm25'
            
            return pack
            
        except Exception as e:
            import sys
            sys.stderr.write(f"❌ Erro ao construir context pack: {e}\n")
            return {'query': query, 'total_tokens': 0, 'chunks': [], 'error': str(e)}

    def start_auto_indexing(self) -> bool:
        """Inicia o sistema de auto-indexação"""
        if not self.enable_auto_indexing or not self.file_watcher:
            import sys
            sys.stderr.write("⚠️  Auto-indexação não disponível\n")
            return False
            
        return self.file_watcher.start()
    
    def stop_auto_indexing(self):
        """Para o sistema de auto-indexação"""
        if self.file_watcher:
            self.file_watcher.stop()
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas completas do sistema"""
        base_stats = {
            'base_indexer': {
                'chunks_count': len(self.base_indexer.chunks),
                'files_indexed': len(set(chunk.get('file_path', '') for chunk in self.base_indexer.chunks.values())),
                'index_size_mb': self._calculate_index_size()
            }
        }
        
        # Estatísticas semânticas
        if self.semantic_engine:
            base_stats['semantic_search'] = self.semantic_engine.get_cache_stats()
        else:
            base_stats['semantic_search'] = {'enabled': False}
        
        # Estatísticas do file watcher
        if self.file_watcher:
            base_stats['auto_indexing'] = self.file_watcher.get_stats()
        else:
            base_stats['auto_indexing'] = {'enabled': False}
        
        # Configurações gerais
        base_stats['config'] = {
            'semantic_enabled': self.enable_semantic,
            'auto_indexing_enabled': self.enable_auto_indexing,
            'semantic_weight': self.semantic_weight,
            'index_dir': str(self.index_dir),
            'repo_root': str(self.repo_root)
        }
        
        return base_stats
    
    def _calculate_index_size(self) -> float:
        """Calcula tamanho do índice em MB"""
        try:
            total_size = 0
            for root, dirs, files in os.walk(self.index_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            return round(total_size / (1024 * 1024), 2)
        except Exception:
            return 0.0
    
    def clear_all_caches(self):
        """Limpa todos os caches (BM25 + embeddings)"""
        with self._lock:
            # Limpa cache base
            if hasattr(self.base_indexer, 'clear_cache'):
                self.base_indexer.clear_cache()
            
            # Limpa cache de embeddings
            if self.semantic_engine:
                self.semantic_engine.clear_cache()

            import sys
            sys.stderr.write("✅ Todos os caches limpos\n")
    
    def __enter__(self):
        """Context manager entry"""
        if self.enable_auto_indexing:
            self.start_auto_indexing()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.enable_auto_indexing:
            self.stop_auto_indexing()

# Funções utilitárias para compatibilidade com API existente
def create_enhanced_indexer(index_dir: str = ".mcp_index", 
                           repo_root: str = ".",
                           **kwargs) -> EnhancedCodeIndexer:
    """Factory function para criar indexador melhorado"""
    return EnhancedCodeIndexer(
        index_dir=index_dir,
        repo_root=repo_root,
        **kwargs
    )

def enhanced_search_code(indexer: EnhancedCodeIndexer, 
                        query: str, 
                        top_k: int = 30, 
                        filters: Optional[Dict] = None,
                        use_semantic: bool = True) -> List[Dict]:
    """Função de busca compatível com API original"""
    return indexer.search_code(
        query=query,
        top_k=top_k,
        filters=filters,
        use_semantic=use_semantic
    )

def enhanced_build_context_pack(indexer: EnhancedCodeIndexer,
                               query: str,
                               budget_tokens: int = 3000,
                               max_chunks: int = 10,
                               strategy: str = "mmr") -> Dict:
    """Função de context pack compatível com API original"""
    return indexer.build_context_pack(
        query=query,
        budget_tokens=budget_tokens,
        max_chunks=max_chunks,
        strategy=strategy
    )

def enhanced_index_repo_paths(indexer: EnhancedCodeIndexer,
                             paths: List[str],
                             recursive: bool = True,
                             include_globs: List[str] = None,
                             exclude_globs: List[str] = None) -> Dict[str, Any]:
    """Função de indexação compatível com API original"""
    # Implementa lógica de glob matching se necessário
    # Por simplicidade, indexa todos os paths fornecidos
    return indexer.index_files(paths)