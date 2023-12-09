from fastapi import APIRouter, Depends

from src.database.models import User

from src.services.auth import auth_service

from src.schemas import UserResponse


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    return current_user

