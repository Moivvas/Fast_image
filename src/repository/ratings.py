from typing import Type

from fastapi import HTTPException, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.database.models import Rating, User, Image, Role
from src.conf import messages


async def create_rate(image_id: int, rate: int, db: Session, user: User) -> Rating:
    """
    Create a new rating for an image.

    This function creates a new rating for a given image. It checks if the user is trying to rate their own post,
    has already voted, or if the image exists. If any of these conditions are met, it raises an HTTPException.
    Otherwise, it creates and returns the new rating.

    :param image_id: ID of the image to be rated.
    :type image_id: int
    :param rate: Rating value (1 to 5 stars).
    :type rate: int
    :param db: Database session.
    :type db: Session
    :param user: Current user.
    :type user: User
    :return: Created Rating object.
    :rtype: Rating
    """
    is_self_post = (
        db.query(Image)
        .filter(and_(Image.id == image_id, Image.user_id == user.id))
        .first()
    )
    already_voted = (
        db.query(Rating)
        .filter(and_(Rating.image_id == image_id, Rating.user_id == user.id))
        .first()
    )
    image_exists = db.query(Image).filter(Image.id == image_id).first()
    if is_self_post:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail=messages.OWN_POST
        )
    elif already_voted:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail=messages.VOTE_TWICE
        )
    elif image_exists:
        new_rate = Rating(image_id=image_id, rate=rate, user_id=user.id)
        db.add(new_rate)
        db.commit()
        db.refresh(new_rate)
        return new_rate


async def edit_rate(
    rate_id: int, new_rate: int, db: Session, user: User
) -> Type[Rating] | None:
    """
    Edit the rating for a given image.

    This function allows the user to edit their own rating or, if the user is an admin or moderator,
    edit any rating. It updates the rating value and commits the changes to the database.

    :param rate_id: ID of the rating to be edited.
    :type rate_id: int
    :param new_rate: New rating value (1 to 5 stars).
    :type new_rate: int
    :param db: Database session.
    :type db: Session
    :param user: Current user.
    :type user: User
    :return: Updated Rating object.
    :rtype: Type[Rating] | None
    """
    rate = db.query(Rating).filter(Rating.id == rate_id).first()
    if user.role in [Role.admin, Role.moderator] or rate.user_id == user.id:
        if rate:
            rate.rate = new_rate
            db.commit()
    return rate


async def delete_rate(rate_id: int, db: Session, user: User) -> Type[Rating]:
    """
    Delete a rating.

    This function deletes a rating with the given ID. Only the user who created the rating or
    an admin/moderator can delete a rating. It removes the rating from the database and commits the changes.

    :param rate_id: ID of the rating to be deleted.
    :type rate_id: int
    :param db: Database session.
    :type db: Session
    :param user: Current user.
    :type user: User
    :return: Deleted Rating object.
    :rtype: Type[Rating]
    """
    rate = db.query(Rating).filter(Rating.id == rate_id).first()
    if rate:
        db.delete(rate)
        db.commit()
    return rate


async def calculate_rating(image_id: int, db: Session, user: User):
    """
    Calculate the average rating for an image.

    This function calculates the average rating for a given image ID and also retrieves the image URL.
    The average rating and image URL are returned in a dictionary.

    :param image_id: ID of the image for which the rating is calculated.
    :type image_id: int
    :param db: Database session.
    :type db: Session
    :param user: Current user.
    :type user: User
    :return: Dictionary containing the average rating and image URL.
    :rtype: dict
    """
    all_ratings = (
        db.query(func.avg(Rating.rate)).filter(Rating.image_id == image_id).scalar()
    )
    image_url = db.query(Image.url).filter(Image.id == image_id).scalar()
    return {"average_rating": all_ratings, "image_url": str(image_url)}


async def show_my_ratings(db: Session, current_user) -> list[Type[Rating]]:
    """
    Retrieve all ratings given by the current user.

    This function retrieves all ratings given by the current user.

    :param db: Database session.
    :type db: Session
    :param current_user: Current user.
    :type current_user: User
    :return: List of ratings given by the current user.
    :rtype: List[Type[Rating]]
    """
    all_ratings = db.query(Rating).filter(Rating.user_id == current_user.id).all()
    return all_ratings


async def user_rate_image(
    user_id: int, image_id: int, db: Session, user: User
) -> Type[Rating] | None:
    """
    Retrieve the rating given by a specific user to a specific image.

    This function retrieves the rating given by a specific user to a specific image.

    :param user_id: User ID.
    :type user_id: int
    :param image_id: Image ID.
    :type image_id: int
    :param db: Database session.
    :type db: Session
    :param user: Current user.
    :type user: User
    :return: Rating given by the specified user to the specified image.
    :rtype: Type[Rating] | None
    """
    user_p_rate = (
        db.query(Rating)
        .filter(and_(Rating.image_id == image_id, Rating.user_id == user_id))
        .first()
    )
    return user_p_rate


async def user_with_images(db: Session, user: User):
    """
    Retrieve images associated with a specific user.

    This function retrieves all images associated with a specific user.

    :param db: Database session.
    :type db: Session
    :param user: Current user.
    :type user: User
    :return: Images associated with the specified user.
    :rtype: List[Type[Image]] | None
    """
    user_w_images = db.query(Image).all()
    return user_w_images
