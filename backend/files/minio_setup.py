import json
import os

from django.conf import settings
from minio.error import S3Error

from api.constants import get_minio_client


def public_read_policy(bucket):
    """Каноническая политика public-read для MinIO (та, что пишет
    `mc anonymous set download`). Обратите внимание: MinIO требует
    Version "2012-10-17" для bucket policies.
    """
    return json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                    "Resource": [f"arn:aws:s3:::{bucket}"],
                },
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket}/*"],
                },
            ],
        }
    )


def get_minio_admin_client():
    """Клиент с правами администратора (root-пользователь MinIO).

    Создание бакетов и установка политик требуют привилегий, которых у
    обычного приложения аккаунта может не быть. Если root-учётные данные
    не заданы, используется обычный клиент приложения.
    """
    from minio import Minio

    user = os.environ.get('MINIO_ROOT_USER')
    password = os.environ.get('MINIO_ROOT_PASSWORD')
    if user and password:
        return Minio(
            settings.MINIO_ENDPOINT,
            region=settings.MINIO_REGION,
            access_key=user,
            secret_key=password,
            secure=settings.MINIO_USE_HTTPS,
            cert_check=settings.MINIO_USE_HTTPS,
        )
    return get_minio_client()


def initialize_minio_buckets():
    """Проверка наличия и автоматическая инициализация незапущенных бакетов."""
    minio_client = get_minio_admin_client()

    for bucket in settings.MINIO_PUBLIC_BUCKETS:
        try:
            if not minio_client.bucket_exists(bucket):
                minio_client.make_bucket(bucket)
                print(f'Created bucket: {bucket}')
            minio_client.set_bucket_policy(bucket, public_read_policy(bucket))
            print(f'Public access enabled: {bucket}')
        except S3Error as e:
            print(f'Возникла ошибка с публичным бакетом {bucket}: {e}')

    for bucket in settings.MINIO_PRIVATE_BUCKETS:
        try:
            if not minio_client.bucket_exists(bucket):
                minio_client.make_bucket(bucket)
                print(f'Created bucket: {bucket}')
        except S3Error as e:
            print(f'Возникла ошибка: {e}')
