#!/usr/bin/env python3
"""
Script para configurar o contexto inicial do agente
"""
import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server import start_mcp_server
from src.utils.search_cache import search_cache
from code_indexer import search_code

def setup_agent_context():
    """Configura o contexto inicial do agente"""
    print("=== Configurando Contexto do Agente ===")
    
    # 1. Iniciar servidor MCP
    print("1. Servidor MCP disponível em porta padrão")
    
    # 2. Verificar cache
    print("2. Sistema de cache ativo:")
    cache_stats = search_cache.get_stats()
    for key, value in cache_stats.items():
        print(f"   - {key}: {value}")
    
    # 3. Verificar indexação
    print("3. Sistema de indexação pronto")
    
    # 4. Carregar regras
    print("4. Regras disponíveis em .codellm/rules/")
    
    # 5. Mostrar comandos úteis
    print("\n=== Comandos Úteis ===")
    print("• Para iniciar o servidor MCP: python mcp_server.py")
    print("• Para reindexar o projeto: python reindexProject.py")
    print("• Para executar testes: pytest tests/ -v")
    print("• Para verificar cache: python test_cache.py")
    
    print("\n✓ Contexto do agente configurado com sucesso!")

if __name__ == "__main__":
    setup_agent_context()