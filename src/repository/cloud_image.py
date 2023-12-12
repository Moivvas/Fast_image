from sqlalchemy.orm import Session


from src.database.models import Image, User

from src.services.cloud_images_service import image_cloudinary


async def add_image(db: Session, url: str, public_id: str, user: User):
    if not user:
        return None
  
    db_image = Image(url=url, public_id=public_id, user_id=user.id)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

async def show_image(db: Session, id: int, user: User):
    pass

async def delete_image(db: Session, id: int):
    db_image = db.query(Image).filter(Image.id == id).first()
    print(db_image.url)
    print(db_image.user_id)
    public_id = db_image.public_id
    print(public_id)
    image_cloudinary.delete_img(public_id)
    db.delete(db_image)
    db.commit()
    return db_image
