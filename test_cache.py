#!/usr/bin/env python3
"""
Script de teste para o sistema de cache de buscas
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from code_indexer import search_cache, index_code, search_code


def test_cache():
    """Testa o funcionamento do cache de buscas"""
    print("=== Teste do Sistema de Cache ===")
    
    # Indexar alguns arquivos de exemplo
    print("\n1. Indexando arquivos de teste...")
    test_files = ["code_indexer.py", "mcp_server.py"]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            if index_code(file_path):
                print(f"   ✓ {file_path} indexado com sucesso")
            else:
                print(f"   ✗ Falha ao indexar {file_path}")
        else:
            print(f"   ⚠ {file_path} não encontrado")
    
    # Realizar buscas
    print("\n2. Realizando buscas...")
    query = "sistema de cache"
    
    # Primeira busca (não deve estar em cache)
    print(f"   Busca 1: '{query}'")
    results1 = search_code(query, top_k=2, recency_weight=0.5)
    print(f"   Resultados: {len(results1)} encontrado(s)")
    
    # Segunda busca (deve estar em cache)
    print(f"   Busca 2: '{query}' (deve usar cache)")
    results2 = search_code(query, top_k=2, recency_weight=0.5)
    print(f"   Resultados: {len(results2)} encontrado(s)")
    
    # Verificar estatísticas do cache
    print("\n3. Estatísticas do cache:")
    stats = search_cache.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Testar invalidação de cache
    print("\n4. Testando invalidação de cache...")
    if os.path.exists("code_indexer.py"):
        # Indexar novamente o mesmo arquivo (deve invalidar o cache)
        print("   Reindexando code_indexer.py...")
        index_code("code_indexer.py")
        
        # Verificar estatísticas novamente
        stats = search_cache.get_stats()
        print(f"   Entradas no cache após invalidação: {stats['total_entries']}")
    
    print("\n=== Teste concluído ===")


if __name__ == "__main__":
    test_cache()