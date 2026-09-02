"""
Настройки проекта RMC REST API.

ОПИСАНИЕ:
───────────────────────────────────────────────────────────────────────────────
Данный файл содержит все настройки для Django проекта RMC REST API.
Включает конфигурацию баз данных, кеширования, хранения файлов,
очередей задач, аутентификации, документации API и многое другое.
"""

import os
from datetime import timedelta as td
from pathlib import Path

# =============================================================================
# 1. БАЗОВЫЕ НАСТРОЙКИ DJANGO
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')

# Безопасное получение DEBUG
DEBUG = os.environ.get('DEBUG', '').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1, localhost').split(', ')

# =============================================================================
# 2. ПОДКЛЮЧЕННЫЕ ПРИЛОЖЕНИЯ
# =============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'django_opensearch_dsl',
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
    'drf_spectacular_sidecar',
    'djoser',
    'phonenumber_field',
    'dal',
    'dal_select2',
    'docs',
    'brands',
    'addresses',
    'users',
    'counterparties',
    'files',
    'nomenclatures',
    'orders',
    'ch_statistic',
    'tasks',
    'promotions',
    'placement_order',
    'feedback.apps.FeedbackConfig',
    'services.apps.ServicesConfig',
]

# =============================================================================
# 3. НАСТРОЙКИ ЭЛЕКТРОННОЙ ПОЧТЫ
# =============================================================================

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))

EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'false').lower() == 'true'

if DEBUG or os.environ.get('DISABLE_EMAIL_SSL_VERIFY', 'true').lower() == 'true':
    EMAIL_BACKEND = 'feedback.email_backend.CustomEmailBackend'
    print("Using email backend without SSL verification")
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_TIMEOUT = 10

if not DEBUG:
    EMAIL_SSL_CERTFILE = None
    EMAIL_SSL_KEYFILE = None

# =============================================================================
# 4. НАСТРОЙКИ ПРОМЕЖУТОЧНОГО ПО (MIDDLEWARE)
# =============================================================================

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

if DEBUG:
    MIDDLEWARE += [
        'api.middleware.IntegrityMiddleware',
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

# =============================================================================
# 5. НАСТРОЙКИ БАЗ ДАННЫХ
# =============================================================================

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

CLICKHOUSE_HOST = os.environ.get('CLICKHOUSE_HOST')
CLICKHOUSE_STATISTICS_TABLE_SUFFIX = os.environ.get(
    'CLICKHOUSE_STATISTICS_TABLE_SUFFIX', ''
)
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

# =============================================================================
# 6. АУТЕНТИФИКАЦИЯ
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'users.CustomUser'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
]

# =============================================================================
# 7. REST FRAMEWORK И ДОКУМЕНТАЦИЯ API
# =============================================================================

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

if not DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
        'rest_framework.renderers.JSONRenderer',
    )

SPECTACULAR_SETTINGS = {
    'TITLE': 'RMC REST API',
    'DESCRIPTION': """
    # API для управления системой RMC

    ## Возможности
    - Управление номенклатурами (рабочими станциями)
    - Управление заказами (рекламными и фоновыми)
    - Управление пользователями и правами доступа
    - Статистика и аналитика
    - Управление файлами и контентом
    """,
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,

    # Использование drf-spectacular-sidecar
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',

    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'displayRequestDuration': True,
        'filter': True,
        'docExpansion': 'list',
        'defaultModelsExpandDepth': -1,
        'defaultModelExpandDepth': 2,
    },

    'REDOC_SETTINGS': {
        'expandResponses': 'all',
        'disableSearch': False,
        'theme': {
            'colors': {
                'primary': '#2c3e50',
            },
        },
    },

    'SORT_OPERATIONS': False,
    'SORT_PARAMETERS': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_SPLIT_RESPONSE': True,
}

# =============================================================================
# 8. КЕШИРОВАНИЕ (Redis)
# =============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'KEY_PREFIX': 'django_cache',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'IGNORE_EXCEPTIONS': True,
        }
    }
}

CACHE_TTL = 60 * 5

# =============================================================================
# 9. ХРАНЕНИЕ ФАЙЛОВ (MinIO)
# =============================================================================

from datetime import timedelta

MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'files:9000')
MINIO_ACCESS_KEY = os.environ.get('MINIO_STORAGE_ACCESS_KEY')
MINIO_SECRET_KEY = os.environ.get('MINIO_STORAGE_SECRET_KEY')
MINIO_USE_HTTPS = os.environ.get('MINIO_HTTPS', 'false').lower() == 'true'
MINIO_EXTERNAL_ENDPOINT = os.environ.get('MINIO_EXTERNAL_ENDPOINT')
MINIO_EXTERNAL_ENDPOINT_USE_HTTPS = os.environ.get('MINIO_EXTERNAL_HTTPS', 'true').lower() == 'true'
MINIO_REGION = os.environ.get('MINIO_REGION', 'us-east-1')
# django-minio-backend reads this flag from Django settings when deciding
# whether storage.url() may reuse a previously generated presigned URL.
MINIO_URL_CACHING_ENABLED = False

MINIO_PUBLIC_BUCKETS = ['local-static', 'builds']
MINIO_PRIVATE_BUCKETS = ['local-media']

STORAGES = {
    'default': {
        'BACKEND': 'django_minio_backend.models.MinioBackend',
        'OPTIONS': {
            'MINIO_ENDPOINT': MINIO_ENDPOINT,
            'MINIO_ACCESS_KEY': MINIO_ACCESS_KEY,
            'MINIO_SECRET_KEY': MINIO_SECRET_KEY,
            'MINIO_USE_HTTPS': MINIO_USE_HTTPS,
            'MINIO_REGION': MINIO_REGION,
            'MINIO_EXTERNAL_ENDPOINT': MINIO_EXTERNAL_ENDPOINT,
            'MINIO_EXTERNAL_ENDPOINT_USE_HTTPS': MINIO_EXTERNAL_ENDPOINT_USE_HTTPS,
            'MINIO_PRIVATE_BUCKETS': MINIO_PRIVATE_BUCKETS,
            'MINIO_PUBLIC_BUCKETS': MINIO_PUBLIC_BUCKETS,
            'MINIO_URL_EXPIRY_HOURS': timedelta(days=1),
            # API responses contain presigned URLs. They must be generated for
            # the current request, not reused from Django/Redis URL cache.
            'MINIO_URL_CACHING_ENABLED': False,
            'MINIO_CONSISTENCY_CHECK_ON_START': False,
        }
    },
    'staticfiles': {
        'BACKEND': 'django_minio_backend.models.MinioBackendStatic',
        'OPTIONS': {
            'MINIO_ENDPOINT': MINIO_ENDPOINT,
            'MINIO_ACCESS_KEY': MINIO_ACCESS_KEY,
            'MINIO_SECRET_KEY': MINIO_SECRET_KEY,
            'MINIO_USE_HTTPS': MINIO_USE_HTTPS,
            'MINIO_REGION': MINIO_REGION,
            'MINIO_EXTERNAL_ENDPOINT': MINIO_EXTERNAL_ENDPOINT,
            'MINIO_EXTERNAL_ENDPOINT_USE_HTTPS': MINIO_EXTERNAL_ENDPOINT_USE_HTTPS,
            'MINIO_STATIC_FILES_BUCKET': 'local-static',
            'MINIO_URL_EXPIRY_HOURS': timedelta(days=365),
            'MINIO_CONSISTENCY_CHECK_ON_START': True,
        }
    },
}

# =============================================================================
# 10. ЯЗЫК И ВРЕМЯ
# =============================================================================

LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Asia/Krasnoyarsk'
USE_I18N = True
USE_TZ = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# 11. ОЧЕРЕДИ ЗАДАЧ (Celery)
# =============================================================================

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_BACKEND')

if CELERY_BROKER_URL and CELERY_RESULT_BACKEND:
    CELERY_SINGLETON_BACKEND_URL = CELERY_RESULT_BACKEND
    CELERY_TIMEZONE = TIME_ZONE

# =============================================================================
# 12. БЕЗОПАСНОСТЬ (CORS, JWT)
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
CORS_ALLOWED_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type', 'dnt',
    'origin', 'user-agent', 'x-csrftoken', 'x-requested-with'
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

# =============================================================================
# 13. ОТЛАДКА (Debug Toolbar)
# =============================================================================

if DEBUG:
    def show_toolbar(request):
        return True

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': show_toolbar,
        'SQL_QUERY_TIME_THRESHOLD': 0.1,
        'ENABLE_STACKTRACES': True,
        'RESULTS_CACHE_SIZE': 25,
        'RENDER_PANELS': True,
    }

    import mimetypes
    mimetypes.add_type('application/javascript', '.js', True)

# =============================================================================
# 14. ПРОИЗВОДСТВЕННЫЕ НАСТРОЙКИ
# =============================================================================

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

    DATA_UPLOAD_MAX_MEMORY_SIZE = 268435456
    FILE_UPLOAD_MAX_MEMORY_SIZE = 268435456

