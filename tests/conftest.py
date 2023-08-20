from collections.abc import Callable, Generator
from uuid import uuid4

import httpx
import pytest
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy import MetaData
from sqlalchemy.orm import Session

from src.auth.models import User
from src.database import engine, get_db
from src.main import app
from src.tasks.models import Task, UserTasks


@pytest.fixture()
def real_client() -> Generator[httpx.Client, None, None]:
    with httpx.Client(base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app=app) as client:
        yield client


@pytest.fixture()
def user_client(user: User) -> Generator[TestClient, None, None]:
    with TestClient(app=app) as client:
        auth_data = client.post("/token/", data={"username": str(user.username), "password": "any"})
        client.headers.update({"Authorization": f"Bearer {auth_data.json()['access_token']}"})
        yield client


@pytest.fixture()
def admin_client(admin: User) -> Generator[TestClient, None, None]:
    with TestClient(app=app) as client:
        auth_data = client.post("/token/", data={"username": str(admin.username), "password": "any"})
        client.headers.update({"Authorization": f"Bearer {auth_data.json()['access_token']}"})
        yield client


@pytest.fixture()
def db() -> Session:
    return next(get_db())


@pytest.fixture(autouse=True)
def _clear_db(db: Session) -> None:
    meta = MetaData()
    meta.reflect(bind=engine)
    db.query(Task).delete()
    db.query(User).delete()
    db.query(UserTasks).delete()
    db.commit()


@pytest.fixture()
def create_user(db: Session, faker: Faker) -> Callable[[str], User]:
    def _create_user(role: str) -> User:
        username = faker.profile()["username"]
        email = faker.profile()["mail"]
        user = User(username=username, email=email, role=role, id=str(uuid4()))
        db.add(user)
        db.commit()
        return user

    return _create_user


@pytest.fixture()
def admin(create_user) -> User:
    return create_user("admin")


@pytest.fixture()
def user(create_user) -> User:
    return create_user("user")
