from pathlib import Path

import jsonschema_rs
import orjson
from aiokafka import AIOKafkaConsumer
from loguru import logger
from sqlalchemy.orm import Session

from src.database import get_db

from .log import log
from .models import UserAccounting

user_create_schema_v1_path = Path(__file__).parent.parent / "schemas" / "auth" / "user_created" / "1.json"
user_role_changed_v1_path = Path(__file__).parent.parent / "schemas" / "auth" / "user_role_changed" / "1.json"

with user_create_schema_v1_path.open() as f:
    user_create_schema_v1 = f.read()
with user_role_changed_v1_path.open() as f:
    user_role_changed_v1 = f.read()


def get_session() -> Session:
    return next(get_db())


def log_consumer(message: str):
    log(f"⬇️{message}")


def handle_user_created(user_event: dict) -> UserAccounting:
    db_user = UserAccounting(
        id=user_event["id"],
        username=user_event["username"],
        role=user_event["role"],
        email=user_event["email"],
        balance=0,
    )
    session = get_session()
    session.add(db_user)
    session.commit()
    log_consumer(f"UserAccounting created: {db_user}")
    return db_user


def handle_user_role_changed(role_changed_event: dict) -> UserAccounting:
    session = get_session()
    db_user = session.query(UserAccounting).get(role_changed_event["user_id"])
    if not db_user:
        raise ValueError(f"UserAccounting with id {role_changed_event['user_id']} not found")
    db_user.role = role_changed_event["role"]
    session.commit()
    log_consumer(f"UserAccounting role changed: {db_user.id} from {role_changed_event['old_role']} to {db_user.role}")
    return db_user


@logger.catch
async def accounting_auth_worker():
    consumer = AIOKafkaConsumer(
        "users_streaming",
        bootstrap_servers="localhost:9092",
        group_id="accounting_auth",
        enable_auto_commit=True,  # Is True by default anyway
        auto_commit_interval_ms=1000,  # Autocommit every second
        auto_offset_reset="earliest",  # If committed offset not found, start
    )
    await consumer.start()
    log_consumer("consumer started")
    try:
        # Consume messages
        async for msg in consumer:
            data = orjson.loads(msg.value.decode())
            event_name = data["event_name"]
            log_consumer(f"Event {event_name} received")
            if event_name == "user.created":
                validator = jsonschema_rs.JSONSchema.from_str(user_create_schema_v1)
                validator.validate(data)
                handle_user_created(data["payload"])
            elif event_name == "user.role_changed":
                validator = jsonschema_rs.JSONSchema.from_str(user_role_changed_v1)
                validator.validate(data)
                handle_user_role_changed(data["payload"])
            else:
                log_consumer(f"Unknown event name {event_name}")

    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()
