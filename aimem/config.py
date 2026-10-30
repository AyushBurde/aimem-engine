"""
Configuration — Settings class + configure() for library mode.

Two ways to configure:
  1. .env file (for server/FastAPI mode)
  2. aimem.configure(...) (for library/pip mode)
"""

import os
import contextvars
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

current_provider: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_provider", default=None)
current_gemini_key: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_gemini_key", default=None)
current_openai_key: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_openai_key", default=None)
current_openrouter_key: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_openrouter_key", default=None)


class Settings(BaseSettings):
    """All configuration for aimem lives here."""

    # ── LLM Provider Configuration ───────────────────────
    LLM_PROVIDER: str = "gemini"               # "gemini" | "openai" | "openrouter"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: Optional[str] = None      # e.g., "https://openrouter.ai/api/v1"
    OPENROUTER_API_KEY: str = ""
    LLM_MODEL: str = "gemini-3.5-flash-lite"    # Auto-set to gpt-4o-mini or claude
    EXTRACTION_TEMPERATURE: float = 0.1

    # ── Embeddings ───────────────────────────────────────
    EMBEDDING_PROVIDER: str = "gemini"         # "gemini" | "openai" | "local"
    EMBEDDING_MODEL_NAME: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768             # 768 (Gemini), 1536 (OpenAI), 384 (Local)

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./data/aimem.db"

    # ── FAISS ────────────────────────────────────────────
    FAISS_INDEX_PATH: str = "data/faiss.index"
    FAISS_ID_MAP_PATH: str = "data/faiss_id_map.json"

    # ── Retrieval weights ────────────────────────────────
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_WEIGHT_BM25: float = 0.3
    RETRIEVAL_WEIGHT_SEMANTIC: float = 0.5
    RETRIEVAL_WEIGHT_EXACT: float = 0.2
    BM25_K1: float = 1.5
    BM25_B: float = 0.75

    # ── Contradiction detection ──────────────────────────
    SIMILARITY_THRESHOLD: float = 0.85      # above this = duplicate
    CONTRADICTION_THRESHOLD: float = 0.70   # above this + negation = contradiction

    # ── App ──────────────────────────────────────────────
    DEBUG: bool = False

        # ── Auth / JWT ───────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-to-a-random-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours


    def model_post_init(self, __context):
        # Auto-detect provider if user didn't explicitly specify LLM_PROVIDER
        if self.LLM_PROVIDER == "gemini" and not self.GEMINI_API_KEY:
            if self.OPENAI_API_KEY:
                self.LLM_PROVIDER = "openai"
                if self.EMBEDDING_PROVIDER == "gemini":
                    self.EMBEDDING_PROVIDER = "openai"
                    self.EMBEDDING_MODEL_NAME = "text-embedding-3-small"
                    self.EMBEDDING_DIMENSION = 1536
                if self.LLM_MODEL == "gemini-3.5-flash-lite":
                    self.LLM_MODEL = "gpt-4o-mini"
            elif self.OPENROUTER_API_KEY:
                self.LLM_PROVIDER = "openrouter"
                if not self.OPENAI_BASE_URL:
                    self.OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
                if self.LLM_MODEL == "gemini-3.5-flash-lite":
                    self.LLM_MODEL = "anthropic/claude-3.5-sonnet"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# ── Global settings singleton ─────────────────────────────

_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def configure(
    api_key: str = None,
    gemini_api_key: str = None,
    openai_api_key: str = None,
    openrouter_api_key: str = None,
    llm_provider: str = None,
    llm_model: str = None,
    model: str = None,
    embedding_provider: str = None,
    embedding_model: str = None,
    embedding_dimension: int = None,
    database_url: str = None,
    debug: bool = None,
    similarity_threshold: float = None,
    contradiction_threshold: float = None,
    **kwargs,
) -> Settings:
    """
    Programmatic configuration for library usage.

    Usage:
        import aimem

        # Option 1: Gemini (Free)
        aimem.configure(gemini_api_key="AIzaSy...")

        # Option 2: OpenAI (Direct)
        aimem.configure(openai_api_key="sk-...")

        # Option 3: OpenRouter (Claude, etc.)
        aimem.configure(
            openrouter_api_key="sk-or-...",
            llm_model="anthropic/claude-3.5-sonnet"
        )
    """
    global _settings
    overrides = {}

    # 1. Detect Gemini
    if gemini_api_key is not None:
        overrides["GEMINI_API_KEY"] = gemini_api_key
        overrides["LLM_PROVIDER"] = "gemini"
    elif api_key is not None and not (openai_api_key or openrouter_api_key):
        overrides["GEMINI_API_KEY"] = api_key
        overrides["LLM_PROVIDER"] = "gemini"

    # 2. Detect OpenAI
    if openai_api_key is not None:
        overrides["OPENAI_API_KEY"] = openai_api_key
        if llm_provider is None:
            overrides["LLM_PROVIDER"] = "openai"
        if embedding_provider is None:
            overrides["EMBEDDING_PROVIDER"] = "openai"
            overrides["EMBEDDING_MODEL_NAME"] = "text-embedding-3-small"
            overrides["EMBEDDING_DIMENSION"] = 1536

    # 3. Detect OpenRouter
    if openrouter_api_key is not None:
        overrides["OPENROUTER_API_KEY"] = openrouter_api_key
        overrides["OPENAI_API_KEY"] = openrouter_api_key
        overrides["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
        if llm_provider is None:
            overrides["LLM_PROVIDER"] = "openrouter"

    # Provider override if explicitly specified
    if llm_provider is not None:
        overrides["LLM_PROVIDER"] = llm_provider.lower()

    # Model configuration
    chosen_model = llm_model or model
    if chosen_model is not None:
        overrides["LLM_MODEL"] = chosen_model
        overrides["GEMINI_MODEL"] = chosen_model
    elif overrides.get("LLM_PROVIDER") == "openai" and "LLM_MODEL" not in overrides:
        overrides["LLM_MODEL"] = "gpt-4o-mini"
    elif overrides.get("LLM_PROVIDER") == "openrouter" and "LLM_MODEL" not in overrides:
        overrides["LLM_MODEL"] = "anthropic/claude-3.5-sonnet"

    # Embeddings
    if embedding_provider is not None:
        overrides["EMBEDDING_PROVIDER"] = embedding_provider.lower()
    if embedding_model is not None:
        overrides["EMBEDDING_MODEL_NAME"] = embedding_model
    if embedding_dimension is not None:
        overrides["EMBEDDING_DIMENSION"] = embedding_dimension

    # Database
    if database_url is not None:
        overrides["DATABASE_URL"] = database_url

    # Debug & thresholds
    if debug is not None:
        overrides["DEBUG"] = debug
    if similarity_threshold is not None:
        overrides["SIMILARITY_THRESHOLD"] = similarity_threshold
    if contradiction_threshold is not None:
        overrides["CONTRADICTION_THRESHOLD"] = contradiction_threshold

    # Pass through extra kwargs
    for key, value in kwargs.items():
        overrides[key.upper()] = value

    # Set as environment variables
    for key, value in overrides.items():
        os.environ[key] = str(value)

    # Force re-creation of settings
    _settings = Settings()
    try:
        import aimem.memory.llm as llm_mod
        llm_mod._openai_client = None
    except Exception:
        pass
    return _settings


def reset_settings():
    """Reset settings (useful for testing)."""
    global _settings
    _settings = None
    try:
        import aimem.memory.llm as llm_mod
        llm_mod._openai_client = None
    except Exception:
        pass

