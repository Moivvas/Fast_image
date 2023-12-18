from fastapi import HTTPException, status
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from src.repository import ratings as repository_ratings

from src.database.models import Image, User, Tag, Rating

import qrcode
from io import BytesIO

from src.repository.tags import create_tag

from src.services.cloud_images_service import CloudImage, image_cloudinary

from src.schemas import (
    ImageChangeSizeModel,
    ImageAddResponse,
    ImageModel,
    ImageTransformModel,
    ImageProfile,
    CommentByUser,
    ImagesByFilter,
    ImageQRResponse,
    TagModel,
)

from src.conf import messages


async def add_image(
    db: Session, url: str, public_id: str, user: User, description: str
):
    if not user:
        return None
    image = Image(
        url=url, public_id=public_id, user_id=user.id, description=description
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


async def delete_image(db: Session, image_id: int):
    image = db.query(Image).filter(Image.id == image_id).first()
    image_cloudinary.delete_img(image.public_id)
    db.delete(image)
    db.commit()
    return image


async def update_desc(db: Session, image_id: int, description=str):
    image = db.query(Image).filter(Image.id == image_id).first()
    image.description = description
    db.commit()
    db.refresh(image)
    return image


async def get_image_by_id(db: Session, image_id: int) -> Image | None:
    image = db.query(Image).filter(Image.id == image_id).first()
    return image


async def change_size_image(body: ImageChangeSizeModel, db: Session, user: User):
    
    image = db.query(Image).filter(Image.id == body.id).first()
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND)
    if image.user_id != user.id:
        raise HTTPException(status_code=403, detail=messages.NOT_ALLOWED)

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
    

async def fade_edges_image(body: ImageTransformModel, db: Session, user: User):
    image = db.query(Image).filter(Image.id == body.id).first()
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
        )

    if image.user_id != user.id:
        raise HTTPException(status_code=403, detail=messages.NOT_ALLOWED)
    
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


async def black_white_image(body: ImageTransformModel, db: Session, user: User):
    image = db.query(Image).filter(Image.id == body.id).first()
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
        )
    if image.user_id != user.id:
        raise HTTPException(status_code=403, detail=messages.NOT_ALLOWED)

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


async def get_all_images(
    db: Session,
    current_user: User,
    keyword: str = None,
    tag: str = None,
    min_rating: float = None,
):
    query = db.query(Image)
    if keyword:
        query = query.filter(Image.description.ilike(f"%{keyword}%"))
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
        new_rating = rating['average_rating']
        new_image = ImageProfile(
            url=image.url,
            description=image.description,
            average_rating=new_rating,
            tags=tags,
            comments=comments,
        )
        images.append(new_image)
    all_images = ImagesByFilter(images=images)
    return all_images


async def create_qr(body: ImageTransformModel, db: Session, user: User):
    image = db.query(Image).filter(Image.id == body.id).first()

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
        )
    if image.qr_url:
        return ImageQRResponse(image_id=image.id, qr_code_url=image.qr_url)
    
    qr = qrcode.QRCode()
    qr.add_data(image.url)
    qr.make(fit=True)

    qr_code_img = BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(
        qr_code_img
    )

    qr_code_img.seek(0)

    new_public_id = CloudImage.generate_name_image(user.email)

    upload_file = CloudImage.upload_image(
        qr_code_img, new_public_id)

    qr_code_url = CloudImage.get_url_for_image(new_public_id, upload_file)

    image.qr_url = qr_code_url

    db.commit()

    return ImageQRResponse(image_id=image.id, qr_code_url=qr_code_url)

    
async def add_tag(db: Session, user: User, image_id: int, tag_name: str):
    print('repo before db image')

    image = db.query(Image).filter(Image.id == image_id).first()
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
        )
    if image.user_id != user.id:
        raise HTTPException(status_code=403, detail=messages.NOT_ALLOWED)
    if len(image.tags) >= 5:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=messages.ONLY_FIVE_TAGS
        )
    tag = db.query(Tag).filter(Tag.tag_name == tag_name.lower()).first()
    print(image.tags)
    print(type(image.tags))

    if tag is None:
        tag_model = TagModel(tag_name=tag_name)
        tag = await create_tag(tag_model, db)

    image.tags.append(tag)

    db.commit()
    db.refresh(image)

    return {"message": "Tag successfully added", "tag": tag.tag_name}
