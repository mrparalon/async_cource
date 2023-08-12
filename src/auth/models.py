from sqlalchemy import (
    Column,
    DateTime,
    String,
    UniqueConstraint,
    func,
)

from src.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)  # uuid
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)

    __table_args__ = (UniqueConstraint("email", "username", name="unique_email_username"),)
