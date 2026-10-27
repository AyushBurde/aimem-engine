"""
SQLAlchemy engine, session factory, and declarative Base.

- Engine:       the actual connection to your database
- SessionLocal: creates sessions (think: one session = one unit of work)
- Base:         parent class for all our models (Memory, Conversation, Message)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from aimem.config import get_settings


class Base(DeclarativeBase):
    """Every model (Memory, Conversation, Message) inherits from this.
    SQLAlchemy uses this to track all tables and create them."""
    pass


# ── Lazy-initialized globals ──────────────────────────────
_engine = None
_SessionLocal = None


def get_engine():
    """Create the database engine on first call, reuse after."""
    global _engine
    if _engine is None:
        settings = get_settings()
        url = settings.DATABASE_URL

        # SQLite needs this flag for FastAPI's multi-threaded access
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        _engine = create_engine(
            url,
            connect_args=connect_args,
            echo=settings.DEBUG,  # When True, prints every SQL query to console
        )
    return _engine


def get_session_local():
    """Create the session factory on first call, reuse after."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,   # We control when to commit
            autoflush=False,    # We control when to flush to DB
            bind=get_engine(),  # Bind sessions to our engine
        )
    return _SessionLocal


def SessionLocal():
    """Create and return a new database session instance."""
    factory = get_session_local()
    return factory()


def get_db():
    """FastAPI dependency — gives each API request its own DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in the database. Called once on app startup."""
    import aimem.db.models  # noqa: F401
    Base.metadata.create_all(bind=get_engine())
