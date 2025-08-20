#!/usr/bin/env python3
"""
Script para executar o teste de cache com captura de saída e erros
"""
import sys
import os
import subprocess

# Adiciona o diretório raiz ao path para imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=== Executando Teste de Cache com Captura Completa ===")

try:
    # Executa o teste e captura a saída
    result = subprocess.run(
        [sys.executable, "test_cache.py"],
        capture_output=True,
        text=True,
        timeout=60,  # Timeout de 60 segundos
        cwd=project_root
    )
    
    print("STDOUT:")
    print(result.stdout)
    
    print("STDERR:")
    print(result.stderr)
    
    print(f"Return code: {result.returncode}")
    
except subprocess.TimeoutExpired:
    print("✗ Teste excedeu o tempo limite de 60 segundos")
except Exception as e:
    print(f"✗ Erro ao executar teste: {e}")
    import traceback
    traceback.print_exc()