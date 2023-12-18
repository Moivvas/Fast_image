import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import MagicMock
from src.database.models import Image, User
from src.repository.cloud_image import (
    add_image,
    change_size_image,
    delete_image,
    update_desc,
    get_image_by_id,
    fade_edges_image,
    black_white_image,
    get_all_images,
    create_qr,
    add_tag)

class TestImageRepository(unittest.TestCase):
    async def setUp(self) -> None:
        self.db_mock = MagicMock()

    async def test_image_repository(self):
        test_cases = [
            (add_image, [1, "http://example.com/image.jpg", "1234567890", User(id=1, name="test_user"), "Test image"], Image),
            (delete_image, [1], None),
            (update_desc, [1, "New image description"], Image),
            (get_image_by_id, [1], Image),
            (change_size_image, [MagicMock(id=1, width=500), self.db_mock, User(id=1, name="test_user")], Image),
            (fade_edges_image, [MagicMock(id=1), self.db_mock, User(id=1, name="test_user")], Image),
            (black_white_image, [MagicMock(id=1), self.db_mock, User(id=1, name="test_user")], Image),
            (get_all_images, [self.db_mock, User(id=1, name="test_user"), "test"], None),
            (create_qr, [MagicMock(id=1), self.db_mock, User(id=1, name="test_user")], Image),
            (add_tag, [self.db_mock, User(id=1, name="test_user"), 1, "new_tag"], {"message": "Tag successfully added", "tag": "new_tag"}),
            (add_tag, [self.db_mock, User(id=1, name="test_user"), 1, "new_tag"], None),
            (add_tag, [self.db_mock, User(id=1, name="test_user"), 1, "new_tag"], None)
        ]

        for test_function, test_args, expected_output in test_cases:
            result = await test_function(*test_args)
            self.assertEqual(type(result), expected_output)

if __name__ == '__main__':
    unittest.main()