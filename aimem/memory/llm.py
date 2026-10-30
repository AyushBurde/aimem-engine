"""
Unified LLM Gateway for Aimem.

Routes calls dynamically to:
- Google Gemini (Default & Free)
- OpenAI (gpt-4o, gpt-4o-mini)
- OpenRouter (Claude, Llama, DeepSeek, etc.)

Includes auto-retry + model fallback for Gemini overload (503/429).
"""

import json
import logging
import time
from typing import Optional, Dict, List, Any
from aimem.config import get_settings

logger = logging.getLogger(__name__)

_openai_client = None

# ── Gemini fallback chain (tried in order if overloaded) ──
GEMINI_FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",   # Primary: ultra-fast, high throughput, low congestion
    "gemini-3.5-flash",        # Slightly heavier but still fast
    "gemini-3.6-flash",        # Stable mid-tier
]


def _get_gemini_client():
    from aimem.memory.embeddings import _ensure_client
    return _ensure_client()


def _call_gemini_with_retry(client, contents, config, primary_model: str, max_retries: int = 2):
    """
    Call Gemini with auto-retry on 503/429 and fallback to lighter models.
    Total worst-case: primary(3 tries) + lite(2 tries) + 2.0(2 tries) = ~30s max.
    """
    models_to_try = [primary_model]
    for fallback in GEMINI_FALLBACK_MODELS:
        if fallback != primary_model:
            models_to_try.append(fallback)

    last_err = None
    for model_name in models_to_try:
        for attempt in range(max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                if model_name != primary_model:
                    logger.info(f"Gemini fallback succeeded with {model_name}")
                return response
            except Exception as e:
                err_str = str(e).lower()
                last_err = e
                is_overloaded = any(kw in err_str for kw in [
                    "503", "429", "overloaded", "high demand",
                    "unavailable", "resource exhausted", "quota",
                ])
                is_not_found = any(kw in err_str for kw in ["404", "not found", "not available"])

                if is_not_found:
                    logger.warning(f"Model {model_name} not found, trying next fallback...")
                    break  # Skip to next model

                if is_overloaded and attempt < max_retries:
                    wait = 1.0 * (attempt + 1)
                    logger.warning(f"Gemini {model_name} overloaded (attempt {attempt+1}), retrying in {wait}s...")
                    time.sleep(wait)
                    continue

                if is_overloaded:
                    logger.warning(f"Gemini {model_name} still overloaded after {max_retries+1} attempts, trying next model...")
                    break  # Try next fallback model

                # Non-retryable error (auth, invalid request, etc.)
                raise e

    raise last_err


def _get_openai_client():
    from aimem.config import current_openai_key
    req_key = current_openai_key.get()
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "The 'openai' package is required to use OpenAI or OpenRouter. "
            "Install it with: pip install openai"
        )
    settings = get_settings()
    api_key = req_key or settings.OPENAI_API_KEY or settings.OPENROUTER_API_KEY
    if not api_key:
        raise ValueError("OpenAI API key is required. Please provide it in the demo top bar.")
    base_url = settings.OPENAI_BASE_URL
    if settings.LLM_PROVIDER == "openrouter" and not base_url:
        base_url = "https://openrouter.ai/api/v1"
    return OpenAI(api_key=api_key, base_url=base_url)


def generate_text(prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.1) -> str:
    """Generate free-form text from any configured LLM provider."""
    from aimem.config import current_provider
    settings = get_settings()
    provider = (current_provider.get() or settings.LLM_PROVIDER).lower()

    if provider == "gemini":
        from google.genai import types
        client = _get_gemini_client()
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_prompt if system_prompt else None,
        )
        model = settings.GEMINI_MODEL or settings.LLM_MODEL
        response = _call_gemini_with_retry(client, prompt, config, model)
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
    from aimem.config import current_provider
    settings = get_settings()
    provider = (current_provider.get() or settings.LLM_PROVIDER).lower()

    if provider == "gemini":
        from google.genai import types
        client = _get_gemini_client()
        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            system_instruction=system_prompt if system_prompt else None,
        )
        model = settings.GEMINI_MODEL or settings.LLM_MODEL
        response = _call_gemini_with_retry(client, prompt, config, model)
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
