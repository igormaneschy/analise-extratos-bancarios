# __init__.py
"""
MCP System - Model Context Protocol
Sistema avançado de indexação e busca de código para desenvolvimento assistido por IA.
"""

# Versão do pacote
__version__ = "1.0.0"

# Importações principais para facilitar o uso do pacote
from .code_indexer_enhanced import (
    BaseCodeIndexer,
    EnhancedCodeIndexer,
    search_code,
    build_context_pack,
    index_repo_paths,
    enhanced_search_code,
    enhanced_build_context_pack,
    enhanced_index_repo_paths
)

# Verificar se recursos avançados estão disponíveis
try:
    from .embeddings.semantic_search import SemanticSearchEngine
    from .utils.file_watcher import create_file_watcher
    HAS_ENHANCED_FEATURES = True
except ImportError:
    HAS_ENHANCED_FEATURES = False

# Expor funcionalidades principais
__all__ = [
    "BaseCodeIndexer",
    "EnhancedCodeIndexer",
    "search_code",
    "build_context_pack",
    "index_repo_paths",
    "enhanced_search_code",
    "enhanced_build_context_pack",
    "enhanced_index_repo_paths",
    "HAS_ENHANCED_FEATURES"
]

# Se recursos avançados estiverem disponíveis, exportá-los também
if HAS_ENHANCED_FEATURES:
    __all__.extend(["SemanticSearchEngine", "create_file_watcher"])