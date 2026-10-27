# 🧠 aimem — Memory Layer for AI Agents

> AI Agents deserve better memory.

**aimem** is a drop-in memory engine that gives your AI agents long-term, context-aware memory. It extracts facts from conversations, detects contradictions, tracks how facts evolve over time, and retrieves the right context when your agent needs it.

## ✨ Features

- **🔍 Fact Extraction** — Automatically pulls structured facts from natural conversations
- **⚡ Hybrid Retrieval** — BM25 + Semantic (FAISS) + Exact Match fusion for accurate recall
- **🔄 Contradiction Detection** — Catches conflicting facts ("lives in Delhi" vs "lives in Mumbai")
- **⏳ Temporal Reasoning** — Tracks how facts change over time with full history
- **🧹 Memory Consolidation** — Merges duplicate/fragmented memories automatically
- **🔌 Multi-Provider** — Works with Gemini (free!), OpenAI, or OpenRouter (Claude, Llama, etc.)

## 🚀 Quickstart

### Install

```bash
pip install aimem-engine
```

### Use as a Python Library

```python
import aimem

# Configure (pick your LLM)
aimem.configure(gemini_api_key="AIzaSy...")  # Free!
# OR: aimem.configure(openai_api_key="sk-...")
# OR: aimem.configure(openrouter_api_key="sk-or-...")

# Setup
aimem.create_tables()
db = aimem.SessionLocal()
memory = aimem.Memory(db)

# Store memories from a conversation
memory.add(
    messages=[
        {"role": "user", "content": "I'm Parth, I live in Delhi and I love Python"}
    ],
    conversation_id=1,
)

# Recall memories
results = memory.search(query="what's my name?", conversation_id=1)
# → [{"content": "User's name is Parth", "score": 0.95, ...}]

# Temporal history
history = memory.history(query="where does user live?", conversation_id=1)
# → Full timeline of location changes
```

### Use as a REST API

```bash
# Install with server extras
pip install aimem-engine[server]

# Create a .env file (see .env.example)
cp .env.example .env

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000
```

Then call the API from any language:

```bash
# Store memories
curl -X POST http://localhost:8000/api/memories/add \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "I love pizza"}], "conversation_id": 1}'

# Search memories
curl "http://localhost:8000/api/memories/search?query=food&conversation_id=1"

# Chat with memory-augmented AI
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "what food do I like?", "conversation_id": 1}'
```

## 🏗️ How It Works

```
User Message
    │
    ▼
┌─────────────────┐
│  Fact Extractor  │  ← LLM pulls facts from conversation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Classifier    │  ← permanent / temporal / episodic
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Embed (768d)  │  ← Text → vector (Gemini / OpenAI / local)
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Contradiction Checker  │  ← Duplicate? Contradiction? New?
│  (cosine + NLP rules)   │
└────────┬────────────────┘
         │
    ┌────┴────┐
    │         │
  STORE    SUPERSEDE  ← Old fact preserved with valid_until
    │         │
    ▼         ▼
┌─────────────────┐
│  SQLite + FAISS │  ← Persistent storage
└─────────────────┘
```

**At retrieval time:**

```
User Question → Embed → FAISS top-k + BM25 + Exact Match
                          → Weighted fusion → Ranked results
                            → Injected as LLM context
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Chat with memory-augmented AI |
| `POST` | `/api/memories/add` | Extract & store memories from messages |
| `GET` | `/api/memories` | List all memories |
| `GET` | `/api/memories/search` | Hybrid search |
| `GET` | `/api/memories/history` | Temporal history of a fact |
| `PUT` | `/api/memories/{id}` | Update a memory |
| `DELETE` | `/api/memories/{id}` | Delete a memory |
| `POST` | `/api/memories/consolidate` | Merge similar memories |
| `POST` | `/api/conversations` | Create a new conversation |

## ⚙️ Configuration

aimem can be configured via environment variables (`.env`) or programmatically:

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Google Gemini API key (free tier available) |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENROUTER_API_KEY` | — | OpenRouter API key |
| `LLM_MODEL` | `gemini-2.5-flash` | Model to use for extraction/chat |
| `EMBEDDING_PROVIDER` | `gemini` | `gemini`, `openai`, or `local` |
| `DATABASE_URL` | `sqlite:///./data/aimem.db` | Database connection string |
| `SIMILARITY_THRESHOLD` | `0.85` | Above this = duplicate |
| `CONTRADICTION_THRESHOLD` | `0.70` | Above this + value change = contradiction |

## 📁 Project Structure

```
aimem/
├── aimem/                  # Core Python package
│   ├── api/routes.py       # FastAPI endpoints
│   ├── db/                 # SQLAlchemy models & database
│   │   └── models/         # Memory, Conversation, Message
│   ├── memory/             # The brain
│   │   ├── memory.py       # Main orchestrator (add/search/history/delete)
│   │   ├── extractor.py    # LLM fact extraction
│   │   ├── classifier.py   # Memory type classification
│   │   ├── embeddings.py   # Text → vector (multi-provider)
│   │   ├── vector_store.py # FAISS index management
│   │   ├── retriever.py    # BM25 + semantic + exact hybrid search
│   │   ├── similar_memory_search.py  # Contradiction detection
│   │   ├── temporal.py     # Temporal reasoning (supersede/history)
│   │   ├── consolidate.py  # Memory merging
│   │   ├── llm.py          # Unified LLM gateway
│   │   └── chat.py         # Memory-augmented chat
│   ├── config.py           # Settings & configure()
│   └── utils/              # Prompts & helpers
├── frontend/               # Next.js web UI
├── main.py                 # FastAPI server entry point
├── pyproject.toml          # Package config (pip install aimem)
└── test_all.py             # Test suite
```

## 📄 License

MIT — see [LICENSE](LICENSE) for details.
