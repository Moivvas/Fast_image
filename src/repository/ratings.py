from fastapi import HTTPException

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.database.models import Rating, User, Image


async def create_rating(img_id: int, rate: int, db: Session, user: User):
    self_image = db.query(Image).filter(Image.id == img_id).first().user_id == user.id
    already_rated = db.query(Rating).filter(and_(Rating.image_id == img_id, Rating.user_id == user.id)).first()
    image_exists = db.query(Image).filter(Image.id == img_id).first()

    if self_image:
        raise HTTPException(status_code=423, detail='You cannot rate your own images')
    if already_rated:
        raise HTTPException(status_code=423, detail='You cannot rate an image twice')
    if image_exists:
        new_rate = Rating(image_id=img_id, rate=rate, user_id=user.id)
        db.add(new_rate)
        db.commit()
        db.refresh(new_rate)
        return new_rate


async def del_rate(rate_id: int, db: Session, user: User):
    rate = db.query(Rating).filter(Rating.id == rate_id).first()
    if rate:
        db.delete(rate)
        db.commit()
    return None


async def calculate_rating(image_id: int, db: Session, user: User):
    rating = db.query(func.avg(Rating.rate)).filter(Rating.image_id == image_id).scalar()
    return rating


async def images_by_rating(db: Session, user: User):
    images = db.query(Image, func.avg(Rating.rate).label('rate')).join(Rating).order_by('rate').group_by(Image).all()
    sort_images = []
    for image in images:
        sort_images.append(image.Image)
    return sort_images
