import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from src.database.models import User

from src.schemas import UserModel

from src.repository.users import get_users, get_user_by_email, create_user, update_token, update_avatar, ban_user, unban_user


class TestUsersRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.session = MagicMock(spec=Session)
        self.user = User(id=1, name="Dima", email="test@test.com", password="qwerty", avatar="ava", forbidden="False")

    async def test_get_users(self):
        users = [User(), User()]
        self.session.query().all.return_value = users
        result = await get_users(self.session)
        self.assertEqual(result, users)

    async def test_get_user_by_email(self):
        user = User()
        email = "ex@ex.com"
        self.session.query().filter_by().first.return_value = user
        result = await get_user_by_email(email, self.session)
        self.assertEqual(result, user)

    async def test_create_user(self):
        body = UserModel(name="Dima", email="ex@ex.com", password="qwerty")
        result = await create_user(body, self.session)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.email, body.email)
        self.assertTrue(hasattr(result, "id"))

    async def test_update_token(self):
        user = User()
        refresh_token = "qweqrqadsd"
        result = await update_token(user, refresh_token, self.session)
        self.assertEqual(user.refresh_token, refresh_token)

    async def test_update_avatar(self):
        user = self.user
        avatar = "avatar"
        result = await update_avatar(user.email, avatar, self.session)
        self.assertEqual(result.avatar, avatar)

    async def test_ban_user(self):
        result = await ban_user(self.user.email, self.session)
        self.assertTrue(result.forbidden)

    async def test_unban_user(self):
        result = await unban_user(self.user.email, self.session)
        self.assertFalse(result.forbidden)
