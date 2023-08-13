import orjson
from aiokafka import AIOKafkaConsumer
from loguru import logger
from sqlalchemy.orm import Session

from src.database import get_db

from .models import UserTasks


def get_session() -> Session:
    return next(get_db())


def handle_user_created(user_event: dict) -> UserTasks:
    db_user = UserTasks(
        id=user_event["id"],
        username=user_event["username"],
        role=user_event["role"],
        email=user_event["email"],
    )
    session = get_session()
    session.add(db_user)
    session.commit()
    logger.info(f"UserTasks created: {db_user}")
    return db_user


def handle_user_role_changed(role_changed_event: dict) -> UserTasks:
    session = get_session()
    db_user = session.query(UserTasks).get(role_changed_event["user_id"])
    if not db_user:
        raise ValueError(f"UserTasks with id {role_changed_event['user_id']} not found")
    db_user.role = role_changed_event["role"]
    session.commit()
    logger.info(f"UserTasks role changed: {db_user.id} from {role_changed_event['old_role']} to {db_user.role}")
    return db_user


async def tasks_auth_worker():
    consumer = AIOKafkaConsumer(
        "auth",
        bootstrap_servers="localhost:9092",
        group_id="tasks_auth",
        enable_auto_commit=True,  # Is True by default anyway
        auto_commit_interval_ms=1000,  # Autocommit every second
        auto_offset_reset="earliest",  # If committed offset not found, start
    )
    # Get cluster layout and join group `my-group`
    await consumer.start()
    logger.info("consumer started")
    try:
        # Consume messages
        async for msg in consumer:
            data = orjson.loads(msg.value.decode())
            event_name = data["name"]
            if event_name == "user.created":
                handle_user_created(data["payload"])
            elif event_name == "user.role_changed":
                handle_user_role_changed(data["payload"])
            else:
                logger.warning(f"Unknown event name {event_name}")

    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()
