"""
aimem — Full Integration Test Script
Tests every layer: config → DB → Gemini API → embeddings → memory CRUD → search
"""

import sys
import os
import json

# Ensure we're in the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"
results = []


def test(name, func):
    """Run a test and record result."""
    try:
        func()
        results.append((PASS, name))
        print(f"  {PASS} {name}")
    except Exception as e:
        results.append((FAIL, name, str(e)))
        print(f"  {FAIL} {name}: {e}")


# ═══════════════════════════════════════════════════════
# 1. CONFIG & ENV
# ═══════════════════════════════════════════════════════
print("\n🔧 [1/6] CONFIG & ENVIRONMENT")

def test_env_file():
    assert os.path.exists(".env"), ".env file not found!"

def test_config_loads():
    from aimem.config import get_settings
    s = get_settings()
    assert s is not None

def test_api_key_set():
    from aimem.config import get_settings
    s = get_settings()
    assert s.GEMINI_API_KEY, "GEMINI_API_KEY is empty! Set it in .env"
    assert len(s.GEMINI_API_KEY) > 10, f"API key looks too short: {s.GEMINI_API_KEY[:5]}..."

def test_api_key_format():
    from aimem.config import get_settings
    s = get_settings()
    # Gemini keys typically start with "AI" or "AQ"
    assert not s.GEMINI_API_KEY.startswith("your-"), "API key is still placeholder!"

def test_model_name():
    from aimem.config import get_settings
    s = get_settings()
    assert s.GEMINI_MODEL, "GEMINI_MODEL is empty"
    print(f"       Model: {s.GEMINI_MODEL}")

def test_embedding_model():
    from aimem.config import get_settings
    s = get_settings()
    assert s.EMBEDDING_MODEL_NAME, "EMBEDDING_MODEL_NAME is empty"
    print(f"       Embedding model: {s.EMBEDDING_MODEL_NAME}")

def test_database_url():
    from aimem.config import get_settings
    s = get_settings()
    assert s.DATABASE_URL, "DATABASE_URL is empty"
    print(f"       Database URL: {s.DATABASE_URL}")

test(".env file exists", test_env_file)
test("Config loads", test_config_loads)
test("GEMINI_API_KEY is set", test_api_key_set)
test("API key format valid", test_api_key_format)
test("GEMINI_MODEL configured", test_model_name)
test("Embedding model configured", test_embedding_model)
test("DATABASE_URL configured", test_database_url)

# ═══════════════════════════════════════════════════════
# 2. DATABASE
# ═══════════════════════════════════════════════════════
print("\n🗄️  [2/6] DATABASE")

def test_create_tables():
    from aimem.db.database import create_tables
    create_tables()

def test_db_connection():
    from aimem.db.database import get_engine
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(__import__('sqlalchemy').text("SELECT 1"))

def test_tables_exist():
    from aimem.db.database import get_engine
    from sqlalchemy import inspect
    engine = get_engine()
    insp = inspect(engine)
    tables = insp.get_table_names()
    assert "memories" in tables, f"'memories' table missing. Found: {tables}"
    assert "conversations" in tables, f"'conversations' table missing. Found: {tables}"
    print(f"       Tables: {tables}")

test("Create tables", test_create_tables)
test("DB connection works", test_db_connection)
test("Required tables exist", test_tables_exist)

# ═══════════════════════════════════════════════════════
# 3. GEMINI API (generate_content)
# ═══════════════════════════════════════════════════════
print("\n🤖 [3/6] GEMINI API (generate_content)")

def test_gemini_client():
    from aimem.memory.embeddings import _ensure_client
    client = _ensure_client()
    assert client is not None, "Client is None"

def test_generate_content():
    from aimem.memory.embeddings import _ensure_client
    from aimem.config import get_settings
    client = _ensure_client()
    settings = get_settings()
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents="Say 'hello' and nothing else.",
    )
    assert response.text, "Empty response from Gemini"
    print(f"       Response: {response.text.strip()[:50]}")

test("Gemini client initializes", test_gemini_client)
test("generate_content works", test_generate_content)

# ═══════════════════════════════════════════════════════
# 4. EMBEDDINGS
# ═══════════════════════════════════════════════════════
print("\n📐 [4/6] EMBEDDINGS")

def test_embed_text():
    from aimem.memory.embeddings import embed_text
    vec = embed_text("User loves Python programming")
    assert isinstance(vec, list), f"Expected list, got {type(vec)}"
    assert len(vec) > 0, "Embedding is empty"
    print(f"       Dimension: {len(vec)}")
    return vec

def test_embed_dimension():
    from aimem.memory.embeddings import embed_text
    from aimem.config import get_settings
    vec = embed_text("Test embedding dimension")
    expected = get_settings().EMBEDDING_DIMENSION
    assert len(vec) == expected, f"Expected {expected}d, got {len(vec)}d"

def test_batch_embed():
    from aimem.memory.embeddings import batch_embed
    vecs = batch_embed(["text one", "text two"])
    assert len(vecs) == 2, f"Expected 2 embeddings, got {len(vecs)}"

