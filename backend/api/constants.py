class Constants:
    """DRY."""

    empty_values = ('', [], (), {}, None)


    @staticmethod
    def get_task_type(order_type: int):
        """Возвращает соответствующий заказу тип репликации."""
        ORDER_MUSIC = 0
        ORDER_IMAGE = 1
        ORDER_VIDEO = 2
        ORDER_TICKER = 3
        TASK_MUSIC = 5
        TASK_IMAGE = 6
        TASK_VIDEO = 7
        TASK_TICKER = 8
        order_types_to_task_types = {
            ORDER_MUSIC: TASK_MUSIC,
            ORDER_IMAGE: TASK_IMAGE,
            ORDER_VIDEO: TASK_VIDEO,
            ORDER_TICKER: TASK_TICKER
        }
        return order_types_to_task_types[order_type]


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
            region=settings.MINIO_REGION,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_HTTPS,
            cert_check=settings.MINIO_USE_HTTPS
        )
        return minio_client
