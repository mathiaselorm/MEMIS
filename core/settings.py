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

from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/
import os
import environ


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


FRONTEND_URL = 'memis.vercel.app' 

# FRONTEND_URL = 'http://localhost:5173' 



# Mailgun API configuration
BREVO_API_KEY = env('BREVO_API_KEY')
BREVO_DOMAIN = env('BREVO_DOMAIN')

# Default email settings
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='memis@melarc.me')


broker_connection_retry_on_startup = True

# # Celery configuration
# CELERY_BROKER_URL = "redis://127.0.0.1:6380/0"
# CELERY_RESULT_BACKEND = "redis://127.0.0.1:6380/0"

# Heroku Redis in production
CELERY_BROKER_URL = config('REDISCLOUD_URL')
CELERY_RESULT_BACKEND = config('REDISCLOUD_URL')

CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously
CELERY_TASK_EAGER_PROPAGATES = True  # Raise errors immediately
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_ALWAYS_EAGER = False  # Set to True only for local development if needed

BROKER_TRANSPORT_OPTIONS = {
    "max_connections": 2,
}

# Logging for Celery workers
CELERY_WORKER_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
CELERY_WORKER_TASK_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(task_name)s[%(task_id)s]: %(message)s"
CELERY_WORKER_REDIRECT_STDOUTS = True
CELERY_WORKER_REDIRECT_STDOUTS_LEVEL = 'DEBUG'


CELERY_BROKER_URL = env('REDISCLOUD_URL')
CELERY_BEAT_SCHEDULE = {
    # Example: runs every 60 seconds
    'check-maintenance-schedules': {
        'task': 'maintenance.tasks.check_maintenance_schedules',
        'schedule': 60.0,
    },
}




PASSWORD_RESET_TIMEOUT = 60 * 60  # 1 hour in seconds


CSRF_COOKIE_HTTPONLY = False  # Allows JavaScript to access the token
CSRF_COOKIE_NAME = "csrftoken"  # Name of the CSRF token in cookies
CSRF_COOKIE_SECURE = not DEBUG  # Set to True in production
CSRF_TRUSTED_ORIGINS = ['http://localhost:3000']  # Frontend URLs that Django trusts



# Use Cloudinary as the default file storage
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'


# Application definition

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary_storage',
    'cloudinary',
    'django_cleanup.apps.CleanupConfig',
    'rest_framework',
    'django_rest_passwordreset',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_yasg',
    'actstream',
    'channels',
    
    #installed apps
    'accounts.apps.AccountsConfig',
    'assets.apps.AssetsConfig',
    'inventory.apps.InventoryConfig',
    'notification.apps.NotificationConfig',
    'activity_stream'
    
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
    # 'simple_history.middleware.HistoryRequestMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
        'accounts.authentication.CookieJWTAuthentication',
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


DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG = {
    'CLASS': 'django_rest_passwordreset.tokens.RandomStringTokenGenerator',
    'OPTIONS': {
        'lifetime': timedelta(hours=1)
    }
}

REDIS_URL = env('REDISCLOUD_URL')

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL] 
        },
    },
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

# Password reset token expiration time in hours
DJANGO_REST_MULTITOKENAUTH_RESET_TOKEN_EXPIRY_TIME = 1 # Default is 24 hours
# Prevent information leakage for non-existent users on password reset request
DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE = False  # Default is False
# Allow password reset for users without a usable password
DJANGO_REST_MULTITOKENAUTH_REQUIRE_USABLE_PASSWORD = True  # Default is True



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
ASGI_APPLICATION = 'core.asgi.application'  # Required for Channels


LOGGING = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': '{levelname} {asctime} {module} {message}',
                    'style': '{',
                },
            },
            'handlers': {
                'file': {
                    'level': 'ERROR',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': 'django_errors.log',
                    'formatter': 'verbose',
                },
            },
            'loggers': {
                'django': {
                    'handlers': ['file'],
                    'level': 'DEBUG',
                    'propagate': True,
                },
                'accounts': {
                    'handlers': ['file'],
                    'level': 'DEBUG',
                    'propagate': True,
                },
                'assets': {
                    'handlers': ['file'],
                    'level': 'DEBUG',
                    'propagate': True,
                },
            },
        }



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
        'OPTIONS': {
            'min_length': 8, # Minimum length of 8 characters
        }
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

SITE_ID = 1



