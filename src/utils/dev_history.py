w#!/usr/bin/env python3
"""
Módulo para gerenciamento do histórico de desenvolvimento (dev_history.md)
Segue as regras definidas em .codellm/rules/01-historico_desenvolvimento.mdc
"""
import os
import hashlib
import subprocess
from datetime import datetime
from typing import Dict, Optional, List


class DevHistoryManager:
    """Gerencia atualizações automáticas do arquivo dev_history.md seguindo as regras padronizadas"""
    
    def __init__(self, project_root: str = ".", history_file: str = "dev_history.md"):
        self.project_root = project_root
        self.history_file = history_file
        self.ignored_dirs = {".git", "__pycache__", "venv", "node_modules", "build", "dist", ".pytest_cache"}
        self.ignored_files = {"*.pyc", "*.tmp", "*.bak", "*.pkl", "*.onnx", "*.pt"}
    
    def _get_current_date(self) -> str:
        """Obtém a data atual no formato YYYY-MM-DD conforme as regras"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def _create_entry_hash(self, entry_content: str) -> str:
        """Cria um hash para uma entrada para evitar duplicatas"""
        # Remove espaços e quebras de linha para comparação mais robusta
        normalized = entry_content.strip().replace('\n', '').replace(' ', '')
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()[:8]  # 8 caracteres suficientes
    
    def _entry_exists(self, entry_content: str) -> bool:
        """Verifica se uma entrada similar já existe no histórico"""
        history_path = os.path.join(self.project_root, self.history_file)
        if not os.path.exists(history_path):
            return False
            
        entry_hash = self._create_entry_hash(entry_content)
        
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Procura pelo hash na linha de observações
                return f"Hash: {entry_hash}" in content
        except Exception:
            return False
    
    def _validate_action_type(self, action_type: str) -> str:
        """Valida e normaliza o tipo de ação conforme as regras"""
        valid_types = ["Correção", "Melhoria", "Refatoração", "Bug", "Documentação", "Configuração", "Teste"]
        
        # Normaliza capitalização
        action_type = action_type.strip().capitalize()
        
        # Mapeia variações comuns
        mappings = {
            "Fix": "Correção",
            "Bugfix": "Bug", 
            "Feature": "Melhoria",
            "Refactor": "Refatoração",
            "Docs": "Documentação",
            "Config": "Configuração",
            "Test": "Teste",
            "Tests": "Teste"
        }
        
        action_type = mappings.get(action_type, action_type)
        
        if action_type not in valid_types:
            return "Melhoria"  # Default seguro
            
        return action_type
    
    def _format_file_paths(self, file_paths: List[str]) -> str:
        """Formata lista de arquivos conforme as regras (paths relativos à raiz)"""
        formatted_paths = []
        for file_path in file_paths:
            rel_path = os.path.relpath(file_path, self.project_root)
            # Remove ./ do início se presente
            if rel_path.startswith('./'):
                rel_path = rel_path[2:]
            formatted_paths.append(rel_path)
        
        return ", ".join(formatted_paths)
    
    def update_history(self, file_paths: List[str], action_type: str, description: str, 
                      details: Optional[Dict[str, str]] = None, author: str = "Assistant") -> bool:
        """
        Atualiza o arquivo dev_history.md com uma nova entrada seguindo as regras padronizadas.
        
        Args:
            file_paths: Lista de caminhos dos arquivos modificados
            action_type: Tipo de ação (Correção, Melhoria, Refatoração, Bug, Documentação, Configuração, Teste)
            description: Descrição breve da alteração (máximo 2 linhas)
            details: Detalhes adicionais com chaves: Problema, Causa, Solução, Observações
            author: Nome do autor (padrão: "Assistant")
            
        Returns:
            bool: True se a entrada foi adicionada, False se já existia
        """
        if not file_paths:
            return False
            
        # Valores padrão para detalhes se não fornecidos
        if details is None:
            details = {
                "Problema": "Atualização necessária no código",
                "Causa": "Modificação detectada durante desenvolvimento",
                "Solução": "Implementação da alteração solicitada",
                "Observações": "Entrada gerada automaticamente"
            }
        
        # Garante que todas as chaves necessárias existem
        required_keys = ["Problema", "Causa", "Solução", "Observações"]
        for key in required_keys:
            if key not in details:
                details[key] = f"{key} não especificado"
        
        try:
            # Formata dados conforme template das regras
            date_str = self._get_current_date()
            action_type = self._validate_action_type(action_type)
            formatted_files = self._format_file_paths(file_paths)
            
            # Limita descrição a 2 linhas conforme regras
            description_lines = description.strip().split('\n')[:2]
            description = '\n'.join(description_lines).strip()
            
            # Cria hash para evitar duplicatas
            content_for_hash = f"{formatted_files}{action_type}{description}"
            entry_hash = self._create_entry_hash(content_for_hash)
            
            # Template exato conforme as regras
            entry = f"""[{date_str}] - {author}
