from datetime import timedelta as td
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')

# Безопасное получение DEBUG
DEBUG = os.environ.get('DEBUG', '').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1, localhost, 192.168.0.61').split(', ')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'corsheaders',
    'colorfield',
    'django_minio_backend',
    'clickhouse_backend',
    'django_filters',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'debug_toolbar',
    'drf_spectacular',
    'djoser',
    'phonenumber_field',
    'docs',
    'files',
    'nomenclatures',
    'orders',
    'ch_statistic',
    'tasks',
    'users',
    'contact_persons',
]

# Базовый MIDDLEWARE
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Добавляем debug toolbar только в DEBUG режиме
if DEBUG:
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
    MIDDLEWARE.append('api.middleware.IntegrityMiddleware')

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

# Настройки базы данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'HOST': os.environ.get('POSTGRES_HOST'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PORT': os.environ.get('POSTGRES_PORT'),
        'PASSWORD': os.environ.get('POSTGRES_PASS'),
        'CONN_MAX_AGE': 60 if not DEBUG else 0,
    }
}

# Проверяем наличие настроек Clickhouse
CLICKHOUSE_HOST = os.environ.get('CLICKHOUSE_HOST')
if CLICKHOUSE_HOST:
    DATABASES['clickhouse'] = {
        'ENGINE': 'clickhouse_backend.backend',
        'NAME': os.environ.get('CLICKHOUSE_DB'),
        'HOST': CLICKHOUSE_HOST,
        'USER': os.environ.get('CLICKHOUSE_USER'),
        'PORT': os.environ.get('CLICKHOUSE_PORT'),
        'PASSWORD': os.environ.get('CLICKHOUSE_PASSWORD'),
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
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.PageLimitPagination',
    'PAGE_SIZE': 25,
}

# Убираем Browsable API в production
if not DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
        'rest_framework.renderers.JSONRenderer',
    )

SPECTACULAR_SETTINGS = {
    'TITLE': 'RMC REST API',
    'DESCRIPTION': 'API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# ---------------------------------- MINIO ---------------------------------- #
MINIO_REGION = os.environ.get('MINIO_REGION')
MINIO_ACCESS_KEY = os.environ.get('MINIO_STORAGE_ACCESS_KEY')
MINIO_SECRET_KEY = os.environ.get('MINIO_STORAGE_SECRET_KEY')
MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT')  # files:9000 для контейнеров
MINIO_USE_HTTPS = os.environ.get('MINIO_HTTPS', 'false').lower() == 'true'
MINIO_EXTERNAL_ENDPOINT = os.environ.get('MINIO_EXTERNAL_ENDPOINT')  # 192.168.0.61
MINIO_EXTERNAL_ENDPOINT_USE_HTTPS = os.environ.get('MINIO_EXTERNAL_HTTPS', 'false').lower() == 'true'

MINIO_PRIVATE_BUCKETS = ['local-media', 'local-static']
MINIO_MEDIA_FILES_BUCKET = 'local-media'
MINIO_STATIC_FILES_BUCKET = 'local-static'

# URL для статики (для браузера)
STATIC_URL = (
    f"{'https' if MINIO_EXTERNAL_ENDPOINT_USE_HTTPS else 'http'}://"
    f"{MINIO_EXTERNAL_ENDPOINT}:9000/local-static/"
)

MINIO_OPTIONS = {
    'region': MINIO_REGION,
    'access_key': MINIO_ACCESS_KEY,
    'secret_key': MINIO_SECRET_KEY,
    'endpoint': MINIO_ENDPOINT,   # files:9000 — Django внутри Docker
    'use_https': MINIO_USE_HTTPS,
}

# Используем MinIO только если не DEBUG
if DEBUG or not MINIO_ENDPOINT:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STORAGES = {
        'default': {
            'BACKEND': 'django_minio_backend.models.MinioBackend',
            'OPTIONS': MINIO_OPTIONS
        },
        'staticfiles': {
            'BACKEND': 'django_minio_backend.models.MinioBackendStatic',
            'OPTIONS': MINIO_OPTIONS
        },
    }

# --------------------------------- CELERY ---------------------------------- #

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_BACKEND')
if CELERY_BROKER_URL and CELERY_RESULT_BACKEND:
    CELERY_SINGLETON_BACKEND_URL = CELERY_RESULT_BACKEND
    CELERY_TIMEZONE = TIME_ZONE

# -------------------------------- SECURITY --------------------------------- #

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT'
]

CORS_ALLOWED_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type', 'dnt',
    'origin', 'user-agent','x-csrftoken', 'x-requested-with'
]

CSRF_TRUSTED_ORIGINS = os.environ.get('FRONTEND_DOMEN', '').split(', ')
if not DEBUG:
    CORS_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': td(days=30),
    'REFRESH_TOKEN_LIFETIME': td(days=60),
    'AUTH_HEADER_TYPES': ('access_token',),
    'BLACKLIST_AFTER_ROTATION': True,
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_TOKEN_CLASSES': ('api.tokens.CustomAccessToken',)
}

# ------------------------------ DEBUG TOOLBAR ------------------------------ #

if DEBUG:
    def show_toolbar(request):
        return True

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': show_toolbar,
    }

    import mimetypes
    mimetypes.add_type('application/javascript', '.js', True)

# ---------------------------- PRODUCTION SETTINGS -------------------------- #

if not DEBUG:
    # Безопасные настройки для production
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

    # Лимиты для загрузки
    DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
    FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB