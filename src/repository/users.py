from typing import Type

from sqlalchemy.orm import Session
from src.database.models import User
from src.schemas import UserModel, ChangeRoleRequest


async def get_users(db: Session) -> list[Type[User]]:
    users = db.query(User).all()
    return users


async def get_user_by_email(email: str, db: Session) -> User | None:
    return db.query(User).filter_by(email=email).first()


async def create_user(body: UserModel, db: Session) -> User:
    users = await get_users(db)
    female_avatar_url = 'https://res.cloudinary.com/danwilik1/image/upload/v1702548197/fast_image/default_avatar/female_avatar_n0zwxx.jpg'
    male_avatar_url = 'https://res.cloudinary.com/danwilik1/image/upload/v1702548197/fast_image/default_avatar/male_avatar_qjxr9h.jpg'
    
    new_user = User(
        name=body.name,
        email=body.email,
        sex=body.sex,
        avatar=female_avatar_url if body.sex == "female" else male_avatar_url
    )
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
