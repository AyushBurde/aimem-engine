"""
Hybrid Retriever — combines 3 search methods.

1. BM25:     keyword matching ("Python" finds "Python")
2. Semantic: meaning matching ("coding" finds "programming") — via FAISS
3. Exact:    substring match ("Parth" finds "User's name is Parth")

Each produces scores → normalized → weighted sum → final ranking.
"""

import math
import re
from typing import List, Dict
from collections import Counter

import numpy as np
from sqlalchemy.orm import Session

from aimem.config import get_settings
from aimem.memory.embeddings import embed_text
from aimem.memory.vector_store import get_vector_store
from aimem.db.models.memory import Memory


# ─── BM25 (from scratch) ──────────────────────────────

def _tokenize(text: str) -> List[str]:
    """Lowercase + split on non-alphanumeric."""
    return re.findall(r'\w+', text.lower())


def _bm25_score(query: str, documents: List[str], k1: float, b: float) -> List[float]:
    """
    BM25 scoring:
    - Word in FEW documents = more important (IDF)
    - Word appearing many times = diminishing returns (TF saturation)
    - Longer docs slightly penalized (length normalization)
    """
    query_tokens = _tokenize(query)
    doc_tokens = [_tokenize(doc) for doc in documents]

    if not doc_tokens:
        return []

    avg_dl = np.mean([len(d) for d in doc_tokens]) if doc_tokens else 1
    N = len(doc_tokens)

    df = Counter()
    for tokens in doc_tokens:
        for token in set(tokens):
            df[token] += 1

    scores = []
    for tokens in doc_tokens:
        score = 0.0
        dl = len(tokens)
        tf_counter = Counter(tokens)

        for qt in query_tokens:
            if qt not in tf_counter:
                continue
            tf = tf_counter[qt]
            n = df.get(qt, 0)
            idf = math.log((N - n + 0.5) / (n + 0.5) + 1)
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (dl / avg_dl))
            score += idf * (numerator / denominator)

        scores.append(score)
    return scores


# ─── Exact Match ───────────────────────────────────────

def _exact_match_score(query: str, documents: List[str]) -> List[float]:
    """1.0 if query is substring of document, else 0.0."""
    query_lower = query.lower()
    return [1.0 if query_lower in doc.lower() else 0.0 for doc in documents]


# ─── Normalize ─────────────────────────────────────────

def _normalize(scores: List[float]) -> List[float]:
    """Min-max normalize to [0, 1]."""
    if not scores:
        return []
    min_s, max_s = min(scores), max(scores)
    if max_s == min_s:
        return [0.0] * len(scores)
    return [(s - min_s) / (max_s - min_s) for s in scores]


# ─── Hybrid Search (main function) ────────────────────

def hybrid_search(
    query: str,
    db: Session,
    conversation_id: int = None,
    top_k: int = None,
) -> List[Dict]:
    """
    Search memories using all 3 methods, fuse scores, return ranked results.

    Returns: [{"memory": Memory, "score": 0.85, "breakdown": {...}}, ...]
    """
    settings = get_settings()
    if top_k is None:
        top_k = settings.RETRIEVAL_TOP_K

    # 1. Get candidate memories from DB (only active ones)
    # AFTER: Only retrieve currently-valid memories
    # Superseded memories (valid_until is set) are excluded from normal search
    # They're still accessible via the /history endpoint for temporal queries
    q = db.query(Memory).filter(
        Memory.status == "active",
        Memory.valid_until.is_(None),  # Only current truth, not historical facts
    )

    if conversation_id is not None:
        q = q.filter(Memory.conversation_id == conversation_id)
    memories = q.all()

    if not memories:
        return []

    contents = [m.content for m in memories]

    # 2. BM25 scores
    bm25_raw = _bm25_score(query, contents, settings.BM25_K1, settings.BM25_B)
    bm25_norm = _normalize(bm25_raw)

    # 3. Semantic scores (via FAISS)
    vector_store = get_vector_store()
    query_embedding = embed_text(query)
    faiss_results = vector_store.search(query_embedding, top_k=len(memories))
    faiss_scores = {mem_id: score for mem_id, score in faiss_results}
    semantic_norm = _normalize([faiss_scores.get(m.id, 0.0) for m in memories])

    # 4. Exact match scores
    exact_norm = _exact_match_score(query, contents)

    # 5. Weighted fusion
    w_bm25 = settings.RETRIEVAL_WEIGHT_BM25
    w_semantic = settings.RETRIEVAL_WEIGHT_SEMANTIC
    w_exact = settings.RETRIEVAL_WEIGHT_EXACT

    results = []
    for i, memory in enumerate(memories):
        final_score = (
            w_bm25 * bm25_norm[i]
            + w_semantic * semantic_norm[i]
            + w_exact * exact_norm[i]
        )
        results.append({
            "memory": memory,
            "score": round(final_score, 4),
            "breakdown": {
                "bm25": round(bm25_norm[i], 4),
                "semantic": round(semantic_norm[i], 4),
                "exact": round(exact_norm[i], 4),
            },
        })

    # 6. Sort + update access counts
    results.sort(key=lambda x: x["score"], reverse=True)
    for r in results[:top_k]:
        r["memory"].access_count += 1
    db.commit()

    return results[:top_k]
