from typing import List
from fastapi import APIRouter, Depends, Path, HTTPException, status

from src.database.models import User, Role
from src.repository import ratings as repository_ratings
from src.schemas import RatingModel, ImageModel, RatingResponse
from src.database.db import get_db
from src.services.auth import auth_service
from src.services.roles import RoleAccess
from src.conf import messages

from sqlalchemy.orm import Session


router = APIRouter(prefix="/ratings", tags=["ratings"])

get_all_ratings = RoleAccess([Role.admin, Role.moderator, Role.user])
create_ratings = RoleAccess([Role.admin, Role.moderator, Role.user])
remove_ratings = RoleAccess([Role.admin, Role.moderator])
user_image_rate = RoleAccess([Role.admin])
rates_by_user = RoleAccess([Role.admin, Role.moderator, Role.user])
search_user_with_images = RoleAccess([Role.admin, Role.moderator])


@router.post(
    "/{image_id}/{rate}",
    response_model=RatingModel,
    dependencies=[Depends(create_ratings)],
)
async def create_rate(
    image_id: int,
    rate: int = Path(description="From one to five stars", ge=1, le=5),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Create a rating for an image.

    This endpoint allows a user to create a rating for a specific image.

    :param image_id: The ID of the image to rate.
    :type image_id: int
    :param rate: The rating value, from one to five stars.
    :type rate: int
    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: Created rating.
    :rtype: RatingModel
    """
    new_rate = await repository_ratings.create_rate(image_id, rate, db, current_user)
    if new_rate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.NO_IMAGE_ID
        )
    return new_rate


@router.get(
    "/all_my", response_model=List[RatingModel], dependencies=[Depends(rates_by_user)]
)
async def all_my_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Get all ratings given by the current user.

    This endpoint retrieves all ratings given by the current authenticated user.

    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: List of ratings given by the user.
    :rtype: List[RatingModel]
    """
    rates = await repository_ratings.show_my_ratings(db, current_user)
    if rates is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.RATE_NOT_FOUND
        )
    return rates


@router.get(
    "/search_user_with_images",
    response_model=List[ImageModel],
    dependencies=[Depends(search_user_with_images)],
)
async def search_users_with_images(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Search for users who have uploaded images.

    This endpoint retrieves a list of users who have uploaded images.

    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: List of users with images.
    :rtype: List[ImageModel]
    """
    users_with_images = await repository_ratings.user_with_images(db, current_user)
    if not users_with_images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.NO_USER_WITH_IMAGES
        )
    return users_with_images


@router.get(
    "/{image_id}",
    response_model=RatingResponse,
    dependencies=[Depends(get_all_ratings)],
)
async def get_image_avg_rating(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Get the average rating for a specific image.

    This endpoint calculates and returns the average rating for a specific image.

    :param image_id: The ID of the image to calculate the average rating.
    :type image_id: int
    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: Average rating for the image.
    :rtype: RatingResponse
    """
    images_by_rating = await repository_ratings.calculate_rating(
        image_id, db, current_user
    )
    if images_by_rating is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.RATE_NOT_FOUND
        )
    return images_by_rating


@router.get(
    "/user_image/{user_id}/{image_id}",
    response_model=RatingModel,
    dependencies=[Depends(user_image_rate)],
)
async def user_rate_image(
    user_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Get the rating given by a specific user to a specific image.

    This endpoint retrieves the rating given by a specific user to a specific image.

    :param user_id: The ID of the user who gave the rating.
    :type user_id: int
    :param image_id: The ID of the image to retrieve the rating for.
    :type image_id: int
    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: Rating given by the user to the image.
    :rtype: RatingModel
    """
    rate = await repository_ratings.user_rate_image(user_id, image_id, db, current_user)
    if rate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.RATE_NOT_FOUND
        )
    return rate


@router.delete(
    "/delete/{rate_id}",
    response_model=RatingModel,
    dependencies=[Depends(remove_ratings)],
)
async def delete_rate(
    rate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Delete a rating.

    This endpoint deletes a rating given by the current authenticated user.

    :param rate_id: The ID of the rating to be deleted.
    :type rate_id: int
    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: The deleted rating.
    :rtype: RatingModel
    """
    deleted_rate = await repository_ratings.delete_rate(rate_id, db, current_user)
    if deleted_rate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.RATE_NOT_FOUND
        )
    return deleted_rate
