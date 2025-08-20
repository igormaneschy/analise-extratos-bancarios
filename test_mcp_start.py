#!/usr/bin/env python3
"""
Script para testar a inicialização completa do servidor MCP
"""

import sys
import os

def main():
    print("=== Teste de Inicialização Completa do MCP Server ===\n")
    
    try:
        # Testar importação do mcp_server
        print("1. Testando importação do mcp_server...")
        from mcp_server import handle_message, mcp_loop, start_watcher
        print("   ✓ mcp_server importado com sucesso")
        
        # Testar criação do watcher
        print("2. Testando criação do watcher...")
        observer = start_watcher()
        print("   ✓ Watcher criado com sucesso")
        
        # Parar o watcher
        observer.stop()
        observer.join()
        print("   ✓ Watcher parado corretamente")
        
        print("\n🎉 Todos os testes passaram! O servidor MCP deve iniciar corretamente.")
        return 0
        
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())