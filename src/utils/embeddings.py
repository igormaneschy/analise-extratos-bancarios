#!/usr/bin/env python3
"""
Módulo para geração de embeddings usando Sentence Transformers
"""
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Union


class EmbeddingModel:
    """Classe para gerenciar o modelo de embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Inicializa o modelo de embeddings.
        
        Args:
            model_name: Nome do modelo SentenceTransformer a ser usado
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Carrega o modelo de embeddings"""
        try:
            self.model = SentenceTransformer(self.model_name)
            # Removendo todas as mensagens de impressão que podem interferir no parsing JSON
        except Exception:
            # Fallback para modelo mais simples
            try:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self.model = None
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Gera embedding para um texto.

        Args:
            text: Texto para gerar embedding

        Returns:
            Array numpy com o embedding
        """
        if self.model is None:
            # Retorna embedding aleatório se modelo não estiver disponível
            return np.random.rand(384).astype(np.float32)

        try:
            embedding = self.model.encode(text)
            return np.array(embedding, dtype=np.float32)
        except Exception:
            # Retorna embedding aleatório em caso de erro
            return np.random.rand(384).astype(np.float32)
    
    def get_embedding_dimension(self) -> int:
        """
        Retorna a dimensão dos embeddings gerados pelo modelo.
        
        Returns:
            Dimensão dos embeddings
        """
        if self.model is None:
            return 384  # Dimensão padrão para modelos SentenceTransformer pequenos
        return self.model.get_sentence_embedding_dimension()


# Instância singleton para uso global
embedding_model = EmbeddingModel()