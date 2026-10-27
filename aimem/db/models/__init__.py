"""
Model registry — importing here ensures all models are registered with SQLAlchemy's Base.
"""

from aimem.db.models.memory import Memory       # noqa: F401
from aimem.db.models.conversation import Conversation  # noqa: F401
from aimem.db.models.message import Message     # noqa: F401
from aimem.db.models.user import User 
