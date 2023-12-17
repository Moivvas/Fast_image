from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.models import User
from src.database.db import get_db

from src.services.auth import auth_service
from src.conf import messages
from src.schemas import ImageAddResponse, ImageChangeSizeModel, ImageTransformModel

from src.repository import cloud_image as repository_image
from src.services.roles import all_roles, only_admin, admin_and_moder

router = APIRouter(prefix="/formats", tags=["Image formats"])


@router.post('/change_size', response_model=ImageAddResponse, status_code=status.HTTP_201_CREATED)
async def change_size_image(body: ImageChangeSizeModel, 
                            db: Session = Depends(get_db), 
                            current_user: User = Depends(auth_service.get_current_user)):
    
    image= await repository_image.change_size_image(body=body, db=db, user = current_user)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND)
    return image

@router.post('/fade_edges', response_model=ImageAddResponse, status_code=status.HTTP_201_CREATED)
async def fade_edges_image(body: ImageTransformModel, 
                            db: Session = Depends(get_db), 
                            current_user: User = Depends(auth_service.get_current_user)):
   
    image = await repository_image.fade_edges_image(body=body, db=db, user = current_user)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND)
    return image


@router.post('/black_white', response_model=ImageAddResponse, status_code=status.HTTP_201_CREATED)
async def black_white_image(body: ImageTransformModel, 
                            db: Session = Depends(get_db), 
                            current_user: User = Depends(auth_service.get_current_user)):
   
    image = await repository_image.black_white_image(body=body, db=db, user = current_user)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND)
    return image

