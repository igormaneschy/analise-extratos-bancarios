# MCP System - Model Context Protocol
"""
Sistema avançado de indexação e busca de código para desenvolvimento assistido por IA.
Reduz drasticamente o consumo de tokens fornecendo apenas contexto relevante.
"""

__version__ = "1.0.0"
__author__ = "Assistant"

# Importações principais
from .code_indexer_enhanced import (
    EnhancedCodeIndexer,
    BaseCodeIndexer,
    search_code,
    build_context_pack,
    index_repo_paths
)

__all__ = [
    "EnhancedCodeIndexer",
    "BaseCodeIndexer", 
    "search_code",
    "build_context_pack",
    "index_repo_paths"
]