# Development settings
from .base import *
import os

# Override for development
DEBUG = True
SECRET_KEY = 'django-insecure-dev-key-for-testing-only'

# Ensure static directory exists
STATIC_DIR = BASE_DIR / 'static'
if not STATIC_DIR.exists():
    STATIC_DIR.mkdir(exist_ok=True)

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/ooumph_feed_db.sqlite3',  # Use /tmp for write permissions
    }
}

# Ensure media directory exists
MEDIA_DIR = BASE_DIR / 'media'
if not MEDIA_DIR.exists():
    MEDIA_DIR.mkdir(exist_ok=True)

# Simple cache for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ooumph-feed-dev-cache',
        'TIMEOUT': 300,  # 5 minutes for development
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Celery for development (synchronous)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Channels for development (in-memory)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# Remove apps that might cause issues in development
DEVELOPMENT_EXCLUDED_APPS = [
    'django_celery_beat',
    'django_celery_results',
]

INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in DEVELOPMENT_EXCLUDED_APPS]

# Simple REST framework for development
REST_FRAMEWORK.update({
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Allow unauthenticated access for testing
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',
        'user': '10000/hour'
    }
})

# Relaxed CORS for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Development logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'analytics_dashboard': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'feed_algorithm': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
