from fastapi import HTTPException, status
from sqlalchemy.orm import Session


from src.database.models import Image, User

from src.services.cloud_images_service import image_cloudinary

from src.schemas import ImageChangeSizeModel, ImageAddResponse, ImageModel, ImageTransformModel
from src.conf import messages


async def add_image(db: Session, url: str, public_id: str, user: User, description: str):
    if not user:
        return None
    db_image = Image(url=url, public_id=public_id, user_id=user.id, description=description)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image


async def show_image(db: Session, id: int, user: User):
    pass


async def delete_image(db: Session, id: int):
    db_image = db.query(Image).filter(Image.id == id).first()
    image_cloudinary.delete_img(db_image.public_id)
    db.delete(db_image)
    db.commit()
    return db_image


async def update_desc(db: Session, id: int, description=str):
    db_image = db.query(Image).filter(Image.id == id).first()
    db_image.description = description
    db.commit()
    db.refresh(db_image)
    return db_image


async def get_image_by_id(db: Session, image_id: int) -> Image:
    db_image = db.query(Image).filter(Image.id == image_id).first()
    return db_image

async def change_size_image(body: ImageChangeSizeModel, db: Session, user: User):
    try:
        image = db.query(Image).filter(Image.id == body.id).first()
        if image is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND)
        url, public_id = await image_cloudinary.change_size(image.public_id, body.width)
        new_image = Image(url=url, public_id=public_id, user_id=user.id, description=image.description)
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        image_model = ImageModel(id=new_image.id, url=new_image.url, public_id=new_image.public_id, user_id=new_image.user_id)
        return ImageAddResponse(image=image_model, detail=messages.IMAGE_RESIZED_ADDED)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


async def fade_edges_image(body: ImageTransformModel, db: Session, user: User):
    try:
        image = db.query(Image).filter(Image.id == body.id).first()
        if image is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND)
        
        url, public_id = await image_cloudinary.fade_edges_image(public_id=image.public_id)
        
        new_image = Image(url=url, public_id=public_id, user_id=user.id, description=image.description)
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        
        image_model = ImageModel(id=new_image.id, url=new_image.url, public_id=new_image.public_id, user_id=new_image.user_id)
        
        return ImageAddResponse(image=image_model, detail=messages.IMAGE_FADE_ADDED)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

async def black_white_image(body: ImageTransformModel, db: Session, user: User):
    try:
        image = db.query(Image).filter(Image.id == body.id).first()
        if image is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.IMAGE_NOT_FOUND)
        
        url, public_id = await image_cloudinary.make_black_white_image(public_id=image.public_id)
        
        new_image = Image(url=url, public_id=public_id, user_id=user.id, description=image.description)
    
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        
        image_model = ImageModel(id=new_image.id, url=new_image.url, public_id=new_image.public_id, user_id=new_image.user_id)
        
        return ImageAddResponse(image=image_model, detail=messages.BLACK_WHITE_ADDED)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
