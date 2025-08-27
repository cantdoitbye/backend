import os
import logging
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG') == 'True'
IS_LOCAL_STATIC_STORAGE = os.getenv('IS_LOCAL_STATIC_STORAGE') == 'True'
ENV = os.getenv('ENV')


ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'graphql_jwt.refresh_token.apps.RefreshTokenConfig',
    'django_neomodel',
    'graphene_django',
    'graphql_jwt',
    'upload',
    'storages',
    'post_office',
    'auth_manager',
    'community',
    'story',
    'post',
    'connection',
    'msg',
    'service',
    'dairy',
    'shop',
    'corsheaders',
    'vibe_manager',
    'monitoring',
    'docs',
    'agentic',


]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # 'graphql_jwt.middleware.JSONWebTokenMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'socialooumph.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, "email_templates"),
        ],
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

WSGI_APPLICATION = 'socialooumph.wsgi.application'

url = urlparse(os.getenv('DATABASE_URL'))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': url.path[1:], 
        'USER': url.username,
        'PASSWORD': url.password,
        'HOST': url.hostname,
        'PORT': url.port,
    }
}


CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv('REDIS_URL'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # "PASSWORD": os.getenv('REDIS_URL').split(':')[2].split('@')[0]
        }
    }
}

# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://:ooumphmemoriDB003@redis:6379/0",  # Don't forget to put : before password otherwise it did not recognise the password
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
# }



SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


# Celery configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'



# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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



GRAPHQL_JWT = {
    'JWT_PAYLOAD_HANDLER': 'custom_backends.utils.custom_jwt_payload',
    'JWT_VERIFY_EXPIRATION': False,  # Disable token expiration
    'JWT_LONG_RUNNING_REFRESH_TOKEN': True,
    'JWT_SECRET_KEY': SECRET_KEY,
    'JWT_ALGORITHM': 'HS256',
    # 'JWT_EXPIRATION_DELTA': timedelta(days=3),  # Disabled - tokens don't expire
    # 'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),  # Disabled - tokens don't expire
    'JWT_ALLOW_ANY_CLASSES': [
        'graphql_jwt.mutations.Verify',
        'graphql_jwt.mutations.Refresh',
        'graphql_jwt.mutations.ObtainJSONWebToken',
        'graphql_jwt.mutations.Revoke',
    ],
     'JWT_AUTH_HEADER_PREFIX': 'Bearer',
}


LANGUAGE_CODE = 'en-us'

if DEBUG:
    TIME_ZONE = 'Asia/Kolkata'
else:
    TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True






DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')




NEOMODEL_NEO4J_BOLT_URL =os.getenv('NEOMODEL_NEO4J_BOLT_URL')
# NEOMODEL_NEO4J_BOLT_URL="bolt://neo4j:BwA4zwGhfRT8nx5@34.170.99.162:7687"
NEOMODEL_SIGNALS = os.getenv('NEOMODEL_SIGNALS') == 'True'
NEOMODEL_FORCE_TIMEZONE = os.getenv('NEOMODEL_FORCE_TIMEZONE') == 'True'
NEOMODEL_MAX_CONNECTION_POOL_SIZE = int(os.getenv('NEOMODEL_MAX_CONNECTION_POOL_SIZE', 5000))


GRAPHENE = {
    "SCHEMA": "schema.schema.schema",
    "MIDDLEWARE": [
        "graphql_jwt.middleware.JSONWebTokenMiddleware",
        "custom_backends.middlewares.JWTMiddleware.JWTMiddleware",
    ],
}


AUTHENTICATION_BACKENDS = [
    "custom_backends.backends.UserIdBackend",
    "graphql_jwt.backends.JSONWebTokenBackend",
    "django.contrib.auth.backends.ModelBackend",
]



#Email Sender Confg 

EMAIL_BACKEND = 'post_office.EmailBackend'
POST_OFFICE = {
    'DEFAULT_PRIORITY': 'now',
    'BACKENDS': {
        'default': 'django.core.mail.backends.smtp.EmailBackend',
    },
}

EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS') == 'True'
EMAIL_PORT = int(os.getenv('EMAIL_PORT'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

POST_OFFICE_TEMPLATE_DIR = os.path.join(BASE_DIR, 'email_templates')


# MinIO settings
AWS_ACCESS_KEY_ID =os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN')
AWS_QUERYSTRING_AUTH = False  # Disables query string authentication for static files

# Static files (CSS, JavaScript, Images)
STATICFILES_STORAGE = 'custom_backends.custom_storages.StaticStorage'
STATIC_URL = f'{AWS_S3_CUSTOM_DOMAIN}/{AWS_STORAGE_BUCKET_NAME}/'

# Media files (User uploads)
DEFAULT_FILE_STORAGE = 'custom_backends.custom_storages.MediaStorage'
MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/media/'


NOTIFICATION_SERVICE_URL = os.getenv('NOTIFICATION_SERVICE_URL')



if IS_LOCAL_STATIC_STORAGE:
    STATICFILES_STORAGE = 'custom_backends.custom_storages.StaticStorage'
    DEFAULT_FILE_STORAGE = 'custom_backends.custom_storages.MediaStorage'






#Upload Size and Upload Content Type  (It will be utilize pipelined when we structure the media level encoding)
MAX_UPLOAD_SIZE = 10485760  # 10 MB
ALLOWED_CONTENT_TYPES = ['image/jpeg', 'image/png', 'application/pdf']



CORS_ALLOW_ALL_ORIGINS = True
CORS_ORIGIN_ALLOW_ALL = True

MATRIX_SERVER_URL = os.getenv("MATRIX_SERVER_URL")
print(MATRIX_SERVER_URL)
MATRIX_RETRY_LIMIT = os.getenv('MATRIX_RETRY_LIMIT')
MATRIX_TIMEOUT = os.getenv('MATRIX_TIMEOUT')
MATRIX_ADMIN_USER = os.getenv('MATRIX_ADMIN_USER')
MATRIX_ADMIN_PASSWORD = os.getenv('MATRIX_ADMIN_PASSWORD')

# it will get removed in susequent build
CSRF_TRUSTED_ORIGINS = ["https://backend.ooumph.com"] 

# Social Authentication Settings
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')

FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID', '')
FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET', '')

APPLE_CLIENT_ID = os.getenv('APPLE_CLIENT_ID', '')  # Your app's bundle ID
APPLE_KEY_ID = os.getenv('APPLE_KEY_ID', '')  # Key ID from Apple Developer
APPLE_TEAM_ID = os.getenv('APPLE_TEAM_ID', '')  # Team ID from Apple Developer
APPLE_PRIVATE_KEY = os.getenv('APPLE_PRIVATE_KEY', '')  # Private key content


# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s %(levelname)s %(message)s',
#     handlers=[
#         logging.FileHandler('logs/error.log',mode='a'),  
#         logging.FileHandler('logs/request.log', mode='a'),  
#         logging.FileHandler('logs/debug.log', mode='a'),  
#         logging.FileHandler('logs/info.log', mode='a'),  
#         logging.FileHandler('logs/warning.log', mode='a'),
#     ]
# )


# logger = logging.getLogger('django')
# logger.setLevel(logging.DEBUG) 


# logger = logging.getLogger('environment')
# logger.info(f"Running in {ENV} environment"
