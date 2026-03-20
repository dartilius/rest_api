from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from counterparties.models import Counterparty
from nomenclatures.models import Nomenclature
from nomenclatures.tasks import update_search_vectors_batch
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Nomenclature)
def update_search_vector_signal(sender, instance, created, **kwargs):
    """
    Обновление поискового вектора при сохранении номенклатуры
    """
    try:
        # Проверяем, когда последний раз обновлялся поисковый вектор
        if hasattr(instance, 'search_vector_updated_at') and instance.search_vector_updated_at:
            time_since_update = timezone.now() - instance.search_vector_updated_at
            # Если обновлялось менее 5 минут назад - пропускаем (только для существующих записей)
            if time_since_update < timedelta(minutes=5) and not created:
                logger.debug(f"Пропуск обновления search_vector для {instance.id} (частое обновление)")
                return

        # Запускаем обновление для этой номенклатуры
        update_search_vectors_batch.delay([instance.id])
        logger.debug(f"Запланировано обновление search_vector для номенклатуры {instance.id}")

    except Exception as e:
        logger.error(f"Ошибка при планировании обновления search_vector для {getattr(instance, 'id', 'new')}: {e}")


@receiver(pre_save, sender=Nomenclature)
def nomenclature_store_old_legal_entity(sender, instance, **kwargs):
    """
    Сохраняем старое значение legalEntity, чтобы понять,
    кого нужно выключить после save.
    """
    try:
        if not instance.pk:
            instance._old_legal_entity_id = None
            return

        instance._old_legal_entity_id = (
            sender.objects
            .filter(pk=instance.pk)
            .values_list("legalEntity_id", flat=True)
            .first()
        )
    except Exception as e:
        logger.error(f"Ошибка в nomenclature_store_old_legal_entity: {e}")
        instance._old_legal_entity_id = None


@receiver(post_save, sender=Nomenclature)
def nomenclature_set_broadcast(sender, instance, **kwargs):
    """
    Обновление broadcast статуса контрагента при изменении legalEntity
    """
    try:
        # Включаем broadcast для нового legalEntity
        if instance.legalEntity_id:
            Counterparty.objects.filter(
                pk=instance.legalEntity_id,
                broadcast=False
            ).update(broadcast=True)

        # Получаем старый legalEntity
        old_id = getattr(instance, "_old_legal_entity_id", None)

        # Если old_id не сохранился в pre_save, пробуем получить из БД
        if old_id is None and instance.pk:
            old_id = (
                sender.objects
                .filter(pk=instance.pk)
                .values_list("legalEntity_id", flat=True)
                .first()
            )

        # Если старый legalEntity отличается от нового и больше не используется
        if old_id and old_id != instance.legalEntity_id:
            if not Nomenclature.objects.filter(legalEntity_id=old_id).exists():
                Counterparty.objects.filter(pk=old_id).update(broadcast=False)

    except Exception as e:
        logger.error(f"Ошибка в nomenclature_set_broadcast для номенклатуры {instance.id}: {e}")


@receiver(post_delete, sender=Nomenclature)
def nomenclature_unset_broadcast_on_delete(sender, instance, **kwargs):
    """
    Если номенклатуру удалили — возможно,
    нужно выключить broadcast у контрагента.
    """
    try:
        if not instance.legalEntity_id:
            return

        # Проверяем, остались ли еще номенклатуры у этого контрагента
        still_used = Nomenclature.objects.filter(
            legalEntity_id=instance.legalEntity_id
        ).exists()

        # Если не осталось, выключаем broadcast
        if not still_used:
            updated = Counterparty.objects.filter(
                pk=instance.legalEntity_id,
                broadcast=True
            ).update(broadcast=False)

            if updated:
                logger.info(
                    f"Broadcast отключен для контрагента {instance.legalEntity_id} (последняя номенклатура удалена)")

    except Exception as e:
        logger.error(f"Ошибка в nomenclature_unset_broadcast_on_delete: {e}")