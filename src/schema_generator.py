import json
from datetime import datetime
from enum import StrEnum, auto
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, EmailStr


class MetaData(BaseModel):
    event_id: UUID
    event_version: int
    event_timestamp: datetime
    producer: str
    event_name: str


# AUTH


class Role(StrEnum):
    user = auto()
    admin = auto()


class UserSchema(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    role: Role


class UserCreatedEvent(MetaData):
    event_version: int = 1
    event_name: str = "user.created"
    payload: UserSchema


class RoleChanged(BaseModel):
    user_id: UUID
    new_role: Role


class RoleChangedEvent(MetaData):
    event_version: int = 1
    event_name: str = "user.role.changed"
    payload: RoleChanged


# TASKS


class TaskSchema(BaseModel):
    id: UUID
    description: str
    status: str
    assigned_to: UUID
    fee: int
    reward: int


class TaskCreatedEvent(MetaData):
    event_version: int = 1
    event_name: str = "task.created"
    payload: TaskSchema


class TaskUpdatedEvent(MetaData):
    event_version: int = 1
    event_name: str = "task.updated"
    payload: TaskSchema


class TaskAddedEvent(MetaData):
    event_version: int = 1
    event_name: str = "task.added"
    payload: TaskSchema


class TaskAssigned(BaseModel):
    task_id: UUID
    assigned_to: UUID


class TaskAssignedEvent(MetaData):
    event_version: int = 1
    event_name: str = "task.assigned"
    payload: TaskAssigned


class TaskDone(BaseModel):
    task_id: UUID
    completed_by: UUID


class TaskDoneEvent(MetaData):
    event_version: int = 1
    event_name: str = "task.done"
    payload: TaskDone


class TransactionSchema(BaseModel):
    id: int
    user_id: UUID
    amount: int
    transaction_type: str


class TransactionCreatedEvent(MetaData):
    event_version: int = 1
    event_name: str = "transaction.applied"
    payload: TransactionSchema


if __name__ == "__main__":
    path = Path(__file__).parent / "schemas/auth/user_created/1.json"
    with path.open("w") as f:
        f.write(json.dumps(UserCreatedEvent.model_json_schema(), indent=2))
    path = Path(__file__).parent / "schemas/auth/user_role_changed/1.json"
    with path.open("w") as f:
        f.write(json.dumps(RoleChangedEvent.model_json_schema(), indent=2))
    path = Path(__file__).parent / "schemas/tasks/task_created/1.json"
    with path.open("w") as f:
        f.write(json.dumps(TaskCreatedEvent.model_json_schema(), indent=2))
    path = Path(__file__).parent / "schemas/tasks/task_updated/1.json"
    with path.open("w") as f:
        f.write(json.dumps(TaskUpdatedEvent.model_json_schema(), indent=2))
    path = Path(__file__).parent / "schemas/tasks/task_added/1.json"
    with path.open("w") as f:
        f.write(json.dumps(TaskAddedEvent.model_json_schema(), indent=2))
    path = Path(__file__).parent / "schemas/tasks/task_assigned/1.json"
    with path.open("w") as f:
        f.write(json.dumps(TaskAssignedEvent.model_json_schema(), indent=2))
    path = Path(__file__).parent / "schemas/tasks/task_done/1.json"
    with path.open("w") as f:
        f.write(json.dumps(TaskDoneEvent.model_json_schema(), indent=2))
    path = Path(__file__).parent / "schemas/accounting/transaction_applied/1.json"
    with path.open("w") as f:
        f.write(json.dumps(TransactionCreatedEvent.model_json_schema(), indent=2))
