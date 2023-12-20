from fastapi import HTTPException, status
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from src.repository import ratings as repository_ratings

from src.database.models import Image, User, Tag, Rating

import qrcode
from io import BytesIO

from src.repository.tags import create_tag

from src.services.cloud_images_service import CloudImage, image_cloudinary

from src.schemas import (
    ImageChangeSizeModel,
    ImageAddResponse,
    ImageModel,
    ImageTransformModel,
    ImageProfile,
    CommentByUser,
    ImagesByFilter,
    ImageQRResponse,
    TagModel,
)

from src.conf import messages


async def add_image(
    db: Session, url: str, public_id: str, user: User, description: str
):
    """
    Add an image to the database.

    This function adds an image entry to the database with the specified URL, public ID,
    user, and description.

    :param db: Database session.
    :type db: Session
    :param url: URL of the image.
    :type url: str
    :param public_id: Public ID of the image.
    :type public_id: str
    :param user: The user who uploaded the image.
    :type user: User
    :param description: Description of the image.
    :type description: str
    :return: The added image.
    :rtype: Image | None
    """
    if not user:
        return None
    image = Image(
        url=url, public_id=public_id, user_id=user.id, description=description
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


async def delete_image(db: Session, image_id: int):
    """
    Delete an image from the database.

    This function deletes an image entry from the database and also deletes the
    corresponding image from the cloud storage.

    :param db: Database session.
    :type db: Session
    :param image_id: ID of the image to be deleted.
    :type image_id: int
    :return: The deleted image.
    :rtype: Image | None
    """
    image = db.query(Image).filter(Image.id == image_id).first()
    image_cloudinary.delete_img(image.public_id)
    db.delete(image)
    db.commit()
    return image


async def update_desc(db: Session, image_id: int, description=str):
    """
    Update the description of an image.

    This function updates the description of an image in the database.

    :param db: Database session.
    :type db: Session
    :param image_id: ID of the image to be updated.
    :type image_id: int
    :param description: New description for the image.
    :type description: str
    :return: The updated image.
    :rtype: Image | None
    """
    image = db.query(Image).filter(Image.id == image_id).first()
    image.description = description
    db.commit()
    db.refresh(image)
    return image


async def get_image_by_id(db: Session, image_id: int) -> Image | None:
    """
    Retrieve an image by its ID.

    This function retrieves an image from the database based on its ID.

    :param db: Database session.
    :type db: Session
    :param image_id: ID of the image to retrieve.
    :type image_id: int
    :return: The retrieved image or None if not found.
    :rtype: Image | None
    """
    image = db.query(Image).filter(Image.id == image_id).first()
    return image


async def change_size_image(body: ImageChangeSizeModel, db: Session, user: User):
    """
    Change the size of an image.

    This function changes the size of an image in the database based on the provided
    `ImageChangeSizeModel`. It creates a new image record with the updated size and adds
    it to the database.

    :param body: The data containing the image ID and the new width.
    :type body: ImageChangeSizeModel
    :param db: Database session.
    :type db: Session
    :param user: The user making the request.
    :type user: User
    :return: Response containing the new image details.
    :rtype: ImageAddResponse
    """
    image = db.query(Image).filter(Image.id == body.id).first()
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
        )
    if image.user_id != user.id:
        raise HTTPException(status_code=403, detail=messages.NOT_ALLOWED)

    url, public_id = await image_cloudinary.change_size(image.public_id, body.width)
    new_image = Image(
        url=url, public_id=public_id, user_id=user.id, description=image.description
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    image_model = ImageModel(
        id=new_image.id,
        url=new_image.url,
        public_id=new_image.public_id,
        user_id=new_image.user_id,
    )
    return ImageAddResponse(image=image_model, detail=messages.IMAGE_RESIZED_ADDED)


async def fade_edges_image(body: ImageTransformModel, db: Session, user: User):
    """
    Apply a fade edges effect to an image.

    This function applies a fade edges effect to an image in the database based on the
    provided `ImageTransformModel`. It creates a new image record with the effect applied
    and adds it to the database.

    :param body: The data containing the image ID.
    :type body: ImageTransformModel
    :param db: Database session.
    :type db: Session
    :param user: The user making the request.
    :type user: User
    :return: Response containing the new image details.
    :rtype: ImageAddResponse
    """
    image = db.query(Image).filter(Image.id == body.id).first()
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
        )

    if image.user_id != user.id:
        raise HTTPException(status_code=403, detail=messages.NOT_ALLOWED)

    url, public_id = await image_cloudinary.fade_edges_image(public_id=image.public_id)

    new_image = Image(
        url=url, public_id=public_id, user_id=user.id, description=image.description
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    image_model = ImageModel(
        id=new_image.id,
        url=new_image.url,
        public_id=new_image.public_id,
        user_id=new_image.user_id,
    )

    return ImageAddResponse(image=image_model, detail=messages.IMAGE_FADE_ADDED)


async def black_white_image(body: ImageTransformModel, db: Session, user: User):
    """
    Apply a black and white effect to an image.

    This function applies a black and white effect to an image in the database based on
    the provided `ImageTransformModel`. It creates a new image record with the effect
    applied and adds it to the database.

    :param body: The data containing the image ID.
    :type body: ImageTransformModel
    :param db: Database session.
    :type db: Session
    :param user: The user making the request.
    :type user: User
    :return: Response containing the new image details.
    :rtype: ImageAddResponse
    """
    image = db.query(Image).filter(Image.id == body.id).first()
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
        )
    if image.user_id != user.id:
        raise HTTPException(status_code=403, detail=messages.NOT_ALLOWED)

    url, public_id = await image_cloudinary.make_black_white_image(
        public_id=image.public_id
    )

    new_image = Image(
        url=url, public_id=public_id, user_id=user.id, description=image.description
    )

    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    image_model = ImageModel(
        id=new_image.id,
        url=new_image.url,
        public_id=new_image.public_id,
        user_id=new_image.user_id,
    )

    return ImageAddResponse(image=image_model, detail=messages.BLACK_WHITE_ADDED)


