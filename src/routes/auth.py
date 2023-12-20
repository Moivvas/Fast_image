from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Security,
)
from fastapi.responses import JSONResponse
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import UserModel, UserResponse, TokenModel
from src.repository import users as repository_users
from src.conf import messages
from src.services.auth import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(body: UserModel, db: Session = Depends(get_db)):
    """
    Register a new user.

    This endpoint allows creating a new user in the system.

    :param body: Data of the new user.
    :type body: UserModel
    :param db: Database session.
    :type db: Session, optional
    :return: Information about the new user.
    :rtype: UserResponse
    :raises HTTPException 409: If a user with the specified email already exists.
    :raises HTTPException 201: Upon successful user registration.
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=messages.ACCOUNT_ALREADY_EXISTS
        )
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    return new_user


@router.post("/login", response_model=TokenModel)
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Authenticate a user and generate access and refresh tokens.

    This endpoint allows users to log in and receive access and refresh tokens for authentication.

    :param body: Request form data containing the username and password.
    :type body: OAuth2PasswordRequestForm
    :param db: Database session.
    :type db: Session, optional
    :return: Access and refresh tokens.
    :rtype: TokenModel
    :raises HTTPException 401: If the email or password is invalid.
    :raises HTTPException 403: If the user is banned.
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_EMAIL
        )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_PASSWORD
        )
    if user.forbidden:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=messages.BANNED
        )
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(token: str = Depends(auth_service.oauth2_scheme)) -> JSONResponse:
    """
    Log out a user and invalidate the provided token.

    This endpoint allows users to log out and invalidates the provided access token.

    :param token: Access token to be invalidated.
    :type token: str
    :return: JSON response indicating successful logout.
    :rtype: JSONResponse
    """
    await auth_service.ban_token(token)
    return JSONResponse(content={"message": "Successfully logged out"})


@router.get("/refresh_token", response_model=TokenModel)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
):
    """
    Refresh the access token using a valid refresh token.

    This endpoint allows users to obtain a new access token using a valid refresh token.

    :param credentials: HTTP Authorization credentials containing the refresh token.
    :type credentials: HTTPAuthorizationCredentials
    :param db: Database session.
    :type db: Session
    :return: New access and refresh tokens.
    :rtype: TokenModel
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=messages.INVALID_REFRESH_TOKEN,
        )
    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
