#!/usr/bin/env python3
"""
Cliente MCP para obter estatísticas do sistema
"""

import json
import asyncio
import os
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def get_stats():
    """Obtém estatísticas do servidor MCP"""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    server_params = StdioServerParameters(
        command="python",
        args=["-u", "-m", "mcp_system.mcp_server_enhanced"],
        env={
            "INDEX_DIR": os.path.join(base_dir, ".mcp_index"),
            "INDEX_ROOT": os.path.abspath(os.path.join(base_dir, '..'))
        }
    )

    max_retries = 10
    retry_delay = 1  # segundos

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            for attempt in range(max_retries):
                try:
                    tools = await session.list_tools()
                    print("Ferramentas disponíveis:")
                    for tool in tools:
                        print(f"  - {tool.name}: {tool.description}")

                    print("\nExecutando comando get_stats...")
                    result = await session.call_tool("get_stats", {})
                    print("Resultado:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    break
                except Exception as e:
                    print(f"Tentativa {attempt+1} falhou: {e}")
                    if attempt == max_retries - 1:
                        print("Falha ao executar comando após várias tentativas.")
                        break
                    await asyncio.sleep(retry_delay)

if __name__ == "__main__":
    asyncio.run(get_stats())