from typing import Type
from fastapi import HTTPException, status

from sqlalchemy.orm import Session, joinedload
from src.database.models import User, Image
from src.conf import messages, avatars
from src.schemas import (
    UserModel,
    ChangeRoleRequest,
    CommentByUser,
    ImageProfile,
    UserProfile,
    UserInfoProfile,
    UserProfileMe,
    ProfileMe,
    AllUsersProfiles,
)
from src.repository import ratings as repository_rating
from src.services.auth import auth_service


async def get_users(db: Session) -> list[Type[User]]:
    """
    Get all users from the database.

    :param db: Database session.
    :type db: Session
    :return: List of users.
    :rtype: list[Type[User]]
    """
    users = db.query(User).all()
    return users


async def get_user_by_email(email: str, db: Session) -> User | None:
    """
    Get a user by email from the database.

    :param email: User's email.
    :type email: str
    :param db: Database session.
    :type db: Session
    :return: User if found, else None.
    :rtype: User | None
    """
    return db.query(User).filter_by(email=email).first()


async def get_user_by_id(user_id: int, db: Session) -> User | None:
    """
    Get a user by ID from the database.

    :param user_id: User's ID.
    :type user_id: int
    :param db: Database session.
    :type db: Session
    :return: User if found, else None.
    :rtype: User | None
    """
    return db.query(User).filter_by(id=user_id).first()


async def get_user_by_name(user_name: str, db: Session) -> User | None:
    """
    Get a user by name from the database.

    :param user_name: User's name.
    :type user_name: str
    :param db: Database session.
    :type db: Session
    :return: User if found, else None.
    :rtype: User | None
    """
    return db.query(User).filter_by(name=user_name).first()


async def create_user(body: UserModel, db: Session) -> User:
    """
    Create a new user in the database.

    :param body: User model containing user information.
    :type body: UserModel
    :param db: Database session.
    :type db: Session
    :return: Newly created user.
    :rtype: User
    """
    users = await get_users(db)

    new_user = User(
        name=body.name, email=body.email, sex=body.sex, password=body.password
    )
    new_user.avatar = (
        avatars.FEMALE_AVATAR if body.sex == "female" else avatars.MALE_AVATAR
    )
    if not users:
        new_user.role = "admin"
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, refresh_token, db: Session) -> None:
    """
    Update the refresh token for a user in the database.

    :param user: User for whom the token is updated.
    :type user: User
    :param refresh_token: New refresh token.
    :type refresh_token: str
    :param db: Database session.
    :type db: Session
    """
    user.refresh_token = refresh_token
    db.commit()


async def update_avatar(email, url: str, db: Session) -> User:
    """
    Update the avatar URL for a user in the database.

    :param email: User's email.
    :type email: str
    :param url: New avatar URL.
    :type url: str
    :param db: Database session.
    :type db: Session
    :return: Updated user.
    :rtype: User
    """
    user = await get_user_by_email(email, db)

    user.avatar = url
    db.commit()
    db.refresh(user)
    return user


async def ban_user(email: str, db: Session) -> User | None:
    """
    Ban a user by setting the 'forbidden' flag in the database.

    :param email: User's email.
    :type email: str
    :param db: Database session.
    :type db: Session
    :return: Banned user if found, else None.
    :rtype: User | None
    """
    user = await get_user_by_email(email, db)
    if user:
        user.forbidden = True
        db.commit()
        db.refresh(user)
    return user


async def unban_user(email: str, db: Session) -> User | None:
    """
    Unban a user by resetting the 'forbidden' flag in the database.

    :param email: User's email.
    :type email: str
    :param db: Database session.
    :type db: Session
    :return: Unbanned user if found, else None.
    :rtype: User | None
    """
    user = await get_user_by_email(email, db)
    if user:
        user.forbidden = False
        db.commit()
        db.refresh(user)
    return user


async def change_user_role(body: ChangeRoleRequest, db: Session) -> User | None:
    """
    Change the role of a user in the database.

    :param body: Request body containing email and new role.
    :type body: ChangeRoleRequest
    :param db: Database session.
    :type db: Session
    :return: User with updated role if found, else None.
    :rtype: User | None
    """
    user = await get_user_by_email(body.email, db)
    if user:
        user.role = body.role
        db.commit()
        db.refresh(user)
    return user


