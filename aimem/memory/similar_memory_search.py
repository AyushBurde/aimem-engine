"""
Similar Memory Search + Contradiction Detection.

This is the brain that prevents your memory system from storing:
  Memory 1: "User lives in Delhi"
  Memory 2: "User lives in Mumbai"   ← CONTRADICTION!

Flow when a new fact arrives:
  1. Embed the new fact
  2. Find similar existing memories (same topic)
  3. For each similar memory, check: duplicate? contradiction? or just related?
  4. Return verdict: STORE / SKIP / UPDATE

Why not just use FAISS top-k?
  → FAISS finds "similar" but can't tell if they AGREE or DISAGREE.
     "Lives in Delhi" and "Lives in Mumbai" are both about location
     (high similarity), but they contradict each other.
     We need NLP-level negation/value detection on top of vector similarity.
"""

import re
import logging
from typing import List, Dict, Optional
from enum import Enum
from dataclasses import dataclass

from sqlalchemy.orm import Session

from aimem.config import get_settings
from aimem.db.models.memory import Memory
from aimem.memory.embeddings import embed_text
from aimem.memory.similarity import cosine_similarity, batch_cosine_similarity

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Types
# ═══════════════════════════════════════════════════════════

class ConflictAction(Enum):
    """What to do with the new memory."""
    STORE = "store"           # Brand new fact, just save it
    SKIP = "skip"             # Duplicate of existing, ignore it
    UPDATE = "update"         # Contradicts existing → replace old with new
    STORE_BOTH = "store_both" # Related but not contradictory → keep both


@dataclass
class ConflictResult:
    """Result of checking a new fact against existing memories."""
    action: ConflictAction
    new_content: str
    existing_memory: Optional[Memory] = None
    similarity_score: float = 0.0
    reason: str = ""


# ═══════════════════════════════════════════════════════════
# Negation / Value Change Detection
# ═══════════════════════════════════════════════════════════

# Patterns that indicate negation or reversal
NEGATION_PATTERNS = [
    r"\bnot\b", r"\bno longer\b", r"\bstopped\b", r"\bquit\b",
    r"\bdoesn't\b", r"\bdon't\b", r"\bdoes not\b", r"\bdo not\b",
    r"\bnever\b", r"\bno\b", r"\bhates?\b", r"\bdislikes?\b",
    r"\bavoids?\b", r"\brefuses?\b",
]

# Temporal keywords that signal value changes (not contradictions per se,
# but the NEW fact should replace the OLD one)
TEMPORAL_CHANGE_PATTERNS = [
    r"\bnow\b", r"\bcurrently\b", r"\brecently\b", r"\bmoved to\b",
    r"\bswitched to\b", r"\bchanged to\b", r"\bstarted\b",
    r"\bupdated\b", r"\bnew\b",
]


def _has_negation(text: str) -> bool:
    """Check if text contains negation words."""
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in NEGATION_PATTERNS)


def _has_temporal_change(text: str) -> bool:
    """Check if text signals a temporal update (moved, switched, etc.)."""
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in TEMPORAL_CHANGE_PATTERNS)


def _extract_value(text: str) -> Optional[str]:
    """
    Try to extract the key 'value' from a memory.

    "User lives in Delhi"       → "delhi"
    "User's name is Parth"      → "parth"
    "User works at Google"      → "google"

    Used to detect: same structure + different value = contradiction.
    """
    # Common patterns: "X is Y", "X in Y", "X at Y", "X to Y"
    patterns = [
        r"(?:is|are|was|were)\s+(.+?)\.?$",
        r"(?:lives?|living|moved)\s+(?:in|to)\s+(.+?)\.?$",
        r"(?:works?|working)\s+(?:at|for|with)\s+(.+?)\.?$",
        r"(?:studies|studying|studied)\s+(?:at|in)\s+(.+?)\.?$",
        r"(?:likes?|loves?|enjoys?|prefers?)\s+(.+?)\.?$",
        r"(?:name is|called)\s+(.+?)\.?$",
    ]
    text_lower = text.lower().strip()
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return match.group(1).strip()
    return None


def _values_differ(text_a: str, text_b: str) -> bool:
    """
    Check if two semantically similar memories have DIFFERENT values.

    "User lives in Delhi" vs "User lives in Mumbai"
    → values: "delhi" vs "mumbai" → True (differ!)

    "User lives in Delhi" vs "User resides in Delhi"
    → values: "delhi" vs "delhi" → False (same thing, duplicate)
    """
    val_a = _extract_value(text_a)
    val_b = _extract_value(text_b)

    # If we can't extract values, fall back to negation check
    if val_a is None or val_b is None:
        return False

    return val_a != val_b


# ═══════════════════════════════════════════════════════════
# Main Contradiction Checker
# ═══════════════════════════════════════════════════════════

