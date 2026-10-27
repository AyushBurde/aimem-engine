"""
aimem — AI Agent Memory Service.

Usage as a library:
    from aimem import configure, create_tables, Memory, SessionLocal

    configure(gemini_api_key="your-key") # or openai_api_key="sk-..."
    create_tables()

    db = SessionLocal()
    memory = Memory(db)
"""

from aimem.config import configure, get_settings, Settings
from aimem.memory.memory import Memory
from aimem.db.database import get_db, get_engine, create_tables, Base, SessionLocal

__version__ = "0.1.0"

__all__ = [
    # Core
    "Memory",
    "configure",
    "get_settings",
    "Settings",
    # Database
    "get_db",
    "get_engine",
    "create_tables",
    "SessionLocal",
    "Base",
    # Meta
    "__version__",
]
