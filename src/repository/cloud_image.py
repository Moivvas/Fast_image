from sqlalchemy.orm import Session


from src.database.models import Image, User

from src.services.cloud_images_service import image_cloudinary


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

async def update_desc(db: Session, id:int, description=str):
    db_image = db.query(Image).filter(Image.id == id).first()
    db_image.description = description
    db.commit()
    db.refresh(db_image)
    return db_image



def get_image_by_id(db: Session, image_id: int) -> Image:
    db_image = db.query(Image).filter(Image.id == image_id).first()
    return db_image