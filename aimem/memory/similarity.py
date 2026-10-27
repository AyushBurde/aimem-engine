"""
Similarity utilities.

Core functions:
  - cosine_similarity()         → compare two vectors (1-to-1)
  - batch_cosine_similarity()   → compare one vector vs many (1-to-N)
  - are_semantically_similar()  → quick boolean check with threshold
"""

import numpy as np
from typing import List, Tuple


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Returns a value between -1 and 1:
        1.0  = identical direction (same meaning)
        0.0  = orthogonal (unrelated)
       -1.0  = opposite direction

    In practice, our normalized embeddings give values between 0 and 1.

    Why not just use FAISS?
    → FAISS gives us the top-k nearest neighbors, but we sometimes
      need to compare a specific pair of vectors (e.g., new fact vs
      one specific existing memory). This is faster for 1-to-1 checks.
    """
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)

    # Avoid division by zero
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


def batch_cosine_similarity(
    query_vec: List[float], candidate_vecs: List[List[float]]
) -> List[Tuple[int, float]]:
    """
    Compare one vector against many. Returns [(index, score), ...] sorted by score desc.

    Used by contradiction detector to find ALL similar memories, not just top-k.

    Example:
        scores = batch_cosine_similarity(new_embedding, [m.embedding for m in existing])
        # → [(3, 0.92), (7, 0.88), (0, 0.45), ...]
    """
    if not candidate_vecs:
        return []

    query = np.array(query_vec, dtype=np.float32)
    candidates = np.array(candidate_vecs, dtype=np.float32)

    # Normalize
    query_norm = np.linalg.norm(query)
    if query_norm == 0:
        return [(i, 0.0) for i in range(len(candidate_vecs))]

    query = query / query_norm
    norms = np.linalg.norm(candidates, axis=1, keepdims=True)
    norms[norms == 0] = 1  # avoid div by zero
    candidates = candidates / norms

    # Batch dot product
    scores = candidates @ query

    # Sort by score descending
    indexed_scores = [(int(i), float(scores[i])) for i in range(len(scores))]
    indexed_scores.sort(key=lambda x: x[1], reverse=True)

    return indexed_scores


def are_semantically_similar(
    vec_a: List[float], vec_b: List[float], threshold: float = 0.85
) -> bool:
    """
    Quick boolean: are these two vectors talking about the same thing?

    Used as the first gate in contradiction detection:
      Step 1: Are they about the same topic? (this function)
      Step 2: If yes, do they say opposite things? (contradiction detector)
    """
    return cosine_similarity(vec_a, vec_b) >= threshold
