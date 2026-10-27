"""
Memory Consolidation Engine.

Scans memories → finds clusters of similar facts → merges via LLM → archives originals.

Example:
  Before: 5 memories about Python coding
  After:  1 clean memory "User is an experienced Python developer"
          + 4 originals marked status="consolidated"
"""

import numpy as np
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from aimem.memory.llm import generate_text


from aimem.config import get_settings
from aimem.db.models.memory import Memory as MemoryModel
from aimem.memory.embeddings import embed_text, _ensure_client
from aimem.memory.similarity import cosine_similarity


# ── Prompt for merging a cluster ──────────────────────

MERGE_PROMPT = """You are a memory consolidation system. You are given multiple memories about a user that are semantically similar or related.

Your job: Merge them into ONE clean, concise fact that preserves ALL important information.

Rules:
- Keep the most specific and up-to-date information
- Don't lose any unique details
- Output ONLY the merged fact, nothing else
- Keep it under 2 sentences

Memories to merge:
{memories}

Merged fact:"""


def find_clusters(
    memories: List[MemoryModel],
    similarity_threshold: float = 0.80,
) -> List[List[MemoryModel]]:
    """
    Find groups of semantically similar memories.

    How it works:
      1. Compare every pair of memories using cosine similarity
      2. If similarity > threshold, they're in the same cluster
      3. Uses Union-Find to handle transitive similarity
         (if A~B and B~C, then {A,B,C} is one cluster)

    Returns: List of clusters, each cluster is a list of 2+ similar memories
    """
    n = len(memories)
    if n < 2:
        return []

    # Filter out memories without embeddings
    valid = [(i, m) for i, m in enumerate(memories) if m.embedding is not None]
    if len(valid) < 2:
        return []

    # Union-Find for clustering
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    # Compare all pairs
    for i in range(len(valid)):
        for j in range(i + 1, len(valid)):
            idx_i, mem_i = valid[i]
            idx_j, mem_j = valid[j]
            sim = cosine_similarity(mem_i.embedding, mem_j.embedding)
            if sim >= similarity_threshold:
                union(idx_i, idx_j)

    # Group by cluster
    from collections import defaultdict
    groups = defaultdict(list)
    for idx, mem in valid:
        groups[find(idx)].append(mem)

    # Only return clusters with 2+ members
    return [cluster for cluster in groups.values() if len(cluster) >= 2]


def merge_cluster(memories: List[MemoryModel]) -> str:
    """Takes a list of similar memories and uses the LLM to produce one merged fact."""
    bullet_list = "\n".join(f"- {m.content}" for m in memories)
    prompt = MERGE_PROMPT.format(memories=bullet_list)
    merged_text = generate_text(prompt)
    return merged_text.strip()



def consolidate_memories(
    db: Session,
    conversation_id: int,
    similarity_threshold: float = 0.80,
) -> Dict:
    """
    Main consolidation pipeline.

    Steps:
      1. Load all active memories
      2. Find similar clusters
      3. Merge each cluster via LLM
      4. Create new merged memory
      5. Mark originals as status="consolidated"

    Returns summary of what was done.
    """
    # Step 1: Load active memories
    memories = (
        db.query(MemoryModel)
        .filter(
            MemoryModel.conversation_id == conversation_id,
            MemoryModel.status == "active",
        )
        .all()
    )

    if len(memories) < 2:
        return {"clusters_found": 0, "memories_merged": 0, "new_memories": []}

    # Step 2: Find clusters
    clusters = find_clusters(memories, similarity_threshold)

    if not clusters:
        return {"clusters_found": 0, "memories_merged": 0, "new_memories": []}

    results = {
        "clusters_found": len(clusters),
        "memories_merged": 0,
        "new_memories": [],
        "archived_memories": [],
    }

    for cluster in clusters:
        # Step 3: Merge via LLM
        merged_text = merge_cluster(cluster)

        # Step 4: Determine type & category (use the most common in cluster)
        types_in_cluster = [m.memory_type for m in cluster]
        cats_in_cluster = [m.category for m in cluster]
        best_type = max(set(types_in_cluster), key=types_in_cluster.count)
        best_cat = max(set(cats_in_cluster), key=cats_in_cluster.count)

        # Embed the new merged text
        merged_embedding = embed_text(merged_text)

        # Create new merged memory
        new_memory = MemoryModel(
            content=merged_text,
            memory_type=best_type,
            category=best_cat,
            confidence=1.0,
            conversation_id=conversation_id,
            status="active",
            access_count=sum(m.access_count for m in cluster),
        )
        new_memory.embedding = merged_embedding
        db.add(new_memory)
        db.flush()  # Get the new ID

        # Step 5: Mark originals as consolidated
        for mem in cluster:
            mem.status = "consolidated"
            mem.consolidated_into_id = new_memory.id
            mem.updated_at = datetime.now(timezone.utc)
            results["archived_memories"].append({
                "id": mem.id,
                "content": mem.content,
            })

        results["memories_merged"] += len(cluster)
        results["new_memories"].append({
            "id": new_memory.id,
            "content": merged_text,
            "merged_from": [m.id for m in cluster],
        })

    db.commit()

    return results
