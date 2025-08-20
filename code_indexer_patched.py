# code_indexer_patched.py
# Lightweight, dependency-free code indexer with BM25-like search + MMR and budgeted context packs.
from __future__ import annotations
import os, re, json, math, time, hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional

LANG_EXTS = {
    ".py",".pyi",
    ".js",".jsx",".ts",".tsx",
    ".java",".go",".rb",".php",
    ".c",".cpp",".h",".hpp",".cs",".rs",".m",".mm",".swift",".kt",".kts",
    ".sql",".sh",".bash",".zsh",".ps1",".psm1",
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

class CodeIndexer:
    def __init__(self, index_dir: str = ".mcp_index", repo_root: str = ".") -> None:
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
        self.file_mtime[str(file_path)] = mtime

        chunks = self._split_chunks(file_path, text)
        new_chunks = 0
        new_tokens = 0
        for (start, end, content) in chunks:
            chunk_key = f"{file_path}|{start}|{end}|{mtime}"
            cid = hash_id(chunk_key)
            toks = tokenize(content)
            if not toks:
                continue
            self.chunks[cid] = {
                "chunk_id": cid,
                "file_path": str(file_path),
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
# -------- Public API: indexação de paths --------

def index_repo_paths(
    indexer: CodeIndexer,
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


# -------- Scoring helpers: BM25, recência, normalização, MMR --------

def _bm25_scores(indexer: CodeIndexer, query_tokens: List[str], k1: float = 1.5, b: float = 0.75) -> Dict[str, float]:
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

def _recency_boost(indexer: CodeIndexer, cids: List[str], half_life_days: float = 30.0) -> Dict[str, float]:
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

def _mmr_select(indexer: CodeIndexer, candidates: List[str], query_tokens: List[str], k: int = 10, lambda_diverse: float = 0.7) -> List[str]:
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


# -------- Busca pública --------

def search_code(indexer: CodeIndexer, query: str, top_k: int = 30, filters: Optional[Dict] = None) -> List[Dict]:
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
# -------- Helpers + Context Pack --------

def get_chunk_by_id(indexer: CodeIndexer, chunk_id: str) -> Optional[Dict]:
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
    indexer: CodeIndexer,
    query: str,
    budget_tokens: int = 3000,
    max_chunks: int = 10,
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
    q_tokens = tokenize(query)
    search_res = search_code(indexer, query, top_k=max_chunks * 3)
    ordered_ids = [r["chunk_id"] for r in search_res]

    if strategy == "mmr":
        ordered_ids = _mmr_select(indexer, ordered_ids, q_tokens, k=min(max_chunks, len(ordered_ids)), lambda_diverse=0.7)
    else:
        ordered_ids = ordered_ids[:max_chunks]

    pack = {"query": query, "total_tokens": 0, "chunks": []}
    remaining = max(1, budget_tokens)

    for cid in ordered_ids:
        c = indexer.chunks[cid]
        header = f"{c['file_path']}:{c['start_line']}-{c['end_line']}"
        summary = _summarize_chunk(c, q_tokens, max_lines=18)

        # snippet inicial = summary (já inclui header + linhas relevantes)
        snippet = summary
        est = est_tokens(snippet)

        # se não cabe e já temos algo no pack, tenta o próximo
        if est > remaining and pack["chunks"]:
            continue

        # tentativa de poda para caber no orçamento
        while est > remaining and "\n" in snippet:
            snippet = "\n".join(snippet.splitlines()[:-3])  # corta 3 linhas por iteração
            est = est_tokens(snippet)
            if len(snippet) < 40:
                break

        pack["chunks"].append({
            "chunk_id": cid,
            "header": header,
            "summary": summary,
            "content_snippet": snippet,
        })
        pack["total_tokens"] += est
        remaining = max(0, remaining - est)

        if len(pack["chunks"]) >= max_chunks or remaining <= 0:
            break

    return pack
