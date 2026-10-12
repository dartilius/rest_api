"""Offline checks and unit tests; never loads .env or connects to live services.

Database integration tests still require a disposable PostgreSQL configured via
POSTGRES_* variables. Use `python -m django`, not manage.py (which loads .env).
"""
from rmc_rest_api.settings import *  # noqa: F403
import os

os.environ["URL_1C"] = "http://127.0.0.1:1"

SECRET_KEY = "offline-corporate-broadcast-checks-only"
DEBUG = False
STATIC_URL = "/static/"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
CSRF_TRUSTED_ORIGINS = ["http://localhost"]
CORS_ALLOWED_ORIGINS = ["http://localhost"]
MINIO_ACCESS_KEY = "offline-access"
MINIO_SECRET_KEY = "offline-secret"
MINIO_ENDPOINT = "127.0.0.1:9000"
MINIO_EXTERNAL_ENDPOINT = "127.0.0.1:9000"
MINIO_USE_HTTPS = False
MINIO_EXTERNAL_ENDPOINT_USE_HTTPS = False
STORAGES = {
    "default": {"BACKEND": "django_minio_backend.models.MinioBackend", "OPTIONS": {
        "MINIO_ENDPOINT": MINIO_ENDPOINT, "MINIO_ACCESS_KEY": MINIO_ACCESS_KEY,
        "MINIO_SECRET_KEY": MINIO_SECRET_KEY, "MINIO_USE_HTTPS": False,
        "MINIO_EXTERNAL_ENDPOINT": MINIO_EXTERNAL_ENDPOINT,
        "MINIO_EXTERNAL_ENDPOINT_USE_HTTPS": False,
        "MINIO_REGION": "us-east-1", "MINIO_CONSISTENCY_CHECK_ON_START": False,
        "MINIO_PRIVATE_BUCKETS": ["local-media"], "MINIO_PUBLIC_BUCKETS": [],
    }},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
DATABASES = {"default": {**DATABASES["default"], "HOST": DATABASES["default"].get("HOST") or "127.0.0.1", "NAME": DATABASES["default"].get("NAME") or "corporate_checks", "OPTIONS": {"connect_timeout": 2}}}  # noqa: F405
DATABASE_ROUTERS = []
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
LOGGING = {"version": 1, "disable_existing_loggers": False}
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"
OPENSEARCH_DSL_AUTOSYNC = False
# files.apps.ready() otherwise tries to create buckets even during offline checks.
# Explicit storage OPTIONS above remain valid for model field construction.
MINIO_ENDPOINT = None
