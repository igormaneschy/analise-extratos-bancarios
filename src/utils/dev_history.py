#!/usr/bin/env python3
"""
Módulo para gerenciamento do histórico de desenvolvimento (dev_history.md)
"""
import os
import hashlib
from datetime import datetime
from typing import Dict, Optional


class DevHistoryManager:
    """Gerencia atualizações automáticas do arquivo dev_history.md"""
    
    def __init__(self, project_root: str = ".", history_file: str = "dev_history.md"):
        self.project_root = project_root
        self.history_file = history_file
        self.ignored_dirs = {".git", "__pycache__", "venv", "node_modules", "build", "dist"}
    
    def _create_entry_hash(self, entry: str) -> str:
        """Cria um hash para uma entrada para evitar duplicatas"""
        return hashlib.md5(entry.encode('utf-8')).hexdigest()
    
    def _entry_exists(self, entry: str) -> bool:
        """Verifica se uma entrada já existe no histórico"""
        history_path = os.path.join(self.project_root, self.history_file)
        if not os.path.exists(history_path):
            return False
            
        entry_hash = self._create_entry_hash(entry)
        
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Verifica se o hash da entrada já existe no arquivo
            # Usamos uma marcação especial para identificar hashes
            hash_marker = f"<!-- HASH:{entry_hash} -->"
            return hash_marker in content
        except Exception:
            return False
    
    def update_history(self, file_path: str, action_type: str, 
                      description: str = "Atualização automática do código.",
                      details: Optional[Dict[str, str]] = None) -> bool:
        """
        Atualiza o arquivo dev_history.md com as alterações feitas no código.
        
        Args:
            file_path: Caminho do arquivo modificado
            action_type: Tipo de ação (Correção, Melhoria, Refatoração, etc.)
            description: Descrição da alteração
            details: Detalhes da alteração (problema, causa, solução, observações)
            
        Returns:
            bool: True se a atualização foi bem-sucedida, False caso contrário
        """
        try:
            # Get relative path from project root
            rel_path = os.path.relpath(file_path, self.project_root)
            
            # Skip if it's in ignored directories
            if any(ignored in rel_path.split(os.sep) for ignored in self.ignored_dirs):
                return False
                
            # Get current date
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Default details if not provided
            if details is None:
                details = {
                    "Problema": "Código modificado mas histórico de desenvolvimento não foi atualizado automaticamente.",
                    "Causa": "Falta de integração entre o MCP e o registro automático de histórico.",
                    "Solução": "Implementação de função para atualizar dev_history.md automaticamente quando arquivos são modificados.",
                    "Observações": "Esta entrada foi gerada automaticamente pelo sistema MCP."
                }
            
            # Create dev history entry
            entry = f"""[{current_date}] - Assistant
Arquivos: {rel_path}
Ação/Tipo: {action_type}
Descrição: {description}
Detalhes:
Problema: {details["Problema"]}
Causa: {details["Causa"]}
Solução: {details["Solução"]}
Observações: {details["Observações"]}

"""
            
            # Verifica se a entrada já existe
            if self._entry_exists(entry):
                return False  # Entrada já existe, não adiciona duplicata
            
            # Adiciona um hash da entrada para detecção futura de duplicatas
            hash_marker = f"<!-- HASH:{self._create_entry_hash(entry)} -->\n"
            entry_with_hash = hash_marker + entry
            
            # Append to dev_history.md
            history_path = os.path.join(self.project_root, self.history_file)
            with open(history_path, "a", encoding="utf-8") as f:
                f.write(entry_with_hash)
                
            print(f"[MCP] dev_history.md atualizado com alterações em {rel_path}")
            return True
        except Exception as e:
            print(f"[MCP] Falha ao atualizar dev_history.md: {e}")
            return False
    
    def should_track_file(self, file_path: str) -> bool:
        """
        Verifica se um arquivo deve ser rastreado para atualização do histórico.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            bool: True se o arquivo deve ser rastreado, False caso contrário
        """
        rel_path = os.path.relpath(file_path, self.project_root)
        
        # Skip if it's in ignored directories
        if any(ignored in rel_path.split(os.sep) for ignored in self.ignored_dirs):
            return False
            
        # Track only code files
        code_extensions = (".py", ".js", ".ts", ".rb", ".java", ".cpp", ".c", ".cs", ".go")
        return file_path.endswith(code_extensions)


# Instância singleton para uso global
dev_history_manager = DevHistoryManager()