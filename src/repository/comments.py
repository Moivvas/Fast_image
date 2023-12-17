from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.database.models import Comment, User
from src.schemas import CommentModel
from src.conf import messages


async def get_comments(db: Session):
    return db.query(Comment).all()


async def get_comments_for_photo(image_id, db: Session):
    return db.query(Comment).filter_by(image_id=image_id).all()


async def get_comment_by_id(comment_id: int, db: Session):
    return db.query(Comment).filter_by(id=comment_id).first()


async def create_comment(body: CommentModel, current_user: User, db: Session):
    comment = Comment(**body.model_dump(), user_id=current_user.id)
    db.add(comment)
    db.commit()
    return comment


async def update_comment(body: CommentModel, db: Session, current_user: User):
    comment = await get_comment_by_id(body.comment_id, db)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,  detail=messages.NO_COMMENT)
    if comment.user_id == current_user.id:
        comment.comment = body.comment
        db.commit()
        return comment
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.CANT_CHANGE_COMMENT)

async def remove_comment(comment_id, db: Session):
    comment = await get_comment_by_id(comment_id, db)
    if comment:
        db.delete(comment)
        db.commit()
    return comment