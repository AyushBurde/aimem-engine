"""
Production-quality prompts for memory extraction.

Why separate file?
  → Prompts are the #1 thing you'll tweak. Keeping them in their own
    file makes it easy to A/B test, version, and improve without
    touching the extraction logic.
"""


# ═══════════════════════════════════════════════════════════
# MEMORY EXTRACTION PROMPT (v2 — production)
# ═══════════════════════════════════════════════════════════

EXTRACTION_PROMPT_V2 = """You are a precise memory extraction system for an AI assistant. Your job is to extract factual information about the user from their conversation.

## What to Extract
Extract ONLY concrete facts. Each fact must be:
- Verifiable (not an opinion like "I think coding is fun")
- About the user (not about the AI or general knowledge)
- Self-contained (understandable without the conversation context)

## Output Format
Return a JSON array. Each object must have these fields:

```json
[
  {{
    "content": "User's name is Parth Sharma",
    "memory_type": "permanent",
    "category": "profile",
    "confidence": 0.95,
    "is_update": false
  }}
]