Arquivos: {formatted_files}
Ação/Tipo: {action_type}
Descrição: {description}
Detalhes:
Problema: {details["Problema"]}
Causa: {details["Causa"]}
Solução: {details["Solução"]}
Observações: {details["Observações"]} (Hash: {entry_hash})

"""
            
            # Verifica se a entrada já existe
            if self._entry_exists(content_for_hash):
                return False  # Entrada já existe, não adiciona duplicata
            
            # Adiciona ao arquivo de histórico
            history_path = os.path.join(self.project_root, self.history_file)
            
            # Cria arquivo se não existir
            if not os.path.exists(history_path):
                with open(history_path, "w", encoding="utf-8") as f:
                    f.write("# Histórico de Desenvolvimento\n\n")
            
            # Adiciona entrada ao final
            with open(history_path, "a", encoding="utf-8") as f:
                f.write(entry)
                
            return True
            
        except Exception as e:
            # Em caso de erro, não interfere no funcionamento
            return False
    
    def should_track_file(self, file_path: str) -> bool:
        """
        Verifica se um arquivo deve ser rastreado conforme as regras de escopo.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            bool: True se o arquivo deve ser rastreado, False caso contrário
        """
        rel_path = os.path.relpath(file_path, self.project_root)
        
        # ❌ NÃO documentar conforme regras
        ignored_patterns = [
            "__pycache__", ".pyc", ".tmp", ".bak", 
            ".vscode", ".idea", "dist/", "build/",
            "node_modules", ".git", "legacy/", "old_version/"
        ]
        
        if any(pattern in rel_path for pattern in ignored_patterns):
            return False
        
        # ✅ SEMPRE documentar conforme regras
        track_patterns = [
            "src/", "app/", "lib/", "tests/", "test_",
            "requirements.txt", "pyproject.toml", "package.json",
            "config/", ".env.example", "database/migrations/"
        ]
        
        # Extensões de código
        code_extensions = (".py", ".js", ".ts", ".tsx", ".rb", ".java", ".cpp", ".c", ".cs", ".go", ".rs")
        
        # Verifica se deve ser rastreado
        should_track = (
            any(pattern in rel_path for pattern in track_patterns) or
            file_path.endswith(code_extensions) or
            rel_path in ["main.py", "app.py", "index.js", "README.md"]
        )
        
        return should_track
    
    def bulk_update(self, changes: List[Dict]) -> int:
        """
        Atualiza múltiplas entradas de uma vez.
        
        Args:
            changes: Lista de dicionários com chaves: files, action, description, details
            
        Returns:
            int: Número de entradas adicionadas
        """
        added_count = 0
        for change in changes:
            if self.update_history(
                file_paths=change.get("files", []),
                action_type=change.get("action", "Melhoria"),
                description=change.get("description", "Alteração no código"),
                details=change.get("details")
            ):
                added_count += 1
        return added_count


# Instância singleton para uso global
dev_history_manager = DevHistoryManager()


# Funções de conveniência para uso direto
def log_change(file_path: str, action: str, description: str, **details):
    """Função de conveniência para registrar uma mudança simples"""
    return dev_history_manager.update_history([file_path], action, description, details)


def log_multiple_changes(file_paths: List[str], action: str, description: str, **details):
    """Função de conveniência para registrar mudanças em múltiplos arquivos"""
    return dev_history_manager.update_history(file_paths, action, description, details)