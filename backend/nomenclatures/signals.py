from django.db.models.signals import pre_save, post_save, post_delete, m2m_changed
from django.dispatch import receiver
import logging

from counterparties.models import Counterparty
from nomenclatures.models import Nomenclature, NomenclatureTenant

logger = logging.getLogger(__name__)

from nomenclatures.tasks import update_opensearch_for_instance

@receiver(post_save, sender=Nomenclature)
def update_nomenclature_search_vector(sender, instance, created, **kwargs):
    """Обновляет search_vector при сохранении номенклатуры."""
    if kwargs.get('raw', False):
        return

    instance.update_search_vector()

@receiver(m2m_changed, sender=Nomenclature.tenants.through)
def update_search_vector_on_tenants_change(sender, instance, action, **kwargs):
    """Обновляет search_vector при изменении арендаторов."""
    if action in ['post_add', 'post_remove', 'post_clear']:
        instance.update_search_vector()

@receiver(post_save, sender=Nomenclature)
def update_search_vector_signal(sender, instance, **kwargs):
    update_opensearch_for_instance.delay(str(instance.id))

# 🔴 Когда добавляют/меняют арендатора
@receiver(post_save, sender=NomenclatureTenant)
def update_opensearch_on_tenant_change(sender, instance, **kwargs):
    """Обновить OpenSearch при изменении арендатора"""
    update_opensearch_for_instance.delay(str(instance.nomenclature_id))

# 🔴 Когда удаляют арендатора
@receiver(post_delete, sender=NomenclatureTenant)
def update_opensearch_on_tenant_delete(sender, instance, **kwargs):
    """Обновить OpenSearch при удалении арендатора"""
    update_opensearch_for_instance.delay(str(instance.nomenclature_id))

@receiver(post_delete, sender=Nomenclature)
def delete_from_opensearch(sender, instance, **kwargs):
    from nomenclatures.documents import NomenclatureDocument
    try:
        doc = NomenclatureDocument()
        doc.delete(instance)  # ← исправил: было action='delete'
    except Exception as e:
        logger.error(f"Ошибка удаления из OpenSearch: {e}")

@receiver(post_save, sender=Nomenclature)
def nomenclature_set_broadcast(sender, instance, **kwargs):

    if instance.legalEntity_id:
        Counterparty.objects.filter(
            pk=instance.legalEntity_id,
            broadcast=False
        ).update(broadcast=True)

    old_id = getattr(instance, "_old_legal_entity_id", None)

    if old_id is None and instance.pk:
        old_id = (
            sender.objects
            .filter(pk=instance.pk)
            .values_list("legalEntity_id", flat=True)
            .first()
        )

    if old_id and old_id != instance.legalEntity_id:
        if not Nomenclature.objects.filter(legalEntity_id=old_id).exists():
            Counterparty.objects.filter(pk=old_id).update(broadcast=False)


@receiver(post_delete, sender=Nomenclature)
def nomenclature_unset_broadcast_on_delete(sender, instance, **kwargs):
    """
    Если номенклатуру удалили — возможно,
    нужно выключить broadcast.
    """
    if not instance.legalEntity_id:
        return

    still_used = Nomenclature.objects.filter(
        legalEntity_id=instance.legalEntity_id
    ).exists()

    if not still_used:
        Counterparty.objects.filter(
            pk=instance.legalEntity_id,
            broadcast=True
        ).update(broadcast=False)