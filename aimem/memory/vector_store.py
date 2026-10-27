"""
FAISS vector store — our vector database.

Stores memory embeddings and does fast similarity search.
"""

import json
import os
from typing import List, Tuple, Optional

import faiss  
import numpy as np

from aimem.config import get_settings


class VectorStore:
    """Manages a FAISS index for memory embeddings."""

    def __init__(self):
        settings = get_settings()
        self.dimension = settings.EMBEDDING_DIMENSION
        self.index_path = settings.FAISS_INDEX_PATH
        self.id_map_path = settings.FAISS_ID_MAP_PATH

        # IndexFlatIP = Inner Product on normalized vectors = cosine similarity
        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(self.dimension)

        # Maps FAISS position → our memory ID
        self.id_map: List[int] = []

    def add(self, memory_id: int, embedding: List[float]):
        """Add one memory's vector to the index."""
        vector = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(vector)
        self.index.add(vector)
        self.id_map.append(memory_id)

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Find top_k most similar memories.
        Returns: [(memory_id, score), ...]
        """
        if self.index.ntotal == 0:
            return []

        vector = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(vector)

        k = min(top_k, self.index.ntotal)
        D, I = self.index.search(vector, k)

        results = []
        for score, idx in zip(D[0], I[0]):
            if idx < len(self.id_map):
                results.append((self.id_map[idx], float(score)))
        return results

    def remove(self, memory_id: int):
        """Remove a memory. Requires rebuild."""
        if memory_id in self.id_map:
            self.id_map.remove(memory_id)
            self._rebuild()

    def _rebuild(self):
        """Rebuild index from scratch."""
        old_vectors = []
        if self.index.ntotal > 0:
            all_vecs = faiss.rev_swig_ptr(
                self.index.get_xb(), self.index.ntotal * self.dimension
            ).reshape(self.index.ntotal, self.dimension).copy()
            old_vectors = [all_vecs[i] for i in range(len(self.id_map))]

        self.index = faiss.IndexFlatIP(self.dimension)
        if old_vectors:
            self.index.add(np.array(old_vectors, dtype=np.float32))

    def save(self):
        """Save index + ID map to disk."""
        os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.id_map_path, "w") as f:
            json.dump(self.id_map, f)

    def load(self):
        """Load index + ID map from disk."""
        if os.path.exists(self.index_path) and os.path.exists(self.id_map_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.id_map_path, "r") as f:
                self.id_map = json.load(f)

    def rebuild_from_db(self, db_session):
        """Full rebuild from SQLAlchemy (if index gets corrupted)."""
        from aimem.db.models.memory import Memory

        self.index = faiss.IndexFlatIP(self.dimension)
        self.id_map = []

        memories = db_session.query(Memory).filter(Memory.embedding.isnot(None)).all()
        for mem in memories:
            self.add(mem.id, mem.embedding)
        self.save()


_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the global VectorStore."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
        _vector_store.load()
    return _vector_store
