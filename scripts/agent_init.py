#!/usr/bin/env python3
"""
Script de inicialização do agente - Prepara todo o ambiente para uso do agente
"""
import os
import sys

def main():
    """Função principal de inicialização do agente"""
    print("🤖 Inicializando Ambiente do Agente")
    print("=" * 50)

    # 1. Verificar ambiente virtual
    print("1. Verificando ambiente...")
    if "VIRTUAL_ENV" not in os.environ:
        print("⚠️  Aviso: Não está em um ambiente virtual")
        print("   Recomendação: source venv/bin/activate")
    else:
        print("✅ Ambiente virtual ativo")

    # 2. Verificar dependências
    print("\n2. Verificando dependências...")
    dependencies = [
        "sentence_transformers",
        "pytest",
        "click",
        "requests"
    ]

    missing_deps = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep}")
            missing_deps.append(dep)

    if missing_deps:
        print(f"\n❌ Dependências faltando: {', '.join(missing_deps)}")
        print("   Execute: pip install -r requirements.txt")
        return False
    else:
        print("✅ Todas as dependências estão instaladas")

    # 3. Mostrar comandos úteis
    print("\n" + "=" * 50)
    print("✅ Ambiente do agente pronto para uso!")
    print("\nComandos úteis:")
    print("• python main.py --help          # Ajuda do sistema")
    print("• python main.py analyze <arquivo>  # Analisar extrato")
    print("• pytest tests/ -v               # Executar testes")
    print("• python mcp_server.py           # Iniciar servidor MCP")
    print("• python reindexProject.py       # Reindexar projeto")
    print("• python test_cache.py           # Testar cache")

    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Ambiente configurado com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Falha na configuração do ambiente")
        sys.exit(1)