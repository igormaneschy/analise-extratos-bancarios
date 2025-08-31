#!/usr/bin/env python3
"""
Setup automático do sistema MCP melhorado
Configura busca semântica, auto-indexação e otimizações
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any
import pathlib

# Obter o diretório do script atual
CURRENT_DIR = pathlib.Path(__file__).parent.absolute()

def print_header(title: str):
    """Imprime header formatado"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")

def print_step(step: str, status: str = ""):
    """Imprime passo com status"""
    if status == "ok":
        print(f"✅ {step}")
    elif status == "warn":
        print(f"⚠️  {step}")
    elif status == "error":
        print(f"❌ {step}")
    else:
        print(f"🔄 {step}")

def check_dependencies() -> Dict[str, bool]:
    """Verifica dependências necessárias"""
    print_header("Verificando Dependências")
    
    deps = {}
    
    # Python básico
    try:
        import sys
        deps['python'] = sys.version_info >= (3, 8)
        print_step(f"Python {sys.version.split()[0]}", "ok" if deps['python'] else "error")
    except Exception:
        deps['python'] = False
        print_step("Python", "error")
    
    # MCP SDK
    try:
        import mcp
        deps['mcp'] = True
        print_step("MCP SDK", "ok")
    except ImportError:
        deps['mcp'] = False
        print_step("MCP SDK (pip install mcp)", "error")
    
    # Sentence Transformers
    try:
        import sentence_transformers
        deps['sentence_transformers'] = True
        print_step("Sentence Transformers", "ok")
    except ImportError:
        deps['sentence_transformers'] = False
        print_step("Sentence Transformers (busca semântica)", "warn")
    
    # Watchdog
    try:
        import watchdog
        deps['watchdog'] = True
        print_step("Watchdog", "ok")
    except ImportError:
        deps['watchdog'] = False
        print_step("Watchdog (auto-indexação)", "warn")
    
    # NumPy
    try:
        import numpy
        deps['numpy'] = True
        print_step("NumPy", "ok")
    except ImportError:
        deps['numpy'] = False
        print_step("NumPy", "warn")
    
    return deps

def install_dependencies(missing_deps: List[str]) -> bool:
    """Instala dependências em falta"""
    if not missing_deps:
        return True
        
    print_header("Instalando Dependências")
    
    try:
        # Instala requirements_enhanced.txt se existir
        req_file = CURRENT_DIR / "requirements_enhanced.txt"
        if req_file.exists():
            print_step("Instalando via requirements_enhanced.txt")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(req_file)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print_step("Dependências instaladas", "ok")
                return True
            else:
                print_step(f"Erro na instalação: {result.stderr}", "error")
                return False
        else:
            # Instala pacotes individualmente
            packages = []
            if "sentence_transformers" in missing_deps:
                packages.append("sentence-transformers>=2.0.0")
            if "watchdog" in missing_deps:
                packages.append("watchdog>=3.0.0")
            if "numpy" in missing_deps:
                packages.append("numpy>=1.21.0")
            if "scikit_learn" in missing_deps:
                packages.append("scikit-learn>=1.0.0")
                
            if packages:
                print_step("Instalando pacotes individualmente")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install"] + packages,
                    capture_output=True, text=True
                )
                
                if result.returncode == 0:
                    print_step("Dependências instaladas", "ok")
                    return True
                else:
                    print_step(f"Erro na instalação: {result.stderr}", "error")
                    return False
            else:
                print_step("Nenhum pacote para instalar", "ok")
                return True
                
    except Exception as e:
        print_step(f"Erro ao instalar dependências: {e}", "error")
        return False

def setup_index_directory():
    """Configura o diretório de índice"""
    print_header("Configurando Diretório de Índice")
    
    try:
        index_dir = CURRENT_DIR / ".mcp_index"
        index_dir.mkdir(exist_ok=True)
        print_step(f"Diretório de índice criado: {index_dir}", "ok")
        return True
    except Exception as e:
        print_step(f"Erro ao criar diretório de índice: {e}", "error")
        return False

def test_basic_functionality():
    """Testa funcionalidade básica do MCP"""
    print_header("Testando Funcionalidade Básica")
    
    try:
        # Testar importação dos módulos principais
        from code_indexer_enhanced_bkp import BaseCodeIndexer
        print_step("Importação do indexador básico", "ok")
        
        # Testar criação do indexador
        index_dir = CURRENT_DIR / ".mcp_index"
        indexer = BaseCodeIndexer(index_dir=str(index_dir))
        print_step("Criação do indexador", "ok")
        
        # Testar métodos básicos
        stats = indexer.get_stats()
        print_step("Obtenção de estatísticas", "ok")
        
        print_step("Testes básicos concluídos com sucesso", "ok")
        return True
        
    except Exception as e:
        print_step(f"Erro nos testes básicos: {e}", "error")
        return False

def main():
    """Função principal de setup"""
    print_header("Setup Automático do Sistema MCP")
    
    # Verificar dependências
    deps = check_dependencies()
    missing_deps = [dep for dep, available in deps.items() if not available]
    
    if missing_deps:
        print(f"\nDependências em falta: {', '.join(missing_deps)}")
        install = input("\nDeseja instalar as dependências em falta? (s/n): ").lower().strip()
        if install == 's':
            if not install_dependencies(missing_deps):
                print("Falha na instalação de dependências. Saindo.")
                return 1
        else:
            print("Instalação de dependências cancelada.")
    else:
        print("\n✅ Todas as dependências estão instaladas!")
    
    # Configurar diretório de índice
    if not setup_index_directory():
        print("Falha na configuração do diretório de índice. Saindo.")
        return 1
    
    # Testar funcionalidade básica
    if not test_basic_functionality():
        print("Falha nos testes básicos. Saindo.")
        return 1
    
    print_header("Setup Concluído com Sucesso!")
    print("O sistema MCP está pronto para uso.")
    print(f"O diretório de índice está localizado em: {CURRENT_DIR / '.mcp_index'}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())