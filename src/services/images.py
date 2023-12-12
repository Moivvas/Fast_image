from fastapi import HTTPException, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.database import models
from src.database.models import Image, User
from src.schemas import Rating
from src.services.auth import Auth

auth_service = Auth()


def rate_image(db: Session, rating: Rating, current_user: User = Depends(auth_service.get_current_user)):
    image = db.query(Image).filter(Image.id == rating.image_id).first()
    if image:
        if image.user_id == current_user.id:
            raise HTTPException(status_code=400, detail='You cannot rate your own photo.')

        if 1 <= rating.rating <= 5:
            image.total_rating += 1
            image.average_rating = ((image.average_rating * (image.total_rating - 1))
                                    + rating.rating) / image.total_rating
            db.commit()
            return {'message': 'Rating saved successfully'}
        else:
            raise HTTPException(status_code=400, detail='Invalid rating. Please provide a rating between 1 and 5.')
    else:
        raise HTTPException(status_code=404, detail='Photo not found')


def get_average_rating(db: Session, image_id: int):
    average_rating = db.query(func.avg(models.Image.average_rating)).filter(models.Image.id == image_id).scalar()
    return average_rating or 0.0
