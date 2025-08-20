#!/usr/bin/env python3
"""
Teste rápido do sistema MCP melhorado
Verifica se todas as funcionalidades estão operacionais
"""

import os
import sys
import time
from pathlib import Path

def test_enhanced_system():
    """Testa o sistema MCP melhorado"""
    print("🧪 Testando Sistema MCP Melhorado")
    print("=" * 50)
    
    # 1. Teste de importação
    try:
        print("🔄 Importando módulos...")
        from code_indexer_enhanced import EnhancedCodeIndexer
        print("✅ EnhancedCodeIndexer importado")
        
        from src.embeddings.semantic_search import SemanticSearchEngine
        print("✅ SemanticSearchEngine importado")
        
        from src.utils.file_watcher import create_file_watcher
        print("✅ FileWatcher importado")
        
    except ImportError as e:
        print(f"⚠️  Erro de importação: {e}")
        print("💡 Execute: pip install -r requirements_enhanced.txt")
        return False
    
    # 2. Teste do indexador
    try:
        print("\n🔄 Testando indexador melhorado...")
        indexer = EnhancedCodeIndexer(
            index_dir=".test_mcp_index",
            repo_root=".",
            enable_semantic=True,
            enable_auto_indexing=False  # Não inicia watcher no teste
        )
        
        # Indexa alguns arquivos de teste
        result = indexer.index_files([__file__, "README.md"])
        print(f"✅ Indexados {result.get('files_indexed', 0)} arquivos")
        
        # Teste de busca
        search_results = indexer.search_code("teste sistema", top_k=3)
        print(f"✅ Busca retornou {len(search_results)} resultados")
        
        # Teste de context pack
        context = indexer.build_context_pack("função de teste", budget_tokens=1000)
        print(f"✅ Context pack: {context['total_tokens']} tokens, {len(context['chunks'])} chunks")
        
    except Exception as e:
        print(f"❌ Erro no indexador: {e}")
        return False
    
    # 3. Teste do servidor MCP
    try:
        print("\n🔄 Testando servidor MCP...")
        import mcp_server_enhanced
        
        server = mcp_server_enhanced.EnhancedCompatServer("test")
        tools = server.list_tools()
        print(f"✅ Servidor MCP: {len(tools)} tools disponíveis")
        
        for tool in tools:
            print(f"  • {tool.name}")
            
    except Exception as e:
        print(f"❌ Erro no servidor MCP: {e}")
        return False
    
    # 4. Teste das estatísticas
    try:
        print("\n🔄 Testando estatísticas...")
        stats = indexer.get_comprehensive_stats()
        
        print("✅ Estatísticas coletadas:")
        print(f"  • Chunks: {stats['base_indexer']['chunks_count']}")
        print(f"  • Busca semântica: {stats['semantic_search']['enabled']}")
        print(f"  • Auto-indexação: {stats['auto_indexing']['enabled']}")
        print(f"  • Cache size: {stats['base_indexer']['index_size_mb']} MB")
        
    except Exception as e:
        print(f"⚠️  Erro nas estatísticas: {e}")
    
    # 5. Limpeza
    try:
        print("\n🔄 Limpando arquivos de teste...")
        import shutil
        test_dir = Path(".test_mcp_index")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        print("✅ Limpeza concluída")
        
    except Exception as e:
        print(f"⚠️  Erro na limpeza: {e}")
    
    print("\n🎉 Teste concluído com sucesso!")
    print("\n💡 Para usar o sistema:")
    print("   1. Execute: python scripts/setup_enhanced_mcp.py")
    print("   2. Reinicie seu editor")
    print("   3. Use as MCP tools via Claude/Cursor")
    
    return True

def test_dependencies():
    """Testa dependências necessárias"""
    print("🔍 Verificando Dependências")
    print("-" * 30)
    
    deps = {
        'mcp': 'MCP SDK (obrigatório)',
        'sentence_transformers': 'Busca semântica (opcional)',
        'watchdog': 'Auto-indexação (opcional)', 
        'numpy': 'Embeddings (opcional)'
    }
    
    available = []
    missing = []
    
    for dep, desc in deps.items():
        try:
            __import__(dep)
            print(f"✅ {desc}")
            available.append(dep)
        except ImportError:
            print(f"❌ {desc}")
            missing.append(dep)
    
    if missing:
        print(f"\n⚠️  Dependências em falta: {', '.join(missing)}")
        print("💡 Para instalar: pip install -r requirements_enhanced.txt")
    
    return len(missing) == 0 or 'mcp' not in missing

if __name__ == "__main__":
    print("🚀 Sistema MCP Melhorado - Teste Rápido")
    print("=" * 60)
    
    # Verifica dependências primeiro
    if not test_dependencies():
        print("\n❌ Teste abortado devido a dependências em falta")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    
    # Executa teste principal
    try:
        success = test_enhanced_system()
        if success:
            print("\n✅ Todos os testes passaram!")
            sys.exit(0)
        else:
            print("\n❌ Alguns testes falharam")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste cancelado pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)