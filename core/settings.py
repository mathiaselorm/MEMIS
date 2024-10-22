"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 5.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""


from datetime import timedelta
from pathlib import Path
from decouple import config
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/
import os
import environ
#from decouple import config


# Initialise environment variables
env = environ.Env()
#Locates the .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=False)


ALLOWED_HOSTS = ['*']


EMAIL_BACKEND = 'accounts.utils.BrevoAPIBackend'

# Mailgun API configuration
BREVO_API_KEY = config('BREVO_API_KEY')
BREVO_DOMAIN = config('BREVO_DOMAIN')

# Default email settings
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='memis@melarc.me')


# Backgroud_task settings
BACKGROUND_TASK_RUN_ASYNC = True
BACKGROUND_TASK_MAX_ATTEMPTS = 3
BACKGROUND_TASK_EXPIRED = 60 * 60 * 24   # Tasks will expire after 24 hours if they are not completed (measured in seconds)
BACKGROUND_TASK_RETRY_INTERVAL = [50, 300, 600] # Retry intervals in seconds: 1 minute, 5 minutes, 10 minutes between retries
BACKGROUND_TASK_COMPLETE_EXPIRED = 60 * 60 * 24  # Completed tasks expire after 24 hours


PASSWORD_RESET_TIMEOUT = 60 * 60  # 1 hour in seconds


CSRF_COOKIE_HTTPONLY = False  # Allows JavaScript to access the token
CSRF_COOKIE_NAME = "csrftoken"  # Name of the CSRF token in cookies
CSRF_COOKIE_SECURE = not DEBUG  # Set to True in production
CSRF_TRUSTED_ORIGINS = ['http://localhost:3000']  # Frontend URLs that Django trusts


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary_storage',
    'cloudinary',
    'background_task',
    'django_cleanup.apps.CleanupConfig',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_yasg',
    'auditlog',
    'accounts',
    'assets',
    'inventory'
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # 'accounts.authentication.cookie_authentication.CookieJWTAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
         'rest_framework.filters.SearchFilter',
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
}

# Cloudinary storage configuration using environment variables
cloudinary.config(
    cloud_name=config('CLOUDINARY_CLOUD_NAME'),
    api_key=config('CLOUDINARY_API_KEY'),
    api_secret=config('CLOUDINARY_API_SECRET'),
    secure=True  # Ensure the connection is secure
)

# check
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
MEDIA_URL = 'https://res.cloudinary.com/dr8uzgh5e/image/upload/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

ROOT_URLCONF = 'core.urls'

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{levelname} {asctime} {module} {message}',
#             'style': '{',
#         },
#     },
#     'handlers': {
#         'file': {
#             'level': 'DEBUG',  # Capture more details, including debug info
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': 'django_errors.log',  # Make sure this file is writable
#             'formatter': 'verbose',
#             'maxBytes': 1024 * 1024 * 5,  # 5MB log file
#             'backupCount': 3,
#         },
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         },
#     },
#     'root': {  # Configure root logger to capture all logs
#         'handlers': ['file', 'console'],  # Output to both file and console
#         'level': 'DEBUG',  # Log all events down to DEBUG level
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['file', 'console'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#         'django.db.backends': {  # Log database queries
#             'handlers': ['file'],
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#         'background_task': {
#             'handlers': ['file'],
#             'level': 'DEBUG',  # Capture debug info for background tasks
#             'propagate': True,
#         },
#     },
# }



# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases



DATABASES = {
    'default': env.db()
}




# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATIC_ROOT = BASE_DIR / "staticfiles"


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.CustomUser'








# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{levelname} {asctime} {module} {message}',
#             'style': '{',
#         },
#     },
#     'handlers': {
#         'file': {
#             'level': 'DEBUG',  # Capture more details, including debug info
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': 'django_errors.log',  # Make sure this file is writable
#             'formatter': 'verbose',
#             'maxBytes': 1024 * 1024 * 5,  # 5MB log file
#             'backupCount': 3,
#         },
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         },
#     },
#     'root': {  # Configure root logger to capture all logs
#         'handlers': ['file', 'console'],  # Output to both file and console
#         'level': 'DEBUG',  # Log all events down to DEBUG level
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['file', 'console'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#         'django.db.backends': {  # Log database queries
#             'handlers': ['file'],
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#         'background_task': {
#             'handlers': ['file'],
#             'level': 'DEBUG',  # Capture debug info for background tasks
#             'propagate': True,
#         },
#     },
# }
