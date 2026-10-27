"""
Chat with Memory — recalls memories to answer questions naturally.
"""

from typing import List, Dict
from aimem.memory.llm import generate_text

CHAT_PROMPT = """You are an AI assistant with access to a memory system.
You remember things the user has told you in previous conversations.

Here are the relevant memories you have about this user:
{memories}

Based on these memories, respond to the user's message naturally and helpfully.
If the memories contain the answer, use them confidently (e.g. "Your name is Parth!").
If you don't have relevant memories, say you don't remember that yet and ask them to tell you.
Keep responses concise and friendly.

User: {message}"""


def chat_with_memory(
    message: str,
    memories: List[Dict],
) -> str:
    """Generate an LLM response using recalled memories as context."""
    if memories:
        memory_text = "\n".join(
            f"- {m['content']} (type: {m.get('memory_type', 'unknown')}, "
            f"relevance: {m.get('score', 0):.0%})"
            for m in memories
        )
    else:
        memory_text = "(No memories stored yet)"

    prompt = CHAT_PROMPT.format(memories=memory_text, message=message)
    return generate_text(prompt)
