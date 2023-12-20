import unittest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from src.conf import messages
from src.database.models import User, Role
from src.schemas import RatingModel, AverageRatingResponse, ImageModel
from src.repository import ratings as repository_rating
from src.routes.ratings import (create_rate,
                                get_image_avg_rating,
                                all_my_rates,
                                user_rate_image,
                                delete_rate,
                                search_users_with_images)


class TestCreateRate(unittest.TestCase):

    async def test_create_new_rating_success(self, repository_ratings=repository_rating):
        image_id = 1
        rate = 4
        db_mock = MagicMock()
        current_user_mock = MagicMock()
        repository_ratings.create_rate = AsyncMock(return_value=RatingModel(id=1,
                                                                            created_at=datetime.now(),
                                                                            image_id=image_id,
                                                                            user_id=current_user_mock.id))

        result = await create_rate(image_id, rate, db_mock, current_user_mock)

        repository_ratings.create_rate.assert_called_once_with(image_id, rate, db_mock, current_user_mock)
        assert result == RatingModel(id=1, created_at=datetime.now(), image_id=image_id, user_id=current_user_mock.id)

    async def test_create_new_rating_negative_image_id(self):
        image_id = -1
        rate = 4
        db_mock = MagicMock()
        current_user_mock = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await create_rate(image_id, rate, db_mock, current_user_mock)

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST


class TestImageByRating(unittest.TestCase):

    async def test_returns_average_rating_and_image_url(self, repository_ratings=repository_rating):
        image_id = 1
        db = MagicMock()
        current_user = User(id=1,
                            name="John",
                            email="john@example.com",
                            sex="Male",
                            password="password",
                            created_at=datetime.now(),
                            refresh_token="token",
                            forbidden=False,
                            role=Role.user,
                            images=[],
                            avatar="avatar.jpg")
        expected_response = AverageRatingResponse(average_rating=4.5, image_url="example.com/image.jpg")
        repository_ratings.calculate_rating = MagicMock(return_value=expected_response)

        response = await get_image_avg_rating(image_id, db, current_user)

        self.assertEqual(response, expected_response)

    async def test_uses_current_user_to_calculate_rating(self, repository_ratings=repository_rating):
        image_id = 1
        db = MagicMock()
        current_user = User(id=1,
                            name="John",
                            email="john@example.com",
                            sex="Male",
                            password="password",
                            created_at=datetime.now(),
                            refresh_token="token",
                            forbidden=False,
                            role=Role.user,
                            images=[],
                            avatar="avatar.jpg")
        expected_response = AverageRatingResponse(average_rating=4.5, image_url="example.com/image.jpg")
        repository_ratings.calculate_rating = MagicMock(return_value=expected_response)

        response = await get_image_avg_rating(image_id, db, current_user)

        self.assertEqual(response, expected_response)


class TestAllMyRates(unittest.TestCase):

    async def test_returns_all_ratings(self, repository_ratings=repository_rating):
        db_mock = MagicMock()
        current_user_mock = MagicMock()

        expected_rates = [RatingModel(id=1, image_id=1, user_id=1),
                          RatingModel(id=2, image_id=2, user_id=1)]
        repository_ratings.show_my_ratings.return_value = expected_rates

        result = await all_my_rates(db=db_mock, current_user=current_user_mock)

        assert result == expected_rates

    async def test_empty_ratings_list(self, repository_ratings=repository_rating):
        db_mock = MagicMock()
        current_user_mock = MagicMock()

        expected_rates = []
        repository_ratings.show_my_ratings.return_value = expected_rates

        result = await all_my_rates(db=db_mock, current_user=current_user_mock)

        assert result == expected_rates


class TestUserRateImage(unittest.TestCase):

    async def test_valid_user_id_and_image_id(self, repository_ratings=repository_rating):
        mock_db = MagicMock()
        mock_current_user = MagicMock()

        user_id = 1
        image_id = 1

        expected_output = RatingModel(id=1, image_id=1, user_id=1)

        repository_ratings.user_rate_image = MagicMock(return_value=expected_output)

        result = await user_rate_image(user_id, image_id, db=mock_db, current_user=mock_current_user)

        self.assertEqual(result, expected_output)

    async def test_sqlalchemy_error(self, repository_ratings=repository_rating):
        mock_db = MagicMock()
        mock_current_user = MagicMock()

        user_id = 1
        image_id = 1

        repository_ratings.user_rate_image = MagicMock(side_effect=SQLAlchemyError())

        with self.assertRaises(HTTPException) as context:
            await user_rate_image(user_id, image_id, db=mock_db, current_user=mock_current_user)

        self.assertEqual(context.exception.status_code, status.HTTP_400_BAD_REQUEST)


class TestDeleteRate(unittest.TestCase):

    async def test_valid_inputs(self, repository_ratings=repository_rating):
        rate_id = 1
        db_mock = MagicMock()
        current_user_mock = MagicMock()

        repository_ratings.delete_rate = AsyncMock(return_value=RatingModel(id=1, image_id=1, user_id=1))

        result = await delete_rate(rate_id, db_mock, current_user_mock)

        repository_ratings.delete_rate.assert_called_once_with(rate_id, db_mock, current_user_mock)
        assert result == RatingModel(id=1, image_id=1, user_id=1)

    async def test_invalid_rate_id(self, repository_ratings=repository_rating):
        rate_id = 1
        db_mock = MagicMock()
        current_user_mock = MagicMock()

        repository_ratings.delete_rate = AsyncMock(return_value=None)

        with self.assertRaises(HTTPException) as exc:
            await delete_rate(rate_id, db_mock, current_user_mock)

        repository_ratings.delete_rate.assert_called_once_with(rate_id, db_mock, current_user_mock)
        assert exc.exception.status_code == status.HTTP_404_NOT_FOUND
        assert exc.exception.detail == messages.RATE_NOT_FOUND


class TestSearchUsersWithImages(unittest.TestCase):

    async def test_valid_session_and_current_user(self, repository_ratings=repository_rating):
        db_mock = MagicMock()
        current_user_mock = MagicMock()

        repository_ratings.user_with_images = AsyncMock(return_value=[ImageModel(id=1,
                                                                                 url='image1.jpg',
                                                                                 public_id='public1',
                                                                                 user_id=1),
                                                                      ImageModel(id=2,
                                                                                 url='image2.jpg',
                                                                                 public_id='public2',
                                                                                 user_id=2)])

        result = await search_users_with_images(db=db_mock, current_user=current_user_mock)

        self.assertEqual(result, [ImageModel(id=1,
                                             url='image1.jpg',
                                             public_id='public1',
                                             user_id=1),
                                  ImageModel(id=2,
                                             url='image2.jpg',
                                             public_id='public2',
                                             user_id=2)])

    async def test_all_users_have_no_images(self, repository_ratings=repository_rating):
        db_mock = MagicMock()
        current_user_mock = MagicMock()

        repository_ratings.user_with_images = AsyncMock(return_value=[])

        result = await search_users_with_images(db=db_mock, current_user=current_user_mock)

        self.assertEqual(result, [])
