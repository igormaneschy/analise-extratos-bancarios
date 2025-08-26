# code_indexer_enhanced.py
# Sistema MCP melhorado com busca híbrida, auto-indexação e cache inteligente
from __future__ import annotations
import os, re, json, math, time, hashlib, threading, csv, datetime as dt
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pathlib

#logs para métricas

# Diretório atual deste módulo para resoluções relativas ao pacote mcp_system
CURRENT_DIR = pathlib.Path(__file__).parent.absolute()

# CSV padrão para métricas de context_pack (consultas)
# Mantém compatibilidade via env MCP_METRICS_FILE, mas por padrão separa em metrics_context.csv
METRICS_PATH = os.environ.get("MCP_METRICS_FILE", str(CURRENT_DIR / ".mcp_index/metrics_context.csv"))

def _log_metrics(row: dict):
    """Append de uma linha de métricas em CSV."""
    os.makedirs(os.path.dirname(METRICS_PATH), exist_ok=True)
    file_exists = os.path.exists(METRICS_PATH)
    with open(METRICS_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            w.writeheader()
        w.writerow(row)

# Tenta importar recursos avançados
HAS_ENHANCED_FEATURES = True
try:
    from .embeddings.semantic_search import SemanticSearchEngine
    from .utils.file_watcher import create_file_watcher
except ImportError:
    HAS_ENHANCED_FEATURES = False
    SemanticSearchEngine = None
    create_file_watcher = None

# ========== CONSTANTES E UTILITÁRIOS BASE ==========

LANG_EXTS = {
    ".py", ".pyi",
    ".js", ".jsx", ".ts", ".tsx",
    ".java", ".go", ".rb", ".php",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rs", ".m", ".mm", ".swift", ".kt", ".kts",
    ".sql", ".sh", ".bash", ".zsh", ".ps1", ".psm1",
}

DEFAULT_INCLUDE = [
    "**/*.py","**/*.js","**/*.ts","**/*.tsx","**/*.jsx","**/*.java",
    "**/*.go","**/*.rb","**/*.php","**/*.c","**/*.cpp","**/*.cs",
    "**/*.rs","**/*.swift","**/*.kt","**/*.kts","**/*.sql","**/*.sh"
]
DEFAULT_EXCLUDE = [
    "**/.git/**","**/node_modules/**","**/dist/**","**/build/**",
    "**/.venv/**","**/__pycache__/**"
]

TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z_0-9]{1,}|[A-Za-z]{2,}")

def now_ts() -> float:
    return time.time()

def tokenize(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_PATTERN.findall(text)]

def est_tokens(text: str) -> int:
    # rough heuristic: ~4 chars per token
    return max(1, int(len(text) / 4))

def hash_id(s: str) -> str:
    return hashlib.blake2s(s.encode("utf-8"), digest_size=12).hexdigest()

# ========== INDEXADOR BASE ==========

