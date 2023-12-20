from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Path
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from src.services.auth import auth_service

from src.database.db import get_db
from src.database.models import Image, User
from src.services.roles import admin_and_moder, only_admin

from src.schemas import (
    CommentResponse,
    CommentModel,
    CommentDeleteResponse,
    CommentModelUpdate,
)
from src.repository import comments as repository_comments
from src.conf import messages

router = APIRouter(prefix="/comment", tags=["comment"])

security = HTTPBearer()


@router.get(
    "/all", response_model=List[CommentResponse], dependencies=[Depends(only_admin)]
)
async def get_comments(db: Session = Depends(get_db)):
    """
    Retrieve all comments.

    This endpoint allows only administrators to retrieve all comments.

    :param db: Database session.
    :type db: Session
    :return: List of comments.
    :rtype: List[CommentResponse]
    """
    comments = await repository_comments.get_comments(db)
    return comments


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    body: CommentModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Create a new comment.

    This endpoint allows a user to create a new comment for a specific image.

    :param body: The data for the comment.
    :type body: CommentModel
    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: The created comment.
    :rtype: CommentResponse
    """
    image = db.query(Image).filter_by(id=body.image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.NO_IMAGE
        )
    comment = await repository_comments.create_comment(body, current_user, db)
    return comment


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment_by_id(
    comment_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Retrieve a comment by its ID.

    This endpoint allows a user to retrieve a comment by providing its ID.

    :param comment_id: The ID of the comment to retrieve.
    :type comment_id: int
    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: The retrieved comment.
    :rtype: CommentResponse
    """
    comment = await repository_comments.get_comment_by_id(comment_id, db)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.NO_COMMENT
        )
    return comment


@router.get("/image/{image_id}", response_model=List[CommentResponse])
async def get_comment_by_image_id(
    image_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Retrieve comments for a specific image by its ID.

    This endpoint allows a user to retrieve comments associated with a specific image
    by providing the image's ID.

    :param image_id: The ID of the image for which to retrieve comments.
    :type image_id: int
    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: List of comments for the specified image.
    :rtype: List[CommentResponse]
    """
    comment = await repository_comments.get_comments_for_photo(image_id, db)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.NO_IMAGE
        )
    return comment


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    body: CommentModelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    comment = await repository_comments.update_comment(body, db, current_user)
    return comment


@router.delete(
    "/{comment_id}",
    response_model=CommentDeleteResponse,
    dependencies=[Depends(admin_and_moder)],
)
async def remove_comment(comment_id: int = Path(ge=1), db: Session = Depends(get_db)):
    """
    Update a comment by its ID.

    This endpoint allows a user to update a comment by providing the comment's ID.

    :param comment_id: The ID of the comment to update.
    :type comment_id: int
    :param body: The updated data for the comment.
    :type body: CommentModelUpdate
    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: Updated comment.
    :rtype: CommentResponse
    """
    comment = await repository_comments.remove_comment(comment_id, db)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.NO_COMMENT
        )
    return comment
