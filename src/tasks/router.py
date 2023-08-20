import random
from datetime import datetime
from enum import StrEnum, auto
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

import jsonschema_rs
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict
from pydantic.functional_serializers import PlainSerializer
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from src.database import get_db
from src.events import send_event

from .log import log
from .models import Task, UserTasks

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

StrUUID = Annotated[UUID, PlainSerializer(lambda x: str(x), return_type=str, when_used="unless-none")]

task_created_schema_v1_path = Path(__file__).parent.parent / "schemas" / "tasks" / "task_created" / "1.json"
task_updated_schema_v1_path = Path(__file__).parent.parent / "schemas" / "tasks" / "task_updated" / "1.json"
task_added_schema_v1_path = Path(__file__).parent.parent / "schemas" / "tasks" / "task_added" / "1.json"
task_assigned_schema_v1_path = Path(__file__).parent.parent / "schemas" / "tasks" / "task_assigned" / "1.json"
task_done_schema_v1_path = Path(__file__).parent.parent / "schemas" / "tasks" / "task_done" / "1.json"

with task_created_schema_v1_path.open() as f:
    task_created_schema_v1 = f.read()
with task_updated_schema_v1_path.open() as f:
    task_updated_schema_v1 = f.read()
with task_added_schema_v1_path.open() as f:
    task_added_schema_v1 = f.read()
with task_assigned_schema_v1_path.open() as f:
    task_assigned_schema_v1 = f.read()
with task_done_schema_v1_path.open() as f:
    task_done_schema_v1 = f.read()


class Status(StrEnum):
    todo = auto()
    done = auto()


class TaskCreatePayload(BaseModel):
    description: str


class TaskSchema(BaseModel):
    id: StrUUID
    description: str
    status: str
    assigned_to: StrUUID
    fee: int
    reward: int

    model_config = ConfigDict(from_attributes=True)


router = APIRouter()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserTasks:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    user = db.query(UserTasks).filter(UserTasks.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user


async def send_task_streaming_event(name: str, payload: dict, schema: str, event_version: int):
    """
    Schema is a json schema
    """
    validator = jsonschema_rs.JSONSchema.from_str(schema)
    data = {
        "event_id": str(uuid4()),
        "event_version": event_version,
        "event_timestamp": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "producer": "tasks",
        "event_name": name,
        "payload": payload,
    }
    validator.validate(data)
    log(f"⬆️'tasks_streamin' : {data}")
    await send_event("tasks_streaming", data)


async def send_task_biz_event(name: str, payload: dict, schema: str, event_version: int):
    """
    Schema is a json schema
    """
    validator = jsonschema_rs.JSONSchema.from_str(schema)
    data = {
        "event_id": str(uuid4()),
        "event_version": event_version,
        "event_timestamp": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "producer": "tasks",
        "event_name": name,
        "payload": payload,
    }
    validator.validate(data)
    log(f"⬆️'tasks_lifecicle': {data}")
    await send_event("tasks_lifecicle", data)


@router.post("/tasks/", status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreatePayload,
    db: Session = Depends(get_db),
    current_user: UserTasks = Depends(get_current_user),
) -> TaskSchema:
    assigned_to: UserTasks = db.query(UserTasks).filter(UserTasks.role == "user").order_by(func.random()).first()
    if assigned_to is None:
        raise HTTPException(status_code=404, detail="No user available")

    task = Task(
        id=str(uuid4()),
        description=payload.description,
        status=Status.todo.value,
        assigned_to=str(assigned_to.id),
        fee=random.randint(10, 20),
        reward=random.randint(20, 40),
    )
    db.add(task)
    task_schema = TaskSchema.model_validate(task)
    await send_task_streaming_event(
        "task.created",
        task_schema.dict(),
        schema=task_created_schema_v1,
        event_version=1,
    )
    await send_task_biz_event(
        "task.added",
        task_schema.dict(),
        schema=task_added_schema_v1,
        event_version=1,
    )
    await send_task_biz_event(
        "task.assigned",
        {
            "task_id": str(task.id),
            "assigned_to": str(assigned_to.id),
        },
        schema=task_assigned_schema_v1,
        event_version=1,
    )
    db.commit()
    return task


@router.get("/tasks/{task_id}", response_model=TaskSchema)
async def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    _: UserTasks = Depends(get_current_user),
) -> TaskSchema:
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/tasks/", response_model=list[TaskSchema])
async def get_tasks(
    assigned_to_me: bool = False,
    db: Session = Depends(get_db),
    current_user: UserTasks = Depends(get_current_user),
) -> list[TaskSchema]:
    query = db.query(Task)
    if assigned_to_me:
        query = query.filter(Task.assigned_to == str(current_user.id))
    return query.all()


@router.post("/tasks/{task_id}/done")
async def mark_task_as_done(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserTasks = Depends(get_current_user),
) -> TaskSchema:
    task = db.query(Task).filter(Task.id == str(task_id)).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.assigned_to != str(current_user.id):
        raise HTTPException(status_code=403, detail="You are not allowed to mark this task as done")
    task.status = Status.done.value
    task_schema = TaskSchema.model_validate(task)
    await send_task_streaming_event(
        "task.updated",
        task_schema.dict(),
        schema=task_updated_schema_v1,
        event_version=1,
    )
    await send_task_biz_event(
        "task.done",
        {"task_id": str(task.id), "completed_by": str(task.assigned_to)},
        schema=task_done_schema_v1,
        event_version=1,
    )
    db.commit()
    return task


@router.post("/tasks/reassign")
async def reassign_task(
    db: Session = Depends(get_db),
    current_user: UserTasks = Depends(get_current_user),
) -> list[TaskSchema]:
    """
    Reassign all tasks for all users to random users
    Allowed only for admins
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You are not allowed to reassign tasks")
    users = db.query(UserTasks).filter(UserTasks.role == "user").all()
    tasks = db.query(Task).filter(Task.status == Status.todo.value).all()
    for task in tasks:
        assigned_to = random.choice(users)
        task.assigned_to = str(assigned_to.id)
        await send_task_biz_event(
            "task.assigned",
            {"task_id": str(task.id), "assigned_to": str(task.assigned_to)},
            schema=task_assigned_schema_v1,
            event_version=1,
        )
        await send_task_streaming_event(
            "task.updated",
            TaskSchema.model_validate(task).dict(),
            schema=task_updated_schema_v1,
            event_version=1,
        )
    db.commit()
    return tasks
