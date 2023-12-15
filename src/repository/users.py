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
    AllUsersProfiles,
)


async def get_users(db: Session) -> list[Type[User]]:
    users = db.query(User).all()
    return users


async def get_user_by_email(email: str, db: Session) -> User | None:
    return db.query(User).filter_by(email=email).first()


async def get_user_by_id(user_id: int, db: Session) -> User | None:
    return db.query(User).filter_by(id=user_id).first()


async def get_user_by_name(user_name: str, db: Session) -> User | None:
    return db.query(User).filter_by(name=user_name).first()


async def create_user(body: UserModel, db: Session) -> User:
    users = await get_users(db)
    female_avatar_url = 'https://res.cloudinary.com/danwilik1/image/upload/v1702548197/fast_image/default_avatar/female_avatar_n0zwxx.jpg'
    male_avatar_url = 'https://res.cloudinary.com/danwilik1/image/upload/v1702548197/fast_image/default_avatar/male_avatar_qjxr9h.jpg'
    
    new_user = User(
        name=body.name,
        email=body.email,
        sex=body.sex,
        password=body.password
    )
    new_user.avatar = female_avatar_url if body.sex == "female" else male_avatar_url
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


async def get_user_profile_by_name(user_name: str, db: Session, current_user: User):

    user = await get_user_by_name(user_name, db)
    user_data = UserInfoProfile(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        avatar=user.avatar,
        forbidden=user.forbidden,
        created_at=user.created_at
    )
    images = await get_user_images_by_id(user.id, db)
    user_profile = UserProfile(user=user_data, images=images)
    return user_profile


async def get_user_profile_me(db: Session, current_user: User):
    user = UserProfileMe(
        name=current_user.name,
        email=current_user.email,
        avatar=current_user.avatar,
    )
    images = await get_user_images_by_id(current_user.id, db)
    user_profile = ProfileMe(user=user, images=images)
    return user_profile


async def get_user_images_by_id(user_id: int, db: Session):
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
        new_image = ImageProfile(url=image.url, description=image.description, tags=tags, comments=comments)
        images.append(new_image)
    return images


async def get_users_profiles(db: Session, current_user: User):
    users = await get_users(db)
    users_profiles = []
    for user in users:
        user_data = UserInfoProfile(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            avatar=user.avatar,
            forbidden=user.forbidden,
            created_at=user.created_at,
        )
        images = await get_user_images_by_id(user.id, db)
        user_profile = UserProfile(user=user_data, images=images)
        users_profiles.append(user_profile)
    all_users_profiles = AllUsersProfiles(users=users_profiles)
    return all_users_profiles