async def get_all_images(
    db: Session,
    current_user: User,
    keyword: str = None,
    tag: str = None,
    min_rating: float = None,
):
    """
    Retrieve all images from the database based on specified filters.

    This function retrieves all images from the database based on the provided filters
    such as keyword, tag, and minimum rating.

    :param db: Database session.
    :type db: Session
    :param current_user: The user making the request.
    :type current_user: User
    :param keyword: Keyword to filter images by description.
    :type keyword: str, optional
    :param tag: Tag to filter images.
    :type tag: str, optional
    :param min_rating: Minimum rating to filter images.
    :type min_rating: float, optional
    :return: Response containing the list of filtered images.
    :rtype: ImagesByFilter
    """
    query = db.query(Image)
    if keyword:
        query = query.filter(Image.description.ilike(f"%{keyword}%"))
    if tag:
        query = query.filter(Image.tags.any(Tag.tag_name == tag))
    if min_rating is not None:
        query = query.join(Rating, Image.id == Rating.image_id)
        query = query.group_by(Image.id).having(func.avg(Rating.rate) >= min_rating)
    query = query.order_by(desc(Image.created_at))
    result = query.all()
    images = []
    for image in result:
        tags = []
        comments = []
        for comment in image.comments:
            new_comment = CommentByUser(
                user_id=comment.user_id, comment=comment.comment
            )
            comments.append(new_comment)
        for tag in image.tags:
            new_tag = tag.tag_name
            tags.append(new_tag)
        rating = await repository_ratings.calculate_rating(image.id, db, current_user)
        new_rating = rating["average_rating"]
        new_image = ImageProfile(
            url=image.url,
            description=image.description,
            average_rating=new_rating,
            tags=tags,
            comments=comments,
        )
        images.append(new_image)
    all_images = ImagesByFilter(images=images)
    return all_images


async def create_qr(body: ImageTransformModel, db: Session, user: User):
    """
    Generate and associate a QR code with an image.

    This function generates a QR code for an image and associates it with the image
    in the database.

    :param body: Request body containing the image ID.
    :type body: ImageTransformModel
    :param db: Database session.
    :type db: Session
    :param user: The user making the request.
    :type user: User
    :return: Response containing the image ID and QR code URL.
    :rtype: ImageQRResponse
    """
    image = db.query(Image).filter(Image.id == body.id).first()

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
        )
    if image.qr_url:
        return ImageQRResponse(image_id=image.id, qr_code_url=image.qr_url)

    qr = qrcode.QRCode()
    qr.add_data(image.url)
    qr.make(fit=True)

    qr_code_img = BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(qr_code_img)

    qr_code_img.seek(0)

    new_public_id = CloudImage.generate_name_image(user.email)

    upload_file = CloudImage.upload_image(qr_code_img, new_public_id)

    qr_code_url = CloudImage.get_url_for_image(new_public_id, upload_file)

    image.qr_url = qr_code_url

    db.commit()

    return ImageQRResponse(image_id=image.id, qr_code_url=qr_code_url)


async def add_tag(db: Session, user: User, image_id: int, tag_name: str):
    """
    Add a tag to an image.

    This function adds a tag to an image. If the tag does not exist, it is created
    before being added to the image.

    :param db: Database session.
    :type db: Session
    :param user: The user making the request.
    :type user: User
    :param image_id: ID of the image.
    :type image_id: int
    :param tag_name: Name of the tag to be added.
    :type tag_name: str
    :return: Response containing a message and the added tag name.
    :rtype: dict
    """
    image = db.query(Image).filter(Image.id == image_id).first()
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND
        )
    if image.user_id != user.id:
        raise HTTPException(status_code=403, detail=messages.NOT_ALLOWED)
    if len(image.tags) >= 5:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=messages.ONLY_FIVE_TAGS
        )
    tag = db.query(Tag).filter(Tag.tag_name == tag_name.lower()).first()

    if tag is None:
        tag_model = TagModel(tag_name=tag_name)
        tag = await create_tag(tag_model, db)

    image.tags.append(tag)

    db.commit()
    db.refresh(image)

    return {"message": "Tag successfully added", "tag": tag.tag_name}
