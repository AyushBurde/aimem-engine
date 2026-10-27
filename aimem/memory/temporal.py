"""
Temporal Memory — handles fact validity over time.

Core concept: Memories have a "validity window" [valid_from, valid_until].
  - valid_until = NULL means "currently true"
  - valid_until = <timestamp> means "was true until this time"

This is inspired by how Zep's Graphiti engine handles temporal facts,
but implemented as a simpler, queryable model rather than a full knowledge graph.

Two key operations:
  1. supersede: mark an old fact as no longer current, link to the new fact
  2. history: retrieve the full timeline of how a fact evolved
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

from sqlalchemy.orm import Session

from aimem.db.models.memory import Memory as MemoryModel
from aimem.memory.embeddings import embed_text
from aimem.memory.similarity import batch_cosine_similarity

logger = logging.getLogger(__name__)


def supersede_memory(
    old_memory: MemoryModel,
    new_memory: MemoryModel,
    db: Session,
) -> None:
    """
    Mark an old memory as superseded by a newer one.

    This is called when we detect a contradiction like:
      Old: "User lives in Delhi"
      New: "User moved to Bangalore"

    What happens:
      - Old memory: status → "superseded", valid_until → now, superseded_by_id → new.id
      - New memory: valid_from → now (already set by default)

    The old memory is NOT deleted. It becomes part of the user's history.
    This lets us answer "where did the user live before?" later.

    This is the key difference from your current approach which just overwrites
    the old content. Overwriting = data loss. Superseding = data preservation.
    """
    now = datetime.now(timezone.utc)

    # Mark old memory as no longer current
    old_memory.status = "superseded"
    old_memory.valid_until = now
    old_memory.superseded_by_id = new_memory.id
    old_memory.updated_at = now

    # Ensure new memory has valid_from set
    if new_memory.valid_from is None:
        new_memory.valid_from = now

    logger.info(
        f"SUPERSEDED: Memory #{old_memory.id} ('{old_memory.content}') "
        f"→ replaced by #{new_memory.id} ('{new_memory.content}')"
    )


def get_memory_timeline(
    query: str,
    db: Session,
    conversation_id: int = None,
    similarity_threshold: float = 0.70,
) -> List[Dict]:
    """
    Get the full history of how a fact evolved over time.

    Example query: "Where does the user live?"
    Returns:
      [
        {"content": "User lives in Delhi",     "valid_from": "Jan 2026", "valid_until": "Aug 2026", "status": "superseded"},
        {"content": "User lives in Bangalore",  "valid_from": "Aug 2026", "valid_until": None,       "status": "active"},
      ]

    How it works:
      1. Embed the query
      2. Find ALL memories (active + superseded) that are semantically similar
      3. Sort by valid_from ascending → gives you the timeline

    This is powerful because it lets you answer:
      - "Where does user live?" → latest active memory
      - "Where did user live before?" → superseded memories
      - "When did user move?" → look at valid_until of the superseded one
    """
    query_embedding = embed_text(query)

    # Get ALL memories (including superseded ones — that's the whole point)
    q = db.query(MemoryModel).filter(
        MemoryModel.status.in_(["active", "superseded"]),
        MemoryModel._embedding.isnot(None),
    )
    if conversation_id is not None:
        q = q.filter(MemoryModel.conversation_id == conversation_id)

    all_memories = q.all()

    if not all_memories:
        return []

    # Find semantically similar memories
    embeddings = [m.embedding for m in all_memories]
    scores = batch_cosine_similarity(query_embedding, embeddings)

    # Filter by threshold and build timeline
    timeline = []
    for idx, score in scores:
        if score >= similarity_threshold:
            mem = all_memories[idx]
            timeline.append({
                "id": mem.id,
                "content": mem.content,
                "memory_type": mem.memory_type,
                "category": mem.category,
                "status": mem.status,
                "valid_from": mem.valid_from.isoformat() if mem.valid_from else None,
                "valid_until": mem.valid_until.isoformat() if mem.valid_until else None,
                "superseded_by_id": mem.superseded_by_id,
                "is_current": mem.is_current,
                "similarity_score": round(score, 4),
            })

    # Sort by valid_from (oldest first) → chronological timeline
    timeline.sort(key=lambda x: x["valid_from"] or "")

    return timeline


def get_current_memories(
    db: Session,
    conversation_id: int = None,
) -> List[MemoryModel]:
    """
    Get only currently-valid memories (active + no valid_until).

    This is what you use for most retrieval — you usually want
    the CURRENT truth, not historical facts.
    """
    q = db.query(MemoryModel).filter(
        MemoryModel.status == "active",
        MemoryModel.valid_until.is_(None),
    )
    if conversation_id is not None:
        q = q.filter(MemoryModel.conversation_id == conversation_id)

    return q.all()
