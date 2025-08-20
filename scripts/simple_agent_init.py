#!/usr/bin/env python3
"""
Script de inicialização do agente - Versão simplificada
"""
import os
import sys

def main():
    print("🤖 Inicializando Ambiente do Agente")
    print("=" * 50)
    
    # Verificar ambiente virtual
    if "VIRTUAL_ENV" not in os.environ:
        print("⚠️  Aviso: Não está em um ambiente virtual")
    else:
        print("✅ Ambiente virtual ativo")
    
    # Verificar dependências essenciais
    try:
        import sentence_transformers
        print("✅ sentence_transformers disponível")
    except ImportError:
        print("❌ sentence_transformers não encontrado")
    
    try:
        import pytest
        print("✅ pytest disponível")
    except ImportError:
        print("❌ pytest não encontrado")
    
    print("\n✅ Inicialização concluída!")
    print("\nComandos disponíveis:")
    print("• python main.py --help")
    print("• python mcp_server.py")
    print("• python reindexProject.py")
    print("• pytest tests/ -v")

if __name__ == "__main__":
    main()