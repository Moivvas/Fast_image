from operator import or_

from fastapi import HTTPException, status
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from src.repository import ratings as repository_ratings

from src.database.models import Image, User, Tag, Rating

import qrcode
from io import BytesIO
from src.database.models import Image, User

from src.services.cloud_images_service import CloudImage, image_cloudinary

from src.schemas import (
    ImageChangeSizeModel,
    ImageAddResponse,
    ImageModel,
    ImageTransformModel,
    ImageProfile,
    CommentByUser,
    ImagesByFilter,
    ImageQRResponse
)

from src.conf import messages


async def add_image(
    db: Session, url: str, public_id: str, user: User, description: str
):
    if not user:
        return None
    db_image = Image(
        url=url, public_id=public_id, user_id=user.id, description=description
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image


async def delete_image(db: Session, id: int):
    db_image = db.query(Image).filter(Image.id == id).first()
    image_cloudinary.delete_img(db_image.public_id)
    db.delete(db_image)
    db.commit()
    return db_image


async def update_desc(db: Session, id: int, description=str):
    db_image = db.query(Image).filter(Image.id == id).first()
    db_image.description = description
    db.commit()
    db.refresh(db_image)
    return db_image


async def get_image_by_id(db: Session, image_id: int) -> Image:
    db_image = db.query(Image).filter(Image.id == image_id).first()
    return db_image


async def change_size_image(body: ImageChangeSizeModel, db: Session, user: User):
    try:
        image = db.query(Image).filter(Image.id == body.id).first()
        if image is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
            )
        url, public_id = await image_cloudinary.change_size(image.public_id, body.width)
        new_image = Image(
            url=url, public_id=public_id, user_id=user.id, description=image.description
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        image_model = ImageModel(
            id=new_image.id,
            url=new_image.url,
            public_id=new_image.public_id,
            user_id=new_image.user_id,
        )
        return ImageAddResponse(image=image_model, detail=messages.IMAGE_RESIZED_ADDED)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def fade_edges_image(body: ImageTransformModel, db: Session, user: User):
    try:
        image = db.query(Image).filter(Image.id == body.id).first()
        if image is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
            )

        url, public_id = await image_cloudinary.fade_edges_image(
            public_id=image.public_id
        )

        new_image = Image(
            url=url, public_id=public_id, user_id=user.id, description=image.description
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)

        image_model = ImageModel(
            id=new_image.id,
            url=new_image.url,
            public_id=new_image.public_id,
            user_id=new_image.user_id,
        )

        return ImageAddResponse(image=image_model, detail=messages.IMAGE_FADE_ADDED)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def black_white_image(body: ImageTransformModel, db: Session, user: User):
    try:
        image = db.query(Image).filter(Image.id == body.id).first()
        if image is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
            )

        url, public_id = await image_cloudinary.make_black_white_image(
            public_id=image.public_id
        )

        new_image = Image(
            url=url, public_id=public_id, user_id=user.id, description=image.description
        )

        db.add(new_image)
        db.commit()
        db.refresh(new_image)

        image_model = ImageModel(
            id=new_image.id,
            url=new_image.url,
            public_id=new_image.public_id,
            user_id=new_image.user_id,
        )

        return ImageAddResponse(image=image_model, detail=messages.BLACK_WHITE_ADDED)
    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def get_all_images(
    db: Session,
    current_user: User,
    keyword: str = None,
    tag: str = None,
    min_rating: int = None,
):
    query = db.query(Image)
    if keyword:
        query = query.filter(
            or_(
                Image.image_name.ilike(f"%{keyword}%"),
                Image.description.ilike(f"%{keyword}%"),
            )
        )
    if tag:
        query = query.filter(Image.tags.any(Tag.tag_name == tag))
    if min_rating is not None:
        query = query.join(Rating, Image.id == Rating.image_id)
        query = query.group_by(Image.id).having(func.avg(Rating.rate) >= min_rating)
    query = query.order_by(desc(Image.created_at))
    result = query.all()
    images = []
    for image in result:
        tags = []
        comments = []
        for comment in image.comments:
            new_comment = CommentByUser(
                user_id=comment.user_id, comment=comment.comment
            )
            comments.append(new_comment)
        for tag in image.tags:
            new_tag = tag.tag_name
            tags.append(new_tag)
        rating = await repository_ratings.calculate_rating(image.id, db, current_user)
        new_image = ImageProfile(
            url=image.url,
            description=image.description,
            average_rating=rating,
            tags=tags,
            comments=comments,
        )
        images.append(new_image)
    all_images = ImagesByFilter(images=images)
    return all_images


async def create_qr(body: ImageTransformModel, db: Session, user: User):
    try:
        image = db.query(Image).filter(Image.id == body.id).first()
        
        if image is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND)
        
        qr = qrcode.QRCode()
        qr.add_data(image.url)
        qr.make(fit=True)
        
        qr_code_img = BytesIO()
        qr.make_image(fill_color="black", back_color="white").save(qr_code_img, format='PNG')
        
        qr_code_img.seek(0)
        
        new_public_id = CloudImage.generate_name_image(user.email)
        
        upload_file = CloudImage.upload_image(qr_code_img, new_public_id, folder="qrcodes")

        qr_code_url = CloudImage.get_url_for_image(new_public_id, upload_file)
        
        image.qr_url = qr_code_url
        
        db.commit()
                
        return ImageQRResponse(image_id=image.id, qr_code_url=qr_code_url)
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    



