from typing import Type

from sqlalchemy.orm import Session, joinedload
from src.database.models import User, Image
from src.schemas import (
    UserModel,
    ChangeRoleRequest,
    UserResponse,
    CommentByUser,
    ImageProfile,
    UserProfile,
    UserInfoProfile,
    UserProfileMe,
    ProfileMe,
)


async def get_users(db: Session) -> list[Type[User]]:
    users = db.query(User).all()
    return users


async def get_user_by_email(email: str, db: Session) -> User | None:
    return db.query(User).filter_by(email=email).first()


async def get_user_by_id(user_id: int, db) -> User | None:
    return db.query(User).filter_by(id=user_id).first()


async def create_user(body: UserModel, db: Session) -> User:
    users = await get_users(db)
    new_user = User(**body.model_dump(), avatar="avatar_url")
    if not users:
        new_user.role = "admin"
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, refresh_token, db: Session) -> None:
    user.refresh_token = refresh_token
    db.commit()


async def update_avatar(email, url: str, db: Session) -> User:
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user


async def ban_user(email: str, db: Session) -> User | None:
    user = await get_user_by_email(email, db)
    if user:
        user.forbidden = True
        db.commit()
        db.refresh(user)
    return user


async def unban_user(email: str, db: Session) -> User | None:
    user = await get_user_by_email(email, db)
    if user:
        user.forbidden = False
        db.commit()
        db.refresh(user)
    return user


async def change_user_role(body: ChangeRoleRequest, db: Session) -> User | None:
    user = await get_user_by_email(body.email, db)
    if user:
        user.role = body.role
        db.commit()
        db.refresh(user)
    return user


async def get_user_profile_by_id(user_id: int, db: Session, current_user: User):

    user = await get_user_by_id(user_id, db)
    user = UserInfoProfile(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        avatar=user.avatar,
        forbidden=user.forbidden,
        created_at=user.created_at
    )
    user_photos = (
        db.query(Image)
        .filter_by(user_id=user_id)
        .options(joinedload(Image.tags), joinedload(Image.comments))
        .all()
    )
    images = []
    for image in user_photos:
        tags = []
        comments = []
        for comment in image.comments:
            new_comment = CommentByUser(user_id=comment.user_id, comment=comment.comment)
            comments.append(new_comment)
        for tag in image.tags:
            new_tag = tag.tag_name
            tags.append(new_tag)
        new_image = ImageProfile(url=image.url, tags=tags, comments=comments)
        images.append(new_image)
    user_profile = UserProfile(user=user, images=images)
    return user_profile


async def get_user_profile_me(db: Session, current_user: User):
    user = UserProfileMe(
        name=current_user.name,
        email=current_user.email,
        avatar=current_user.avatar,
    )
    user_photos = (
        db.query(Image)
        .filter_by(user_id=current_user.id)
        .options(joinedload(Image.tags), joinedload(Image.comments))
        .all()
    )
    images = []
    for image in user_photos:
        tags = []
        comments = []
        for comment in image.comments:
            new_comment = CommentByUser(user_id=comment.user_id, comment=comment.comment)
            comments.append(new_comment)
        for tag in image.tags:
            new_tag = tag.tag_name
            tags.append(new_tag)
        new_image = ImageProfile(url=image.url, tags=tags, comments=comments)
        images.append(new_image)
    user_profile = ProfileMe(user=user, images=images)
    return user_profile

