from minio import Minio
from minio.error import S3Error
from django.conf import settings


def initialize_minio_buckets():
    """Проверка наличия и автоматическая инициализация незапущенных бакетов."""
    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_HTTPS,
        cert_check=settings.MINIO_USE_HTTPS
    )

    for bucket in settings.MINIO_PRIVATE_BUCKETS:
        try:
            if not minio_client.bucket_exists(bucket):
                minio_client.make_bucket(bucket)
                print(f'Created bucket: {bucket}')
        except S3Error as e:
            print(f'Возникла ошибка: {e}')
