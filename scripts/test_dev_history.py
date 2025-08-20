#!/usr/bin/env python3
"""
Script de teste para verificar se o utilitário de histórico está seguindo as regras corretamente
"""
import sys
import os

# Adiciona o diretório src ao path para importar o módulo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.dev_history import dev_history_manager

def test_history_utility():
    """Testa o utilitário de histórico de desenvolvimento"""
    
    print("🧪 Testando utilitário de histórico de desenvolvimento...")
    
    # Teste 1: Entrada simples
    print("\n1️⃣ Teste de entrada simples:")
    result1 = dev_history_manager.update_history(
        file_paths=["src/utils/dev_history.py"],
        action_type="Correção",
        description="Correção do utilitário para seguir as regras padronizadas.",
        details={
            "Problema": "Utilitário não seguia o template das regras corretamente",
            "Causa": "Implementação anterior não considerava formato exato e validações",
            "Solução": "Reescrita completa seguindo template das regras com validações",
            "Observações": "Agora inclui hash, data correta e formato padronizado"
        }
    )
    print(f"✅ Resultado: {'Adicionado' if result1 else 'Já existia ou erro'}")
    
    # Teste 2: Múltiplos arquivos
    print("\n2️⃣ Teste com múltiplos arquivos:")
    result2 = dev_history_manager.update_history(
        file_paths=["scripts/test_dev_history.py", "src/utils/dev_history.py"],
        action_type="Teste",
        description="Criação de script de teste para validar funcionamento do histórico.",
        details={
            "Problema": "Não havia forma de testar se o utilitário estava funcionando",
            "Causa": "Falta de script de validação",
            "Solução": "Criação de script de teste abrangente",
            "Observações": "Testa diferentes cenários e valida formato"
        }
    )
    print(f"✅ Resultado: {'Adicionado' if result2 else 'Já existia ou erro'}")
    
    # Teste 3: Validação de tipo de ação
    print("\n3️⃣ Teste de validação de tipo:")
    result3 = dev_history_manager.update_history(
        file_paths=["test_file.py"],
        action_type="feature",  # Deve ser convertido para "Melhoria"
        description="Teste de normalização de tipo de ação.",
        details={
            "Problema": "Tipos de ação podem vir em formatos diferentes",
            "Causa": "Entrada manual ou automática pode usar variações",
            "Solução": "Normalização automática para tipos válidos",
            "Observações": "Mapeia 'feature' para 'Melhoria' automaticamente"
        }
    )
    print(f"✅ Resultado: {'Adicionado' if result3 else 'Já existia ou erro'}")
    
    # Teste 4: Verificação de arquivos que devem ser rastreados
    print("\n4️⃣ Teste de arquivos que devem ser rastreados:")
    test_files = [
        "src/domain/models.py",  # ✅ Deve rastrear
        "__pycache__/test.pyc",  # ❌ Não deve rastrear
        "requirements.txt",      # ✅ Deve rastrear
        ".vscode/settings.json", # ❌ Não deve rastrear
        "tests/test_main.py",    # ✅ Deve rastrear
        "build/output.txt"       # ❌ Não deve rastrear
    ]
    
    for file_path in test_files:
        should_track = dev_history_manager.should_track_file(file_path)
        status = "✅ Rastrear" if should_track else "❌ Ignorar"
        print(f"  {file_path}: {status}")
    
    print("\n🎯 Verificando arquivo de histórico gerado...")
    
    # Verifica se o arquivo foi criado e tem o formato correto
    history_path = "dev_history.md"
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Verifica elementos obrigatórios das regras
        checks = [
            ("[2025-" in content, "✅ Data no formato YYYY-MM-DD"),
            ("Arquivos:" in content, "✅ Campo Arquivos presente"),
            ("Ação/Tipo:" in content, "✅ Campo Ação/Tipo presente"),
            ("Descrição:" in content, "✅ Campo Descrição presente"),
            ("Detalhes:" in content, "✅ Seção Detalhes presente"),
            ("Problema:" in content, "✅ Campo Problema presente"),
            ("Causa:" in content, "✅ Campo Causa presente"),
            ("Solução:" in content, "✅ Campo Solução presente"),
            ("Observações:" in content, "✅ Campo Observações presente"),
            ("Hash:" in content, "✅ Hash para evitar duplicatas presente")
        ]
        
        print("\n📋 Validação do formato:")
        for check, message in checks:
            print(f"  {message if check else message.replace('✅', '❌')}")
        
        # Mostra últimas linhas do arquivo
        lines = content.strip().split('\n')
        print(f"\n📄 Últimas 10 linhas do histórico:")
        for line in lines[-10:]:
            print(f"  {line}")
            
    else:
        print("❌ Arquivo dev_history.md não foi criado")
    
    print("\n🎉 Teste concluído!")

if __name__ == "__main__":
    test_history_utility()