from typing import List

from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime

from fastapi import Path
from pydantic_settings import SettingsConfigDict

from src.database.models import Role


class UserModel(BaseModel):
    name: str = Field(min_length=2, max_length=20)
    email: EmailStr
    sex: str
    password: str = Field(min_length=6, max_length=16)

    @field_validator("sex")
    def validate_role(cls, v):
        allowed_sex = {"male", "female"}
        if v not in allowed_sex:
            raise ValueError(
                f"Invalid sex. Allowed sex are: {', '.join(allowed_sex)}"
            )
        return v

class UserResponse(BaseModel):
    model_config = SettingsConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    sex: str
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
    detail: str = "Image has been added"


class ImageDeleteResponse(BaseModel):
    detail: str = "Image has been deleted"


class ImageUpdateResponse(BaseModel):
    id: int
    description: str
    detail: str = "Image has been updated"


class ImageURLResponse(BaseModel):
    url: str
    

class ImageChangeSizeModel(BaseModel):
    id: int
    width: int = 200


class ImageTransformModel(BaseModel):
    id: int


class ImageQRResponse(BaseModel):
    image_id: int
    qr_code_url: str


class AddTag(BaseModel):

    detail: str = "Image tags has been updated"
   

class AverageRatingResponse(BaseModel):
    average_rating: float


class RatingResponse(BaseModel):
    average_rating: float | None
    image_url: str


class RatingBase(BaseModel):
    rate: int


class RatingModel(RatingBase):
    model_config = SettingsConfigDict(from_attributes=True)
    id: int
    rate: int
    image_id: int
    user_id: int


class AverageRatingResponse(BaseModel):
    average_rating: float



class CommentByUser(BaseModel):
    user_id: int
    comment: str


class ImageProfile(BaseModel):
    url: str
    description: str | None
    average_rating: float | None
    tags: List[str] | None
    comments: List[CommentByUser] | None


class UserInfoProfile(BaseModel):
    model_config = SettingsConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: Role
    avatar: str | None
    forbidden: bool
    created_at: datetime


class UserProfileMe(BaseModel):
    model_config = SettingsConfigDict(from_attributes=True)
    name: str
    email: EmailStr
    avatar: str | None


class ProfileMe(BaseModel):
    model_config = SettingsConfigDict(from_attributes=True)
    user: UserProfileMe
    images: List[ImageProfile] | None


class UserProfile(BaseModel):
    model_config = SettingsConfigDict(from_attributes=True)
    user: UserInfoProfile
    images: List[ImageProfile] | None


class AllUsersProfiles(BaseModel):
    model_config = SettingsConfigDict(from_attributes=True)
    users: List[UserProfile]


class ImagesByFilter(BaseModel):
    images: List[ImageProfile]


class UserDb(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    role: Role = Field()


class CommentDeleteResponse(BaseModel):
    id: int = 1
    comment: str = 'My comment'


class CommentResponse(BaseModel):
    id: int = 1
    comment: str
    image_id: int = 1


class CommentModel(BaseModel):
    comment: str = Field(min_length=1, max_length=255)
    image_id: int = Field(1, gt=0)


class CommentModelUpdate(BaseModel):
    comment: str = Field(min_length=1, max_length=255)
    comment_id: int = Path(ge=1)
