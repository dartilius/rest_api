from django.conf import settings
from minio.error import S3Error

from api.constants import get_minio_client


def initialize_minio_buckets():
    """Проверка наличия и автоматическая инициализация незапущенных бакетов."""
    minio_client = get_minio_client()

    for bucket in settings.MINIO_PRIVATE_BUCKETS:
        try:
            if not minio_client.bucket_exists(bucket):
                minio_client.make_bucket(bucket)
                print(f'Created bucket: {bucket}')
        except S3Error as e:
            print(f'Возникла ошибка: {e}')
