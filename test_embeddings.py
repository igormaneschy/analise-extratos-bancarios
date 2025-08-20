#!/usr/bin/env python3
"""
Script para testar o módulo de embeddings
"""
import sys
import os

# Adiciona o diretório raiz ao path para imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=== Testando Módulo de Embeddings ===")
print(f"Diretório atual: {os.getcwd()}")
print(f"Project root: {project_root}")

try:
    print("Importando embedding_model...")
    from src.utils.embeddings import embedding_model
    print("✓ Módulo de embeddings importado com sucesso")
    
    print("Testando geração de embedding...")
    test_text = "teste de embeddings"
    embedding = embedding_model.encode(test_text)
    print(f"✓ Embedding gerado com sucesso. Dimensão: {len(embedding)}")
    
    print("Testando dimensão...")
    dim = embedding_model.get_embedding_dimension()
    print(f"✓ Dimensão obtida: {dim}")
    
except Exception as e:
    print(f"✗ Erro: {e}")
    import traceback
    traceback.print_exc()