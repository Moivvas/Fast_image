from typing import Union

from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException
from sqlalchemy.orm import Session

from src.conf import messages
from src.database.models import User
from src.database.db import get_db

from src.services.auth import auth_service
from src.services.cloud_avatar import CloudAvatar

from src.schemas import (
    UserResponse,
    ChangeRoleRequest,
    UserProfile,
    ProfileMe,
    AllUsersProfiles,
)

from src.repository import users as repository_users
from src.services.roles import admin_and_moder, only_admin, all_roles

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=ProfileMe, dependencies=[Depends(all_roles)])
async def read_users_me(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Retrieve the profile information of the authenticated user.

    This endpoint returns the profile information of the currently authenticated user.

    :param current_user: The current authenticated user.
    :type current_user: User
    :param db: Database session.
    :type db: Session
    :return: The profile information of the authenticated user.
    :rtype: ProfileMe
    """
    user_profile = await repository_users.get_user_profile_me(db, current_user)
    return user_profile


@router.patch("/avatar", response_model=UserResponse, dependencies=[Depends(all_roles)])
async def update_avatar_user(
    file: UploadFile = File(),
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the avatar of the authenticated user.

    This endpoint allows the authenticated user to update their avatar.

    :param file: The avatar image file to upload.
    :type file: UploadFile
    :param current_user: The current authenticated user.
    :type current_user: User
    :param db: Database session.
    :type db: Session
    :return: The updated user information.
    :rtype: UserResponse
    """
    public_id = CloudAvatar.generate_name_avatar(current_user.email)
    r = CloudAvatar.upload_avatar(file.file, public_id)
    src_url = CloudAvatar.get_url_for_avatar(public_id, r)
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    return user


@router.get(
    "/", response_model=AllUsersProfiles, dependencies=[Depends(admin_and_moder)]
)
async def get_users_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
) -> AllUsersProfiles:
    """
    Get profiles of all users.

    This endpoint retrieves profiles of all users in the system. It requires
    admin or moderator privileges.

    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: Profiles of all users.
    :rtype: AllUsersProfiles
    """
    users = await repository_users.get_users_profiles(db, current_user)
    return users


@router.get(
    "/user/{email}",
    response_model=UserResponse,
    dependencies=[Depends(admin_and_moder)],
)
async def get_user(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
) -> User:
    """
    Get user by email.

    This endpoint retrieves a user by their email address. It requires
    admin or moderator privileges.

    :param email: The email address of the user to retrieve.
    :type email: str
    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: User information.
    :rtype: UserResponse
    """
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND
        )
    return user


@router.patch("/user", response_model=UserResponse, dependencies=[Depends(only_admin)])
async def change_user_role(
    body: ChangeRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
) -> User:
    """
    Change user role.

    This endpoint allows an admin to change the role of a user.

    :param body: Request body containing user email and new role.
    :type body: ChangeRoleRequest
    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: User information with updated role.
    :rtype: UserResponse
    """
    user = await repository_users.change_user_role(body, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND
        )
    return user


@router.get(
    "/{user_name}", response_model=UserProfile, dependencies=[Depends(all_roles)]
)
async def get_user_profile(
    user_name,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Get user profile by username.

    This endpoint retrieves the profile information of a user by their username.

    :param user_name: Username of the user.
    :type user_name: str
    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: User profile information.
    :rtype: UserProfile
    """
    user_profile = await repository_users.get_user_profile_by_name(
        user_name, db, current_user
    )
    return user_profile


@router.patch(
    "/me/info", response_model=UserResponse, dependencies=[Depends(all_roles)]
)
async def update_user_info(
    new_name: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Update user information.

    This endpoint allows the authenticated user to update their profile information.

    :param new_name: New name for the user.
    :type new_name: str | None
    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: Updated user information.
    :rtype: UserResponse
    """
    updated_user = await repository_users.update_user_profile_me_info(
        user_id=current_user.id,
        new_name=new_name,
        db=db,
        current_user=current_user,
    )
    return updated_user


@router.patch(
    "/me/credential", response_model=UserResponse, dependencies=[Depends(all_roles)]
)
async def update_user_credential(
    new_email: Union[str, None] = None,
    new_password: Union[str, None] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Update user credentials.

    This endpoint allows the authenticated user to update their email or password.

    :param new_email: New email for the user.
    :type new_email: Union[str, None]
    :param new_password: New password for the user.
    :type new_password: Union[str, None]
    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: Updated user information.
    :rtype: UserResponse
    """
    updated_user = await repository_users.update_user_profile_me_credential(
        user_id=current_user.id,
        new_email=new_email,
        new_password=new_password,
        db=db,
        current_user=current_user,
    )
    return updated_user


@router.patch(
    "/ban_user", response_model=UserResponse, dependencies=[Depends(only_admin)]
)
async def ban_user(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Ban a user.

    This endpoint allows an administrator to ban a user by email.

    :param email: Email of the user to be banned.
    :type email: str
    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user (admin).
    :type current_user: User
    :return: Banned user information.
    :rtype: UserResponse
    """
    forbidden_user = await repository_users.ban_user(email, db)
    if not forbidden_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND
        )
    return forbidden_user


@router.patch(
    "/unban_user", response_model=UserResponse, dependencies=[Depends(only_admin)]
)
async def unban_user(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Unban a user.

    This endpoint allows an administrator to unban a user by email.

    :param email: Email of the user to be unbanned.
    :type email: str
    :param db: Database session.
    :type db: Session
    :param current_user: The current authenticated user (admin).
    :type current_user: User
    :return: Unbanned user information.
    :rtype: UserResponse
    """
    forbidden_user = await repository_users.unban_user(email, db)
    if not forbidden_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND
        )
    return forbidden_user
