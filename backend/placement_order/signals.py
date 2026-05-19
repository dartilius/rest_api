import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from placement_order.models import PlacementOrder

logger = logging.getLogger('placement_order')


@receiver(post_save, sender=PlacementOrder)
def on_placement_order_created(sender, instance: PlacementOrder, created: bool, **kwargs) -> None:
    if not created:
        return

    logger.info(f"[СИГНАЛ] PlacementOrder id={instance.id} создан, запускаем таск")

    try:
        from placement_order.tasks import send_placement_order_email
        task = send_placement_order_email.delay(order_id=str(instance.id))
        logger.info(f"[СИГНАЛ] Таск создан: {task.id}")
    except Exception as e:
        logger.error(f"[СИГНАЛ] Не удалось запустить таск: {e}")