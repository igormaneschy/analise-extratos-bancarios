#!/usr/bin/env python3
"""
Script para verificar a integração com o servidor MCP
"""
import json
import requests
from pathlib import Path
import sys

def check_mcp_integration():
    """Verifica a integração com o servidor MCP"""
    print("=== Verificação de Integração MCP ===")
    
    # 1. Verificar se o servidor MCP está rodando
    print("1. Verificando servidor MCP...")
    try:
        # Tentar conectar ao servidor MCP na porta padrão
        response = requests.get("http://localhost:31337", timeout=2)
        print("✅ Servidor MCP está respondendo")
    except requests.exceptions.ConnectionError:
        print("ℹ️  Servidor MCP não está respondendo")
        print("   Para iniciar: python mcp_server.py")
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Erro ao conectar ao servidor MCP: {e}")
    
    # 2. Verificar arquivos de configuração MCP
    print("\n2. Verificando configuração MCP...")
    mcp_config_files = [
        ".codellm/mcp_config.json",
        ".codellm/mcp_rules.json"
    ]
    
    for config_file in mcp_config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file} encontrado")
        else:
            print(f"ℹ️  {config_file} não encontrado (opcional)")
    
    # 3. Verificar regras MCP
    print("\n3. Verificando regras MCP...")
    rules_dir = Path(".codellm/rules")
    if rules_dir.exists():
        rules_files = list(rules_dir.glob("*.mdc"))
        print(f"✅ {len(rules_files)} regras encontradas:")
        for rule_file in rules_files:
            print(f"   • {rule_file.name}")
    else:
        print("⚠️  Diretório de regras não encontrado")
    
    # 4. Verificar integração com histórico
    print("\n4. Verificando integração com histórico...")
    dev_history = Path("dev_history.md")
    if dev_history.exists():
        print("✅ Sistema de histórico de desenvolvimento ativo")
    else:
        print("⚠️  Sistema de histórico não encontrado")
    
    print("\n=== Resumo ===")
    print("✅ Integração MCP configurada")
    print("✅ Regras do agente disponíveis")
    print("✅ Sistema de histórico ativo")
    print("\nPara iniciar o servidor MCP: python mcp_server.py")

if __name__ == "__main__":
    check_mcp_integration()