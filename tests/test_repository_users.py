import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from src.database.models import User

from src.schemas import UserModel

from src.repository.users import get_users, get_user_by_email, create_user, update_token, update_avatar, ban_user, unban_user, update_user_profile_me_info, update_user_profile_me_credential


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
        body = UserModel(name="Dima", email="ex@ex.com", password="qwerty", sex="male")
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

    async def test_update_user_profile_me_info(self):
        user = self.user
        new_name = "Richard"

        with patch("src.repository.users.get_user_by_id", return_value=user):
            result = await update_user_profile_me_info(
                user_id=user.id,
                new_name=new_name,
                db=self.session,
                current_user=user
            )
            self.assertEqual(result.name, new_name)

    async def test_update_user_profile_me_credential(self):
        new_email = "new_email@example.com"
        new_password = "new_password"

        with patch("src.repository.users.get_user_by_id") as mock_get_user_by_id, \
             patch("src.repository.users.get_user_by_email") as mock_get_user_by_email, \
             patch("src.services.auth.auth_service.get_password_hash") as mock_get_password_hash:

            mock_get_user_by_id.return_value = self.user
            mock_get_user_by_email.return_value = None
            mock_get_password_hash.return_value = "hashed_password"

            result = await update_user_profile_me_credential(
                user_id=self.user.id,
                new_email=new_email,
                new_password=new_password,
                db=self.session,
                current_user=self.user,
            )
            self.assertEqual(result, self.user)
            mock_get_user_by_id.assert_called_once_with(self.user.id, self.session)
            mock_get_user_by_email.assert_called_once_with(new_email, self.session)
            mock_get_password_hash.assert_called_once_with(new_password)
            self.assertEqual(self.user.email, new_email)
            self.assertEqual(self.user.password, "hashed_password")
            self.session.commit.assert_called_once()
            self.session.refresh.assert_called_once_with(self.user)


if __name__ == '__main__':
    unittest.main()
