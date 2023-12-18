import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import func

from fastapi import HTTPException, status
from src.schemas import CommentByUser, ImageAddResponse, ImageProfile, ImageTransformModel, ImageUpdateResponse, ImagesByFilter
import unittest
import asyncio
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from src.database.models import Image, Rating, Tag, User
from src.services.cloud_images_service import CloudImage, image_cloudinary
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

from src.conf import messages
class TestAddImage(unittest.TestCase):
    async def setUp(self) -> None:
        self.session = MagicMock(spec=Session)
        
    async def test_add_image(self):
        db_mock = MagicMock(Session)
        url = "http://example.com/image.jpg"
        public_id = "1234567890"
        user = User(id=1, name="test_user")
        description = "Test image"

        result = await add_image(db_mock, url, public_id, user, description)

        self.assertIsInstance(result, Image)
        self.assertEqual(result.url, url)
        self.assertEqual(result.public_id, public_id)
        self.assertEqual(result.user_id, user.id)
        self.assertEqual(result.description, description)
        db_mock.rollback.assert_called()

    async def test_delete_image(self):
        db_mock = MagicMock()
        image_id = 1
        fake_image = Image(id=image_id, public_id="fake_public_id")

        db_mock.query().filter().first.return_value = fake_image
        db_mock.commit.return_value = None

        deleted_image = await delete_image(db_mock, image_id)

        db_mock.query.assert_called_once()
        db_mock.query().filter.assert_called_once_with(Image.id == image_id)
        db_mock.query().filter().first.assert_called_once()
        db_mock.delete.assert_called_once_with(fake_image)
        db_mock.commit.assert_called_once()

        image_cloudinary.delete_img.assert_called_once_with(fake_image.public_id)

        self.assertEqual(deleted_image, fake_image)

        db_mock.reset_mock()

    async def test_update_description(self):
        db_mock = MagicMock(Session)
        image_id = 1
        new_description = "New image description"

        updated_image = await update_desc(db_mock, image_id, new_description)

        db_mock.query.assert_called_with(Image)
        db_mock.query.return_value.filter.assert_called_with(Image.id == image_id)
        db_mock.query.return_value.filter.return_value.first.return_value.refresh.assert_called()
        self.assertEqual(updated_image.description, new_description)

    async def test_get_image_by_id(self):
        db_mock = MagicMock(Session)
        image_id = 1

        fetched_image = await get_image_by_id(db_mock, image_id)

        db_mock.query.assert_called_with(Image)
        db_mock.query.return_value.filter.assert_called_with(Image.id == image_id)
        self.assertEqual(fetched_image, db_mock.query.return_value.filter.return_value.first.return_value)

    async def test_change_size_image(self):
        db_mock = MagicMock()
        body = MagicMock()
        body.id = 1
        body.width = 500
        user = User(id=1, name="test_user")

        result = await change_size_image(body, db_mock, user)

        self.assertIsNotNone(result) 
        self.assertIsInstance(result, ImageAddResponse)
    
    async def test_fade_edges_image(self):
        await self._test_image_transformation(fade_edges_image)

    async def test_black_white_image(self):
        await self._test_image_transformation(black_white_image)

    async def _test_image_transformation(self, transformation_function):
        db_mock = MagicMock()
        body = MagicMock()
        body.id = 1 
        user = User(id=1, name="test_user") 
        result = await transformation_function(body, db_mock, user)

        self.assertIsNotNone(result) 
        self.assertIsInstance(result, ImageAddResponse)
    
    async def test_filter_by_keyword(self):
        db_mock = MagicMock()
        current_user = User(id=1, name="test_user") 
        keyword = "test"

        expected_result = ImagesByFilter(images=[
            ImageProfile(
                url="http://example.com/image.jpg",
                description="Test image",
                average_rating=4.5,
                tags=["nature", "landscape"],
                comments=[
                    CommentByUser(user_id=1, comment="Great image!"),
                    CommentByUser(user_id=2, comment="Nice shot!"),
                ]
            ),
        ])

        result = await get_all_images(db_mock, current_user, keyword=keyword)

        db_mock.query.assert_called_with(Image)
        db_mock.query.return_value.filter.assert_called_with(Image.description.ilike(f"%{keyword}%"))

        self.assertEqual(result, expected_result)
        
    async def test_filter_by_tag(self):
        db_mock = MagicMock()
        current_user = User(id=1, name="test_user")  
        tag = "nature"

        expected_result = ImagesByFilter(images=[
            ImageProfile(
                url="http://example.com/nature_image.jpg",
                description="Nature's beauty",
                average_rating=4.8,
                tags=["nature", "landscape"],
                comments=[
                    CommentByUser(user_id=1, comment="Amazing scenery!"),
                    CommentByUser(user_id=2, comment="Love this shot!"),
                ]
            ),
        ])

        result = await get_all_images(db_mock, current_user, tag=tag)

        db_mock.query.assert_called_with(Image)
        db_mock.query.return_value.filter.assert_called_with(Image.tags.any(Tag.tag_name == tag))

        self.assertEqual(result, expected_result)
    
    async def test_filter_by_min_rating(self):
        db_mock = MagicMock()
        current_user = User(id=1, name="test_user")  
        min_rating = 3.5 

        expected_result = [
            Image(id=1, url="http://example.com/image1.jpg", description="Description 1"),
            Image(id=2, url="http://example.com/image2.jpg", description="Description 2"),
        ]

        db_mock.query().join().group_by().having().all.return_value = expected_result

        result = await get_all_images(db_mock, current_user, min_rating=min_rating)

        db_mock.query.assert_called_with(Image)
        db_mock.query.return_value.join.assert_called_with(Rating, Image.id == Rating.image_id)
        db_mock.query.return_value.group_by.assert_called_with(Image.id)
        db_mock.query.return_value.having.assert_called_with(func.avg(Rating.rate) >= min_rating)

        self.assertEqual(result, expected_result)
    
    async def test_qr_code_url_generation(self):
        db_mock = MagicMock()
        user = User(id=1, name="test_user")  
        body = ImageTransformModel(id=1)
        image = Image(id=1, url="http://example.com/image.jpg", qr_url=None)

        expected_qr_url = "Expected QR-code URL"
        
        db_mock.query.return_value.filter.return_value.first.return_value = image

        CloudImage.get_url_for_image = MagicMock(return_value=expected_qr_url)

        result = await create_qr(body, db_mock, user)

        db_mock.query.assert_called_with(Image)
        db_mock.query.return_value.filter.assert_called_with(Image.id == body.id)
        db_mock.commit.assert_called()

        self.assertEqual(result.qr_code_url, expected_qr_url)
    
    async def test_successful_tag_addition(self):
        db_mock = MagicMock()
        user = User(id=1, name="test_user")
        image_id = 1
        tag_name = "new_tag"

        result = await add_tag(db_mock, user, image_id, tag_name)

        db_mock.query.assert_called_with(Image)
        db_mock.query.return_value.filter.assert_called_with(Image.id == image_id)
        db_mock.commit.assert_called()

        self.assertEqual(result["message"], "Tag successfully added")
        self.assertEqual(result["tag"], tag_name)
    
    async def test_failed_tag_addition_due_to_limit(self):
        db_mock = MagicMock()
        user = User(id=1, name="test_user")
        image_id = 1
        tag_name = "new_tag"

        image_with_max_tags = Image(tags=[Tag(), Tag(), Tag(), Tag(), Tag()])

        db_mock.query.return_value.filter.return_value.first.return_value = image_with_max_tags

        try:
            await add_tag(db_mock, user, image_id, tag_name)
        except HTTPException as e:
            # Assert
            self.assertEqual(e.status_code, status.HTTP_406_NOT_ACCEPTABLE)
            self.assertEqual(e.detail, messages.ONLY_FIVE_TAGS)
    
    
    async def test_failed_tag_addition_due_to_user_permission(self):
        db_mock = MagicMock()
        user = User(id=1, name="test_user")
        image_owner = User(id=2, name="image_owner")
        image_id = 1
        tag_name = "new_tag"

        image = Image(user_id=image_owner.id)

        db_mock.query.return_value.filter.return_value.first.return_value = image

        try:
            await add_tag(db_mock, user, image_id, tag_name)
        except HTTPException as e:
            self.assertEqual(e.status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(e.detail, messages.NOT_ALLOWED)
            
if __name__ == '__main__':
    unittest.main()
