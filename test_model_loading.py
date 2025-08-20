#!/usr/bin/env python3
"""
Script para testar a inicialização do modelo de embeddings com mais detalhes
"""
import sys
import os
import time

# Adiciona o diretório raiz ao path para imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=== Testando Inicialização do Modelo de Embeddings ===")
print(f"Diretório atual: {os.getcwd()}")
print(f"Project root: {project_root}")

print("Importando SentenceTransformer...")
start_time = time.time()
try:
    from sentence_transformers import SentenceTransformer
    end_time = time.time()
    print(f"✓ SentenceTransformer importado com sucesso em {end_time - start_time:.2f} segundos")
except Exception as e:
    print(f"✗ Erro ao importar SentenceTransformer: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Tentando carregar modelo...")
start_time = time.time()
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    end_time = time.time()
    print(f"✓ Modelo carregado com sucesso em {end_time - start_time:.2f} segundos")
    
    print("Testando codificação...")
    start_time = time.time()
    embedding = model.encode("teste")
    end_time = time.time()
    print(f"✓ Codificação realizada com sucesso em {end_time - start_time:.2f} segundos")
    print(f"Dimensão do embedding: {len(embedding)}")
    
except Exception as e:
    print(f"✗ Erro ao carregar/codificar com o modelo: {e}")
    import traceback
    traceback.print_exc()