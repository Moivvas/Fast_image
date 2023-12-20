import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from unittest.mock import MagicMock, patch
from src.repository.users import auth_service


@pytest.fixture()
def token(client, user, session):
    client.post("/project/auth/signup", json=user)
    session.commit()
    response = client.post("/project/auth/login", data={"username": user.get("email"), "password": user.get("password")})
    data = response.json()
    return data["access_token"]


def test_upload_image(client, token):
    with patch.object(auth_service, "redis_db") as redis_mock:
        redis_mock.get.return_value = None

        cloudinary_mock = MagicMock(return_value={'secure_url': 'https://example.com/image.jpg'})
        with patch('cloudinary.uploader.upload', cloudinary_mock):
            image_path = "image_test.png"
            with open(image_path, "rb") as image_file:
                files = {"file": (image_path, image_file)}

                response = client.post(
                    "/project/images/",
                    data={"description": "creepy"},
                    files=files,
                    headers={"Authorization": f"Bearer {token}"}
                )

            assert response.status_code == 201, response.text
            data = response.json()
            print(data)
            print("Response keys:", data.keys())

            assert "id" in data


def test_delete_image(client, token):
    with patch.object(auth_service, "redis_db") as redis_mock:
        redis_mock.get.return_value = None

        cloudinary_mock = MagicMock(return_value={'secure_url': 'https://example.com/image.jpg'})
        with patch('cloudinary.uploader.destroy', cloudinary_mock):

                response = client.delete(
                    "/project/images/1",
                    headers={"Authorization": f"Bearer {token}"}
                )

        assert response.status_code == 200, response.text
        data = response.json()

        print("Response keys:", data.keys())

        assert "detail" in data

# def test_update_description(client, token, session):
#     with patch.object(auth_service, "redis_db") as redis_mock:
#         redis_mock.get.return_value = None
        
#         image = session.query(Image).filter(Image.id == 1).first()
#         response_update = client.patch(
#             f"/project/images/1",
#             json={"description": "new description"},
#             headers={"Authorization": f"Bearer {token}"}
#         )

#         updated_data = response_update.json()
#         print(updated_data)
#         assert updated_data.get("description") == "new description"

#         image_response = ImageUpdateResponse(**updated_data)
#         assert image_response.description == "new_description"
#         assert image_response.id == 1