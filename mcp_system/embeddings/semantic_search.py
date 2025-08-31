# embeddings/semantic_search.py
# Engine semântico com fallback TF-IDF + cosine e suporte opcional a sentence-transformers
from __future__ import annotations
from typing import List, Dict, Any, Optional
import math
import os


def _ensure_local_cache(cache_dir: Optional[str]) -> None:
    """Garante caches locais dentro da pasta do servidor MCP.

    - SENTENCE_TRANSFORMERS_HOME: usado pelo SentenceTransformer
    - HF_HOME / HUGGINGFACE_HUB_CACHE: usados pelo huggingface hub
    Se cache_dir não for informado, tenta usar EMBEDDINGS_CACHE_DIR do ambiente.
    """
    if not cache_dir:
        cache_dir = os.environ.get("EMBEDDINGS_CACHE_DIR")
    if not cache_dir:
        return
    try:
        os.makedirs(cache_dir, exist_ok=True)
    except Exception:
        return
    os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", cache_dir)
    os.environ.setdefault("HF_HOME", cache_dir)
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", cache_dir)


class SemanticSearchEngine:
    def __init__(self, cache_dir: Optional[str] = None) -> None:
        self.cache_dir = cache_dir
        _ensure_local_cache(self.cache_dir)
        self._backend = None
        self._use_st = False
        try:
            # Tenta usar sentence-transformers se disponível
            from sentence_transformers import SentenceTransformer, util  # type: ignore
            self._st_model = SentenceTransformer('all-MiniLM-L6-v2')
            self._st_util = util
            self._use_st = True
        except Exception:
            # Fallback leve para TF-IDF
            self._use_st = False
            from collections import Counter
            self._Counter = Counter

    def _embed_st(self, texts: List[str]):
        return self._st_model.encode(texts, convert_to_tensor=True, show_progress_bar=False)

    def _cosine_st(self, a, b):
        return self._st_util.pytorch_cos_sim(a, b)

    def _tfidf_vec(self, texts: List[str]):
        # Implementação mínima TF-IDF para fallback (vetor esparso via dict)
        # Não otimizada, suficiente para repositórios pequenos/médios
        docs = [t.lower().split() for t in texts]
        df = {}
        for doc in docs:
            for term in set(doc):
                df[term] = df.get(term, 0) + 1
        N = len(docs)
        vecs = []
        for doc in docs:
            tf = self._Counter(doc)
            v = {}
            for term, cnt in tf.items():
                idf = math.log((N + 1) / (df.get(term, 1) + 1)) + 1.0
                v[term] = (cnt / len(doc)) * idf
            vecs.append(v)
        return vecs

    def _cosine_sparse(self, a: Dict[str, float], b: Dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        # dot
        dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in set(a.keys()) | set(b.keys()))
        # norms
        na = math.sqrt(sum(v*v for v in a.values()))
        nb = math.sqrt(sum(v*v for v in b.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def hybrid_search(self,
                      query: str,
                      bm25_results: List[Dict[str, Any]],
                      chunk_data: Dict[str, Dict[str, Any]],
                      semantic_weight: float = 0.3,
                      top_k: int = 30,
                      use_mmr: bool = True) -> List[Dict[str, Any]]:
        if not bm25_results:
            return []
        # Limitar universo para re-rank semântico
        candidates = bm25_results[: max(top_k * 4, 40)]
        if self._use_st:
            texts = [query] + [chunk_data[r['chunk_id']]['content'] for r in candidates if r.get('chunk_id') in chunk_data]
            embs = self._embed_st(texts)
            q = embs[0]
            docs = embs[1:]
            sims = self._cosine_st(docs, q)
            sims = sims.squeeze().tolist()
        else:
            texts = [query] + [chunk_data[r['chunk_id']]['content'] for r in candidates if r.get('chunk_id') in chunk_data]
            vecs = self._tfidf_vec(texts)
            qv = vecs[0]
            dvs = vecs[1:]
            sims = [self._cosine_sparse(v, qv) for v in dvs]
        # Combina com BM25
        combined = []
        for i, r in enumerate(candidates):
            sem = float(sims[i]) if i < len(sims) else 0.0
            bm = float(r.get('score', 0.0))
            comb = (1 - semantic_weight) * bm + semantic_weight * sem
            rr = dict(r)
            rr['semantic_score'] = sem
            rr['combined_score'] = comb
            combined.append(rr)
        # Ordena por score combinado
        combined.sort(key=lambda x: x.get('combined_score', 0.0), reverse=True)
        # MMR simples (opcional)
        if use_mmr and len(combined) > top_k:
            selected: List[Dict[str, Any]] = []
            selected_ids = set()
            lambda_div = 0.7
            while combined and len(selected) < top_k:
                best = None
                best_score = -1e9
                for cand in combined:
                    # penaliza duplicatas por chunk_id
                    if cand.get('chunk_id') in selected_ids:
                        continue
                    div_penalty = 0.0  # placeholder (sem embeddings detalhados)
                    score = lambda_div * cand['combined_score'] - (1 - lambda_div) * div_penalty
                    if score > best_score:
                        best = cand
                        best_score = score
                selected.append(best)
                selected_ids.add(best.get('chunk_id'))
                combined.remove(best)
            combined = selected
        return combined[:top_k]
