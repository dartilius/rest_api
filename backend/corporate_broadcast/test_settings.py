"""Offline settings for the landing API tests; no .env or live services."""
import os

os.environ["URL_1C"] = "http://127.0.0.1:1"

from rmc_rest_api.settings import *  # noqa: F403, E402

SECRET_KEY = "offline-landing-tests"
DEBUG = False
STATIC_URL = "/static/"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DATABASE_ROUTERS = []
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
LOGGING = {"version": 1, "disable_existing_loggers": False}
OPENSEARCH_DSL_AUTOSYNC = False
MINIO_ENDPOINT = None  # files.apps.ready must not initialize real buckets.
STORAGES = {
    "default": {"BACKEND": "django_minio_backend.models.MinioBackend", "OPTIONS": {
        "MINIO_ENDPOINT": "127.0.0.1:9000",
        "MINIO_ACCESS_KEY": "offline-access",
        "MINIO_SECRET_KEY": "offline-secret",
        "MINIO_USE_HTTPS": False,
        "MINIO_EXTERNAL_ENDPOINT": "127.0.0.1:9000",
        "MINIO_EXTERNAL_ENDPOINT_USE_HTTPS": False,
        "MINIO_REGION": "us-east-1",
        "MINIO_CONSISTENCY_CHECK_ON_START": False,
        "MINIO_PRIVATE_BUCKETS": ["local-media"],
        "MINIO_PUBLIC_BUCKETS": [],
    }},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
ROOT_URLCONF = "corporate_broadcast.test_urls"
