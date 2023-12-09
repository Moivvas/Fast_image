from typing import Type

from sqlalchemy.orm import Session
from src.database.models import User
from src.schemas import UserModel


async def get_users(db: Session) -> list[Type[User]]:

    users = db.query(User).all()
    return users


async def get_user_by_email(email: str, db: Session) -> User | None:

    return db.query(User).filter_by(email=email).first()


async def create_user(body: UserModel, db: Session) -> User:
    users = await get_users(db)
    new_user = User(**body.model_dump())
    if not users:
        new_user.role = "admin"
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, refresh_token, db: Session) -> None:
    user.refresh_token = refresh_token
    db.commit()





