"""
Memory Extractor — uses LLM to pull facts from conversations.

Input:  [{"role": "user", "content": "I'm Parth, I live in Delhi"}]
Output: [{"content": "User's name is Parth", "memory_type": "permanent", ...}]
"""

from typing import List, Dict
from aimem.memory.llm import generate_json
from aimem.memory.classifier import classify_memory

EXTRACTION_PROMPT = """You are a memory extraction system. Analyze the conversation and extract important facts about the user.

For each fact, provide:
- "content": the fact as a clear, standalone sentence
- "memory_type": "permanent" (name, birthday), "temporal" (current city, job), or "episodic" (what happened today)
- "category": "profile", "preference", "hobby", "work", "relationship", "health", "location", or "other"
- "confidence": 0.0 to 1.0

Rules:
- Only extract FACTS, not greetings or opinions
- Write in third person: "User likes Python" not "I like Python"
- If no facts found, return empty list
- Return ONLY valid JSON array

Conversation:
{conversation}

Return JSON array:"""


def extract_memories(messages: List[Dict]) -> List[Dict]:
    """Analyze messages and extract memory-worthy facts."""
    conversation = "\n".join(
        f"{msg['role'].upper()}: {msg['content']}" for msg in messages
    )

    try:
        facts = generate_json(EXTRACTION_PROMPT.format(conversation=conversation))
        if not isinstance(facts, list):
            return []
    except Exception:
        return []

    # Clean and classify
    cleaned_facts = []
    for fact in facts:
        if not isinstance(fact, dict):
            continue
        content = fact.get("content", "").strip()
        if not content:
            continue

        fact["content"] = content
        fact["confidence"] = min(max(float(fact.get("confidence", 0.8)), 0.0), 1.0)
        fact["category"] = fact.get("category", "other").lower()

        # Run through rule-based classifier to catch common LLM mistakes
        fact["memory_type"] = classify_memory(fact)

        cleaned_facts.append(fact)

    return cleaned_facts
