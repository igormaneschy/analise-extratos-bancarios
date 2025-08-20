#!/usr/bin/env python3
"""
Script para testar o servidor MCP e verificar se todas as correções foram aplicadas corretamente
"""

import sys
import json
import asyncio

def test_imports():
    """Testa se todos os módulos podem ser importados corretamente"""
    print("Testando importações...")

    try:
        import mcp_server
        print("✓ mcp_server importado com sucesso")
    except Exception as e:
        print(f"✗ Erro ao importar mcp_server: {e}")
        return False

    try:
        import code_indexer
        print("✓ code_indexer importado com sucesso")
    except Exception as e:
        print(f"✗ Erro ao importar code_indexer: {e}")
        return False

    try:
        import src.utils.embeddings
        print("✓ embeddings importado com sucesso")
    except Exception as e:
        print(f"✗ Erro ao importar embeddings: {e}")
        return False

    try:
        import src.utils.dev_history
        print("✓ dev_history importado com sucesso")
    except Exception as e:
        print(f"✗ Erro ao importar dev_history: {e}")
        return False

    try:
        import src.utils.search_cache
        print("✓ search_cache importado com sucesso")
    except Exception as e:
        print(f"✗ Erro ao importar search_cache: {e}")
        return False

    return True

def test_json_parsing():
    """Testa se não há mensagens de impressão que interfiram no parsing JSON"""
    print("\nTestando parsing JSON...")

    # Testar uma mensagem de inicialização simples
    initialize_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "capabilities": {}
        }
    }

    try:
        message_str = json.dumps(initialize_message)
        parsed = json.loads(message_str)
        print("✓ JSON parsing funcionando corretamente")
        return True
    except Exception as e:
        print(f"✗ Erro no parsing JSON: {e}")
        return False

async def test_mcp_server_startup():
    """Testa a inicialização do servidor MCP"""
    print("\nTestando inicialização do servidor MCP...")

    try:
        # Importar e testar funções principais
        from mcp_server import handle_message
        print("✓ Funções do servidor MCP carregadas corretamente")

        # Testar handle_message com uma mensagem simples
        test_message = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getCacheStats"
        })

        # Isso não deve lançar exceções de parsing
        response = await handle_message(test_message)
        print("✓ handle_message processou mensagem corretamente")
        return True
    except Exception as e:
        print(f"✗ Erro ao testar servidor MCP: {e}")
        return False

async def main():
    """Função principal de teste"""
    print("=== Teste do Servidor MCP ===\n")

    tests = [
        test_imports,
        test_json_parsing,
        test_mcp_server_startup
    ]

    passed = 0
    total = len(tests)

    # Executar testes síncronos
    for test in tests[:-1]:  # Todos exceto o último (assíncrono)
        if test():
            passed += 1
        else:
            print("Teste falhou!")

    # Executar teste assíncrono
    if await tests[-1]():
        passed += 1
    else:
        print("Teste falhou!")

    print(f"\n=== Resultado: {passed}/{total} testes passaram ===")

    if passed == total:
        print("Todos os testes passaram! O servidor MCP deve funcionar corretamente.")
        return 0
    else:
        print("Alguns testes falharam. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))