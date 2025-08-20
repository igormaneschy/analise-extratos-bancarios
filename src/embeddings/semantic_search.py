# src/embeddings/semantic_search.py
"""
Sistema de busca semântica usando embeddings locais
Integração com sentence-transformers para embeddings eficientes
"""

from __future__ import annotations
import os
import json
import numpy as np
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    SentenceTransformer = None

@dataclass
class EmbeddingResult:
    chunk_id: str
    similarity_score: float
    bm25_score: float
    combined_score: float
    content: str
    file_path: str

class SemanticSearchEngine:
    """
    Sistema de busca semântica que combina embeddings com BM25
    para busca híbrida otimizada
    """
    
    def __init__(self, cache_dir: str = ".mcp_index", model_name: str = "all-MiniLM-L6-v2"):
        self.cache_dir = Path(cache_dir)
        self.embeddings_dir = self.cache_dir / "embeddings"
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_name = model_name
        self.model = None
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        self.metadata_cache: Dict[str, Dict] = {}
        
        if HAS_SENTENCE_TRANSFORMERS:
            self._initialize_model()
        else:
            import sys
            sys.stderr.write("⚠️  sentence-transformers não encontrado. Busca semântica desabilitada.\n")

    def _initialize_model(self):
        """Inicializa o modelo de embeddings de forma lazy"""
        if self.model is None and HAS_SENTENCE_TRANSFORMERS:
            import sys
            sys.stderr.write(f"🔄 Carregando modelo de embeddings: {self.model_name}\n")
            try:
                self.model = SentenceTransformer(self.model_name)
                sys.stderr.write(f"✅ Modelo {self.model_name} carregado com sucesso\n")
            except Exception as e:
                sys.stderr.write(f"❌ Erro ao carregar modelo: {e}\n")
                self.model = None
    
    def _get_embedding_cache_path(self, chunk_id: str) -> Path:
        """Gera caminho do cache para embeddings de um chunk"""
        return self.embeddings_dir / f"{chunk_id}.npy"
    
    def _get_metadata_cache_path(self, chunk_id: str) -> Path:
        """Gera caminho do cache para metadados de um chunk"""
        return self.embeddings_dir / f"{chunk_id}_meta.json"
    
    def _hash_content(self, content: str) -> str:
        """Gera hash do conteúdo para cache invalidation"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get_embedding(self, chunk_id: str, content: str, force_regenerate: bool = False) -> Optional[np.ndarray]:
        """
        Obtém embedding para um chunk, usando cache quando possível
        
        Args:
            chunk_id: Identificador único do chunk
            content: Conteúdo do chunk para gerar embedding
            force_regenerate: Se True, força regeneração do embedding
            
        Returns:
            Array numpy com o embedding ou None se erro
        """
        if not HAS_SENTENCE_TRANSFORMERS or self.model is None:
            return None
            
        cache_path = self._get_embedding_cache_path(chunk_id)
        metadata_path = self._get_metadata_cache_path(chunk_id)
        content_hash = self._hash_content(content)
        
        # Verifica cache se não forçar regeneração
        if not force_regenerate and cache_path.exists() and metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Verifica se conteúdo não mudou
                if metadata.get('content_hash') == content_hash:
                    embedding = np.load(cache_path)
                    self.embeddings_cache[chunk_id] = embedding
                    self.metadata_cache[chunk_id] = metadata
                    return embedding
            except Exception as e:
                import sys
                sys.stderr.write(f"⚠️  Erro ao ler cache de embedding para {chunk_id}: {e}\n")
        
        # Gera novo embedding
        try:
            # Limita conteúdo para não sobrecarregar o modelo
            content_truncated = content[:2000] if len(content) > 2000 else content
            embedding = self.model.encode([content_truncated])[0]
            
            # Salva no cache
            np.save(cache_path, embedding)
            metadata = {
                'chunk_id': chunk_id,
                'content_hash': content_hash,
                'model_name': self.model_name,
                'content_length': len(content),
                'truncated': len(content) > 2000
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            # Atualiza cache em memória
            self.embeddings_cache[chunk_id] = embedding
            self.metadata_cache[chunk_id] = metadata
            
            return embedding
            
        except Exception as e:
            import sys
            sys.stderr.write(f"❌ Erro ao gerar embedding para {chunk_id}: {e}\n")
            return None
    
    def search_similar(self, query: str, chunk_embeddings: Dict[str, np.ndarray], 
                      top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Busca chunks similares semanticamente à query
        
        Args:
            query: Texto da consulta
            chunk_embeddings: Dict de chunk_id -> embedding
            top_k: Número máximo de resultados
            
        Returns:
            Lista de (chunk_id, similarity_score) ordenada por similaridade
        """
        if not HAS_SENTENCE_TRANSFORMERS or self.model is None:
            return []
        
        try:
            # Gera embedding da query
            query_embedding = self.model.encode([query])[0]
            
            # Calcula similaridade com todos os chunks
            similarities = []
            for chunk_id, chunk_embedding in chunk_embeddings.items():
                # Similaridade coseno
                similarity = np.dot(query_embedding, chunk_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
                )
                similarities.append((chunk_id, float(similarity)))
            
            # Ordena por similaridade descendente
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            import sys
            sys.stderr.write(f"❌ Erro na busca semântica: {e}\n")
            return []
    
    def hybrid_search(self, query: str, bm25_results: List[Dict], 
                     chunk_data: Dict[str, Dict], 
                     semantic_weight: float = 0.3, 
                     top_k: int = 10) -> List[EmbeddingResult]:
        """
        Combina resultados BM25 com busca semântica
        
        Args:
            query: Consulta original
            bm25_results: Resultados da busca BM25
            chunk_data: Dados completos dos chunks (chunk_id -> data)
            semantic_weight: Peso da similaridade semântica (0-1)
            top_k: Número de resultados finais
            
        Returns:
            Lista de EmbeddingResult ordenada por score combinado
        """
        if not HAS_SENTENCE_TRANSFORMERS or not bm25_results:
            # Fallback para apenas BM25
            results = []
            for result in bm25_results[:top_k]:
                chunk_id = result['chunk_id']
                chunk = chunk_data.get(chunk_id, {})
                results.append(EmbeddingResult(
                    chunk_id=chunk_id,
                    similarity_score=0.0,
                    bm25_score=result.get('score', 0.0),
                    combined_score=result.get('score', 0.0),
                    content=chunk.get('content', ''),
                    file_path=chunk.get('file_path', '')
                ))
            return results
        
        # Garante que modelo está carregado
        self._initialize_model()
        if self.model is None:
            return []
        
        # Obtém embeddings para chunks relevantes
        chunk_embeddings = {}
        for result in bm25_results[:top_k * 2]:  # Processa mais chunks para melhor seleção
            chunk_id = result['chunk_id']
            chunk = chunk_data.get(chunk_id, {})
            content = chunk.get('content', '')
            
            if content:
                embedding = self.get_embedding(chunk_id, content)
                if embedding is not None:
                    chunk_embeddings[chunk_id] = embedding
        
        # Busca semântica
        semantic_results = self.search_similar(query, chunk_embeddings, top_k * 2)
        semantic_scores = {chunk_id: score for chunk_id, score in semantic_results}
        
        # Normaliza scores BM25
        bm25_scores = {r['chunk_id']: r.get('score', 0.0) for r in bm25_results}
        max_bm25 = max(bm25_scores.values()) if bm25_scores.values() else 1.0
        normalized_bm25 = {cid: score/max_bm25 for cid, score in bm25_scores.items()}
        
        # Combina scores
        combined_results = []
        all_chunk_ids = set(bm25_scores.keys()) | set(semantic_scores.keys())
        
        for chunk_id in all_chunk_ids:
            bm25_score = normalized_bm25.get(chunk_id, 0.0)
            semantic_score = semantic_scores.get(chunk_id, 0.0)
            
            # Score combinado: (1-w)*BM25 + w*Semantic
            combined_score = (1 - semantic_weight) * bm25_score + semantic_weight * semantic_score
            
            chunk = chunk_data.get(chunk_id, {})
            combined_results.append(EmbeddingResult(
                chunk_id=chunk_id,
                similarity_score=semantic_score,
                bm25_score=bm25_score,
                combined_score=combined_score,
                content=chunk.get('content', ''),
                file_path=chunk.get('file_path', '')
            ))
        
        # Ordena por score combinado
        combined_results.sort(key=lambda x: x.combined_score, reverse=True)
        
        return combined_results[:top_k]
    
    def invalidate_cache(self, chunk_id: str):
        """Remove embedding do cache para um chunk específico"""
        cache_path = self._get_embedding_cache_path(chunk_id)
        metadata_path = self._get_metadata_cache_path(chunk_id)
        
        if cache_path.exists():
            cache_path.unlink()
        if metadata_path.exists():
            metadata_path.unlink()
            
        # Remove do cache em memória
        self.embeddings_cache.pop(chunk_id, None)
        self.metadata_cache.pop(chunk_id, None)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache de embeddings"""
        embedding_files = list(self.embeddings_dir.glob("*.npy"))
        metadata_files = list(self.embeddings_dir.glob("*_meta.json"))
        
        total_size = sum(f.stat().st_size for f in embedding_files + metadata_files)
        
        return {
            'enabled': HAS_SENTENCE_TRANSFORMERS and self.model is not None,
            'model_name': self.model_name,
            'cached_embeddings': len(embedding_files),
            'cache_size_mb': round(total_size / (1024 * 1024), 2),
            'in_memory_cache': len(self.embeddings_cache)
        }
    
    def clear_cache(self):
        """Limpa todo o cache de embeddings"""
        import shutil
        if self.embeddings_dir.exists():
            shutil.rmtree(self.embeddings_dir)
            self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        
        self.embeddings_cache.clear()
        self.metadata_cache.clear()