# =============================================================================
# 15. ПОЛНОТЕКСТОВЫЙ ПОИСК (OpenSearch)
# =============================================================================

OPENSEARCH_DSL = {
    'default': {
        'hosts': 'opensearch:9200',
    }
}

OPENSEARCH_DSL_AUTOSYNC = False

# =============================================================================
# 16. ЛОГИРОВАНИЕ
# =============================================================================

LOG_DIR = os.path.join(BASE_DIR, 'logs')
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except Exception:
    LOG_DIR = '/tmp'
    os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} | {module} | {funcName}:{lineno} | {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {asctime} | {message}',
            'style': '{',
            'datefmt': '%H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'feedback_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'feedback.log'),
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 3,
            'formatter': 'verbose',
        },
        'email_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'email.log'),
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 3,
            'formatter': 'verbose',
        },
        'api_1c_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'api_1c.log'),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'opensearch_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'opensearch.log'),
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'debug_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'debug.log'),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'feedback': {
            'handlers': ['feedback_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'feedback.email': {
            'handlers': ['email_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'services.api_1c': {
            'handlers': ['api_1c_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'nomenclatures.services.opensearch_search': {
            'handlers': ['opensearch_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'nomenclatures.filters': {
            'handlers': ['opensearch_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        # 'django.db.backends': {
        #     'handlers': ['debug_file', 'console'],
        #     'level': 'DEBUG' if DEBUG else 'ERROR',
        #     'propagate': False,
        # },
    },
}

# import os
# from datetime import timedelta as td
# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY = os.environ.get('SECRET_KEY')

# # Безопасное получение DEBUG
# DEBUG = os.environ.get('DEBUG', '').lower() == 'true'

# ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1, localhost').split(', ')

# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
#     'django.contrib.postgres',
#     'django_opensearch_dsl',
#     'corsheaders',
#     'colorfield',
#     'django_minio_backend',
#     'clickhouse_backend',
#     'django_filters',
#     'rest_framework',
#     'rest_framework_simplejwt',
#     'rest_framework_simplejwt.token_blacklist',
#     'debug_toolbar',
#     'drf_spectacular',
#     'djoser',
#     'phonenumber_field',
#     'dal',
#     'dal_select2',
#     'docs',
#     'brands',
#     'addresses',
#     'users',
#     'counterparties',
#     'files',
#     'nomenclatures',
#     'orders',
#     'ch_statistic',
#     'tasks',
#     'promotions',
#     'placement_order',
#     'feedback.apps.FeedbackConfig',
#     'services.apps.ServicesConfig',
# ]

# # ---------------------------------- MAIL ---------------------------------- #
# # Базовые настройки

# DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')
# EMAIL_HOST = os.environ.get('EMAIL_HOST', 'email.krasrm.com')
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'info@krasrm.com')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
# EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
# # Настройки TLS/SSL
# EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
# EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'false').lower() == 'true'

# # Выбор бэкенда
# if DEBUG or os.environ.get('DISABLE_EMAIL_SSL_VERIFY', 'true').lower() == 'true':
#     # Используем кастомный бэкенд с отключенной проверкой SSL
#     EMAIL_BACKEND = 'feedback.email_backend.CustomEmailBackend'
#     print("Using email backend without SSL verification")
# else:
#     EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# # Таймаут для SMTP
# EMAIL_TIMEOUT = 10  # секунд

# # Дополнительные настройки безопасности (если нужно)
# if not DEBUG:
#     EMAIL_SSL_CERTFILE = None
#     EMAIL_SSL_KEYFILE = None


# # Базовый MIDDLEWARE
# MIDDLEWARE = [
#     'debug_toolbar.middleware.DebugToolbarMiddleware',
#     'corsheaders.middleware.CorsMiddleware',
#     'django.middleware.security.SecurityMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]

# # Добавляем IntegrityMiddleware только для DEBUG (но уже не трогаем debug_toolbar)
# if DEBUG:
#     MIDDLEWARE += ['api.middleware.IntegrityMiddleware']

# ROOT_URLCONF = 'rmc_rest_api.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [os.path.join(BASE_DIR, 'templates')],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# #Базовый MIDDLEWARE
# MIDDLEWARE = [
#     'corsheaders.middleware.CorsMiddleware',
#     'django.middleware.security.SecurityMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]

# # Добавляем debug toolbar только в DEBUG режиме
# if DEBUG:
#     MIDDLEWARE += ['api.middleware.IntegrityMiddleware', 'debug_toolbar.middleware.DebugToolbarMiddleware']

# ROOT_URLCONF = 'rmc_rest_api.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [os.path.join(BASE_DIR, 'templates')],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'rmc_rest_api.wsgi.application'

# # Настройки базы данных
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get('POSTGRES_DB'),
#         'HOST': os.environ.get('POSTGRES_HOST'),
#         'USER': os.environ.get('POSTGRES_USER'),
#         'PORT': os.environ.get('POSTGRES_PORT'),
#         'PASSWORD': os.environ.get('POSTGRES_PASS'),
#         'CONN_MAX_AGE': 60 if not DEBUG else 0,
#     }
# }

# # Проверяем наличие настроек Clickhouse
# CLICKHOUSE_HOST = os.environ.get('CLICKHOUSE_HOST')
# if CLICKHOUSE_HOST:
#     DATABASES['clickhouse'] = {
#         'ENGINE': 'clickhouse_backend.backend',
#         'NAME': os.environ.get('CLICKHOUSE_DB'),
#         'HOST': CLICKHOUSE_HOST,
#         'USER': os.environ.get('CLICKHOUSE_USER'),
#         'PORT': os.environ.get('CLICKHOUSE_PORT'),
#         'PASSWORD': os.environ.get('CLICKHOUSE_PASSWORD'),
#     }

# DATABASE_ROUTERS = ['rmc_rest_api.dbrouters.ClickHouseRouter']

# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]

# AUTH_USER_MODEL = 'users.CustomUser'

# PASSWORD_HASHERS = [
#     'django.contrib.auth.hashers.Argon2PasswordHasher',
# ]

# LANGUAGE_CODE = 'ru'

# TIME_ZONE = 'Asia/Krasnoyarsk'

# USE_I18N = True

# USE_TZ = False

# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST_FRAMEWORK = {
#     'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'rest_framework_simplejwt.authentication.JWTAuthentication',
#     ),
#     'DEFAULT_PERMISSION_CLASSES': (
#         'rest_framework.permissions.IsAuthenticated',
#     ),
#     'DEFAULT_PAGINATION_CLASS': 'api.pagination.PageLimitPagination',
#     'PAGE_SIZE': 25,
# }

# # Убираем Browsable API в production
# if not DEBUG:
#     REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
#         'rest_framework.renderers.JSONRenderer',
#     )

# SPECTACULAR_SETTINGS = {
#     'TITLE': 'RMC REST API',
#     'DESCRIPTION': 'API',
#     'VERSION': '1.0.0',
#     'SERVE_INCLUDE_SCHEMA': False,
# }

# # ---------------------------------- REDIS ---------------------------------- #
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': 'redis://redis:6379/1',
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#             'KEY_PREFIX': 'django_cache',
#             'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',

#             # Временно убираем hiredis, используем стандартный парсер
#             # 'CONNECTION_POOL_KWARGS': {
#             #     'parser_class': 'redis.connection.HiredisParser',
#             # },

#             'SOCKET_CONNECT_TIMEOUT': 5,
#             'SOCKET_TIMEOUT': 5,
#             'IGNORE_EXCEPTIONS': True,
#         }
#     }
# }
# # Время жизни кэша по умолчанию (в секундах)
# CACHE_TTL = 60 * 5  # 5 минут

# # ---------------------------------- MINIO ---------------------------------- #
# from datetime import timedelta

# # =========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===========
# MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'files:9000')
# MINIO_ACCESS_KEY = os.environ.get('MINIO_STORAGE_ACCESS_KEY')
# MINIO_SECRET_KEY = os.environ.get('MINIO_STORAGE_SECRET_KEY')
# MINIO_USE_HTTPS = os.environ.get('MINIO_HTTPS', 'false').lower() == 'true'
# MINIO_EXTERNAL_ENDPOINT = os.environ.get('MINIO_EXTERNAL_ENDPOINT')
# MINIO_EXTERNAL_ENDPOINT_USE_HTTPS = os.environ.get('MINIO_EXTERNAL_HTTPS', 'true').lower() == 'true'
# MINIO_REGION = os.environ.get('MINIO_REGION', 'us-east-1')

# MINIO_PUBLIC_BUCKETS = ['local-static']
# MINIO_PRIVATE_BUCKETS = ['local-media']

# # =========== STORAGES ===========
# STORAGES = {
#     'default': {
#         'BACKEND': 'django_minio_backend.models.MinioBackend',
#         'OPTIONS': {
#             'MINIO_ENDPOINT': MINIO_ENDPOINT,
#             'MINIO_ACCESS_KEY': MINIO_ACCESS_KEY,
#             'MINIO_SECRET_KEY': MINIO_SECRET_KEY,
#             'MINIO_USE_HTTPS': MINIO_USE_HTTPS,
#             'MINIO_REGION': MINIO_REGION,
#             'MINIO_EXTERNAL_ENDPOINT': MINIO_EXTERNAL_ENDPOINT,
#             'MINIO_EXTERNAL_ENDPOINT_USE_HTTPS': MINIO_EXTERNAL_ENDPOINT_USE_HTTPS,
#             'MINIO_PRIVATE_BUCKETS': MINIO_PRIVATE_BUCKETS,
#             'MINIO_PUBLIC_BUCKETS': MINIO_PUBLIC_BUCKETS,
#             'MINIO_URL_EXPIRY_HOURS': timedelta(days=1),
#             'MINIO_CONSISTENCY_CHECK_ON_START': False,
#         }
#     },
#     'staticfiles': {
#         'BACKEND': 'django_minio_backend.models.MinioBackendStatic',
#         'OPTIONS': {
#             'MINIO_ENDPOINT': MINIO_ENDPOINT,
#             'MINIO_ACCESS_KEY': MINIO_ACCESS_KEY,
#             'MINIO_SECRET_KEY': MINIO_SECRET_KEY,
#             'MINIO_USE_HTTPS': MINIO_USE_HTTPS,
#             'MINIO_REGION': MINIO_REGION,
#             'MINIO_EXTERNAL_ENDPOINT': MINIO_EXTERNAL_ENDPOINT,
#             'MINIO_EXTERNAL_ENDPOINT_USE_HTTPS': MINIO_EXTERNAL_ENDPOINT_USE_HTTPS,
#             'MINIO_STATIC_FILES_BUCKET': 'local-static',
#             'MINIO_URL_EXPIRY_HOURS': timedelta(days=365),
#             'MINIO_CONSISTENCY_CHECK_ON_START': True,
#         }
#     },
# }

# # --------------------------------- CELERY ---------------------------------- #

# CELERY_BROKER_URL = os.environ.get('CELERY_BROKER')
# CELERY_RESULT_BACKEND = os.environ.get('CELERY_BACKEND')
# if CELERY_BROKER_URL and CELERY_RESULT_BACKEND:
#     CELERY_SINGLETON_BACKEND_URL = CELERY_RESULT_BACKEND
#     CELERY_TIMEZONE = TIME_ZONE

# # -------------------------------- SECURITY --------------------------------- #

# CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOW_CREDENTIALS = True

# CORS_ALLOW_METHODS = [
#     'DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT'
# ]

# CORS_ALLOWED_HEADERS = [
#     'accept', 'accept-encoding', 'authorization', 'content-type', 'dnt',
#     'origin', 'user-agent', 'x-csrftoken', 'x-requested-with'
# ]

# CSRF_TRUSTED_ORIGINS = os.environ.get('FRONTEND_DOMEN', '').split(', ')
# if not DEBUG:
#     CORS_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS

# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': td(days=30),
#     'REFRESH_TOKEN_LIFETIME': td(days=60),
#     'AUTH_HEADER_TYPES': ('access_token',),
#     'BLACKLIST_AFTER_ROTATION': True,
#     'ROTATE_REFRESH_TOKENS': True,
#     'AUTH_TOKEN_CLASSES': ('api.tokens.CustomAccessToken',)
# }


# # ------------------------------ DEBUG TOOLBAR ------------------------------ #


# if DEBUG:
#     def show_toolbar(request):
#         return True


#     DEBUG_TOOLBAR_CONFIG = {
#         'SHOW_TOOLBAR_CALLBACK': show_toolbar,
#     }

#     import mimetypes

#     mimetypes.add_type('application/javascript', '.js', True)

# # ---------------------------- PRODUCTION SETTINGS -------------------------- #

# if not DEBUG:
#     # Безопасные настройки для production
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True
#     X_FRAME_OPTIONS = 'DENY'

#     # Лимиты для загрузки
#     DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
#     FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# # ---------------------------- OPENSEARCH SETTINGS -------------------------- #
# OPENSEARCH_DSL = {
#     'default': {
#         'hosts': 'opensearch:9200',
#         # для prod с авторизацией:
#         # 'hosts': [{"scheme": "https", "host": "opensearch.host", "port": 9200}],
#         # 'http_auth': ('admin', 'password'),
#         # 'timeout': 30,
#     }
# }
# # Отключаем автосинк — будем синкать через Celery вручную
# OPENSEARCH_DSL_AUTOSYNC = False

# # settings.py (в конец файла)

# # ---------------------------- LOGGING -------------------------- #

# import os
# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent.parent

# # Создаем директорию для логов с обработкой ошибок
# LOG_DIR = os.path.join(BASE_DIR, 'logs')
# try:
#     os.makedirs(LOG_DIR, exist_ok=True)
#     # Проверяем права на запись
#     test_file = os.path.join(LOG_DIR, '.test_write')
#     with open(test_file, 'w') as f:
#         f.write('test')
#     os.remove(test_file)
#     print(f"LOG_DIR is writable: {LOG_DIR}")
# except Exception as e:
#     print(f"Cannot write to LOG_DIR: {LOG_DIR}")
#     print(f"Error: {e}")
#     # Fallback - используем /tmp если не можем писать в LOG_DIR
#     LOG_DIR = '/tmp'
#     os.makedirs(LOG_DIR, exist_ok=True)
#     print(f"Using fallback LOG_DIR: {LOG_DIR}")

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '[{levelname}] {asctime} | {module} | {funcName}:{lineno} | {message}',
#             'style': '{',
#             'datefmt': '%Y-%m-%d %H:%M:%S',
#         },
#         'simple': {
#             'format': '[{levelname}] {asctime} | {message}',
#             'style': '{',
#             'datefmt': '%H:%M:%S',
#         },
#     },
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'simple',
#         },
#         'feedback_file': {
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': os.path.join(LOG_DIR, 'feedback.log'),
#             'maxBytes': 1024 * 1024 * 5,  # 5 MB
#             'backupCount': 3,
#             'formatter': 'verbose',
#         },
#         'email_file': {
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': os.path.join(LOG_DIR, 'email.log'),
#             'maxBytes': 1024 * 1024 * 5,  # 5 MB
#             'backupCount': 3,
#             'formatter': 'verbose',
#         },
#         'file': {
#             'class': 'logging.FileHandler',
#             'filename': BASE_DIR / 'logs' / 'api_1c.log',
#         },
#         # Новый handler для OpenSearch
#         'opensearch_file': {
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': os.path.join(LOG_DIR, 'opensearch.log'),
#             'maxBytes': 1024 * 1024 * 5,  # 5 MB
#             'backupCount': 5,
#             'formatter': 'verbose',
#         },
#     },
#     'loggers': {
#         'feedback': {
#             'handlers': ['feedback_file', 'console'],
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#         'feedback.email': {
#             'handlers': ['email_file', 'console'],
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#         'services.api_1c': {
#             'handlers': ['file', 'console'],
#             'level': 'INFO',
#         },
#         # Новый logger для OpenSearch
#         'nomenclatures.services.opensearch_search': {
#             'handlers': ['opensearch_file', 'console'],
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#         'nomenclatures.filters': {
#             'handlers': ['opensearch_file', 'console'],
#             'level': 'INFO',
#             'propagate': False,
#         },
#     },
# }



# from datetime import timedelta as td
# from pathlib import Path
# import os
#
# BASE_DIR = Path(__file__).resolve().parent.parent
#
# SECRET_KEY = os.environ.get('SECRET_KEY')
#
# # Безопасное получение DEBUG
# DEBUG = os.environ.get('DEBUG', '').lower() == 'true'
#
# ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1, localhost, 192.168.0.61').split(', ')
#
# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
#     'django.contrib.postgres',
#     'corsheaders',
#     'colorfield',
#     'django_minio_backend',
#     'clickhouse_backend',
#     'django_filters',
#     'rest_framework',
#     'rest_framework_simplejwt',
#     'rest_framework_simplejwt.token_blacklist',
#     'debug_toolbar',
#     'drf_spectacular',
#     'djoser',
#     'phonenumber_field',
#     'counterparties',
#     'dal',
#     'dal_select2',
#     'docs',
#     'files',
#     'nomenclatures',
#     'brands',
#     'orders',
#     'ch_statistic',
#     'tasks',
#     'users',
#     'addresses',
#     'promotions'
# ]
#
# # Базовый MIDDLEWARE
# MIDDLEWARE = [
#     'corsheaders.middleware.CorsMiddleware',
#     'django.middleware.security.SecurityMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]
#
# # Добавляем debug toolbar только в DEBUG режиме
# if DEBUG:
#     MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
#     MIDDLEWARE.append('api.middleware.IntegrityMiddleware')
#
# ROOT_URLCONF = 'rmc_rest_api.urls'
#
# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [os.path.join(BASE_DIR, 'templates')],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]
#
# WSGI_APPLICATION = 'rmc_rest_api.wsgi.application'
#
# # Настройки базы данных
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get('POSTGRES_DB'),
#         'HOST': os.environ.get('POSTGRES_HOST'),
#         'USER': os.environ.get('POSTGRES_USER'),
#         'PORT': os.environ.get('POSTGRES_PORT'),
#         'PASSWORD': os.environ.get('POSTGRES_PASS'),
#         'CONN_MAX_AGE': 60 if not DEBUG else 0,
#     }
# }
#
# # Проверяем наличие настроек Clickhouse
# CLICKHOUSE_HOST = os.environ.get('CLICKHOUSE_HOST')
# if CLICKHOUSE_HOST:
#     DATABASES['clickhouse'] = {
#         'ENGINE': 'clickhouse_backend.backend',
#         'NAME': os.environ.get('CLICKHOUSE_DB'),
#         'HOST': CLICKHOUSE_HOST,
#         'USER': os.environ.get('CLICKHOUSE_USER'),
#         'PORT': os.environ.get('CLICKHOUSE_PORT'),
#         'PASSWORD': os.environ.get('CLICKHOUSE_PASSWORD'),
#     }
#
#
# DATABASE_ROUTERS = ['rmc_rest_api.dbrouters.ClickHouseRouter']
#
# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]
#
# AUTH_USER_MODEL = 'users.CustomUser'
#
# PASSWORD_HASHERS = [
#     'django.contrib.auth.hashers.Argon2PasswordHasher',
# ]
#
# LANGUAGE_CODE = 'ru'
#
# TIME_ZONE = 'Asia/Krasnoyarsk'
#
# USE_I18N = True
#
# USE_TZ = False
#
# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
#
# REST_FRAMEWORK = {
#     'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'rest_framework_simplejwt.authentication.JWTAuthentication',
#     ),
#     'DEFAULT_PERMISSION_CLASSES': (
#         'rest_framework.permissions.IsAuthenticated',
#     ),
#     'DEFAULT_PAGINATION_CLASS': 'api.pagination.PageLimitPagination',
#     'PAGE_SIZE': 25,
# }
#
# # Убираем Browsable API в production
# if not DEBUG:
#     REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
#         'rest_framework.renderers.JSONRenderer',
#     )
#
# SPECTACULAR_SETTINGS = {
#     'TITLE': 'RMC REST API',
#     'DESCRIPTION': 'API',
#     'VERSION': '1.0.0',
#     'SERVE_INCLUDE_SCHEMA': False,
# }
#
#
#
# # ---------------------------------- MINIO ---------------------------------- #
# # MINIO_REGION = os.environ.get('MINIO_REGION')
# # MINIO_ACCESS_KEY = os.environ.get('MINIO_STORAGE_ACCESS_KEY')
# # MINIO_SECRET_KEY = os.environ.get('MINIO_STORAGE_SECRET_KEY')
# # MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT')
# # MINIO_USE_HTTPS = os.environ.get('MINIO_HTTPS').lower() == 'true'
# # MINIO_EXTERNAL_ENDPOINT = os.environ.get('MINIO_EXTERNAL_ENDPOINT')
# # MINIO_EXTERNAL_ENDPOINT_USE_HTTPS = os.environ.get('MINIO_EXTERNAL_HTTPS').lower() == 'true'
# # MINIO_PRIVATE_BUCKETS = [
# #     'local-media',
# #     'local-static'
# # ]
# # MINIO_MEDIA_FILES_BUCKET = 'local-media'
# # MINIO_STATIC_FILES_BUCKET = 'local-static'
# # STATIC_URL = 'http://localhost:9000/local-static/'
# # STORAGES = {
# #     'default': {
# #         'BACKEND': 'django_minio_backend.models.MinioBackend'
# #     },
# #     'staticfiles': {
# #         'BACKEND': 'django_minio_backend.models.MinioBackendStatic'
# #     },
# # }
#
# # # ---------------------------------- MINIO ---------------------------------- #
# # MINIO_REGION = os.environ.get('MINIO_REGION')
# # MINIO_ACCESS_KEY = os.environ.get('MINIO_STORAGE_ACCESS_KEY')
# # MINIO_SECRET_KEY = os.environ.get('MINIO_STORAGE_SECRET_KEY')
# # MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT')  # files:9000 для контейнеров
# # MINIO_USE_HTTPS = os.environ.get('MINIO_HTTPS', 'false').lower() == 'true'
# # MINIO_EXTERNAL_ENDPOINT = os.environ.get('MINIO_EXTERNAL_ENDPOINT')  # 192.168.0.61
# # MINIO_EXTERNAL_ENDPOINT_USE_HTTPS = os.environ.get('MINIO_EXTERNAL_HTTPS', 'false').lower() == 'true'
# #
# # MINIO_PRIVATE_BUCKETS = ['local-media', 'local-static']
# # MINIO_MEDIA_FILES_BUCKET = 'local-media'
# # MINIO_STATIC_FILES_BUCKET = 'local-static'
# #
# # # URL для статики (для браузера)
# # STATIC_URL = (
# #     f"{'https' if MINIO_EXTERNAL_ENDPOINT_USE_HTTPS else 'http'}://"
# #     f"{MINIO_EXTERNAL_ENDPOINT}:9000/local-static/"
# # )
# #
# # MINIO_OPTIONS = {
# #     'region': MINIO_REGION,
# #     'access_key': MINIO_ACCESS_KEY,
# #     'secret_key': MINIO_SECRET_KEY,
# #     'endpoint': MINIO_ENDPOINT,   # files:9000 — Django внутри Docker
# #     'use_https': MINIO_USE_HTTPS,
# # }
# #
# # # Используем MinIO только если не DEBUG
# # if DEBUG or not MINIO_ENDPOINT:
# #     DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
# #     STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
# # else:
# #     STORAGES = {
# #         'default': {
# #             'BACKEND': 'django_minio_backend.models.MinioBackend',
# #             'OPTIONS': MINIO_OPTIONS
# #         },
# #         'staticfiles': {
# #             'BACKEND': 'django_minio_backend.models.MinioBackendStatic',
# #             'OPTIONS': MINIO_OPTIONS
# #         },
# #     }
#
#
# # # --------------------------------- LOGGING ---------------------------------- #
# #
# # LOGGING = {
# #     "version": 1,
# #     "disable_existing_loggers": False,
# #     "formatters": {
# #         "verbose": {
# #             "format": "[{asctime}] {levelname} {name}: {message}",
# #             "style": "{",
# #         },
# #     },
# #     "handlers": {
# #         "brand_conflicts": {
# #             "class": "logging.FileHandler",
# #             "filename": "/app/network_logs/brand_conflicts.log",
# #             "encoding": "utf-8",
# #             "formatter": "verbose",
# #         },
# #         "console": {
# #             "class": "logging.StreamHandler",
# #             "formatter": "verbose",
# #         },
# #     },
# #     "loggers": {
# #         "brands": {
# #             "handlers": ["brand_conflicts", "console"],
# #             "level": "INFO",
# #             "propagate": False,
# #         },
# #     },
# # }
# # --------------------------------- CELERY ---------------------------------- #
#
# CELERY_BROKER_URL = os.environ.get('CELERY_BROKER')
# CELERY_RESULT_BACKEND = os.environ.get('CELERY_BACKEND')
# if CELERY_BROKER_URL and CELERY_RESULT_BACKEND:
#     CELERY_SINGLETON_BACKEND_URL = CELERY_RESULT_BACKEND
#     CELERY_TIMEZONE = TIME_ZONE
#
# # -------------------------------- SECURITY --------------------------------- #
#
# CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOW_CREDENTIALS = True
#
# CORS_ALLOW_METHODS = [
#     'DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT'
# ]
#
# CORS_ALLOWED_HEADERS = [
#     'accept', 'accept-encoding', 'authorization', 'content-type', 'dnt',
#     'origin', 'user-agent', 'x-csrftoken', 'x-requested-with'
# ]
#
# CSRF_TRUSTED_ORIGINS = os.environ.get('FRONTEND_DOMEN', '').split(', ')
# if not DEBUG:
#     CORS_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS
#
# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': td(days=30),
#     'REFRESH_TOKEN_LIFETIME': td(days=60),
#     'AUTH_HEADER_TYPES': ('access_token',),
#     'BLACKLIST_AFTER_ROTATION': True,
#     'ROTATE_REFRESH_TOKENS': True,
#     'AUTH_TOKEN_CLASSES': ('api.tokens.CustomAccessToken',)
# }
#
#
# # ------------------------------ DEBUG TOOLBAR ------------------------------ #
#
# if DEBUG:
#     def show_toolbar(request):
#         return True
#
#     DEBUG_TOOLBAR_CONFIG = {
#         'SHOW_TOOLBAR_CALLBACK': show_toolbar,
#     }
#
#     import mimetypes
#
#     mimetypes.add_type('application/javascript', '.js', True)
#
# # ---------------------------- PRODUCTION SETTINGS -------------------------- #
#
# if not DEBUG:
#     # Безопасные настройки для production
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True
#     X_FRAME_OPTIONS = 'DENY'
#
#     # Лимиты для загрузки
#     DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
#     FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
