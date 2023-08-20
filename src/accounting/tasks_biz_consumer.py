from datetime import datetime
from pathlib import Path
from uuid import uuid4

import jsonschema_rs
import orjson
from aiokafka import AIOKafkaConsumer
from loguru import logger
from sqlalchemy.orm import Session

from src.database import get_db
from src.events import send_event

from .log import log
from .models import CompanyProfit, TasksAccounting, Transactions, UserAccounting, UserAuditLog

task_created_schema_v1_path = Path(__file__).parent.parent / "schemas" / "tasks" / "task_created" / "1.json"
task_updated_schema_v1_path = Path(__file__).parent.parent / "schemas" / "tasks" / "task_updated" / "1.json"
task_added_schema_v1_path = Path(__file__).parent.parent / "schemas" / "tasks" / "task_added" / "1.json"
task_assigned_schema_v1_path = Path(__file__).parent.parent / "schemas" / "tasks" / "task_assigned" / "1.json"
task_done_schema_v1_path = Path(__file__).parent.parent / "schemas" / "tasks" / "task_done" / "1.json"

transaction_applied_schema_v1_path = (
    Path(__file__).parent.parent / "schemas" / "accounting" / "transaction_applied" / "1.json"
)

with task_added_schema_v1_path.open() as f:
    task_added_schema_v1 = f.read()
with task_assigned_schema_v1_path.open() as f:
    task_assigned_schema_v1 = f.read()
with task_done_schema_v1_path.open() as f:
    task_done_schema_v1 = f.read()
with transaction_applied_schema_v1_path.open() as f:
    transaction_applied_schema_v1 = f.read()


def get_session() -> Session:
    return next(get_db())


def log_consumer(message: str):
    log(f"⬇️  {message}")


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


def handle_task_added(task_event: dict) -> TasksAccounting:
    db_task = TasksAccounting(
        id=task_event["id"],
        description=task_event["description"],
        status=task_event["status"],
        assigned_to=task_event["assigned_to"],
        fee=task_event["fee"],
        reward=task_event["reward"],
    )
    session = get_session()
    session.add(db_task)
    session.commit()
    log_consumer(f"Task created: {db_task}")
    return db_task


def handle_task_assigned(task_assigned_event: dict):
    session = get_session()
    db_task = session.query(TasksAccounting).get(task_assigned_event["task_id"])
    if not db_task:
        db_task = TasksAccounting(
            id=task_assigned_event["id"],
        )
    db_task.assigned_to = task_assigned_event["assigned_to"]
    user = session.query(UserAccounting).get(task_assigned_event["assigned_to"])
    if not user:
        return None
    user.balance -= db_task.fee
    audit_log = UserAuditLog(
        user_id=user.id,
        balance_change=-db_task.fee,
        reason=f"Task assigned: {db_task.id}",
    )
    company_profit = session.query(CompanyProfit).first()
    company_profit.balance += db_task.fee
    transaction = Transactions(
        user_id=user.id,
        amount=-db_task.fee,
        reason=f"Task assigned: {db_task.id}",
        type="enrollment",
    )

    session.add(user)
    session.add(db_task)
    session.add(audit_log)
    session.add(company_profit)
    session.add(transaction)
    session.commit()
    log_consumer(f"TaskAccounting assigned: {db_task.id} to {db_task.assigned_to}")
    return db_task


def handle_task_done(task_done_event: dict):
    session = get_session()
    db_task = session.query(TasksAccounting).get(task_done_event["task_id"])
    if not db_task:
        db_task = TasksAccounting(
            id=task_done_event["id"],
        )
    db_task.status = "done"
    user = session.query(UserAccounting).get(task_done_event["completed_by"])
    if not user:
        return None
    user.balance += db_task.reward
    audit_log = UserAuditLog(
        user_id=user.id,
        balance_change=db_task.reward,
        reason=f"Task done: {db_task.id}",
    )
    company_profit = session.query(CompanyProfit).first()
    company_profit.balance -= db_task.reward
    transaction = Transactions(
        user_id=user.id, amount=db_task.reward, reason=f"Task done: {db_task.id}", type="withdrawal"
    )

    session.add(user)
    session.add(db_task)
    session.add(audit_log)
    session.add(company_profit)
    session.add(transaction)
    session.commit()
    log_consumer(f"TaskAccounting done: {db_task.id}")
    return db_task


@logger.catch
async def accounting_tasks_lificycle_worker():
    consumer = AIOKafkaConsumer(
        "tasks_lifecicle",
        bootstrap_servers="localhost:9092",
        group_id="tasks_auth",
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
            if event_name == "task.added":
                validator = jsonschema_rs.JSONSchema.from_str(task_added_schema_v1)
                validator.validate(data)
                handle_task_added(data["payload"])
            elif event_name == "task.assigned":
                validator = jsonschema_rs.JSONSchema.from_str(task_assigned_schema_v1)
                validator.validate(data)
                handle_task_assigned(data["payload"])
            elif event_name == "task.done":
                validator = jsonschema_rs.JSONSchema.from_str(task_done_schema_v1)
                validator.validate(data)
                handle_task_done(data["payload"])

            else:
                log_consumer(f"Unknown event name {event_name}")

    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()
