from typing import List
from fastapi import APIRouter, Depends, Path, status, HTTPException

from src.database.models import User, Role
from src.repository import ratings as repository_ratings
from src.schemas import RatingResponse, AverageRatingResponse, ImageURLResponse
from src.database.db import get_db
from src.services.auth import auth_service
from src.services.roles import RoleAccess

from sqlalchemy.orm import Session


router = APIRouter(prefix='/rating', tags=['ratings'])

post_operation = RoleAccess([Role.admin, Role.moderator, Role.user])
get_operation = RoleAccess([Role.admin, Role.moderator, Role.user])
delete_operation = RoleAccess([Role.admin, Role.moderator])


@router.post('/{image_id}/{rate}', response_model=RatingResponse, dependencies=[Depends(post_operation)])
async def create_rate(image_id: int,
                      rate: int = Path(description='From one to five stars', ge=1, le=5),
                      db: Session = Depends(get_db),
                      current_user: User = Depends(auth_service.get_current_user)):
    new_rate = await repository_ratings.create_rating(image_id, rate, db, current_user)
    if new_rate is None:
        raise HTTPException(status_code=404, detail='Image not found')
    return new_rate


@router.get('/image_rating/{image_id}', response_model=AverageRatingResponse)
async def rating(image_id: int,
                 db: Session = Depends(get_db),
                 current_user: User = Depends(auth_service.get_current_user)):
    average_rate = await repository_ratings.calculate_rating(image_id, db, current_user)
    if average_rate is None:
        raise HTTPException(status_code=404, detail='Image not found')
    return {'average_rating': average_rate}


@router.get('/image_by_rating', response_model=List[ImageURLResponse])
async def image_by_rating(db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    images_by_rating = await repository_ratings.images_by_rating(db, current_user)
    if images_by_rating is None:
        raise HTTPException(status_code=404, detail='Images not found')
    return images_by_rating


@router.delete('/delete/{rate_id}', status_code=204, dependencies=[Depends(delete_operation)])
async def delete_rate(rate_id: int,
                      db: Session = Depends(get_db),
                      current_user: User = Depends(auth_service.get_current_user)):
    deleted_rate = await repository_ratings.del_rate(rate_id, db, current_user)
    if deleted_rate is None:
        raise HTTPException(status_code=404, detail='Rate not found')
    return deleted_rate
