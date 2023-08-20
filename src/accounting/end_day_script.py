from datetime import datetime
from pathlib import Path
from uuid import uuid4

import jsonschema_rs
from sqlalchemy.orm import Session

from src.database import get_db
from src.events import send_event

from .log import log
from .models import Transactions, UserAccounting, UserAuditLog

transaction_applied_schema_v1_path = (
    Path(__file__).parent.parent / "schemas" / "accounting" / "transaction_applied" / "1.json"
)
with transaction_applied_schema_v1_path.open() as f:
    transaction_applied_schema_v1 = f.read()


def get_session() -> Session:
    return next(get_db())


async def send_transaction_event(name: str, payload: dict, schema: str, event_version: int):
    """
    Schema is a json schema
    """
    validator = jsonschema_rs.JSONSchema.from_str(schema)
    data = {
        "event_id": str(uuid4()),
        "event_version": event_version,
        "event_timestamp": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "producer": "accounting",
        "event_name": name,
        "payload": payload,
    }
    validator.validate(data)
    log(f"⬆️'atransaction': {data}")
    await send_event("transactions", data)


def do_payout(user_id: str, amount: int):
    log(f"User {user_id} payout {amount}")


async def end_day():
    """
    Set user balance to 0, create transaction and do payout

    """
    session = get_session()
    # Get all users
    users = session.query(UserAccounting).all()
    for user in users:
        # Create transaction
        if user.balance > 0:
            do_payout(user_id=user.user_id, amount=user.balance)
            audit_log = UserAuditLog(
                user_id=user.user_id,
                created_at=datetime.utcnow(),
                balance_change=-user.balance,
                reason="payout",
            )
        else:
            audit_log = UserAuditLog(
                user_id=user.id,
                created_at=datetime.utcnow(),
                balance_change=user.balance,
                reason="no_payout",
            )
        session.add(audit_log)

        transaction = Transactions(
            user_id=user.id,
            amount=user.balance,
            type="payout",
            created_at=datetime.utcnow(),
            reason="payout",
        )
        session.add(transaction)
        session.commit()
        # Send transaction event
        await send_transaction_event(
            name="transaction_applied",
            payload={
                "id": transaction.id,
                "user_id": transaction.user_id,
                "amount": transaction.amount,
                "transaction_type": transaction.type,
                "created_at": transaction.created_at.isoformat(),
            },
            schema=transaction_applied_schema_v1,
            event_version=1,
        )
        # Set user balance to 0
        user.balance = 0
        session.commit()
        # Send event
        log(f"User {user.id} balance is {user.balance}")
