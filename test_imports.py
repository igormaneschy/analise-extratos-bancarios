#!/usr/bin/env python3
"""
Script simples para testar importações do MCP Server
"""

def test_basic_imports():
    print("Testando importações básicas...")
    
    try:
        import sys
        import asyncio
        import os
        import json
        print("✓ Importações básicas OK")
    except Exception as e:
        print(f"✗ Erro nas importações básicas: {e}")
        return False
    
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        print("✓ Importações watchdog OK")
    except Exception as e:
        print(f"✗ Erro nas importações watchdog: {e}")
        return False
    
    return True

def test_code_indexer_imports():
    print("\nTestando importações do code_indexer...")
    
    try:
        from code_indexer import index_code, search_code, search_cache
        print("✓ Importações code_indexer OK")
    except Exception as e:
        print(f"✗ Erro nas importações code_indexer: {e}")
        return False
    
    return True

def test_utils_imports():
    print("\nTestando importações dos utilitários...")
    
    try:
        from src.utils.dev_history import dev_history_manager
        print("✓ Importação dev_history OK")
    except Exception as e:
        print(f"✗ Erro na importação dev_history: {e}")
        # Isso não é fatal, vamos continuar
        
    try:
        from src.utils.embeddings import embedding_model
        print("✓ Importação embeddings OK")
    except Exception as e:
        print(f"✗ Erro na importação embeddings: {e}")
        return False
    
    try:
        from src.utils.search_cache import search_cache as sc
        print("✓ Importação search_cache OK")
    except Exception as e:
        print(f"✗ Erro na importação search_cache: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== Teste de Importações do MCP Server ===\n")
    
    if not test_basic_imports():
        print("\n❌ Teste de importações básicas falhou")
        exit(1)
    
    if not test_code_indexer_imports():
        print("\n❌ Teste de importações code_indexer falhou")
        exit(1)
    
    if not test_utils_imports():
        print("\n❌ Teste de importações dos utilitários falhou")
        exit(1)
    
    print("\n🎉 Todos os testes de importação passaram!")
    print("O servidor MCP deve iniciar corretamente.")