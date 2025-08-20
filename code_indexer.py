import os
import numpy as np
import faiss
from datetime import datetime
from typing import List, Dict, Tuple, Generator
from src.utils.embeddings import embedding_model
from src.utils.search_cache import search_cache

# ====
# Configurações
# ====
# Dimensão dos embeddings (obtida do modelo)
DIM_EMBED = embedding_model.get_embedding_dimension()

# Configurações de chunking
CHUNK_SIZE = 500  # número de caracteres por chunk
CHUNK_OVERLAP = 50  # sobreposição entre chunks

# FAISS store
index = faiss.IndexFlatL2(DIM_EMBED)
embedding_store = {}  # Armazena chunks: {chunk_id: content}
chunk_metadata = {}   # Metadados dos chunks: {chunk_id: {file_path, chunk_index, start_line, end_line}}
timestamp_store = {}  # Store modification timestamps por arquivo

# Memória resumida (simples dict)
memory_store = {}  # Resumo por arquivo

# ====
# Funções de chunking
# ====

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> Generator[Tuple[str, int, int, int], None, None]:
    """
    Divide texto em chunks sobrepostos.
    
    Args:
        text: Texto para dividir
        chunk_size: Tamanho de cada chunk
        overlap: Sobreposição entre chunks
        
    Yields:
        Tupla de (content, chunk_index, start_line, end_line)
    """
    lines = text.split('\n')
    total_lines = len(lines)
    
    for i in range(0, total_lines, chunk_size - overlap):
        chunk_lines = lines[i:i + chunk_size]
        content = '\n'.join(chunk_lines)
        start_line = i + 1  # 1-indexed
        end_line = min(i + chunk_size, total_lines)
        
        if content.strip():  # Só yield chunks não vazios
            yield (content, i // (chunk_size - overlap), start_line, end_line)

def get_chunk_id(file_path: str, chunk_index: int) -> str:
    """Gera um ID único para um chunk"""
    return f"{file_path}#chunk_{chunk_index}"

# ====
# Funções de integração com MCP / IDE
# ====

def embed_code_via_agent(snippet: str):
    """
    Gera embedding usando o modelo SentenceTransformer.
    """
    # Removendo todas as mensagens de impressão que podem interferir no parsing JSON
    return embedding_model.embed_text(snippet)

def summarize_code_via_agent(snippet: str):
    """
    Resume código extraindo informações estruturais.
    """
    lines = snippet.split('\n')
    total_lines = len(lines)
  
    # Extrair comentários
    comments = [line.strip() for line in lines if line.strip().startswith(('#', '//', '/*', '*', '*/'))]
  
    # Extrair definições de funções/classes
    defs = [line.strip() for line in lines if 'def ' in line or 'class ' in line or 'function' in line]
  
    summary = f"Arquivo com {total_lines} linhas"
    if comments:
        summary += f", {len(comments)} comentários"
    if defs:
        summary += f", {len(defs)} definições"
  
    return summary

# ====
# Indexação com chunking
# ====

def index_code(file_path: str):
    """Indexa código de um arquivo com chunking."""
    # Invalidar cache para este arquivo
    search_cache.invalidate_file(file_path)
    
    # Remover embeddings antigos deste arquivo
    chunks_to_remove = [chunk_id for chunk_id in embedding_store.keys() if chunk_id.startswith(f"{file_path}#")]
    for chunk_id in chunks_to_remove:
        if chunk_id in embedding_store:
            del embedding_store[chunk_id]
        if chunk_id in chunk_metadata:
            del chunk_metadata[chunk_id]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return
        
    # Atualizar timestamp
    timestamp_store[file_path] = datetime.now()
    
    # Gerar resumo e armazenar na memória
    memory_store[file_path] = summarize_code_via_agent(content)
    
    # Chunking e indexação
    chunk_embeddings = []
    chunk_ids = []

    for chunk_content, chunk_index, start_line, end_line in chunk_text(content):
        chunk_id = get_chunk_id(file_path, chunk_index)

        # Armazenar conteúdo do chunk
        embedding_store[chunk_id] = chunk_content

        # Armazenar metadados
        chunk_metadata[chunk_id] = {
            "file_path": file_path,
            "chunk_index": chunk_index,
            "start_line": start_line,
            "end_line": end_line
        }

        # Gerar embedding
        embedding = embed_code_via_agent(chunk_content)
        if embedding is not None:
            chunk_embeddings.append(embedding)
            chunk_ids.append(chunk_id)

    # Adicionar embeddings ao índice FAISSa
    if chunk_embeddings:
        embeddings_array = np.array(chunk_embeddings, dtype=np.float32)
        index.add(embeddings_array)

# Função para busca no índice de código

def search_code(query: str, top_k: int = 5, recency_weight: float = 0.5):
    """Busca no índice de código usando embedding da query e peso de recência."""
    query_embedding = embed_code_via_agent(query)
    if query_embedding is None:
        return []

    query_vector = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
    distances, indices = index.search(query_vector, top_k)

    results = []
    now = datetime.now()

    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        chunk_id = list(embedding_store.keys())[idx]
        metadata = chunk_metadata.get(chunk_id, {})
        file_path = metadata.get("file_path", "")
        timestamp = timestamp_store.get(file_path, now)

        age_seconds = (now - timestamp).total_seconds() if isinstance(timestamp, datetime) else 0
        recency_score = 1 / (1 + age_seconds / (3600 * 24))

        score = (1 - dist) * (1 - recency_weight) + recency_score * recency_weight

        result = {
            "chunk_id": chunk_id,
            "file_path": file_path,
            "score": score,
            "content": embedding_store.get(chunk_id, ""),
            "metadata": metadata
        }
        results.append(result)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results