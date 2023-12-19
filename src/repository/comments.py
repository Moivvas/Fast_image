from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.database.models import Comment, User
from src.schemas import CommentModel
from src.conf import messages


async def get_comments(db: Session):
    try:
        return db.query(Comment).all()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=messages.NO_COMMENTS)


async def get_comments_for_photo(image_id, db: Session):
    try:
        return db.query(Comment).filter_by(image_id=image_id).all()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=messages.NO_COMMENTS_ON_THIS_IMAGE)

async def get_comment_by_id(comment_id: int, db: Session):
    try:
        return db.query(Comment).filter_by(id=comment_id).first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=messages.NO_COMMENTS_ON_THIS_ID)

async def create_comment(body: CommentModel, current_user: User, db: Session):
    try:
        comment = Comment(**body.model_dump(), user_id=current_user.id)
        db.add(comment)
        db.commit()
        return comment
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=messages.ERROR_CREATING_COMMENT)

async def update_comment(body: CommentModel, db: Session, current_user: User):
    comment = await get_comment_by_id(body.comment_id, db)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,  detail=messages.NO_COMMENT)
    if comment.user_id == current_user.id:
        comment.comment = body.comment
        db.commit()
        return comment
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.CANT_UPDATE_COMMENT)


async def remove_comment(comment_id, db: Session):
    comment = await get_comment_by_id(comment_id, db)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,  detail=messages.NO_COMMENT)
    if comment:
        db.delete(comment)
        db.commit()
    return comment
