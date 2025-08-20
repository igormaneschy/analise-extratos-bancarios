#!/usr/bin/env python3
"""
Script para executar o teste de cache com saída detalhada
"""
import sys
import os

# Adiciona o diretório raiz ao path para imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=== Executando Teste de Cache ===")
print(f"Diretório atual: {os.getcwd()}")
print(f"Project root: {project_root}")

try:
    from test_cache import test_cache
    print("✓ Módulo de teste importado com sucesso")
    
    print("Executando teste...")
    test_cache()
    print("✓ Teste executado com sucesso")
    
except Exception as e:
    print(f"✗ Erro ao executar teste: {e}")
    import traceback
    traceback.print_exc()