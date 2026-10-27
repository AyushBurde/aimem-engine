"""
Memory model — stores extracted facts with temporal validity.

Each row = one fact the system extracted from a conversation.
  "User's name is Parth"  → permanent, profile, 0.95
  "User lives in Delhi"   → temporal, location, 0.90, valid_from=Jan, valid_until=Aug

Temporal Design:
  When a fact changes (e.g., user moves cities), we DON'T delete the old memory.
  Instead:
    - Old memory gets valid_until = now, status = "superseded"
    - New memory gets valid_from = now, valid_until = NULL (current truth)
  
  This lets us answer both:
    "Where does user live?" → current valid memory
    "Where did user live before?" → superseded memory with valid_until set
"""

import json
from datetime import datetime, timezone

from sqlalchemy import Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aimem.db.database import Base


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # "permanent" | "temporal" | "episodic"
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False, default="permanent")

    # "profile", "preference", "hobby", "work", "relationship", "health", "location", "other"
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="other")

    confidence: Mapped[float] = mapped_column(Float, default=0.8)

    # Embedding stored as JSON text (list of floats)
    _embedding: Mapped[str] = mapped_column("embedding", Text, nullable=True)

    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id"), nullable=True, index=True
    )

    access_count: Mapped[int] = mapped_column(Integer, default=0)

    # "active" | "superseded" | "consolidated" | "archived"
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)

    # When was this memory last recalled?
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # If consolidated, points to the merged memory that replaced this one
    consolidated_into_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("memories.id"), nullable=True
    )

    # ── TEMPORAL VALIDITY ─────────────────────────────────
    # When did this fact become true?
    # Defaults to creation time — "User lives in Delhi" was true from the moment they told us
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=True,
    )

    # When did this fact STOP being true?
    # NULL = still current truth
    # Set = this fact was superseded by a newer one
    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    # If superseded, which newer memory replaced this one?
    # Different from consolidated_into_id:
    #   - consolidated = merged with similar memories (compression)
    #   - superseded = replaced by contradicting newer fact (temporal update)
    superseded_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("memories.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Helper: is this memory currently valid? ──
    @property
    def is_current(self) -> bool:
        """True if this memory represents a currently-valid fact."""
        return self.status == "active" and self.valid_until is None

    # ── Embedding property (JSON ↔ list) ──
    @property
    def embedding(self):
        if self._embedding is None:
            return None
        return json.loads(self._embedding)

    @embedding.setter
    def embedding(self, value):
        if value is None:
            self._embedding = None
        else:
            self._embedding = json.dumps(value)

    # ── Relationship ──
    conversation = relationship("Conversation", back_populates="memories")

    def __repr__(self):
        validity = "current" if self.is_current else f"until {self.valid_until}"
        return f"<Memory(id={self.id}, type={self.memory_type}, {validity}, content={self.content[:40]}...)>"
