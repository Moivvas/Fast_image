from fastapi import APIRouter, HTTPException, UploadFile, status, File, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.database.models import User
from src.database.db import get_db

from src.repository.cloud_image import get_all_images
from src.repository import cloud_image as repository_image

from src.services.auth import auth_service
from src.services.cloud_images_service import CloudImage
from src.services.roles import all_roles

from src.conf import messages

from src.schemas import (
    AddTag,
    ImageDeleteResponse,
    ImageUpdateResponse,
    ImageURLResponse,
    ImageModel,
    ImagesByFilter,
    ImageQRResponse,
    ImageTransformModel,
    ImageAddResponse,
    ImageChangeSizeModel,
)


router = APIRouter(prefix="/images", tags=["cloudinary_image"])


@router.post(
    "/",
    response_model=ImageModel,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(all_roles)],
)
async def upload_image(
    description: str = None,
    file: UploadFile = File(),
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload an image.

    This endpoint allows users with the necessary roles to upload an image.

    :param description: Image description.
    :type description: str
    :param file: Uploaded image file.
    :type file: UploadFile
    :param current_user: Currently authenticated user.
    :type current_user: User
    :param db: Database session.
    :type db: Session
    :return: Details of the uploaded image.
    :rtype: ImageModel
    """
    public_id = CloudImage.generate_name_image(current_user.email)
    upload_file = CloudImage.upload_image(file.file, public_id)
    src_url = CloudImage.get_url_for_image(public_id, upload_file)
    image = await repository_image.add_image(
        db, src_url, public_id, current_user, description
    )
    return image


@router.delete(
    "/{image_id}", response_model=ImageDeleteResponse, dependencies=[Depends(all_roles)]
)
async def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Delete an image.

    This endpoint allows users with the necessary roles to delete an image.

    :param image_id: ID of the image to be deleted.
    :type image_id: int
    :param db: Database session.
    :type db: Session
    :param current_user: Currently authenticated user.
    :type current_user: User
    :return: Details of the deleted image.
    :rtype: ImageDeleteResponse
    """
    try:
        image = await repository_image.get_image_by_id(db, image_id)
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
            )

        if current_user.role == "admin" or image.user_id == current_user.id:
            deleted_image = await repository_image.delete_image(db, image_id)
            return deleted_image
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=messages.NOT_AUTHORIZED_DELETE,
            )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.patch(
    "/{image_id}", response_model=ImageUpdateResponse, dependencies=[Depends(all_roles)]
)
async def update_description(
    image_id: int,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Update the description of an image.

    This endpoint allows users with the necessary roles to update the description of an image.

    :param image_id: ID of the image to be updated.
    :type image_id: int
    :param description: New description for the image.
    :type description: str
    :param db: Database session.
    :type db: Session
    :param current_user: Currently authenticated user.
    :type current_user: User
    :return: Details of the updated image.
    :rtype: ImageUpdateResponse
    """
    try:
        image = await repository_image.get_image_by_id(db, image_id)
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
            )

        if image.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=messages.NOT_ALLOWED
            )

        updated_image = await repository_image.update_desc(db, image_id, description)
        return updated_image
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/{image_id}", response_model=ImageURLResponse, dependencies=[Depends(all_roles)]
)
async def get_image_url(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Get the URL of an image.

    This endpoint allows users with the necessary roles to retrieve the URL of an image.

    :param image_id: ID of the image.
    :type image_id: int
    :param db: Database session.
    :type db: Session
    :param current_user: Currently authenticated user.
    :type current_user: User
    :return: URL of the image.
    :rtype: ImageURLResponse
    """
    try:
        image = await repository_image.get_image_by_id(db, image_id)
        if not image:
            raise HTTPException(status_code=404, detail=messages.IMAGE_NOT_FOUND)

        if current_user.role != "admin" and image.user_id != current_user.id:
            raise HTTPException(status_code=403, detail=messages.NOT_AUTHORIZED_ACCESS)

        return {"url": image.url}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=ImagesByFilter, dependencies=[Depends(all_roles)])
