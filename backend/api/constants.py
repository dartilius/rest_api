class Constants:
    """DRY."""

    empty_values = ('', [], (), {}, None)

    @staticmethod
    def get_minio_client(external=False):
        """Авторизует запрос для обращений к облаку."""
        from minio import Minio
        from django.conf import settings

        if external:
            endpoint = settings.MINIO_EXTERNAL_ENDPOINT
        else:
            endpoint = settings.MINIO_ENDPOINT
        minio_client = Minio(
            endpoint,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_HTTPS,
            cert_check=settings.MINIO_USE_HTTPS
        )
        return minio_client