test("embed_text works", test_embed_text)
test("Embedding dimension correct", test_embed_dimension)
test("batch_embed works", test_batch_embed)

# ═══════════════════════════════════════════════════════
# 5. MEMORY EXTRACTOR
# ═══════════════════════════════════════════════════════
print("\n🧠 [5/6] MEMORY EXTRACTOR")

def test_extract_memories():
    from aimem.memory.extractor import extract_memories
    messages = [
        {"role": "user", "content": "Hi, I'm Parth. I live in Delhi and I love coding in Python."}
    ]
    facts = extract_memories(messages)
    assert isinstance(facts, list), f"Expected list, got {type(facts)}"
    assert len(facts) > 0, "No facts extracted! Gemini returned empty."
    print(f"       Extracted {len(facts)} facts:")
    for f in facts:
        print(f"         • {f['content']} [{f['memory_type']}/{f['category']}]")
    return facts

test("extract_memories works", test_extract_memories)

# ═══════════════════════════════════════════════════════
# 6. FULL PIPELINE (Memory class CRUD)
# ═══════════════════════════════════════════════════════
print("\n🚀 [6/6] FULL PIPELINE (add → search → update → delete)")

def test_full_pipeline():
    from aimem.db.database import get_session_local
    from aimem.memory.memory import Memory

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # Create conversation first
        from aimem.db.models.conversation import Conversation
        convo = Conversation(agent_id="test", user_id="test", title="Integration Test")
        db.add(convo)
        db.commit()
        db.refresh(convo)
        print(f"       Created conversation #{convo.id}")

        memory = Memory(db)

        # ── ADD ──
        print("       [ADD] Sending messages to extract memories...")
        result = memory.add(
            messages=[
                {"role": "user", "content": "I'm Parth, I'm 22 years old and I live in Delhi. I love playing cricket."},
            ],
            conversation_id=convo.id,
        )
        added_count = result["count"]
        print(f"       Added: {added_count} | Updated: {len(result['memories_updated'])} | Skipped: {len(result['memories_skipped'])}")
        for m in result["memories_added"]:
            print(f"         + [{m['id']}] {m['content']}")
        assert added_count > 0, "No memories were added!"

        # ── GET ALL ──
        print("       [GET ALL] Listing memories...")
        all_mems = memory.get_all(conversation_id=convo.id)
        print(f"       Total memories: {len(all_mems)}")
        assert len(all_mems) > 0

        # ── SEARCH ──
        print("       [SEARCH] Searching for 'where does the user live?'...")
        search_result = memory.search(query="where does the user live?", conversation_id=convo.id)
        print(f"       Found {len(search_result['results'])} results:")
        for r in search_result["results"]:
            print(f"         • [{r['memory_id']}] {r['content']} (score: {r['score']})")
        assert len(search_result["results"]) > 0, "Search returned no results!"

        # ── UPDATE ──
        first_id = result["memories_added"][0]["id"]
        print(f"       [UPDATE] Updating memory #{first_id}...")
        updated = memory.update(memory_id=first_id, text="User's name is Parth Sharma")
        assert updated is not None, f"Update returned None for id={first_id}"
        print(f"         Updated to: {updated['content']}")

        # ── CONTRADICTION TEST ──
        print("       [CONTRADICTION] Sending contradicting info...")
        contra_result = memory.add(
            messages=[
                {"role": "user", "content": "Actually I moved to Mumbai recently."},
            ],
            conversation_id=convo.id,
        )
        print(f"       Added: {contra_result['count']} | Updated: {len(contra_result['memories_updated'])} | Skipped: {len(contra_result['memories_skipped'])}")
        if contra_result["memories_updated"]:
            for u in contra_result["memories_updated"]:
                print(f"         ↻ [{u['id']}] \"{u['old_content']}\" → \"{u['new_content']}\"")

        # ── DELETE ──
        print(f"       [DELETE] Deleting memory #{first_id}...")
        deleted = memory.delete(memory_id=first_id)
        assert deleted, f"Delete failed for id={first_id}"
        print(f"         Deleted ✓")

        # Cleanup test data
        remaining = memory.get_all(conversation_id=convo.id)
        for m in remaining:
            memory.delete(memory_id=m["id"])
        db.delete(convo)
        db.commit()
        print("       Cleaned up test data ✓")

    finally:
        db.close()

test("Full pipeline (add/search/update/contradict/delete)", test_full_pipeline)

# ═══════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════
print("\n" + "═" * 55)
passed = sum(1 for r in results if r[0] == PASS)
failed = sum(1 for r in results if r[0] == FAIL)
total = len(results)

if failed == 0:
    print(f"  🎉 ALL {total} TESTS PASSED!")
else:
    print(f"  Results: {passed}/{total} passed, {failed} failed")
    print("\n  Failed tests:")
    for r in results:
        if r[0] == FAIL:
            print(f"    {FAIL} {r[1]}: {r[2]}")

print("═" * 55 + "\n")
