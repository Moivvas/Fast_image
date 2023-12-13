import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest

from unittest.mock import MagicMock, patch

from src.database.models import User
from src.services.auth import auth_service

# import asyncio
# loop = asyncio.new_event_loop()
# asyncio.set_event_loop(loop)
# print(asyncio.get_event_loop().is_closed())


@pytest.fixture()
def token(client, user, session):
    client.post("/project/auth/signup", json=user)
    session.commit()
    response = client.post("/project/auth/login", data={"username": user.get("email"), "password": user.get("password")})
    data = response.json()
    return data["access_token"]


def test_create_tag(client, token):
    response = client.post(
        "/project/tags/",
        json={"tag_name": "test_tag"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["tag_name"] == "test_tag"
    assert "id" in data


def test_get_tag_by_id(client, token):
    response = client.get(
        "/project/tags/1",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["tag_name"] == "test_tag"
    assert "id" in data


def test_get_tag_by_id_not_found(client, token):
    response = client.get(
        "/project/tags/2",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Invalid tag"


def test_get_tag_by_name(client, token):
    response = client.get(
        "/project/tags/test_tag",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["tag_name"] == "test_tag"
    assert "id" in data


def test_get_tag_by_name_not_found(client, token):
    response = client.get(
        "/project/tags/2",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Invalid tag"


def test_get_tags(client, token):
    response = client.get(
        "/project/tags",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["tag_name"] == "test_tag"
    assert "id" in data[0]


# def test_update_tag(client, token):
#     response = client.patch(
#         "/project/tags/1",
#         json={"tag_name": "new_test_tag", "tag_id": 1},
#         headers={"Authorization": f"Bearer {token}"}
#     )
#     assert response.status_code == 200, response.text
#     data = response.json()
#     assert data["tag_name"] == "new_test_tag"
#     assert "id" in data


# def test_update_tag_not_found(client, token):
#     response = client.patch(
#         "/project/tags/2",
#         json={"tag_id": 2, "tag_name": "new_test_tag"},
#         headers={"Authorization": f"Bearer {token}"}
#     )
#     assert response.status_code == 404, response.text
#     data = response.json()
#     assert data["detail"] == "Invalid tag"


def test_delete_tag_by_id(client, token):
    response = client.delete(
        "/project/tags/?identifier=1&by_id=true",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["tag_name"] == "test_tag"
    assert "id" in data


def test_repeat_delete_tag_by_id(client, token):
    response = client.delete(
        "/project/tags/?identifier=1&by_id=true",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Invalid tag"


def test_delete_tag_by_name(client, token):
    response = client.delete(
        "/project/tags/?identifier=test_tag&by_id=false",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Invalid tag"


def test_repeat_delete_tag_by_name(client, token):
    response = client.delete(
        "/project/tags/?identifier=test_tag&by_id=false",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Invalid tag"