class BaseCodeIndexer:
    def __init__(self, index_dir: str = str(CURRENT_DIR / ".mcp_index"), repo_root: str = str(CURRENT_DIR.parent)) -> None:
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.repo_root = Path(repo_root)
        self.chunks: Dict[str, Dict] = {}             # chunk_id -> data
        self.inverted: Dict[str, Dict[str, int]] = {} # term -> {chunk_id: tf}
        self.doc_len: Dict[str, int] = {}             # chunk_id -> token count
        self.file_mtime: Dict[str, float] = {}        # file_path -> mtime
        self._load()

    # ---------- persistence ----------
    def _paths(self):
        return (
            self.index_dir / "chunks.jsonl",
            self.index_dir / "inverted.json",
            self.index_dir / "doclen.json",
            self.index_dir / "file_mtime.json",
        )

    def _load(self):
        chunks_p, inv_p, dl_p, mt_p = self._paths()
        if chunks_p.exists():
            with chunks_p.open("r", encoding="utf-8") as f:
                for line in f:
                    obj = json.loads(line)
                    self.chunks[obj["chunk_id"]] = obj
        if inv_p.exists():
            self.inverted = json.loads(inv_p.read_text(encoding="utf-8"))
        if dl_p.exists():
            self.doc_len = {k:int(v) for k,v in json.loads(dl_p.read_text(encoding="utf-8")).items()}
        if mt_p.exists():
            self.file_mtime = {k:float(v) for k,v in json.loads(mt_p.read_text(encoding="utf-8")).items()}

    def _save(self):
        chunks_p, inv_p, dl_p, mt_p = self._paths()
        with chunks_p.open("w", encoding="utf-8") as f:
            for c in self.chunks.values():
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        inv_p.write_text(json.dumps(self.inverted), encoding="utf-8")
        dl_p.write_text(json.dumps(self.doc_len), encoding="utf-8")
        mt_p.write_text(json.dumps(self.file_mtime), encoding="utf-8")

    # ---------- métricas e estatísticas ----------
    def get_stats(self) -> Dict[str, Any]:
        try:
            index_size_bytes = sum(len(json.dumps(c)) for c in self.chunks.values())
        except Exception:
            index_size_bytes = 0
        return {
            "total_chunks": len(self.chunks),
            "total_files": len(set(c.get("file_path") for c in self.chunks.values())),
            "index_size_mb": round(index_size_bytes / (1024 * 1024), 3),
        }

    # ---------- chunking ----------
    def _read_text(self, path: Path) -> Optional[str]:
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            try:
                return path.read_text(errors="ignore")
            except Exception:
                return None

    def _split_chunks(self, path: Path, text: str, max_lines: int = 80, overlap: int = 12) -> List[Tuple[int,int,str]]:
        """
        Heuristic chunking: break at def/class for Python; else line windows with overlap.
        Returns list of (start_line, end_line, content)
        """
        lines = text.splitlines()
        boundaries = set()
        if path.suffix == ".py":
            for i, ln in enumerate(lines):
                if ln.lstrip().startswith("def ") or ln.lstrip().startswith("class "):
                    boundaries.add(i)
        boundaries.add(0)
        i = 0
        while i < len(lines):
            boundaries.add(i)
            i += max_lines - overlap
        sorted_bounds = sorted(boundaries)
        chunks = []
        for i in range(len(sorted_bounds)):
            start = sorted_bounds[i]
            end = min(len(lines), start + max_lines)
            content = "\n".join(lines[start:end])
            if content.strip():
                chunks.append((start+1, end, content))
        return chunks

    def _index_file(self, file_path: Path) -> Tuple[int,int]:
        text = self._read_text(file_path)
        if text is None:
            return (0,0)
        mtime = file_path.stat().st_mtime
        # Salvar path relativo ao repo_root para estabilidade
        try:
            rel_path = file_path.resolve().relative_to(self.repo_root.resolve())
        except Exception:
            rel_path = file_path.name
        self.file_mtime[str(rel_path)] = mtime

        chunks = self._split_chunks(file_path, text)
        new_chunks = 0
        new_tokens = 0
        for (start, end, content) in chunks:
            chunk_key = f"{rel_path}|{start}|{end}|{mtime}"
            cid = hash_id(chunk_key)
            toks = tokenize(content)
            if not toks:
                continue
            self.chunks[cid] = {
                "chunk_id": cid,
                "file_path": str(rel_path),
                "start_line": start,
                "end_line": end,
                "content": content,
                "mtime": mtime,
                "terms": toks[:2000],
            }
            self.doc_len[cid] = len(toks)
            new_chunks += 1
            new_tokens += len(toks)
        self._rebuild_inverted()
        return (new_chunks, new_tokens)

    def _rebuild_inverted(self):
        inverted: Dict[str, Dict[str,int]] = {}
        for cid, c in self.chunks.items():
            seen = {}
            for t in c["terms"]:
                seen[t] = seen.get(t, 0) + 1
            for t, tf in seen.items():
                inverted.setdefault(t, {})[cid] = tf
        self.inverted = inverted
        self._save()

# ========== FUNÇÕES DE INDEXAÇÃO ==========

