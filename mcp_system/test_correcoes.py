#!/usr/bin/env python3
"""
Script de teste para verificar correções no sistema MCP
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from code_indexer_enhanced import build_context_pack, BaseCodeIndexer
    print('✅ Importação do indexador funcionando')
    
    # Verificar orçamento padrão
    if build_context_pack.__defaults__:
        print(f'✅ Orçamento padrão: {build_context_pack.__defaults__[0]} tokens')
        print(f'✅ Max chunks padrão: {build_context_pack.__defaults__[1]} chunks')
    else:
        print('⚠️  Não foi possível verificar orçamento padrão')
    
    # Testar criação de indexador
    indexer = BaseCodeIndexer()
    print('✅ Criação de indexador base funcionando')
    
    print('\n🎉 Todos os testes básicos passaram!')
    
except Exception as e:
    print(f'❌ Erro no teste: {e}')
    sys.exit(1)