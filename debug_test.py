#!/usr/bin/env python3
"""
Script para testar a inicialização do servidor MCP
"""

import sys
import os

def test_imports():
    """Testa se todas as importações estão funcionando corretamente"""
    print("Testando importações...")
    
    try:
        import json
        print("✓ json importado com sucesso")
    except Exception as e:
        print(f"✗ Erro ao importar json: {e}")
        return False
    
    try:
        from watchdog.observers import Observer
        print("✓ watchdog.observers importado com sucesso")
    except Exception as e:
        print(f"✗ Erro ao importar watchdog.observers: {e}")
        return False
    
    try:
        from watchdog.events import FileSystemEventHandler
        print("✓ watchdog.events importado com sucesso")
    except Exception as e:
        print(f"✗ Erro ao importar watchdog.events: {e}")
        return False
    
    try:
        from code_indexer import index_code, search_code, search_cache
        print("✓ code_indexer importado com sucesso")
    except Exception as e:
        print(f"✗ Erro ao importar code_indexer: {e}")
        return False
    
    try:
        from src.utils.dev_history import dev_history_manager
        print("✓ dev_history importado com sucesso")
    except Exception as e:
        print(f"✗ Erro ao importar dev_history: {e}")
        return False
    
    try:
        from src.utils.embeddings import embedding_model
        print("✓ embeddings importado com sucesso")
    except Exception as e:
        print(f"✗ Erro ao importar embeddings: {e}")
        return False
    
    try:
        from src.utils.search_cache import search_cache as sc
        print("✓ search_cache importado com sucesso")
    except Exception as e:
        print(f"✗ Erro ao importar search_cache: {e}")
        return False
    
    return True

def test_model_loading():
    """Testa se o modelo de embeddings carrega corretamente"""
    print("\nTestando carregamento do modelo...")
    
    try:
        from src.utils.embeddings import embedding_model
        if embedding_model.model is not None:
            print("✓ Modelo de embeddings carregado com sucesso")
            # Testar geração de embedding
            test_text = "Teste de embedding"
            embedding = embedding_model.embed_text(test_text)
            if embedding is not None:
                print(f"✓ Embedding gerado com sucesso (dimensão: {len(embedding)})")
            else:
                print("✗ Falha ao gerar embedding")
                return False
        else:
            print("✗ Modelo de embeddings não foi carregado")
            return False
    except Exception as e:
        print(f"✗ Erro ao carregar modelo de embeddings: {e}")
        return False
    
    return True

def main():
    """Função principal de teste"""
    print("=== Teste de Inicialização do Servidor MCP ===\n")
    
    # Testar importações
    if not test_imports():
        print("\n❌ Teste de importações falhou")
        return 1
    
    print("\n✅ Todos os módulos importados com sucesso")
    
    # Testar carregamento do modelo
    if not test_model_loading():
        print("\n❌ Teste de carregamento do modelo falhou")
        return 1
    
    print("\n✅ Modelo de embeddings carregado com sucesso")
    
    print("\n🎉 Todos os testes passaram! O servidor MCP deve iniciar corretamente.")
    return 0

if __name__ == "__main__":
    sys.exit(main())