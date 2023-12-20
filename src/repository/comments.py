from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.database.models import Comment, User
from src.schemas import CommentModel
from src.conf import messages


async def get_comments(db: Session):
    """
    Retrieve all comments from the database.

    This function retrieves all comments from the database.

    :param db: Database session.
    :type db: Session
    :return: List of comments.
    :rtype: List[Comment]
    """
    try:
        return db.query(Comment).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=messages.NO_COMMENTS,
        )


async def get_comments_for_photo(image_id, db: Session):
    """
    Retrieve comments for a specific image from the database.

    This function retrieves comments associated with a specific image from the database.

    :param image_id: ID of the image.
    :type image_id: int
    :param db: Database session.
    :type db: Session
    :return: List of comments for the specified image.
    :rtype: List[Comment]
    """
    try:
        return db.query(Comment).filter_by(image_id=image_id).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=messages.NO_COMMENTS_ON_THIS_IMAGE,
        )


async def get_comment_by_id(comment_id: int, db: Session):
    """
    Retrieve a comment by its ID from the database.

    This function retrieves a comment based on its unique identifier from the database.

    :param comment_id: ID of the comment.
    :type comment_id: int
    :param db: Database session.
    :type db: Session
    :return: Comment object or None if not found.
    :rtype: Comment | None
    """
    try:
        return db.query(Comment).filter_by(id=comment_id).first()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=messages.NO_COMMENTS_ON_THIS_ID,
        )


async def create_comment(body: CommentModel, current_user: User, db: Session):
    """
    Create a new comment in the database.

    This function creates a new comment in the database based on the provided data.

    :param body: Comment data model.
    :type body: CommentModel
    :param current_user: User creating the comment.
    :type current_user: User
    :param db: Database session.
    :type db: Session
    :return: Created Comment object.
    :rtype: Comment
    """
    try:
        comment = Comment(**body.model_dump(), user_id=current_user.id)
        db.add(comment)
        db.commit()
        return comment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=messages.ERROR_CREATING_COMMENT,
        )


async def update_comment(body: CommentModel, db: Session, current_user: User):
    """
    Update a comment in the database.

    This function updates an existing comment in the database based on the provided data.

    :param body: Comment data model.
    :type body: CommentModel
    :param db: Database session.
    :type db: Session
    :param current_user: User updating the comment.
    :type current_user: User
    :return: Updated Comment object.
    :rtype: Comment
    """
    comment = await get_comment_by_id(body.comment_id, db)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.NO_COMMENT
        )
    if comment.user_id == current_user.id:
        comment.comment = body.comment
        db.commit()
        return comment
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=messages.CANT_UPDATE_COMMENT
        )


async def remove_comment(comment_id, db: Session):
    """
    Remove a comment from the database.

    This function removes an existing comment from the database based on the provided comment_id.

    :param comment_id: ID of the comment to be removed.
    :type comment_id: int
    :param db: Database session.
    :type db: Session
    :return: Removed Comment object.
    :rtype: Comment
    """
    comment = await get_comment_by_id(comment_id, db)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.NO_COMMENT
        )
    if comment:
        db.delete(comment)
        db.commit()
    return comment
