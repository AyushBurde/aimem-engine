"""
FastAPI routes — thin REST wrapper around the aimem library.

Endpoints:
  POST   /api/chat               → THE MAIN ONE: extract + recall + answer
  POST   /api/memories/add       → extract & store memories from messages
  GET    /api/memories            → list all memories
  GET    /api/memories/search     → hybrid search
  GET    /api/memories/history    → temporal history of a fact
  PUT    /api/memories/{id}       → update a memory
  DELETE /api/memories/{id}       → delete a memory
  POST   /api/memories/consolidate → merge similar memories
  POST   /api/conversations       → create a new conversation
"""

from aimem.memory.consolidate import consolidate_memories
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from aimem.db.database import get_db
from aimem.db.models.conversation import Conversation
from aimem.memory.memory import Memory
from aimem.memory.chat import chat_with_memory

router = APIRouter(prefix="/api")


# ── Request/Response Schemas ─────────────────────────

class MessageIn(BaseModel):
    role: str       # "user" or "assistant"
    content: str


class AddMemoriesRequest(BaseModel):
    messages: List[MessageIn]
    conversation_id: int


class ChatRequest(BaseModel):
    message: str
    conversation_id: int


class UpdateMemoryRequest(BaseModel):
    text: str


class SearchQuery(BaseModel):
    query: str
    conversation_id: Optional[int] = None
    limit: int = 5


class CreateConversationRequest(BaseModel):
    agent_id: str = "default"
    user_id: str = "default"
    title: Optional[str] = None


# ── ROUTES ───────────────────────────────────────────

@router.post("/conversations")
def create_conversation(req: CreateConversationRequest, db: Session = Depends(get_db)):
    """Create a new conversation. Returns its ID."""
    convo = Conversation(
        agent_id=req.agent_id,
        user_id=req.user_id,
        title=req.title,
    )
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return {"id": convo.id, "agent_id": convo.agent_id, "user_id": convo.user_id}


@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    THE MAIN ENDPOINT. Full pipeline:
      1. Extract & store any new facts from the message
      2. Search memories relevant to the message (embed → FAISS dot product → top-k)
      3. Inject top memories as context into LLM prompt
      4. Return the LLM's answer + what was extracted/recalled
    """
    memory = Memory(db)

    # Step 1: Extract & store new memories
    extraction = memory.add(
        messages=[{"role": "user", "content": req.message}],
        conversation_id=req.conversation_id,
    )

    # Step 2: Search for relevant memories (embed query → FAISS similarity → ranked)
    search_result = memory.search(
        query=req.message,
        conversation_id=req.conversation_id,
        limit=5,
    )
    recalled = search_result.get("results", [])

    # Step 3: Feed recalled memories + message to Gemini → answer
    answer = chat_with_memory(
        message=req.message,
        memories=recalled,
    )

    return {
        "answer": answer,
        "extraction": extraction,
        "recalled_memories": recalled,
    }


@router.post("/memories/add")
def add_memories(req: AddMemoriesRequest, db: Session = Depends(get_db)):
    """
    Send chat messages → engine extracts facts → stores in DB + FAISS.
    Handles contradictions and duplicates automatically.
    """
    memory = Memory(db)
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    result = memory.add(messages=messages, conversation_id=req.conversation_id)
    return result


@router.get("/memories")
def list_memories(conversation_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get all stored memories, optionally filtered by conversation."""
    memory = Memory(db)
    return memory.get_all(conversation_id=conversation_id)


@router.get("/memories/search")
def search_memories(
    q: str,
    conversation_id: Optional[int] = None,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    """Hybrid search (BM25 + semantic + exact match)."""
    memory = Memory(db)
    return memory.search(query=q, conversation_id=conversation_id, limit=limit)

@router.get("/memories/history")
def memory_history(
    q: str,
    conversation_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Temporal history: see how a fact evolved over time.

    Example: GET /api/memories/history?q=where does user live
    Returns the full timeline:
      - "User lives in Delhi"     (Jan 2026 → Aug 2026, superseded)
      - "User lives in Bangalore" (Aug 2026 → current, active)
    """
    memory = Memory(db)
    return memory.history(query=q, conversation_id=conversation_id)


@router.put("/memories/{memory_id}")
def update_memory(memory_id: int, req: UpdateMemoryRequest, db: Session = Depends(get_db)):
    """Update a memory's content. Re-embeds automatically."""
    memory = Memory(db)
    result = memory.update(memory_id=memory_id, text=req.text)
    if result is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return result


@router.delete("/memories/{memory_id}")
def delete_memory(memory_id: int, db: Session = Depends(get_db)):
    """Delete a memory from DB and FAISS."""
    memory = Memory(db)
    deleted = memory.delete(memory_id=memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"deleted": True, "id": memory_id}

@router.post("/memories/consolidate")
def consolidate(conversation_id: int, db: Session = Depends(get_db)):
    """
    Scan memories for similar clusters → merge via LLM → archive originals.
    Call this periodically or when memory count gets high.
    """
    result = consolidate_memories(db, conversation_id)
    return result

