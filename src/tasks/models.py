from sqlalchemy import (
    UUID,
    Column,
    DateTime,
    Integer,
    String,
    func,
)

from src.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    description = Column(String, nullable=False)
    status = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    fee = Column(Integer, nullable=False)
    reward = Column(Integer, nullable=False)


class User(Base):
    __tablename__ = "tasks_users"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    username = Column(String, nullable=False)
    email = Column(String, nullable=False)
    role = Column(String, nullable=False)
