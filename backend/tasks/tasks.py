from celery import shared_task


@shared_task()
def create_task(owner, client, _type, parameters):
    """Создание репликации."""


