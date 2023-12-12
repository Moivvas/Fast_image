from sqlalchemy.orm import Session


from PIL import Image

from src.database.models import Image, User

from src.services.cloud_images import image_cloudinary


async def add_image(db: Session, url: str, public_id: str, user: User):
    if not user:
        return None
  
    db_image = Image(url=url, public_id=public_id, user_id=user.id)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image


async def delete_image(db: Session, id: int, user: User):
    db_image = db.query(Image).filter(Image.id == id).first()
    await image_cloudinary.delete_image(db_image.public_id)
    db.delete(db_image)
    db.commit()
    return db_image
