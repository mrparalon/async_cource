import pytest
from httpx import Client


@pytest.mark.parametrize("role", ["user", "admin"])
def test__create_user(real_client: Client, role: str, insert_assert):
    response = real_client.post(
        "/users/",
        json={"username": "johndoe", "email": "test@test.com", "role": role},
    )
    assert response.status_code == 201
