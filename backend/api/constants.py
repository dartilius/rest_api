from minio import Minio
from django.conf import settings


class Constants:
    empty_values = ('', [], (), {}, None)

    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_HTTPS,
        cert_check=settings.MINIO_USE_HTTPS
    )
