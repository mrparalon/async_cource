from collections.abc import Callable
from unittest.mock import ANY, AsyncMock
from uuid import UUID

import pytest
from dirty_equals import IsStr
from httpx import Client
from jose import jwt
from pytest_mock import MockFixture

from src.auth.models import User
from src.auth.router import SECRET_KEY, Role


@pytest.fixture()
def mock_send_event(mocker: MockFixture):
    return mocker.patch("src.auth.router.send_event")


@pytest.mark.parametrize(
    ("role", "username", "email"), [("user", "johndoe", "user@test.com"), ("admin", "admin", "admin@test.com")]
)
def test__create_user(client: Client, role: str, username: str, email: str, insert_assert, mock_send_event: AsyncMock):
    response = client.post(
        "/users/",
        json={"username": username, "email": email, "role": role},
    )
    assert response.status_code == 201
    # insert_assert(response.json())
    assert response.json() == {
        "id": ANY,
        "username": username,
        "email": email,
        "role": role,
    }
    mock_send_event.assert_called_once()
    mock_send_event.assert_called_with(
        "auth",
        {
            "name": "user.created",
            "payload": {
                "id": UUID(response.json()["id"]),
                "username": username,
                "email": email,
                "role": Role(role),
            },
        },
    )


def test__get_token_with_any_password(client: Client, insert_assert):
    username = "johndoe"
    response = client.post(
        "/users/",
        json={"username": "johndoe", "email": "test@test.com", "role": "user"},
    )
    assert response.status_code == 201
    user_id = response.json()["id"]
    response = client.post("/token/", data={"username": username, "password": "any"})
    assert response.status_code == 200
    # insert_assert(response.json())
    assert response.json() == {
        "access_token": IsStr(),
        "token_type": "bearer",
    }
    token_data = jwt.decode(response.json()["access_token"], SECRET_KEY, algorithms=["HS256"])
    assert token_data == {"sub": user_id, "exp": ANY}


@pytest.mark.parametrize(
    ("previous_role", "new_role"),
    [
        (Role.user, Role.admin),
        (Role.admin, Role.user),
    ],
)
def test__change_user_role(
    admin_client: Client,
    create_user: Callable[[str], User],
    previous_role: Role,
    new_role: Role,
    insert_assert,
    mock_send_event: AsyncMock,
):
    user = create_user(previous_role.value)
    response = admin_client.patch(
        f"/users/{user.id}",
        json={"role": new_role.value},
    )
    assert response.status_code == 200
    # insert_assert(response.json())
    assert response.json() == {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": new_role.value,
    }
    mock_send_event.assert_called_once()
    mock_send_event.assert_called_with(
        "auth",
        {
            "name": "role.chaged",
            "payload": {
                "user_id": user.id,
                "previous_role": previous_role.value,
                "new_role": new_role.value,
            },
        },
    )
