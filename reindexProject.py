import os
from code_indexer import index_code

# ==========================
# Configurações
# ==========================
PROJECT_PATH = "./"  # raiz do projeto
EXTENSIONS = (".py", ".js", ".ts", ".rb", ".java")  # extensões que deseja indexar
IGNORE_DIRS = {".git", "node_modules", "build", "__pycache__"}  # pastas a ignorar

# ==========================
# Função para reindexar
# ==========================
def reindex_project(path=PROJECT_PATH):
    print(f"[REINDEX] Iniciando reindexação do projeto em: {os.path.abspath(path)}")
    total_files = 0
    for root, dirs, files in os.walk(path):
        # Ignorar pastas não desejadas
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if file.endswith(EXTENSIONS):
                file_path = os.path.join(root, file)
                if index_code(file_path):
                    total_files += 1

    print(f"[REINDEX] Reindexação completa! Total de arquivos indexados: {total_files}")

# ==========================
# Executa script
# ==========================
if __name__ == "__main__":
    reindex_project()