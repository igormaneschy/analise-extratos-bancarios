#!/usr/bin/env python3
"""Teste mínimo do servidor MCP"""

print("🔍 Testando importações...")

try:
    from mcp.server.fastmcp import FastMCP
    print('✅ FastMCP importado')
    HAS_FASTMCP = True
except ImportError as e:
    print(f'❌ FastMCP falhou: {e}')
    HAS_FASTMCP = False

try:
    from mcp.server import Server
    print('✅ Server importado')
    HAS_SERVER = True
except ImportError as e:
    print(f'❌ Server falhou: {e}')
    HAS_SERVER = False

print("🔍 Testando importações enhanced...")

try:
    from code_indexer_enhanced import EnhancedCodeIndexer
    print('✅ EnhancedCodeIndexer importado')
    HAS_ENHANCED = True
except ImportError as e:
    print(f'❌ EnhancedCodeIndexer falhou: {e}')
    HAS_ENHANCED = False

print("🔍 Testando instanciação...")

if HAS_ENHANCED:
    try:
        indexer = EnhancedCodeIndexer(
            index_dir=".mcp_index", 
            repo_root="."
        )
        print('✅ EnhancedCodeIndexer instanciado')
    except Exception as e:
        print(f'❌ Erro na instanciação: {e}')
        print(f'Tipo do erro: {type(e).__name__}')
        import traceback
        traceback.print_exc()

print("🔍 Testando servidor...")

if HAS_FASTMCP:
    try:
        mcp = FastMCP(name="test-server")
        print('✅ FastMCP servidor criado')
        
        @mcp.tool()
        def test_tool() -> dict:
            return {"status": "ok"}
        
        print('✅ Tool registrada')
        print('Servidor pronto!')
        
    except Exception as e:
        print(f'❌ Erro no servidor: {e}')
        import traceback
        traceback.print_exc()