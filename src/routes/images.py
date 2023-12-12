from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.db import get_db
from src.schemas import Rating
from src.services.images import rate_image, get_average_rating

router = APIRouter()


@router.post('/rate-image')
async def rate_image_route(rating: Rating, db: Session = Depends(get_db)):
    return rate_image(db, rating)


@router.get('/average-rating/{image_id}')
async def average_rating_route(image_id: int, db: Session = Depends(get_db)):
    return {"average_rating": get_average_rating(db, image_id)}
