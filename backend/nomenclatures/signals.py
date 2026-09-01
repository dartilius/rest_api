"""
Сигналы для приложения nomenclatures.

ОПТИМИЗАЦИЯ:
───────────────────────────────────────────────────────────────────────────────
1. Объединение сигналов для уменьшения количества вызовов
2. Проверка релевантных полей перед обновлением
3. Отложенное обновление через transaction.on_commit
4. Проверка raw для пропуска загрузки фикстур
5. Обработка ошибок с логированием
"""

import logging

from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from counterparties.models import Counterparty
from nomenclatures.models import Nomenclature, NomenclatureTenant
from nomenclatures.services.search import NomenclatureSearchService
from nomenclatures.tasks import update_opensearch_for_instance

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Nomenclature)
def handle_nomenclature_post_save(sender, instance, created, **kwargs):
    """
    Обработчик сохранения номенклатуры.

    Объединяет обновление search_vector и OpenSearch в один сигнал.
    Выполняется только при изменении релевантных полей.

    Аргументы:
        sender (Model): Класс модели Nomenclature
        instance (Nomenclature): Сохраненный объект
        created (bool): Создан ли объект
        **kwargs: Дополнительные аргументы сигнала
    """
    if kwargs.get("raw", False):
        return

    # Список релевантных полей для обновления поисковых индексов
    relevant_fields = [
        "name",
        "code1c",
        "id_rasb",
        "description",
        "contentType",
        "brand",
        "legalEntity",
        "typeOfPlace",
        "responsible_ad",
        "responsible_placement_marketing",
        "for_web",
        "is_active",
        "pricePerMonth",
    ]

    update_fields = kwargs.get("update_fields")
    should_update = (
        created
        or update_fields is None
        or bool(set(update_fields) & set(relevant_fields))
    )

    if should_update:
        transaction.on_commit(lambda: instance.update_search_vector())
        transaction.on_commit(
            lambda: update_opensearch_for_instance.delay(str(instance.id))
        )


@receiver(post_delete, sender=Nomenclature)
def delete_from_opensearch(sender, instance, **kwargs):
    """
    Удаление из OpenSearch при удалении номенклатуры.

    Аргументы:
        sender (Model): Класс модели Nomenclature
        instance (Nomenclature): Удаляемый объект
        **kwargs: Дополнительные аргументы сигнала
    """
    from nomenclatures.documents import NomenclatureDocument

    try:
        doc = NomenclatureDocument()
        doc.delete(instance)
        logger.info(f"Удалена из OpenSearch: {instance.id}")
    except Exception as e:
        logger.error(f"Ошибка удаления из OpenSearch: {e}")


@receiver(post_save, sender=NomenclatureTenant)
@receiver(post_delete, sender=NomenclatureTenant)
def update_opensearch_on_tenant_change(sender, instance, **kwargs):
    """
    Обновление OpenSearch при изменении арендатора.

    Аргументы:
        sender (Model): Класс модели NomenclatureTenant
        instance (NomenclatureTenant): Измененный объект
        **kwargs: Дополнительные аргументы сигнала
    """
    if kwargs.get("raw", False):
        return

    if not instance.nomenclature:
        return

    transaction.on_commit(
        lambda: update_opensearch_for_instance.delay(str(instance.nomenclature_id))
    )


@receiver(post_save, sender=Nomenclature)
def invalidate_search_cache_on_save(sender, instance, **kwargs):
    """
    Очищает кэш поиска при изменении номенклатуры.

    Аргументы:
        sender (Model): Класс модели Nomenclature
        instance (Nomenclature): Сохраненный объект
        **kwargs: Дополнительные аргументы сигнала
    """
    if kwargs.get("raw", False):
        return
    NomenclatureSearchService.clear_cache()


@receiver(post_delete, sender=Nomenclature)
def invalidate_search_cache_on_delete(sender, instance, **kwargs):
    """
    Очищает кэш поиска при удалении номенклатуры.

    Аргументы:
        sender (Model): Класс модели Nomenclature
        instance (Nomenclature): Удаляемый объект
        **kwargs: Дополнительные аргументы сигнала
    """
    NomenclatureSearchService.clear_cache()


@receiver(post_save, sender=Nomenclature)
def nomenclature_set_broadcast(sender, instance, **kwargs):
    """
    Устанавливает флаг broadcast для юридического лица при создании номенклатуры.

    Аргументы:
        sender (Model): Класс модели Nomenclature
        instance (Nomenclature): Сохраненный объект
        **kwargs: Дополнительные аргументы сигнала
    """
    if instance.legalEntity_id:
        Counterparty.objects.filter(pk=instance.legalEntity_id, broadcast=False).update(
            broadcast=True
        )

    old_id = getattr(instance, "_old_legal_entity_id", None)

    if old_id is None and instance.pk:
        old_id = (
            sender.objects.filter(pk=instance.pk)
            .values_list("legalEntity_id", flat=True)
            .first()
        )

    if old_id and old_id != instance.legalEntity_id:
        if not Nomenclature.objects.filter(legalEntity_id=old_id).exists():
            Counterparty.objects.filter(pk=old_id).update(broadcast=False)


@receiver(post_delete, sender=Nomenclature)
def nomenclature_unset_broadcast_on_delete(sender, instance, **kwargs):
    """
    Отключает флаг broadcast для юридического лица при удалении номенклатуры.

    Аргументы:
        sender (Model): Класс модели Nomenclature
        instance (Nomenclature): Удаляемый объект
        **kwargs: Дополнительные аргументы сигнала
    """
    if not instance.legalEntity_id:
        return

    still_used = Nomenclature.objects.filter(
        legalEntity_id=instance.legalEntity_id
    ).exists()

    if not still_used:
        Counterparty.objects.filter(pk=instance.legalEntity_id, broadcast=True).update(
            broadcast=False
        )
