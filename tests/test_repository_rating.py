import unittest
from unittest.mock import Mock
from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.repository.ratings import create_rating, del_rate, calculate_rating, images_by_rating


class TestRating(unittest.TestCase):

    async def test_create_rating(self):
        db = Mock(spec=Session)
        user = Mock()
        user.id = 1

        db.query.return_value.filter.return_value.first.return_value.user_id.return_value = 2
        response = await create_rating(img_id=1, rate=4, db=db, user=user)
        self.assertIsNotNone(response)

        db.query.return_value.filter.return_value.first.return_value.user_id.return_value = 1
        with self.assertRaises(HTTPException) as context:
            await create_rating(img_id=1, rate=4, db=db, user=user)
        self.assertEqual(context.exception.status_code, 423)

        db.query.return_value.filter.return_value.first.return_value.user_id.return_value = None
        db.query.return_value.filter.return_value.first.return_value = Mock()
        with self.assertRaises(HTTPException) as context:
            await create_rating(img_id=1, rate=4, db=db, user=user)
        self.assertEqual(context.exception.status_code, 423)

    async def test_del_rate(self):
        db = Mock(spec=Session)
        user = Mock()
        user.id = 1

        db.query.return_value.filter.return_value.first.return_value = Mock()
        response = await del_rate(rate_id=1, db=db, user=user)
        self.assertIsNone(response)

        db.query.return_value.filter.return_value.first.return_value = None
        response = await del_rate(rate_id=999, db=db, user=user)
        self.assertIsNone(response)

    async def test_calculate_rating(self):
        db = Mock(spec=Session)
        user = Mock()
        user.id = 1

        db.query.return_value.filter.return_value.scalar.return_value = 4.5
        response = await calculate_rating(image_id=1, db=db, user=user)
        self.assertEqual(response, 4.5)

    async def test_images_by_rating(self):
        db = Mock(spec=Session)
        user = Mock()
        user.id = 1

        db.query.return_value.join.return_value.order_by.return_value.group_by.return_value.all.return_value = [
            (Mock(), 4.5),
            (Mock(), 3.0)
        ]
        response = await images_by_rating(db=db, user=user)
        self.assertEqual(len(response), 2)
        self.assertIsInstance(response[0], Mock)