def find_similar_memories(
    content: str,
    embedding: List[float],
    db: Session,
    conversation_id: int = None,
    threshold: float = None,
) -> List[Dict]:
    """
    Find existing memories similar to the new content.

    Returns list of: {"memory": Memory, "score": 0.92}
    sorted by similarity score descending.
    """
    settings = get_settings()
    if threshold is None:
        threshold = settings.CONTRADICTION_THRESHOLD

    # Get all existing memories
    q = db.query(Memory).filter(Memory._embedding.isnot(None))
    if conversation_id is not None:
        q = q.filter(Memory.conversation_id == conversation_id)
    existing = q.all()

    if not existing:
        return []

    # Batch compare
    existing_embeddings = [m.embedding for m in existing]
    scores = batch_cosine_similarity(embedding, existing_embeddings)

    # Filter by threshold
    similar = []
    for idx, score in scores:
        if score >= threshold:
            similar.append({
                "memory": existing[idx],
                "score": score,
            })

    return similar


def check_contradiction(
    new_content: str,
    new_embedding: List[float],
    db: Session,
    conversation_id: int = None,
) -> ConflictResult:
    """
    The main entry point. Check if a new fact contradicts existing memories.

    Decision logic:
    ┌──────────────────────────────────────────────────┐
    │ score >= 0.85 (SIMILARITY_THRESHOLD)             │
    │  └─ values same?  → SKIP (duplicate)             │
    │  └─ values differ? → UPDATE (contradiction)      │
    │  └─ negation?      → UPDATE (contradiction)      │
    ├──────────────────────────────────────────────────┤
    │ score >= 0.70 (CONTRADICTION_THRESHOLD)          │
    │  └─ values differ? → UPDATE (soft contradiction) │
    │  └─ otherwise      → STORE_BOTH (related)        │
    ├──────────────────────────────────────────────────┤
    │ score < 0.70                                     │
    │  └─ STORE (new fact, unrelated)                  │
    └──────────────────────────────────────────────────┘
    """
    settings = get_settings()
    sim_threshold = settings.SIMILARITY_THRESHOLD
    contra_threshold = settings.CONTRADICTION_THRESHOLD

    # Find similar existing memories
    similar = find_similar_memories(
        content=new_content,
        embedding=new_embedding,
        db=db,
        conversation_id=conversation_id,
        threshold=contra_threshold,
    )

    if not similar:
        return ConflictResult(
            action=ConflictAction.STORE,
            new_content=new_content,
            reason="No similar memories found",
        )

    # Check the most similar one
    top = similar[0]
    top_memory = top["memory"]
    top_score = top["score"]

    # ── High similarity (>= 0.85): duplicate or direct contradiction ──
    if top_score >= sim_threshold:
        # Check if values differ
        if _values_differ(new_content, top_memory.content):
            logger.info(
                f"CONTRADICTION detected: '{new_content}' vs '{top_memory.content}' "
                f"(score={top_score:.3f})"
            )
            return ConflictResult(
                action=ConflictAction.UPDATE,
                new_content=new_content,
                existing_memory=top_memory,
                similarity_score=top_score,
                reason=f"Value changed: replaces memory #{top_memory.id}",
            )

        # Check for negation
        new_has_neg = _has_negation(new_content)
        old_has_neg = _has_negation(top_memory.content)
        if new_has_neg != old_has_neg:
            logger.info(
                f"NEGATION contradiction: '{new_content}' vs '{top_memory.content}'"
            )
            return ConflictResult(
                action=ConflictAction.UPDATE,
                new_content=new_content,
                existing_memory=top_memory,
                similarity_score=top_score,
                reason=f"Negation detected: replaces memory #{top_memory.id}",
            )

        # Same values, no negation → duplicate
        logger.debug(f"DUPLICATE skipped: '{new_content}' ≈ '{top_memory.content}'")
        return ConflictResult(
            action=ConflictAction.SKIP,
            new_content=new_content,
            existing_memory=top_memory,
            similarity_score=top_score,
            reason=f"Duplicate of memory #{top_memory.id}",
        )

    # ── Medium similarity (>= 0.70): possible soft contradiction ──
    if _values_differ(new_content, top_memory.content):
        # Temporal change? (e.g., "now lives in Mumbai")
        if _has_temporal_change(new_content):
            logger.info(
                f"TEMPORAL UPDATE: '{new_content}' replaces '{top_memory.content}'"
            )
            return ConflictResult(
                action=ConflictAction.UPDATE,
                new_content=new_content,
                existing_memory=top_memory,
                similarity_score=top_score,
                reason=f"Temporal update: replaces memory #{top_memory.id}",
            )

        return ConflictResult(
            action=ConflictAction.UPDATE,
            new_content=new_content,
            existing_memory=top_memory,
            similarity_score=top_score,
            reason=f"Soft contradiction: replaces memory #{top_memory.id}",
        )

    # Related but not contradictory
    return ConflictResult(
        action=ConflictAction.STORE_BOTH,
        new_content=new_content,
        existing_memory=top_memory,
        similarity_score=top_score,
        reason="Related but not contradictory — keeping both",
    )
