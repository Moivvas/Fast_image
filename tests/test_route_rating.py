from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from src.database.db import get_db
from src.database.models import Base
from src.services.auth import auth_service
from src.database.models import User, Role
from src.conf import messages
import pytest

# Assuming you have a testing environment set up
SQLALCHEMY_DATABASE_URL = "sqlite:///./tests/test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db):
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[auth_service.get_current_user] = lambda: User(id=1, role=Role.admin)
    client = TestClient(app)
    return client


def test_create_rate(client):
    response = client.post("/project/rating/1/4")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() is not None


def test_create_rate_invalid_image(client):
    response = client.post("/project/rating/999/4")
    assert response.status_code == 404
    assert response.json()["detail"] == messages.IMAGE_NOT_FOUND


def test_rating(client):
    response = client.get("/project/rating/image_rating/1")
    assert response.status_code == 200
    assert response.json() is not None


def test_rating_invalid_image(client):
    response = client.get("/project/rating/image_rating/999")
    assert response.status_code == 404
    assert response.json()["detail"] == messages.IMAGE_NOT_FOUND


def test_image_by_rating(client):
    response = client.get("/project/rating/image_by_rating")
    assert response.status_code == 200
    assert response.json() is not None


def test_image_by_rating_no_images(client):
    response = client.get("/project/rating/image_by_rating")
    assert response.status_code == 404
    assert response.json()["detail"] == messages.IMAGE_NOT_FOUND


def test_delete_rate(client):
    response = client.delete("/project/rating/delete/1")
    assert response.status_code == 204


def test_delete_rate_invalid_rate(client):
    response = client.delete("/project/rating/delete/999")
    assert response.status_code == 404
    assert response.json()["detail"] == messages.RATE_NOT_FOUND
