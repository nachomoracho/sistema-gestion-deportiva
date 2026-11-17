import os
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='INSECURE-change-in-production')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())
DJANGO_ENV = config('DJANGO_ENV', default='development')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'corsheaders',
    'django_filters',
    'src',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'src.config.middleware.SecurityHeadersMiddleware',
    'src.config.middleware.AuditLoggingMiddleware',
]

ROOT_URLCONF = 'src.config.urls'

DB_ENGINE = config('DB_ENGINE', default='sqlite')

if DB_ENGINE == 'oracle':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.oracle',
            'NAME': config('ORACLE_DSN'),
            'USER': config('ORACLE_USER'),
            'PASSWORD': config('ORACLE_PASSWORD'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'src.controllers.authentication.JWTAuthenticationBackend',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': config('ANON_RATE_THROTTLE', default='5/min'),
        'user': config('USER_RATE_THROTTLE', default='60/min'),
    },
    'EXCEPTION_HANDLER': 'src.config.exceptions.custom_exception_handler',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=30, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=1, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000', cast=Csv())
CORS_ALLOW_CREDENTIALS = True

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_BROWSER_XSS_FILTER = True

if DJANGO_ENV == 'production':
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

LOG_LEVEL = config('LOG_LEVEL', default='INFO')
AUDIT_LOG_FILE = config('AUDIT_LOG_FILE', default='security_audit.log')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'audit': {
            'format': '%(asctime)s [%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / AUDIT_LOG_FILE,
            'formatter': 'audit',
        },
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'audit',
        },
    },
    'loggers': {
        'security_audit': {
            'handlers': ['audit_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
