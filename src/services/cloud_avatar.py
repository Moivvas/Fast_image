import hashlib

import cloudinary
import cloudinary.uploader

from src.conf.config import settings


class CloudAvatar:
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )

    @staticmethod
    def generate_name_avatar(email: str) -> str:
        name = hashlib.sha256(email.encode('utf-8')).hexdigest()[:12]
        return f"fast_image/{name}"

    @staticmethod
    def upload_avatar(file, public_id: str) -> dict:
        r = cloudinary.uploader.upload(file, public_id=public_id, overwrite=True)
        return r

    @staticmethod
    def get_url_for_avatar(public_id, r) -> str:
        src_url = cloudinary.CloudinaryImage(public_id) \
            .build_url(width=250, height=250, crop='fill', version=r.get('version'))
        return src_url