def index_repo_paths(
    indexer: BaseCodeIndexer,
    paths: List[str],
    recursive: bool = True,
    include_globs: List[str] = None,
    exclude_globs: List[str] = None
) -> Dict[str,int]:
    include = include_globs or DEFAULT_INCLUDE
    exclude = set(exclude_globs or DEFAULT_EXCLUDE)
    files_indexed = 0
    total_chunks = 0

    for p in paths:
        pth = Path(p)
        if not pth.is_absolute():
            pth = (indexer.repo_root / pth).resolve()
        if pth.is_file():
            if any(pth.match(gl) for gl in include) and not any(pth.match(gl) for gl in exclude):
                c, _ = indexer._index_file(pth)
                files_indexed += 1 if c > 0 else 0
                total_chunks += c
        elif pth.is_dir():
            base = pth
            # Atenção: rglob/glob invertidos — para recursivo usar rglob
            for gl in include:
                iter_paths = base.rglob(gl) if recursive else base.glob(gl)
                for fp in iter_paths:
                    if any(fp.match(eg) for eg in exclude):
                        continue
                    if not fp.is_file():
                        continue
                    c, _ = indexer._index_file(fp)
                    files_indexed += 1 if c > 0 else 0
                    total_chunks += c
        else:
            # caminho inexistente: ignora
            pass

    indexer._save()
    return {"files_indexed": files_indexed, "chunks": total_chunks}

# ========== FUNÇÕES DE BUSCA BM25 ==========

def _bm25_scores(indexer: BaseCodeIndexer, query_tokens: List[str], k1: float = 1.5, b: float = 0.75) -> Dict[str, float]:
    N = max(1, len(indexer.chunks))
    avgdl = max(1, sum(indexer.doc_len.values()) / len(indexer.doc_len)) if indexer.doc_len else 1
    scores: Dict[str, float] = {}

    # df / idf
    unique_q = set(query_tokens)
    df = {t: len(indexer.inverted.get(t, {})) for t in unique_q}
    idf = {t: math.log((N - df.get(t, 0) + 0.5) / (df.get(t, 0) + 0.5) + 1) for t in unique_q}

    for t in query_tokens:
        postings = indexer.inverted.get(t, {})
        for cid, tf in postings.items():
            dl = indexer.doc_len.get(cid, 1)
            denom = tf + k1 * (1 - b + b * (dl / avgdl))
            s = idf[t] * (tf * (k1 + 1)) / denom
            scores[cid] = scores.get(cid, 0.0) + s
    return scores

def _recency_boost(indexer: BaseCodeIndexer, cids: List[str], half_life_days: float = 30.0) -> Dict[str, float]:
    now = now_ts()
    boosts = {}
    for cid in cids:
        c = indexer.chunks.get(cid)
        if not c:
            continue
        age_days = max(0.0, (now - float(c.get("mtime", now))) / 86400.0)
        # meia-vida: 30 dias => score cai pela metade a cada 30 dias
        boosts[cid] = 0.5 ** (age_days / half_life_days)
    return boosts

def _normalize(scores: Dict[str, float]) -> Dict[str, float]:
    if not scores:
        return {}
    mx = max(scores.values())
    if mx <= 0:
        return {k: 0.0 for k in scores}
    return {k: v / mx for k, v in scores.items()}

def _similarity(a_tokens: List[str], b_tokens: List[str]) -> float:
    if not a_tokens or not b_tokens:
        return 0.0
    sa, sb = set(a_tokens), set(b_tokens)
    inter = len(sa & sb)
    uni = len(sa | sb)
    return inter / max(1, uni)

def _mmr_select(indexer: BaseCodeIndexer, candidates: List[str], query_tokens: List[str], k: int = 10, lambda_diverse: float = 0.7) -> List[str]:
    selected: List[str] = []
    candidates = list(candidates)
    while candidates and len(selected) < k:
        best_cid = None
        best_score = -1e9
        for cid in list(candidates):
            rel = _similarity(query_tokens, indexer.chunks[cid]["terms"])
            if not selected:
                div = 0.0
            else:
                div = max(_similarity(indexer.chunks[cid]["terms"], indexer.chunks[sc]["terms"]) for sc in selected)
            mmr = lambda_diverse * rel - (1 - lambda_diverse) * div
            if mmr > best_score:
                best_score = mmr
                best_cid = cid
        if best_cid is None:
            break
        selected.append(best_cid)
        candidates.remove(best_cid)
    return selected

