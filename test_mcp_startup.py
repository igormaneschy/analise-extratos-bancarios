#!/usr/bin/env python3
"""
Teste rápido do servidor MCP enhanced
Verifica se pode ser iniciado sem erros
"""

import sys
import os

def test_server_startup():
    """Testa se o servidor pode ser iniciado"""
    print("🧪 Testando startup do servidor MCP...")
    
    try:
        # Importa o servidor
        import mcp_server_enhanced
        print("✅ Importação OK")
        
        # Verifica se as funções principais existem
        if hasattr(mcp_server_enhanced, 'mcp'):
            print("✅ FastMCP server criado")
            
        # Verifica tools registradas
        if hasattr(mcp_server_enhanced.mcp, '_tools'):
            tools_count = len(mcp_server_enhanced.mcp._tools)
            print(f"✅ {tools_count} tools registradas")
            
        print("✅ Servidor MCP enhanced está pronto!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    success = test_server_startup()
    sys.exit(0 if success else 1)