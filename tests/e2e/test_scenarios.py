from time import sleep
from faker import Faker

import pytest
from httpx import Client


@pytest.fixture()
def prepare_users(real_client: Client, faker: Faker) -> tuple:
    # create user
    users = []
    for _i in range(5):
        username = faker.profile()["username"]
        email = faker.profile()["mail"]
        response = real_client.post(
            "/users/",
            json={"username": username, "email": email, "role": "user"},
        )
        assert response.status_code == 201
        users.append(response.json())
    username = faker.profile()["username"]
    email = faker.profile()["mail"]
    response = real_client.post(
        "/users/",
        json={"username": username, "email": email, "role": "admin"},
    )
    assert response.status_code == 201

    admin = response.json()
    return users, admin


@pytest.mark.parametrize("role", ["user", "admin"])
def test__create_user(real_client: Client, role: str, insert_assert):
    response = real_client.post(
        "/users/",
        json={"username": "johndoe", "email": "test@test.com", "role": role},
    )
    assert response.status_code == 201


def test__tasks_create_and_reassign(real_client: Client, insert_assert, faker, prepare_users):
    # make sure that users synced
    users, admin = prepare_users
    token_resp = real_client.post(
        "/token",
        data={"username": admin["username"], "password": "any"},
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    real_client.headers.update({"Authorization": f"Bearer {token}"})
    # get task with timeout to make sure that users synced
    for _i in range(10):
        tasks_resp = real_client.get("/tasks/")
        if tasks_resp.status_code == 200:
            break
        sleep(0.5)

    # create tasks
    for i in range(3):
        response = real_client.post(
            "/tasks/",
            json={"description": f"task {i}"},
        )
        assert response.status_code == 201
        task_data = response.json()
        assert task_data["assigned_to"] in [u["id"] for u in users]
    all_tasks = real_client.get("/tasks/").json()
    assert len(all_tasks) == 3

    # reassign all tasks
    reassigned_tasks_resp = real_client.post("/tasks/reassign")
    assert reassigned_tasks_resp.status_code == 200
    reassigned_tasks = reassigned_tasks_resp.json()
    assert len(reassigned_tasks) == 3
    assert [i["assigned_to"] for i in all_tasks] != [i["assigned_to"] for i in reassigned_tasks]


def test__tasks_mark_as_done(real_client: Client, insert_assert, faker, prepare_users):
    # make sure that users synced
    users, admin = prepare_users
    token_resp = real_client.post(
        "/token",
        data={"username": admin["username"], "password": "any"},
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    real_client.headers.update({"Authorization": f"Bearer {token}"})
    # get task with timeout to make sure that users synced
    for _i in range(10):
        tasks_resp = real_client.get("/tasks/")
        if tasks_resp.status_code == 200:
            break
        sleep(0.5)
    for i in range(3):
        response = real_client.post(
            "/tasks/",
            json={"description": f"task {i}"},
        )
        assert response.status_code == 201
        task_data = response.json()
        assert task_data["assigned_to"] in [u["id"] for u in users]
    user_from_task = next(u for u in users if u["id"] == task_data["assigned_to"])
    token_resp = real_client.post(
        "/token",
        data={"username": user_from_task["username"], "password": "any"},
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    real_client.headers.update({"Authorization": f"Bearer {token}"})
    response = real_client.post(f"/tasks/{task_data['id']}/done")
    assert response.status_code == 200
