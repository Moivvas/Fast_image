from pydantic import BaseModel, EmailStr, Field
from datetime import date

from pydantic_settings import SettingsConfigDict

from src.database.models import Role


class UserModel(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6, max_length=16)


class UserResponse(BaseModel):
    model_config = SettingsConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    role: Role
    avatar: str


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

