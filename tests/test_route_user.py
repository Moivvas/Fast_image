from unittest.mock import patch

import pytest
from fastapi import Depends

from src.database.models import User, Role
from src.conf import messages
from src.schemas import AllUsersProfiles, UserProfileMe
from src.services.auth import auth_service


@pytest.fixture()
def token(client, user, session):
    client.post("/project/auth/signup", json=user)

    current_user: User = (
        session.query(User).filter(User.email == user.get("email")).first()
    )

    response = client.post(
        "/project/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    data = response.json()
    return data["access_token"]


def test_user_me(user, session, client, token):
    with patch.object(auth_service, "redis_db") as redis_mock:
        redis_mock.get.return_value = None
        current_user: User = (
            session.query(User).filter(User.email == user.get("email")).first()
        )
        session.commit()
        response = client.get(
            "/project/users/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert type(payload["user"]) == dict


def test_get_user(user, session, client, token):
    with patch.object(auth_service, "redis_db") as redis_mock:
        redis_mock.get.return_value = None
        response = client.get(
            "/project/users/user/deadpool@example.com",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert type(payload) == dict
        assert payload["name"] == "deadpool"


def test_user_change_role(user, session, client, token):
    with patch.object(auth_service, "redis_db") as redis_mock:
        redis_mock.get.return_value = None
        client.post("/project/auth/signup", json={"name": "Dima", "email": "exam@exam.com", "password": "qwerty", "sex": "male"})

        response = client.patch(
            "/project/users/user",
            json={"email": "exam@exam.com", "role": "moderator"},
            headers={"Authorization": f"Bearer {token}"},

        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["name"] == "Dima"
        assert payload["email"] == "exam@exam.com"
        assert payload["role"] == "moderator"


def test_get_users_profiles(session, user, client, token):
    with patch.object(auth_service, "redis_db") as redis_mock:
        redis_mock.get.return_value = None
        response = client.get(
            "/project/users", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert type(payload["users"]) == list
        assert type(payload["users"][0]) == dict
        assert payload["users"][0]["user"]["name"] == "deadpool"


def test_get_user_profile(session, user, client, token):
    with patch.object(auth_service, "redis_db") as redis_mock:
        redis_mock.get.return_value = None

        response = client.get(
            "/project/users/deadpool", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert type(payload["user"]) == dict
        assert payload["user"]["email"] == "deadpool@example.com"
        assert payload["user"]["name"] == "deadpool"
        assert type(payload["images"]) == list

        
def test_update_user_info(user, session, client, token):
    with patch.object(auth_service, "redis_db") as redis_mock:
        redis_mock.get.return_value = None

        client.post("/project/auth/signup", json={"name": "John", "email": "john@example.com", "password": "password", "sex": "male"})
        response_login = client.post("/project/auth/login", data={"username": "john@example.com", "password": "password"})
        token_john = response_login.json()["access_token"]

        new_name = "Johnny"
        response_update = client.patch(
            "/project/users/me/info?new_name=Johnny",
            json={"new_name": new_name},
            headers={"Authorization": f"Bearer {token_john}"},
        )

        assert response_update.status_code == 200, response_update.text
        payload = response_update.json()
        assert payload["name"] == new_name


def test_update_user_credential(user, session, client, token):
    with patch.object(auth_service, "redis_db") as redis_mock:
        redis_mock.get.return_value = None

        new_email = "new_email@example.com"
        new_password = "new_password"

        response_update = client.patch(
            "/project/users/me/credential?new_email=new_email%40example.com&new_password=new_password",
            json={"new_email": new_email, "new_password": new_password},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response_update.status_code == 200, response_update.text
        payload = response_update.json()
        assert payload["email"] == new_email