async def get_user_profile_by_name(user_name: str, db: Session, current_user: User):
    """
    Get the profile of a user by name, including their images.

    :param user_name: User's name.
    :type user_name: str
    :param db: Database session.
    :type db: Session
    :param current_user: Current user making the request.
    :type current_user: User
    :return: User profile including images.
    :rtype: UserProfile
    """
    user = await get_user_by_name(user_name, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=messages.USER_NOT_FOUND
        )
    user_data = UserInfoProfile(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        avatar=user.avatar,
        forbidden=user.forbidden,
        created_at=user.created_at,
    )
    images = await get_user_images_by_id(user.id, db, current_user)
    user_profile = UserProfile(user=user_data, images=images)
    return user_profile


async def get_user_profile_me(db: Session, current_user: User):
    """
    Get the profile of the current user, including their images.

    :param db: Database session.
    :type db: Session
    :param current_user: Current user making the request.
    :type current_user: User
    :return: User profile including images.
    :rtype: ProfileMe
    """
    user = UserProfileMe(
        name=current_user.name,
        email=current_user.email,
        avatar=current_user.avatar,
    )
    images = await get_user_images_by_id(current_user.id, db, current_user)
    user_profile = ProfileMe(user=user, images=images)
    return user_profile


async def get_user_images_by_id(user_id: int, db: Session, current_user: User):
    """
    Get the images of a user by ID.

    :param user_id: User's ID.
    :type user_id: int
    :param db: Database session.
    :type db: Session
    :param current_user: Current user making the request.
    :type current_user: User
    :return: List of images for the user.
    :rtype: List[ImageProfile]
    """
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
            new_comment = CommentByUser(
                user_id=comment.user_id, comment=comment.comment
            )
            comments.append(new_comment)
        for tag in image.tags:
            new_tag = tag.tag_name
            tags.append(new_tag)
        rating = await repository_rating.calculate_rating(image.id, db, current_user)
        new_rating = rating["average_rating"]
        new_image = ImageProfile(
            url=image.url,
            description=image.description,
            average_rating=new_rating,
            tags=tags,
            comments=comments,
        )
        images.append(new_image)
    return images


async def get_users_profiles(db: Session, current_user: User):
    """
    Get profiles of all users, including their images.

    :param db: Database session.
    :type db: Session
    :param current_user: Current user making the request.
    :type current_user: User
    :return: All user profiles including images.
    :rtype: AllUsersProfiles
    """
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
        images = await get_user_images_by_id(user.id, db, current_user)
        user_profile = UserProfile(user=user_data, images=images)
        users_profiles.append(user_profile)
    all_users_profiles = AllUsersProfiles(users=users_profiles)
    return all_users_profiles


async def update_user_profile_me_info(
    user_id: int,
    new_name: str | None,
    db: Session,
    current_user: User,
) -> User:
    """
    Update the profile information of the current user.

    :param user_id: User ID.
    :type user_id: int
    :param new_name: New name (if provided).
    :type new_name: str | None
    :param db: Database session.
    :type db: Session
    :param current_user: Current user making the request.
    :type current_user: User
    :return: Updated user profile.
    :rtype: User
    """
    user = await get_user_by_id(user_id, db)

    if user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=messages.NOT_AUTHORIZED_ACCESS
        )

    if new_name:
        user.name = new_name

    db.commit()
    db.refresh(user)
    return user


async def update_user_profile_me_credential(
    user_id: int,
    new_email: str | None,
    new_password: str | None,
    db: Session,
    current_user: User,
) -> User:
    """
    Update the credential information of the current user.

    :param user_id: User ID.
    :type user_id: int
    :param new_email: New email (if provided).
    :type new_email: str | None
    :param new_password: New password (if provided).
    :type new_password: str | None
    :param db: Database session.
    :type db: Session
    :param current_user: Current user making the request.
    :type current_user: User
    :return: Updated user profile.
    :rtype: User
    """
    user = await get_user_by_id(user_id, db)

    if user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=messages.NOT_AUTHORIZED_ACCESS
        )

    try:
        if new_email and new_email != user.email:
            existing_user = await get_user_by_email(new_email, db)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=messages.EMAIL_ALREADY_EXISTS,
                )
            user.email = new_email

        if new_password:
            user.password = auth_service.get_password_hash(new_password)

        db.commit()
        db.refresh(user)
        return user

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=str(e))
