"""
Embedding module — converts text into vectors.

Supports:
- Gemini (Default & Free): gemini-embedding-001 (768 dims)
- OpenAI: text-embedding-3-small (1536 dims)
- Local: all-MiniLM-L6-v2 via sentence-transformers (384 dims, 100% offline)
"""

from typing import List
from aimem.config import get_settings

_client = None
_local_model = None


def _ensure_client():
    """Configure Gemini API client on first use or with per-request key."""
    from google import genai
    from aimem.config import current_gemini_key, get_settings
    key = current_gemini_key.get() or get_settings().GEMINI_API_KEY
    if not key:
        raise ValueError(
            "Gemini API key is required. Please provide your Gemini API key in the demo top bar."
        )
    return genai.Client(api_key=key)


def _get_local_model():
    """Lazy-load local SentenceTransformer model."""
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer
        _local_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _local_model


def embed_text(text: str) -> List[float]:
    """Convert a single text into a vector."""
    from aimem.config import current_provider
    settings = get_settings()
    provider = (current_provider.get() or getattr(settings, "EMBEDDING_PROVIDER", "gemini")).lower()
    if provider == "openrouter":
        # OpenRouter users usually use sentence-transformers or openai
        provider = "local" if not settings.OPENAI_API_KEY else "openai"

    if provider == "gemini":
        from google.genai import types
        client = _ensure_client()
        result = client.models.embed_content(
            model=settings.EMBEDDING_MODEL_NAME,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=settings.EMBEDDING_DIMENSION,
            ),
        )
        return result.embeddings[0].values

    elif provider == "openai":
        from aimem.memory.llm import _get_openai_client
        client = _get_openai_client()
        model = settings.EMBEDDING_MODEL_NAME if "embedding" in settings.EMBEDDING_MODEL_NAME else "text-embedding-3-small"
        res = client.embeddings.create(input=text, model=model)
        return res.data[0].embedding

    elif provider in ["local", "sentence-transformers"]:
        model = _get_local_model()
        return model.encode(text).tolist()

    else:
        # Default fallback
        from google.genai import types
        client = _ensure_client()
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=768),
        )
        return result.embeddings[0].values


def batch_embed(texts: List[str]) -> List[List[float]]:
    """Embed multiple texts at once."""
    settings = get_settings()
    provider = getattr(settings, "EMBEDDING_PROVIDER", "gemini").lower()

    if provider in ["local", "sentence-transformers"]:
        model = _get_local_model()
        return [vec.tolist() for vec in model.encode(texts)]

    return [embed_text(t) for t in texts]
