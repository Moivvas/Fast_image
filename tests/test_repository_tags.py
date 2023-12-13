import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import MagicMock
from typing import List, Type

from sqlalchemy.orm import Session
from fastapi import HTTPException

from src.database.models import Tag
from src.schemas import TagModel
from src.repository.tags import (
    create_tag, 
    get_tag_by_id, 
    get_tag_by_name, 
    get_tags, 
    update_tag, 
    remove_tag_by_id, 
    remove_tag_by_name
)


class TestTag(unittest.TestCase):
    def setUp(self) -> None:
        self.session = MagicMock(spec=Session)
        self.tag_1 = Tag(tag_name = "Test_1")
        self.tag_2 = Tag(tag_name = "Test_2")
    
    async def test_create_tag(self):
        body = TagModel(tag_name = "Test_1")
        result = await create_tag(body, self.session)
        self.assertEqual(result, self.tag_1)

    async def test_get_tag_by_id_succsess(self):
        tag_id = 1
        tag_name = self.tag_1.tag_name
        expected_tag = Tag(tag_id, tag_name)

        self.session.query(Tag).filter_by(id=tag_id).first.return_value = expected_tag
        result = await get_tag_by_id(tag_id, self.session)
        self.assertEqual(result, expected_tag)

    async def test_get_tag_by_id_not_exists(self):
        mock_query = MagicMock(return_value=[])
        self.session = mock_query
        with self.assertRaises(HTTPException) as exc:
            await get_tag_by_id(self.tag_1.id, self.session)

    async def test_get_tag_by_name_succsess(self):
        tag_id = 1
        tag_name = self.tag_1.tag_name
        expected_tag = Tag(tag_id, tag_name)

        self.session.query(Tag).filter_by(tag_name=tag_name).first.return_value = expected_tag
        result = await get_tag_by_name(tag_name, self.session)
        self.assertEqual(result, expected_tag)
    
    async def test_get_tag_by_name_not_exists(self):
        mock_query = MagicMock(return_value="")
        self.session = mock_query
        with self.assertRaises(HTTPException) as exc:
            await get_tag_by_name(self.tag_1.tag_name, self.session)

    async def test_get_tags_succsess(self):
        tags = [self.tag_1, self.tag_2]
        self.session.query(Tag).filter_by().all.return_value = tags
        result = await get_tags(self.session)
        self.assertEqual(result, tags)   
    
    async def test_get_tags_not_exist(self):
        mock_query = MagicMock(return_value=[])
        self.session = mock_query
        with self.assertRaises(HTTPException) as exc:
            await get_tags(self.session)

    async def test_update_tag_success(self):
        body = TagModel(tag_name = self.tag_1.tag_name)
        tag_name_new = "New_test_1"

        updated_tag = await update_tag(self.tag_1.id, body, self.session)
        self.assertEqual(updated_tag.tag_name, tag_name_new)
        self.assertTrue(self.session.commit.called)

    async def test_update_tag_not_exists(self):
        mock_query = MagicMock(return_value=[])
        self.session= mock_query
        with self.assertRaises(HTTPException) as exc:
            await update_tag(self.session)

    async def test_remove_tag_by_id_success(self):
        body = TagModel(tag_name = self.tag_1.tag_name)
        result = await remove_tag_by_id(self.tag_1.id, self.session)
        self.assertEqual(result, body)
        self.assertTrue(self.session.commit.called)

    async def test_remove_tag_by_id_not_exists(self):
        mock_query = MagicMock(return_value=[])
        self.session.query = mock_query
        with self.assertRaises(HTTPException) as exc:
            await remove_tag_by_id(self.session)

    async def test_remove_tag_by_name_success(self):
        body = TagModel(tag_name = self.tag_1.tag_name)
        result = await remove_tag_by_name(self.tag_1.tag_name, self.session)
        self.assertEqual(result, body)
        self.assertTrue(self.session.commit.called)

    async def test_remove_tag_by_name_not_exists(self):
        mock_query = MagicMock(return_value=[])
        self.session.query = mock_query
        with self.assertRaises(HTTPException) as exc:
            await remove_tag_by_name(self.session)       
      
if __name__ == '__main__':
    unittest.main()
