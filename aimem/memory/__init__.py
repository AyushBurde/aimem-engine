"""
Memory engine package — exports core classes.
"""

from aimem.memory.memory import Memory
from aimem.memory.similarity import cosine_similarity, batch_cosine_similarity
from aimem.memory.similar_memory_search import check_contradiction, ConflictAction, ConflictResult
from aimem.memory.embeddings import embed_text
from aimem.memory.extractor import extract_memories
from aimem.memory.temporal import supersede_memory, get_memory_timeline, get_current_memories

__all__ = [
    "Memory",
    "cosine_similarity",
    "batch_cosine_similarity",
    "check_contradiction",
    "ConflictAction",
    "ConflictResult",
    "embed_text",
    "extract_memories",
    "supersede_memory",
    "get_memory_timeline",
    "get_current_memories",
]

