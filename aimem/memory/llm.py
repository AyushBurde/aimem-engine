"""
Unified LLM Gateway for Aimem.

Routes calls dynamically to:
- Google Gemini (Default & Free)
- OpenAI (gpt-4o, gpt-4o-mini)
- OpenRouter (Claude, Llama, DeepSeek, etc.)
"""

import json
import logging
from typing import Optional, Dict, List, Any
from aimem.config import get_settings

logger = logging.getLogger(__name__)

_openai_client = None


def _get_gemini_client():
    from aimem.memory.embeddings import _ensure_client
    return _ensure_client()


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "The 'openai' package is required to use OpenAI or OpenRouter. "
                "Install it with: pip install openai"
            )
        settings = get_settings()
        api_key = settings.OPENAI_API_KEY or settings.OPENROUTER_API_KEY
        base_url = settings.OPENAI_BASE_URL
        if settings.LLM_PROVIDER == "openrouter" and not base_url:
            base_url = "https://openrouter.ai/api/v1"
        _openai_client = OpenAI(api_key=api_key, base_url=base_url)
    return _openai_client


def generate_text(prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.1) -> str:
    """Generate free-form text from any configured LLM provider."""
    settings = get_settings()
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini":
        from google.genai import types
        client = _get_gemini_client()
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_prompt if system_prompt else None,
        )
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL or settings.LLM_MODEL,
            contents=prompt,
            config=config,
        )
        return response.text or ""

    elif provider in ["openai", "openrouter"]:
        client = _get_openai_client()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=settings.LLM_MODEL or ("gpt-4o-mini" if provider == "openai" else "anthropic/claude-3.5-sonnet"),
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


def generate_json(prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.1) -> Any:
    """Generate parsed JSON from any configured LLM provider."""
    settings = get_settings()
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini":
        from google.genai import types
        client = _get_gemini_client()
        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            system_instruction=system_prompt if system_prompt else None,
        )
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL or settings.LLM_MODEL,
            contents=prompt,
            config=config,
        )
        text = response.text or "[]"
        return json.loads(text)

    elif provider in ["openai", "openrouter"]:
        client = _get_openai_client()
        messages = []
        sys_msg = system_prompt or "You are a helpful assistant that outputs only valid JSON."
        messages.append({"role": "system", "content": sys_msg})
        messages.append({"role": "user", "content": prompt})

        model_name = settings.LLM_MODEL or ("gpt-4o-mini" if provider == "openai" else "anthropic/claude-3.5-sonnet")
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            parsed = json.loads(raw)
            # If wrapped in a dictionary key like {"facts": [...]}, extract the inner list
            if isinstance(parsed, dict) and len(parsed) == 1 and isinstance(list(parsed.values())[0], list):
                return list(parsed.values())[0]
            return parsed
        except Exception:
            # Fallback for providers that don't support response_format
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
            )
            raw = response.choices[0].message.content or "[]"
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1]
                if clean.endswith("```"):
                    clean = clean.rsplit("```", 1)[0]
            return json.loads(clean.strip())

    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
