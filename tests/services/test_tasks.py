from uuid import uuid4
from fastapi.testclient import TestClient

import pytest
from faker import Faker
from sqlalchemy.orm import Session

from src.auth.models import User
from src.tasks.models import UserTasks


@pytest.fixture(autouse=True)
def create_user_for_client(db: Session, user: User):
    user_for_tasks = UserTasks(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
    )
    db.add(user_for_tasks)
    db.commit()
    return user_for_tasks


@pytest.fixture()
def user_for_task(db: Session, faker: Faker):
    user = UserTasks(
        id=str(uuid4()),
        username=faker.profile()["username"],
        email=faker.profile()["mail"],
        role="user",
    )
    db.add(user)
    db.commit()
    return user


def test__create_task(user_client: TestClient, insert_assert, user_for_task: UserTasks):
    response = user_client.post(
        "/tasks/",
        json={"description": "task 1"},
    )
    assert response.status_code == 201
    task_data = response.json()
