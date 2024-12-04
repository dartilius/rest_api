from datetime import timedelta as td
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = os.environ.get('DEBUG').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1, localhost').split(', ')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'corsheaders',
    'django_minio_backend',
    'clickhouse_backend',
    'django_filters',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'debug_toolbar',
    'drf_yasg',
    'djoser',
    'phonenumber_field',
    'docs',
    'files',
    'nomenclatures',
    'orders',
    'ch_statistic',
    'tasks',
    'users',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'api.middleware.IntegrityMiddleware',  # ждём фикса в джанге и убираем это
]

ROOT_URLCONF = 'rmc_rest_api.urls'

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

WSGI_APPLICATION = 'rmc_rest_api.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'HOST': os.environ.get('POSTGRES_HOST'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PORT': os.environ.get('POSTGRES_PORT'),
        'PASSWORD': os.environ.get('POSTGRES_PASS')
    },
    'clickhouse': {
        'ENGINE': 'clickhouse_backend.backend',
        'NAME': os.environ.get('CLICKHOUSE_DB'),
        'HOST': os.environ.get('CLICKHOUSE_HOST'),
        'USER': os.environ.get('CLICKHOUSE_USER'),
        'PORT': os.environ.get('CLICKHOUSE_PORT'),
        'PASSWORD': os.environ.get('CLICKHOUSE_PASSWORD'),
    }
}

DATABASE_ROUTERS = ['rmc_rest_api.dbrouters.ClickHouseRouter']


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

AUTH_USER_MODEL = 'users.CustomUser'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
]

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Asia/Krasnoyarsk'

USE_I18N = True

USE_TZ = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.PageLimitPagination',
    'PAGE_SIZE': 25,
}

# ---------------------------------- MINIO ---------------------------------- #

MINIO_REGION = os.environ.get('MINIO_REGION')
MINIO_ACCESS_KEY = os.environ.get('MINIO_STORAGE_ACCESS_KEY')
MINIO_SECRET_KEY = os.environ.get('MINIO_STORAGE_SECRET_KEY')
MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT')
MINIO_USE_HTTPS = os.environ.get('MINIO_HTTPS').lower() == 'true'
MINIO_EXTERNAL_ENDPOINT = os.environ.get('MINIO_EXTERNAL_ENDPOINT')
MINIO_EXTERNAL_ENDPOINT_USE_HTTPS = os.environ.get('MINIO_EXTERNAL_HTTPS').lower() == 'true'
MINIO_PRIVATE_BUCKETS = [
    'local-media',
    'local-static'
]
MINIO_MEDIA_FILES_BUCKET = 'local-media'
MINIO_STATIC_FILES_BUCKET = 'local-static'
STORAGES = {
    'default': {
        'BACKEND': 'django_minio_backend.models.MinioBackend'
    },
    'staticfiles': {
        'BACKEND': 'django_minio_backend.models.MinioBackendStatic'
    },
}

# --------------------------------- CELERY ---------------------------------- #

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_BACKEND')
CELERY_SINGLETON_BACKEND_URL = CELERY_RESULT_BACKEND
CELERY_TIMEZONE = TIME_ZONE

# -------------------------------- SECURITY --------------------------------- #

CORS_ALLOW_ALL_ORIGINS = DEBUG
CSRF_TRUSTED_ORIGINS = os.environ.get('FRONTEND_DOMEN').split(', ')
if not DEBUG:
    CORS_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': td(
        days=int(os.environ.get("ACCESS_TOKEN_LIFETIME_DAYS"))
    ),
    'REFRESH_TOKEN_LIFETIME': td(
        days=int(os.environ.get("REFRESH_TOKEN_LIFETIME_DAYS"))
    ),
    'AUTH_HEADER_TYPES': ('access_token',),
    'BLACKLIST_AFTER_ROTATION': True,
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_TOKEN_CLASSES': ('api.tokens.CustomAccessToken',)
}

# ------------------------------ DEBUG TOOLBAR ------------------------------ #


def show_toolbar(request):
    return DEBUG


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
}

if DEBUG:
    import mimetypes
    mimetypes.add_type('application/javascript', '.js', True)