async def search_images(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
    keyword: str = Query(default=None),
    tag: str = Query(default=None),
    min_rating: int = Query(default=None),
):
    """
    Search for images based on specified filters.

    This endpoint allows users with the necessary roles to search for images based on various filters.

    :param db: Database session.
    :type db: Session
    :param current_user: Currently authenticated user.
    :type current_user: User
    :param keyword: Keyword to search for in image descriptions.
    :type keyword: str
    :param tag: Tag to filter images by.
    :type tag: str
    :param min_rating: Minimum rating for images.
    :type min_rating: int
    :return: Images matching the specified filters.
    :rtype: ImagesByFilter
    """
    try:
        all_images = await get_all_images(db, current_user, keyword, tag, min_rating)
        return all_images
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/", response_model=AddTag, dependencies=[Depends(all_roles)])
async def add_tag(
    image_id: int,
    tag: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Add a tag to an image.

    This endpoint allows users with the necessary roles to add a tag to a specific image.

    :param image_id: ID of the image.
    :type image_id: int
    :param tag: Tag to be added to the image.
    :type tag: str
    :param db: Database session.
    :type db: Session
    :param current_user: Currently authenticated user.
    :type current_user: User
    :return: Response indicating the success of the operation.
    :rtype: AddTag
    """
    response = await repository_image.add_tag(db, current_user, image_id, tag)

    return response


@router.post(
    "/create_qr", response_model=ImageQRResponse, status_code=status.HTTP_201_CREATED
)
async def create_qr(
    body: ImageTransformModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Create a QR code from the given image.

    This endpoint allows the user to create a QR code from an existing image.

    :param body: Data for creating the QR code.
    :type body: ImageTransformModel
    :param db: Database session.
    :type db: Session
    :param current_user: Currently authenticated user.
    :type current_user: User
    :return: Response containing information about the created QR code.
    :rtype: ImageQRResponse
    """
    image = await repository_image.create_qr(body=body, db=db, user=current_user)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
        )
    return image


@router.post(
    "/change_size", response_model=ImageAddResponse, status_code=status.HTTP_201_CREATED
)
async def change_size_image(
    body: ImageChangeSizeModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Change the size of an image.

    This endpoint allows the user to change the size of an existing image.

    :param body: Data for changing the size of the image.
    :type body: ImageChangeSizeModel
    :param db: Database session.
    :type db: Session
    :param current_user: Currently authenticated user.
    :type current_user: User
    :return: Response containing information about the modified image.
    :rtype: ImageAddResponse
    """
    image = await repository_image.change_size_image(
        body=body, db=db, user=current_user
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
        )
    return image


@router.post(
    "/fade_edges", response_model=ImageAddResponse, status_code=status.HTTP_201_CREATED
)
async def fade_edges_image(
    body: ImageTransformModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Apply fade edges transformation to an image.

    This endpoint allows the user to apply a fade edges transformation to an existing image.

    :param body: Data for the fade edges transformation.
    :type body: ImageTransformModel
    :param db: Database session.
    :type db: Session
    :param current_user: Currently authenticated user.
    :type current_user: User
    :return: Response containing information about the modified image.
    :rtype: ImageAddResponse
    """
    image = await repository_image.fade_edges_image(body=body, db=db, user=current_user)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
        )
    return image


@router.post(
    "/black_white", response_model=ImageAddResponse, status_code=status.HTTP_201_CREATED
)
async def black_white_image(
    body: ImageTransformModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Apply black and white transformation to an image.

    This endpoint allows the user to apply a black and white transformation to an existing image.

    :param body: Data for the black and white transformation.
    :type body: ImageTransformModel
    :param db: Database session.
    :type db: Session
    :param current_user: Currently authenticated user.
    :type current_user: User
    :return: Response containing information about the modified image.
    :rtype: ImageAddResponse
    """
    image = await repository_image.black_white_image(
        body=body, db=db, user=current_user
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
        )
    return image
