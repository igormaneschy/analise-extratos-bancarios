#!/usr/bin/env python3
"""Teste de importações do MCP"""

print("🔍 Testando importações do MCP...")

try:
    from mcp.server.fastmcp import FastMCP
    print('✅ FastMCP available')
    HAS_FASTMCP = True
except ImportError as e:
    print('❌ FastMCP not available:', e)
    HAS_FASTMCP = False

try:
    from mcp.server import Server
    print('✅ Server available') 
    HAS_SERVER = True
except ImportError as e:
    print('❌ Server not available:', e)
    HAS_SERVER = False

try:
    import mcp
    print('✅ MCP base module available')
    print('MCP dir:', [x for x in dir(mcp) if not x.startswith('_')])
except Exception as e:
    print('❌ Error importing mcp:', e)

try:
    from mcp import types
    print('✅ MCP types available')
except ImportError as e:
    print('❌ MCP types not available:', e)

print(f"\nResumo:")
print(f"FastMCP: {'✅' if HAS_FASTMCP else '❌'}")
print(f"Server:  {'✅' if HAS_SERVER else '❌'}")