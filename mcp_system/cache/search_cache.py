#!/usr/bin/env python3
"""
Módulo para gerenciamento de cache de resultados de busca
"""
import json
import hashlib
import time
from typing import Any, Dict, Optional
# Removendo imports não utilizados que podem causar problemas

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
            Resultados em cache ou None se não disponíveis/inválidos
        """
        key = self._generate_key(query, **kwargs)

        # Verificar se a chave existe no cache
        if key not in self.cache:
            return None

        # Verificar se a entrada expirou
        entry = self.cache[key]
        if time.time() - entry["timestamp"] > self.ttl_seconds:
            # Remover entrada expirada
            del self.cache[key]
            if key in self.access_order:
                del self.access_order[key]
            return None

        # Atualizar ordem de acesso para LRU
        self.access_order[key] = time.time()

        return entry["results"]

    def set(self, query: str, results: Any, **kwargs) -> None:
        """
        Armazena resultados no cache.

        Args:
            query: Texto da consulta
            results: Resultados para armazenar
            **kwargs: Outros parâmetros da consulta
        """
        key = self._generate_key(query, **kwargs)

        # Remover entradas antigas se o cache estiver cheio
        if len(self.cache) >= self.max_size:
            # Encontrar a entrada LRU (menor timestamp de acesso)
            if self.access_order:
                lru_key = min(self.access_order.keys(), key=lambda k: self.access_order[k])
                del self.cache[lru_key]
                del self.access_order[lru_key]

        # Armazenar resultados
        self.cache[key] = {
            "results": results,
            "timestamp": time.time()
        }

        # Atualizar ordem de acesso
        self.access_order[key] = time.time()

    def invalidate_file(self, file_path: str) -> None:
        """
        Invalida todas as entradas do cache relacionadas a um arquivo específico.

        Args:
            file_path: Caminho do arquivo que foi modificado
        """
        keys_to_remove = []

        # Identificar entradas relacionadas ao arquivo
        for key, entry in self.cache.items():
            cached_results = entry.get("results", [])

            # Verificar se os resultados contêm referências ao arquivo
            if isinstance(cached_results, list):
                for result in cached_results:
                    if isinstance(result, dict) and result.get("file_path") == file_path:
                        keys_to_remove.append(key)
                        break
            elif isinstance(cached_results, dict) and cached_results.get("file") == file_path:
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