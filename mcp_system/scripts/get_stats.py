#!/usr/bin/env python3
"""
Script para obter estatísticas do sistema MCP
"""

import json
import subprocess
import sys

def get_mcp_stats():
    """Executa o comando get_stats no servidor MCP"""
    # Comando JSON-RPC para obter estatísticas
    request = {
        "jsonrpc": "2.0",
        "method": "get_stats",
        "params": {},
        "id": 1
    }
    
    # Converte para string JSON
    request_str = json.dumps(request)
    
    print("Enviando requisição para o servidor MCP...")
    print(f"Requisição: {request_str}")
    
    # Aqui você precisaria se conectar ao servidor MCP
    # Esta é uma implementação simplificada
    print("\nPara executar este comando, você pode:")
    print("1. Usar a interface do VS Code com a extensão MCP")
    print("2. Enviar a requisição JSON-RPC diretamente para o servidor")
    print("3. Usar uma ferramenta como curl ou Postman se o servidor expuser uma API HTTP")

if __name__ == "__main__":
    get_mcp_stats()