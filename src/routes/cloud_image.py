from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from src.database.models import User
from src.database.db import get_db

from src.services.auth import auth_service
from src.services.cloud_images_service import CloudImage
from src.conf import messages
from src.schemas import ImageDeleteResponse, ImageUpdateResponse, ImageURLResponse, ImageModel

from src.repository import cloud_image as repository_image
from src.services.roles import all_roles, only_admin, admin_and_moder


router = APIRouter(prefix="/cloud_image", tags=["cloud_image"])


@router.post("/image", response_model=ImageModel, status_code=status.HTTP_201_CREATED)
async def upload_image(
    description: str = None,
    file: UploadFile = File(),
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    public_id = CloudImage.generate_name_image(current_user.email)
    upload_file = CloudImage.upload_image(file.file, public_id)
    src_url = CloudImage.get_url_for_image(public_id, upload_file)
    image = await repository_image.add_image(
        db, src_url, public_id, current_user, description
    )
    return image


@router.delete(
    "/{id}", response_model=ImageDeleteResponse, dependencies=[Depends(all_roles)]
)
async def delete_image(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    image = await repository_image.delete_image(db, id)
    return image


@router.put(
    "/{id}", response_model=ImageUpdateResponse, dependencies=[Depends(all_roles)]
)
async def update_description(
    id: int,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    image = await repository_image.update_desc(db, id, description)
    if not image:
        raise HTTPException(status_code=404, detail=messages.IMAGE_NOT_FOUND)
    return image


@router.get(
    "/{image_id}", response_model=ImageURLResponse, dependencies=[Depends(all_roles)]
)
async def get_image_url(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    image = repository_image.get_image_by_id(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail=messages.IMAGE_NOT_FOUND)
    return {"url": image.url}
