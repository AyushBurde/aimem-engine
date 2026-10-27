"""
Memory Classifier — rule-based type correction.

The extractor (LLM) suggests a type, but can be wrong.
This catches obvious mistakes with keyword rules.
"""


PERMANENT_KEYWORDS = [
    "name is", "born", "birthday", "nationality",
    "mother tongue", "blood type", "allergic to", "graduated from",
]

TEMPORAL_KEYWORDS = [
    "currently", "right now", "these days", "working on",
    "lives in", "living in", "job is", "works at",
]

EPISODIC_KEYWORDS = [
    "today", "yesterday", "just now", "this morning",
    "last night", "this week", "feeling",
]


def classify_memory(fact: dict) -> str:
    """
    Returns corrected memory_type.
    
    "User's name is Parth" + type="temporal" → returns "permanent" (corrected)
    """
    content = fact.get("content", "").lower()

    for keyword in PERMANENT_KEYWORDS:
        if keyword in content:
            return "permanent"

    for keyword in TEMPORAL_KEYWORDS:
        if keyword in content:
            return "temporal"

    for keyword in EPISODIC_KEYWORDS:
        if keyword in content:
            return "episodic"

    # No keyword match → trust the LLM's suggestion
    return fact.get("memory_type", "permanent")
