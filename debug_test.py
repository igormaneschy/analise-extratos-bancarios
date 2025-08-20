#!/usr/bin/env python3
"""
Script de debug para o sistema de cache de buscas
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=== Debug do Sistema de Teste ===")
print("1. Verificando imports...")

try:
    from code_indexer import search_cache, index_code, search_code
    print("   ✓ Imports realizados com sucesso")
except Exception as e:
    print(f"   ✗ Erro nos imports: {e}")
    sys.exit(1)

print("2. Verificando função de teste...")
try:
    from test_cache import test_cache
    print("   ✓ Função de teste importada com sucesso")
except Exception as e:
    print(f"   ✗ Erro ao importar função de teste: {e}")
    sys.exit(1)

print("3. Executando teste...")
try:
    test_cache()
    print("   ✓ Teste executado com sucesso")
except Exception as e:
    print(f"   ✗ Erro ao executar teste: {e}")
    import traceback
    traceback.print_exc()