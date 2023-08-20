from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class TasksAccounting(Base):
    __tablename__ = "accounting_tasks"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now())
    description = Column(String, nullable=True)
    status = Column(String, nullable=True)
    assigned_to = Column(String, nullable=True)
    fee = Column(Integer, nullable=True)
    reward = Column(Integer, nullable=True)


class UserAccounting(Base):
    __tablename__ = "accounting_users"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    username = Column(String, nullable=False)
    email = Column(String, nullable=False)
    role = Column(String, nullable=False)
    balance = Column(Integer, nullable=False, default=0)


class UserAuditLog(Base):
    __tablename__ = "audit_log_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    user_id = Column(String, nullable=False)
    balance_change = Column(Integer, nullable=False, default=0)
    reason = Column(String, nullable=False)


class CompanyProfit(Base):
    __tablename__ = "accounting_company"

    id: Mapped[int] = mapped_column(primary_key=True)
    date = Column(DateTime, server_default=func.now(), nullable=False)
    amount = Column(Integer, nullable=False, default=0)


class Transactions(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    user_id = Column(String, nullable=False)
    amount = Column(Integer, nullable=False, default=0)
    type = Column(String, nullable=False)
    reason = Column(String, nullable=False)
