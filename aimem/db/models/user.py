from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from aimem.db.database import Base

class User(Base) : 
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer,primary_key = True, autoincrement = True)
    email : Mapped[str] = mapped_column(String(255), unique = True, nullable = False, index = True)
    password_hash : Mapped[str] = mapped_column(String(255), nullable = False)
    name : Mapped[str] = mapped_column(String(100), nullable = True) 
    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        )
    

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
