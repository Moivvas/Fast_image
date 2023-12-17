from datetime import datetime
import unittest
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.database.models import User, Rating
from src.schemas import RatingModel
from src.repository.ratings import (create_rate,
                                    delete_rate,
                                    calculate_rating,
                                    show_my_ratings,
                                    edit_rate,
                                    user_rate_image,
                                    user_with_images)


class TestCreateRate(unittest.TestCase):

    async def test_create_new_rating(self, repository_ratings=None):
        # Mock dependencies
        image_id = 1
        rate = 4
        db_mock = MagicMock()
        current_user_mock = MagicMock()
        repository_ratings.create_rate = AsyncMock(return_value=RatingModel(id=1, created_at=datetime.now(),
                                                                            image_id=image_id,
                                                                            user_id=current_user_mock.id))

        result = await create_rate(image_id, rate, db_mock, current_user_mock)

        repository_ratings.create_rate.assert_called_once_with(image_id, rate, db_mock, current_user_mock)
        assert result == RatingModel(id=1, created_at=datetime.now(), image_id=image_id, user_id=current_user_mock.id)

    @pytest.mark.asyncio
    async def test_return_http_exception_invalid_rate_value(self):
        image_id = 1
        rate = 0
        db_mock = MagicMock()
        current_user_mock = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await create_rate(image_id, rate, db_mock, current_user_mock)

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST

        rate = 6

        with pytest.raises(HTTPException) as exc:
            await create_rate(image_id, rate, db_mock, current_user_mock)

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST


class TestDeleteRate(unittest.TestCase):

    async def test_valid_rate_exists(self):
        rate_id = 1
        db = Session()
        user = User()

        result = await delete_rate(rate_id, db, user)

        self.assertIsNone(result)
        self.assertEqual(db.query(Rating).filter(Rating.id == rate_id).first(), None)

    async def test_none_rate_id(self):
        rate_id = None
        db = Session()
        user = User()

        result = await delete_rate(rate_id, db, user)

        self.assertIsNone(result)


class TestCalculateRating(unittest.TestCase):

    async def test_returns_dictionary_with_keys(self):
        db_mock = MagicMock()
        db_mock.query.return_value.filter.return_value.scalar.return_value = 4.5
        db_mock.query.return_value.filter.return_value.scalar.side_effect = ['image_url']

        user_mock = MagicMock()

        result = await calculate_rating(1, db_mock, user_mock)

        self.assertEqual(result, {'average_rating': 4.5, 'image_url': 'image_url'})

    async def test_raises_exception_if_image_id_not_found(self):
        db_mock = MagicMock()
        db_mock.query.return_value.filter.return_value.scalar.return_value = None

        user_mock = MagicMock()

        with self.assertRaises(Exception):
            await calculate_rating(1, db_mock, user_mock)


class TestShowMyRatings(unittest.TestCase):

    async def test_returns_all_ratings(self):
        db = Session()
        user = User(id=1)
        expected_ratings = [Rating(id=1, rate=5), Rating(id=2, rate=4)]

        result = await show_my_ratings(db, user)

        self.assertEqual(result, expected_ratings)

    async def test_returns_empty_list_if_user_is_none(self):
        db = Session()
        user = None

        result = await show_my_ratings(db, user)

        # Assert
        self.assertEqual(result, [])


class TestEditRate(unittest.TestCase):

    async def test_update_valid_rate(self):
        rate_id = 1
        new_rate = 5
        db = Session()
        user = User()

        result = await edit_rate(rate_id, new_rate, db, user)

        self.assertEqual(result.rate, new_rate)

    async def test_invalid_rate_id(self):
        rate_id = -1
        new_rate = 5
        db = Session()
        user = User()

        result = await edit_rate(rate_id, new_rate, db, user)

        self.assertIsNone(result)


class TestUserRateImage(unittest.TestCase):

    async def test_return_none_if_no_rating(self):
        user_id = 1
        image_id = 1
        db = Session()
        user = User()

        result = await user_rate_image(user_id, image_id, db, user)

        self.assertIsNone(result)

    async def test_handle_none_user_id_or_image_id(self):
        user_id = None
        image_id = 1
        db = Session()
        user = User()

        result = await user_rate_image(user_id, image_id, db, user)

        self.assertIsNone(result)


class TestUserWithImages(unittest.TestCase):

    async def test_return_images_associated_with_user(self):
        db = Session()
        user = User()

        result = await user_with_images(db, user)

        self.assertIsInstance(result, list)

    async def test_raise_exception_when_db_session_is_none(self):
        db = None
        user = User()

        with self.assertRaises(Exception):
            await user_with_images(db, user)
