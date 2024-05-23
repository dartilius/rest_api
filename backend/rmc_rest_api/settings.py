from pathlib import Path
from datetime import timedelta as td
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = True

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1, localhost').split(', ')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'corsheaders',
    'django_filters',
    'rest_framework',
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
    'users'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
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
        'NAME': os.getenv('POSTGRES_DB', 'django'),
        'USER': os.getenv('POSTGRES_USER', 'django'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', 5432)
    },
    # "clickhouse": {
    #     "ENGINE": "clickhouse_backend.backend",
    #     "NAME": "default",
    #     "HOST": "localhost",
    #     "USER": "DB_USER",
    #     "PASSWORD": "DB_PASSWORD",
    # }
}

# DATABASE_ROUTERS = ["dbrouters.ClickHouseRouter"]


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

AUTH_USER_MODEL = "users.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
]

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Asia/Krasnoyarsk'

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOW_ALL_ORIGINS = True

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_STORAGE_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_STORAGE_SECRET_KEY")
MINIO_USE_HTTPS = False
MINIO_PRIVATE_BUCKETS = [
    'local-media',
    'local-static'
]
DEFAULT_FILE_STORAGE = 'django_minio_backend.models.MinioBackend'
MINIO_MEDIA_FILES_BUCKET = 'local-media'
STATICFILES_STORAGE = 'django_minio_backend.models.MinioBackendStatic'
MINIO_STATIC_FILES_BUCKET = 'local-static'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.PageLimitPagination',
    'PAGE_SIZE': 25
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': td(days=30),
    'REFRESH_TOKEN_LIFETIME': td(days=60),
    'AUTH_HEADER_TYPES': ('access_token',),
}


def show_toolbar(request):
    return True


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": show_toolbar,
}

if DEBUG:
    import mimetypes
    mimetypes.add_type("application/javascript", ".js", True)
