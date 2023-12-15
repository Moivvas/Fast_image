from pytest import fixture
from unittest.mock import patch

from src.database.models import User, Image, Rating
from fastapi import status
from src.services.auth import auth_service
import datetime


@fixture(scope='module')
def token(client, user, session):
    response = client.post("/project/auth/signup", json=user)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()

    response = client.post("/project/auth/login",
                           data={"username": user.get("email"), "password": user.get("password")})
    data = response.json()
    return data["access_token"]


@fixture(scope='module')
def image(client, user, session):
    response = client.post("/project/auth/signup", json=user)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    image = session.query(Image).filter(Image.id == 1).first()
    if image is None:
        image = Image(
            id=1,
            url="https://res.cloudinary.com/dv5a15oym/image/upload/"
                "c_fill,h_250,w_250/v1702535818/fast_image/e2b850d5b1ca",
            user_id=1,
            created_at=datetime.datetime.now(),
        )
        session.add(image)
        session.commit()
        session.refresh(image)
    return image


@fixture(scope='module')
def rating(client, user, session):
    response = client.post("/project/auth/signup", json=user)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    rating = session.query(Image).filter(Rating.id == 1).first()
    if rating is None:
        rating = Rating(
            id=1,
            rate=5,
            user_id=current_user.id,
            image_id=1,
        )
        session.add(rating)
        session.commit()
        session.refresh(rating)
    return rating


def test_show_images_by_rating(client, token, image, session):
    with patch.object(auth_service, "redis_db") as redis_mock:
        redis_mock.get.return_value = None
        response = client.get("/project/rating/image_by_rating",
                              headers={'Authorization': f'Bearer {token}'}
                              )
        assert response.status_code == status.HTTP_200_OK


# def test_create_rate(client, token, image, session):
#     with patch.object(auth_service, "redis_db") as redis_mock:
#         redis_mock.get.return_value = None
#         response = client.post("/project/rating/1/5",
#                                headers={'Authorization': f'Bearer {token}'}
#                                )
#         assert response.status_code == status.HTTP_200_OK


def test_delete_rate(client, token, session, rating):
    with patch.object(auth_service, "redis_db") as redis_mock:
        redis_mock.get.return_value = None
        response = client.delete("/project/rating/delete/1",
                                 headers={'Authorization': f'Bearer {token}'}
                                 )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# def test_show_image_rating(client, token, image, session):
#     with patch.object(auth_service, "redis_db") as redis_mock:
#         redis_mock.get.return_value = None
#         response = client.get("/project/rating/image_rating/1",
#                               headers={'Authorization': f'Bearer {token}'}
#                               )
#         assert response.status_code == status.HTTP_200_OK
