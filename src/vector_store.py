import json
import math
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from src.config import INDEX_DIR, settings

class SimpleCache:
    """In-memory LRU / TTL Cache for queries and embeddings (D7)."""
    def __init__(self, ttl_sec: int = 3600):
        self.ttl_sec = ttl_sec
        self.cache: Dict[str, Tuple[float, Any]] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            ts, val = self.cache[key]
            if time.time() - ts <= self.ttl_sec:
                self.hits += 1
                return val
            del self.cache[key]
        self.misses += 1
        return None

    def set(self, key: str, val: Any):
        self.cache[key] = (time.time(), val)


retrieval_cache = SimpleCache(ttl_sec=settings.CACHE_TTL_SEC)


def tokenize(text: str) -> List[str]:
    return [w for w in re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", text.lower()) if len(w) > 1]


class ClauseChunk:
    def __init__(self, clause_id: str, title: str, category: str, text: str, metadata: Optional[Dict[str, Any]] = None):
        self.clause_id = clause_id
        self.title = title
        self.category = category
        self.text = text
        self.metadata = metadata or {}
        self.tokens = tokenize(f"{clause_id} {title} {text} {category}")


class LocalPolicyIndex:
    """
    Search and retrieval index for Policy clauses & Day-care schedule.
    Supports BM25 lexical scoring + semantic token overlap + clause ID lookup.
    """
    def __init__(self):
        self.chunks: List[ClauseChunk] = []
        self.chunk_by_id: Dict[str, ClauseChunk] = {}
        self.doc_freq: Counter = Counter()
        self.avg_doc_len: float = 0.0
        self.k1 = 1.5
        self.b = 0.75
        self.metadata: Dict[str, Any] = {}
        self.load_index()

    def load_index(self):
        index_file = INDEX_DIR / "corpus_index.json"
        meta_file = INDEX_DIR / "index_metadata.json"
        if not index_file.exists():
            return

        with open(index_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.chunks = []
        self.chunk_by_id = {}
        total_tokens = 0
        df: Counter = Counter()

        for item in data:
            chunk = ClauseChunk(
                clause_id=item["clause_id"],
                title=item["title"],
                category=item["category"],
                text=item["text"],
                metadata=item.get("metadata", {})
            )
            self.chunks.append(chunk)
            self.chunk_by_id[chunk.clause_id] = chunk
            unique_tokens = set(chunk.tokens)
            for t in unique_tokens:
                df[t] += 1
            total_tokens += len(chunk.tokens)

        self.doc_freq = df
        self.avg_doc_len = total_tokens / max(len(self.chunks), 1)

        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

    def lookup_clause(self, clause_id: str) -> Optional[Dict[str, Any]]:
        clean_id = clause_id.strip().upper()
        chunk = self.chunk_by_id.get(clean_id)
        if chunk:
            return {
                "clause_id": chunk.clause_id,
                "title": chunk.title,
                "category": chunk.category,
                "text": chunk.text,
                "metadata": chunk.metadata
            }
        return None

    def search(self, query: str, top_k: int = 3, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        cache_key = f"q:{query.strip().lower()}:k:{top_k}:c:{category_filter}"
        if settings.ENABLE_CACHE:
            cached = retrieval_cache.get(cache_key)
            if cached is not None:
                return cached

        q_tokens = tokenize(query)
        if not q_tokens or not self.chunks:
            return []

        n_docs = len(self.chunks)
        scores = []

        for chunk in self.chunks:
            if category_filter and chunk.category.lower() != category_filter.lower():
                continue

            doc_len = len(chunk.tokens)
            doc_tf = Counter(chunk.tokens)
            bm25_score = 0.0

            for qt in q_tokens:
                if qt in doc_tf:
                    df = self.doc_freq.get(qt, 1)
                    idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)
                    tf = doc_tf[qt]
                    term_score = idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len)))
                    bm25_score += term_score

            # Boost exact clause matches or procedure matches
            if any(qt == chunk.clause_id.lower() for qt in q_tokens):
                bm25_score += 10.0

            if bm25_score > 0:
                scores.append((bm25_score, chunk))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, chunk in scores[:top_k]:
            results.append({
                "clause_id": chunk.clause_id,
                "title": chunk.title,
                "category": chunk.category,
                "text": chunk.text,
                "score": round(score, 4),
                "metadata": chunk.metadata
            })

        if settings.ENABLE_CACHE:
            retrieval_cache.set(cache_key, results)

        return results


policy_index = LocalPolicyIndex()
