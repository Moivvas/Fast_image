from pydantic import BaseModel, EmailStr, Field, field_validator
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
    avatar: str | None
    forbidden: bool


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TagModel(BaseModel):
    tag_name: str


class TagResponse(TagModel):
    model_config = SettingsConfigDict(from_attributes=True)
    id: int
    tag_name: str


class ChangeRoleRequest(BaseModel):
    model_config = SettingsConfigDict(from_attributes=True)
    email: EmailStr
    role: str

    @field_validator("role")
    def validate_role(cls, v):
        allowed_roles = {"admin", "user", "moderator"}
        if v not in allowed_roles:
            raise ValueError(
                f"Invalid role. Allowed roles are: {', '.join(allowed_roles)}"
            )
        return v

class ImageModel(BaseModel):
    id: int
    url: str
    public_id: str
    user_id: int
    
class ImageAddResponse(BaseModel):
    image: ImageModel

class ImageDeleteResponse(BaseModel):
    image: ImageModel
