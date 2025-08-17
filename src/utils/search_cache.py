#!/usr/bin/env python3
"""
Módulo para gerenciamento de cache de resultados de busca
"""
import json
import hashlib
import time
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta


class SearchCache:
    """Sistema de cache para resultados de busca"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Inicializa o cache de buscas.
        
        Args:
            max_size: Número máximo de entradas no cache
            ttl_seconds: Tempo de vida das entradas em segundos
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_order: Dict[str, float] = {}  # Para LRU
    
    def _generate_key(self, query: str, **kwargs) -> str:
        """
        Gera uma chave única para uma consulta e seus parâmetros.
        
        Args:
            query: Texto da consulta
            **kwargs: Outros parâmetros da consulta
            
        Returns:
            Chave hash única para o cache
        """
        # Criar um dicionário ordenado com todos os parâmetros
        params = {"query": query, **kwargs}
        
        # Ordenar as chaves para garantir consistência
        sorted_params = {k: params[k] for k in sorted(params.keys())}
        
        # Converter para JSON e gerar hash
        params_str = json.dumps(sorted_params, sort_keys=True, default=str)
        return hashlib.md5(params_str.encode()).hexdigest()
    
    def get(self, query: str, **kwargs) -> Optional[Any]:
        """
        Recupera resultados do cache se disponíveis e válidos.
        
        Args:
            query: Texto da consulta
            **kwargs: Outros parâmetros da consulta
            
        Returns:
            Resultados em cache ou None se não encontrados/inválidos
        """
        key = self._generate_key(query, **kwargs)
        
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Verificar se expirou
        if time.time() - entry["timestamp"] > self.ttl_seconds:
            # Remover entrada expirada
            del self.cache[key]
            if key in self.access_order:
                del self.access_order[key]
            return None
        
        # Atualizar ordem de acesso para LRU
        self.access_order[key] = time.time()
        
        return entry["results"]
    
    def put(self, query: str, results: Any, **kwargs) -> None:
        """
        Armazena resultados no cache.
        
        Args:
            query: Texto da consulta
            results: Resultados a serem armazenados
            **kwargs: Outros parâmetros da consulta
        """
        # Remover entradas expiradas
        self._cleanup_expired()
        
        # Se o cache está cheio, remover a entrada menos recentemente usada
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        key = self._generate_key(query, **kwargs)
        
        # Armazenar resultados
        self.cache[key] = {
            "results": results,
            "timestamp": time.time(),
            "query": query,
            "params": kwargs
        }
        
        # Registrar acesso
        self.access_order[key] = time.time()
    
    def _cleanup_expired(self) -> None:
        """Remove entradas expiradas do cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry["timestamp"] > self.ttl_seconds
        ]
        
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_order:
                del self.access_order[key]
    
    def _evict_lru(self) -> None:
        """Remove a entrada menos recentemente usada (LRU)."""
        if not self.access_order:
            return
        
        # Encontrar a chave com o menor timestamp de acesso
        lru_key = min(self.access_order.keys(), key=lambda k: self.access_order[k])
        
        # Remover do cache e ordem de acesso
        del self.cache[lru_key]
        del self.access_order[lru_key]
    
    def invalidate_file(self, file_path: str) -> None:
        """
        Invalida todas as entradas de cache relacionadas a um arquivo específico.
        
        Args:
            file_path: Caminho do arquivo que foi modificado
        """
        keys_to_remove = []
        
        for key, entry in self.cache.items():
            # Verificar se os resultados contêm referências ao arquivo
            results = entry["results"]
            if isinstance(results, list):
                for result in results:
                    if isinstance(result, dict) and result.get("file") == file_path:
                        keys_to_remove.append(key)
                        break
            elif isinstance(results, dict) and results.get("file") == file_path:
                keys_to_remove.append(key)
        
        # Remover entradas relacionadas ao arquivo
        for key in keys_to_remove:
            del self.cache[key]
            if key in self.access_order:
                del self.access_order[key]
    
    def clear(self) -> None:
        """Limpa todo o cache."""
        self.cache.clear()
        self.access_order.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.
        
        Returns:
            Dicionário com estatísticas do cache
        """
        current_time = time.time()
        expired_count = sum(
            1 for entry in self.cache.values()
            if current_time - entry["timestamp"] > self.ttl_seconds
        )
        
        return {
            "total_entries": len(self.cache),
            "max_size": self.max_size,
            "expired_entries": expired_count,
            "ttl_seconds": self.ttl_seconds
        }


# Instância singleton para uso global
search_cache = SearchCache()