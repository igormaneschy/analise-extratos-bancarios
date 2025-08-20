# mcp_server.py
import asyncio
from mcp.server import Server
from code_indexer import index_code, search_code

# Cria o servidor MCP
server = Server("code-indexer")

# Tool para indexar arquivo
@server.tool("index_file")
def index_file(params: dict):
    file_path = params.get("path")
    if not file_path:
        return {"error": "Parâmetro 'path' é obrigatório"}
    index_code(file_path)
    return {"status": "indexed", "file": file_path}

# Tool para buscar no código
@server.tool("search_code")
def search_tool(params: dict):
    query = params.get("query")
    if not query:
        return {"error": "Parâmetro 'query' é obrigatório"}
    top_k = params.get("top_k", 5)
    results = search_code(query, top_k=top_k)
    return results

if __name__ == "__main__":
    # Importante: não pode ter nenhum print solto aqui
    asyncio.run(server.run_stdio())