import cloudinary
from decouple import config


CLOUDINARY_CLOUD_NAME = config('CLOUDINARY_CLOUD_NAME', default='dr8uzgh5e')
CLOUDINARY_API_KEY = config('CLOUDINARY_API_KEY', default='462169394955256')
CLOUDINARY_API_SECRET = config('CLOUDINARY_API_SECRET')

def cloudinary_init():
    cloudinary.config( 
        cloud_name = CLOUDINARY_CLOUD_NAME, 
        api_key = CLOUDINARY_API_KEY, 
        api_secret = CLOUDINARY_API_SECRET, 
        secure=True
    )