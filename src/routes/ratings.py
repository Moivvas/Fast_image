from typing import List
from fastapi import APIRouter, Depends, Path, HTTPException, status

from src.database.models import User, Role
from src.repository import ratings as repository_ratings
from src.schemas import RatingModel, AverageRatingResponse, ImageModel, RatingResponse
from src.database.db import get_db
from src.services.auth import auth_service
from src.services.roles import RoleAccess
from src.conf import messages

from sqlalchemy.orm import Session


router = APIRouter(prefix='/ratings', tags=['ratings'])

get_all_ratings = RoleAccess([Role.admin, Role.moderator, Role.user])
create_ratings = RoleAccess([Role.admin, Role.moderator, Role.user])
remove_ratings = RoleAccess([Role.admin, Role.moderator])
user_image_rate = RoleAccess([Role.admin])
rates_by_user = RoleAccess([Role.admin, Role.moderator, Role.user])
search_user_with_images = RoleAccess([Role.admin, Role.moderator])


@router.post('/{image_id}/{rate}', response_model=RatingModel, dependencies=[Depends(create_ratings)])
async def create_rate(image_id: int,
                      rate: int = Path(description='From one to five stars', ge=1, le=5),
                      db: Session = Depends(get_db),
                      current_user: User = Depends(auth_service.get_current_user)):
    new_rate = await repository_ratings.create_rate(image_id, rate, db, current_user)
    if new_rate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NO_IMAGE_ID)
    return new_rate


@router.get('/all_my', response_model=List[RatingModel], dependencies=[Depends(rates_by_user)])
async def all_my_rates(db: Session = Depends(get_db),
                       current_user: User = Depends(auth_service.get_current_user)):
    rates = await repository_ratings.show_my_ratings(db, current_user)
    if rates is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.RATE_NOT_FOUND)
    return rates


@router.get('/search_user_with_images', response_model=List[ImageModel],
            dependencies=[Depends(search_user_with_images)])
async def search_users_with_images(db: Session = Depends(get_db),
                                   current_user: User = Depends(auth_service.get_current_user)):
    users_with_images = await repository_ratings.user_with_images(db, current_user)
    if not users_with_images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NO_USER_WITH_IMAGES)
    return users_with_images


@router.get('/{image_id}',
            response_model=RatingResponse,
            dependencies=[Depends(get_all_ratings)])
async def get_image_avg_rating(image_id: int,
                          db: Session = Depends(get_db),
                          current_user: User = Depends(auth_service.get_current_user)):
    images_by_rating = await repository_ratings.calculate_rating(image_id, db, current_user)
    if images_by_rating is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.RATE_NOT_FOUND)
    return images_by_rating


@router.get('/user_image/{user_id}/{image_id}', response_model=RatingModel, dependencies=[Depends(user_image_rate)])
async def user_rate_image(user_id: int,
                          image_id: int,
                          db: Session = Depends(get_db),
                          current_user: User = Depends(auth_service.get_current_user)):
    rate = await repository_ratings.user_rate_image(user_id, image_id, db, current_user)
    if rate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.RATE_NOT_FOUND)
    return rate


@router.delete('/delete/{rate_id}', response_model=RatingModel, dependencies=[Depends(remove_ratings)])
async def delete_rate(rate_id: int,
                      db: Session = Depends(get_db),
                      current_user: User = Depends(auth_service.get_current_user)):
    deleted_rate = await repository_ratings.delete_rate(rate_id, db, current_user)
    if deleted_rate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.RATE_NOT_FOUND)
    return deleted_rate