def search_code(indexer: BaseCodeIndexer, query: str, top_k: int = 30, filters: Optional[Dict] = None) -> List[Dict]:
    q_tokens = tokenize(query)
    if not q_tokens:
        return []

    bm25 = _bm25_scores(indexer, q_tokens)
    if not bm25:
        return []

    bm25_norm = _normalize(bm25)
    rec = _recency_boost(indexer, list(bm25.keys()))
    rec_norm = _normalize(rec)

    # combinação simples (80–90% lexical, 10–20% recency)
    combined = {cid: 0.85 * bm25_norm.get(cid, 0.0) + 0.15 * rec_norm.get(cid, 0.0) for cid in bm25}

    # pega mais candidatos primeiro, depois diversifica
    ranked = sorted(combined.items(), key=lambda kv: kv[1], reverse=True)[:max(1, top_k * 3)]
    candidate_ids = [cid for cid, _ in ranked]

    selected = _mmr_select(indexer, candidate_ids, q_tokens, k=min(top_k, len(candidate_ids)), lambda_diverse=0.7)

    results = []
    for cid in selected:
        c = indexer.chunks[cid]
        preview = c["content"].splitlines()[:12]
        results.append({
            "chunk_id": cid,
            "file_path": c["file_path"],
            "start_line": c["start_line"],
            "end_line": c["end_line"],
            "score": combined.get(cid, 0.0),
            "preview": "\n".join(preview),
        })
    return results

# ========== FUNÇÕES DE CONTEXTO ==========

def get_chunk_by_id(indexer: BaseCodeIndexer, chunk_id: str) -> Optional[Dict]:
    return indexer.chunks.get(chunk_id)

def _summarize_chunk(c: Dict, query_tokens: List[str], max_lines: int = 18) -> str:
    """
    Sumariza o chunk pegando linhas que contenham termos da query.
    Se nada casar, usa as primeiras `max_lines` linhas.
    """
    lines = c["content"].splitlines()
    header = f"{c['file_path']}:{c['start_line']}-{c['end_line']}"
    qset = set(query_tokens)

    picked = []
    for ln in lines:
        tks = tokenize(ln)
        if set(tks) & qset:
            picked.append(ln)
        if len(picked) >= max_lines:
            break

    if not picked:
        picked = lines[:max_lines]

    summary = header + "\n" + "\n".join(picked)
    return summary

