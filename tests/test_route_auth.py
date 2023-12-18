import pytest

from src.database.models import User
from src.conf import messages


@pytest.fixture()
def refresh_token(client, user, session):

    response = client.post(
        "/project/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    data = response.json()
    return data["refresh_token"]


@pytest.fixture()
def access_token(client, user, session):

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


def test_create_user(client, user):

    response = client.post("/project/auth/signup", json=user)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["email"] == user.get("email")


def test_repeat_create_user(client, user):
    response = client.post("/project/auth/signup", json=user)
    assert response.status_code == 409, response.text
    payload = response.json()
    assert payload["detail"] == messages.ACCOUNT_ALREADY_EXISTS


def test_login_user(client, user, session):
    print(user)
    response = client.post("/project/auth/login", data={"username": user.get("email"), "password": user.get("password")})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["token_type"] == "bearer"


def test_login_user_with_wrong_password(client, user, session):
    current_user: User = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()
    response = client.post("/project/auth/login", data={"username": user.get("email"), "password": "password"})
    assert response.status_code == 401, response.text
    payload = response.json()
    assert payload["detail"] == "Invalid password"


def test_login_user_with_wrong_email(client, user, session):
    current_user: User = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()
    response = client.post("/project/auth/login", data={"username": "example@test.com", "password": user.get("password")})
    assert response.status_code == 401, response.text
    payload = response.json()
    assert payload["detail"] == "Invalid email"


def test_refresh_token(client, user, refresh_token):
    response = client.get(
        "/project/auth/refresh_token",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data





