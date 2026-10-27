"""
Memory — the main orchestrator.

This is the public interface. Users call:
    memory = Memory(db)
    memory.add(messages=[...], conversation_id=1)
    memory.search(query="...", conversation_id=1)
    memory.update(memory_id=1, text="...")
    memory.delete(memory_id=1)
    memory.history(query="...", conversation_id=1)  # NEW: temporal history

Internally coordinates: extractor → classifier → contradiction_check → embeddings → DB + FAISS

v3 changes (temporal memory):
  - Contradictions now SUPERSEDE instead of overwrite
  - Old memories preserved with valid_until timestamp
  - New history() method for temporal queries
  - Retrieval prioritizes currently-valid memories
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from aimem.db.models.memory import Memory as MemoryModel
from aimem.memory.extractor import extract_memories
from aimem.memory.classifier import classify_memory
from aimem.memory.embeddings import embed_text
from aimem.memory.vector_store import get_vector_store
from aimem.memory.retriever import hybrid_search
from aimem.memory.similar_memory_search import check_contradiction, ConflictAction
from aimem.memory.temporal import supersede_memory, get_memory_timeline

logger = logging.getLogger(__name__)


class Memory:
    def __init__(self, db: Session):
        self.db = db

    # ═══════════════════════════════════════════════════
    # ADD (v3 — with temporal superseding)
    # ═══════════════════════════════════════════════════

    def add(self, messages: List[Dict], conversation_id: int) -> Dict:
        """
        Extract memories from messages and store them.

        Flow:
          messages → extractor → classifier → embed →
          contradiction_check → (STORE | SKIP | SUPERSEDE) → DB + FAISS

        v3 change: UPDATE action now creates a new memory and supersedes the old
        one instead of overwriting in-place. This preserves temporal history.

        Returns:
            {
                "memories_added": [...],
                "memories_superseded": [...],  # was "memories_updated"
                "memories_skipped": [...],
                "count": int,
            }
        """
        # Step 1: Gemini extracts facts
        raw_facts = extract_memories(messages)

        if not raw_facts:
            return {
                "memories_added": [],
                "memories_superseded": [],
                "memories_skipped": [],
                "count": 0,
            }

        added = []
        superseded = []
        skipped = []
        vector_store = get_vector_store()

        for fact in raw_facts:
            # Step 2: Correct the type if LLM got it wrong
            corrected_type = classify_memory(fact)

            # Step 3: Text → 768-dim vector
            embedding = embed_text(fact["content"])

            # Step 4: ★ CONTRADICTION CHECK ★
            conflict = check_contradiction(
                new_content=fact["content"],
                new_embedding=embedding,
                db=self.db,
                conversation_id=conversation_id,
            )

            if conflict.action == ConflictAction.SKIP:
                # Duplicate — don't store
                logger.info(f"SKIP duplicate: '{fact['content']}'")
                skipped.append({
                    "content": fact["content"],
                    "reason": conflict.reason,
                    "similar_to": conflict.existing_memory.id if conflict.existing_memory else None,
                })
                continue

            elif conflict.action == ConflictAction.UPDATE:
                # ══════════════════════════════════════════════
                # v3 CHANGE: SUPERSEDE instead of overwrite
                # ══════════════════════════════════════════════
                # Before (v2): We overwrote the old memory's content in-place.
                #   Problem: The old fact is lost forever. No history.
                #
                # Now (v3): We create a NEW memory for the updated fact,
                #   and mark the old memory as "superseded" with a timestamp.
                #   The old memory stays in the DB as historical record.
                #
                # Example:
                #   Old: "User lives in Delhi"   → status="superseded", valid_until=now
                #   New: "User lives in Bangalore" → status="active", valid_from=now
                # ══════════════════════════════════════════════

                old_memory = conflict.existing_memory
                logger.info(
                    f"SUPERSEDE: '{old_memory.content}' → '{fact['content']}'"
                )

                # Create the new memory (the current truth)
                new_memory = MemoryModel(
                    content=fact["content"],
                    memory_type=corrected_type,
                    category=fact.get("category", old_memory.category),
                    confidence=fact.get("confidence", 0.8),
                    conversation_id=conversation_id,
                    status="active",
                    valid_from=datetime.now(timezone.utc),
                )
                new_memory.embedding = embedding
                self.db.add(new_memory)
                self.db.flush()  # Get the new ID

                # Add new vector to FAISS
                vector_store.add(new_memory.id, embedding)

                # Supersede the old memory (mark it as historical)
                # This sets: status="superseded", valid_until=now, superseded_by_id=new.id
                supersede_memory(old_memory, new_memory, self.db)

                # Remove old memory from FAISS (it shouldn't appear in normal search)
                vector_store.remove(old_memory.id)

                superseded.append({
                    "new_id": new_memory.id,
                    "new_content": fact["content"],
                    "old_id": old_memory.id,
                    "old_content": old_memory.content,
                    "reason": conflict.reason,
                    "old_valid_from": old_memory.valid_from.isoformat() if old_memory.valid_from else None,
                    "old_valid_until": old_memory.valid_until.isoformat() if old_memory.valid_until else None,
                })
                continue

            # ConflictAction.STORE or STORE_BOTH — save as new memory
            memory = MemoryModel(
                content=fact["content"],
                memory_type=corrected_type,
                category=fact.get("category", "other"),
                confidence=fact.get("confidence", 0.8),
                embedding=embedding,
                conversation_id=conversation_id,
                valid_from=datetime.now(timezone.utc),
            )
            self.db.add(memory)
            self.db.flush()  # Gets auto ID without full commit

            # Add vector to FAISS
            vector_store.add(memory.id, embedding)
            added.append(memory)

        self.db.commit()
        vector_store.save()

        return {
            "memories_added": [
                {
                    "id": m.id,
                    "content": m.content,
                    "memory_type": m.memory_type,
                    "category": m.category,
                    "confidence": m.confidence,
                }
                for m in added
            ],
            "memories_superseded": superseded,
            "memories_skipped": skipped,
            "count": len(added),
        }

    # ═══════════════════════════════════════════════════
    # SEARCH
    # ═══════════════════════════════════════════════════

    def search(self, query: str, conversation_id: int = None, limit: int = 5) -> Dict:
        """
        Hybrid search: BM25 + FAISS semantic + exact match → fused scores.
        Only returns currently-valid memories (active + valid_until is NULL).
        """
        results = hybrid_search(
            query=query,
            db=self.db,
            conversation_id=conversation_id,
            top_k=limit,
        )

        return {
            "query": query,
            "results": [
                {
                    "memory_id": r["memory"].id,
                    "content": r["memory"].content,
                    "memory_type": r["memory"].memory_type,
                    "score": r["score"],
                    "breakdown": r["breakdown"],
                }
                for r in results
            ],
        }

    # ═══════════════════════════════════════════════════
    # HISTORY (NEW — temporal queries)
    # ═══════════════════════════════════════════════════

    def history(self, query: str, conversation_id: int = None) -> Dict:
        """
        Get the temporal history of a fact.

        Example:
          query: "where does user live"
          → [
              {content: "Delhi",     valid_from: Jan, valid_until: Aug, status: "superseded"},
              {content: "Bangalore", valid_from: Aug, valid_until: None, status: "active"},
            ]

        This is the temporal reasoning feature that makes our system
        understand WHEN facts changed, not just WHAT the current fact is.
        """
        timeline = get_memory_timeline(
            query=query,
            db=self.db,
            conversation_id=conversation_id,
        )

        return {
            "query": query,
            "timeline": timeline,
            "total_versions": len(timeline),
            "current": next((t for t in timeline if t["is_current"]), None),
        }

    # ═══════════════════════════════════════════════════
    # UPDATE
    # ═══════════════════════════════════════════════════

    def update(self, memory_id: int, text: str) -> Optional[Dict]:
        """
        Update a memory's content. Re-embeds and updates FAISS.
        """
        memory = self.db.query(MemoryModel).get(memory_id)
        if not memory:
            return None

        # Update content
        memory.content = text

        # Re-embed with new text
        new_embedding = embed_text(text)
        memory.embedding = new_embedding

        # Update FAISS: remove old → add new
        vector_store = get_vector_store()
        vector_store.remove(memory_id)
        vector_store.add(memory_id, new_embedding)

        self.db.commit()
        vector_store.save()

        return {
            "id": memory.id,
            "content": memory.content,
            "memory_type": memory.memory_type,
            "updated": True,
        }

    # ═══════════════════════════════════════════════════
    # DELETE
    # ═══════════════════════════════════════════════════

    def delete(self, memory_id: int) -> bool:
        """
        Delete a memory from DB and FAISS.
        """
        memory = self.db.query(MemoryModel).get(memory_id)
        if not memory:
            return False

        # Remove from FAISS
        vector_store = get_vector_store()
        vector_store.remove(memory_id)

        # Remove from DB
        self.db.delete(memory)
        self.db.commit()
        vector_store.save()

        return True

    # ═══════════════════════════════════════════════════
    # GET ALL
    # ═══════════════════════════════════════════════════

    def get_all(self, conversation_id: int = None) -> List[Dict]:
        """
        Get all memories, optionally filtered by conversation.
        """
        q = self.db.query(MemoryModel).filter(MemoryModel.status == "active")
        if conversation_id is not None:
            q = q.filter(MemoryModel.conversation_id == conversation_id)

        memories = q.order_by(MemoryModel.created_at.desc()).all()

        return [
            {
                "id": m.id,
                "content": m.content,
                "memory_type": m.memory_type,
                "category": m.category,
                "confidence": m.confidence,
                "access_count": m.access_count,
                "conversation_id": m.conversation_id,
                "is_current": m.is_current,
                "valid_from": m.valid_from.isoformat() if m.valid_from else None,
                "valid_until": m.valid_until.isoformat() if m.valid_until else None,
                "created_at": str(m.created_at),
            }
            for m in memories
        ]