def build_context_pack(
    indexer: BaseCodeIndexer,
    query: str,
    budget_tokens: int = 2000,  # Reduzido de 3000 para 2000
    max_chunks: int = 5,        # Reduzido de 10 para 5
    strategy: str = "mmr"
) -> Dict:
    """
    Retorna um "pacote de contexto" pronto para injeção no prompt:
      {
        "query": ...,
        "total_tokens": ...,
        "chunks": [
          {
            "chunk_id": ...,
            "header": "path:start-end",
            "summary": "<linhas mais relevantes>",
            "content_snippet": "<trecho comprimido dentro do orçamento>"
          },
          ...
        ]
      }
    """
    t0 = time.perf_counter()  # <-- start para medir latência

    q_tokens = tokenize(query)
    search_res = search_code(indexer, query, top_k=max_chunks * 3)
    ordered_ids = [r["chunk_id"] for r in search_res]

    if strategy == "mmr":
        ordered_ids = _mmr_select(
            indexer,
            ordered_ids,
            q_tokens,
            k=min(max_chunks, len(ordered_ids)),
            lambda_diverse=0.7,
        )
    else:
        ordered_ids = ordered_ids[:max_chunks]

    pack = {"query": query, "total_tokens": 0, "chunks": []}
    remaining = max(1, budget_tokens)

    # Limite máximo por chunk para evitar consumo excessivo
    MAX_TOKENS_PER_CHUNK = min(400, budget_tokens // max(1, max_chunks))

    for cid in ordered_ids:
        c = indexer.chunks[cid]
        header = f"{c['file_path']}:{c['start_line']}-{c['end_line']}"
        summary = _summarize_chunk(c, q_tokens, max_lines=12)  # Reduzido de 18 para 12

        # snippet inicial = summary (já inclui header + linhas relevantes)
        snippet = summary
        est = est_tokens(snippet)

        # Aplicar limite máximo por chunk
        if est > MAX_TOKENS_PER_CHUNK:
            # Poda mais agressiva - corta para caber no limite
            target_chars = MAX_TOKENS_PER_CHUNK * 3  # ~3 chars por token
            if len(snippet) > target_chars:
                snippet = snippet[:target_chars] + "..."
                est = est_tokens(snippet)

        # se não cabe e já temos algo no pack, tenta o próximo
        if est > remaining and pack["chunks"]:
            continue

        # tentativa de poda adicional para caber no orçamento restante
        while est > remaining and "\n" in snippet and len(snippet) > 50:
            lines = snippet.splitlines()
            # Poda mais agressiva - remove 5 linhas por vez
            snippet = "\n".join(lines[:-5]) if len(lines) > 5 else lines[0]
            est = est_tokens(snippet)
            if len(snippet) < 50:
                break

        pack["chunks"].append({
            "chunk_id": cid,
            "header": header,
            "summary": summary,
            "content_snippet": snippet,
            "estimated_tokens": est,  # Adicionar estimativa para debug
        })
        pack["total_tokens"] += est
        remaining = max(0, remaining - est)

        if len(pack["chunks"]) >= max_chunks or remaining <= 50:  # Parar se restam poucos tokens
            break

    # --- LOG MÉTRICAS CSV ---
    try:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        _log_metrics({
            "ts": dt.datetime.utcnow().isoformat(timespec="seconds"),
            "query": query[:160],
            "chunk_count": len(pack["chunks"]),
            "total_tokens": pack["total_tokens"],
            "budget_tokens": budget_tokens,
            "budget_utilization": round(pack["total_tokens"] / max(1, budget_tokens), 3),
            "latency_ms": latency_ms,
        })
    except Exception:
        pass  # não quebra o fluxo se log falhar

    return pack


# ========== INDEXADOR MELHORADO ==========

class EnhancedCodeIndexer:
    """
    Indexador de código melhorado que combina:
    - BM25 search (do indexador original)
    - Busca semântica com embeddings
    - Auto-indexação com file watcher
    - Cache inteligente
    """
    
    def __init__(self, 
                 index_dir: str = ".mcp_index", 
                 repo_root: str = ".",
                 enable_semantic: bool = True,
                 enable_auto_indexing: bool = True,
                 semantic_weight: float = 0.3):
        
        # Inicializa indexador base
        self.base_indexer = BaseCodeIndexer(index_dir=index_dir, repo_root=repo_root)
        
        # Configurações
        self.index_dir = Path(index_dir)
        self.repo_root = Path(repo_root)
        self.enable_semantic = enable_semantic and HAS_ENHANCED_FEATURES
        self.enable_auto_indexing = enable_auto_indexing and HAS_ENHANCED_FEATURES
        self.semantic_weight = semantic_weight
        
        # Inicializa componentes opcionais
        self.semantic_engine = None
        self.file_watcher = None
        
        if self.enable_semantic:
            try:
                self.semantic_engine = SemanticSearchEngine(cache_dir=str(self.index_dir))
                # Mensagem será enviada pelo mcp_server_enhanced.py
            except Exception as e:
                import sys
                sys.stderr.write(f"⚠️  Erro ao inicializar busca semântica: {e}\n")
                self.enable_semantic = False

        if self.enable_auto_indexing:
            try:
                self.file_watcher = create_file_watcher(
                    watch_path=str(self.repo_root),
                    indexer_callback=self._auto_index_callback,
                    debounce_seconds=2.0
                )
                # Mensagem será enviada pelo mcp_server_enhanced.py
            except Exception as e:
                import sys
                sys.stderr.write(f"⚠️  Erro ao inicializar auto-indexação: {e}\n")
                self.enable_auto_indexing = False

        # Lock para thread safety
        self._lock = threading.RLock()

    def _auto_index_callback(self, changed_files: List[Path]) -> Dict[str, Any]:
        """Callback para reindexação automática de arquivos modificados"""
        with self._lock:
            try:
                # Converte paths para strings
                file_paths = [str(f) for f in changed_files]

                # Reindexar usando indexador base
                result = self.index_files(file_paths, show_progress=False)

                # Mensagens de debug via stderr para não interferir com protocolo MCP
                import sys
                sys.stderr.write(f"🔄 Auto-reindexação: {result.get('files_indexed', 0)} arquivos, {result.get('chunks', 0)} chunks\n")

                return result

            except Exception as e:
                import sys
                sys.stderr.write(f"❌ Erro na auto-indexação: {e}\n")
                return {"files_indexed": 0, "chunks": 0, "error": str(e)}

    def index_files(self,
                   paths: List[str],
                   recursive: bool = True,
                   include_globs: List[str] = None,
                   exclude_globs: List[str] = None,
                   show_progress: bool = True) -> Dict[str, Any]:
        """
        Indexa arquivos usando o indexador base
        
        Args:
            paths: Lista de caminhos para indexar
            recursive: Se deve indexar recursivamente
            include_globs: Padrões de arquivos para incluir
            exclude_globs: Padrões de arquivos para excluir
            show_progress: Se deve mostrar progresso
            
        Returns:
            Dicionário com estatísticas da indexação
        """
        with self._lock:
            try:
                if show_progress:
                    import sys
                    sys.stderr.write(f"📁 Indexando {len(paths)} caminhos...\n")
                
                # Usa função de indexação base
                result = index_repo_paths(
                    self.base_indexer,
                    paths=paths,
                    recursive=recursive,
                    include_globs=include_globs,
                    exclude_globs=exclude_globs
                )
                
                if show_progress:
                    import sys
                    sys.stderr.write(f"✅ Indexação concluída: {result.get('files_indexed', 0)} arquivos, {result.get('chunks', 0)} chunks\n")
                
                return result
                
            except Exception as e:
                import sys
                sys.stderr.write(f"❌ Erro na indexação: {e}\n")
                return {"files_indexed": 0, "chunks": 0, "error": str(e)}
    
    def search_code(self, 
                   query: str, 
                   top_k: int = 30, 
                   use_semantic: Optional[bool] = None,
                   semantic_weight: Optional[float] = None,
                   use_mmr: bool = True,
                   filters: Optional[Dict] = None) -> List[Dict]:
        """
        Busca híbrida combinando BM25 e busca semântica
        
        Args:
            query: Consulta de busca
            top_k: Número máximo de resultados
            use_semantic: Se True, usa busca híbrida. Se None, usa configuração padrão
            semantic_weight: Peso da similaridade semântica (sobrescreve padrão)
            filters: Filtros adicionais
            
        Returns:
            Lista de resultados ordenados por relevância
        """
        # Define se usar busca semântica
        use_semantic = use_semantic if use_semantic is not None else self.enable_semantic
        semantic_weight = semantic_weight if semantic_weight is not None else self.semantic_weight
        
        # Busca BM25 base
        bm25_results = []
        try:
            # Usa função de busca base integrada
            bm25_results = search_code(self.base_indexer, query, top_k=top_k * 2, filters=filters)
        except Exception as e:
            import sys
            sys.stderr.write(f"❌ Erro na busca BM25: {e}\n")
            return []
        
        # Se busca semântica não habilitada, retorna apenas BM25
        if not use_semantic or not self.semantic_engine:
            return bm25_results[:top_k]

        # Busca híbrida
        try:
            semantic_results = self.semantic_engine.hybrid_search(
                query=query,
                bm25_results=bm25_results,
                chunk_data=self.base_indexer.chunks,
                semantic_weight=semantic_weight,
                top_k=top_k,
                use_mmr=use_mmr
            )
            return semantic_results
        except Exception as e:
            import sys
            sys.stderr.write(f"⚠️  Erro na busca semântica, usando apenas BM25: {e}\n")
            return bm25_results[:top_k]

    def build_context_pack(self,
                          query: str,
                          budget_tokens: int = 2000,  # Alinhado com servidor
                          max_chunks: int = 5,        # Alinhado com servidor
                          strategy: str = "mmr",
                          use_semantic: Optional[bool] = None) -> Dict:
        """
        Constrói pacote de contexto otimizado

        Args:
            query: Consulta de busca
            budget_tokens: Orçamento máximo de tokens
            max_chunks: Número máximo de chunks
            strategy: Estratégia de seleção ("mmr" ou "topk")
            use_semantic: Se usar busca semântica

        Returns:
            Pacote de contexto formatado
        """
        # Busca chunks relevantes
        search_results = self.search_code(
            query=query,
            top_k=max_chunks * 3,  # Busca mais para melhor seleção
            use_semantic=use_semantic
        )

        # Usa função de construção de contexto base integrada
        try:
            # Simula resultado de busca no formato esperado pela função base
            mock_results = []
            for result in search_results:
                mock_results.append({
                    'chunk_id': result['chunk_id'],
                    'score': result['score']
                })

            # Constrói pack usando função base
            pack = build_context_pack(
                self.base_indexer,
                query=query,
                budget_tokens=budget_tokens,
                max_chunks=max_chunks,
                strategy=strategy
            )

            # Adiciona informações sobre tipo de busca usada
            pack['search_type'] = 'hybrid' if (use_semantic and self.enable_semantic) else 'bm25'
            pack['semantic_enabled'] = self.enable_semantic
            pack['auto_indexing_enabled'] = self.enable_auto_indexing

            return pack

        except Exception as e:
            import sys
            sys.stderr.write(f"❌ Erro ao construir contexto: {e}\n")
            return {"query": query, "total_tokens": 0, "chunks": [], "error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do indexador"""
        return {
            "total_chunks": len(self.base_indexer.chunks),
            "total_files": len(set(c["file_path"] for c in self.base_indexer.chunks.values())),
            "index_size_mb": sum(len(json.dumps(c)) for c in self.base_indexer.chunks.values()) / (1024 * 1024),
            "semantic_enabled": self.enable_semantic,
            "auto_indexing_enabled": self.enable_auto_indexing,
            "has_enhanced_features": HAS_ENHANCED_FEATURES
        }
    
    def start_auto_indexing(self) -> bool:
        """Inicia o file watcher para auto-indexação"""
        if not self.enable_auto_indexing or not self.file_watcher:
            return False
        try:
            self.file_watcher.start()
            return True
        except Exception as e:
            import sys
            sys.stderr.write(f"❌ Erro ao iniciar auto-indexação: {e}\n")
            return False
    
    def stop_auto_indexing(self) -> bool:
        """Para o file watcher"""
        if not self.file_watcher:
            return False
        try:
            self.file_watcher.stop()
            return True
        except Exception as e:
            import sys
            sys.stderr.write(f"❌ Erro ao parar auto-indexação: {e}\n")
            return False

# ========== FUNÇÕES PÚBLICAS PARA COMPATIBILIDADE ==========

def enhanced_index_repo_paths(
    indexer: EnhancedCodeIndexer,
    paths: List[str],
    recursive: bool = True,
    include_globs: List[str] = None,
    exclude_globs: List[str] = None,
    enable_semantic: bool = True  # Adicionado para compatibilidade com o servidor
) -> Dict[str,int]:
    """Wrapper para compatibilidade com API antiga"""
    # O parâmetro enable_semantic não é usado diretamente na indexação,
    # mas é mantido para compatibilidade com a API do servidor
    return indexer.index_files(
        paths=paths,
        recursive=recursive,
        include_globs=include_globs,
        exclude_globs=exclude_globs
    )

def enhanced_search_code(
    indexer: EnhancedCodeIndexer,
    query: str,
    top_k: int = 30,
    filters: Optional[Dict] = None,
    semantic_weight: float = None,
    use_mmr: bool = True
) -> List[Dict]:
    """Wrapper para compatibilidade com API antiga"""
    # Os parâmetros semantic_weight e use_mmr são mantidos para compatibilidade
    # mas podem não ser usados dependendo da implementação do indexer
    return indexer.search_code(query=query, top_k=top_k, filters=filters)

def enhanced_build_context_pack(
    indexer: EnhancedCodeIndexer,
    query: str,
    budget_tokens: int = 2000,  # Alinhado com servidor
    max_chunks: int = 5,        # Alinhado com servidor
    strategy: str = "mmr"
) -> Dict:
    """Wrapper para construir pacote de contexto alinhado com servidor"""
    return indexer.build_context_pack(
        query=query,
        budget_tokens=budget_tokens,
        max_chunks=max_chunks,
        strategy=strategy,
    )

def enhanced_build_context_pack(
    indexer: EnhancedCodeIndexer,
    query: str,
    budget_tokens: int = 3000,
    max_chunks: int = 10,
    strategy: str = "mmr"
) -> Dict:
    """Wrapper para compatibilidade com API antiga"""
    return indexer.build_context_pack(
        query=query,
        budget_tokens=budget_tokens,
        max_chunks=max_chunks,
        strategy=strategy
    )

# Alias para compatibilidade com código existente
CodeIndexer = BaseCodeIndexer