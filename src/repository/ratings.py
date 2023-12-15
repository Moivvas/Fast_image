from fastapi import HTTPException, status

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.database.models import Rating, User, Image
from src.conf import messages


async def create_rating(img_id: int, rate: int, db: Session, user: User):
    image = db.query(Image).filter(Image.id == img_id).first()
    already_rated = db.query(Rating).filter(Image.id == img_id).first()

    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND)

    if image.user_id == user.id:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=messages.SELF_IMAGE_RATE)
    if already_rated:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=messages.IMAGE_RATE_TWICE)

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
