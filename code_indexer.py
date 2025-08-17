import os
import numpy as np
import faiss
from datetime import datetime
from typing import List, Dict, Tuple, Generator
from src.utils.embeddings import embedding_model
from src.utils.search_cache import search_cache

# ==========================
# Configurações
# ==========================
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

# ==========================
# Funções de chunking
# ==========================

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Divide um texto em chunks sobrepostos.
    
    Args:
        text: Texto a ser dividido
        chunk_size: Tamanho de cada chunk em caracteres
        overlap: Sobreposição entre chunks em caracteres
        
    Returns:
        Lista de chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        
        # Se chegamos ao final, saímos
        if end == len(text):
            break
            
        # Avançamos com sobreposição
        start = end - overlap
        # Garantir que não fiquemos em loop
        if start >= len(text):
            break
    
    return chunks

def get_chunk_id(file_path: str, chunk_index: int) -> str:
    """Gera um ID único para um chunk"""
    return f"{file_path}#chunk_{chunk_index}"

# ==========================
# Funções de integração com MCP / IDE
# ==========================

def embed_code_via_agent(snippet: str):
    """
    Gera embedding usando o modelo SentenceTransformer.
    """
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

# ==========================
# Indexação com chunking
# ==========================
def index_code(file_path: str):
    # Invalidar cache para este arquivo
    search_cache.invalidate_file(file_path)
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        print(f"[INDEXER] Falha ao ler {file_path}: {e}")
        return False

    # Dividir em chunks
    chunks = chunk_text(content)
    
    # Indexar cada chunk
    for i, chunk in enumerate(chunks):
        chunk_id = get_chunk_id(file_path, i)
        
        # Gerar embedding para o chunk
        vector = embed_code_via_agent(chunk)
        index.add(np.array([vector]))
        
        # Armazenar o chunk e seus metadados
        embedding_store[chunk_id] = chunk
        chunk_metadata[chunk_id] = {
            "file_path": file_path,
            "chunk_index": i,
            "char_start": i * (CHUNK_SIZE - CHUNK_OVERLAP) if i > 0 else 0,
            "char_end": i * (CHUNK_SIZE - CHUNK_OVERLAP) + len(chunk) if i > 0 else len(chunk)
        }
    
    # Store timestamp para o arquivo (não para chunks individuais)
    timestamp_store[file_path] = datetime.now()

    # Resumo para memória (do arquivo completo)
    summary = summarize_code_via_agent(content)
    memory_store[file_path] = summary
    print(f"[INDEXER] {file_path} indexado em {len(chunks)} chunks e resumido")
    return True

# ==========================
# Busca semântica com priorização por recência
# ==========================
def get_recency_score(file_path: str, max_age_hours: int = 336) -> float:
    """
    Calcula um score de recência baseado na data de modificação do arquivo.
    max_age_hours: idade máxima em horas para considerar recência (padrão: 2 semanas)
    Retorna um valor entre 0 (antigo) e 1 (muito recente).
    """
    if file_path not in timestamp_store:
        return 0.0
    
    file_time = timestamp_store[file_path]
    now = datetime.now()
    age_hours = (now - file_time).total_seconds() / 3600
    
    # Normaliza para um score entre 0 e 1
    if age_hours >= max_age_hours:
        return 0.0
    return 1.0 - (age_hours / max_age_hours)

def search_code(query: str, top_k: int = 3, recency_weight: float = 0.3):
    """
    Busca código semanticamente relevante, com opção de priorizar arquivos recentes.
    
    Args:
        query: Texto de busca
        top_k: Número de resultados
        recency_weight: Peso dado à recência (0.0 = apenas semântica, 1.0 = apenas recência)
    """
    # Verificar cache primeiro
    cached_results = search_cache.get(
        query=query,
        top_k=top_k,
        recency_weight=recency_weight
    )
    
    if cached_results is not None:
        print(f"[CACHE] Resultados em cache encontrados para: {query}")
        return cached_results
    
    if len(embedding_store) == 0:
        return []

    q_vector = embed_code_via_agent(query)
    distances, indices = index.search(np.array([q_vector]), min(len(embedding_store), top_k * 3))
    
    # Calcular scores combinados
    chunk_ids = list(embedding_store.keys())
    scored_results = []
    
    # Agrupar resultados por arquivo para evitar repetições
    file_results = {}
    
    for i, idx in enumerate(indices[0]):
        if idx == -1 or i >= len(chunk_ids):
            continue
        chunk_id = chunk_ids[idx]
        
        if chunk_id not in chunk_metadata:
            continue
            
        metadata = chunk_metadata[chunk_id]
        file_path = metadata["file_path"]
        
        # Score semântico (menor distância = melhor)
        semantic_score = 1.0 / (1.0 + distances[0][i]) if distances[0][i] > 0 else 1.0
        
        # Score de recência
        recency_score = get_recency_score(file_path)
        
        # Score combinado
        combined_score = (1 - recency_weight) * semantic_score + recency_weight * recency_score
        
        # Se já temos resultados para este arquivo, atualizar se este for melhor
        if file_path in file_results:
            if combined_score > file_results[file_path]["combined_score"]:
                file_results[file_path] = {
                    "chunk_id": chunk_id,
                    "file": file_path,
                    "content": embedding_store[chunk_id],
                    "summary": memory_store.get(file_path, ""),
                    "timestamp": timestamp_store.get(file_path),
                    "semantic_score": semantic_score,
                    "recency_score": recency_score,
                    "combined_score": combined_score,
                    "chunk_metadata": metadata
                }
        else:
            file_results[file_path] = {
                "chunk_id": chunk_id,
                "file": file_path,
                "content": embedding_store[chunk_id],
                "summary": memory_store.get(file_path, ""),
                "timestamp": timestamp_store.get(file_path),
                "semantic_score": semantic_score,
                "recency_score": recency_score,
                "combined_score": combined_score,
                "chunk_metadata": metadata
            }
    
    # Converter para lista e ordenar por score combinado
    scored_results = list(file_results.values())
    scored_results.sort(key=lambda x: x["combined_score"], reverse=True)
    
    # Retornar top_k resultados
    results = scored_results[:top_k]
    
    # Armazenar no cache
    search_cache.put(
        query=query,
        results=results,
        top_k=top_k,
        recency_weight=recency_weight
    )
    
    return results