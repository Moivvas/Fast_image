from typing import Type

from fastapi import HTTPException, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.database.models import Rating, User, Image, Role
from src.conf import messages


async def create_rate(image_id: int, rate: int, db: Session, user: User) -> Rating:
    is_self_post = db.query(Image).filter(and_(Image.id == image_id, Image.user_id == user.id)).first()
    already_voted = db.query(Rating).filter(and_(Rating.image_id == image_id, Rating.user_id == user.id)).first()
    image_exists = db.query(Image).filter(Image.id == image_id).first()
    if is_self_post:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=messages.OWN_POST)
    elif already_voted:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=messages.VOTE_TWICE)
    elif image_exists:
        new_rate = Rating(
            image_id=image_id,
            rate=rate,
            user_id=user.id
        )
        db.add(new_rate)
        db.commit()
        db.refresh(new_rate)
        return new_rate


async def edit_rate(rate_id: int, new_rate: int, db: Session, user: User) -> Type[Rating] | None:
    rate = db.query(Rating).filter(Rating.id == rate_id).first()
    if user.role in [Role.admin, Role.moderator] or rate.user_id == user.id:
        if rate:
            rate.rate = new_rate
            db.commit()
    return rate


async def delete_rate(rate_id: int, db: Session, user: User) -> Type[Rating]:
    rate = db.query(Rating).filter(Rating.id == rate_id).first()
    if rate:
        db.delete(rate)
        db.commit()
    return rate


async def calculate_rating(image_id: int, db: Session, user: User):
    all_ratings = db.query(func.avg(Rating.rate)).filter(Rating.image_id == image_id).scalar()
    image_url = db.query(Image.url).filter(Image.id == image_id).scalar()
    return {'average_rating': all_ratings, 'image_url': str(image_url)}


async def show_my_ratings(db: Session, current_user) -> list[Type[Rating]]:
    all_ratings = db.query(Rating).filter(Rating.user_id == current_user.id).all()
    return all_ratings


async def user_rate_image(user_id: int, image_id: int, db: Session, user: User) -> Type[Rating] | None:
    user_p_rate = db.query(Rating).filter(and_(Rating.image_id == image_id, Rating.user_id == user_id)).first()
    return user_p_rate


async def user_with_images(db: Session, user: User):
    user_w_images = db.query(Image).all()
    return user_w_images
