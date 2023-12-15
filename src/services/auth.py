import pickle
import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Optional


from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from src.conf import messages
from src.database.db import get_db
from src.repository import users as repository_users
from src.conf.config import settings


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/project/auth/login")
    redis_db = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        return self.pwd_context.hash(password)

    async def create_access_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=60)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"}
        )
        encoded_access_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_access_token

    async def create_refresh_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):

        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"}
        )
        encoded_refresh_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):

        try:
            payload = jwt.decode(
                refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            if payload["scope"] == "refresh_token":
                email = payload["sub"]
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=messages.INVALID_SCOPE_FOR_TOKEN,
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=messages.COULD_NOT_VALIDATE_CREDENTIALS,
            )

    async def ban_token(self, access_token):
        await self.redis_db.setex(access_token, 3600, access_token)

    async def banned_token(self, access_token):
        token = await self.redis_db.get(access_token)
        if token:
            return True
        return False

    async def get_current_user(
        self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
    ):

        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=messages.COULD_NOT_VALIDATE_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )

        banned_token = await self.banned_token(token)
        if banned_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.USER_IS_NOT_AUTHORIZED)
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == "access_token":
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = await repository_users.get_user_by_email(email, db)
        if user is None:
            raise credentials_exception

        return user


auth_service = Auth()
